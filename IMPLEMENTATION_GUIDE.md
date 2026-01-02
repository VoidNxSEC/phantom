# Implementation Guide
## Step-by-Step Instructions for Repository Reorganization

**Target Audience**: Developers implementing the reorganization plan
**Prerequisite**: Read `REORGANIZATION_PLAN.md` first
**Timeline**: 4-6 weeks

---

## Quick Start

### Prerequisites
```bash
# Ensure you have Nix with flakes enabled
nix --version  # Should be 2.4+

# Ensure experimental features are enabled
mkdir -p ~/.config/nix
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf
```

### Setup Development Environment
```bash
cd /home/kernelcore/dev/projects/phantom

# Enter development shell
nix develop

# Verify tools are available
cargo --version
python --version
pytest --version
ruff --version
```

---

## Phase 1: Crate Consolidation (Week 1-2)

### Step 1.1: Backup Current State
```bash
# Create backup branch
git checkout -b backup-pre-reorganization
git push origin backup-pre-reorganization

# Create feature branch for reorganization
git checkout main
git checkout -b feat/reorganize-crates
```

### Step 1.2: Create New Crate Directories
```bash
cd intelagent

# Create security crate (merging audit + privacy)
mkdir -p crates/security/{src,tests}

# Create governance crate (merging dao + rewards)
mkdir -p crates/governance/{src,tests}
```

### Step 1.3: Move Code to New Crates

**Security Crate** (audit + privacy):
```bash
# Create main library file
cat > crates/security/Cargo.toml << 'EOF'
[package]
name = "intelagent-security"
version.workspace = true
edition.workspace = true
license.workspace = true
authors.workspace = true

[dependencies]
# Workspace dependencies
anyhow.workspace = true
thiserror.workspace = true
serde.workspace = true
serde_json.workspace = true
blake3.workspace = true
ed25519-dalek.workspace = true
sqlx.workspace = true
chrono.workspace = true
tracing.workspace = true

# Local workspace crates
intelagent-core = { path = "../core" }

[dev-dependencies]
tokio.workspace = true
mockall.workspace = true

[features]
default = ["audit", "privacy"]
audit = []
privacy = []
EOF

# Create module structure
cat > crates/security/src/lib.rs << 'EOF'
//! IntelAgent Security Module
//!
//! Combines audit trails and privacy features (ZK proofs)

#![warn(missing_docs)]

#[cfg(feature = "audit")]
pub mod audit;

#[cfg(feature = "privacy")]
pub mod privacy;

// Re-export main types
#[cfg(feature = "audit")]
pub use audit::*;

#[cfg(feature = "privacy")]
pub use privacy::*;
EOF

# Move existing audit code
mkdir -p crates/security/src/audit
cp -r crates/audit/src/* crates/security/src/audit/ || echo "No audit code yet"

# Move existing privacy code
mkdir -p crates/security/src/privacy
cp -r crates/privacy/src/* crates/security/src/privacy/ || echo "No privacy code yet"
```

**Governance Crate** (dao + rewards):
```bash
cat > crates/governance/Cargo.toml << 'EOF'
[package]
name = "intelagent-governance"
version.workspace = true
edition.workspace = true
license.workspace = true
authors.workspace = true

[dependencies]
# Workspace dependencies
anyhow.workspace = true
thiserror.workspace = true
serde.workspace = true
serde_json.workspace = true
reqwest.workspace = true
chrono.workspace = true
tracing.workspace = true

# Local workspace crates
intelagent-core = { path = "../core" }

[dev-dependencies]
tokio.workspace = true
mockall.workspace = true

[features]
default = ["dao", "rewards"]
dao = []
rewards = []
EOF

cat > crates/governance/src/lib.rs << 'EOF'
//! IntelAgent Governance Module
//!
//! Combines DAO governance and reward mechanisms

#![warn(missing_docs)]

#[cfg(feature = "dao")]
pub mod dao;

#[cfg(feature = "rewards")]
pub mod rewards;

// Re-export main types
#[cfg(feature = "dao")]
pub use dao::*;

#[cfg(feature = "rewards")]
pub use rewards::*;
EOF

# Move existing dao code
mkdir -p crates/governance/src/dao
cp -r crates/dao/src/* crates/governance/src/dao/ || echo "No dao code yet"

# Move existing rewards code
mkdir -p crates/governance/src/rewards
cp -r crates/rewards/src/* crates/governance/src/rewards/ || echo "No rewards code yet"
```

