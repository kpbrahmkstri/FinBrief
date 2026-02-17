# Cache Folder

This folder stores runtime caches used by the assistant.

- `cache.sqlite3` is created automatically at runtime (TTL cache for market quotes).
- Do not commit the sqlite file to GitHub (add to `.gitignore`).

Recommended `.gitignore` entries:
- src/data/cache/cache.sqlite3
- src/data/knowledge_base/faiss_index/