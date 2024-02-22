import re
import json
import numpy as np
import pandas as pd
import streamlit as st 
import vertexai
from vertexai.preview.language_models import TextEmbeddingModel, TextGenerationModel
from vertexai.generative_models import (
    GenerativeModel,
    GenerationConfig,
    Image,
    Content,
    Part,
    GenerationResponse,
)
from google.oauth2 import service_account
from bus_helper import *

type = st.secrets["type"]
project_id = st.secrets["project_id"]
private_key_id = st.secrets["private_key_id"]
private_key = st.secrets["private_key"]
client_email = st.secrets["client_email"]
client_id = st.secrets["client_id"]
auth_uri = st.secrets["auth_uri"]
token_uri  = st.secrets["token_uri"]
auth_provider_x509_cert_url  = st.secrets["auth_provider_x509_cert_url"]
client_x509_cert_url  = st.secrets["client_x509_cert_url"]
universe_domain  = st.secrets["universe_domain"]
location = st.secrets["location"]
LTA_API_KEY = st.secrets["LTA_API_KEY"]

bus_stop_df = pd.read_excel('bus_stop_details.xlsx')

credentials_details = {
  "type": type,
  "project_id": project_id,
  "private_key_id": private_key_id,
  "private_key": private_key,
  "client_email": client_email,
  "client_id": client_id,
  "auth_uri": auth_uri,
  "token_uri": token_uri,
  "auth_provider_x509_cert_url": auth_provider_x509_cert_url,
  "client_x509_cert_url": client_x509_cert_url,
  "universe_domain": universe_domain
}
#credentials = service_account.Credentials.from_service_account_file('genaisa.json')
credentials = service_account.Credentials.from_service_account_info(credentials_details)

# Initiate Vertex AI
vertexai.init(project=project_id, location=location, credentials = credentials)

# This function takes a text string as input and returns the embedding of the text
def get_embedding(text: str) -> list:
    try:
        model = TextEmbeddingModel.from_pretrained("google/textembedding-gecko@001")
        embeddings = model.get_embeddings([text])
        return embeddings[0].values
    except:
        return []

# Compute the cosine similarity of two vectors, wrap as returned function to make easier to use with Pandas
def get_similarity_fn(query_vector):
    def fn(row):
        return np.dot(row, query_vector) / (
            np.linalg.norm(row) * np.linalg.norm(query_vector)
        )
    return fn

def get_context(question, vector_store, num_docs, embedding_col):
    # Embed the search query
    query_vector = np.array(get_embedding(question))
    # Get similarity to all other vectors and sort, cut off at num_docs
    top_matched = (
        vector_store[embedding_col]
        .apply(get_similarity_fn(query_vector))
        .sort_values(ascending=False)[:num_docs]
        .index
    )
    top_matched_df = vector_store[vector_store.index.isin(top_matched)][["bus_service_info"]]
    # Return a string with the top matches
    context = " ".join(top_matched_df.bus_service_info.values)
    return context

def preprocessing():
    # Reading JSON file
    with st.spinner("Loading Embeddings ..."):
        with open('bus_service_embeddings.json', 'r') as json_file:
            data = json.load(json_file)

        unpack = []
        for key in list(data.keys()):
            unpack.append([key, data[key][1],data[key][0]])

        df = pd.DataFrame(unpack)
        df.columns = ['bus_service','bus_service_info','bus_service_embedding']
    return df

def display_conversation(messages):
    for convo in messages:
        with st.chat_message("user"):
            st.markdown(convo[0])
        with st.chat_message("assistant"):
            st.markdown(convo[1])
             
def extract_numbers(text):
    return re.findall(r'\b\d{1,3}[a-zA-Z]?\b', text)

def bus_chatbot():
    llm = GenerativeModel("gemini-1.0-pro")
    ## Initialise conversation and other variables
    if 'model' not in st.session_state:
        st.session_state.model = llm

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    if 'vs' not in st.session_state:
        st.session_state.vs = None
    
    if 'vs_loaded' not in st.session_state:
        st.session_state.vs_loaded = False

    st.title("Singapore Public Bus Services Query")

    st.markdown(
        "A Chatbot with functionalities to get live bus timing from specified bus stop for a specified bus, and getting bus service information such as first and last bus timing, directions of travel and route list.\n\n"
        "Some Sample below to help you out: \n"
        
        "Getting Live Bus Timing (Need to specify 1 Bus Stop Code and 1 Bus Service Number) - What is the arrival timing for bus 913 at 46009\n"

        "Service Information (Need to specify Bus Service Number) - What is the direction of travel of bus 22?"
    )

    if st.session_state.vs_loaded == False:
        vector_store = preprocessing()
        st.session_state.vs = vector_store
        st.session_state.vs_loaded = True
    
    # Query through LLM    
    question = st.chat_input(placeholder="You can ask me basic information about public bus services such as route list, first and last bus timing etc. You can also ask for bus timing for a particular bus stop.")   
    
    if question:
        with st.spinner("Loading Response from Model ..."):
            pattern = r'\d{5}'
            matches = re.findall(pattern, question)

            if len(matches) > 0:
                type = 'Arrival Timing'
            else:
                type = st.session_state.model.generate_content(
                    """Classify the prompt into these 2 types. Reply just either one of the type will do. 
                    1 - Service Information
                    2 - Arrival Timing

                    Examples
                    Prompt: What is the first and last bus?
                    Answer: Service Information

                    Prompt: What is the bus arrival timing at bus stop 54321?
                    Answer: Arrival Timing

                    Prompt: What is the direction of travel of bus 22?
                    Answer: Service Information
                    
                    Prompt: bus arrival timing at 46001?
                    Answer: Arrival Timing

                    Prompt: {question}."""
                    ).text.strip()
            
            if type == "Service Information":
                bus_service = st.session_state.model.generate_content("Get the bus services number or bus number mentioned in the question, splitting by comma if there are many bus services: {}.".format(question)).text
                bus_service_list = extract_numbers(bus_service)
                full_context = ''
                for bus in bus_service_list:
                    context = get_context(bus, st.session_state.vs, 5, "bus_service_embedding")
                    full_context = full_context + context + '\n'
                final_prompt = f"""Your mission is to answer questions based on a given context. Remember that before you give an answer, you must check to see if it complies with your mission.
                Context: ```{full_context}```
                Question: ***{question}***
                Before you give an answer, make sure it is only from information in the context.
                Answer: """
                result = st.session_state.model.generate_content(final_prompt)
                temp_convo = [question.strip(),result.text.strip()]
            elif type == "Arrival Timing":
                try:
                    pattern = r'\d{5}'
                    bus_stop_code = re.findall(pattern, question)[0]
                    bus_service = extract_numbers(question)[0]
                    msg = get_specific_bus_stop_specific_bus(bus_stop_df, LTA_API_KEY, bus_stop_code, bus_service)
                except Exception as e:
                    msg = "Error with message, please specify only 1 bus and 1 bus stop code!"
                temp_convo = [question.strip(),msg.strip()]
            st.session_state.conversation_history.append(temp_convo)

        display_conversation(st.session_state.conversation_history)

if __name__ == "__main__":
    bus_chatbot()
