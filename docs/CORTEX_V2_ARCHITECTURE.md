# CORTEX v2.0 — Chunking & Embeddings Architecture

## Overview

CORTEX v2.0 introduced semantic chunking and vector embeddings as a preprocessing stage before LLM classification. Instead of sending entire documents to the LLM, CORTEX splits text into token-bounded chunks and processes them independently. This enables:

- **Lower per-request memory usage**: each LLM call processes a 1k-token chunk instead of a full document
- **Parallel classification**: chunks are independent and can be processed concurrently via a thread pool
- **Full document coverage**: no content is truncated, regardless of document length
- **Vector search**: chunk embeddings are indexed in FAISS for retrieval after processing

---

## Pipeline Stages

```
Input: Markdown / Text / PDF
    │
    ├─► STAGE 1: Semantic Chunking
    │   ├─ Strategy: recursive splitting by headers (markdown-aware)
    │   ├─ Size: 512–1024 tokens per chunk (configurable)
    │   ├─ Overlap: 128 tokens (preserves cross-boundary context)
    │   └─ Metadata: source_file, chunk_id, header hierarchy
    │
    ├─► STAGE 2: Embedding Generation
    │   ├─ Model: sentence-transformers (local, default: all-MiniLM-L6-v2)
    │   ├─ Batch size: 32 chunks
    │   └─ Output: float32 vectors (dimensionality depends on model)
    │
    ├─► STAGE 3: Vector Storage (FAISS)
    │   ├─ Index type: flat inner-product (cosine similarity)
    │   ├─ BM25 sparse index built lazily alongside dense index
    │   └─ Stored per chunk: text, embedding, metadata
    │
    ├─► STAGE 4: Classification
    │   ├─ Each chunk sent to llama.cpp for LLM classification
    │   ├─ Thread pool (configurable workers, default 4–8)
    │   ├─ Retry logic on transient failures
    │   └─ Output: structured JSON per chunk (Pydantic-validated)
    │
    └─► STAGE 5: Search & Retrieval
        ├─ Dense search: FAISS cosine similarity
        ├─ Sparse search: BM25 keyword matching
        ├─ Hybrid search: BM25 + FAISS fused via Reciprocal Rank Fusion
        └─ RAG: retrieve context chunks, build prompt, generate answer
```

---

## Chunking Strategies

### Recursive by Headers (default for markdown)

Preserves document structure. Each heading boundary produces a chunk break, with chunks capped at `max_tokens`.

```
Document
├─ # Header 1
│  ├─ ## Subheader 1.1  → Chunk 1
│  └─ ## Subheader 1.2  → Chunk 2
└─ # Header 2
   └─ ## Subheader 2.1  → Chunk 3
```

- Chunks are semantically coherent (single section per chunk)
- Header hierarchy is preserved in chunk metadata

### Sliding Window (for unstructured text)

Fixed-size window with configurable overlap:

```
[────────────────]
      [────────────────]
            [────────────────]
```

Used when the input has no structural markers (plain text, logs).

---

## VRAM Considerations

Chunk-level processing reduces per-request VRAM compared to full-document processing. The tradeoff is more LLM calls per document.

| Component | Approximate VRAM |
|-----------|-----------------|
| Embedding model (MiniLM-L6-v2) | ~500 MB |
| LLM context per chunk (1k tokens) | ~0.75 GB |
| Typical headroom needed | ~1.5–2 GB |

Example with a 24 GB GPU running Qwen3-30B Q4_K_M:

```
Model weights:    16.8 GB
Embedding model:   0.5 GB
Chunk context:     0.8 GB
Overhead:          0.5 GB
───────────────────────────
Total:            18.6 GB
Free:              5.4 GB
```

These are rough estimates. Actual usage depends on model quantization, batch size, and concurrent workers. The VRAM monitor (`/api/system/metrics`) reports real-time values during processing.

---

## Parallel Processing

Chunks are classified independently via a thread pool:

```python
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = []
    for doc in documents:
        chunks = chunk_document(doc)
        for chunk in chunks:
            future = executor.submit(process_chunk, chunk)
            futures.append(future)
    results = [f.result() for f in as_completed(futures)]
```

The VRAM monitor throttles submission when GPU memory drops below the configured critical threshold (default: 256 MB free).

---

## Design Decisions

### Embedding Model

The default model is `all-MiniLM-L6-v2` (384 dimensions, ~80 MB). It provides a reasonable balance between speed and retrieval quality for general-purpose document search.

| Model | Dimensions | Size | Notes |
|-------|-----------|------|-------|
| all-MiniLM-L6-v2 | 384 | 80 MB | Default. Fast, low memory |
| all-mpnet-base-v2 | 768 | 420 MB | Higher retrieval quality |

The model is configurable via `PHANTOM_EMBEDDING_MODEL`.

### Vector Store

FAISS was chosen for its simplicity and zero-infrastructure requirement — no external server needed. The index lives in-process and can be saved to / loaded from disk.

Tradeoffs:
- **No built-in persistence server** — the application must manage save/load
- **No metadata filtering at query time** — filtering is done post-search in application code
- **In-memory** — index size is bounded by available RAM

BM25 sparse search (via `rank_bm25`) is built lazily on first sparse/hybrid query and invalidated on each `add()` call.

---

## Implementation Status

| Component | Status | File |
|-----------|--------|------|
| Semantic chunker | Shipped | `src/phantom/core/cortex.py` |
| Embedding generator | Shipped | `src/phantom/core/embeddings.py` |
| FAISS vector store | Shipped | `src/phantom/rag/vectors.py` |
| Hybrid search (BM25 + FAISS) | Shipped | `src/phantom/rag/vectors.py` |
| Parallel chunk classification | Shipped | `src/phantom/core/cortex.py` |
| VRAM monitoring + throttling | Shipped | `src/phantom/core/cortex.py` |
| REST API endpoints | Shipped | `src/phantom/api/app.py` |
| ChromaDB integration | Not planned | — |
| Qdrant integration | Not planned | — |
| Topic clustering | Not implemented | — |
| Incremental processing (skip existing) | Not implemented | — |

---

## Limitations

- **No incremental indexing**: re-indexing a document adds duplicate chunks. The caller must manage deduplication or clear the index first.
- **No cross-chunk reasoning**: each chunk is classified independently. The LLM does not see the full document during classification.
- **Embedding model runs on CPU by default**: GPU acceleration requires PyTorch with CUDA. The sentence-transformers model will use GPU automatically if available.
- **BM25 index is rebuilt from scratch** on each `add()` call. For large corpora with frequent updates, this becomes expensive.
