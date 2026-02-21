from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import settings
from ..tools.rag import get_rag_retriever

SYSTEM = (
    "You are a Finance Q&A education assistant. "
    "Use retrieved context only. If context is insufficient, say so clearly. "
    "Provide clear explanations for beginners. "
    "Add citations like [1], [2] that map to the sources provided."
)

def rag_qa(user_message: str, category: Optional[str] = None) -> Dict[str, Any]:
    retriever = get_rag_retriever(category=category)
    docs = retriever.get_relevant_documents(user_message)

    citations: List[Dict[str, str]] = []
    context_parts = []
    for i, d in enumerate(docs[:4], start=1):
        meta = d.metadata or {}
        src = meta.get("source", "unknown")
        title = meta.get("title", "Untitled")
        cat = meta.get("category", "Uncategorized")

        snippet = (d.page_content or "")[:900]
        context_parts.append(f"[{i}] Title: {title}\nCategory: {cat}\nSource: {src}\n{snippet}")
        citations.append({"id": str(i), "title": title, "category": cat, "source": src})

    context = "\n\n".join(context_parts) if context_parts else "(no retrieved context)"

    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
    )

    prompt = (
        f"User question: {user_message}\n\n"
        f"Retrieved context:\n{context}\n\n"
        "Answer in this format:\n"
        "1) Direct answer (with citations like [1])\n"
        "2) Key takeaways (bullets)\n"
        "3) Common misconceptions (bullets)\n"
        "4) What to do next (education-only)\n"
    )

    answer = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)]).content
    return {"answer": answer, "citations": citations}