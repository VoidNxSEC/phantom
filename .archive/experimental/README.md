# Experimental Code Archive

This directory contains experimental/WIP code that is not yet production-ready
but shows promise for future development.

## Archival Policy

Code is moved here when it meets these criteria:
1. Has potential value but is incomplete
2. Not part of current production roadmap
3. May be revisited in future phases
4. Too early to delete permanently

## Restoration Policy

When restoring experimental code:
1. Review for bitrot and dependency updates
2. Add comprehensive tests (>70% coverage)
3. Update documentation
4. Ensure it fits current architecture
5. Add to roadmap/backlog

## Archived Experiments

### Tools (CLI Utilities)

#### `tools/project_auditor.py`
- **Archived**: 2026-02-04
- **Status**: CLI stub, incomplete implementation
- **Potential**: Project audit and assessment engine
- **Blockers**: Needs full implementation, tests, CLI integration
- **Notes**: Nice-to-have, not critical for Phase 0-4

#### `tools/prompt_workbench.py`
- **Archived**: 2026-02-04
- **Status**: CLI stub, incomplete implementation
- **Potential**: Prompt engineering and testing workbench
- **Blockers**: Needs full implementation, tests, CLI integration
- **Notes**: Useful for LLM development

#### `tools/vram_calculator.py`
- **Archived**: 2026-02-04
- **Status**: CLI stub, incomplete implementation
- **Potential**: VRAM requirement calculator for ML models
- **Blockers**: Needs full implementation, tests, CLI integration
- **Notes**: Useful for hardware planning

### Applications

#### `apps/desktop/main.py`
- **Archived**: 2026-02-04
- **Status**: Working GTK4/Adwaita application, not production-ready
- **Potential**: Native desktop interface for Phantom (no Electron/web)
- **Features**: Document intelligence dashboard, RAG query interface, vector search
- **Blockers**: Not registered in pyproject.toml, no packaging, desktop priority later
- **Notes**: Beautiful GTK4 app, but API/CLI are higher priority for Phase 0-4

---

**Audit Reference**: Phase 2 - Dead Code Removal
**Decision**: Archive as experimental (Option B) - revisit post-Phase 10
