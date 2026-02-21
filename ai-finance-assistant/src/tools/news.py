# src/tools/news.py
from __future__ import annotations

from typing import Dict, List, Any
import re
import feedparser
from datetime import datetime, timezone

RSS_SOURCES: Dict[str, str] = {
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "Yahoo Finance": "https://finance.yahoo.com/rss/",
    "MarketWatch Top Stories": "https://www.marketwatch.com/rss/topstories",
    "Investing.com News": "https://www.investing.com/rss/news.rss",
}

TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "All": [],
    "Markets": ["stocks", "market", "s&p", "nasdaq", "dow", "equities", "selloff", "rally"],
    "Macro": ["inflation", "rates", "fed", "cpi", "jobs", "gdp", "yield", "treasury"],
    "Tech": ["apple", "microsoft", "google", "amazon", "meta", "nvidia", "ai", "chip"],
    "Crypto": ["bitcoin", "ethereum", "crypto", "sec", "etf", "coinbase"],
    "ETFs": ["etf", "index fund", "vanguard", "ishares", "spy", "qqq"],
    "Earnings": ["earnings", "guidance", "revenue", "eps", "quarter", "profit", "loss"],
}

def _norm_title(t: str) -> str:
    t = (t or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9\s%&\-\.,:]", "", t)
    return t

def _parse_published(entry: Any) -> str:
    # feedparser entries often have published / updated
    for key in ("published", "updated", "pubDate"):
        val = getattr(entry, key, None)
        if val:
            return str(val)
    return ""

def _topic_match(title: str, topic: str) -> bool:
    if topic == "All":
        return True
    kws = [k.lower() for k in TOPIC_KEYWORDS.get(topic, [])]
    if not kws:
        return True
    t = (title or "").lower()
    return any(k in t for k in kws)

def fetch_news(topic: str = "All", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Returns a list of items with:
      title, url, published, source
    """
    items: List[Dict[str, Any]] = []

    # Pull more than limit, then filter/dedup down
    per_source_cap = max(limit * 3, 20)

    for source, url in RSS_SOURCES.items():
        feed = feedparser.parse(url)
        for e in getattr(feed, "entries", [])[:per_source_cap]:
            title = getattr(e, "title", "") or ""
            link = getattr(e, "link", "") or ""
            published = _parse_published(e)

            if not title or not link:
                continue
            if not _topic_match(title, topic):
                continue

            items.append(
                {
                    "title": title.strip(),
                    "url": link.strip(),
                    "published": published,
                    "source": source,
                }
            )

    # Dedup by normalized title
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for it in items:
        key = _norm_title(it["title"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(it)

    # Keep only the newest-looking items first (if dates missing, they naturally fall behind)
    # We don't parse all date formats perfectly—RSS is inconsistent—so we do a light heuristic.
    def _date_score(published: str) -> int:
        if not published:
            return 0
        return 1

    deduped.sort(key=lambda x: (_date_score(x.get("published", ""))), reverse=True)

    return deduped[:limit]