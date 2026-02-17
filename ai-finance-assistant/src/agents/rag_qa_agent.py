from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import settings
from ..tools.rag import get_rag_retriever

SYSTEM = (
    "You are a helpful finance education assistant. "
    "Explain clearly for beginners. "
    "Use the provided context snippets as sources. "
    "If the context is insufficient, say so and provide safe general guidance."
)

def rag_qa(user_message: str) -> Dict[str, Any]:
    retriever = get_rag_retriever()
    docs = retriever.get_relevant_documents(user_message)

    citations: List[Dict[str, str]] = []
    context_parts = []
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source", "unknown")
        snippet = d.page_content[:800]
        context_parts.append(f"[{i}] Source: {src}\n{snippet}")
        citations.append({"id": str(i), "source": src})

    context = "\n\n".join(context_parts) if context_parts else "(no retrieved context)"

    llm = ChatOpenAI(model=settings.llm_model, api_key=settings.openai_api_key, temperature=0.2)
    msgs = [
        SystemMessage(content=SYSTEM),
        HumanMessage(content=f"Question: {user_message}\n\nContext:\n{context}\n\n"
                            "Answer with clarity and include citation markers like [1], [2] where used.")
    ]
    resp = llm.invoke(msgs).content

    return {"answer": resp, "citations": citations}