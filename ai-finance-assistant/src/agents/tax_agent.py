# src/agents/tax_agent.py
from __future__ import annotations

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from ..config import settings
from ..tools.rag import get_rag_retriever


SYSTEM = (
    "You are a Tax Education Agent. You provide educational explanations only. "
    "Do NOT provide personalized tax advice. Do NOT guess rates/thresholds. "
    "If the retrieved context doesn't contain enough detail, say so and suggest what to verify.\n\n"
    "Always use citations like [1], [2] tied to the sources list.\n\n"
    "Answer format:\n"
    "### Education-only note\n"
    "### Direct answer\n"
    "### Example\n"
    "### Common pitfalls / edge cases\n"
    "### Relevant account types (if applicable)\n"
    "### What to do next (education-only)\n"
)

def tax_qa(user_message: str) -> Dict[str, Any]:
    # Hard filter to Tax category only
    retriever = get_rag_retriever(category="Tax")
    docs = retriever.get_relevant_documents(user_message)

    citations: List[Dict[str, str]] = []
    context_parts = []

    for i, d in enumerate(docs[:5], start=1):
        meta = d.metadata or {}
        title = meta.get("title", "Untitled")
        src = meta.get("source", "unknown")
        cat = meta.get("category", "Uncategorized")

        # enforce category guard (extra safety)
        if str(cat).lower() != "tax":
            continue

        snippet = (d.page_content or "")[:900]
        context_parts.append(
            f"[{i}] Title: {title}\nCategory: {cat}\nSource: {src}\n{snippet}"
        )
        citations.append({"id": str(i), "title": title, "category": cat, "source": src})

    context = "\n\n".join(context_parts) if context_parts else "(no retrieved context)"

    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0.15,
    )

    prompt = (
        f"User question: {user_message}\n\n"
        f"Retrieved context (Tax only):\n{context}\n\n"
        "If the user asks for a comparison (e.g., Roth vs Traditional vs Taxable), include a small markdown table.\n"
        "If the question depends on location, filing status, income thresholds, or current-year rules and those are "
        "not present in context, explicitly say what info is missing.\n"
    )

    answer = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)]).content

    return {"answer": answer, "citations": citations}

def tax_education_answer(user_message: str):
    return tax_qa(user_message)