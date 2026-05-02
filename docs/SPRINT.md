# SPRINT — Unlock Phantom's Potential

> **Goal**: Transform Phantom from a powerful-but-hidden framework into a
> discoverable, demonstrable, and delightful developer experience.
>
> **Status**: 🟡 Planning
> **Duration**: 2–3 weeks (part-time)
> **Owner**: kernelcore
> **Last Updated**: 2026-05-01

---

## 📋 Table of Contents

- [Why This Sprint](#why-this-sprint)
- [Sprint Themes](#sprint-themes)
- [Epics](#epics)
  - [Epic 1: `phantom demo` — One-Command Showcase](#epic-1-phantom-demo--one-command-showcase)
  - [Epic 2: `phantom doctor` — Diagnostic Toolkit](#epic-2-phantom-doctor--diagnostic-toolkit)
  - [Epic 3: CLI Discovery & DX](#epic-3-cli-discovery--dx)
  - [Epic 4: Unify the Server Story](#epic-4-unify-the-server-story)
  - [Epic 5: Playground Web UI](#epic-5-playground-web-ui)
- [Appendix: Architecture](#appendix-architecture)
- [Appendix: Success Metrics](#appendix-success-metrics)

---

## Why This Sprint

Phantom ships a **production-grade stack** — CORTEX, RAG, provider registry,
streaming chat, DAG pipeline, system metrics, FAISS vector search — but most
of it is invisible unless you read the source code.

| Problem | Symptom | Fix |
|---|---|---|
| Two APIs, one known | `phantom-api` only runs `cortex_api.py`; `app.py` is invisible | `just up` + unified entry point |
| No demo pipeline | New users can't see the full flow in <30s | `phantom demo` |
| No health diagnostics | Provider failures are silent until runtime | `phantom doctor` |
| CLI is dense but hidden | No autocomplete, no example-driven help | Shell completions + richer `--help` |
| No playground | Every endpoint test requires `curl` | Web Playground tab |

This sprint closes the gap between **what Phantom can do** and **what people
know it can do**.

---

## Sprint Themes

```
┌──────────────────────────────────────────────────────────┐
│                    SPRINT THEMES                          │
│                                                          │
│   🎬 DEMO     🩺 DOCTOR    ⌨️  DX    🔌 UNIFY    🎨 UI   │
│                                                          │
│   phantom     phantom      autocom-  just up     web     │
│   demo        doctor       plete +   one cmd    play-   │
│   (30s        (provider    help      both       ground  │
│   pipeline)   diag)        flags     servers    (api)   │
└──────────────────────────────────────────────────────────┘
```

---

## Epics

### Epic 1: `phantom demo` — One-Command Showcase

**Story**: A developer runs `phantom demo` and immediately sees:
1. A document being chunked semantically (no LLM needed)
2. Its chunks embedded via sentence-transformers
3. A FAISS index built from those embeddings
4. A semantic search returning relevant results
5. (Optional) A RAG chat answer if a local or cloud LLM is configured

**Status**: ✅ **COMPLETED**

**Tasks**:

| # | Task | Effort | Status |
|---|---|---|---|
| 1.1 | Create `demo_input/` directory with 3 sample documents (financial report, technical blog, quantum research) | 30 min | ✅ |
| 1.2 | Implement `cli/demo.py` with a `demo` Typer command: chunk → embed → index → search → (optional) chat | 3 h | ✅ |
| 1.3 | Rich progress panels, color-coded search results, summary on completion | 1 h | ✅ |
| 1.4 | Add `just demo` recipe in `justfile` | 5 min | ✅ |
| 1.5 | Add `demo_input/` samples to `pyproject.toml` package data | 10 min | 🟡 Open |

**Acceptance Criteria**:
- `phantom demo --doc financial --no-rag` runs entirely offline with no dependencies ✅
- `phantom demo --doc tech` works with the technical blog document ✅
- Rich output with panels, tables, and color-coded scores ✅
- `--no-rag` flag skips LLM step gracefully ✅
- Falls back gracefully when no LLM provider is available ✅
- RAG chat step uses provider registry (local → openai → anthropic → deepseek) ✅

---

### Epic 2: `phantom doctor` — Diagnostic Toolkit

**Story**: A developer runs `phantom doctor` and instantly sees the health of
every component — providers, vector store, NATS, GPU, system resources.

**Status**: ✅ **COMPLETED**

**Tasks**:

| # | Task | Effort | Status |
|---|---|---|---|
| 2.1 | Implement `cli/doctor.py` with `doctor` Typer command | 2 h | ✅ |
| 2.2 | Provider diagnostics: ping local llama.cpp, check API keys, test connectivity with tiny prompt | 2 h | ✅ |
| 2.3 | Vector store check: FAISS lib, index files on disk, vector count & dimension | 1 h | ✅ |
| 2.4 | System check: Python version, platform, RAM, CPU load, disk, GPU/VRAM (nvidia-smi), NATS | 1.5 h | ✅ |
| 2.5 | Rich color-coded table output with ✅ / ⚠️ / ❌ / ⬜ per component, severity-based exit codes | 1 h | ✅ |
| 2.6 | Add `just doctor` alias + `--providers-only` flag | 5 min | ✅ |

**Acceptance Criteria**:
- `phantom doctor` shows a comprehensive table with all components ✅
- System resources: Python, RAM, CPU, disk, GPU (via nvidia-smi) ✅
- Core libraries: imports, FAISS version, embedding model loaded ✅
- Vector store: FAISS index existence, dimension, vector count ✅
- Servers: pings Phantom API (:8000) and Cortex API (:8087) health endpoints ✅
- Providers: local llama.cpp ping, cloud API key presence, connectivity test ✅
- Falls back gracefully when components are missing (e.g., no GPU, no NATS) ✅
- Exits with code 0 (healthy), 1 (degraded), or 2 (critical failure) ✅
- `--providers-only` flag for quick provider diagnostics ✅

---

### Epic 3: CLI Discovery & DX

**Story**: A developer types `phantom` and sees a well-organized help page with
examples. Tab-completion works in bash/zsh/fish.

**Tasks**:

| # | Task | Effort | Depends On |
|---|---|---|---|
| 3.1 | Audit all CLI commands for missing `--help` descriptions and example usage | 1 h | — |
| 3.2 | Add rich `epilog` / `examples` to each Typer command with real-world usage | 2 h | 3.1 |
| 3.3 | Register shell completion: `phantom --install-completion` for bash/zsh/fish | 1 h | — |
| 3.4 | Add `just completions` to generate and persist completions | 30 min | 3.3 |
| 3.5 | Create a `just cheat` command that prints a one-page quick reference | 30 min | — |

**Acceptance Criteria**:
- `phantom --help` shows organized groups with descriptions
- Each subcommand has at least one example in its help text
- `phantom --install-completion` works for zsh/bash/fish
- `just cheat` prints a dense, readable one-page reference

---

### Epic 4: Unify the Server Story

**Story**: A developer runs `just up` and both servers start. The `justfile`
clearly explains what runs where and why.

**Tasks**:

| # | Task | Effort | Depends On |
|---|---|---|---|
| 4.1 | ✅ **DONE** — Add `just api` recipe for `app.py` on port 8000 | — | — |
| 4.2 | ✅ **DONE** — Add `just up` recipe that starts both servers | — | — |
| 4.3 | Register `phantom-api-core` as a second Nix package for `app.py` | 1 h | — |
| 4.4 | Update `CLAUDE.md` to document the two-server architecture clearly | 30 min | 4.3 |
| 4.5 | Add `just ps` to check which servers are running | 15 min | — |

**Acceptance Criteria**:
- `just up` starts both servers with a single command
- Each server's purpose is documented in `just --list` description
- `just ps` shows PID, port, and uptime for each server

---

### Epic 5: Playground Web UI

**Story**: A developer opens `http://localhost:8000/playground` and sees a
minimal HTML page where they can test every API endpoint without curl.

**Tasks**:

| # | Task | Effort | Depends On |
|---|---|---|---|
| 5.1 | Serve a simple HTML playground from a FastAPI route in `app.py` | 2 h | — |
| 5.2 | Add sections: Process, Search, Chat, Models, Metrics, Doctor | 2 h | 5.1 |
| 5.3 | Each section has a form → calls the local API → shows the JSON response | 1.5 h | 5.2 |
| 5.4 | Style with minimal CSS (dark theme, monospace output) | 1 h | 5.3 |
| 5.5 | Add `just playground` to open `http://localhost:8000/playground` in browser | 5 min | 5.1 |

**Acceptance Criteria**:
- All major API endpoints are accessible from the playground
- Forms have sensible defaults so one click produces results
- Responses are displayed as formatted JSON
- Works in a browser without JavaScript errors

---

## Appendix: Architecture

### How the servers fit together

```
┌────────────────────────────────────────────────────────────┐
│                    Developer Machine                        │
│                                                            │
│  ┌─────────────────┐    ┌──────────────────────────────┐   │
│  │  Cortex API      │    │  Phantom API (★ this sprint) │   │
│  │  :8087           │    │  :8000                      │   │
│  │                  │    │                              │   │
│  │  • /health       │    │  • /health                  │   │
│  │  • /process      │    │  • /api/chat + stream       │   │
│  │  • /analyze      │    │  • /api/models (registry)   │   │
│  │  • /judge        │    │  • /vectors/search/index    │   │
│  │  • /api/chat     │    │  • /api/pipeline            │   │
│  │  • /api/models   │    │  • /api/system/metrics      │   │
│  │                  │    │  • /api/prompt/test         │   │
│  │  ← legacy/       │    │  • /playground (NEW)        │   │
│  │    desktop GUI   │    │                              │   │
│  └─────────────────┘    │  ← serves: CLI, API clients  │   │
│                          │    agents, MCP tools         │   │
│                          └──────────────────────────────┘   │
│                                                            │
│  CLI: phantom demo | doctor | extract | classify | search  │
└────────────────────────────────────────────────────────────┘
```

### Data flow for `phantom demo`

```
phantom demo
  │
  ├─ 1. Process sample doc ──→ CORTEX → insights + chunks
  ├─ 2. Index chunks ────────→ embeddings → FAISS
  ├─ 3. Search by query ─────→ FAISS → top-k results
  └─ 4. RAG chat ────────────→ context + LLM → answer
```

---

## Appendix: Success Metrics

| Metric | Current | Target | How to Measure |
|---|---|---|---|
| Time to "wow" (new dev) | ~20 min reading code | **<60 s** (`phantom demo`) | Stopwatch |
| CLI help usefulness | Minimal | **Every command has examples** | `phantom --help` audit |
| Server discoverability | One hidden server | **Two documented, one-command start** | `just --list` |
| Provider diagnostics | Silent failures | **`phantom doctor` shows all** | Run command |
| API testability | curl-only | **Playground at :8000/playground** | Open browser |
| Shell completions | None | **zsh/bash/fish supported** | `phantom --install-completion` |

---

*This sprint feeds into the broader Phantom roadmap. See `ROADMAP.md` for the
long-term vision.*