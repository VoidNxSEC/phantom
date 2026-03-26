---
id: "ADR-0018"
title: "Sprint Backlog: Remaining Work for Phantom v2.0.0 GA"
status: proposed
date: "2026-03-25"

authors:
  - name: "AI Agent"
    role: "Senior Systems Architect"
    github: "securellm-mcp"
  - name: "kernelcore"
    role: "Project Lead"
    github: "marcosfpina"

reviewers: []

governance:
  classification: "major"
  requires_approval_from:
    - architect
  compliance_tags: ["roadmap", "frontend", "rust-agent", "testing"]
  review_deadline: "2026-04-08"
  auto_supersede_after: "6m"

scope:
  projects:
    - PHANTOM
  layers:
    - frontend
    - agent
    - testing
    - infrastructure
  environments:
    - development
    - staging
    - production

rationale:
  drivers:
    - "Sprint 2026-03 delivered CLI, pipeline API, and streaming chat — core backend is now feature-complete."
    - "Frontend remains a monolithic 1,193-line Svelte component, blocking UI feature development."
    - "IntelAgent Rust workspace is scaffolding only — no functional agent loop."
    - "Zero frontend test coverage creates regression risk as UI grows."
    - "No caching layer increases LLM latency and repeated embedding costs."
  alternatives_considered:
    - "Ship v2.0.0 GA with current state (rejected: frontend and agent gaps too visible)"
    - "Rewrite frontend in GTK4 (deferred: Tauri+SvelteKit investment is sound, needs decomposition not replacement)"
  trade_offs:
    - "Frontend decomposition first vs IntelAgent first: frontend has higher user-facing impact."
    - "BM25 scaling fix now vs later: current volume is fine, defer until 10K+ docs are real."

consequences:
  positive:
    - "Component-based frontend enables parallel UI development."
    - "Functional IntelAgent unlocks autonomous pipeline orchestration."
    - "Frontend tests prevent regressions as features are added."
    - "Cache layer reduces LLM costs and improves response latency."
  negative:
    - "Frontend decomposition is a non-trivial refactor with zero new features."
    - "IntelAgent scope (ZK/DAO) risks scope creep if not staged carefully."
  risks:
    - "Svelte 5 runes migration during decomposition may surface edge cases."
    - "IntelAgent trait design may need revision once real use cases are tested."

implementation:
  effort: "large"
  timeline: "4-6 weeks"
  dependencies:
    - "Completed: CLI implementation (6d593b6)"
    - "Completed: /api/pipeline endpoint (6d593b6)"
    - "Completed: /api/chat/stream SSE (6d593b6)"
  blocked_by: []
  tasks:
    - "P1: Frontend component decomposition"
    - "P2: Frontend test infrastructure (Vitest + Playwright)"
    - "P3: IntelAgent core loop (Agent + Task + QualityGate traits)"
    - "P4: In-memory/Redis cache layer for embeddings and queries"
    - "P5: LLM response streaming in desktop UI"

audit:
  created_at: "2026-03-25T22:00:00Z"
  last_modified: "2026-03-25T22:00:00Z"
  version: 1
---

# ADR-0018: Sprint Backlog — Remaining Work for Phantom v2.0.0 GA

## Context

Sprint 2026-03 closed with commit `6d593b6`, completing the three highest-priority items from the technical analysis:

1. **CLI fully functional** — all 9 commands wired to real modules
2. **`/api/pipeline` + `/api/pipeline/scan`** — DAG orchestrator exposed via REST
3. **`/api/chat/stream`** — SSE streaming with true LlamaCpp streaming support

The backend is now feature-complete for the v2.0.0 scope. This ADR documents the remaining work items, their priority, and implementation guidance for the next sprint(s).

---

## P1: Frontend Component Decomposition

**Priority**: HIGH
**Effort**: Medium (1-2 weeks)
**File**: `cortex-desktop/src/routes/+page.svelte` (1,193 LOC)

### Problem

The entire UI lives in a single monolithic Svelte component. Adding features (progress indicators, error toasts, real-time metrics) requires touching a 1,200-line file with interleaved state for 6 different tabs.

### Proposed Structure

