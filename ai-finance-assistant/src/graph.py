from typing import Any, Dict, List
from langgraph.graph import StateGraph, END

from .state import FinanceState
from .agents.router_agent import classify_intent
from .agents.rag_qa_agent import rag_qa
from .agents.market_agent import market_intelligence
from .agents.portfolio_agent import portfolio_analysis
from .agents.goal_agent import goal_planning
from .agents.news_agent import summarize_news
from .agents.memory_agent import update_profile, append_memory
from .agents.safety_agent import apply_guardrail

def node_router(state: FinanceState) -> FinanceState:
    user_message = state.get("user_message", "")
    out = classify_intent(user_message)
    state["intent"] = out["intent"]
    state["sub_intents"] = out["sub_intents"]
    state["required_agents"] = out["required_agents"]
    state["debug"] = {"router": out}
    return state

def node_memory(state: FinanceState) -> FinanceState:
    profile = state.get("profile", {}) or {}
    memory = state.get("memory", []) or []
    user_message = state.get("user_message", "")

    profile = update_profile(profile, user_message)
    memory = append_memory(memory, "user", user_message)

    state["profile"] = profile
    state["memory"] = memory
    return state

def node_rag(state: FinanceState) -> FinanceState:
    res = rag_qa(state.get("user_message", ""))
    state["rag_answer"] = res["answer"]
    state["rag_citations"] = res["citations"]
    return state

def node_market(state: FinanceState) -> FinanceState:
    req = state.get("market_request") or {}
    symbols = req.get("symbols") or []

    # If user asked "price of AAPL", parse simple tickers from text as fallback
    if not symbols:
        text = state.get("user_message", "")
        tokens = [t.strip(" ,.$()").upper() for t in text.split()]
        symbols = [t for t in tokens if t.isalpha() and 1 <= len(t) <= 5]
        symbols = symbols[:5]

    state["market_request"] = {"symbols": symbols}
    state["market_data"] = market_intelligence(symbols)["quotes"]
    return state

def node_portfolio(state: FinanceState) -> FinanceState:
    holdings = state.get("portfolio_input") or []
    quotes = state.get("market_data") or {}
    res = portfolio_analysis(holdings, quotes=quotes)
    state["portfolio_metrics"] = res["metrics"]
    # store narrative in rag_answer slot for composing (simple)
    state["debug"]["portfolio_narrative"] = res["narrative"] if state.get("debug") else {"portfolio_narrative": res["narrative"]}
    return state

def node_goals(state: FinanceState) -> FinanceState:
    req = state.get("goals_request") or {}
    target = float(req.get("target", 50000))
    monthly = float(req.get("monthly", 300))
    years = float(req.get("years", 10))

    state["goals_request"] = {"target": target, "monthly": monthly, "years": years}
    state["goals_projection"] = goal_planning(target, monthly, years)
    return state

def node_news(state: FinanceState) -> FinanceState:
    req = state.get("news_request") or {}
    topic = req.get("topic", "markets")
    state["news_request"] = {"topic": topic}
    state["news_summary"] = summarize_news(topic)
    return state

def node_compose(state: FinanceState) -> FinanceState:
    intent = state.get("intent", "qa")
    parts: List[str] = []

    # compose based on computed artifacts
    if intent in ["qa", "mixed"] and state.get("rag_answer"):
        parts.append("### 📚 Explanation\n" + state["rag_answer"])

        cits = state.get("rag_citations") or []
        if cits:
            parts.append("**Sources used (KB):** " + ", ".join([f"[{c['id']}] {c['source']}" for c in cits]))

    if intent in ["market", "mixed"] and state.get("market_data"):
        parts.append("### 📈 Market Data")
        for sym, q in state["market_data"].items():
            if "error" in q:
                parts.append(f"- **{sym}**: {q['error']}")
            else:
                lp = q.get("last_price")
                pc = q.get("previous_close")
                src = q.get("source")
                parts.append(f"- **{sym}**: last=${lp} prev_close=${pc} (source={src})")

    if intent in ["portfolio", "mixed"] and state.get("portfolio_metrics"):
        pm = state["portfolio_metrics"]
        parts.append("### 🧾 Portfolio Summary")
        parts.append(f"- Total value: **${pm['total_value']:,.2f}**")
        parts.append(f"- Effective holdings: **{pm['effective_holdings']:.2f}**")
        parts.append(f"- Concentration risk: **{pm['concentration_risk']}**")

    if intent in ["goals", "mixed"] and state.get("goals_projection"):
        gp = state["goals_projection"]
        parts.append("### 🎯 Goal Projection")
        parts.append(gp["summary"])
        # show reached month info for each scenario
        for k, v in gp["scenarios"].items():
            rm = v["reached_month"]
            parts.append(f"- {k}: " + (f"reached in ~{rm} months" if rm else "not reached within horizon"))

    if intent in ["news", "mixed"] and state.get("news_summary"):
        ns = state["news_summary"]
        parts.append("### 📰 News Summary")
        parts.append(ns["summary"])

    answer = "\n\n".join(parts) if parts else "I can help with finance education, portfolio basics, market quotes, goals, and news. What would you like to do?"
    answer = apply_guardrail(state.get("user_message", ""), answer)
    state["final_answer"] = answer

    # update memory with assistant response
    state["memory"] = append_memory(state.get("memory", []), "assistant", answer)
    return state

def route_next(state: FinanceState) -> str:
    intent = state.get("intent", "qa")
    if intent == "qa":
        return "rag"
    if intent == "market":
        return "market"
    if intent == "portfolio":
        return "market_then_portfolio"  # portfolio often needs quotes
    if intent == "goals":
        return "goals"
    if intent == "news":
        return "news"
    if intent == "mixed":
        return "mixed"
    return "rag"

def build_graph():
    g = StateGraph(FinanceState)

    g.add_node("router", node_router)
    g.add_node("memory", node_memory)
    g.add_node("rag", node_rag)
    g.add_node("market", node_market)
    g.add_node("portfolio", node_portfolio)
    g.add_node("goals", node_goals)
    g.add_node("news", node_news)
    g.add_node("compose", node_compose)

    g.set_entry_point("memory")
    g.add_edge("memory", "router")

    # conditional routing
    g.add_conditional_edges("router", route_next, {
        "rag": "rag",
        "market": "market",
        "goals": "goals",
        "news": "news",
        "market_then_portfolio": "market",
        "mixed": "rag",  # start with RAG for mixed; then chain based on sub_intents
    })

    # chain edges
    g.add_edge("rag", "compose")
    g.add_edge("market", "compose")
    g.add_edge("goals", "compose")
    g.add_edge("news", "compose")

    # portfolio chain: market -> portfolio -> compose
    g.add_edge("market", "portfolio")
    g.add_edge("portfolio", "compose")

    g.add_edge("compose", END)

    return g.compile()