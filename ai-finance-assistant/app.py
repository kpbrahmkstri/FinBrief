import streamlit as st
import os
os.environ["STREAMLIT_FILE_WATCHER_TYPE"] = "none"
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

    qa_category = st.selectbox(
        "Q&A Category (optional)",
        ["All", "Investing", "Tax", "Retirement", "Markets", "Risk", "Personal Finance"],
        index=0
    )
    
    user_message = st.text_input("Ask a finance question:", placeholder="Explain diversification, or price of AAPL, or plan a goal...")

    if st.button("Send", type="primary") and user_message:
        out = run_graph(
            user_message,
            extra_state={
                "profile": {
                    "qa_category": qa_category
                }
            }
        )
        st.markdown(out.get("final_answer", ""))

        tax_cites = out.get("tax_citations", []) or []
        if tax_cites:
            st.markdown("**Sources used (Tax KB):**")
            for c in tax_cites:
                st.write(
                    f"- [{c.get('id','?')}] "
                    f"{c.get('title','Untitled')} — {c.get('source','')}"
                )

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
        out = run_graph(
            "Analyze my portfolio allocation and diversification.",
            extra_state={
                "portfolio_input": st.session_state.portfolio,
                "market_request": {"symbols": [x["symbol"] for x in st.session_state.portfolio]},
            },
        )

        pm = out.get("portfolio_metrics", {})
        st.markdown(out.get("final_answer", ""))

        if pm and pm.get("positions"):
            pos = pd.DataFrame(pm["positions"])
            st.dataframe(pos, use_container_width=True)

            # --- Donut Allocation Chart (cleaner than pie) ---
            labels = pos["symbol"].tolist()
            sizes = pos["allocation_pct"].tolist()

            fig = plt.figure(figsize=(3, 3))
            wedges, texts, autotexts = plt.pie(
                sizes,
                labels=labels,
                autopct="%1.1f%%",
                pctdistance=0.78,
                labeldistance=1.05,
            )
            centre_circle = plt.Circle((0, 0), 0.55, fc="white")
            fig.gca().add_artist(centre_circle)
            plt.title("Allocation (%)")
            plt.tight_layout()
            st.pyplot(fig)

            # --- Concentration metrics ---
            hhi = pm.get("hhi")
            grade = pm.get("diversification_grade")

            c1, c2 = st.columns(2)
            with c1:
                st.metric("Concentration (HHI)", f"{hhi:.3f}" if isinstance(hhi, (int, float)) else "N/A")
            with c2:
                st.metric("Diversification Grade", grade or "N/A")

            # --- Top holdings & flags ---
            flags = pm.get("concentration_flags", {}) or {}
            top_pos = flags.get("top_positions", [])

            if top_pos:
                st.subheader("Top Holdings")
                for x in top_pos:
                    st.write(f"- **{x['symbol']}**: {x['allocation_pct']:.1f}%")

            # --- Recommendations ---
            recs = pm.get("recommendations", []) or []
            if recs:
                st.subheader("Education-only Suggestions")
                for r in recs:
                    st.write(f"- {r}")    



with tab_market:
    st.subheader("Market")

    tickers = st.text_input("Tickers (comma-separated):", value="AAPL,MSFT")

    if st.button("Get Quotes"):
        symbols = [t.strip().upper() for t in tickers.split(",") if t.strip()]

        out = run_graph(
            f"Get price quotes for {', '.join(symbols)}",
            extra_state={"market_request": {"symbols": symbols}}
        )

        # Print text summary
        st.markdown(out.get("final_answer", ""))

        # Access structured market data
        market_data = out.get("market_data", {})

        import matplotlib.pyplot as plt

        for sym, quote in market_data.items():

            st.markdown(f"### {sym}")
            #st.write("DEBUG keys:", list(quote.keys()))

            if "error" in quote:
                st.error(f"{sym}: {quote['error']}")
                continue

            last = quote.get("last_price")
            prev = quote.get("previous_close")
            pct = quote.get("pct_change")
            hist = quote.get("history_5d", [])
            hist_dates = quote.get("history_dates", [])

            # Calculate pct_change if not provided but we have prices
            if pct is None and last is not None and prev is not None and prev != 0:
                pct = ((last - prev) / prev) * 100.0

            # Nice formatted metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Last Price", f"${last:.2f}" if last else "N/A")

            with col2:
                st.metric("Prev Close", f"${prev:.2f}" if prev else "N/A")

            with col3:
                if pct is not None:
                    st.metric("Change", f"{pct:+.2f}%", delta=f"{pct:+.2f}%")
                else:
                    st.metric("Change", "N/A")

            # Sparkline chart
            if hist and len(hist) >= 2:
                fig = plt.figure(figsize=(8, 4))
                plt.plot(hist, marker='o', linewidth=2, markersize=8)
                
                # Add price labels at each point
                for i, price in enumerate(hist):
                    plt.text(i, price, f'${price:.2f}', ha='center', va='bottom', fontsize=9)
                
                plt.title(f"{sym} - Last 5 Closes", fontsize=12)
                plt.xlabel("Date", fontsize=10)
                plt.ylabel("Price ($)", fontsize=10)
                
                # Use actual dates if available, otherwise use day numbers
                if hist_dates and len(hist_dates) == len(hist):
                    plt.xticks(range(len(hist)), hist_dates, rotation=45)
                else:
                    plt.xticks(range(len(hist)), [f"Day {i+1}" for i in range(len(hist))])
                
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig)
    

