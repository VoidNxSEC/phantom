# IntelAgent Project Structure

Complete directory structure with descriptions.

```
intelagent/
│
├── Cargo.toml                      # Workspace configuration
├── README.md                       # Main documentation
├── MANIFEST.md                     # Project constitution (MUST READ)
├── LICENSE                         # MIT License
├── .gitignore                      # Git ignore patterns
│
├── crates/                         # Rust crates (modular components)
│   │
│   ├── core/                       # Core abstractions
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs              # Public API exports
│   │       ├── agent.rs            # Agent trait + AgentId
│   │       ├── task.rs             # Task, TaskResult
│   │       ├── quality.rs          # QualityGate trait
│   │       ├── context.rs          # Context, ProjectMemory
│   │       ├── proof.rs            # ZK Proof types
│   │       └── types.rs            # Common types (Reputation, etc)
│   │
│   ├── mcp/                        # Model Context Protocol
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── server.rs           # MCP server implementation
│   │       ├── client.rs           # MCP client
│   │       └── servers/            # Built-in MCP servers
│   │           ├── project_memory.rs
│   │           ├── quality_metrics.rs
│   │           ├── dao_state.rs
│   │           └── audit_trail.rs
│   │
│   ├── quality/                    # Quality framework
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── gates/              # Quality gate implementations
│   │       │   ├── min_quality.rs
│   │       │   ├── validation_evidence.rs
│   │       │   ├── conventions.rs
│   │       │   └── edge_cases.rs
│   │       ├── peer_review.rs      # Peer review system
│   │       └── brainstorm.rs       # Brainstorm protocol
│   │
│   ├── memory/                     # Project memory & context
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── project_memory.rs   # ADRs, conventions, standards
│   │       ├── context_graph.rs    # Knowledge graph
│   │       └── semantic_cache.rs   # Semantic query cache
│   │
│   ├── rewards/                    # Token economics & reputation
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── reputation.rs       # Reputation system
│   │       ├── tokens.rs           # $INTEL token economics
│   │       └── metrics.rs          # Objective metrics
│   │
│   ├── privacy/                    # Privacy & ZK proofs
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── circom.rs           # Circom integration
│   │       ├── proof_gen.rs        # Proof generation
│   │       ├── verification.rs     # Proof verification
│   │       └── commitment.rs       # Data commitments (hashes)
│   │
│   ├── dao/                        # Algorand DAO integration
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── client.rs           # Algorand client
│   │       ├── contracts.rs        # Contract interfaces
│   │       └── governance.rs       # Voting, proposals
│   │
│   ├── audit/                      # Audit trail
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── trail.rs            # Event logging
│   │       ├── storage.rs          # SQLite + Algorand
│   │       └── reports.rs          # Compliance reports
│   │
│   └── cli/                        # Command-line interface
│       ├── Cargo.toml
│       └── src/
│           ├── main.rs             # CLI entry point
│           ├── commands/           # Subcommands
│           │   ├── run.rs
│           │   ├── verify.rs
│           │   └── audit.rs
│           └── ui.rs               # Terminal UI (rich output)
│
├── circuits/                       # Circom ZK circuits
│   ├── quality_proof.circom        # Quality gate proof
│   ├── compliance_proof.circom     # Compliance proof
│   ├── collaboration_proof.circom  # Peer review proof
│   ├── execution_proof.circom      # Execution proof
│   └── build/                      # Compiled circuits (gitignored)
│
├── contracts/                      # Algorand smart contracts (PyTeal)
│   ├── agent_registry.py           # Register/deregister agents
│   ├── quality_validator.py        # Enforce quality standards
│   ├── reward_distributor.py       # Token distribution
│   ├── governance.py               # Voting mechanism
│   ├── audit_logger.py             # Immutable event log
│   └── tests/                      # Contract tests
│
├── examples/                       # Usage examples
│   ├── basic_agent.rs              # Simple echo agent
│   ├── phantom_integration.rs      # Using Phantom as worker
│   ├── quality_gates.rs            # Custom quality gates
│   └── zk_proof.rs                 # ZK proof generation
│
├── tests/                          # Integration tests
│   ├── orchestration.rs            # End-to-end orchestration
│   ├── quality_enforcement.rs      # Quality gate tests
│   └── dao_integration.rs          # DAO smart contract tests
│
├── docs/                           # Documentation
│   ├── architecture.md             # System architecture
│   ├── CONTRIBUTING.md             # Contribution guide
│   ├── api/                        # API documentation
│   ├── tutorials/                  # Step-by-step guides
│   └── adrs/                       # Architecture Decision Records
│       ├── 001-rust-for-core.md
│       ├── 002-algorand-for-dao.md
│       └── 003-circom-for-zk.md
│
├── scripts/                        # Development scripts
│   ├── build-circuits.sh           # Compile Circom circuits
│   ├── deploy-contracts.sh         # Deploy Algorand contracts
│   └── run-tests.sh                # Run all tests
│
└── .github/                        # GitHub workflows
    └── workflows/
        ├── ci.yml                  # Continuous integration
        ├── release.yml             # Release automation
        └── audit.yml               # Security audits
```

## Module Dependencies

```
┌─────────────┐
│     CLI     │
└──────┬──────┘
       │
       ├──────────────────────┐
       │                      │
┌──────▼──────┐        ┌─────▼─────┐
│   Quality   │        │   Audit   │
└──────┬──────┘        └─────┬─────┘
       │                     │
       ├─────────────────────┤
       │                     │
┌──────▼──────┐        ┌─────▼─────┐
│   Privacy   │        │    DAO    │
└──────┬──────┘        └─────┬─────┘
       │                     │
       ├─────────────────────┼──────────────┐
       │                     │              │
┌──────▼──────┐        ┌─────▼─────┐  ┌────▼────┐
│   Memory    │        │   Rewards │  │   MCP   │
└──────┬──────┘        └─────┬─────┘  └────┬────┘
       │                     │              │
       └─────────────────────┴──────────────┘
                            │
                     ┌──────▼──────┐
                     │    CORE     │
                     └─────────────┘
```

## Key Files by Phase

### Phase 1: Foundation (Current)
- ✅ `Cargo.toml` - Workspace setup
- ✅ `MANIFEST.md` - Constitution
- ✅ `crates/core/src/*.rs` - Core abstractions
- ✅ `README.md` - Documentation
- ⏳ `examples/basic_agent.rs` - Example

### Phase 2: Protocol
- `crates/mcp/src/server.rs` - MCP server
- `crates/mcp/src/client.rs` - MCP client
- `crates/memory/src/project_memory.rs` - Context

### Phase 3: Quality
- `crates/quality/src/gates/*.rs` - Quality gates
- `crates/quality/src/peer_review.rs` - Peer review
- `crates/quality/src/brainstorm.rs` - Brainstorm

### Phase 4: Privacy
- `circuits/*.circom` - ZK circuits
- `crates/privacy/src/proof_gen.rs` - Proof generation
- `crates/privacy/src/verification.rs` - Verification

### Phase 5: Governance
- `contracts/*.py` - Smart contracts (PyTeal)
- `crates/dao/src/client.rs` - Algorand integration
- `crates/dao/src/governance.rs` - Voting

### Phase 6: Compliance
- `crates/audit/src/trail.rs` - Audit logging
- `crates/audit/src/reports.rs` - Compliance reports

---

**Navigation Tips:**

- Start with `MANIFEST.md` to understand principles
- Read `README.md` for quick start
- Check `crates/core/src/lib.rs` for API overview
- See `examples/` for usage patterns
- Refer to `docs/architecture.md` for design decisions

---

Last updated: 2025-01-01
