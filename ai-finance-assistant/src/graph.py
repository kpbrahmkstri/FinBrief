# src/graph.py
from __future__ import annotations

from typing import Any, Dict, List
from langgraph.graph import StateGraph, END
from matplotlib import category
import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver

from .state import FinanceState
from .config import get_session_db_path
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
    # ✅ If UI already decided the intent, honor it and skip classification
    forced = state.get("forced_intent")
    if forced:
        state["intent"] = forced
        state["sub_intents"] = []
        state["required_agents"] = [forced]
        state["debug"] = {"router": {"forced_intent": forced}}
        return state

    user_message = state.get("user_message", "") or ""
    out = classify_intent(user_message)

    state["intent"] = out.get("intent", "qa")
    state["sub_intents"] = out.get("sub_intents", [])
    state["required_agents"] = out.get("required_agents", [])

    # If multiple agents required → collaboration
    req = state["required_agents"] or []
    if len(req) >= 2:
        state["intent"] = "mixed"

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
    category = (state.get("profile") or {}).get("qa_category")  
    
    msgs = state.get("messages") or []
    history = []
    # Convert LangChain messages into simple strings
    for m in msgs[-10:]:
        # Handle both dict-like and LangChain message objects
        if isinstance(m, dict):
            role = (m.get("role") or "").lower()
            content = m.get("content") or ""
        else:
            # LangChain message objects have .type and .content attributes
            role = getattr(m, "type", "").lower()
            content = getattr(m, "content", "") or ""
        
        if not content:
            continue
        history.append(f"{role}: {content}")

    res = rag_qa(
        state.get("user_message", "") or "",
        category=category,
        history=history,
    )

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
    state["market_answer"] = state.get("final_answer", "") or state.get("market_answer", "")
    return state

def node_planner(state: FinanceState) -> FinanceState:
    """
    Build a deterministic multi-agent execution plan using router output.
    """
    req = state.get("required_agents") or []

    # Map your router's agent names → graph node steps
    # Adjust strings if your classify_intent uses different labels.
    mapping = {
        "finance_qa": "rag",
        "rag": "rag",
        "tax": "tax",
        "tax_education": "tax",
        "goal_planning": "goals",
        "goals": "goals",
        "news": "news",
        "news_synth": "news",
    }

    # Build plan in a good order:
    # RAG first for explanation, then goals/tax/news
    ordered = []
    for k in req:
        step = mapping.get(k, None)
        if step and step not in ordered:
            ordered.append(step)

    # If router gave unknown labels, default to rag
    if not ordered:
        ordered = ["rag"]

    # Ensure rag appears first if present
    if "rag" in ordered:
        ordered = ["rag"] + [x for x in ordered if x != "rag"]

    state["plan"] = ordered
    return state

def node_execute_plan(state: FinanceState) -> FinanceState:
    plan = state.get("plan") or ["rag"]

    # Defaults to prevent crashes if user didn't fill UI fields
    state.setdefault("news_request", {"topic": "All", "limit": 8})
    state.setdefault(
        "goals_request",
        {
            "target": 50000,
            "monthly": 300,
            "years": 10,
            "current": 0,
            "expected_return": 0.06,
            "inflation": 0.02,
        },
    )

    for step in plan:
        if step == "rag":
            state = node_rag(state)
        elif step == "tax":
            state = node_tax(state)
        elif step == "goals":
            state = node_goals(state)
        elif step == "news":
            state = node_news(state)

    return state

def node_compose_collab(state: FinanceState) -> FinanceState:
    parts = []
    parts.append("⚠️ **Education-only:** General information, not personalized financial or tax advice.\n")

    rag = (state.get("rag_answer") or "").strip()
    if rag:
        parts.append("## 📘 Finance Explanation\n" + rag)

    gp = state.get("goals_projection") or {}
    if gp:
        ia = gp.get("inflation_adjusted_target")
        rm = gp.get("required_monthly_contribution")
        gap = gp.get("gap")
        parts.append(
            "## 🎯 Goal Planning Snapshot\n"
            f"- Inflation-adjusted target: **{f'${ia:,.0f}' if isinstance(ia,(int,float)) else 'N/A'}**\n"
            f"- Required monthly contribution: **{f'${rm:,.0f}' if isinstance(rm,(int,float)) else 'N/A'}**\n"
            f"- Gap: **{f'${gap:,.0f}' if isinstance(gap,(int,float)) else 'N/A'}**\n"
        )

    tax = (state.get("tax_answer") or "").strip()
    if tax:
        parts.append("## 🧾 Tax Notes\n" + tax)

    ns = state.get("news_summary") or {}
    if ns.get("summary"):
        parts.append("## 🗞️ News Digest\n" + ns["summary"])

    state["final_answer"] = "\n\n---\n\n".join(parts).strip()
    return state

def node_portfolio(state: FinanceState) -> FinanceState:
    """
    Analyze portfolio holdings. Uses market_data quotes if already fetched.
    """
    holdings = state.get("portfolio_input") or []
    quotes = state.get("market_data") or {}

    res = portfolio_analysis(holdings, quotes=quotes)
    metrics = res.get("metrics", {}) or {}
    narrative = res.get("narrative", "") or ""

    state["portfolio_metrics"] = metrics
    state["portfolio_narrative"] = narrative

    # keep narrative in debug (optional)
    dbg = state.get("debug") or {}
    dbg["portfolio_narrative"] = res.get("narrative", "")
    state["portfolio_answer"] = state["portfolio_narrative"]
    state["portfolio_answer"] = state.get("portfolio_narrative", "") or ""
    state["portfolio_narrative"] = narrative
    state["debug"] = dbg
    return state


