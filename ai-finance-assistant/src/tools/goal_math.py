from __future__ import annotations
from typing import Dict
import math


def future_value_lump_sum(pv: float, rate: float, years: float) -> float:
    return pv * ((1 + rate) ** years)


def required_monthly_contribution(
    target: float,
    current: float,
    annual_rate: float,
    years: float,
) -> float:
    """
    Solve for monthly contribution needed to reach target.
    """
    r = annual_rate / 12
    n = years * 12

    if r == 0:
        return max((target - current) / n, 0)

    fv_current = current * ((1 + r) ** n)

    numerator = target - fv_current
    denominator = (((1 + r) ** n - 1) / r)

    if denominator <= 0:
        return 0.0

    return max(numerator / denominator, 0)


def inflation_adjust(value: float, inflation: float, years: float) -> float:
    return value * ((1 + inflation) ** years)


def goal_projection(
    current: float,
    target: float,
    years: float,
    expected_return: float,
    inflation: float,
) -> Dict:

    infl_adj_target = inflation_adjust(target, inflation, years)

    fv_current = future_value_lump_sum(current, expected_return, years)

    monthly_needed = required_monthly_contribution(
        infl_adj_target,
        current,
        expected_return,
        years,
    )

    gap = infl_adj_target - fv_current

    return {
        "inflation_adjusted_target": infl_adj_target,
        "future_value_current": fv_current,
        "required_monthly_contribution": monthly_needed,
        "gap": gap,
    }