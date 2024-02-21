import re
import numpy as np
import pandas as pd
import streamlit as st 
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

credentials = service_account.Credentials.from_service_account_file('genaisa.json')
project='meta-method-196013'
location='us-central1'

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
    df = pd.read_excel('Bus Services Info.xlsx')
    # This may take several minutes to complete.
    df["bus_service_embedding"] = df["bus_service"].apply(lambda x: get_embedding(x))
    return df

def display_conversation(messages):
    for convo in messages:
        with st.chat_message("user"):
            st.write(convo[0])
        with st.chat_message("assistant"):
            st.write(convo[1])
               
def extract_numbers(text):
    return re.findall(r'\d+', text)

def bus_chatbot():
    ### Initialise
    st.title("Singapore Public Bus Services Query")
    vector_store = preprocessing()
    llm = GenerativeModel("gemini-1.0-pro")
    ## Initialise conversation and other variables
    if 'chat' not in st.session_state:
        st.session_state.chat = llm.start_chat(history = [])

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    # Query through LLM    
    question = st.chat_input(placeholder="You can ask me basic information about public bus services such as route list, first and last bus timing etc.")   
    
    if question:
        with st.spinner("Loading Response from Model ..."):
            # Get the bus services in the prompt first.
            bus_service = st.session_state.chat.send_message("Get the bus services number mentioned in the question, splitting by comma if there are many bus services: {}.".format(question)).text
            bus_service_list = extract_numbers(bus_service)
            full_context = ''
            for bus in bus_service_list:
                context = get_context(bus, vector_store, 5, "bus_service_embedding")
                full_context = full_context + context + '\n'
            final_prompt = f"""Your mission is to answer questions based on a given context. Remember that before you give an answer, you must check to see if it complies with your mission.
            Context: ```{full_context}```
            Question: ***{question}***
            Before you give an answer, make sure it is only from information in the context.
            Answer: """
            
            result = st.session_state.chat.send_message(final_prompt)
            
            temp_convo = [question.strip(),result.text.strip()]
            st.session_state.conversation_history.append(temp_convo)

        display_conversation(st.session_state.conversation_history)

if __name__ == "__main__":
    bus_chatbot()