def node_goals(state: FinanceState) -> FinanceState:
    req = state.get("goals_request") or {}

    target = float(req.get("target", 50000))
    monthly = float(req.get("monthly", 300))
    years = float(req.get("years", 10))
    current = float(req.get("current", 0))
    expected_return = float(req.get("expected_return", 0.06))
    inflation = float(req.get("inflation", 0.02))

    goal_input = {
        "goal_amount": target,
        "monthly_contribution": monthly,
        "years": years,
        "current_savings": current,
        "expected_return": expected_return,
        "inflation_rate": inflation,
    }

    result = goal_planning(goal_input)

    state["goals_request"] = goal_input
    state["goals_projection"] = result.get("goal_metrics", {})
    state["final_answer"] = result.get("narrative", "")

    gp = state.get("goals_projection") or {}
    rm = gp.get("required_monthly_contribution")
    gap = gp.get("gap")
    ia = gp.get("inflation_adjusted_target")

    state["goals_answer"] = (
        "⚠️ Education-only: Not personalized financial advice.\n\n"
        "## 🎯 Goal Projection Summary\n"
        f"- Inflation-adjusted target: **{f'${ia:,.0f}' if isinstance(ia,(int,float)) else 'N/A'}**\n"
        f"- Required monthly contribution: **{f'${rm:,.0f}' if isinstance(rm,(int,float)) else 'N/A'}**\n"
        f"- Gap: **{f'${gap:,.0f}' if isinstance(gap,(int,float)) else 'N/A'}**\n"
    )

    return state


def node_news(state: FinanceState) -> FinanceState:
    req = state.get("news_request") or {}
    topic = str(req.get("topic", "All"))
    limit = int(req.get("limit", 10))

    from .agents.news_agent import synthesize_news

    res = synthesize_news(topic=topic, limit=limit)

    state["news_summary"] = {
        "topic": res.get("topic", topic),
        "items": res.get("items", []),
        "citations": res.get("citations", []),
    }

    # Put the synthesized narrative into final_answer
    state["final_answer"] = res.get("summary", "")
    ns = state.get("news_summary") or {}
    state["news_answer"] = ns.get("summary", "") or ""
    return state

def node_tax(state: FinanceState) -> FinanceState:
    from .agents.tax_agent import tax_qa

    user_message = state.get("user_message", "") or ""
    #res = tax_qa(user_message)
    msgs = state.get("messages") or []
    history = []
    for m in msgs[-10:]:
        role = getattr(m, "type", None) or m.__class__.__name__.lower()
        content = getattr(m, "content", "")
        if not content:
            continue
        if "human" in role:
            history.append(f"user: {content}")
        elif "ai" in role:
            history.append(f"assistant: {content}")
        else:
            history.append(f"{role}: {content}")

    res = tax_education_answer(
        state.get("user_message", "") or "",
        history=history,
    )

    state["tax_answer"] = res.get("answer", "")
    state["tax_citations"] = res.get("citations", [])

    # show this answer to the UI
    state["final_answer"] = state["tax_answer"]
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
    # Only show market summary when the user asked for market directly
    # (prevents Market Data from cluttering Portfolio results)
    if state.get("intent") in ("market",):
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

                lp_str = f"{lp:.2f}" if isinstance(lp, (int, float)) else "N/A"
                pc_str = f"{pc:.2f}" if isinstance(pc, (int, float)) else "N/A"

                parts.append(f"- **{sym}**: ${lp_str} (prev close: ${pc_str}, source: {src})")
            
    # --- Portfolio ---
    # Only show portfolio summary when portfolio was explicitly analyzed
    if state.get("intent") in ("portfolio",) and state.get("portfolio_metrics"):
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

def node_append_assistant(state: FinanceState) -> FinanceState:
    ans = state.get("final_answer") or ""
    if ans:
        state["messages"] = (state.get("messages") or []) + [{"role": "assistant", "content": ans}]
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
        return "planner"
    if intent == "collab":
        return "planner"
    return "rag"


# --------------
# Graph builder 
# --------------

def build_graph():
    """
    Deterministic StateGraph with no fan-out edges (prevents concurrent write errors).
    Adds persistent multi-turn chat memory via SQLite checkpointer + JSON-safe messages.
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
    g.add_node("tax", node_tax)

    g.add_node("planner", node_planner)
    g.add_node("execute_plan", node_execute_plan)
    g.add_node("compose_collab", node_compose_collab)

    g.add_node("compose", node_compose)

    # ✅ new: append assistant answer to messages for persistence
    g.add_node("append_assistant", node_append_assistant)

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
        "planner": "planner",
        "tax": "tax",
    })

    # Paths (deterministic)
    g.add_edge("rag", "compose")

    g.add_edge("market_only", "compose")

    g.add_edge("market_then_portfolio", "portfolio")
    g.add_edge("portfolio", "compose")

    g.add_edge("planner", "execute_plan")
    g.add_edge("execute_plan", "compose_collab")
    g.add_edge("compose_collab", "append_assistant")

    g.add_edge("goals", "compose")
    g.add_edge("news", "compose")
    g.add_edge("tax", "compose")

    # ✅ After composing, append assistant message, then end
    g.add_edge("compose", "append_assistant")
    g.add_edge("append_assistant", END)

    # Checkpointer (persistent memory across sessions)
    db_path = get_session_db_path()

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    return g.compile(checkpointer=checkpointer)