with tab_goals:
    st.subheader("Goals")

    row1 = st.columns(3)
    with row1[0]:
        target = st.number_input("Target amount ($)", min_value=1_000, value=50_000, step=1_000)
    with row1[1]:
        current = st.number_input("Current savings ($)", min_value=0, value=5_000, step=500)
    with row1[2]:
        years = st.number_input("Time horizon (years)", min_value=1, value=10, step=1)

    row2 = st.columns(3)
    with row2[0]:
        monthly = st.number_input("Monthly contribution ($)", min_value=0, value=300, step=10)
    with row2[1]:
        exp_return = st.slider("Expected annual return (%)", 0.0, 15.0, 6.0) / 100.0
    with row2[2]:
        inflation = st.slider("Inflation rate (%)", 0.0, 10.0, 2.0) / 100.0

    if st.button("Run Projection"):
        out = run_graph(
            "Help me plan this financial goal.",
            extra_state={
                "goals_request": {
                    "target": target,
                    "monthly": monthly,
                    "years": years,
                    "current": current,
                    "expected_return": exp_return,
                    "inflation": inflation,
                }
            },
        )

        gp = out.get("goals_projection", {}) or {}
        st.markdown(out.get("final_answer", ""))

        # Summary cards
        c1, c2, c3 = st.columns(3)
        ia = gp.get("inflation_adjusted_target")
        fv = gp.get("future_value_current")
        rm = gp.get("required_monthly_contribution")

        with c1:
            st.metric("Inflation-adjusted target", f"${ia:,.0f}" if isinstance(ia, (int, float)) else "N/A")
        with c2:
            st.metric("Projected value of current savings", f"${fv:,.0f}" if isinstance(fv, (int, float)) else "N/A")
        with c3:
            st.metric("Required monthly contribution", f"${rm:,.0f}" if isinstance(rm, (int, float)) else "N/A")

        gap = gp.get("gap")
        if isinstance(gap, (int, float)):
            if gap > 0:
                st.warning(f"You are short by about **${gap:,.0f}** under these assumptions.")
            else:
                st.success("You appear on track under these assumptions.")

        # Plot: Compounded monthly growth curve (no scenario dependency)
        months = int(years * 12)
        monthly_rate = exp_return / 12.0

        balances = []
        bal = float(current)
        for _ in range(months):
            bal = bal * (1 + monthly_rate) + float(monthly)
            balances.append(bal)

        fig = plt.figure(figsize=(6, 3))
        plt.plot(range(1, months + 1), balances)
        plt.title("Projected Growth Over Time (Compounded)")
        plt.xlabel("Month")
        plt.ylabel("Balance ($)")
        plt.tight_layout()
        st.pyplot(fig)

with tab_news:
    st.subheader("News")

    topic = st.selectbox(
        "Topic",
        ["All", "Markets", "Macro", "Tech", "Crypto", "ETFs", "Earnings"],
        index=0,
    )
    limit = st.slider("Number of headlines", 5, 30, 10)

    if st.button("Fetch & Summarize News"):
        out = run_graph(
            "Summarize the latest financial news.",
            extra_state={"news_request": {"topic": topic, "limit": limit}},
        )

        st.markdown(out.get("final_answer", ""))

        ns = out.get("news_summary", {}) or {}
        items = ns.get("items", []) or []

        if items:
            st.subheader("Sources")
            for it in items:
                title = it.get("title", "Untitled")
                url = it.get("url", "")
                published = it.get("published", "")
                source = it.get("source", "")
                # clickable
                st.markdown(f"- [{title}]({url}) — {source} ({published})")