### Step 1.4: Update Workspace Cargo.toml
```bash
cd intelagent

# Edit Cargo.toml to update members
cat > Cargo.toml << 'EOF'
[workspace]
resolver = "2"
members = [
    "crates/core",
    "crates/mcp",
    "crates/quality",
    "crates/memory",
    "crates/security",      # NEW: replaces audit + privacy
    "crates/governance",    # NEW: replaces dao + rewards
    "crates/cli",
    "crates/soc",
]

[workspace.package]
version = "0.1.0"
edition = "2021"
license = "MIT"
authors = ["kernelcore <kernelcore@voidnix.dev>"]
repository = "https://github.com/kernelcore/intelagent"

[workspace.dependencies]
# Async runtime
tokio = { version = "1.35", features = ["full"] }
async-trait = "0.1"

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
bincode = "1.3"

# Error handling
anyhow = "1.0"
thiserror = "1.0"

# Logging
tracing = "0.1"
tracing-subscriber = "0.3"

# Crypto
blake3 = "1.5"
ed25519-dalek = "2.1"

# Time
chrono = { version = "0.4", features = ["serde"] }

# UUID
uuid = { version = "1.6", features = ["v4", "serde"] }

# HTTP client
reqwest = { version = "0.11", features = ["json"] }

# Database
sqlx = { version = "0.7", features = ["runtime-tokio-native-tls", "sqlite"] }

# Testing
mockall = "0.12"

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = true
EOF
```

### Step 1.5: Verify Build
```bash
cd intelagent

# Check that workspace is valid
cargo check --workspace

# Build all crates
cargo build --workspace

# Run tests (will fail if there are broken dependencies)
cargo test --workspace || echo "Some tests may fail - this is expected"
```

### Step 1.6: Commit Changes
```bash
cd /home/kernelcore/dev/projects/phantom

git add intelagent/
git commit -m "refactor(intelagent): consolidate crates from 10 to 7

- Merge audit + privacy → security crate
- Merge dao + rewards → governance crate
- Update workspace dependencies
- Maintain feature flags for gradual migration

BREAKING CHANGE: Crate structure has changed"
```

---

## Phase 2: Adopt Enhanced Flake (Week 2)

### Step 2.1: Replace flake.nix
```bash
cd /home/kernelcore/dev/projects/phantom

# Backup current flake
cp flake.nix flake.nix.backup

# Use enhanced flake
cp flake-enhanced.nix flake.nix

# Update flake lock
nix flake update
```

### Step 2.2: Test Enhanced Flake
```bash
# Test dev shell
nix develop

# Test builds
nix build .#intelagent
nix build .#phantom

# Test checks (this will run all CI checks locally)
nix flake check --print-build-logs
```

### Step 2.3: Commit Flake Changes
```bash
git add flake.nix flake.lock
git commit -m "build: adopt Crane for incremental Rust builds

- Add rust-overlay for stable toolchain
- Add Crane for dependency caching
- Implement Nix checks (tests, clippy, fmt, audit)
- Add Python checks (tests, lint, fmt)
- Significantly faster builds with caching"
```

---

## Phase 3: Setup CI/CD (Week 3)

### Step 3.1: Add GitHub Actions Workflows
```bash
# Workflows are already created in .github/workflows/
git add .github/workflows/
git commit -m "ci: add comprehensive CI/CD pipelines

- Main CI workflow (tests, linting, builds)
- Security audit workflow (weekly scans)
- Release workflow (automated releases)
- Use Cachix for binary caching"
```

### Step 3.2: Setup Cachix

1. Create account at https://cachix.org
2. Create cache named `phantom`
3. Get auth token from https://app.cachix.org/cache/phantom/settings

