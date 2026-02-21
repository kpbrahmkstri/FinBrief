# src/graph.py
from __future__ import annotations

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
from .agents.tax_agent import tax_education_answer


# ---------------------------
# Node implementations
# ---------------------------

def node_router(state: FinanceState) -> FinanceState:
    user_message = state.get("user_message", "") or ""
    out = classify_intent(user_message)
    state["intent"] = out["intent"]
    state["sub_intents"] = out["sub_intents"]
    state["required_agents"] = out["required_agents"]
    state["debug"] = {"router": out}
    return state


def node_memory_update(state: FinanceState) -> FinanceState:
    profile = state.get("profile", {}) or {}
    memory = state.get("memory", []) or []
    user_message = state.get("user_message", "") or ""

    profile = update_profile(profile, user_message)
    memory = append_memory(memory, "user", user_message)

    state["profile"] = profile
    state["memory"] = memory
    return state


def node_rag(state: FinanceState) -> FinanceState:
    res = rag_qa(state.get("user_message", "") or "")
    state["rag_answer"] = res["answer"]
    state["rag_citations"] = res["citations"]
    return state


def node_market(state: FinanceState) -> FinanceState:
    """
    Fetch market quotes.
    Uses state.market_request.symbols if provided, otherwise extracts tickers robustly:
    - Prefer $TICKER format
    - Otherwise extract uppercase 1-5 letter tokens
    - Filter out common English words like PRICE/OF/etc.
    """
    req = state.get("market_request") or {}
    symbols = req.get("symbols") or []

    if not symbols:
        import re

        text = state.get("user_message", "") or ""

        # First: tickers like $AAPL
        dollar_tickers = re.findall(r"\$([A-Za-z]{1,5})\b", text)

        # Second: plain tickers like AAPL (uppercase tokens)
        # Only accept tokens that appear uppercase in the original input
        plain_tickers = re.findall(r"\b[A-Z]{1,5}\b", text)

        candidates = [t.upper() for t in (dollar_tickers + plain_tickers)]

        # Filter common words that match the ticker pattern
        STOPWORDS = {
            "PRICE", "OF", "THE", "AND", "FOR", "WITH", "LAST", "CLOSE", "QUOTE",
            "STOCK", "TODAY", "WHAT", "SHOW", "GET", "GIVE", "TELL", "DATA", "MARKET"
        }

        symbols = [t for t in candidates if t not in STOPWORDS]

        # If user typed "price of AAPL", use the last token as a fallback
        if not symbols:
            tokens = re.findall(r"[A-Za-z]{1,5}", text)
            if tokens:
                last = tokens[-1].upper()
                if last not in STOPWORDS:
                    symbols = [last]

        symbols = symbols[:5]

    state["market_request"] = {"symbols": symbols}
    state["market_data"] = market_intelligence(symbols)["quotes"]
    return state

def node_portfolio(state: FinanceState) -> FinanceState:
    """
    Analyze portfolio holdings. Uses market_data quotes if already fetched.
    """
    holdings = state.get("portfolio_input") or []
    quotes = state.get("market_data") or {}

    res = portfolio_analysis(holdings, quotes=quotes)
    state["portfolio_metrics"] = res["metrics"]

    # keep narrative in debug (optional)
    dbg = state.get("debug") or {}
    dbg["portfolio_narrative"] = res.get("narrative", "")
    state["debug"] = dbg
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

def node_tax(state: FinanceState) -> FinanceState:
    res = tax_education_answer(state.get("user_message", "") or "")
    state["tax_answer"] = res["answer"]
    state["tax_citations"] = res["citations"]
    return state