```
cortex-desktop/src/lib/components/
├── ChatPanel.svelte          # RAG conversation UI
├── ProcessPanel.svelte       # Document processing + upload
├── SearchPanel.svelte        # Vector semantic search
├── WorkbenchPanel.svelte     # Prompt engineering
├── LibraryPanel.svelte       # Saved prompts
├── SettingsPanel.svelte      # API configuration
├── SystemMonitor.svelte      # Real-time CPU/VRAM/RAM (new)
├── MessageBubble.svelte      # Chat message rendering
├── FileUploader.svelte       # Drag-and-drop file upload
└── ErrorToast.svelte         # Toast notification system
```

### Implementation Notes

- Extract each tab's markup + reactive state into its own component
- Keep shared state (apiUrl, activeTab, conversationId) in `+page.svelte`
- Pass state down via props, emit events up via Svelte dispatch
- Use Svelte 5 `$state` runes within each component
- Add `SystemMonitor.svelte` calling `/api/system/metrics` on interval

---

## P2: Frontend Test Infrastructure

**Priority**: HIGH
**Effort**: Small (3-5 days)
**Blocked by**: P1 (decomposition makes components testable)

### Setup Required

1. **Vitest** for unit tests (component logic, API client, state management)
2. **Playwright** for e2e tests (full user flows against real API)
3. **Testing Library** (`@testing-library/svelte`) for component rendering

### Critical Test Coverage

- `api.ts` — mock API responses, error handling, timeout behavior
- `ChatPanel.svelte` — message send/receive, source display, streaming
- `SearchPanel.svelte` — query, results display, mode switching
- `SettingsPanel.svelte` — API URL persistence, provider selection

---

## P3: IntelAgent Core Loop

**Priority**: MEDIUM
**Effort**: Large (2-3 weeks for core, ongoing for advanced features)
**Location**: `intelagent/`

### Phase 1 — Core (this sprint)

Implement the fundamental agent loop using the existing trait definitions:

```rust
// crates/core/src/lib.rs
pub trait Agent {
    fn perceive(&mut self, input: &TaskInput) -> Result<Perception>;
    fn decide(&self, perception: &Perception) -> Result<Action>;
    fn act(&mut self, action: &Action) -> Result<TaskOutput>;
    fn reflect(&mut self, output: &TaskOutput) -> Result<()>;
}

pub trait QualityGate {
    fn evaluate(&self, output: &TaskOutput) -> Result<QualityScore>;
    fn threshold(&self) -> f64;
}
```

- Implement a `SimpleAgent` with perceive/decide/act/reflect cycle
- Implement `BasicQualityGate` with configurable threshold
- Wire to Phantom API via HTTP client (reqwest)
- Add CLI command: `intelagent run --task <task.json>`

### Phase 2 — Advanced (defer)

- ZK proofs (Circom) — defer until agent loop is proven
- DAO governance (Algorand) — defer until multi-agent scenarios exist
- Ed25519 signing — add after core loop, before production use

---

## P4: Cache Layer

**Priority**: LOW
**Effort**: Small (3-5 days)
**Location**: `src/phantom/core/cache.py` (new)

### Approach

Start with in-memory LRU cache, add Redis later:

1. **Embedding cache** — hash(text) -> embedding vector (avoid re-encoding)
2. **Query cache** — hash(query + top_k + mode) -> search results (TTL: 5min)
3. **LLM cache** — hash(prompt) -> response (TTL: 30min, disabled by default)

### Interface

```python
class PhantomCache:
    def get_embedding(self, text: str) -> np.ndarray | None
    def set_embedding(self, text: str, embedding: np.ndarray) -> None
    def get_query(self, query: str, top_k: int, mode: str) -> list | None
    def set_query(self, query: str, top_k: int, mode: str, results: list) -> None
    def stats(self) -> dict  # hit rate, size, evictions
```

Integrate into `get_embedding_generator()` and `get_vector_store()` singletons.

---

## P5: Desktop Streaming Integration

**Priority**: LOW
**Effort**: Small (2-3 days)
**Blocked by**: P1 (ChatPanel component)

Wire `ChatPanel.svelte` to `/api/chat/stream` (SSE) instead of `/api/chat`:

```typescript
const eventSource = new EventSource('/api/chat/stream', { method: 'POST', body: ... });
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'token') appendToMessage(data.content);
    if (data.type === 'sources') setSources(data.sources);
    if (data.type === 'done') finalize();
};
```

Note: SSE is GET-only by spec. For POST, use `fetch()` with `ReadableStream` instead:

```typescript
const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
});
const reader = response.body.getReader();
```

---

## Decision

Prioritize **P1 → P2 → P3** in the next sprint. P4 and P5 can be picked up opportunistically or deferred to the following sprint.
