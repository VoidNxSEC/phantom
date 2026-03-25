# Executive Summary

## Overview

Phantom is a production-ready document intelligence framework that transforms unstructured data into an active, programmatic knowledge base.

Rather than routing your company's operational data through third-party platforms, Phantom orchestrates the entire intelligence lifecycle—from semantic chunking to LLM classification and FAISS vector indexing—directly on your infrastructure.

It provides a rational approach to extracting value from documents: uncompromising privacy, predictable performance at scale, and a complete elimination of recurring cloud inference costs.

The project is structured into two core runtime components:

- **Phantom Core** (Python) — The primary pipeline. Handles NLP, document processing, semantic search, and the REST API.
- **IntelAgent** (Rust) — The agent infrastructure. Provides security auditing, context memory, quality gates, and governance across the toolset.

## Architecture

The system is organized into three layers: ingestion, processing, and retrieval.

```javascript
graph TD
    subgraph "Ingestion"
        DOCS[Documents] -->|Upload| API[REST API<br/>FastAPI]
    end

    subgraph "Processing"
        API --> CORTEX[CORTEX Engine<br/>Chunking + Classification]
        API --> EMBEDDER[Embedding Generator<br/>sentence-transformers]
        CORTEX -->|llama.cpp| LLM[Local LLM]
    end

    subgraph "Retrieval"
        EMBEDDER --> FAISS[(FAISS Index)]
        FAISS --> SEARCH[Hybrid Search<br/>BM25 + Cosine]
        SEARCH --> RESULTS[Structured Results<br/>JSON + Pydantic]
    end
```

## Components

### Phantom Core (Python)

Handles document processing and serves the REST API.

- **CORTEX Engine**: semantic chunking (tiktoken), parallel LLM classification, insight extraction
- **RAG Pipeline**: FAISS vector store with hybrid search (BM25 + cosine via Reciprocal Rank Fusion)
- **Analysis**: sentiment scoring (NLTK VADER), named entity extraction (SPECTRE)
- **API**: FastAPI with Prometheus metrics, health/readiness probes, system resource monitoring
- **Pipeline**: PII detection and redaction, file fingerprinting (SHA-256), content routing by type

### IntelAgent (Rust)

Multi-crate workspace providing agent infrastructure. Modules include security/privacy auditing, governance, context memory, quality gates, and MCP protocol handling. Builds with Crane (Nix) and Tokio for async execution.

### Cortex Desktop (Tauri + SvelteKit)

Desktop interface with tabs for RAG chat, document processing, vector search, and prompt workbench. Framework is in place; UI components are minimal. See the [Roadmap](../README.md#roadmap) for current status.

## Technology Stack

| Component     | Technology                   | Purpose                                     |
| ------------- | ---------------------------- | ------------------------------------------- |
| Backend       | Python 3.11+, FastAPI        | API, document processing, ML pipeline       |
| Agent         | Rust, Tokio, Crane           | Security, governance, memory modules        |
| Desktop       | Tauri 2, SvelteKit           | Cross-platform desktop UI                   |
| Vector Store  | FAISS, sentence-transformers | Embedding generation and similarity search  |
| LLM Inference | llama.cpp                    | Local model serving (OpenAI-compatible API) |
| Build/Dev     | Nix Flakes, Just             | Reproducible environment, task automation   |
| CI/CD         | GitHub Actions               | Lint, test, security scan, CodeQL, SBOM     |

## Data Flow

1. **Upload**: user submits a document via API or CLI
2. **Chunking**: CORTEX splits text into semantic chunks (configurable size/overlap)
3. **Classification**: each chunk is sent to llama.cpp for parallel LLM classification
4. **Embedding**: sentence-transformers generates vector embeddings per chunk
5. **Indexing**: embeddings are stored in FAISS for retrieval
6. **Query**: users search the index via dense, sparse (BM25), or hybrid modes

## Platform Support

| Platform                      | Status                       |
| ----------------------------- | ---------------------------- |
| Linux (x86\_64)               | Supported (Nix, pip)         |
| macOS (Apple Silicon / Intel) | Supported (Nix, pip)         |
| Windows                       | Untested (pip — should work) |

Standalone binaries for Linux and macOS are planned.

## License

Apache License 2.0 — see [LICENSE](../LICENSE).
