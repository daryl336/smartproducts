import os
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import tempfile
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import DeepLake, Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.document_loaders import UnstructuredFileLoader, PyPDFLoader
from unstructured.cleaners.core import clean_extra_whitespace
import streamlit as st 

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
os.environ['GOOGLE_API_KEY']=GOOGLE_API_KEY

# Define the system message template
system_template = """Use the document to your best ability to answer the question below.

Question: {}
Answer: ## Input your answer here ##
"""

def loading_file(uploaded_file,text_splitter,embeddings):
    file_name = uploaded_file.name
    #db = DeepLake(
    #    dataset_path="./deeplake", embedding=embeddings, overwrite=True
    #)

    with st.spinner("Loading {} ...".format(file_name)):
        temp_dir = tempfile.TemporaryDirectory()
        temp_filepath = os.path.join(temp_dir.name,file_name)

        with open(temp_filepath,'wb') as f:
            f.write(uploaded_file.getvalue())
    
        loader = UnstructuredFileLoader(
            temp_filepath,
            post_processors=[clean_extra_whitespace],
        )
        doc = loader.load()   
        texts = text_splitter.split_documents(doc)
        
        all_texts = [i.page_content for i in texts]
        db = Chroma.from_texts(all_texts, embeddings)

        #reader = PdfReader(temp_filepath) 
        #file_data = []
        #for i in range(len(reader.pages)):
        #    page = reader.pages[i]
        #    text = page.extract_text()
        #    file_data.append(text)
        #file_data = " ".join(file_data)
        #docs = text_splitter.create_documents([file_data])
        #db = Chroma.from_documents(docs, embeddings)
        
        #pdf_loader = PyPDFLoader(temp_filepath)
        #pages = pdf_loader.load_and_split()
        
        #context = "\n\n".join(str(p.page_content) for p in pages)
        #texts = text_splitter.split_text(context)
        #db = Chroma.from_texts(texts, embeddings)
        
        
    return db

def display_conversation(messages):
    for convo in messages:
        with st.chat_message("user"):
            st.write(convo[0])
        with st.chat_message("assistant"):
            st.write(convo[1])
               

def submit():
    st.session_state.question = st.session_state.widget
    st.session_state.widget = ''

def doc_chatbot():
    ### Initialise
    #text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n","\n","\t"],chunk_size=100,chunk_overlap=20)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=2000)
    #text_splitter = CharacterTextSplitter(chunk_size=10000, chunk_overlap=2000)
    #embeddings = LlamaCppEmbeddings(model_path = model_path)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # Make sure the model path is correct for your system!
    llm = ChatGoogleGenerativeAI(model="gemini-pro",temperature=0.2,convert_system_message_to_human=True)
    #llm = GoogleGenerativeAI(model="gemini-pro")
    memory = ConversationBufferMemory(memory_key='chat_history',return_messages=True)

    st.title("Document Chatbot")

    uploaded_file = st.file_uploader(label='Upload any text Document!')

    ## Initialise conversation and other variables
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    if 'file_loaded' not in st.session_state:
        st.session_state.file_loaded = False

    if 'question' not in st.session_state:
        st.session_state.question = ''

    if st.session_state.file_loaded == False:
        if uploaded_file is not None:
            db = loading_file(uploaded_file,text_splitter,embeddings)
            st.session_state.db = db
            st.success("File Loaded Successfully!!")
            st.session_state.file_loaded = True
    else:
        if uploaded_file is None:
            st.session_state.file_loaded = False
        else:
            db = st.session_state.db
            st.success("File Loaded Successfully!!")

    # Query through LLM    
    question = st.chat_input(placeholder="Type your question here!", disabled=not uploaded_file)   
    
    if question:
        with st.spinner("Loading Response from Model ..."):
            final_query = system_template.format(question) 
            convo_qa = ConversationalRetrievalChain.from_llm(llm=llm, retriever=db.as_retriever(), memory=memory)
            result = convo_qa({'question':final_query}, return_only_outputs=True)
            
            if "Question:" in result['answer']:
                final_result = result['answer'].split('Question:')[0].strip()
            else:
                final_result = result['answer']
            
            #qa_chain = RetrievalQA.from_chain_type(
            #    llm,
            #    retriever=db.as_retriever(search_kwargs={"k":5}),
            #    return_source_documents=False,
            #    memory=memory
            #)
            #result = qa_chain({"query": final_query})
            #final_result = result["result"]
            
            temp_convo = [question.strip(),final_result.strip().replace("<|im_end|>","")]
            st.session_state.conversation_history.append(temp_convo)

        display_conversation(st.session_state.conversation_history)
    
def main():
    st.set_page_config(page_title="Google API functions!", layout="wide")    
    functions = ["Document Chatbot", ]
    page = st.sidebar.selectbox("Choose a function", functions)
    if page == functions[0]:
        doc_chatbot()
    #elif page == functions[1]:
    #    transcription()

if __name__ == "__main__":
    main()