from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

def get_project_root() -> Path:
    """Get the project root directory (parent of src/)"""
    return Path(__file__).parent.parent

def get_data_dir() -> Path:
    """Get the data directory, create it if it doesn't exist"""
    data_dir = get_project_root() / "src" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def get_kb_dir() -> Path:
    """Get the knowledge base directory"""
    kb_dir = get_data_dir() / "knowledge_base" / "sample_articles"
    kb_dir.mkdir(parents=True, exist_ok=True)
    return kb_dir

def get_faiss_index_dir() -> Path:
    """Get the FAISS index directory"""
    faiss_dir = get_data_dir() / "knowledge_base" / "faiss_index"
    faiss_dir.mkdir(parents=True, exist_ok=True)
    return faiss_dir

def get_cache_db_path() -> Path:
    """Get the cache database path"""
    cache_file = get_data_dir() / "cache.sqlite3"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    return cache_file

def get_session_db_path() -> Path:
    """Get the session database path for memory persistence"""
    session_dir = get_data_dir() / "session"
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir / "finbrief_memory.sqlite"

def get_thread_id_file() -> Path:
    """Get the thread ID file path"""
    session_dir = get_data_dir() / "session"
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir / "thread_id.txt"

class Settings(BaseModel):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    newsapi_key: str = os.getenv("NEWSAPI_KEY", "")

    # RAG index paths - use environment variables or defaults
    kb_dir: Path = Path(os.getenv("KB_DIR", str(get_kb_dir())))
    faiss_index_dir: Path = Path(os.getenv("FAISS_INDEX_DIR", str(get_faiss_index_dir())))

    # Caching
    cache_db_path: Path = Path(os.getenv("CACHE_DB_PATH", str(get_cache_db_path())))
    market_cache_ttl_seconds: int = int(os.getenv("MARKET_CACHE_TTL_SECONDS", "1800"))  # 30 minutes

    # Model
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    class Config:
        arbitrary_types_allowed = True

settings = Settings()