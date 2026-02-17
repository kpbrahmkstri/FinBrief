from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict, Literal

Intent = Literal["qa", "portfolio", "market", "goals", "news", "mixed", "unknown"]

class FinanceState(TypedDict, total=False):
    # raw user input
    user_message: str

    # router outputs
    intent: Intent
    sub_intents: List[Intent]
    required_agents: List[str]

    # memory/profile
    profile: Dict[str, Any]               # e.g., {"risk_tolerance": "moderate", "experience": "beginner"}
    memory: List[Dict[str, str]]          # chat history [{"role":"user","content":"..."}, ...]

    # artifacts computed by agents
    rag_answer: Optional[str]
    rag_citations: Optional[List[Dict[str, str]]]

    portfolio_input: Optional[List[Dict[str, Any]]]   # [{"symbol":"AAPL","quantity":10}, ...]
    portfolio_metrics: Optional[Dict[str, Any]]

    market_request: Optional[Dict[str, Any]]          # {"symbols":["AAPL","MSFT"]}
    market_data: Optional[Dict[str, Any]]             # { "AAPL": {...}, ... }

    goals_request: Optional[Dict[str, Any]]           # {"target":50000,"monthly":300,"years":10,"assumption":"moderate"}
    goals_projection: Optional[Dict[str, Any]]

    news_request: Optional[Dict[str, Any]]            # {"topic":"markets"} or {"tickers":["AAPL"]}
    news_summary: Optional[Dict[str, Any]]

    # composed response
    final_answer: Optional[str]
    debug: Optional[Dict[str, Any]]