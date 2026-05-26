=====================
Phantom Documentation
=====================

Phantom is a local-first document intelligence framework with a Python runtime,
a FastAPI service, a Tauri/Svelte desktop client, Rust agent primitives, and
reproducible Nix packaging.

Start with the project topology when orienting new contributors or planning
repo cleanup. It separates live runtime code from generated reports, archives,
fixtures, and companion components.

.. toctree::
   :maxdepth: 2
   :caption: Architecture

   architecture/project_topology

Live Surfaces
=============

.. list-table::
   :header-rows: 1
   :widths: 22 48 30

   * - Surface
     - Purpose
     - Entry Point
   * - CLI
     - Extract, analyze, classify, scan, query RAG, run tools, and start the
       local API.
     - ``phantom``
   * - API
     - Health, metrics, document processing, upload, vector search, RAG chat,
       pipeline execution, and judge endpoints.
     - ``phantom-api`` / ``src/phantom/api/app.py``
   * - Desktop
     - Local GUI for the Phantom API and document workflows.
     - ``cortex-desktop/``
   * - Agent Core
     - Rust abstractions for agents, tasks, contexts, proofs, and quality gates.
     - ``intelagent/``
   * - Delivery
     - Nix shell, packages, checks, and OCI fallback.
     - ``flake.nix`` / ``Dockerfile``

Reference Files
===============

The current documentation corpus is mostly Markdown. These files are useful
while the Sphinx/MyST setup is consolidated:

* ``docs/guides/ROADMAP.md`` - current roadmap snapshot.
* ``docs/architecture/CORTEX_V2_ARCHITECTURE.md`` - CORTEX chunking,
  embeddings, vector storage, and retrieval design.
* ``docs/DEPLOYMENT.md`` - deployment notes.
* ``docs/development/NIX_PYTHON_GUIDELINES.md`` - development conventions.
* ``docs/history/`` - completed migrations and historical implementation notes.
* ``arch/`` - generated architecture reports and machine-readable snapshots.

API Endpoints
=============

Health and monitoring:

.. code-block:: text

   GET  /health
   GET  /ready
   GET  /metrics
   GET  /api/system/metrics

Document processing and upload:

.. code-block:: text

   POST /extract
   POST /process
   POST /upload
   POST /api/upload

Vector search and RAG:

.. code-block:: text

   POST /vectors/search
   POST /vectors/index
   POST /vectors/batch-index
   POST /api/chat
   POST /api/chat/stream
   GET  /api/models
   POST /api/prompt/test

Pipeline and integrations:

.. code-block:: text

   POST /api/pipeline
   POST /api/pipeline/scan
   GET  /rag/query
   POST /judge

CLI Reference
=============

.. code-block:: bash

   phantom extract -i <input> -o <output>
   phantom analyze <file>
   phantom classify <directory>
   phantom scan <directory>
   phantom rag ingest <directory>
   phantom rag query <question>
   phantom tools vram
   phantom tools prompt
   phantom tools audit <directory>
   phantom api serve --host 127.0.0.1 --port 8000
   phantom version

Configuration
=============

.. code-block:: bash

   LLAMACPP_BASE_URL=http://localhost:8081
   SECURELLM_BRIDGE_URL=http://localhost:8081
   PYTHON_LOG_LEVEL=INFO
   VRAM_WARNING_MB=512
   VRAM_CRITICAL_MB=256
