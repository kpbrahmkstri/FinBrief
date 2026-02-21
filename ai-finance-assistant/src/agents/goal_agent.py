from typing import Dict, Any
from ..tools.goal_math import goal_projection


def goal_planning(goal_input: Dict[str, Any]) -> Dict[str, Any]:

    current = float(goal_input.get("current_savings", 0))
    target = float(goal_input.get("goal_amount", 0))
    years = float(goal_input.get("years", 0))
    expected_return = float(goal_input.get("expected_return", 0.06))
    inflation = float(goal_input.get("inflation_rate", 0.02))

    projection = goal_projection(
        current=current,
        target=target,
        years=years,
        expected_return=expected_return,
        inflation=inflation,
    )

    narrative = (
        f"Your inflation-adjusted goal is **${projection['inflation_adjusted_target']:,.2f}**.\n"
        f"If you invest your current savings, it may grow to **${projection['future_value_current']:,.2f}**.\n"
        f"To reach your goal, you would need to contribute approximately "
        f"**${projection['required_monthly_contribution']:,.2f} per month** (education-only estimate).\n"
    )

    if projection["gap"] > 0:
        narrative += f"You are currently **below** your projected target by about **${projection['gap']:,.2f}**."
    else:
        narrative += "You are on track based on current assumptions."

    return {
        "goal_metrics": projection,
        "narrative": narrative,
    }