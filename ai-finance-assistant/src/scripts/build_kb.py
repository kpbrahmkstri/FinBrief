from src.tools.rag import build_or_load_faiss

if __name__ == "__main__":
    build_or_load_faiss()
    print("KB FAISS index built/loaded successfully.")