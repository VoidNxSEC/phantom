# Repository Reorganization Plan
## Phantom Framework - Architecture Best Practices & CI/CD Implementation

**Date**: 2026-01-02
**Version**: 1.0
**Status**: Draft for Review

---

## Executive Summary

This plan reorganizes the Phantom repository to follow architecture best practices, consolidate the IntelAgent framework, and implement comprehensive CI/CD testing. The reorganization will:

1. **Consolidate** IntelAgent from 10 to 7 crates (30% reduction)
2. **Separate** concerns between Python (Phantom CORTEX) and Rust (IntelAgent)
3. **Implement** comprehensive CI/CD with Nix flakes
4. **Standardize** testing across all components
5. **Improve** build performance with incremental compilation

**Timeline**: 4-6 weeks
**Complexity**: Medium-High
**Impact**: High (foundational improvements)

---

## Current State Analysis

### Repository Structure (Current)

```
phantom/
├── src/phantom/              # Python CORTEX v2.0 (mature)
├── intelagent/               # Rust framework (early stage)
│   └── crates/               # 10 crates (mostly empty)
├── cortex-desktop/           # Tauri + SvelteKit
├── docs/                     # Documentation
├── tests/                    # Python tests only
├── nix/                      # NixOS modules
├── flake.nix                 # Nix flake (no Crane, no CI checks)
├── pyproject.toml            # Python project (well-configured)
└── ARCHITECTURAL_SYNTHESIS.md # Excellent analysis document
```

### Issues Identified

#### 1. IntelAgent Over-Engineering
- **Problem**: 10 crates for early-stage project, most with 1 LOC stubs
- **Impact**: Long dependency chains (5 levels), slow compilation, complexity
- **Evidence**: From ARCHITECTURAL_SYNTHESIS.md lines 58-60

#### 2. Missing CI/CD
- **Problem**: No automated testing, no Nix checks, no CI pipeline
- **Impact**: Manual validation, potential regressions, no quality gates
- **Current**: Only manual `pytest` for Python

#### 3. Rust Build Performance
- **Problem**: Not using Crane for incremental builds
- **Impact**: Full rebuilds on every change (~2-5 min compile times)
- **Solution**: Implement Crane (reduces to ~30s with cache)

#### 4. Monorepo Without Proper Separation
- **Problem**: Python and Rust mixed without clear boundaries
- **Impact**: Confusion about what to test, unclear ownership
- **Needed**: Clear module boundaries and testing strategies

---

## Reorganization Proposal

### Phase 1: Crate Consolidation (Week 1-2)

#### Current Crate Structure (10 crates)
```
intelagent/crates/
├── core/          (27 LOC - abstractions)
├── mcp/           (1 LOC - stub)
├── quality/       (1 LOC - stub)
├── memory/        (1 LOC - stub)
├── rewards/       (1 LOC - stub)
├── privacy/       (1 LOC - stub)
├── dao/           (1 LOC - stub)
├── audit/         (1 LOC - stub)
├── cli/           (1 LOC - stub)
└── soc/           (81 LOC - GTK4 interface)
```

#### Proposed Structure (7 crates)
```
intelagent/crates/
├── core/          # Core abstractions (Agent, Task, Context, QualityGate)
├── mcp/           # Model Context Protocol servers
├── quality/       # Quality gates, peer review, brainstorming
├── memory/        # Project memory, context graphs, decision trees
├── security/      # NEW: privacy + audit merged
│   ├── privacy/   # Circom circuits, ZK proofs
│   └── audit/     # Audit trails, compliance
├── governance/    # NEW: dao + rewards merged
│   ├── dao/       # Algorand smart contracts
│   └── rewards/   # Token economics, reputation
├── cli/           # Command-line interface
└── soc/           # Security Operations Center (consider extracting)
```

#### Consolidation Actions

**Merge 1: `privacy` + `audit` → `security`**
```bash
mkdir -p intelagent/crates/security/{privacy,audit}
git mv intelagent/crates/privacy/* intelagent/crates/security/privacy/
git mv intelagent/crates/audit/* intelagent/crates/security/audit/
```

