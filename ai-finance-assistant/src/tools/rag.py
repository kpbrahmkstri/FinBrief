import os
from typing import Optional
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from ..config import settings

_VECTORSTORE: Optional[FAISS] = None

def build_or_load_faiss() -> FAISS:
    global _VECTORSTORE
    if _VECTORSTORE is not None:
        return _VECTORSTORE

    # If index exists, load it
    if os.path.isdir(settings.faiss_index_dir) and os.listdir(settings.faiss_index_dir):
        _VECTORSTORE = FAISS.load_local(
            settings.faiss_index_dir,
            embeddings=OpenAIEmbeddings(api_key=settings.openai_api_key),
            allow_dangerous_deserialization=True,
        )
        return _VECTORSTORE

    # Else build from KB text files
    docs = []
    for fname in os.listdir(settings.kb_dir):
        if fname.endswith(".txt"):
            path = os.path.join(settings.kb_dir, fname)
            loader = TextLoader(path, encoding="utf-8")
            docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)
    _VECTORSTORE = FAISS.from_documents(chunks, embeddings)
    os.makedirs(settings.faiss_index_dir, exist_ok=True)
    _VECTORSTORE.save_local(settings.faiss_index_dir)
    return _VECTORSTORE

def get_rag_retriever():
    vs = build_or_load_faiss()
    return vs.as_retriever(search_kwargs={"k": 4})