from typing import Dict, Any, List
from ..tools.portfolio_math import compute_portfolio_metrics
from ..tools.portfolio_metrics import compute_hhi, diversification_grade, concentration_flags, generate_portfolio_recommendations

from typing import List, Dict, Any

def portfolio_analysis(holdings: List[Dict[str, Any]], quotes: Dict[str, Any] | None = None) -> Dict[str, Any]:
    metrics = compute_portfolio_metrics(holdings, quotes=quotes or {})

    # --- NEW: HHI + grade + flags + recommendations ---
    positions = metrics.get("positions", []) or []
    weights = [p.get("allocation_pct", 0.0) for p in positions]

    hhi = compute_hhi(weights) if weights else None
    grade = diversification_grade(hhi) if isinstance(hhi, (int, float)) else None
    flags = concentration_flags(positions) if positions else {}
    recs = generate_portfolio_recommendations(hhi, flags) if isinstance(hhi, (int, float)) else []

    metrics["hhi"] = hhi
    metrics["diversification_grade"] = grade
    metrics["concentration_flags"] = flags
    metrics["recommendations"] = recs

    # --- Narrative (more reviewer-friendly) ---
    total = metrics.get("total_value", 0.0)
    eff = metrics.get("effective_holdings", 0.0)
    risk = metrics.get("concentration_risk", "Unknown")

    narrative = (
        f"Your portfolio value (based on available prices) is **${total:,.2f}**.\n"
        f"Estimated diversification (effective holdings): **{eff:.2f}**.\n"
        f"Concentration risk looks **{risk}** (heuristic).\n"
    )

    if isinstance(hhi, (int, float)) and grade:
        narrative += f"HHI concentration score: **{hhi:.3f}** → **{grade}**.\n"

    if flags and flags.get("over_25_count", 0) > 0:
        narrative += f"⚠️ One or more holdings exceed **25%** allocation.\n"

    if recs:
        narrative += "\n**Education-only suggestions:**\n" + "\n".join([f"- {r}" for r in recs])

    return {"metrics": metrics, "narrative": narrative}