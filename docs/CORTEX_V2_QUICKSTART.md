# CORTEX v2.0 — Quick Start

## What Changed in v2.0

CORTEX v2.0 processes documents by splitting them into semantic chunks before sending them to the LLM. This means:

- Documents of any length are fully processed (no truncation)
- Each LLM call handles a small chunk, reducing per-request memory usage
- Chunks are processed in parallel via a thread pool
- Chunk embeddings are indexed in FAISS for vector search

---

## Installation

Dependencies are declared in `flake.nix`:

```bash
nix develop
```

Or via pip:

```bash
pip install -e ".[dev]"
```

The embedding model (`all-MiniLM-L6-v2`, ~80 MB) downloads automatically on first use.

---

## Basic Usage

### Python API

```python
from phantom.core.cortex import CortexProcessor, SemanticChunker
from phantom.core.embeddings import EmbeddingGenerator
from phantom.rag.vectors import FAISSVectorStore

# 1. Chunk a document
chunker = SemanticChunker(max_tokens=1024, overlap=128)
chunks = chunker.chunk_text(text, "document.md")

# 2. Generate embeddings
embedder = EmbeddingGenerator()  # default: all-MiniLM-L6-v2
embeddings = embedder.encode([c.text for c in chunks])

# 3. Index in FAISS
store = FAISSVectorStore(embedding_dim=embedder.dimension)
metadata = [{"source": "document.md", "chunk_id": c.chunk_id} for c in chunks]
store.add(embeddings, [c.text for c in chunks], metadata)

# 4. Search
query_embedding = embedder.encode(["how to handle errors"])[0]
results = store.search(query_embedding, top_k=5)
for r in results:
    print(f"{r.score:.3f}: {r.text[:100]}")
```

### Full Pipeline (CortexProcessor)

```python
from phantom.core.cortex import CortexProcessor
from phantom.providers.llamacpp import LlamaCppProvider

processor = CortexProcessor(
    provider=LlamaCppProvider(base_url="http://localhost:8080"),
    chunk_size=1024,
    chunk_overlap=128,
    workers=4,
    enable_vectors=True,
    embedding_model="all-MiniLM-L6-v2",
)

insights = processor.process_document("report.md")
print(f"Themes: {len(insights.themes)}")
print(f"Patterns: {len(insights.patterns)}")
```

### REST API

```bash
# Start the server
phantom-api

# Process a document
curl -X POST http://localhost:8008/process -F "file=@report.md"

# Index for search
curl -X POST http://localhost:8008/vectors/index -F "file=@report.md"

# Search
curl -X POST http://localhost:8008/vectors/search \
  -H "Content-Type: application/json" \
  -d '{"query": "error handling", "top_k": 5, "mode": "hybrid"}'
```

---

## Chunking Strategies

### Recursive (default)

Splits by markdown headers, respecting document structure. Each section becomes a chunk, further split if it exceeds `max_tokens`.

Best for: structured documents with headers.

### Sliding Window

Fixed-size chunks with configurable overlap. No awareness of document structure.

Best for: plain text, logs, unstructured input.

---

## Embedding Models

The default model is `all-MiniLM-L6-v2` (384 dimensions, ~80 MB). For higher retrieval quality at the cost of speed and memory:

| Model | Dimensions | Size | Notes |
|-------|-----------|------|-------|
| `all-MiniLM-L6-v2` | 384 | 80 MB | Default — fast, low memory |
| `all-mpnet-base-v2` | 768 | 420 MB | Better retrieval quality |

Change via environment variable:

```bash
export PHANTOM_EMBEDDING_MODEL="all-mpnet-base-v2"
```

---

## Search Modes

The vector store supports three search modes:

| Mode | Method | Use case |
|------|--------|----------|
| `dense` | FAISS cosine similarity | Default — semantic matching |
| `sparse` | BM25 keyword matching | Exact term lookup |
| `hybrid` | BM25 + FAISS via Reciprocal Rank Fusion | Best overall retrieval quality |

---

## See Also

- [CORTEX_V2_ARCHITECTURE.md](CORTEX_V2_ARCHITECTURE.md) — architecture and design decisions
- [VRAM_CALCULATOR.md](VRAM_CALCULATOR.md) — hardware planning
