<div align="center">

# PHANTOM

```
╔══════════════════════════════════════════════════════════════════╗
║  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗ ║
║  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║ ║
║  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║ ║
║  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║ ║
║  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║ ║
║  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝ ║
╚══════════════════════════════════════════════════════════════════╝
```

**Living Machine Learning Framework**

_Production-grade document intelligence, RAG pipeline, and AI classification system_

[![CI](https://github.com/kernelcore/phantom/actions/workflows/ci.yml/badge.svg)](https://github.com/kernelcore/phantom/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![NixOS](https://img.shields.io/badge/NixOS-5277C3.svg)](https://nixos.org/)

[Features](#features) | [Quick Start](#quick-start) | [Architecture](#architecture) | [Contributing](CONTRIBUTING.md)

</div>

---

## 🏗️ System Architecture

### High-Level Component Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        CLI[CLI Interface<br/>Typer + Rich]
        API[REST API<br/>FastAPI]
        GUI[Desktop App<br/>Tauri + React]
    end

    subgraph "Application Layer"
        CORTEX[CORTEX Engine<br/>Document Intelligence]
        RAG[RAG Pipeline<br/>Vector Search]
        ANALYSIS[Analysis Suite<br/>NLP + ML]
    end

    subgraph "Processing Layer"
        CHUNKER[Semantic Chunker<br/>Tiktoken]
        EMBEDDER[Embedding Generator<br/>sentence-transformers]
        CLASSIFIER[LLM Classifier<br/>Multi-threaded]
        PIPELINE[DAG Pipeline<br/>Orchestration]
    end

    subgraph "Storage Layer"
        FAISS[(FAISS Index<br/>Vector DB)]
        CACHE[(Semantic Cache<br/>Redis)]
        FS[(File System<br/>Document Store)]
    end

    subgraph "External Services"
        LLAMA[llama.cpp Server<br/>Local Inference]
    end

    CLI --> CORTEX
    API --> CORTEX
    GUI --> API

    CORTEX --> CHUNKER
    CORTEX --> CLASSIFIER
    CORTEX --> RAG

    RAG --> EMBEDDER
    RAG --> FAISS

    CLASSIFIER --> LLAMA

    EMBEDDER --> FAISS
    CHUNKER --> PIPELINE

    PIPELINE --> FS
    RAG --> CACHE

    style CORTEX fill:#4CAF50,stroke:#2E7D32,color:#fff
    style RAG fill:#2196F3,stroke:#1565C0,color:#fff
    style FAISS fill:#FF9800,stroke:#E65100,color:#fff
    style LLAMA fill:#9C27B0,stroke:#6A1B9A,color:#fff
```

### Data Flow - Document Processing Pipeline

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant CLI
    participant CortexProcessor
    participant SemanticChunker
    participant LLMProvider
    participant EmbeddingGen
    participant FAISSStore
    participant VRAMMonitor

    User->>CLI: phantom process doc.md
    CLI->>CortexProcessor: process_document()

    CortexProcessor->>VRAMMonitor: Check VRAM availability
    VRAMMonitor-->>CortexProcessor: 6.5GB available

    CortexProcessor->>SemanticChunker: chunk_text(doc, size=1024)
    SemanticChunker-->>CortexProcessor: [chunk1, chunk2, ..., chunkN]

    par Parallel Classification
        CortexProcessor->>LLMProvider: classify(chunk1)
        CortexProcessor->>LLMProvider: classify(chunk2)
        CortexProcessor->>LLMProvider: classify(chunkN)
    end

    LLMProvider-->>CortexProcessor: [insights1, insights2, ..., insightsN]

    CortexProcessor->>EmbeddingGen: generate_embeddings(chunks)
    EmbeddingGen-->>CortexProcessor: vectors[768-dim]

    CortexProcessor->>FAISSStore: index_vectors(vectors, metadata)
    FAISSStore-->>CortexProcessor: index_id

    CortexProcessor-->>CLI: ProcessingResult(insights, index_id)
    CLI-->>User: ✅ Processed | 📊 Insights | 🔍 Indexed
```

### Deployment Architecture

```mermaid
graph LR
    subgraph "Development"
        DEV[Nix Development Shell]
        PRE[Pre-commit Hooks]
    end

    subgraph "CI/CD Pipeline"
        LINT[Lint & Format<br/>Ruff]
        TEST[Unit Tests<br/>pytest + coverage]
        SECURITY[Security Scan<br/>Bandit + pip-audit]
        BUILD[Build<br/>Python + Nix]
        CODEQL[CodeQL<br/>SAST Analysis]
        SBOM[SBOM Generation<br/>CycloneDX]
    end

    subgraph "Release"
        PYPI[PyPI<br/>Python Package]
        GHR[GitHub Release<br/>Binaries]
        CACHIX[Cachix<br/>Nix Cache]
    end

    subgraph "Deployment"
        NIXOS[NixOS Module<br/>System Service]
        DOCKER[Docker Container<br/>OCI Image]
        K8S[Kubernetes<br/>Helm Chart]
    end

    DEV --> PRE
    PRE --> LINT
    LINT --> TEST
    TEST --> SECURITY
    SECURITY --> CODEQL
    CODEQL --> SBOM
    SBOM --> BUILD

    BUILD --> PYPI
    BUILD --> GHR
    BUILD --> CACHIX

    PYPI --> DOCKER
    GHR --> NIXOS
    CACHIX --> NIXOS
    DOCKER --> K8S

    style CODEQL fill:#28a745,stroke:#1e7e34,color:#fff
    style SBOM fill:#007bff,stroke:#0056b3,color:#fff
    style SECURITY fill:#dc3545,stroke:#c82333,color:#fff
```

### State Machine - Resource Management

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> Monitoring: Start Processing
    Monitoring --> Processing: VRAM > 4GB
    Monitoring --> Waiting: VRAM < 512MB

    Processing --> Monitoring: Check VRAM
    Processing --> Throttled: VRAM < 256MB (Critical)
    Processing --> Completed: All Tasks Done

    Waiting --> Monitoring: VRAM Recovered
    Waiting --> Failed: Timeout (5min)

    Throttled --> Processing: VRAM > 512MB
    Throttled --> Failed: Sustained Critical

    Completed --> [*]
    Failed --> [*]

    note right of Monitoring
        Real-time nvidia-smi polling
        Threshold-based throttling
    end note

    note right of Processing
        Thread pool: 4-8 workers
        Batch size: dynamic
    end note
```

---

## What is Phantom?

Phantom is a **living ML framework** that transforms unstructured documents into actionable intelligence. Built on a foundation of semantic chunking, vector embeddings, and parallel LLM inference, Phantom provides production-ready tools for document classification, insight extraction, and RAG-powered question answering.

### Core Philosophy

- **Living Framework**: Continuously evolving components that adapt to your data
- **Local-First**: Runs entirely on your infrastructure with llama.cpp
- **Declarative**: Fully reproducible Nix-based environment
- **Production-Grade**: VRAM monitoring, resource throttling, parallel processing
- **Modular**: Use individual components or the complete pipeline

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ PHANTOM v2.0                                                    │
│ Living ML Framework Pipeline                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌───────────────┼───────────────┐
        │               │               │
  ┌─────▼─────┐   ┌────▼────┐   ┌─────▼──────┐
  │   CORE    │   │   RAG   │   │  ANALYSIS  │
  ├───────────┤   ├─────────┤   ├────────────┤
  │  Cortex   │   │ Vectors │   │ Sentiment  │
  │ Chunking  │   │  FAISS  │   │  Entities  │
  │Embeddings │   │ Search  │   │   Topics   │
  └─────┬─────┘   └────┬────┘   └─────┬──────┘
        │              │              │
        └──────┬───────┴──────┬───────┘
               │              │
        ┌──────▼──────┐ ┌────▼────────┐
        │  PIPELINE   │ │  PROVIDERS  │
        ├─────────────┤ ├─────────────┤
        │  DAG Exec   │ │ llama.cpp   │
        │ Classifier  │ │ (local)     │
        │ Sanitizer   │ └─────────────┘
        └──────┬──────┘
               │
        ┌──────┴──────┬──────────┐
        │             │          │
   ┌────▼─────┐ ┌────▼─────┐
   │   CLI    │ │   API    │
   ├──────────┤ ├──────────┤
   │  Typer   │ │ FastAPI  │
   │ Rich UI  │ │   REST   │
   └──────────┘ └──────────┘
```

---

## Features

### Document Intelligence (CORTEX)

- **Semantic Chunking**: Intelligent text splitting that preserves context
- **Parallel Classification**: Multi-threaded LLM inference with retry logic
- **Insight Extraction**: Themes, patterns, learnings, concepts, recommendations
- **Pydantic Validation**: Strict schema enforcement for all extracted data

### RAG Pipeline

- **Vector Embeddings**: sentence-transformers with local inference
- **FAISS Indexing**: Blazing-fast similarity search (CPU/GPU)
- **Semantic Caching**: Reduce redundant computations
- **Hybrid Search**: Combine vector and keyword search

### Resource Management

- **VRAM Monitoring**: Real-time GPU memory tracking via nvidia-smi
- **Auto-Throttling**: Pause processing when resources are low
- **Parallel Execution**: ThreadPool-based concurrent processing
- **Progress Tracking**: Rich terminal UI with live updates

### Production Features

- **Declarative Environment**: Fully reproducible Nix flake
- **Type Safety**: Complete Pydantic models for all data structures
- **API Server**: FastAPI REST endpoints with async support
- **CLI Interface**: Feature-rich Typer CLI with beautiful output
- **Testing**: Comprehensive pytest suite

---

## Quick Start

### NixOS (Recommended)

```bash
git clone https://github.com/kernelcore/phantom.git
cd phantom

nix develop          # enters reproducible dev shell

phantom version      # verify install
phantom-api          # start REST API on :8000
phantom --help       # full CLI reference
```

### Standard Python

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

phantom version
```

---

## Usage

### CLI

```bash
# Extract insights from a document
phantom extract -i ./docs -o output.jsonl

# Analyze a single file
phantom analyze report.md --sentiment --entities

# Classify files in a directory
phantom classify ./input --dry-run

# Scan for sensitive data
phantom scan ./project

# RAG pipeline
phantom rag query "What are the security patterns?"
phantom rag ingest ./knowledge

# Start API server
phantom api serve --host 127.0.0.1 --port 8000 --reload
```

### Python API

```python
from phantom import CortexProcessor
from phantom.providers.llamacpp import LlamaCppProvider

# Initialize processor
processor = CortexProcessor(
    provider=LlamaCppProvider(base_url="http://localhost:8080"),
    chunk_size=1024,
    chunk_overlap=128,
    workers=4,
    enable_vectors=True,
    embedding_model="all-MiniLM-L6-v2",
    verbose=True
)

# Process document
insights = processor.process_document("document.md")

# Access extracted data
for theme in insights.themes:
    print(f"{theme.title}: {theme.description}")

# Semantic search
results = processor.search("security best practices", top_k=5)
for result in results:
    print(f"Score: {result.score:.3f} | {result.text[:100]}...")

# Save vector index
processor.save_index("./phantom_index")
```

### REST API

```bash
# Start server
phantom api serve

# Health check
curl http://localhost:8000/health

# Extract insights
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"content": "# My Document\n\nContent here.", "filename": "doc.md"}'

# Upload file
curl -X POST http://localhost:8000/upload -F "file=@report.md"

# RAG query
curl "http://localhost:8000/rag/query?question=What+is+Phantom?"

# Judge bundle (AI-OS-Agent integration)
curl -X POST http://localhost:8000/judge \
  -H "Content-Type: application/json" \
  -d '{"timestamp": "2026-02-04T00:00:00Z", "hostname": "host", "metrics": {}, "alerts": [], "logs": []}'
```

---

## Module Reference

### `phantom.core`

**CortexProcessor** - Main intelligence engine

- Semantic chunking with tiktoken
- Parallel LLM classification
- FAISS vector indexing
- Resource monitoring

**EmbeddingGenerator** - Vector embeddings

- sentence-transformers models
- Batch processing
- GPU acceleration support

**SemanticChunker** - Intelligent text splitting

- Markdown-aware splitting
- Token counting with tiktoken
- Configurable overlap

### `phantom.rag`

**FAISSVectorStore** - Vector database

- CPU/GPU FAISS support
- Metadata filtering
- Persistence to disk

**SearchResult** - Typed search results

- Distance scores
- Metadata extraction
- Ranking utilities

### `phantom.analysis`

**SentimentAnalyzer** - Sentiment detection
**EntityExtractor** - Named entity recognition
**TopicModeler** - LDA topic modeling

### `phantom.pipeline`

**DAGPipeline** - Directed acyclic graph execution
**FileClassifier** - Document classification
**DataSanitizer** - PII removal and sanitization

### `phantom.providers`

**LlamaCppProvider** - llama.cpp local inference (TURBO)

> Cloud providers (OpenAI, Anthropic, DeepSeek) are planned.
> Extend `AIProvider` base class to add custom backends.

---

## Configuration

### Environment Variables

```bash
# LLM Provider
export PHANTOM_LLAMACPP_URL="http://localhost:8080"
export PHANTOM_OPENAI_API_KEY="sk-..."

# Resource Limits
export PHANTOM_VRAM_WARNING_MB=512
export PHANTOM_VRAM_CRITICAL_MB=256
export PHANTOM_MAX_WORKERS=8

# Processing
export PHANTOM_CHUNK_SIZE=1024
export PHANTOM_CHUNK_OVERLAP=128
export PHANTOM_BATCH_SIZE=10

# Embeddings
export PHANTOM_EMBEDDING_MODEL="all-MiniLM-L6-v2"
export PHANTOM_VECTOR_BACKEND="faiss"
```

### NixOS Development

```bash
# All dependencies are declared in flake.nix
cd phantom && nix develop   # enters the dev shell

# Build the package
nix build .#phantom
nix run .#phantom -- --help
```

---

## Development

### Project Structure

```
phantom/
├── src/phantom/
│   ├── core/          # CORTEX engine, embeddings, chunking
│   ├── rag/           # Vector stores (FAISS), search
│   ├── analysis/      # Sentiment, SPECTRE, viability
│   ├── pipeline/      # DAG orchestration, classification, sanitization
│   ├── providers/     # LLM providers (llama.cpp)
│   ├── cerebro/       # RAG engine + knowledge integration
│   ├── neutron/       # Compliance guardrails (SENTINEL)
│   ├── api/           # FastAPI REST server + Judge API
│   └── cli/           # Typer CLI interface
├── tests/
│   ├── unit/          # Unit tests
│   ├── integration/   # API + CLI integration tests
│   └── e2e/           # End-to-end pipeline tests
├── .archive/          # Dead code + experimental (audited)
├── intelagent/        # Rust agent (part of ai-agent-os ecosystem)
├── docs/              # Documentation
└── flake.nix          # Reproducible Nix environment
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=phantom --cov-report=html

# Specific module
pytest tests/test_cortex.py -v
```

### Code Quality

```bash
# Format code
ruff format src/

# Lint
ruff check src/

# Type checking
mypy src/
```

---

## Roadmap

### Current (Phase 0–4)
- [x] Critical import fixes and dead code cleanup
- [x] Dependency audit and version pinning
- [x] Test structure: unit / integration / e2e
- [x] CI/CD pipeline (lint, test, security scan, release)
- [ ] Coverage target: 70% across all modules

### Upcoming
- [ ] Cloud providers (OpenAI, Anthropic, DeepSeek)
- [ ] Full CLI command implementations (extract, analyze, classify)
- [ ] RAG query and ingestion pipeline
- [ ] Desktop app (GTK4 — archived, revisit later)
- [ ] Docker + NixOS module packaging
- [ ] Prometheus metrics endpoint (`/metrics`)

---

## Contributing

Contributions are welcome! Please read our guidelines:

- [CONTRIBUTING.md](CONTRIBUTING.md) - Development workflow and code standards
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - Community guidelines
- [SECURITY.md](SECURITY.md) - Security policy and vulnerability reporting

### Development Workflow

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes with tests
4. Run quality checks (`pytest && ruff check`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **llama.cpp**: Fast LLM inference
- **sentence-transformers**: Local embedding models
- **FAISS**: Efficient similarity search
- **Nix**: Reproducible environments
- **FastAPI**: Modern Python web framework

---

## Support

- **Documentation**: [docs/](docs/)
- **Security**: [SECURITY.md](SECURITY.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

Phantom v2.0 | NixOS + llama.cpp | MIT License
