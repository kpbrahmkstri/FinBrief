# src/agents/news_agent.py
from __future__ import annotations

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from ..config import settings
from ..tools.news import fetch_news

SYSTEM = (
    "You are a Financial News Synthesizer. "
    "You summarize and contextualize financial news for a general audience. "
    "Be factual. Do not hallucinate numbers or events. "
    "If details are missing, say so. "
    "Do not provide personalized financial advice.\n\n"
    "Output format:\n"
    "### Top stories\n"
    "- Headline — why it matters — what to watch next (include citation tags like [1])\n\n"
    "### Themes & signal\n"
    "- 3-5 bullets synthesizing patterns across stories\n\n"
    "### Risk notes\n"
    "- 2-3 bullets: what could change the narrative\n"
)

def synthesize_news(topic: str = "All", limit: int = 10) -> Dict[str, Any]:
    items = fetch_news(topic=topic, limit=limit)

    citations: List[Dict[str, str]] = []
    context_lines = []
    for i, it in enumerate(items, start=1):
        citations.append(
            {
                "id": str(i),
                "title": it.get("title", "Untitled"),
                "source": it.get("source", "unknown"),
                "url": it.get("url", ""),
                "published": it.get("published", ""),
            }
        )
        context_lines.append(
            f"[{i}] {it.get('title','')}\n"
            f"Source: {it.get('source','')}\n"
            f"Published: {it.get('published','')}\n"
            f"URL: {it.get('url','')}"
        )

    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
    )

    if not items:
        return {
            "summary": "No headlines were retrieved for the selected topic. Try **All** or increase the limit.",
            "items": [],
            "citations": [],
            "topic": topic,
        }

    prompt = (
        f"Topic filter: {topic}\n"
        f"Headlines:\n\n" + "\n\n".join(context_lines) + "\n\n"
        "Synthesize these headlines. Use citations [1], [2], etc when referencing a specific story."
    )

    summary = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)]).content

    return {
        "summary": summary,
        "items": items,
        "citations": citations,
        "topic": topic,
    }

def summarize_news(topic: str = "All", limit: int = 10):
    return synthesize_news(topic=topic, limit=limit)