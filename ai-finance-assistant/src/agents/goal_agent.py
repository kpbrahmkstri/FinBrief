from typing import Dict, Any
from ..tools.goal_math import scenario_projection

def goal_planning(target: float, monthly: float, years: float) -> Dict[str, Any]:
    scenarios = scenario_projection(target=target, monthly=monthly, years=years)
    # brief summary
    moderate = scenarios["moderate"]
    reached = moderate["reached_month"]
    summary = (
        f"Using a **moderate** return assumption (~{moderate['annual_rate']*100:.1f}%/yr), "
        f"you {'could reach the goal in ~'+str(reached)+' months' if reached else 'may not reach the goal within the chosen horizon'}."
    )
    return {"scenarios": scenarios, "summary": summary}