# Hugging Face Spaces Deployment Guide

This guide explains how to deploy the FinBrief AI Finance Assistant on Hugging Face Spaces.

## Pre-Deployment Checklist ✅

- [x] All paths use `pathlib.Path` for cross-platform compatibility
- [x] Environment variables properly configured
- [x] Dependencies listed in `requirements.txt`
- [x] Data directories automatically created at runtime

## Step 1: Create a Hugging Face Account

1. Go to [huggingface.co](https://huggingface.co)
2. Sign up or log in to your account
3. Create a new personal access token at: https://huggingface.co/settings/tokens
   - Select "write" access scope
   - Save the token securely

## Step 2: Create a New Space

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in the details:
   - **Space name**: `finbrief-assistant` (or your preferred name)
   - **Owner**: Select your username
   - **License**: Select "openrail" or "apache-2.0"
   - **Space SDK**: Select **Streamlit**
   - **Visibility**: Private (for now) or Public
4. Click **"Create Space"**

## Step 3: Prepare the Repository

Clone the Space repository locally:

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/finbrief-assistant
cd finbrief-assistant
```

## Step 4: Copy Project Files

Copy all project files to the cloned directory:

```bash
# Copy all files from your local ai-finance-assistant to the HF space
cp -r /path/to/ai-finance-assistant/* .
```

File structure should look like:
```
.
├── app.py
├── requirements.txt
├── README.md
├── HUGGINGFACE_DEPLOYMENT.md
├── src/
│   ├── config.py
│   ├── graph.py
│   ├── state.py
│   ├── agents/
│   ├── tools/
│   ├── scripts/
│   └── data/
│       ├── knowledge_base/
│       │   └── sample_articles/
│       └── session/
```

## Step 5: Set Up Environment Variables

Create a `.streamlit/secrets.toml` file in your HF Space (or use the Secrets feature):

**Option A: Using HF Space Secrets UI (Recommended)**
1. Go to your Space settings
2. Click on **"Repository secrets"** tab
3. Add the following secrets:
   - **OPENAI_API_KEY**: Your OpenAI API key
   - **NEWSAPI_KEY**: Your NewsAPI key

**Option B: Using `.streamlit/secrets.toml`** (Less secure, not recommended for production)
```toml
OPENAI_API_KEY = "your_openai_api_key_here"
NEWSAPI_KEY = "your_newsapi_key_here"
```

## Step 6: Update Requirements

The `requirements.txt` is already optimized for HF Spaces. It includes:
- streamlit>=1.33.0
- langchain and related packages
- faiss-cpu (instead of faiss-gpu)
- yfinance, pandas, numpy, matplotlib
- All other dependencies

No changes needed unless you want to pin specific versions.

## Step 7: Create/Update `app.py`

The app.py is already configured to work with HF Spaces. Key features:
- Uses `pathlib.Path` for all file operations
- Automatically creates data directories
- Reads secrets from environment variables
- Streamlit-compatible UI

## Step 8: Create `.gitignore`

Create a `.gitignore` file to avoid committing unnecessary files:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv

# Project specific
*.sqlite3
src/data/cache/
src/data/session/
src/data/knowledge_base/faiss_index/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

## Step 9: Commit and Push to HF

```bash
git add .
git commit -m "Initial deployment: FinBrief AI Finance Assistant"
git push
```

The Space will automatically build and deploy!

## Step 10: Monitor Deployment

1. Go to your Space page: `https://huggingface.co/spaces/YOUR_USERNAME/finbrief-assistant`
2. Click on **"Logs"** to see build progress
3. Once complete, click **"App"** to view your deployed application

## Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution**: Check that all imports in `src/` files use relative imports (e.g., `from ..config import settings`)

### Issue: "FileNotFoundError: KB_DIR not found"
**Solution**: The app automatically creates `src/data/knowledge_base/` at runtime. Ensure sample article files are in the repository.

### Issue: "API Key not found"
**Solution**: 
1. Check that secrets are properly set in HF Space settings
2. Verify environment variable names match exactly: `OPENAI_API_KEY`, `NEWSAPI_KEY`
3. Restart the Space after adding secrets

### Issue: FAISS index not found
**Solution**: The index will be built on first run. This may take a few minutes depending on:
- Number of documents
- OpenAI API availability
- Server resources

Wait for app to finish loading, then refresh.

### Issue: "Permission Denied" errors on file operations
**Solution**: HF Spaces have write access to the repo. Ensure all paths use `pathlib.Path` (already done).

## Environment Variables Reference

All paths use `pathlib.Path` and are configured in `src/config.py`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | Required | OpenAI API authentication |
| `NEWSAPI_KEY` | Required | NewsAPI authentication |
| `KB_DIR` | `src/data/knowledge_base/sample_articles` | Knowledge base documents |
| `FAISS_INDEX_DIR` | `src/data/knowledge_base/faiss_index` | Vector index storage |
| `CACHE_DB_PATH` | `src/data/cache.sqlite3` | Market data cache |
| `MARKET_CACHE_TTL_SECONDS` | `1800` (30 min) | Cache duration |
| `LLM_MODEL` | `gpt-4o-mini` | LLM model selection |

## Performance Notes

**On Hugging Face Spaces (Free tier):**
- First load: ~30-60 seconds (FAISS index building if new)
- Subsequent loads: ~5-10 seconds
- Max concurrent users: Limited by Space resources
- Memory: ~3-4 GB

**Recommendations:**
- Upgrade to a paid tier if experiencing timeout issues
- Consider using GPU Space if budget allows (for faster inference)
- Monitor logs for any errors

## Data Persistence

**Session Data:**
- Thread IDs stored in `src/data/session/thread_id.txt`
- Conversation history persists via SQLite checkpoint

**Cache:**
- Market data cached in `src/data/cache.sqlite3`
- FAISS index stored in `src/data/knowledge_base/faiss_index/`

All data is stored within the repository and will persist across Space restarts.

## Security Considerations

1. **Never commit secrets** - Always use HF Space secrets UI
2. **Use `.gitignore`** - Exclude sensitive files and caches
3. **Keep dependencies updated** - Regularly update requirements.txt
4. **Monitor API usage** - Track OpenAI and NewsAPI quota

## Updating Your Space

To update the Space with new code:

```bash
cd /path/to/your/hf-space-clone
git pull
# Make your changes
git add .
git commit -m "Update: description of changes"
git push
```

The Space will automatically rebuild with the latest code.

## Additional Resources

- [Hugging Face Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [LangChain Documentation](https://python.langchain.com/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)

## Support

If you encounter issues:
1. Check the Space logs for error messages
2. Verify all environment variables are set correctly
3. Ensure all required files are present (check `.gitignore`)
4. Check HF Community forum: https://huggingface.co/spaces

---

**Deployed on**: [Your Space URL]
**Last Updated**: February 2025
