# src/tools/portfolio_metrics.py
from __future__ import annotations
from typing import Dict, Any, List


def compute_hhi(weights_pct: List[float]) -> float:
    """
    Herfindahl–Hirschman Index (HHI) on portfolio weights.
    Using weights in percent: HHI = sum((w/100)^2)
    Range: ~0 (very diversified) to 1 (single holding).
    """
    w = [(x or 0.0) / 100.0 for x in weights_pct]
    return sum([x * x for x in w])


def diversification_grade(hhi: float) -> str:
    """
    Simple rubric-style grades.
    """
    if hhi <= 0.06:
        return "A (Highly diversified)"
    if hhi <= 0.10:
        return "B (Well diversified)"
    if hhi <= 0.18:
        return "C (Moderate concentration)"
    if hhi <= 0.30:
        return "D (High concentration)"
    return "F (Very high concentration)"


def concentration_flags(positions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Flags concentrated allocations.
    positions items should have: symbol, allocation_pct
    """
    over_25 = [p for p in positions if (p.get("allocation_pct") or 0) >= 25]
    over_10 = [p for p in positions if (p.get("allocation_pct") or 0) >= 10]

    return {
        "over_25_count": len(over_25),
        "over_25": [{"symbol": p["symbol"], "allocation_pct": p["allocation_pct"]} for p in over_25],
        "top_positions": sorted(
            [{"symbol": p["symbol"], "allocation_pct": p["allocation_pct"]} for p in positions],
            key=lambda x: x["allocation_pct"],
            reverse=True
        )[:5],
        "over_10_count": len(over_10),
    }


def generate_portfolio_recommendations(hhi: float, flags: Dict[str, Any]) -> List[str]:
    recs = []
    grade = diversification_grade(hhi)

    if "F" in grade or "D" in grade:
        recs.append("Your portfolio is highly concentrated. Consider spreading exposure across more holdings or diversified funds (education-only).")
    if flags.get("over_25_count", 0) > 0:
        recs.append("One or more holdings exceed ~25% allocation. Many diversified portfolios cap single-stock exposure lower (education-only).")
    if flags.get("over_10_count", 0) >= 4:
        recs.append("Multiple holdings are each >10%. Consider whether sector overlap is increasing risk (education-only).")

    if not recs:
        recs.append("Diversification looks reasonable based on allocation concentration metrics (education-only).")

    return recs