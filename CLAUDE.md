# PHANTOM - Development Guide for Claude

> **Living Machine Learning Framework** - Production-grade document intelligence, RAG pipeline, and AI classification system.

**Version**: 2.0.0 (Beta)
**Python**: 3.11+
**License**: Apache-2.0
**Last Updated**: 2026-02-05

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Current State Assessment](#current-state-assessment)
- [Architecture Quick Reference](#architecture-quick-reference)
- [Development Priorities](#development-priorities)
- [Quality Assessment](#quality-assessment)
- [Frontend-Backend Integration](#frontend-backend-integration)
- [Key Files Reference](#key-files-reference)
- [Testing Strategy](#testing-strategy)
- [Common Tasks](#common-tasks)
- [Known Issues & TODOs](#known-issues--todos)

---

## 🎯 Project Overview

### What is Phantom?

Phantom is a **local-first AI document intelligence framework** that processes unstructured documents into actionable intelligence using:

- **CORTEX Engine**: Semantic chunking, parallel LLM classification, insight extraction
- **RAG Pipeline**: FAISS vector indexing with sentence-transformers embeddings
- **Multi-Interface**: CLI (Typer), REST API (FastAPI), Desktop UI (Tauri + SvelteKit)
- **Production-Ready**: VRAM monitoring, auto-throttling, thread pool concurrency, Prometheus metrics
- **Fully Reproducible**: Nix flake with locked dependencies

### Core Capabilities

1. **Document Processing**: Extract insights from markdown, text, PDFs
2. **Vector Search**: Semantic search over document embeddings (FAISS)
3. **Classification**: Multi-threaded LLM-based document classification
4. **Sentiment Analysis**: NLTK VADER + optional spaCy NER
5. **RAG Pipeline**: Question-answering over knowledge base
6. **Resource Management**: Real-time VRAM/RAM monitoring with auto-throttling

### Tech Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic 2.0
- **Frontend**: Tauri 2.0, SvelteKit, Svelte 5, Tailwind CSS
- **ML/NLP**: sentence-transformers, FAISS, NLTK, scikit-learn, tiktoken
- **Inference**: llama.cpp (local, OpenAI-compatible API)
- **Agent**: Rust (Crane build system, multi-crate workspace)
- **DevOps**: Nix flake, GitHub Actions (8 workflows), pre-commit hooks
- **Observability**: structlog, Prometheus metrics

---

## 📊 Current State Assessment

### ✅ Production-Ready Components

| Component           | Status     | Files                   | Test Coverage |
| ------------------- | ---------- | ----------------------- | ------------- |
| CORTEX Processor    | ✅ Complete | `core/cortex.py`        | High          |
| Semantic Chunker    | ✅ Complete | `core/cortex.py`        | High          |
| FAISS Vector Store  | ✅ Complete | `rag/vectors.py`        | High          |
| Sentiment Engine    | ✅ Complete | `analysis/sentiment.py` | High          |
| Embedding Generator | ✅ Complete | `core/embeddings.py`    | Medium        |
| LlamaCpp Provider   | ✅ Complete | `providers/llamacpp.py` | Medium        |
| FastAPI Server      | ✅ Complete | `api/app.py`            | High          |
| Prometheus Metrics  | ✅ Complete | `api/app.py`            | High          |
| Pydantic Schemas    | ✅ Complete | All modules             | High          |
| CI/CD Pipelines     | ✅ Complete | `.github/workflows/`    | N/A           |
| Nix Environment     | ✅ Complete | `flake.nix`             | N/A           |

### 🟡 Partially Implemented Components

| Component           | Status         | Missing             | Priority |
| ------------------- | -------------- | ------------------- | -------- |
| CLI Commands        | 🟡 Stubs       | Implementations     | High     |
| Desktop UI          | 🟡 Framework   | Components          | Medium   |
| RAG Query API       | 🟡 Endpoint    | Implementation      | High     |
| Document Upload     | 🟡 Endpoint    | Processing logic    | High     |
| Vector Indexing API | 🟡 Missing     | Full endpoint       | High     |
| Judge API           | 🟡 Integration | Full implementation | Low      |

### ❌ Not Implemented

- Cloud LLM Providers (OpenAI, Anthropic, DeepSeek)
- Kubernetes/Helm packaging
- Full desktop app UI (marked for GTK4 migration)
- Redis semantic cache integration
- Advanced prompt workbench features

### Code Quality Metrics

- **Total Python LOC**: 11,290 (33 source files)
- **Test Files**: 18 (unit, integration, e2e)
- **Test Coverage**: 70% minimum (enforced via pytest)
- **Linting**: Ruff (enforced in CI)
- **Type Checking**: mypy (enabled, non-strict mode)
- **Security Scanning**: bandit, pip-audit, cargo-audit
- **Documentation**: 20+ markdown files

---

## 🏗️ Architecture Quick Reference

### Directory Structure

```javascript
phantom/
├── src/phantom/              # Main Python source (11,290 LOC)
│   ├── core/                # CORTEX engine, embeddings, chunking
│   ├── rag/                 # Vector stores (FAISS), search
│   ├── analysis/            # Sentiment, SPECTRE, viability
│   ├── pipeline/            # DAG orchestration, classification
│   ├── providers/           # LLM providers (llama.cpp base)
│   ├── cerebro/             # RAG engine + knowledge integration
│   ├── neutron/             # Compliance guardrails (SENTINEL)
│   ├── api/                 # FastAPI REST server + Judge API
│   └── cli/                 # Typer CLI interface
├── tests/                   # 18 test files
│   ├── unit/                # Unit tests (isolated components)
│   ├── integration/         # API + CLI tests
│   └── e2e/                 # End-to-end pipeline tests
├── cortex-desktop/          # Tauri + SvelteKit + Svelte 5
├── intelagent/              # Rust agent (multi-crate workspace)
│   ├── crates/security/     # Privacy & audit modules
│   ├── crates/governance/   # DAO & rewards systems
│   ├── crates/memory/       # Context & knowledge graphs
│   ├── crates/quality/      # Automated peer review gates
│   └── crates/mcp/          # MCP protocol handlers
├── docs/                    # 20+ markdown documentation files
├── nix/                     # NixOS module definitions
└── .github/workflows/       # CI/CD pipelines (8 workflows)
```

### Data Flow

```javascript
User Input → CLI/API/Desktop
    ↓
CORTEX Processor → Semantic Chunker → Embeddings
    ↓
LLM Classifier (llama.cpp) → Insights Extraction
    ↓
FAISS Vector Store → RAG Pipeline
    ↓
Results (JSON + Pydantic validation)
```

### API Endpoints (Current)

| Endpoint     | Method | Status         | Returns              |
| ------------ | ------ | -------------- | -------------------- |
| `/health`    | GET    | ✅ Complete     | Health status        |
| `/ready`     | GET    | ✅ Complete     | Readiness checks     |
| `/metrics`   | GET    | ✅ Complete     | Prometheus metrics   |
| `/extract`   | POST   | 🟡 TODO        | Document insights    |
| `/upload`    | POST   | 🟡 Partial     | File upload          |
| `/rag/query` | GET    | 🟡 TODO        | RAG query            |
| `/judge`     | POST   | 🟡 Integration | AI-OS-Agent judgment |

### Missing API Endpoints (Needed for Frontend)

| Endpoint           | Method | Purpose                 | Frontend Usage                               |
| ------------------ | ------ | ----------------------- | -------------------------------------------- |
| `/process`         | POST   | Document processing     | `cortex-desktop/src/lib/api.ts:24`           |
| `/vectors/search`  | POST   | Vector semantic search  | `cortex-desktop/src/lib/api.ts:64`           |
| `/vectors/index`   | POST   | Index document to FAISS | `cortex-desktop/src/lib/api.ts:81`           |
| `/api/chat`        | POST   | RAG chat interface      | `cortex-desktop/src/routes/+page.svelte:145` |
| `/api/models`      | GET    | List available models   | `cortex-desktop/src/routes/+page.svelte:127` |
| `/api/prompt/test` | POST   | Test prompt rendering   | `cortex-desktop/src/routes/+page.svelte:209` |
| `/api/upload`      | POST   | Multi-file upload       | `cortex-desktop/src/routes/+page.svelte:287` |

---

## 🎯 Development Priorities

### Phase 1: Complete Backend API ✅ **COMPLETED** (2026-02-05)

**Goal**: Implement missing API endpoints so frontend can use real data instead of stubs.

**Status**: All 7 endpoints implemented and tested. See `PHASE1_IMPLEMENTATION.md` for details.

#### 1.1 Document Processing Endpoint

**File**: `src/phantom/api/app.py`

**Current**:

```python
@app.post("/extract", response_model=ExtractResponse)
async def extract(request: ExtractRequest):
    # TODO: Implement using CortexProcessor
    insights = { "themes": [], "patterns": [], ... }
```

**Needs**:

```python
from phantom.core.cortex import CortexProcessor

@app.post("/process")
async def process(file: UploadFile, chunk_strategy: str = "recursive", chunk_size: int = 1024):
    """Process document using CORTEX engine."""
    content = await file.read()
    processor = CortexProcessor()
    result = processor.extract_insights(content.decode(), filename=file.filename)
    return {
        "filename": file.filename,
        "insights": result.model_dump(),
        "processing_time": ...,
    }
```

**Frontend expects**: `cortex-desktop/src/lib/api.ts:20-31`

---

#### 1.2 Vector Search Endpoint

**File**: `src/phantom/api/app.py` (new endpoint)

**Needs**:

```python
from phantom.rag.vectors import FAISSVectorStore

@app.post("/vectors/search")
async def vector_search(query: str, top_k: int = 5):
    """Semantic search using FAISS."""
    store = FAISSVectorStore()  # Or singleton instance
    results = await store.search(query, top_k=top_k)
    return {
        "query": query,
        "results": [{"text": r.text, "score": r.score} for r in results],
        "total_results": len(results),
    }
```

**Frontend expects**: `cortex-desktop/src/lib/api.ts:63-75`

---

#### 1.3 Vector Indexing Endpoint

**File**: `src/phantom/api/app.py` (new endpoint)

**Needs**:

```python
@app.post("/vectors/index")
async def vector_index(file: UploadFile):
    """Index document into FAISS vector store."""
    content = await file.read()
    store = FAISSVectorStore()
    chunks = semantic_chunker.chunk(content.decode())
    count = await store.add_documents(chunks)
    return {"status": "indexed", "chunks_indexed": count}
```

**Frontend expects**: `cortex-desktop/src/lib/api.ts:77-88`

---

#### 1.4 RAG Chat Endpoint

**File**: `src/phantom/api/app.py` (replace `/rag/query`)

**Needs**:

```python
@app.post("/api/chat")
async def rag_chat(
    message: str,
    conversation_id: str,
    history: list[dict],
    context_size: int = 5,
    llm_provider: str = "local"
):
    """RAG-powered chat with context."""
    # 1. Vector search for relevant context
    store = FAISSVectorStore()
    context_chunks = await store.search(message, top_k=context_size)

    # 2. Build prompt with context
    prompt = build_rag_prompt(message, context_chunks, history)

    # 3. Call LLM
    provider = get_llm_provider(llm_provider)
    response = await provider.complete(prompt)

    return {
        "message": {
            "content": response,
            "sources": [{"text": c.text, "score": c.score} for c in context_chunks]
        }
    }
```

**Frontend expects**: `cortex-desktop/src/routes/+page.svelte:145-186`

---

#### 1.5 Models List Endpoint

**File**: `src/phantom/api/app.py` (new endpoint)

**Needs**:

```python
@app.get("/api/models")
async def list_models():
    """List available LLM models by provider."""
    return {
        "local": [
            {"id": "qwen-30b", "name": "Qwen 30B (Local)"},
            {"id": "llama-3-8b", "name": "Llama 3 8B (Local)"}
        ],
        "openai": [],  # Future: OpenAI models
        "anthropic": []  # Future: Claude models
    }
```

**Frontend expects**: `cortex-desktop/src/routes/+page.svelte:127-129`

---

### Phase 2: System Monitoring Integration (MEDIUM PRIORITY) 🟡

**Goal**: Expose real host machine metrics to frontend (CPU, memory, VRAM, temperature).

#### 2.1 Add System Metrics Endpoint

**File**: `src/phantom/api/app.py` (new endpoint)

**Implementation**:

```python
import psutil

@app.get("/api/system/metrics")
async def system_metrics():
    """Get real-time system resource metrics."""
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # VRAM monitoring (existing code in core/cortex.py:226)
    from phantom.core.cortex import get_vram_usage
    vram = get_vram_usage()

    return {
        "cpu": {
            "percent": cpu_percent,
            "count": psutil.cpu_count()
        },
        "memory": {
            "total": mem.total,
            "used": mem.used,
            "available": mem.available,
            "percent": mem.percent
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        },
        "vram": vram  # If GPU available
    }
```

**Frontend Integration**:

- Add system monitor component in `cortex-desktop/`
- Display real-time metrics in settings or dashboard tab
- Use for resource warnings before heavy operations

---

### Phase 3: Desktop UI Enhancement (LOW PRIORITY) 🟢

**Goal**: Complete the Cortex Desktop UI with functional components.

#### 3.1 Current State

**Framework**: Tauri 2 + SvelteKit + Svelte 5
**Status**: Infrastructure ready, minimal UI implemented
**File**: `cortex-desktop/src/routes/+page.svelte` (1,193 lines)

**Implemented Tabs**:

- ✅ Chat (RAG conversation)
- ✅ Process (document processing)
- ✅ Search (vector search)
- ✅ Workbench (prompt engineering)
- ✅ Library (saved prompts)
- ✅ Settings (API config)

**Issues**:

- Backend endpoints missing (Phase 1 priority)
- No real-time metrics display
- No error handling UI
- No processing progress indicators

#### 3.2 Enhancement Tasks

1. **Add System Monitor Tab**
   - Real-time CPU/memory/VRAM charts
   - Historical metrics (last 24h)
   - Resource alerts
2. **Improve Error Handling**
   - Toast notifications for API errors
   - Retry logic with exponential backoff
   - Offline mode detection
3. **Add Progress Indicators**
   - Document processing progress
   - Indexing progress (chunk by chunk)
   - Model loading status
4. **Enhance Chat UI**
   - Markdown rendering for responses
   - Code syntax highlighting
   - Copy-to-clipboard for responses
   - Export conversation history

---

## 📈 Quality Assessment

### Code Quality: **A- (Excellent)**

**Strengths**:

- ✅ Comprehensive Pydantic validation (type safety)
- ✅ Clean separation of concerns (core, rag, analysis, api, cli)
- ✅ Extensive testing infrastructure (70% coverage minimum)
- ✅ Modern Python 3.11+ features (type hints, dataclasses)
- ✅ Production-ready observability (structlog, Prometheus)
- ✅ Strict linting (Ruff) and security scanning (bandit, pip-audit)

**Areas for Improvement**:

- 🟡 Missing docstrings in some modules (inconsistent)
- 🟡 TODO comments in production code (api/app.py)
- 🟡 No auto-generated API documentation (Sphinx/MkDocs)
- 🟡 Some type annotations use `any` (reduce this)

### Architecture: **A (Very Good)**

**Strengths**:

- ✅ Clear layered architecture (client → application → processing → storage)
- ✅ Provider abstraction for LLM flexibility
- ✅ DAG pipeline for complex workflows
- ✅ Reproducible builds (Nix flake)
- ✅ Comprehensive ADR documentation

**Considerations**:

- 🟡 Singleton pattern for vector store (consider dependency injection)
- 🟡 No caching layer implemented (Redis planned)
- 🟡 No distributed processing support (single-node only)

### Testing: **B+ (Good)**

**Strengths**:

- ✅ Multi-level testing (unit, integration, e2e)
- ✅ Fixture-based test data (conftest.py)
- ✅ Async test support (pytest-asyncio)
- ✅ Coverage enforcement (70% minimum)
- ✅ CI/CD integration

**Gaps**:

- 🟡 Frontend tests missing (no Vitest/Playwright setup)
- 🟡 CLI commands untested (stubs not implemented)
- 🟡 Load testing not implemented
- 🟡 No mutation testing

### Documentation: **B+ (Good)**

**Strengths**:

- ✅ Extensive README (634 lines)
- ✅ Architecture diagrams (Mermaid)
- ✅ Quick start guides
- ✅ ADR records
- ✅ Security policy

**Gaps**:

- 🟡 No auto-generated API docs
- 🟡 Inconsistent module docstrings
- 🟡 No video tutorials
- 🟡 Missing deployment guides

---

## 🔗 Frontend-Backend Integration

### Current Status

**Frontend Architecture**:

- **Framework**: Tauri 2.0 (Rust backend) + SvelteKit + Svelte 5
- **API Client**: `cortex-desktop/src/lib/api.ts`
- **State Management**: Svelte 5 runes (`$state`, `$effect`)
- **Styling**: Tailwind CSS (Catppuccin Mocha theme)

**Key Finding**: **Frontend does NOT use mock data** ✅

The frontend is properly designed to call real API endpoints at:

- `http://localhost:8000` (CORTEX API)
- `http://localhost:8081` (RAG API)

**Problem**: Backend endpoints are marked as "TODO" (see Phase 1 priorities).

### Integration Checklist

- Frontend API client properly structured (`api.ts`)
- TypeScript interfaces match expected backend responses
- Health check endpoint working (`/health`)
- Prometheus metrics working (`/metrics`)
- Document processing endpoint (`/process`) - **TODO**
- Vector search endpoint (`/vectors/search`) - **TODO**
- Vector indexing endpoint (`/vectors/index`) - **TODO**
- RAG chat endpoint (`/api/chat`) - **TODO**
- Models list endpoint (`/api/models`) - **TODO**
- System metrics endpoint (`/api/system/metrics`) - **TODO**

---

## 📂 Key Files Reference

### Backend Core

| File                                | Purpose                             | LOC  | Test Coverage |
| ----------------------------------- | ----------------------------------- | ---- | ------------- |
| `src/phantom/core/cortex.py`        | CORTEX processor, semantic chunking | 500+ | High          |
| `src/phantom/core/embeddings.py`    | sentence-transformers integration   | 200+ | Medium        |
| `src/phantom/rag/vectors.py`        | FAISS vector store                  | 300+ | High          |
| `src/phantom/analysis/sentiment.py` | NLTK VADER sentiment                | 250+ | High          |
| `src/phantom/api/app.py`            | FastAPI server                      | 190  | High          |
| `src/phantom/cli/main.py`           | Typer CLI                           | 150+ | Low (stubs)   |
| `src/phantom/providers/llamacpp.py` | llama.cpp provider                  | 200+ | Medium        |

### Frontend Core

| File                                     | Purpose            | LOC   |
| ---------------------------------------- | ------------------ | ----- |
| `cortex-desktop/src/routes/+page.svelte` | Main UI component  | 1,193 |
| `cortex-desktop/src/lib/api.ts`          | API client         | 89    |
| `cortex-desktop/src-tauri/src/main.rs`   | Tauri Rust backend | \~100 |

### Configuration

| File                      | Purpose                    |
| ------------------------- | -------------------------- |
| `flake.nix`               | Nix environment definition |
| `pyproject.toml`          | Python package config      |
| `pytest.ini`              | Test configuration         |
| `.pre-commit-config.yaml` | Pre-commit hooks           |
| `justfile`                | Task runner (50+ commands) |

### Documentation

| File                        | Purpose                                |
| --------------------------- | -------------------------------------- |
| `README.md`                 | Main project documentation (634 lines) |
| `CORTEX_V2_ARCHITECTURE.md` | Architecture deep-dive                 |
| `VRAM_CALCULATOR.md`        | Hardware planning guide                |
| `ROADMAP.md`                | 4-phase development plan               |
| `CONTRIBUTING.md`           | Development workflow                   |

---

## 🧪 Testing Strategy

### Running Tests

```bash
# Enter Nix development environment
nix develop

# Run all tests
just test

# Run with coverage report
just test-cov

# Run specific test levels
just test-unit          # Unit tests only
just test-integration   # Integration tests
just test-e2e          # End-to-end tests

# Run tests by marker
pytest -m "not slow"    # Skip slow tests
pytest -m "integration" # Integration only
```

### Test Structure

```javascript
tests/
├── conftest.py                 # Shared fixtures
├── test_imports.py            # Critical import validation
├── unit/
│   ├── test_cortex.py         # CORTEX processor
│   ├── test_cortex_chunker.py # Semantic chunking
│   ├── test_sentiment.py      # Sentiment analysis
│   ├── test_vector_store.py   # FAISS operations
│   └── test_pipeline.py       # DAG pipeline
├── integration/
│   ├── test_api.py            # FastAPI endpoints
│   └── test_cli.py            # CLI commands
└── e2e/
    └── test_full_pipeline.py  # End-to-end flows
```

### Coverage Requirements

- **Minimum**: 70% (enforced via `pytest.ini`)
- **Target**: 80%+
- **Exclusions**: `*/tests/*`, `*/__pycache__/*`

### Adding New Tests

1. **Unit Tests**: Test isolated functions/classes
2. **Integration Tests**: Test API endpoints
3. **E2E Tests**: Test full workflows

---

## ⚙️ Common Tasks

### Starting the Development Environment

```bash
# Enter Nix shell with all dependencies
nix develop

# Or use direnv (auto-load on cd)
echo "use flake" > .envrc
direnv allow
```

### Running the API Server

```bash
# Development server (auto-reload)
just run-api

# Or manually with uvicorn
python -m uvicorn phantom.api.app:app --reload --host 127.0.0.1 --port 8000
```

### Running the Desktop App

```bash
cd cortex-desktop
npm install        # First time only
npm run tauri dev  # Start Tauri dev server
```

### Code Quality Checks

```bash
# Lint Python code
just lint

# Format Python code
just format

# Type check
just typecheck

# Security scan
just security-scan

# All checks at once
just quality
```

### Database/Vector Store Management

```bash
# Initialize FAISS index (if needed)
python -c "from phantom.rag.vectors import FAISSVectorStore; store = FAISSVectorStore(); store.save('data/index.faiss')"

# Check index stats
python -c "from phantom.rag.vectors import FAISSVectorStore; store = FAISSVectorStore.load('data/index.faiss'); print(f'Vectors: {store.ntotal}')"
```

### Git Workflow

```bash
# Pre-commit hooks installed automatically in Nix shell
git add .
git commit -m "feat: implement /process endpoint"  # Hooks run automatically

# Manual hook run
pre-commit run --all-files
```

---

## 🚨 Known Issues & TODOs

### Critical (Fix Immediately)

1. **Missing API Endpoints** (`src/phantom/api/app.py`)
   - `/process` - Document processing
   - `/vectors/search` - Vector search
   - `/vectors/index` - Document indexing
   - `/api/chat` - RAG chat
   - `/api/models` - Model listing
   - `/api/prompt/test` - Prompt testing
2. **CLI Not Functional** (`src/phantom/cli/main.py`)
   - `phantom extract` - Stub only
   - `phantom analyze` - Stub only
   - `phantom classify` - Stub only
   - `phantom scan` - Stub only

### High Priority

1. **No Frontend Tests**
   - Set up Vitest for unit tests
   - Set up Playwright for e2e tests
   - Test API client (`api.ts`)
2. **Documentation Gaps**
   - Auto-generate API docs (Sphinx/MkDocs)
   - Add module docstrings to all files
   - Create deployment guide

### Medium Priority

1. **Error Handling**
   - Add proper exception hierarchy
   - Improve API error responses (consistent format)
   - Add retry logic for transient failures
2. **Observability**
   - Add distributed tracing (OpenTelemetry)
   - Add request ID propagation
   - Add structured error logging

### Low Priority

1. **Cloud Providers**
   - OpenAI integration
   - Anthropic integration
   - DeepSeek integration
2. **Advanced Features**
   - Redis semantic cache
   - Kubernetes/Helm charts
   - Multi-node distributed processing

---

## 🎓 Development Philosophy

### Key Principles

1. **Local-First**: No cloud dependencies for core functionality
2. **Type Safety**: Pydantic everywhere, strong typing
3. **Reproducibility**: Nix flake, locked dependencies
4. **Production-Ready**: Metrics, logging, health checks from day one
5. **Test-Driven**: 70% minimum coverage, multi-level testing
6. **Clean Architecture**: Layered, modular, dependency injection

### Code Style

- **Python**: Follow Ruff rules (pycodestyle, pyflakes, isort, flake8-bugbear)
- **TypeScript**: Follow Prettier + ESLint
- **Rust**: Follow rustfmt + clippy
- **Commits**: Conventional Commits format (`feat:`, `fix:`, `docs:`)
- **Line Length**: 100 characters (Python), 120 (TypeScript)

### Adding New Features

1. **Write Tests First** (TDD when possible)
2. **Implement Minimal Viable Feature**
3. **Add Type Annotations & Pydantic Models**
4. **Add Docstrings (Google style)**
5. **Run Quality Checks** (`just quality`)
6. **Update Documentation** (README, CLAUDE.md)
7. **Commit with Conventional Commits**

---

## 📚 Additional Resources

### Documentation Files

- `README.md` - Main project documentation
- `CORTEX_V2_ARCHITECTURE.md` - Architecture deep-dive
- `CORTEX_V2_QUICKSTART.md` - Getting started guide
- `VRAM_CALCULATOR.md` - Hardware planning
- `NIX_PYTHON_GUIDELINES.md` - Nix + Python best practices
- `ROADMAP.md` - Development phases
- `CONTRIBUTING.md` - Contribution guidelines
- `SECURITY.md` - Security policy

### External Links

- **Repository**: <https://github.com/kernelcore/phantom>
- **CI/CD**: <https://github.com/kernelcore/phantom/actions>
- **NixOS Packages**: <https://search.nixos.org/packages>
- **FastAPI Docs**: <https://fastapi.tiangolo.com/>
- **SvelteKit Docs**: <https://kit.svelte.dev/>

---

## 🚀 Quick Start Checklist

### For New Developers

- Clone repository
- Install Nix (if not installed): `curl -L https://nixos.org/nix/install | sh`
- Enter dev environment: `nix develop`
- Run tests: `just test`
- Start API server: `just run-api`
- Read `CONTRIBUTING.md`
- Check current issues: Phase 1 priorities above

### For Claude

- Read this file fully
- Check Phase 1 priorities (Backend API endpoints)
- Verify test coverage before implementing features
- Follow code style (Ruff, type hints, docstrings)
- Update this file when adding new features
- Run `just quality` before committing

---

**Last Updated**: 2026-02-05
**Maintainer**: kernelcore <kernelcore@voidnix.dev>
**Version**: 2.0.0 (Beta)

---

*This document is auto-updated. For questions, check CONTRIBUTING.md or open an issue.*
