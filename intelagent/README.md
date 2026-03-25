# IntelAgent

**Agent orchestration framework — a component of [Phantom](https://github.com/kernelcore/phantom)**

[![Rust](https://img.shields.io/badge/rust-1.75+-orange.svg)](https://www.rust-lang.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](../LICENSE)

---

## What is IntelAgent?

IntelAgent is a Rust workspace that provides agent infrastructure for Phantom. It defines core abstractions (agents, tasks, quality gates, proofs) and organizes domain-specific logic into separate crates: security, governance, memory, quality assessment, and MCP protocol handling.

The project is in early development. The core abstractions are defined; most crate implementations are scaffolding.

---

## Architecture

```
intelagent/
├── crates/
│   ├── core/         # Core traits: Agent, Task, QualityGate, Context, Proof
│   ├── security/     # Privacy and audit modules
│   ├── governance/   # Governance and rules
│   ├── memory/       # Context and knowledge graph
│   ├── quality/      # Quality gates and peer review
│   ├── mcp/          # Model Context Protocol handlers
│   ├── soc/          # SOC (Security Operations Center) binary
│   └── cli/          # Command-line interface
└── Cargo.toml        # Workspace definition
```

### Core Abstractions (`crates/core`)

| Type | Purpose |
|------|---------|
| `Agent` | Autonomous unit of work with capabilities and metadata |
| `Task` | Work item with requirements, constraints, and status tracking |
| `QualityGate` | Objective validation with severity levels |
| `Context` | Shared knowledge and project memory |
| `Proof` | Verification primitives (designed for zero-knowledge proofs) |

---

## Building

IntelAgent is part of the Phantom repository and builds within its Nix environment:

```bash
cd phantom
nix develop

cd intelagent
cargo build
cargo test
```

Or with Cargo directly (Rust 1.75+ required):

```bash
cd phantom/intelagent
cargo build --release
cargo test
```

---

## Integration with Phantom

IntelAgent is designed as a worker backend for Phantom's document intelligence pipeline. The `Agent` trait can wrap Phantom's `CortexProcessor`:

```rust
use intelagent_core::{Agent, Task, Context};

struct PhantomAgent {
    // wraps Phantom's Python processing via API calls
}

impl Agent for PhantomAgent {
    async fn execute(&self, task: Task, context: &Context) -> Result<TaskResult> {
        // call Phantom REST API for document processing
        // return structured results
    }
}
```

---

## Implementation Status

| Crate | Status | Notes |
|-------|--------|-------|
| `core` | Traits defined | Agent, Task, QualityGate, Context, Proof types exported |
| `soc` | Binary scaffold | ~80 lines, entry point exists |
| `security` | Scaffold | Module declared, no implementation |
| `governance` | Scaffold | Module declared, no implementation |
| `memory` | Scaffold | Module declared, no implementation |
| `quality` | Scaffold | Module declared, no implementation |
| `mcp` | Scaffold | Module declared, no implementation |
| `cli` | Scaffold | Module declared, no implementation |

### Planned

- [ ] Basic agent orchestrator
- [ ] Phantom API integration (REST client)
- [ ] MCP server implementation
- [ ] Quality gate evaluation pipeline
- [ ] Audit trail with cryptographic signatures (BLAKE3 + Ed25519)
- [ ] Zero-knowledge proof integration (Circom)
- [ ] DAO governance (Algorand)

The ZK and DAO features are long-term goals. Current priority is the orchestrator and Phantom integration.

---

## Dependencies

Key workspace dependencies (see `Cargo.toml`):

- `tokio` — async runtime
- `serde` / `serde_json` — serialization
- `blake3` — cryptographic hashing
- `ed25519-dalek` — digital signatures
- `sqlx` (SQLite) — persistence
- `reqwest` — HTTP client
- `anyhow` / `thiserror` — error handling

---

## Contributing

Contributions welcome. Guidelines:

- All public APIs must have rustdoc comments
- Tests required for new features
- Run `cargo clippy -- -D warnings` before submitting
- Use [Conventional Commits](https://www.conventionalcommits.org/) format

---

## License

Apache License 2.0 — see [LICENSE](../LICENSE).
