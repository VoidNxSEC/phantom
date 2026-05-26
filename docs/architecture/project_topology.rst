================
Project Topology
================

This page is the canonical topology map for the current Phantom repository. It
describes the live project shape as it exists today, separates runtime code from
historical material, and gives future cleanup work a stable target.

System Shape
============

Phantom is a local-first document intelligence stack. The Python package owns
the runtime pipeline and API; the desktop client talks to that API; Nix and
Docker package the same surfaces for repeatable development and deployment.

.. code-block:: text

   user / operator / automation
              |
              v
   +----------------------+     +----------------------+
   | phantom CLI          |     | Cortex Desktop       |
   | Typer commands       |     | Tauri + SvelteKit    |
   +----------+-----------+     +----------+-----------+
              |                            |
              +-------------+--------------+
                            |
                            v
                  +------------------+
                  | Phantom FastAPI  |
                  | src/phantom/api  |
                  +--------+---------+
                           |
        +------------------+-------------------+
        |                  |                   |
        v                  v                   v
   +----------+      +------------+      +-------------+
   | CORTEX   |      | DAG        |      | RAG/Search  |
   | chunking |      | classify   |      | FAISS/BM25  |
   | insights |      | sanitize   |      | Cerebro     |
   +----+-----+      +------+-----+      +------+------+
        |                   |                   |
        +-------------------+-------------------+
                            |
                            v
                 +---------------------+
                 | Providers + Events  |
                 | llama.cpp + NATS    |
                 +---------------------+

Repository Layout
=================

.. list-table::
   :header-rows: 1
   :widths: 24 38 18 20

   * - Path
     - Role
     - Owner Surface
     - Status
   * - ``src/phantom/``
     - Canonical Python package for CLI, API, CORTEX, RAG, DAG, providers,
       NATS, and integration modules.
     - Runtime
     - Live
   * - ``cortex-desktop/``
     - Desktop GUI built with Tauri 2, SvelteKit, Svelte 5, and a typed local
       API client.
     - Application
     - Live
   * - ``intelagent/``
     - Rust workspace for agent abstractions, tasks, context, proofs, and
       quality-gate primitives.
     - Companion runtime
     - Live scaffold
   * - ``spectre/``
     - Companion component for sentiment, pattern extraction, and signal
       processing experiments.
     - Companion service
     - Thin scaffold
   * - ``nix/`` and ``flake.nix``
     - Reproducible dev shell, package outputs, checks, Rust toolchains, and
       desktop build plumbing.
     - Delivery
     - Live
   * - ``Dockerfile``
     - OCI build surface for environments that do not consume Nix directly.
     - Delivery
     - Live
   * - ``tests/``
     - Python unit, integration, and e2e tests for the core runtime surfaces.
     - Quality
     - Live
   * - ``docs/``
     - Curated documentation: architecture, guides, deployment, development
       notes, reference material, and historical summaries.
     - Documentation
     - Live
   * - ``arch/``
     - Generated reports from architecture analysis scripts. These files are
       evidence artifacts, not hand-maintained design docs.
     - Generated evidence
     - Regenerated
   * - ``.audit/``
     - Progress, baseline, and decision artifacts used during repo audits.
     - Governance
     - Evidence
   * - ``input_data/`` and ``demo_input/``
     - Sample and local input datasets for development and demos.
     - Data
     - Non-runtime fixture
   * - ``.phantom/``
     - Local runtime staging, output, and quarantine directories.
     - Runtime state
     - Local only
   * - ``.archive/`` and ``docs/history/``
     - Historical experiments, migration records, and dead-code snapshots.
     - Archive
     - Not runtime

Python Package Map
==================

