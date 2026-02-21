# src/agents/tax_agent.py
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import settings
from ..tools.rag import get_rag_retriever


SYSTEM = (
    "You are a Tax Education Agent for a finance assistant. "
    "Explain US tax concepts clearly for beginners. "
    "Focus on education only: definitions, general rules, examples, and tradeoffs. "
    "Do NOT provide filing instructions or personalized tax advice. "
    "If something depends on jurisdiction or personal details, say so.\n\n"
    "When you use retrieved context, add citation markers like [1], [2]."
)

def tax_education_answer(user_message: str) -> Dict[str, Any]:
    retriever = get_rag_retriever()

    # Retrieve broader set then filter to tax category heuristically
    docs = retriever.get_relevant_documents(user_message)

    # Heuristic filter: keep docs containing "Category: Tax"
    tax_docs = [d for d in docs if "Category: Tax" in (d.page_content or "")]
    chosen = tax_docs if tax_docs else docs

    citations: List[Dict[str, str]] = []
    context_parts = []
    for i, d in enumerate(chosen[:4], start=1):
        src = d.metadata.get("source", "unknown")
        snippet = (d.page_content or "")[:900]
        context_parts.append(f"[{i}] Source: {src}\n{snippet}")
        citations.append({"id": str(i), "source": src})

    context = "\n\n".join(context_parts) if context_parts else "(no retrieved context)"

    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
    )

    prompt = (
        f"User question: {user_message}\n\n"
        f"Context:\n{context}\n\n"
        "Respond with:\n"
        "1) Direct answer\n"
        "2) Key takeaways (bullets)\n"
        "3) Common mistakes (bullets)\n"
        "4) 'When to ask a tax professional'\n"
        "Keep it educational."
    )

    resp = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=prompt),
    ]).content

    return {"answer": resp, "citations": citations}