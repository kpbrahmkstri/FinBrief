📊 FinBrief — AI-Powered Multi-Agent Finance Assistant

FinBrief is a multi-agent AI system that provides financial education, market insights, portfolio analytics, goal planning, tax explanations, and financial news synthesis.

Built using:
- LangGraph (agent orchestration)
- LangChain + FAISS (RAG + vector search)
- OpenAI LLM
- Streamlit (UI)
- yfinance (market data)

🧠 Architecture Overview

Although the UI contains 5 tabs for simplicity, the backend consists of 6 independent AI agents, orchestrated via a graph-based routing layer.

User Input
   ↓
Intent Router (LangGraph)
   ├── Finance Q&A Agent
   ├── Tax Education Agent
   ├── Market Analysis Agent
   ├── Portfolio Analysis Agent
   ├── Goal Planning Agent
   └── News Synthesizer Agent

Each agent has:

- A dedicated node in the graph
- A distinct prompt strategy
- Independent tools and retrieval logic
- Structured outputs

🤖 Implemented Agents:

1️⃣ Finance Q&A Agent

Handles general financial education queries using Retrieval-Augmented Generation (RAG).

Features:

- 50+ curated financial education articles
- FAISS vector index
- Metadata-aware retrieval (title, category, source)
- Category filtering (Investing, Risk, Retirement, etc.)
- Structured answers
- Citation-backed responses

Example Questions:

- What is an ETF?
- What is diversification?
- How does dollar-cost averaging work?

2️⃣ Tax Education Agent

Specialized agent focused only on tax-related topics.

Features:

- Hard-filtered retrieval to Tax category
- Structured output (definition → example → pitfalls → next steps)
- Education-only disclaimer
- Supports comparisons (Roth vs Traditional vs Taxable)
- Citation support

Example Questions:

- What is the wash sale rule?
- Roth IRA vs Traditional IRA?
- What are capital gains?

3️⃣ Market Analysis Agent

Provides real-time market insights.

Features:

- Live quotes via yfinance
- % change calculation
- 5-day sparkline chart
- Multi-symbol support

Example:

Get price quotes for AAPL, MSFT

4️⃣ Portfolio Analysis Agent

Analyzes user portfolios for diversification and concentration risk.

Features:

- Allocation percentages
- Donut chart visualization
- Effective holdings metric
- Herfindahl-Hirschman Index (HHI)
- Diversification grade (A–F)
- Concentration warnings
- Educational suggestions

5️⃣ Goal Planning Agent

Helps users project financial goals.

Features:

- Inflation-adjusted targets
- Future value of current savings
- Required monthly contribution
- Gap analysis
- Compounded growth chart
- Sensitivity to return & inflation assumptions

6️⃣ News Synthesizer Agent

Aggregates and synthesizes financial news from multiple sources.

Features:

- Multi-source RSS ingestion
- Deduplication
- Topic filtering (Markets, Macro, Tech, Crypto, ETFs, Earnings)
- LLM-based thematic synthesis
- Clickable source attribution
- Structured summary:

    - Top stories
    - Themes & signals
    - Risk notes

📚 Knowledge Base Implementation

The system includes a curated financial education corpus:

- 50+ financial education articles
- Structured headers:
    - Title
    - Category
- Vectorized using FAISS
- Metadata stored for:
    - Source attribution
    - Category filtering
- Efficient similarity search retrieval

Rebuild index:
```bash
python -m src.scripts.build_kb
```

🧭 Routing Logic

The system uses intent-based routing to dispatch user queries to the appropriate agent.

Examples:

Intent	                            Routed To

“What is an ETF?”	            Finance Q&A Agent

“What is the wash sale rule?”	Tax Agent

“Get price for AAPL”	        Market Agent

“Analyze my portfolio”	        Portfolio Agent

“Help me plan retirement”	    Goal Agent

“Summarize latest macro news”	News Agent


🛠 Tech Stack

- Python 3.12
- LangGraph
- LangChain
- FAISS
- OpenAI GPT model
- Streamlit
- yfinance
- feedparser
- matplotlib
- pandas

🚀 How To Run

1️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

2️⃣ Set environment variables (.env)
```bash
OPENAI_API_KEY=your_key_here
```

3️⃣ Build Knowledge Base
```bash
python -m src.scripts.build_kb
```

4️⃣ Run Application
```bash
streamlit run app.py
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
cp .env.example .env