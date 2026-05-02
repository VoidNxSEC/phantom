# PHANTOM - Development Guide for Claude

> **Living Machine Learning Framework** - Production-grade document intelligence, RAG pipeline, and AI classification system.

**Version**: 0.0.1 (Pre-Alpha)
**Python**: 3.11+
**License**: Apache-2.0
**Last Updated**: 2026-03-26

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
| OpenAI Provider     | ✅ Complete | `providers/openai_provider.py` | Low     |
| Anthropic Provider  | ✅ Complete | `providers/anthropic_provider.py` | Low   |
| DeepSeek Provider   | ✅ Complete | `providers/deepseek_provider.py` | Low    |
| Provider Registry   | ✅ Complete | `providers/registry.py` | Low          |
| FastAPI Server      | ✅ Complete | `api/app.py`            | High          |
| Prometheus Metrics  | ✅ Complete | `api/app.py`            | High          |
| Pydantic Schemas    | ✅ Complete | All modules             | High          |
| CI/CD Pipelines     | ✅ Complete | `.github/workflows/`    | N/A           |
| Nix Environment     | ✅ Complete | `flake.nix`             | N/A           |
| CLI Commands        | ✅ Complete | `cli/main.py`           | Medium        |
| RAG Query API       | ✅ Complete | `api/app.py`            | High          |
| Document Upload     | ✅ Complete | `api/app.py`            | High          |
| Vector Indexing API | ✅ Complete | `api/app.py`            | High          |
| SSE Streaming Chat  | ✅ Complete | `api/app.py`            | Medium        |

### 🟡 Partially Implemented Components

| Component           | Status         | Missing                          | Priority |
| ------------------- | -------------- | -------------------------------- | -------- |
| Desktop UI          | 🟡 Framework   | Component polish, e2e tests      | Medium   |
| tools vram          | 🟡 Partial     | Model-specific VRAM estimates    | Low      |

### ❌ Not Implemented

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
│   ├── neotron/             # Compliance guardrails (SENTINEL)
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

| Endpoint            | Method | Status       | Returns                       |
| ------------------- | ------ | ------------ | ----------------------------- |
| `/health`           | GET    | ✅ Complete  | Health status                 |
| `/ready`            | GET    | ✅ Complete  | Readiness checks              |
| `/metrics`          | GET    | ✅ Complete  | Prometheus metrics            |
| `/api/system/metrics`| GET   | ✅ Complete  | System resource metrics       |
| `/extract`          | POST   | ✅ Complete  | Document insights             |
| `/process`          | POST   | ✅ Complete  | CORTEX document processing    |
| `/upload`           | POST   | ✅ Complete  | Single file upload            |
| `/api/upload`       | POST   | ✅ Complete  | Multi-file upload             |
| `/vectors/search`   | POST   | ✅ Complete  | Vector search (dense/sparse/hybrid) |
| `/vectors/index`    | POST   | ✅ Complete  | Vector indexing               |
| `/vectors/batch-index`| POST | ✅ Complete  | Batch indexing                |
| `/api/chat`         | POST   | ✅ Complete  | RAG chat interface            |
| `/api/chat/stream`  | POST   | ✅ Complete  | SSE streaming chat            |
| `/api/models`       | GET    | ✅ Complete  | List available models         |
| `/api/prompt/test`  | POST   | ✅ Complete  | Test prompt rendering         |
| `/api/pipeline`     | POST   | ✅ Complete  | DAG pipeline execution        |
| `/api/pipeline/scan`| POST   | ✅ Complete  | File classification scan      |
| `/rag/query`        | GET    | ✅ Complete  | Legacy RAG query              |
| `/judge`            | POST   | ✅ Complete  | AI-OS-Agent judgment          |

---

## 🎯 Development Priorities

### Phase 1: Backend API ✅ **COMPLETED**

**Goal**: Implement all API endpoints for frontend-backend integration.

**Status**: All endpoints fully implemented with production-quality code.

