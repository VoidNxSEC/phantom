# Dependency Audit — 2026-02-04

## Removed (not imported anywhere in src/)

| Package | Reason |
|---------|--------|
| `pandas` | Zero imports in active code |
| `polars` | Zero imports in active code |
| `transformers` | Zero imports in active code (sentence-transformers pulls what we need) |
| `chromadb` | Zero imports in active code; FAISS is the vector store |

## Kept (verified usage)

| Package | Used in |
|---------|---------|
| `sentence-transformers` | cerebro/rag_engine.py, core/embeddings.py |
| `faiss-cpu` | rag/vectors.py, core/cortex.py, cerebro/rag_engine.py |
| `tiktoken` | core/cortex.py |
| `nltk` | analysis/sentiment_analysis.py |
| `scikit-learn` | analysis/ modules |
| `numpy` | core/embeddings.py, analysis/ |
| `fastapi` | api/ |
| `uvicorn` | api/app.py (serve entrypoint) |
| `requests` | providers/llamacpp.py |
| `httpx` | api/ async clients |
| `pydantic` | models across all modules |
| `rich` | cli/ |
| `typer` | cli/main.py |
| `psutil` | analysis/latency_optimizer.py |
| `python-magic` | pipeline/ file classification |
| `pyyaml` | config loading |
| `aiofiles` | api/ async file ops |

## Changes

- All versions pinned to `>=X.Y, <NEXT_MAJOR`
- Added `safety` + `pip-audit` to `[dev]` for CVE scanning
