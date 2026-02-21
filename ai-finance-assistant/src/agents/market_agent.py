from ..tools.market_data import fetch_quotes
from ..tools.cache import SQLiteTTLCache
from ..config import settings

def market_intelligence(symbols):
    cache = SQLiteTTLCache(settings.cache_db_path)
    quotes = fetch_quotes(symbols, cache, settings.market_cache_ttl_seconds)
    return {"quotes": quotes}