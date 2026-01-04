# IntelAgent

**Intelligent Agent Orchestration Framework**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rust](https://img.shields.io/badge/rust-1.75+-orange.svg)](https://www.rust-lang.org)

---

## Vision

IntelAgent is a **decentralized, privacy-preserving, formally-verified agent orchestration framework** that replaces "prompts and hope" with "specifications and proofs".

```
Traditional AI Agents:
  ❌ Unpredictable (casino-like results)
  ❌ Opaque (no visibility into reasoning)
  ❌ Centralized (controlled by Big Tech)
  ❌ Privacy-invasive (data sent to cloud)

IntelAgent:
  ✅ Deterministic (same input → same output)
  ✅ Transparent (auditable reasoning)
  ✅ Decentralized (DAO governance)
  ✅ Privacy-preserving (ZK proofs)
```

---

## Core Principles

1. **Quality over Quantity** - Objective metrics, not subjective RLHF
2. **Privacy by Design** - Zero-knowledge proofs for sensitive operations
3. **Decentralized Governance** - DAO controls, not individuals
4. **Formal Verification** - Mathematical proofs, not "it works on my machine"
5. **Collaboration** - Agents work as a team, not isolated workers

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  LAYER 5: COMPLIANCE                    │
│  Audit Trail • Regulatory Reports • ZK Compliance       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   LAYER 4: PRIVACY                      │
│  Circom Circuits • ZK Proofs • Data Commitments         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 LAYER 3: PROTOCOL (MCP)                 │
│  Project Memory • Code Intelligence • Quality Metrics   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              LAYER 2: ORCHESTRATION                     │
│  Agent Coordination • Quality Gates • Peer Review       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                LAYER 1: GOVERNANCE                      │
│  Algorand DAO • Smart Contracts • Token Economics       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│               LAYER 0: INTELLIGENCE                     │
│  Phantom • Custom Workers • LLM Providers               │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Rust 1.75+
- (Optional) Circom for ZK proofs
- (Optional) Algorand node for DAO integration

### Installation

```bash
# Clone repository
git clone https://github.com/kernelcore/intelagent
cd intelagent

# Build all crates
cargo build --release

# Run tests
cargo test
```

### Basic Usage

```rust
use intelagent_core::{Agent, Task, TaskInput, Context};

// Create a task
let task = Task::new(
    "Analyze security vulnerabilities",
    TaskInput::Text(code_snippet),
)
.with_objective("Find SQL injection risks")
.with_privacy(PrivacyLevel::Private);

// Create context
let context = Context::default();

// Execute with agent
let result = agent.execute(task, &context).await?;

// Verify quality
assert!(result.quality_score >= 0.8);
```

---

## Project Structure

```
intelagent/
├── crates/
│   ├── core/           # Core abstractions (Agent, Task, QualityGate)
│   ├── mcp/            # Model Context Protocol servers/clients
│   ├── quality/        # Quality gates, peer review, brainstorm
│   ├── memory/         # Project memory, context graph
│   ├── rewards/        # Token economics, reputation
│   ├── privacy/        # Circom integration, ZK proofs
│   ├── dao/            # Algorand smart contracts (PyTeal)
│   ├── audit/          # Immutable audit trail
│   └── cli/            # Command-line interface
├── circuits/           # Circom circuits for ZK proofs
├── contracts/          # Algorand smart contracts
├── docs/               # Documentation
├── MANIFEST.md         # Project constitution
└── README.md           # This file
```

---

## Key Features

### 1. Objective Quality Metrics

No RLHF bias. Agents evaluated on:
- **Correctness** (40%) - Tests pass, specs met
- **Completeness** (25%) - All requirements addressed
- **Efficiency** (15%) - Resource usage
- **Honesty** (10%) - Admits uncertainty
- **Collaboration** (10%) - Helps peers

### 2. Zero-Knowledge Proofs

Prove correctness WITHOUT revealing sensitive data:

```rust
// Generate ZK proof
let proof = generate_quality_proof(
    private: (task_data, reasoning),
    public: (threshold, compliance_rules),
)?;

// Anyone can verify
assert!(proof.verify() == VerificationResult::Valid);
// But nobody sees the private data!
```

### 3. DAO Governance

Decentralized decision-making:
- Quality standards set by community vote
- Token-based reputation system
- On-chain audit trail (Algorand)
- Transparent, immutable rules

### 4. MCP Integration

Standardized context sharing:
- `project-memory` - Architecture decisions
- `quality-metrics` - Test results, coverage
- `dao-state` - Current rules, governance
- `audit-trail` - Historical events

---

## Roadmap

**Phase 1: Foundation** (Weeks 1-2) ← YOU ARE HERE
- [x] Project structure
- [x] MANIFEST.md
- [x] Core abstractions
- [ ] Basic orchestrator
- [ ] Phantom integration

**Phase 2: Protocol** (Weeks 3-4)
- [ ] MCP servers
- [ ] Context management

**Phase 3: Quality** (Weeks 5-6)
- [ ] Quality gates
- [ ] Peer review

**Phase 4: Privacy** (Weeks 7-10)
- [ ] Circom circuits
- [ ] ZK proof generation

**Phase 5: Governance** (Weeks 11-14)
- [ ] Algorand smart contracts
- [ ] DAO voting

**Phase 6: Compliance** (Weeks 15-16)
- [ ] Audit trail
- [ ] Regulatory reports

---

## Documentation

- **[MANIFEST.md](MANIFEST.md)** - Project constitution (READ THIS FIRST)
- **[Architecture](docs/architecture.md)** - System design
- **[API Docs](https://docs.rs/intelagent-core)** - Rust API reference
- **[Contributing](docs/CONTRIBUTING.md)** - How to contribute

---

## Integration with Phantom

IntelAgent uses [Phantom](https://github.com/kernelcore/phantom) as a worker for document intelligence tasks:

```rust
use intelagent_core::Agent;
use phantom::CortexProcessor;

struct PhantomAgent {
    processor: CortexProcessor,
}

impl Agent for PhantomAgent {
    async fn execute(&self, task: Task, context: &Context) -> Result<TaskResult> {
        let insights = self.processor.process_document(task.input)?;
        TaskResult::success(task.id, TaskOutput::Json(insights), 0.9, 1000)
    }
}
```

---

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

**Key points**:
- Follow the MANIFEST.md principles
- All public APIs must have rustdoc
- Tests required for new features
- Conventional commits

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/kernelcore/intelagent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kernelcore/intelagent/discussions)
- **Matrix**: Coming soon

---

**Built with Rust | Governed by DAO | Privacy by ZK**

```
"From chaos to clarity, from prompts to proofs."
```

Last updated: 2025-01-01