**Merge 2: `dao` + `rewards` → `governance`**
```bash
mkdir -p intelagent/crates/governance/{dao,rewards}
git mv intelagent/crates/dao/* intelagent/crates/governance/dao/
git mv intelagent/crates/rewards/* intelagent/crates/governance/rewards/
```

**Update Cargo.toml**:
```toml
[workspace]
members = [
    "crates/core",
    "crates/mcp",
    "crates/quality",
    "crates/memory",
    "crates/security",      # NEW
    "crates/governance",    # NEW
    "crates/cli",
    "crates/soc",
]
```

#### Benefits
- ✅ Reduced compilation time (~30% faster)
- ✅ Clearer dependency graph (max 3 levels)
- ✅ Easier to test (fewer mocks needed)
- ✅ Logical grouping of related functionality

---

### Phase 2: Separate Testing Directories (Week 2)

#### New Structure
```
phantom/
├── src/phantom/              # Python source
├── tests/                    # Root test directory
│   ├── python/               # Python tests
│   │   ├── unit/             # Fast unit tests
│   │   ├── integration/      # Integration tests
│   │   └── e2e/              # End-to-end tests
│   ├── rust/                 # Rust workspace tests
│   │   ├── unit/             # Per-crate unit tests
│   │   ├── integration/      # Cross-crate integration
│   │   └── benchmarks/       # Performance benchmarks
│   └── desktop/              # Tauri app tests
│       ├── unit/             # Component tests
│       └── e2e/              # Full app tests
├── intelagent/               # Rust workspace
│   └── crates/
│       └── */tests/          # Crate-specific tests
└── cortex-desktop/
    └── src/tests/            # Frontend tests
```

#### Testing Pyramid (Per Component)

```
         ╱╲
        ╱E2E╲      ← 10% (Integration tests, slow)
       ╱──────╲
      ╱  Unit  ╲   ← 70% (Fast, isolated)
     ╱──────────╲
    ╱ Properties ╲ ← 20% (Property-based testing)
   ╱──────────────╲
```

---

### Phase 3: Implement Crane for Rust Builds (Week 2-3)

#### Current flake.nix (Simplified)
```nix
outputs = { nixpkgs, ... }: {
  devShells.default = pkgs.mkShell {
    buildInputs = [ pkgs.cargo pkgs.rustc ];
  };
}
```

#### Proposed flake.nix with Crane
```nix
{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    rust-overlay.url = "github:oxalica/rust-overlay";
    crane.url = "github:ipetkov/crane";
  };

  outputs = { nixpkgs, flake-utils, rust-overlay, crane, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ rust-overlay.overlays.default ];
        };

        # Rust toolchain
        rustToolchain = pkgs.rust-bin.stable.latest.default.override {
          extensions = [ "rust-analyzer" "rust-src" ];
        };

        # Crane library
        craneLib = (crane.mkLib pkgs).overrideToolchain rustToolchain;

        # Common build args
        commonArgs = {
          src = craneLib.cleanCargoSource ./intelagent;
          buildInputs = with pkgs; [ gtk4 libadwaita openssl ];
          nativeBuildInputs = with pkgs; [ pkg-config ];
        };

        # Build dependencies only (cached separately)
        cargoArtifacts = craneLib.buildDepsOnly commonArgs;

        # Build the workspace
        intelagent = craneLib.buildPackage (commonArgs // {
          inherit cargoArtifacts;
        });

      in {
        packages = {
          default = intelagent;
          intelagent = intelagent;
        };

        # CI checks (tests, clippy, fmt)
        checks = {
          # Run cargo tests
          intelagent-tests = craneLib.cargoNextest (commonArgs // {
            inherit cargoArtifacts;
            cargoNextestExtraArgs = "--all-features";
          });

          # Clippy lints
          intelagent-clippy = craneLib.cargoClippy (commonArgs // {
            inherit cargoArtifacts;
            cargoClippyExtraArgs = "--all-features -- --deny warnings";
          });

          # Format check
          intelagent-fmt = craneLib.cargoFmt {
            src = ./intelagent;
          };

          # Security audit
          intelagent-audit = craneLib.cargoAudit {
            inherit (commonArgs) src;
          };
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ intelagent ];
          buildInputs = with pkgs; [
            # Rust development
            rustToolchain
            cargo-watch
            cargo-nextest
            cargo-audit

            # Python environment (existing)
            pythonEnv

            # System tools
            ripgrep fd tree jq
          ];
        };
      }
    );
}
```