### Step 3.3: Add GitHub Secrets
```bash
# Go to: https://github.com/kernelcore/phantom/settings/secrets/actions
# Add the following secrets:

# CACHIX_AUTH_TOKEN: from Cachix dashboard
# PYPI_TOKEN: from PyPI (for releases)
# CODECOV_TOKEN: from codecov.io (for coverage)
```

### Step 3.4: Configure Branch Protection

1. Go to: `https://github.com/kernelcore/phantom/settings/branches`
2. Add rule for `main` branch:
   - Require status checks: `CI Success`
   - Require approvals: 1
   - Require linear history: ✓
   - Include administrators: ✓

### Step 3.5: Test CI Pipeline
```bash
# Push to feature branch
git push origin feat/reorganize-crates

# GitHub Actions will automatically run
# Check: https://github.com/kernelcore/phantom/actions

# Wait for all checks to pass
```

---

## Phase 4: Implement Testing (Week 4)

### Step 4.1: Create Test Structure
```bash
cd /home/kernelcore/dev/projects/phantom

# Create test directories
mkdir -p tests/python/{unit,integration,e2e}
mkdir -p tests/rust/{unit,integration,benchmarks}
mkdir -p tests/desktop/{unit,e2e}

# Add __init__.py files
touch tests/python/__init__.py
touch tests/python/unit/__init__.py
touch tests/python/integration/__init__.py
touch tests/python/e2e/__init__.py
```

### Step 4.2: Add Python Unit Tests
```bash
cat > tests/python/unit/test_cortex.py << 'EOF'
"""Unit tests for Cortex processor"""
import pytest
from phantom.core.cortex import CortexProcessor

class TestCortexProcessor:
    """Test suite for CortexProcessor"""

    @pytest.fixture
    def processor(self):
        """Create a test processor instance"""
        return CortexProcessor(model="test-model")

    def test_initialization(self, processor):
        """Test processor initialization"""
        assert processor is not None
        assert processor.model == "test-model"

    def test_semantic_chunking(self, processor):
        """Test semantic chunking functionality"""
        text = "This is a test document. " * 100
        chunks = processor.chunk_text(text, max_tokens=512)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    @pytest.mark.slow
    def test_embedding_generation(self, processor):
        """Test embedding generation (slow)"""
        text = "Sample text for embedding"
        embedding = processor.generate_embedding(text)

        assert embedding is not None
        assert len(embedding) > 0
EOF
```

### Step 4.3: Add Rust Unit Tests
```bash
cat > intelagent/crates/core/tests/integration_test.rs << 'EOF'
//! Integration tests for core crate

use intelagent_core::{Agent, Task, Context};

#[tokio::test]
async fn test_agent_basic_execution() {
    // This is a placeholder - implement with actual agent
    let task = Task::new("test", "input");
    assert_eq!(task.kind, "test");
}

#[tokio::test]
async fn test_context_creation() {
    let context = Context::new();
    assert!(context.is_empty());
}
EOF
```

### Step 4.4: Run Tests Locally
```bash
# Python tests
nix develop --command pytest tests/python/ -v

# Rust tests
nix develop --command bash -c "cd intelagent && cargo test --workspace"

# All tests via Nix checks
nix flake check
```

### Step 4.5: Commit Tests
```bash
git add tests/ intelagent/crates/*/tests/
git commit -m "test: add comprehensive test suite

- Python unit tests for CORTEX
- Rust integration tests for IntelAgent
- Configure pytest with coverage
- Add test markers (unit, integration, e2e, slow)"
```

---

## Phase 5: Setup Pre-commit Hooks (Week 4)

### Step 5.1: Install Pre-commit
```bash
nix develop

# Pre-commit should be available in the shell
pre-commit --version
```

### Step 5.2: Install Hooks
```bash
# Configuration is already in .pre-commit-config.yaml
pre-commit install
pre-commit install --hook-type commit-msg
```

### Step 5.3: Test Pre-commit
```bash
# Run on all files
pre-commit run --all-files

# Should run:
# - Ruff (Python linting & formatting)
# - Cargo fmt (Rust formatting)
# - Cargo clippy (Rust linting)
# - Various file checks
# - Nixpkgs-fmt (Nix formatting)
```

