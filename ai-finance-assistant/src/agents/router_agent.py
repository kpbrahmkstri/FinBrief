from typing import Dict, Any, List
import re

TAX_KEYWORDS = [
    "tax", "taxes", "capital gains", "short-term", "long-term",
    "wash sale", "tax-loss", "harvesting", "1099", "w-2", "w2",
    "deduction", "deductions", "credits", "tax credit", "withholding",
    "ira", "roth", "traditional ira", "401k", "403b", "hsa", "fsa",
    "brokerage account tax", "dividend tax", "qualified dividend",
]

def classify_intent(user_message: str) -> Dict[str, Any]:
    t = user_message.lower()

    intents: List[str] = []
    if any(k in t for k in ["portfolio", "allocation", "diversification", "holdings"]):
        intents.append("portfolio")
    if any(k in t for k in ["price", "quote", "ticker", "market cap", "stock price"]):
        intents.append("market")
    if any(k in t for k in ["goal", "retirement", "save", "saving", "target", "projection"]):
        intents.append("goals")
    if any(k in t for k in ["news", "headline", "what happened today", "latest"]):
        intents.append("news")
    if any(k in t for k in TAX_KEYWORDS):
        intents.append("tax")
    if any(k in t for k in ["what is", "explain", "difference between", "how does", "define"]):
        intents.append("qa")


    # if no obvious, default to QA
    if not intents:
        intents = ["qa"]

    if len(intents) == 1:
        intent = intents[0]
    else:
        intent = "mixed"

    required_agents = []
    # mapping to node names
    if intent == "mixed":
        required_agents = list(dict.fromkeys(intents))  # unique preserve order
    else:
        required_agents = [intent]

    return {
        "intent": intent,
        "sub_intents": intents if intent == "mixed" else [intent],
        "required_agents": required_agents,
    }