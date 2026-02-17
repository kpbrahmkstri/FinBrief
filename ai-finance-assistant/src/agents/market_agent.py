from typing import Dict, Any, List
from ..config import settings
from ..tools.cache import SQLiteTTLCache
from ..tools.market_data import fetch_quotes

def market_intelligence(symbols: List[str]) -> Dict[str, Any]:
    cache = SQLiteTTLCache(settings.cache_db_path)
    data = fetch_quotes(symbols, cache=cache, ttl_seconds=settings.market_cache_ttl_seconds)
    return {"quotes": data}