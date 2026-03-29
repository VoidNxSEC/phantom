<div align="center">

```
██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
```

**Local-first AI document intelligence. No cloud required. No excuses.**

[![CI](https://github.com/kernelcore/phantom/actions/workflows/ci.yml/badge.svg)](https://github.com/kernelcore/phantom/actions/workflows/ci.yml)
[![Security](https://github.com/kernelcore/phantom/actions/workflows/security.yml/badge.svg)](https://github.com/kernelcore/phantom/actions/workflows/security.yml)
[![CodeQL](https://github.com/kernelcore/phantom/actions/workflows/codeql.yml/badge.svg)](https://github.com/kernelcore/phantom/actions/workflows/codeql.yml)
[![Coverage](https://codecov.io/gh/kernelcore/phantom/branch/main/graph/badge.svg)](https://codecov.io/gh/kernelcore/phantom)
[![License](https://img.shields.io/badge/license-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![Nix](https://img.shields.io/badge/built_with-nix-5277C3?logo=nixos)](https://nixos.org)
[![Version](https://img.shields.io/badge/version-0.0.1-orange)](https://github.com/kernelcore/phantom/releases/tag/0.0.1)

</div>

---

Phantom is a **production-grade document intelligence engine** that classifies, sanitizes, and understands unstructured data — locally, privately, and fast.

It's not a wrapper around an API. It's not a demo. It runs entirely on your hardware, speaks to local LLMs via llama.cpp, indexes your documents into FAISS, and answers questions about them through a hybrid RAG pipeline. The only dependency is Nix.

**What it does in one sentence**: feed it documents, get back structured intelligence — themes, patterns, PII reports, vector search, and RAG-powered chat — without a single byte leaving your machine.

---

## What's Inside

```
phantom/
├── CORTEX Engine          — semantic chunking, LLM classification, VRAM-aware
├── RAG Pipeline           — FAISS + BM25 hybrid search with RRF fusion
├── FastAPI Server         — 20 endpoints, SSE streaming, Prometheus metrics
├── DAG Pipeline           — file classification, PII detection, sanitization
├── IntelAgent (Rust)      — 8-crate workspace: governance, security, memory, MCP
├── Cortex Desktop         — Tauri 2 + SvelteKit GUI
└── CLI                    — Typer-based, scriptable, composable
```

---

## Quickstart

You need [Nix](https://nixos.org/download). That's it.

```bash
git clone https://github.com/kernelcore/phantom
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

No `pip install`. No virtualenv. No "works on my machine." The environment is hermetic and reproducible — today, in six months, on any machine.

---

## Core Capabilities

### CORTEX Engine

The heart of Phantom. Processes raw documents into structured insights through a multi-stage pipeline:

```
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
curl -X POST http://localhost:8000/process \
  -F "file=@report.pdf" \
  -F "chunk_strategy=recursive" \
  -F "chunk_size=1024"
```

### Hybrid Vector Search

Most RAG systems pick either semantic or keyword search. Phantom does both and fuses the results using [Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf):

```
Query → FAISS (dense cosine) ─┐
                               ├→ RRF Fusion → Ranked Results
Query → BM25Okapi (sparse) ───┘
```

- FAISS `IndexFlatIP` with L2-normalized cosine similarity
- Optional GPU acceleration via `StandardGpuResources`
- BM25 index rebuilt lazily on each `add()` — no manual sync required

```bash
curl -X POST http://localhost:8000/vectors/search \
  -H "Content-Type: application/json" \
  -d '{"query": "compliance requirements", "top_k": 5, "search_type": "hybrid"}'
```

### RAG Chat with Streaming

Context-aware chat over your document base. Supports SSE streaming for real-time token delivery.

```bash
# Streaming chat
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key risks in the Q3 report?",
    "conversation_id": "session-001",
    "history": [],
    "context_size": 5
  }'
```

The LLM provider is fully abstracted. Default is `llama.cpp` over HTTP (OpenAI-compatible). OpenAI, Anthropic, and DeepSeek slots exist in the provider registry — they're just not wired yet. That's intentional: we're not building cloud lock-in.

### Data Sanitization Pipeline

Phantom's DAG pipeline processes files through a classification and sanitization chain before they ever touch your vector store:

```
Discovery → Fingerprint → Classify → Pseudonymize → Sanitize → Verify → Persist
```

Four sanitization levels:

| Level | What happens |
|---|---|
| `none` | Direct copy, no modifications |
| `strip_metadata` | EXIF, document properties, author fields removed |
| `redact_pii` | Email, phone, SSN, CPF/CNPJ, credit cards replaced with `[REDACTED]` |
| `full_sanitize` | Everything above + content normalization |

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

| Algorithm | Use case |
|---|---|
| SHA256 | Baseline integrity, broad compatibility |
| BLAKE3 | High-throughput, modern standard |
| xxHash | Maximum speed, block-level streaming |

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

The FastAPI server runs at `http://localhost:8000` by default. Prometheus metrics at `/metrics`, OpenAPI docs at `/docs`.

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Liveness probe |
| `/ready` | GET | Readiness check with downstream deps |
| `/metrics` | GET | Prometheus metrics |
| `/api/system/metrics` | GET | CPU, RAM, VRAM, disk |
| `/process` | POST | Process document with CORTEX |
| `/extract` | POST | Extract insights from text |
| `/upload` | POST | Single file upload |
| `/api/upload` | POST | Multi-file upload with processing |
| `/vectors/search` | POST | Hybrid vector search |
| `/vectors/index` | POST | Index document to FAISS |
| `/vectors/batch-index` | POST | Batch indexing |
| `/api/chat` | POST | RAG-powered chat |
| `/api/chat/stream` | POST | SSE streaming chat |
| `/api/models` | GET | List available LLM models |
| `/api/prompt/test` | POST | Render and token-count a prompt |
| `/api/pipeline` | POST | Full DAG pipeline execution |
| `/api/pipeline/scan` | POST | Scan-only (read-only, no writes) |
| `/judge` | POST | AI-Agent-OS judgment integration |

All request/response bodies are validated by Pydantic v2. No silent failures.

---

## Output Structure

```
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
  "phantom_version": "0.0.1",
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

```
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

## IntelAgent (Rust)

A separate Rust workspace living inside Phantom's repo. Eight crates, each with a defined responsibility:

| Crate | Purpose |
|---|---|
| `intelagent-core` | Shared types, traits, runtime primitives |
| `intelagent-mcp` | MCP protocol implementation (agent-to-agent comms) |
| `intelagent-memory` | Context windows, knowledge graphs |
| `intelagent-quality` | Automated peer review gates |
| `intelagent-security` | Privacy auditing, ed25519 signing, blake3 hashing |
| `intelagent-governance` | DAO-style rules, reward mechanisms |
| `intelagent-cli` | Command-line interface for the agent |
| `intelagent-soc` | GTK4 Security Operations Center UI |

Built with `opt-level=3 + LTO + strip=true`. Production binaries, not dev toys.

```bash
# Build all Rust crates
nix build .#intelagent

# Run Rust tests (nextest parallel runner)
nix flake check
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

```
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

These are documented tradeoffs, not bugs.

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
curl -X POST http://localhost:8000/vectors/index -F "file=@docs.pdf"
curl -X POST http://localhost:8000/api/chat \
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

| Component | Status |
|---|---|
| CORTEX Engine | Production ready |
| FAISS Vector Store + Hybrid Search | Production ready |
| FastAPI Server (20 endpoints) | Production ready |
| DAG Pipeline + Sanitization | Production ready |
| Prometheus Metrics + Structlog | Production ready |
| CI/CD (7 workflows) | Production ready |
| IntelAgent Rust Workspace | Production ready |
| Cortex Desktop (Tauri + SvelteKit) | Beta |
| CLI Commands | Complete |
| Cloud LLM Providers | Planned (Q2 2026) |
| Redis Semantic Cache | Planned (Q2 2026) |
| Kubernetes Helm Charts | Planned (Q3 2026) |

---

## License

Apache 2.0. See [LICENSE](LICENSE).

---

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

For architecture changes or significant API modifications, open an issue first. The `docs/adr/` directory has the decision history — read it before proposing something we already debated and rejected.

Contributions welcome. Hot takes about the architecture go in the issues. Fixes go in PRs.
