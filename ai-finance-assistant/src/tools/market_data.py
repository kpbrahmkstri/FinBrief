# src/tools/market_data.py
from typing import Dict, Any, List, Optional
import time
import yfinance as yf

from .cache import SQLiteTTLCache


def _safe_float(x) -> Optional[float]:
    try:
        return float(x) if x is not None else None
    except Exception:
        return None

def _get_daily_closes(ticker: yf.Ticker, days: int = 5):
    try:
        daily = ticker.history(period=f"{days}d", interval="1d")
        if daily is None or daily.empty:
            return []
        closes = daily["Close"].dropna().tolist()
        return [float(x) for x in closes][-days:]
    except Exception:
        return []

def _get_daily_closes_with_dates(ticker: yf.Ticker, days: int = 5):
    try:
        daily = ticker.history(period=f"{days}d", interval="1d")
        if daily is None or daily.empty:
            return {"dates": [], "prices": []}
        daily = daily[daily["Close"].notna()]
        closes = daily["Close"].tolist()
        dates = daily.index.strftime("%Y-%m-%d").tolist()
        return {
            "dates": dates[-days:],
            "prices": [float(x) for x in closes][-days:]
        }
    except Exception:
        return {"dates": [], "prices": []}

def _get_last_from_history(ticker: yf.Ticker) -> Dict[str, Optional[float]]:
    """
    Most reliable path for "price now":
    - Try 1-minute candles for the last trading session
    - Fallback to daily close
    Returns: {"last_price": ..., "previous_close": ...}
    """
    # 1) Try intraday 1m (best for current/most recent price)
    try:
        intraday = ticker.history(period="1d", interval="1m")
        if intraday is not None and not intraday.empty:
            close_series = intraday["Close"].dropna()
            if len(close_series) >= 1:
                last_price = _safe_float(close_series.iloc[-1])
                # previous close from the prior minute if available
                prev_close = _safe_float(close_series.iloc[-2]) if len(close_series) >= 2 else None
                return {"last_price": last_price, "previous_close": prev_close}
    except Exception:
        pass

    # 2) Fallback to daily history
    try:
        daily = ticker.history(period="5d", interval="1d")
        if daily is not None and not daily.empty:
            close_series = daily["Close"].dropna()
            if len(close_series) >= 1:
                last_price = _safe_float(close_series.iloc[-1])
                prev_close = _safe_float(close_series.iloc[-2]) if len(close_series) >= 2 else None
                return {"last_price": last_price, "previous_close": prev_close}
    except Exception:
        pass

    return {"last_price": None, "previous_close": None}


def fetch_quotes(symbols: List[str], cache: SQLiteTTLCache, ttl_seconds: int) -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    for raw in symbols:
        sym = raw.upper().strip()
        if not sym:
            continue

        key = f"quote:{sym}"
        cached = cache.get(key)
        if cached:
            cached["cache_hit"] = True
            results[sym] = cached
            continue

        payload = {
            "symbol": sym,
            "last_price": None,
            "previous_close": None,
            "market_cap": None,
            "currency": None,
            "source": "yfinance",
            "cache_hit": False,
            "fetched_at": int(time.time()),
        }

        try:
            t = yf.Ticker(sym)

            # Try fast_info (sometimes works)
            try:
                fi = getattr(t, "fast_info", None)
                if fi:
                    payload["last_price"] = _safe_float(fi.get("last_price"))
                    payload["previous_close"] = _safe_float(fi.get("previous_close"))
                    payload["market_cap"] = _safe_float(fi.get("market_cap"))
                    payload["currency"] = fi.get("currency")
                    history_data = _get_daily_closes_with_dates(t, days=5)
                    payload["history_5d"] = history_data.get("prices", [])
                    payload["history_dates"] = history_data.get("dates", [])

                    # percent change
                    lp = payload.get("last_price")
                    pc = payload.get("previous_close")

                    # If previous_close missing, try to infer from daily closes
                    if pc is None:
                        hist = payload.get("history_5d") or []
                        if len(hist) >= 2:
                            pc = hist[-2]
                            payload["previous_close"] = pc

                    if isinstance(lp, (int, float)) and isinstance(pc, (int, float)) and pc != 0:
                        payload["pct_change"] = ((lp - pc) / pc) * 100.0
                    else:
                        payload["pct_change"] = None
            except Exception:
                pass

            # If still missing, use history (more reliable)
            if payload["last_price"] is None:
                hist_vals = _get_last_from_history(t)
                payload["last_price"] = hist_vals["last_price"]
                # only set previous_close if not already present
                if payload["previous_close"] is None:
                    payload["previous_close"] = hist_vals["previous_close"]

            # Final validation
            if payload["last_price"] is None:
                raise ValueError("No price returned from Yahoo Finance (may be rate-limited or blocked).")

            cache.set(key, payload, ttl_seconds)
            results[sym] = payload

        except Exception as e:
            results[sym] = {
                "symbol": sym,
                "error": f"Failed to fetch quote: {e}",
                "source": "error",
                "cache_hit": False,
                "fetched_at": int(time.time()),
            }

    return results