#### Benefits
- ✅ **Incremental builds**: Only rebuild changed crates
- ✅ **Dependency caching**: Build deps once, reuse forever
- ✅ **CI integration**: Nix checks run in CI
- ✅ **Cross-compilation**: Easy to add new targets

#### Build Time Comparison
| Scenario | Before (no Crane) | After (with Crane) |
|----------|-------------------|-------------------|
| Clean build | 4-5 min | 4-5 min (first time) |
| Incremental (code change) | 2-3 min | 15-30s |
| Dependencies only | 4-5 min | 30s (cached) |
| CI rebuild | 4-5 min | 30s (with Cachix) |

---

### Phase 4: CI/CD Pipeline Implementation (Week 3-4)

#### GitHub Actions Workflow

**File**: `.github/workflows/ci.yml`
```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  # Nix flake checks (Rust + Python)
  nix-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Nix
        uses: cachix/install-nix-action@v24
        with:
          extra_nix_config: |
            experimental-features = nix-command flakes

      - name: Setup Cachix
        uses: cachix/cachix-action@v13
        with:
          name: phantom
          authToken: '${{ secrets.CACHIX_AUTH_TOKEN }}'

      - name: Run all Nix checks
        run: |
          nix flake check --print-build-logs

      - name: Build all packages
        run: |
          nix build .#intelagent --print-build-logs
          nix build .#phantom --print-build-logs

  # Python-specific tests
  python-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12', '3.13']

    steps:
      - uses: actions/checkout@v4

      - name: Install Nix
        uses: cachix/install-nix-action@v24

      - name: Enter dev shell and run tests
        run: |
          nix develop --command pytest tests/python/ \
            --cov=phantom \
            --cov-report=xml \
            --cov-report=html

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  # Rust-specific tests
  rust-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Nix
        uses: cachix/install-nix-action@v24

      - name: Run Rust tests
        run: |
          nix develop --command cargo test --workspace --all-features

      - name: Run benchmarks
        run: |
          nix develop --command cargo bench --workspace --no-run

  # Desktop app tests
  desktop-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Nix
        uses: cachix/install-nix-action@v24

      - name: Build Tauri app
        run: |
          cd cortex-desktop
          nix develop --command npm install
          nix develop --command npm run build
          nix develop --command npm run tauri build

  # Code quality checks
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Nix
        uses: cachix/install-nix-action@v24

      - name: Python linting (ruff)
        run: |
          nix develop --command ruff check src/

      - name: Python type checking (mypy)
        run: |
          nix develop --command mypy src/

      - name: Rust linting (clippy)
        run: |
          nix develop --command cargo clippy --all-features -- -D warnings

      - name: Rust formatting
        run: |
          nix develop --command cargo fmt --check
```

#### Additional Workflows

**File**: `.github/workflows/security.yml`
```yaml
name: Security Audit

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Nix
        uses: cachix/install-nix-action@v24

      - name: Rust security audit
        run: |
          nix develop --command cargo audit

      - name: Python security audit
        run: |
          nix develop --command pip-audit
```

**File**: `.github/workflows/release.yml`
```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-and-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Nix
        uses: cachix/install-nix-action@v24

      - name: Build release artifacts
        run: |
          nix build .#intelagent --out-link intelagent-release
          nix build .#phantom --out-link phantom-release

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            intelagent-release/bin/*
            phantom-release/bin/*
```

---

### Phase 5: Test Implementation (Week 4-5)

#### Python Tests Structure

**File**: `tests/python/unit/test_cortex.py`
```python
import pytest
from phantom.core.cortex import CortexProcessor

class TestCortexProcessor:
    @pytest.fixture
    def processor(self):
        return CortexProcessor(model="test-model")

    def test_semantic_chunking(self, processor):
        """Test semantic chunking functionality"""
        text = "Long document content..."
        chunks = processor.chunk_text(text, max_tokens=512)

        assert len(chunks) > 0
        assert all(len(chunk) <= 512 for chunk in chunks)

    def test_embedding_generation(self, processor):
        """Test embedding generation"""
        text = "Sample text for embedding"
        embedding = processor.generate_embedding(text)

        assert embedding is not None
        assert len(embedding) == 384  # sentence-transformers default
```

