import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import OllamaEmbeddings

def load_abstracts(abstract_file='abstracts.txt'):
    with open(abstract_file, "r") as file:
        abstract_text = file.read()
    
    abstracts = abstract_text.split("\n\n")

    return abstracts

def split_abstracts(abstracts):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    abstracts_docs = splitter.create_documents(abstracts)
    abstract_splits = splitter.split_documents(abstracts_docs)
    return abstract_splits

def get_embedding(abstract_splits):
    # embedding_model = 
    vectorstore = FAISS.from_documents(
        documents=abstract_splits,
        embedding=OllamaEmbeddings(model="llama3.1:8b")
    )
    print("got here")
    # get top 3 most relevant documents
    return vectorstore.as_retriever(k=3)

# Test
abstracts = load_abstracts(abstract_file='abstracts.txt')
# print(abstracts[0])
abstract_splits = split_abstracts(abstracts)
vectorstore = get_embedding(abstract_splits)

question = "Mention some genes?"
docs = vectorstore.similarity_search(question)
context = docs[0].page_content

print(context)