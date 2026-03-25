# Phantom Roadmap

## Shipped

- [x] Project reorganization (`src/phantom/` package structure)
- [x] Import refactoring to new package layout
- [x] CI/CD pipeline (lint, test, security scan, CodeQL, SBOM)
- [x] Pre-commit hooks (ruff, mypy, bandit)
- [x] CORTEX v2.0: semantic chunking, embeddings, parallel classification
- [x] FAISS vector store with hybrid search (BM25 + cosine, RRF)
- [x] FastAPI REST API with Prometheus metrics
- [x] Sentiment analysis and entity extraction (SPECTRE)
- [x] System resource monitoring endpoint
- [x] pip-installable Python package
- [x] Nix flake development environment
- [x] Test coverage at 70%+ minimum (enforced in CI)

## In Progress

- [ ] CLI command implementations (extract, analyze, classify, scan — currently stubs)
- [ ] Cortex Desktop UI components (Tauri + SvelteKit framework in place)

## Planned — Near Term

- [ ] Standalone binaries for Linux and macOS
- [ ] Windows validation
- [ ] Docker / OCI image
- [ ] Cloud LLM providers (OpenAI, Anthropic)
- [ ] NixOS module for system-level deployment

## Planned — Long Term

- [ ] IntelAgent orchestrator and Phantom integration
- [ ] Redis-based semantic cache
- [ ] Distributed / multi-node processing
- [ ] IntelAgent MCP server implementation
- [ ] Desktop app: real-time system metrics, processing progress, error handling UI

---

*Last updated: 2026-03-25*
