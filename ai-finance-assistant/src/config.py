from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    newsapi_key: str = os.getenv("NEWSAPI_KEY", "")

    # RAG index paths
    kb_dir: str = os.getenv("KB_DIR", "src/data/knowledge_base/sample_articles")
    faiss_index_dir: str = os.getenv("FAISS_INDEX_DIR", "src/data/knowledge_base/faiss_index")

    # Caching
    cache_db_path: str = os.getenv("CACHE_DB_PATH", "src/data/cache.sqlite3")
    market_cache_ttl_seconds: int = int(os.getenv("MARKET_CACHE_TTL_SECONDS", "1800"))  # 30 minutes

    # Model
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

settings = Settings()