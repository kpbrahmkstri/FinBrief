from typing import List, Dict, Any
import math

def compute_portfolio_metrics(
    holdings: List[Dict[str, Any]],
    quotes: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    holdings: [{"symbol":"AAPL","quantity":10}, ...]
    quotes: {"AAPL":{"last_price":...}, ...}
    """
    quotes = quotes or {}
    rows = []
    total_value = 0.0

    for h in holdings:
        sym = str(h["symbol"]).upper()
        qty = float(h.get("quantity", 0))
        price = None
        q = quotes.get(sym, {})
        if isinstance(q, dict):
            price = q.get("last_price")

        # if no price, treat value as 0 but still keep row
        value = float(price) * qty if price is not None else 0.0
        total_value += value
        rows.append({"symbol": sym, "quantity": qty, "price": price, "value": value})

    # allocation %
    for r in rows:
        r["allocation_pct"] = (r["value"] / total_value * 100.0) if total_value > 0 else 0.0

    # simple diversification heuristic: effective number of holdings (1/sum(w^2))
    weights = [(r["value"] / total_value) for r in rows if total_value > 0 and r["value"] > 0]
    hhi = sum([w*w for w in weights]) if weights else 1.0
    effective_n = (1.0 / hhi) if hhi > 0 else 1.0

    # heuristic risk based on concentration
    # (higher effective_n => lower concentration risk)
    if effective_n >= 10:
        concentration_risk = "low"
    elif effective_n >= 5:
        concentration_risk = "moderate"
    else:
        concentration_risk = "high"

    return {
        "total_value": total_value,
        "positions": rows,
        "effective_holdings": effective_n,
        "concentration_risk": concentration_risk,
    }