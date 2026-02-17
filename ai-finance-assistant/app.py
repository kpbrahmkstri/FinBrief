import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from src.graph import build_graph

st.set_page_config(page_title="FinBrief", layout="wide")

GRAPH = build_graph()

# Session state
if "profile" not in st.session_state:
    st.session_state.profile = {"experience": "beginner", "risk_tolerance": "moderate"}
if "memory" not in st.session_state:
    st.session_state.memory = []
if "portfolio" not in st.session_state:
    st.session_state.portfolio = [{"symbol": "AAPL", "quantity": 5}, {"symbol": "MSFT", "quantity": 3}]
if "last_state" not in st.session_state:
    st.session_state.last_state = {}

st.title("FinBrief- AI Finance Assistant")

tab_chat, tab_portfolio, tab_market, tab_goals, tab_news = st.tabs(
    ["Chat", "Portfolio", "Market", "Goals", "News"]
)

def run_graph(user_message: str, extra_state: dict):
    state = {
        "user_message": user_message,
        "profile": st.session_state.profile,
        "memory": st.session_state.memory,
        **extra_state,
    }
    out = GRAPH.invoke(state)
    st.session_state.profile = out.get("profile", st.session_state.profile)
    st.session_state.memory = out.get("memory", st.session_state.memory)
    st.session_state.last_state = out
    return out

with tab_chat:
    st.subheader("Chat")
    user_message = st.text_input("Ask something (education-only):", placeholder="Explain diversification, or price of AAPL, or plan a goal...")

    if st.button("Send", type="primary") and user_message:
        out = run_graph(user_message, extra_state={
            "portfolio_input": st.session_state.portfolio
        })
        st.markdown(out.get("final_answer", ""))

    st.markdown("### Conversation Memory (last 6)")
    for m in st.session_state.memory[-6:]:
        if m["role"] == "user":
            st.markdown(f"**🧑 You:** {m['content']}")
        else:
            st.markdown(f"**🤖 Assistant:** {m['content']}")

with tab_portfolio:
    st.subheader("Portfolio")
    df = pd.DataFrame(st.session_state.portfolio)
    edited = st.data_editor(df, num_rows="dynamic")
    st.session_state.portfolio = edited.to_dict(orient="records")

    if st.button("Analyze Portfolio"):
        out = run_graph("Analyze my portfolio allocation and diversification.", extra_state={
            "portfolio_input": st.session_state.portfolio,
            "market_request": {"symbols": [x["symbol"] for x in st.session_state.portfolio]},
        })
        pm = out.get("portfolio_metrics")
        st.markdown(out.get("final_answer", ""))

        if pm and pm.get("positions"):
            pos = pd.DataFrame(pm["positions"])
            st.dataframe(pos)

            # Allocation chart
            fig = plt.figure()
            fig = plt.figure(figsize=(4, 4))
            labels = pos["symbol"].tolist()
            sizes = pos["allocation_pct"].tolist()
            plt.pie(sizes, labels=labels, autopct="%1.1f%%")
            plt.title("Allocation (%)")
            st.pyplot(fig)

with tab_market:
    st.subheader("Market")
    tickers = st.text_input("Tickers (comma-separated):", value="AAPL,MSFT")
    if st.button("Get Quotes"):
        symbols = [t.strip().upper() for t in tickers.split(",") if t.strip()]
        out = run_graph(f"Get price quotes for {', '.join(symbols)}", extra_state={
            "market_request": {"symbols": symbols}
        })
        st.markdown(out.get("final_answer", ""))

with tab_goals:
    st.subheader("Goals")
    col1, col2, col3 = st.columns(3)
    with col1:
        target = st.number_input("Target amount ($)", min_value=1000, value=50000, step=1000)
    with col2:
        monthly = st.number_input("Monthly contribution ($)", min_value=10, value=300, step=10)
    with col3:
        years = st.number_input("Time horizon (years)", min_value=1, value=10, step=1)

    if st.button("Run Projection"):
        out = run_graph("Help me plan this financial goal.", extra_state={
            "goals_request": {"target": target, "monthly": monthly, "years": years}
        })
        gp = out.get("goals_projection", {})
        st.markdown(out.get("final_answer", ""))

        # Plot moderate scenario
        if gp and "scenarios" in gp:
            balances = gp["scenarios"]["moderate"]["balances"]
            fig = plt.figure()
            plt.plot(list(range(1, len(balances)+1)), balances)
            plt.title("Moderate Projection Balance Over Time")
            plt.xlabel("Month")
            plt.ylabel("Balance ($)")
            st.pyplot(fig)

with tab_news:
    st.subheader("News")
    topic = st.text_input("News topic:", value="markets")
    if st.button("Summarize News"):
        out = run_graph(f"Summarize latest finance news about {topic}.", extra_state={
            "news_request": {"topic": topic}
        })
        st.markdown(out.get("final_answer", ""))