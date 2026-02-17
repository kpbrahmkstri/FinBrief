# Knowledge Base (RAG)

This folder contains the finance education content used for Retrieval-Augmented Generation (RAG).

## Structure
- `sample_articles/`: Text files used to build the FAISS index.
- `faiss_index/`: Generated vector index (do not commit).
- `sources_manifest.json`: Tracks what content is included.

## How RAG uses these files
1. Articles are chunked into passages.
2. Passages are embedded.
3. FAISS index is built and queried for relevant context.
4. The assistant answers with citations (file names act as sources).

## Adding more articles (to reach 100+)
- Add more `.txt` files to `sample_articles/`.
- Keep each file short and focused (~200–600 words).
- Use the same template as existing files.

Then rebuild:
```bash
python -m src.scripts.build_kb