# Dead Code Archive Manifest

This directory contains code that was removed from the active codebase during
the production readiness audit (2026-02-04).

## Archival Policy

Code is moved here when it meets ALL of these criteria:
1. Not imported by any active module (verified via grep)
2. Not declared in any `__init__.py` `__all__` list
3. Not referenced in pyproject.toml scripts
4. No active tests depend on it

## Archived Modules

### Core Modules

#### `core/cortex_v2.py`
- **Archived**: 2026-02-04
- **Reason**: Experimental v2 implementation never integrated into main codebase
- **Status**: cortex.py (v1) is the canonical implementation
- **Impact**: None - never imported by any module
- **Notes**: Imports from standalone scripts (cortex_chunker, cortex_embeddings) that are also archived

### Provider Modules

#### `providers/cloud_providers.py`
- **Archived**: 2026-02-04
- **Reason**: Never imported, incomplete implementation
- **Status**: Placeholder for future cloud provider implementations
- **Impact**: None - never imported by any module
- **Notes**: OpenAI, Anthropic, DeepSeek providers not yet implemented

#### `providers/cortex_gcp_config.py`
- **Archived**: 2026-02-04
- **Reason**: GCP-specific config never used in codebase
- **Status**: Configuration for unimplemented GCP integration
- **Impact**: None - never imported by any module
- **Notes**: Related to cloud_providers.py (also archived)

### Legacy Directories

#### `phantom_core/`
- **Archived**: 2026-02-04
- **Reason**: Explicitly marked as DEPRECATED (see DEPRECATED.md in directory)
- **Status**: Legacy code, superseded by src/phantom/
- **Impact**: None - never imported by any active module
- **Notes**: Original prototype before restructuring to src/phantom/ layout

### RAG Modules

#### `rag/prompt_pipeline.py`
- **Archived**: 2026-02-04
- **Reason**: Standalone CLI script with `if __name__ == "__main__"`, never imported as module
- **Status**: Experimental prompt management pipeline
- **Impact**: None - never imported by any module
- **Notes**: Functionality may exist elsewhere in the codebase

#### `rag/cortex_chunker.py`
- **Archived**: 2026-02-04
- **Restored**: 2026-02-04 — `tests/unit/test_components.py` and `tests/unit/test_cortex_chunker.py` depend on it; now lives at `src/phantom/rag/cortex_chunker.py`

#### `rag/cortex_embeddings.py`
- **Archived**: 2026-02-04
- **Restored**: 2026-02-04 — `tests/unit/test_components.py` depends on it; now lives at `src/phantom/rag/cortex_embeddings.py`

## Restoration Process

If any of these modules need to be restored:

1. Review the module for bitrot (dependencies may have changed)
2. Add proper tests before integrating
3. Update relevant `__init__.py` to export the module
4. Add to pyproject.toml if it provides CLI commands
5. Document the restoration in CHANGELOG.md

## Audit Trail

| Date | Action | Files | Commit |
|------|--------|-------|--------|
| 2026-02-04 | Initial archive | 6 modules | TBD |

---

**Audit Reference**: Phase 2 - Dead Code Removal
**ADR**: ADR-0024 Phantom Ecosystem Consolidation Strategy
