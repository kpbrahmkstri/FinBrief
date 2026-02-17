from typing import Dict, Any, List
import math

ASSUMPTION_RATES = {
    "conservative": 0.03,
    "moderate": 0.06,
    "aggressive": 0.09,
}

def project_goal(target: float, monthly: float, years: float, assumption: str) -> Dict[str, Any]:
    r_annual = ASSUMPTION_RATES.get(assumption, 0.06)
    r_monthly = r_annual / 12.0
    n = int(years * 12)

    balances: List[float] = []
    bal = 0.0
    for _ in range(n):
        bal = bal * (1 + r_monthly) + monthly
        balances.append(bal)

    reached = next((i for i, b in enumerate(balances, start=1) if b >= target), None)

    return {
        "assumption": assumption,
        "annual_rate": r_annual,
        "months": n,
        "balances": balances,
        "reached_month": reached,
        "final_balance": balances[-1] if balances else 0.0,
    }

def scenario_projection(target: float, monthly: float, years: float) -> Dict[str, Any]:
    scenarios = {}
    for a in ["conservative", "moderate", "aggressive"]:
        scenarios[a] = project_goal(target, monthly, years, a)
    return scenarios