```html
<div align="center">
```

```javascript
██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
```

**Local-first document intelligence engine. Private, sovereign, and platform-agnostic.**

[!\[Nix Build\](https://github.com/VoidNxSEC/phantom/actions/workflows/nix-build.yml/badge.svg)](https://github.com/VoidNxSEC/phantom/actions/workflows/nix-build.yml)
[!\[Nix Check\](https://github.com/VoidNxSEC/phantom/actions/workflows/nix-check.yml/badge.svg)](https://github.com/VoidNxSEC/phantom/actions/workflows/nix-check.yml)
[!\[Secret Scan\](https://github.com/VoidNxSEC/phantom/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/VoidNxSEC/phantom/actions/workflows/secret-scan.yml)
[!\[License\](https://img.shields.io/badge/license-Apache\_2.0-blue.svg)](LICENSE)
[!\[Python\](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[!\[Nix\](https://img.shields.io/badge/built\_with-nix-5277C3?logo=nixos)](https://nixos.org)
[!\[Version\](https://img.shields.io/badge/version-0.1.0-orange)](https://github.com/VoidNxSEC/phantom/releases/latest)

```html
</div>
```

---

Phantom is a **voidnxlabs-grade document intelligence engine** that classifies, sanitizes, and understands unstructured data — locally, privately, and fast.

It is architected as an infrastructure-agnostic system. While it leverages Nix for hermetic development environments, it is fully compatible with any OCI-compliant container runtime or standard Python 3.11+ environment. It interfaces with local LLMs via `llama.cpp` and indexes data into FAISS through a high-performance RAG pipeline.

**Core Mission**: Transform raw documents into structured intelligence — themes, patterns, PII reports, and vector search — without data ever leaving your controlled environment.

---

## What's Inside

```javascript
phantom/
├── src/phantom/           — Core Python logic (CORTEX, RAG, DAG, API)
├── cortex-desktop/        — Desktop GUI (Tauri 2 + SvelteKit)
├── spectre/               — Sentiment & Pattern Extraction component
├── docs/                  — Structured documentation (Architecture, API, Guides)
├── nix/                   — Hermetic environment & package definitions
└── tests/                 — Comprehensive Python & Integration test suite
```

---

## Roadmap

- **Cloud LLM Providers** — Native support for OpenAI, Anthropic, and DeepSeek.
- **Redis Semantic Cache** — Low-latency response caching for recurring queries.
- **Kubernetes Helm Charts** — For scalable, self-hosted enterprise deployments.

# Contributing

Fork the repo to your own account, make changes, and open a pr.
Follow voidnxlabs on [social media](https://voidnxlabs.com/links) for updates.

# Support
For enterprise support, open a [support ticket](https://voidnxlabs.com/support).

---

## Quickstart

Phantom is optimized for [Nix](https://nixos.org/download), but supports any OCI-compliant or Python 3.11+ environment.

```bash
git clone https://github.com/VoidNxSEC/phantom
cd phantom

# Drop into the fully-pinned dev environment
nix develop

# Run the test suite to confirm everything works
just test

# Start the API server
just serve

# Or run the full desktop app
just desktop
```

By leveraging Nix, the development environment is hermetic and reproducible. However, Phantom remains fully deployable via standard Python tools or Docker for production environments.

---

## Core Capabilities

### CORTEX Engine

The heart of Phantom. Processes raw documents into structured insights through a multi-stage pipeline:

```javascript
Document → SemanticChunker → EmbeddingGenerator → LLM Classifier → Pydantic Schema
```

- Chunking with configurable token budgets (default: 1024 tokens, 128 overlap)
- Parallel LLM calls with retry logic (3 attempts, 2s backoff)
- Real-time VRAM monitoring with auto-throttle — won't OOM your GPU
- Extracts: `Theme`, `Pattern`, `Learning`, `Concept`, `Recommendation`

```bash
# Process a document directory
just run extract --input ./docs --output ./insights.json

# Or hit the API directly
curl -X POST http://localhost:8008/process \
  -F "file=@report.pdf" \
  -F "chunk_strategy=recursive" \
  -F "chunk_size=1024"
```

### Hybrid Vector Search

Most RAG systems pick either semantic or keyword search. Phantom does both and fuses the results using [Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf):

```javascript
Query → FAISS (dense cosine) ─┐
                               ├→ RRF Fusion → Ranked Results
Query → BM25Okapi (sparse) ───┘
```

- FAISS `IndexFlatIP` with L2-normalized cosine similarity
- Optional GPU acceleration via `StandardGpuResources`
- BM25 index rebuilt lazily on each `add()` — no manual sync required

```bash
curl -X POST http://localhost:8008/vectors/search \
  -H "Content-Type: application/json" \
  -d '{"query": "compliance requirements", "top_k": 5, "mode": "hybrid"}'
```

### RAG Chat with Streaming

Context-aware chat over your document base. Supports SSE streaming for real-time token delivery.

```bash
# Streaming chat
curl -X POST http://localhost:8008/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key risks in the Q3 report?",
    "conversation_id": "session-001",
    "history": [],
    "context_size": 5
  }'
```

Phantom utilizes a strictly decoupled **Provider Abstraction Layer**. While local inference via `llama.cpp` is the primary target for maximum data sovereignty, the engine is architected as a cloud-native agnostic infrastructure. The provider registry ensures seamless interoperability with any OpenAI-compatible API, allowing deployment across diverse environments without architectural lock-in.

### Data Sanitization Pipeline

Phantom's DAG pipeline processes files through a classification and sanitization chain before they ever touch your vector store:

```javascript
Discovery → Fingerprint → Classify → Pseudonymize → Sanitize → Verify → Persist
```

Four sanitization levels:

| Level            | What happens                                                         |
| ---------------- | -------------------------------------------------------------------- |
| `none`           | Direct copy, no modifications                                        |
| `strip_metadata` | EXIF, document properties, author fields removed                     |
| `redact_pii`     | Email, phone, SSN, CPF/CNPJ, credit cards replaced with `[REDACTED]` |
| `full_sanitize`  | Everything above + content normalization                             |

PII detection covers: email addresses, phone numbers, SSN, CPF/CNPJ, payment card numbers, AWS credentials, API keys, Bearer tokens, private keys, PGP blocks, IPv4/IPv6 ranges, UUIDs.

```bash
# Scan a directory for sensitive content
phantom-scan ./repo | jq '.findings[] | select(.risk_score > 0.7)'

# Sanitize before exporting
phantom-dag -i ./internal_dataset -o ./export --sanitize pii

# Dry-run to preview what would happen
phantom -i ./input -o ./output --dry-run
```

### Cryptographic Integrity

Every file processed gets a hash. You choose the algorithm:

| Algorithm | Use case                                |
| --------- | --------------------------------------- |
| SHA256    | Baseline integrity, broad compatibility |
| BLAKE3    | High-throughput, modern standard        |
| xxHash    | Maximum speed, block-level streaming    |

```bash
# Generate a manifest
phantom-hash ./directory > manifest.json

# Verify a file against a known hash
phantom-verify report.pdf abc123def456...

# Diff two manifests (transfer verification)
diff <(jq -S . before.json) <(jq -S . after.json)
```

---

## API Reference

The FastAPI server runs at `http://localhost:8008` by default. Prometheus metrics at `/metrics`, OpenAPI docs at `/docs`.

| Endpoint               | Method | Purpose                              |
| ---------------------- | ------ | ------------------------------------ |
| `/health`              | GET    | Liveness probe                       |
| `/ready`               | GET    | Readiness check with downstream deps |
| `/metrics`             | GET    | Prometheus metrics                   |
| `/api/system/metrics`  | GET    | CPU, RAM, VRAM, disk                 |
| `/process`             | POST   | Process document with CORTEX         |
| `/extract`             | POST   | Extract insights from text           |
| `/upload`              | POST   | Single file upload                   |
| `/api/upload`          | POST   | Multi-file upload with processing    |
| `/vectors/search`      | POST   | Hybrid vector search                 |
| `/vectors/index`       | POST   | Index document to FAISS              |
| `/vectors/batch-index` | POST   | Batch indexing                       |
| `/api/chat`            | POST   | RAG-powered chat                     |
| `/api/chat/stream`     | POST   | SSE streaming chat                   |
| `/api/models`          | GET    | List available LLM models            |
| `/api/prompt/test`     | POST   | Render and token-count a prompt      |
| `/api/pipeline`        | POST   | Full DAG pipeline execution          |
| `/api/pipeline/scan`   | POST   | Scan-only (read-only, no writes)     |
| `/judge`               | POST   | AI-Agent-OS judgment integration     |

All request/response bodies are validated by Pydantic v2. No silent failures.

---

## Output Structure

```javascript
output/
├── documents/          # PDF, DOCX, TXT, MD
├── images/             # PNG, JPG, SVG
├── audio/              # MP3, FLAC, WAV
├── video/              # MP4, MKV, AVI
├── code/               # PY, JS, RS, GO, NIX
├── data/               # JSON, CSV, PARQUET
├── archives/           # ZIP, TAR, 7Z
├── configs/            # ENV, CONF, INI
├── logs/               # LOG, OUT, ERR
├── crypto/             # PEM, KEY, P12
├── executables/        # ELF, EXE, DEB
├── unknown/            # Unclassified
└── .phantom/
    ├── phantom.db          # SQLite audit log
    ├── pseudonym_map.json  # Reversible path mapping
    ├── reports/            # JSON execution reports
    ├── audit/              # Chain of custody
    ├── staging/            # Processing scratch space
    └── quarantine/         # Files that failed validation
```

### Execution Report

```json
{
  "phantom_version": "0.1.0",
  "statistics": {
    "total_files": 15420,
    "processed": 15398,
    "failed": 22,
    "success_rate": "99.86%",
    "total_size_human": "48.32 GB",
    "duration_seconds": "127.45",
    "throughput_files_per_sec": "120.81",
    "files_with_sensitive_data": 847
  },
  "sensitivity_breakdown": {
    "PUBLIC": 12453,
    "INTERNAL": 1892,
    "CONFIDENTIAL": 734,
    "SECRET": 289,
    "TOP_SECRET": 30
  }
}
```

---

## Path Pseudonymization

Original paths are replaced with deterministic, reversible pseudonyms. Nothing is lost — the mapping is persisted in `pseudonym_map.json`.

```javascript
/home/user/docs/secret_report_2024.pdf
             ↓
PH-a1b2c3d4-e5f6a7b8-1234abcd.pdf
  │  │        │         │
  │  │        │         └─ Hexadecimal timestamp
  │  │        └─ Random entropy block
  │  └─ Deterministic path hash
  └─ Namespace prefix

# Resolve it back
phantom --resolve PH-a1b2c3d4-e5f6a7b8-1234abcd.pdf
```

---

## Testing

Three levels. No compromises.

```bash
# Everything
just test

# Targeted
just test-unit
just test-integration
just test-e2e

# With coverage report (enforced minimum: 70%)
just test-cov

# GPU-specific tests
just test-gpu

# Match a pattern
just test-match "test_vector"
```

```javascript
tests/
├── conftest.py                 # Shared fixtures
├── test_imports.py             # Critical import smoke tests
├── unit/                       # 17 test modules (isolated, fast)
├── integration/                # API + CLI tests (requires running server)
└── e2e/                        # Full pipeline tests (slow, thorough)
```

Coverage is enforced at 70% minimum via `pytest --fail-under=70`. The CI will fail before you merge something that regresses it.

---

## Extending Phantom

### Add a sensitivity pattern

```python
# src/phantom/pipeline/phantom_dag.py
SENSITIVE_PATTERNS = [
    # (regex, label, risk_score)
    (r'your_pattern', 'YOUR_LABEL', 0.9),
]
```

### Add a file type

```python
EXT_MAP = {
    '.yourext': Classification.DOCUMENTS,
}
```

### Add an LLM provider

Implement `AIProvider` from `src/phantom/providers/base.py`:

```python
class YourProvider(AIProvider):
    async def generate(self, prompt: str, **kwargs) -> GenerationResult: ...
    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]: ...
    async def health_check(self) -> ProviderStatus: ...
```

Register it in the API's provider resolver. Done.

---

## Known Constraints

- Files over 10MB are skipped during deep PII scanning (magic bytes + extension classification still applies).
- Encrypted file content cannot be classified beyond magic bytes and extension.
- Metadata stripping is best-effort on proprietary formats — some residual metadata may survive.

We are working on this issues, you can submit a PR or open a issue.

---

## Common Workflows

**Normalize legacy storage:**

```bash
phantom -i /mnt/legacy -o /mnt/normalized -w 8 -v
```

**Export sanitized dataset:**

```bash
phantom-dag -i ./internal -o ./export --sanitize pii
```

**Audit a repo before committing:**

```bash
phantom-scan ./project | jq '.findings[] | select(.risk_score > 0.7)'
```

**Verify a data transfer:**

```bash
phantom-hash ./original > before.json
cp -r ./original ./destination
phantom-hash ./destination > after.json
diff <(jq -S . before.json) <(jq -S . after.json)
```

**Ask questions about your documents:**

```bash
just serve &
curl -X POST http://localhost:8008/vectors/index -F "file=@docs.pdf"
curl -X POST http://localhost:8008/api/chat \
  -d '{"message": "Summarize the main risks", "conversation_id": "s1", "history": []}'
```

---

## Security

Phantom runs a full security stack on every commit:

- **SAST**: CodeQL (Python + JavaScript), Bandit
- **Dependency audit**: pip-audit, safety, cargo-audit
- **Secret scanning**: Trufflehog, detect-secrets
- **SBOM**: CycloneDX, SPDX JSON, Syft — every build
- **Vulnerability scan**: Grype against SBOM
- **Supply chain**: OpenSSF Scorecard

Found a vulnerability? See [SECURITY.md](SECURITY.md).

---

## Development

```bash
nix develop          # enter the pinned shell
just lint            # ruff + mypy
just fmt             # ruff format
just quality         # lint + typecheck + security scan
just ci              # lint + test (what CI runs)
just stats           # project statistics
just info            # environment summary
```

All tasks live in the `justfile`. Run `just` with no arguments to list them.

Pre-commit hooks are installed automatically when you enter `nix develop`. They run ruff, mypy, and bandit before every commit.

---

## Status

| Component                          | Status           |
| ---------------------------------- | ---------------- |
| CORTEX Engine                      | Production ready |
| FAISS Vector Store + Hybrid Search | Production ready |
| FastAPI Server (19 endpoints)      | Production ready |
| DAG Pipeline + Sanitization        | Production ready |
| Prometheus Metrics + Structlog     | Production ready |
| CI/CD (8 workflows)                | Production ready |
| Cortex Desktop (Tauri + SvelteKit) | Beta             |
| CLI Commands                       | Complete         |
| SPECTRE Analysis                   | Production ready |

---

## License

Apache 2.0. See [LICENSE](LICENSE).

---

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

For architecture changes or significant API modifications, open an issue first. The `docs/adr/` directory has the decision history — read it before proposing something we already debated and rejected.

Contributions welcome. Hot takes about the architecture go in the issues. Fixes go in PRs.