**Implementation highlights**:
- `/process` — CORTEX engine document processing with temporary file handling
- `/vectors/search` — Semantic search with dense, sparse, and hybrid modes (FAISS + BM25)
- `/vectors/index` — Document chunking, embedding generation, and FAISS indexing
- `/vectors/batch-index` — Batch index multiple text documents in one call
- `/api/chat` — RAG-powered chat with vector context retrieval and LLM generation
- `/api/chat/stream` — SSE streaming chat for real-time token delivery
- `/api/models` — Dynamic model listing via provider registry (local, OpenAI, Anthropic, DeepSeek)
- `/api/prompt/test` — Prompt template rendering with variable substitution and token estimation
- `/api/upload` — Multi-file upload with CORTEX processing pipeline
- `/api/system/metrics` — Real-time CPU, memory, disk, and VRAM monitoring

**Provider architecture**:
- `providers/base.py` — Abstract `AIProvider` base class with `generate()`, `agenerate()`, `stream()`
- `providers/registry.py` — Provider factory with `get_provider()`, `get_available_providers()`, `clear_provider_cache()`
- `providers/llamacpp.py` — Local llama.cpp server (TURBO)
- `providers/openai_provider.py` — OpenAI GPT-4o, GPT-4, GPT-3.5 (cloud, via OPENAI_API_KEY env var)
- `providers/anthropic_provider.py` — Anthropic Claude 3.5/3/2 (cloud, via ANTHROPIC_API_KEY env var)
- `providers/deepseek_provider.py` — DeepSeek Chat & Reasoner (cloud, via DEEPSEEK_API_KEY env var)

---

### Phase 2: System Monitoring Integration ✅ **COMPLETED**

**Goal**: Expose real host machine metrics to frontend (CPU, memory, VRAM, temperature).

**Status**: `/api/system/metrics` endpoint implemented at `src/phantom/api/app.py:232`.

**Returns**:
- CPU: percent, count, frequency
- Memory: total, used, available, percent (bytes and GB)
- Disk: total, used, free, percent (bytes and GB)
- Network: bytes sent/recv, packets sent/recv
- VRAM: GPU memory via nvidia-smi (if available)
- Timestamp

**Frontend Integration**: Add system monitor component to Cortex Desktop (future work).

---

### Phase 3: Desktop UI Enhancement (LOW PRIORITY) 🟢

**Goal**: Complete the Cortex Desktop UI with functional components.

**Framework**: Tauri 2 + SvelteKit + Svelte 5
**Status**: All 6 tabs implemented and connected to live backend endpoints.
**File**: `cortex-desktop/src/routes/+page.svelte`

**Implemented Tabs**:

- ✅ Chat (RAG conversation with sources display)
- ✅ Process (CORTEX document processing with configurable chunking)
- ✅ Search (vector semantic search with score display)
- ✅ Workbench (prompt engineering with variable testing and LLM execution)
- ✅ Library (saved prompt templates)
- ✅ Settings (provider selection, model selection, temperature, token config)

**Provider options in Settings**:
- `tensor_forge` → Local Tensor Engine (LlamaCpp)
- `openai` → OpenAI Managed (GPT-4o, GPT-4, GPT-3.5)
- `anthropic` → Anthropic API (Claude 3.5 Sonnet, Claude 3, Claude 2)
- `deepseek` → DeepSeek API (Chat V3, Reasoner R1)

**Remaining Enhancement Tasks**:

1. **Add System Monitor Tab**
   - Real-time CPU/memory/VRAM charts
   - Resource alerts
2. **Improve Error Handling**
   - Toast notifications for API errors
   - Retry logic with exponential backoff
3. **Add Progress Indicators**
   - Document processing progress
   - Indexing progress (chunk by chunk)
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

### 🔴 Port Mismatch (Fixed)

The default port in `serve()` was changed from **8008** to **8087** to match the Vite proxy configuration (`vite.config.js` → `http://localhost:8087`).

| Command | Port |
|---|---|
| `just cortex` / `phantom-api` | **8087** (default) |
| `just serve` | 8008 (explicit `--port`) |
| `just desktop` (Vite proxy) | 1420 → proxies to :8087 |

### High Priority

1. **No Frontend Tests**
   - Set up Vitest for unit tests
   - Set up Playwright for e2e tests
   - Test API client (`api.ts`)
2. **Cloud Provider Tests**
   - Unit tests for OpenAI, Anthropic, DeepSeek providers
   - Mock HTTP responses for cloud API calls
3. **Documentation Gaps**
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
