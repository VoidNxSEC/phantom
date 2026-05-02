# Phantom Roadmap

## Shipped

- [x] Project reorganization (`src/phantom/` package structure)
- [x] Import refactoring to new package layout
- [x] CI/CD pipeline (lint, test, security scan, CodeQL, SBOM)
- [x] Pre-commit hooks (ruff, mypy, bandit)
- [x] CORTEX v2.0: semantic chunking, embeddings, parallel classification
- [x] FAISS vector store with hybrid search (BM25 + cosine, RRF)
- [x] FastAPI REST API with Prometheus metrics (22 endpoints)
- [x] Sentiment analysis and entity extraction (SPECTRE)
- [x] System resource monitoring endpoint
- [x] pip-installable Python package
- [x] Nix flake development environment
- [x] Test coverage at 70%+ minimum (enforced in CI)
- [x] CLI fully functional (extract, analyze, classify, scan, rag, tools)
- [x] DAG pipeline exposed via REST (`/api/pipeline`, `/api/pipeline/scan`)
- [x] SSE streaming chat (`/api/chat/stream`) with LlamaCpp streaming
- [x] RAG ingestion and query via CLI (`phantom rag ingest`, `phantom rag query`)
- [x] Cortex Desktop: Tauri 2.0 + SvelteKit 5 + Svelte 5 runes
- [x] Cortex Desktop: 6 tab components (Chat, Process, Search, Workbench, Library, Settings)
- [x] Cortex Desktop: centralized state management (`state.svelte.ts`, 320 LOC)
- [x] Cortex Desktop: typed API client with Vite proxy to backend
- [x] Cortex Desktop: Catppuccin Mocha theme, responsive layout
- [x] Cortex Desktop: streaming chat integration
- [x] IntelAgent core abstractions (Agent, Task, Context, Proof, QualityGate traits)
- [x] IntelAgent SOC kernel (scheduler, task queue, agent pool, event bus, metrics, UI)

## In Progress

- [ ] Frontend sub-components (MessageBubble, FileUploader, ErrorToast, ResultCard)
- [ ] Frontend test infrastructure — Vitest + Playwright (ADR-0018 P2)

## Planned — Near Term

- [ ] System metrics dashboard tab (wire to `/api/system/metrics`)
- [ ] Markdown rendering + code syntax highlighting in chat
- [ ] IntelAgent: implement remaining crates (security, governance, memory, quality, mcp, cli)
- [ ] In-memory/Redis cache layer for embeddings and queries (ADR-0018 P4)
- [ ] Standalone binaries for Linux and macOS
- [ ] Docker / OCI image

## Planned — Long Term

- [ ] Cloud LLM providers (OpenAI, Anthropic, DeepSeek)
- [ ] Windows validation
- [ ] NixOS module for system-level deployment
- [ ] IntelAgent advanced features (ZK proofs, DAO governance, MCP server)
- [ ] Distributed / multi-node processing

---

> **Note**: `phantom-ray/phantom-stack/libs/intelagent/` is a stale copy of the IntelAgent
> workspace from ~2026-01-14. The canonical version lives in `phantom/intelagent/` —
> phantom-ray's copy has compile errors (`Vec<QualityGate>` instead of `Vec<Box<dyn QualityGate>>`)
> and missing Clone support. Do not use phantom-ray's version.

---

*Last updated: 2026-03-25*