.. list-table::
   :header-rows: 1
   :widths: 24 56 20

   * - Package
     - Responsibility
     - Public Boundary
   * - ``phantom.cli``
     - Typer command surface for extraction, analysis, classification, scans,
       RAG, utilities, API startup, and version reporting.
     - ``phantom``
   * - ``phantom.api``
     - FastAPI application, health/readiness, metrics, upload, vector, chat,
       pipeline, and judge endpoints.
     - ``phantom-api`` / HTTP
   * - ``phantom.core``
     - CORTEX processor, semantic chunking, embeddings, resource monitoring,
       and core schemas.
     - Python API
   * - ``phantom.rag``
     - Vector primitives, chunk helpers, and FAISS/BM25 retrieval support.
     - Python API / HTTP
   * - ``phantom.cerebro``
     - Higher-level knowledge loading and RAG orchestration.
     - Python API
   * - ``phantom.pipeline``
     - DAG classification, sensitive-data detection, sanitization, quarantine,
       and audit-chain processing.
     - CLI / HTTP
   * - ``phantom.providers``
     - Provider abstraction and local ``llama.cpp`` implementation.
     - Provider API
   * - ``phantom.analysis``
     - Sentiment, SPECTRE, latency, viability, and AI-analysis helpers.
     - Python API
   * - ``phantom.nats``
     - Event publisher, consumer, and scanner integration hooks.
     - NATS
   * - ``phantom.neotron``
     - Compliance and guardrail integration helpers.
     - Python API

Runtime Boundaries
==================

* The Python package is the source of truth for runtime behavior.
* The desktop app must communicate through the local API boundary instead of
  importing Python internals directly.
* Provider-specific code belongs under ``phantom.providers``; core processors
  should depend on the provider abstraction.
* Event-bus integration belongs under ``phantom.nats``; business logic should
  not depend on NATS clients directly.
* Generated reports belong under ``arch/``. Curated architecture decisions and
  durable explanations belong under ``docs/architecture/``.
* Historical material belongs under ``.archive/`` or ``docs/history/`` and must
  not be treated as a runtime source of truth.

Delivery Topology
=================

.. code-block:: text

   flake.nix
   ├── devShells.default       -> Python, Rust, Tauri, testing, and system tools
   ├── packages.phantom        -> Python CLI wrapper
   ├── packages.phantom-api    -> API wrapper
   ├── packages.cortexDesktop  -> Tauri desktop package
   ├── checks.python-*         -> pytest, ruff, format checks
   ├── checks.cortex-*         -> cargo checks for the desktop backend
   └── checks.intelagent-*     -> cargo checks for the Rust agent workspace

Professionalization Rules
=========================

These rules keep the topology clean as the repo grows:

* New Python runtime modules go under ``src/phantom/<domain>/`` and are exported
  through CLI, API, provider, or event boundaries.
* New UI work stays under ``cortex-desktop/`` and treats the FastAPI server as
  the backend contract.
* New Rust agent work stays under ``intelagent/crates/`` until a deliberate
  workspace migration is approved.
* New documentation goes into the most specific ``docs/`` section. Use
  ``docs/architecture/`` for durable design and ``docs/history/`` for completed
  migration notes.
* Root-level Markdown should be reserved for project entry points, release
  notes, security, conduct, contribution, and active status only.
* Local/generated state must stay ignored or isolated. Do not promote
  ``.phantom/``, caches, build outputs, or generated snapshots into the runtime
  topology.

Cleanup Backlog
===============

The current repo is usable, but these follow-up changes would make the physical
layout cleaner after the topology is agreed:

* Normalize the ``skills/`` directory naming and decide whether it is part of
  Phantom or only local operator tooling.
* Move stale root status summaries into ``docs/history/`` or a dedicated
  ``docs/project/`` area.
* Refresh ``arch/README.md`` and the generator labels so they describe Phantom,
  not a generic NixOS configuration.
* Decide whether ``spectre/`` should remain a companion scaffold here or move to
  a separate service repo.
* Make the Sphinx index reflect the real Markdown documentation stack, either by
  adding MyST support or by converting durable pages to reStructuredText.
