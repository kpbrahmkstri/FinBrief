from typing import Dict, Any, List, Optional
import feedparser
import requests

DEFAULT_RSS_FEEDS = [
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",   # WSJ Markets (RSS)
    "https://www.investing.com/rss/news_25.rss",       # Investing.com market news RSS
    "https://www.marketwatch.com/rss/topstories",      # MarketWatch top stories
]

def fetch_rss_headlines(max_items: int = 8, feeds: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    feeds = feeds or DEFAULT_RSS_FEEDS
    items: List[Dict[str, Any]] = []

    for url in feeds:
        d = feedparser.parse(url)
        for e in d.entries[:max_items]:
            items.append({
                "title": getattr(e, "title", ""),
                "link": getattr(e, "link", ""),
                "published": getattr(e, "published", ""),
                "source": url,
            })

    # de-dup by title
    seen = set()
    uniq = []
    for it in items:
        t = it["title"]
        if t and t not in seen:
            seen.add(t)
            uniq.append(it)
    return uniq[:max_items]

def fetch_newsapi_headlines(api_key: str, query: str = "markets", max_items: int = 8) -> List[Dict[str, Any]]:
    if not api_key:
        return []

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "pageSize": max_items,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": api_key,
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    articles = data.get("articles", [])
    out = []
    for a in articles[:max_items]:
        out.append({
            "title": a.get("title", ""),
            "link": a.get("url", ""),
            "published": a.get("publishedAt", ""),
            "source": (a.get("source") or {}).get("name", "NewsAPI"),
        })
    return out