from typing import Dict, Any, List
import yfinance as yf

from .cache import SQLiteTTLCache

def fetch_quotes(symbols: List[str], cache: SQLiteTTLCache, ttl_seconds: int) -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    for sym in symbols:
        key = f"quote:{sym.upper()}"
        cached = cache.get(key)
        if cached:
            cached["source"] = "cache"
            results[sym.upper()] = cached
            continue

        try:
            t = yf.Ticker(sym)
            info = t.fast_info  # fast + reliable for many tickers
            payload = {
                "symbol": sym.upper(),
                "last_price": float(info.get("last_price")) if info.get("last_price") is not None else None,
                "previous_close": float(info.get("previous_close")) if info.get("previous_close") is not None else None,
                "market_cap": float(info.get("market_cap")) if info.get("market_cap") is not None else None,
                "currency": info.get("currency"),
                "source": "yfinance",
            }
            cache.set(key, payload, ttl_seconds)
            results[sym.upper()] = payload
        except Exception as e:
            # fallback: cached if exists (even if expired is not available here), otherwise error
            results[sym.upper()] = {
                "symbol": sym.upper(),
                "error": f"Failed to fetch quote: {e}",
                "source": "error",
            }

    return results