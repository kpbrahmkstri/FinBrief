import sqlite3
import json
import time
from typing import Any, Optional, Tuple

class SQLiteTTLCache:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        now = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?",
                (key,),
            ).fetchone()
        if not row:
            return None
        value_str, expires_at = row
        if expires_at < now:
            self.delete(key)
            return None
        return json.loads(value_str)

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        expires_at = int(time.time()) + ttl_seconds
        value_str = json.dumps(value)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, value_str, expires_at),
            )
            conn.commit()

    def delete(self, key: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()