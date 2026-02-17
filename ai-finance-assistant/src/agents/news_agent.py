from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import settings
from ..tools.news import fetch_rss_headlines, fetch_newsapi_headlines

SYSTEM = (
    "You summarize finance news for educational purposes. "
    "Be concise, neutral, and avoid hype. "
    "Output format:\n"
    "- Headline\n"
    "  - Why it matters (1 sentence)\n"
    "  - What to watch (1 sentence)\n"
)

def summarize_news(topic: str = "markets") -> Dict[str, Any]:
    # Prefer RSS (no API key needed). If NewsAPI key present, you can swap.
    items = fetch_rss_headlines(max_items=6)

    # Optional: if you prefer NewsAPI
    if settings.newsapi_key:
        try:
            items = fetch_newsapi_headlines(settings.newsapi_key, query=topic, max_items=6) or items
        except Exception:
            pass

    headlines_text = "\n".join([f"- {it['title']} ({it.get('published','')})" for it in items])

    llm = ChatOpenAI(model=settings.llm_model, api_key=settings.openai_api_key, temperature=0.2)
    msg = HumanMessage(content=f"Topic: {topic}\n\nHeadlines:\n{headlines_text}\n\nSummarize:")
    resp = llm.invoke([SystemMessage(content=SYSTEM), msg]).content

    return {"headlines": items, "summary": resp}