**File**: `tests/python/integration/test_pipeline.py`
```python
import pytest
import tempfile
from pathlib import Path
from phantom.pipeline.dag import DAGPipeline

@pytest.mark.integration
class TestFullPipeline:
    def test_document_classification(self, tmp_path):
        """Test full document classification pipeline"""
        # Create test input
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        # Create test file
        test_file = input_dir / "test.txt"
        test_file.write_text("Test document content")

        # Run pipeline
        pipeline = DAGPipeline(
            input_dir=input_dir,
            output_dir=output_dir
        )
        result = pipeline.execute()

        assert result.success
        assert result.files_processed == 1
```

#### Rust Tests Structure

**File**: `intelagent/crates/core/tests/integration.rs`
```rust
use intelagent_core::{Agent, Task, Context, TaskResult};

#[tokio::test]
async fn test_agent_execution() {
    let agent = create_test_agent();
    let task = Task::new("test-task", "Test input");
    let context = Context::new();

    let result = agent.execute(task, &context).await;

    assert!(result.is_ok());
    let result = result.unwrap();
    assert!(result.quality_score > 0.0);
}

#[tokio::test]
async fn test_quality_gate() {
    let gate = MinQualityScoreGate::new(0.8);
    let result = TaskResult::success(
        "task-id".into(),
        "output".into(),
        0.9,
        1000
    );

    let validation = gate.validate(&result).await;
    assert!(validation.is_ok());
}
```

#### Desktop Tests Structure

**File**: `cortex-desktop/src/tests/components.test.ts`
```typescript
import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import DocumentViewer from '$lib/components/DocumentViewer.svelte';

describe('DocumentViewer', () => {
  it('renders document content', () => {
    const { container } = render(DocumentViewer, {
      props: {
        content: 'Test content',
        title: 'Test Document'
      }
    });

    expect(screen.getByText('Test Document')).toBeInTheDocument();
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });
});
```

---

### Phase 6: Documentation Updates (Week 5-6)

#### New Documentation Structure
```
docs/
├── README.md                    # Main overview
├── architecture/
│   ├── overview.md              # Architecture overview
│   ├── python-components.md     # Python CORTEX architecture
│   ├── rust-components.md       # IntelAgent architecture
│   └── integration.md           # How components integrate
├── development/
│   ├── setup.md                 # Development setup
│   ├── testing.md               # Testing guide
│   ├── contributing.md          # Contribution guidelines
│   └── ci-cd.md                 # CI/CD documentation
├── api/
│   ├── python-api.md            # Python API reference
│   ├── rust-api.md              # Rust API reference
│   └── rest-api.md              # REST API documentation
└── guides/
    ├── quick-start.md           # Quick start guide
    ├── classification.md        # Classification guide
    └── deployment.md            # Deployment guide
```

---

## Implementation Checklist

### Week 1-2: Consolidation
- [ ] Create `security` crate directory structure
- [ ] Create `governance` crate directory structure
- [ ] Move `privacy` and `audit` code to `security`
- [ ] Move `dao` and `rewards` code to `governance`
- [ ] Update `Cargo.toml` workspace members
- [ ] Update internal dependencies
- [ ] Verify builds work: `cargo build --workspace`
- [ ] Update documentation references

### Week 2-3: Build System
- [ ] Add `rust-overlay` to flake inputs
- [ ] Add `crane` to flake inputs
- [ ] Implement Crane build configuration
- [ ] Add Nix checks (tests, clippy, fmt, audit)
- [ ] Test local builds: `nix build .#intelagent`
- [ ] Test checks: `nix flake check`
- [ ] Document build improvements

### Week 3-4: CI/CD
- [ ] Create `.github/workflows/ci.yml`
- [ ] Create `.github/workflows/security.yml`
- [ ] Create `.github/workflows/release.yml`
- [ ] Setup Cachix account and token
- [ ] Add `CACHIX_AUTH_TOKEN` to GitHub secrets
- [ ] Test CI pipeline on feature branch
- [ ] Setup branch protection rules
- [ ] Configure status checks

