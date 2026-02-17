# AI Finance Assistant (Multi-Agent + LangGraph)

Educational finance assistant with:
- 6 core agents (Router, RAG-QA, Market, Portfolio, Goals, Memory)
- Bonus News summarization agent
- RAG using FAISS + embeddings
- Real-time market quotes via yfinance with TTL caching
- Streamlit multi-tab UI

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
cp .env.example .env