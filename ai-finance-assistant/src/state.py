# src/state.py
from typing import Annotated, Any, Dict, List, Optional, TypedDict, Literal
#from langchain_core.messages import BaseMessage

IntentType = Literal["qa", "portfolio", "market", "goals", "news", "tax", "mixed", "unknown"]

class FinanceState(TypedDict, total=False):
    # raw user input
    user_message: str
    final_answer: str

    messages: List[Dict[str, str]]

    # router outputs
    intent: IntentType
    sub_intents: List[IntentType]
    required_agents: List[str]

    # memory/profile
    profile: Dict[str, Any]
    memory: List[Dict[str, str]]

    # artifacts computed by agents
    rag_answer: Optional[str]
    rag_citations: Optional[List[Dict[str, str]]]

    tax_answer: Optional[str]
    tax_citations: Optional[List[Dict[str, str]]]

    portfolio_input: Optional[List[Dict[str, Any]]]
    portfolio_metrics: Optional[Dict[str, Any]]

    market_request: Optional[Dict[str, Any]]
    market_data: Optional[Dict[str, Any]]

    market_answer: str
    portfolio_answer: str
    goals_answer: str
    news_answer: str

    goals_request: Optional[Dict[str, Any]]
    goals_projection: Optional[Dict[str, Any]]

    news_request: Optional[Dict[str, Any]]
    news_summary: Optional[Dict[str, Any]]

    # composed response
    final_answer: Optional[str]
    debug: Optional[Dict[str, Any]]