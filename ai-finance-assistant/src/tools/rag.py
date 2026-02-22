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

def _parse_header_fields(text: str) -> tuple[str | None, str | None]:
    """
    Extracts:
      Title: ...
      Category: ...
    from the top of each KB txt file.
    """
    title = None
    category = None
    for line in (text or "").splitlines()[:20]:
        line_stripped = line.strip()
        if line_stripped.lower().startswith("title:"):
            title = line_stripped.split(":", 1)[1].strip()
        if line_stripped.lower().startswith("category:"):
            category = line_stripped.split(":", 1)[1].strip()
    return title, category


def _load_kb_documents(kb_dir) -> List:
    from pathlib import Path
    from langchain_core.documents import Document

    kb_path = Path(kb_dir) if not isinstance(kb_dir, Path) else kb_dir
    if not kb_path.exists():
        raise FileNotFoundError(f"KB_DIR not found: {kb_path}")

    docs = []
    for path in kb_path.glob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        title, category = _parse_header_fields(text)

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": path.name,          # filename
                    "title": title or path.stem,  # fallback
                    "category": category or "Uncategorized",
                },
            )
        )

    if not docs:
        raise ValueError(f"No .txt files found in KB_DIR: {kb_path}")

    return docs

def build_or_load_faiss() -> FAISS:
    """
    Loads FAISS index if (index.faiss AND index.pkl) exist.
    Otherwise builds from KB text files and saves locally.
    """
    global _VECTORSTORE
    if _VECTORSTORE is not None:
        return _VECTORSTORE

    # Ensure settings.faiss_index_dir is a Path object
    index_dir = Path(settings.faiss_index_dir) if not isinstance(settings.faiss_index_dir, Path) else settings.faiss_index_dir
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


def get_rag_retriever(category: str | None = None):
    vs = build_or_load_faiss()
    if category and category != "All":
        return vs.as_retriever(search_kwargs={"k": 5, "filter": {"category": category}})
    return vs.as_retriever(search_kwargs={"k": 5})