### Step 5.4: Commit Hook Configuration
```bash
git add .pre-commit-config.yaml
git commit -m "chore: setup pre-commit hooks

- Add ruff for Python
- Add cargo fmt/clippy for Rust
- Add general file checks
- Add Nix formatting
- Configure commitizen for commit messages"
```

---

## Phase 6: Documentation Updates (Week 5)

### Step 6.1: Create Documentation Structure
```bash
mkdir -p docs/{architecture,development,api,guides}

# Main architecture docs
touch docs/architecture/{overview,python-components,rust-components,integration}.md

# Development docs
touch docs/development/{setup,testing,contributing,ci-cd}.md

# API docs
touch docs/api/{python-api,rust-api,rest-api}.md

# Guides
touch docs/guides/{quick-start,classification,deployment}.md
```

### Step 6.2: Update Main README
```bash
# Edit docs/README.md to reflect new structure
# Include:
# - New crate organization
# - CI/CD badge links
# - Quick start with new commands
# - Link to comprehensive documentation
```

### Step 6.3: Generate API Documentation
```bash
# Rust API docs
nix develop --command bash -c "
  cd intelagent
  cargo doc --workspace --no-deps --open
"

# Python API docs (using pdoc or sphinx)
nix develop --command bash -c "
  pip install pdoc3
  pdoc --html --output-dir docs/api/generated src/phantom
"
```

---

## Verification Checklist

After completing all phases, verify:

### Build & Development
- [ ] `nix flake check` passes all checks
- [ ] `nix build .#intelagent` succeeds
- [ ] `nix build .#phantom` succeeds
- [ ] `nix develop` enters shell successfully
- [ ] Rust incremental builds work (`cargo build` < 30s after first build)

### Testing
- [ ] `pytest tests/python/ -v` passes
- [ ] `cargo test --workspace` passes
- [ ] Coverage > 60% (target: 80%)
- [ ] All test markers work (`pytest -m unit`, etc.)

### Code Quality
- [ ] `ruff check src/` has no errors
- [ ] `cargo clippy --all-features -- -D warnings` passes
- [ ] `cargo fmt --check` passes
- [ ] Pre-commit hooks run successfully

### CI/CD
- [ ] GitHub Actions CI workflow passes
- [ ] Cachix caching works (check build times)
- [ ] Security audit workflow scheduled
- [ ] Branch protection enabled

### Documentation
- [ ] README updated with new structure
- [ ] Architecture docs created
- [ ] API documentation generated
- [ ] Development setup guide complete

---

## Troubleshooting

### Issue: Nix flake check fails
**Solution**:
```bash
# Check detailed error
nix flake check --print-build-logs --show-trace

# Common issues:
# 1. Missing dependencies: Update flake inputs
nix flake update

# 2. Build failures: Test individual checks
nix build .#checks.x86_64-linux.intelagent-tests
```

### Issue: Rust compilation errors after consolidation
**Solution**:
```bash
# Clear build cache
cd intelagent
cargo clean

# Update dependencies
cargo update

# Check for broken imports
cargo check --workspace
```

### Issue: Python tests fail
**Solution**:
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# Install dev dependencies
nix develop

# Run with verbose output
pytest tests/python/ -vv
```

### Issue: Pre-commit hooks fail
**Solution**:
```bash
# Update pre-commit
pre-commit autoupdate

# Run specific hook
pre-commit run ruff --all-files

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

---

## Next Steps

After completing this implementation:

1. **Merge to main**: Create PR and get review
2. **Monitor CI**: Watch first few CI runs for issues
3. **Update team**: Notify about new structure
4. **Extract SOC**: Begin Phase 7 from reorganization plan
5. **Implement MCP**: Begin Phase 8 from reorganization plan

---

## Getting Help

- **Issues**: Create GitHub issue with `reorganization` label
- **Questions**: Use GitHub Discussions
- **Urgent**: Contact @kernelcore directly

---

**Last Updated**: 2026-01-02
**Version**: 1.0
