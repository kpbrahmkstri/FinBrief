import re
from typing import Tuple

ADVICE_PATTERNS = [
    r"\bshould i buy\b",
    r"\bshould i sell\b",
    r"\bwhat should i invest in\b",
    r"\btell me the best stock\b",
    r"\bguaranteed returns\b",
]

DISCLAIMER = (
    "⚠️ **Important:** I can provide educational information, not personalized financial advice. "
    "For decisions, consider consulting a qualified financial professional.\n"
)

def needs_guardrail(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in ADVICE_PATTERNS)

def apply_guardrail(user_text: str, answer: str) -> str:
    if needs_guardrail(user_text):
        return DISCLAIMER + answer + "\n\n" + (
            "If you want, tell me your **goal + time horizon + risk tolerance**, "
            "and I can explain the **factors** people evaluate (risk, diversification, fees, liquidity)."
        )
    return DISCLAIMER + answer