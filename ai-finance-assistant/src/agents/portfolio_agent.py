from typing import Dict, Any, List
from ..tools.portfolio_math import compute_portfolio_metrics

def portfolio_analysis(holdings: List[Dict[str, Any]], quotes: Dict[str, Any] | None = None) -> Dict[str, Any]:
    metrics = compute_portfolio_metrics(holdings, quotes=quotes or {})
    # Add beginner-friendly narrative
    total = metrics["total_value"]
    eff = metrics["effective_holdings"]
    risk = metrics["concentration_risk"]
    narrative = (
        f"Your portfolio value (based on available prices) is **${total:,.2f}**.\n"
        f"Estimated diversification (effective holdings): **{eff:.2f}**.\n"
        f"Concentration risk looks **{risk}** (heuristic based on weights).\n"
    )
    return {"metrics": metrics, "narrative": narrative}