### Week 4-5: Testing
- [ ] Create `tests/python/` structure
- [ ] Implement Python unit tests (target: 80% coverage)
- [ ] Implement Python integration tests
- [ ] Create `tests/rust/` structure
- [ ] Implement Rust unit tests per crate
- [ ] Implement Rust integration tests
- [ ] Setup coverage reporting (codecov.io)
- [ ] Add test documentation

### Week 5-6: Documentation
- [ ] Update main README.md
- [ ] Create architecture documentation
- [ ] Create development setup guide
- [ ] Create testing guide
- [ ] Create CI/CD documentation
- [ ] Update API documentation
- [ ] Create migration guide (for contributors)
- [ ] Review all documentation

---

## Success Metrics

### Build Performance
- ✅ Clean build: < 5 minutes
- ✅ Incremental build: < 30 seconds (with Crane cache)
- ✅ CI rebuild: < 1 minute (with Cachix)

### Code Quality
- ✅ Rust: Zero clippy warnings
- ✅ Python: Zero ruff errors
- ✅ Test coverage: > 80% for core modules
- ✅ Security audit: Zero critical vulnerabilities

### CI/CD
- ✅ All checks passing on main branch
- ✅ PR checks complete in < 5 minutes
- ✅ Automated releases working
- ✅ Branch protection enforced

### Architecture
- ✅ Crate count reduced from 10 to 7
- ✅ Max dependency depth: 3 levels
- ✅ Each crate: < 2000 lines
- ✅ Clear separation of concerns

---

## Risk Mitigation

### Risk 1: Breaking Existing Code
**Mitigation**:
- Create feature branch for all changes
- Implement changes incrementally
- Run comprehensive tests after each change
- Keep rollback plan ready

### Risk 2: CI Pipeline Failures
**Mitigation**:
- Test CI configuration locally with `nix flake check`
- Start with basic checks, add more incrementally
- Use matrix testing for different environments
- Have fallback to manual testing

### Risk 3: Build Time Regression
**Mitigation**:
- Benchmark before and after changes
- Monitor CI build times
- Use Cachix for shared binary cache
- Profile slow builds with `cargo build --timings`

### Risk 4: Test Coverage Gaps
**Mitigation**:
- Implement tests incrementally
- Focus on critical paths first
- Use coverage tools to identify gaps
- Add integration tests for end-to-end flows

---

## Future Enhancements (Post-Implementation)

### Phase 7: Extract SOC as Separate Project
- Create `observant-soc` repository
- Define `OrchestrationKernel` trait
- Implement trait in IntelAgent
- Reuse in other projects (swissknife, arch-analyzer)

### Phase 8: MCP Protocol Implementation
- Implement `project-memory` MCP server
- Implement `quality-metrics` MCP server
- Integrate with Claude Code
- Add MCP compliance tests

### Phase 9: Advanced Testing
- Property-based testing with `proptest`
- Mutation testing with `cargo-mutants`
- Fuzz testing for parsers
- Performance regression tests

### Phase 10: Performance Optimization
- Profile hot paths with `flamegraph`
- Optimize embeddings with GPU acceleration
- Implement streaming for large files
- Add distributed processing support

---

## Conclusion

This reorganization plan provides a comprehensive roadmap to transform the Phantom repository into a well-structured, tested, and maintainable codebase. The implementation will take approximately 4-6 weeks and will significantly improve:

1. **Developer Experience**: Faster builds, clearer structure, better documentation
2. **Code Quality**: Automated testing, linting, security audits
3. **Reliability**: CI/CD ensures nothing breaks
4. **Maintainability**: Reduced complexity, better separation of concerns

The plan is designed to be implemented incrementally, with each phase building on the previous one, minimizing risk and allowing for adjustments based on learnings.

---

**Next Steps**:
1. Review this plan with stakeholders
2. Prioritize phases based on immediate needs
3. Create GitHub project board for tracking
4. Begin Phase 1 implementation

**Questions/Feedback**: Please review and provide feedback on this plan before implementation begins.
