# src/tools/rag.py
from __future__ import annotations

from pathlib import Path
from typing import Optional, List

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from ..config import settings

_VECTORSTORE: Optional[FAISS] = None


def _load_kb_documents(kb_dir: str) -> List:
    kb_path = Path(kb_dir)
    if not kb_path.exists():
        raise FileNotFoundError(f"KB_DIR not found: {kb_dir}")

    docs = []
    for path in kb_path.glob("*.txt"):
        loader = TextLoader(str(path), encoding="utf-8")
        docs.extend(loader.load())

    if not docs:
        raise ValueError(f"No .txt files found in KB_DIR: {kb_dir}")

    return docs


def build_or_load_faiss() -> FAISS:
    """
    Loads FAISS index if (index.faiss AND index.pkl) exist.
    Otherwise builds from KB text files and saves locally.
    """
    global _VECTORSTORE
    if _VECTORSTORE is not None:
        return _VECTORSTORE

    index_dir = Path(settings.faiss_index_dir)
    faiss_file = index_dir / "index.faiss"
    pkl_file = index_dir / "index.pkl"

    embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)

    # ✅ Only load if BOTH files exist
    if faiss_file.exists() and pkl_file.exists():
        _VECTORSTORE = FAISS.load_local(
            str(index_dir),
            embeddings=embeddings,
            allow_dangerous_deserialization=True,
        )
        return _VECTORSTORE

    # ✅ Otherwise build
    docs = _load_kb_documents(settings.kb_dir)

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    chunks = splitter.split_documents(docs)

    _VECTORSTORE = FAISS.from_documents(chunks, embeddings)
    index_dir.mkdir(parents=True, exist_ok=True)
    _VECTORSTORE.save_local(str(index_dir))
    return _VECTORSTORE


def get_rag_retriever():
    vs = build_or_load_faiss()
    return vs.as_retriever(search_kwargs={"k": 4})