def node_compose(state: FinanceState) -> FinanceState:
    """
    Compose a single user-facing answer from whatever artifacts are available.
    Apply guardrails + update assistant message memory.
    """
    intent = state.get("intent", "qa")
    parts: List[str] = []

    # --- Education / RAG ---
    if state.get("rag_answer"):
        parts.append("### 📚 Explanation\n" + state["rag_answer"])

        cits = state.get("rag_citations") or []
        if cits:
            parts.append(
                "**Sources used (KB):** " +
                ", ".join([f"[{c['id']}] {c['source']}" for c in cits])
            )

        # --- Tax Education ---
    if state.get("tax_answer"):
        parts.append("### 🧾 Tax Education\n" + state["tax_answer"])

        tcits = state.get("tax_citations") or []
        if tcits:
            parts.append(
            "**Tax sources used (KB):** " +
            ", ".join([f"[{c['id']}] {c['source']}" for c in tcits])
        )

    # --- Market ---
    market_data = state.get("market_data") or {}
    if market_data:
        parts.append("### 📈 Market Data")
        for sym, q in market_data.items():
            if not isinstance(q, dict):
                continue

            if "error" in q:
                parts.append(f"- **{sym}**: ❌ {q['error']}")
                continue

            lp = q.get("last_price")
            pc = q.get("previous_close")
            src = q.get("source", "unknown")
            ts = q.get("fetched_at")

            lp_str = f"{lp:.2f}" if isinstance(lp, (int, float)) else "N/A"
            pc_str = f"{pc:.2f}" if isinstance(pc, (int, float)) else "N/A"

            pct = q.get("pct_change")
            pct_str = f"{pct:+.2f}%" if isinstance(pct, (int, float)) else "N/A"

            parts.append(
                f"- **{sym}**: last=${lp_str} | prev_close=${pc_str} | change={pct_str} "
                f"(source={src})"
            )
        
    # --- Portfolio ---
    if state.get("portfolio_metrics"):
        pm = state["portfolio_metrics"]
        parts.append("### 🧾 Portfolio Summary")
        parts.append(f"- Total value: **${pm['total_value']:,.2f}**")
        parts.append(f"- Effective holdings: **{pm['effective_holdings']:.2f}**")
        parts.append(f"- Concentration risk: **{pm['concentration_risk']}**")

        dbg = state.get("debug") or {}
        if dbg.get("portfolio_narrative"):
            parts.append(dbg["portfolio_narrative"])

    # --- Goals ---
    if state.get("goals_projection"):
        gp = state["goals_projection"]
        parts.append("### 🎯 Goal Projection")
        parts.append(gp.get("summary", ""))

        scenarios = gp.get("scenarios", {})
        for k, v in scenarios.items():
            rm = v.get("reached_month")
            parts.append(f"- {k}: " + (f"reached in ~{rm} months" if rm else "not reached within horizon"))

    # --- News ---
    if state.get("news_summary"):
        ns = state["news_summary"]
        parts.append("### 📰 News Summary")
        parts.append(ns.get("summary", ""))

    answer = "\n\n".join([p for p in parts if p]).strip()
    if not answer:
        answer = "I can help with finance education, portfolio basics, market quotes, goals, and news. What would you like to do?"



    # guardrails (education-only)
    answer = apply_guardrail(state.get("user_message", "") or "", answer)
    state["final_answer"] = answer

    # update assistant memory
    state["memory"] = append_memory(state.get("memory", []) or [], "assistant", answer)
    return state


# ---------------------------
# Routing logic
# ---------------------------

def route_next(state: FinanceState) -> str:
    """
    Decide which next node to run after router.
    IMPORTANT: return values must match the conditional mapping in build_graph().
    """
    intent = state.get("intent", "qa")

    if intent == "qa":
        return "rag"
    if intent == "market":
        return "market"
    if intent == "portfolio":
        return "market_then_portfolio"
    if intent == "goals":
        return "goals"
    if intent == "news":
        return "news"
    if intent == "tax":
        return "tax"
    if intent == "mixed":
        # simplest deterministic behavior: start with RAG; you can extend later
        return "rag"
    return "rag"


# ---------------------------
# Graph builder (NO fan-out)
# ---------------------------

def build_graph():
    """
    Deterministic StateGraph with no fan-out edges (prevents concurrent write errors).
    """
    g = StateGraph(FinanceState)

    # Nodes
    g.add_node("memory_update", node_memory_update)
    g.add_node("router", node_router)

    g.add_node("rag", node_rag)

    # split market into two nodes to avoid branching fan-out
    g.add_node("market_only", node_market)
    g.add_node("market_then_portfolio", node_market)

    g.add_node("portfolio", node_portfolio)
    g.add_node("goals", node_goals)
    g.add_node("news", node_news)
    g.add_node("compose", node_compose)
    g.add_node("tax", node_tax)

    # Entry
    g.set_entry_point("memory_update")
    g.add_edge("memory_update", "router")

    # Conditional routing (router -> next)
    g.add_conditional_edges("router", route_next, {
        "rag": "rag",
        "market": "market_only",
        "market_then_portfolio": "market_then_portfolio",
        "goals": "goals",
        "news": "news",
        "tax": "tax",
    })

    # Paths (deterministic)
    g.add_edge("rag", "compose")

    g.add_edge("market_only", "compose")

    g.add_edge("market_then_portfolio", "portfolio")
    g.add_edge("portfolio", "compose")

    g.add_edge("goals", "compose")
    g.add_edge("news", "compose")
    g.add_edge("tax", "compose")

    # End
    g.add_edge("compose", END)

    return g.compile()