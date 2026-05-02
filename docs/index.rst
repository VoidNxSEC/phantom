====================================
Phantom API Documentation
====================================

.. image:: https://img.shields.io/badge/Python-3.11+-blue
.. image:: https://img.shields.io/badge/License-Apache2.0-green
.. image:: https://img.shields.io/badge/Status-Pre--Alpha-orange

AI-powered document intelligence framework with RAG pipeline and semantic search.

Quick Links
===========

- **GitHub**: https://github.com/kernelcore/phantom
- **PyPI**: https://pypi.org/project/phantom
- **Issues**: https://github.com/kernelcore/phantom/issues

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   guides/quickstart
   guides/installation

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/health
   api/documents
   api/vectors
   api/chat
   api/pipeline
   api/models

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   guides/document-processing
   guides/vector-search
   guides/rag-pipeline
   guides/cli-commands

.. toctree::
   :maxdepth: 2
   :caption: Development

   development/architecture
   development/testing
   development/contributing

.. toctree::
   :maxdepth: 2
   :caption: Deployment

   deployment/docker
   deployment/systemd
   deployment/cloud
   deployment/monitoring

API Endpoints
=============

Health & Monitoring
-------------------

.. autosummary::

   GET /health
   GET /ready
   GET /metrics
   GET /api/system/metrics

Document Processing
-------------------

.. autosummary::

   POST /extract
   POST /process
   POST /upload
   POST /api/upload

Vector Store
------------

.. autosummary::

   POST /vectors/search
   POST /vectors/index
   POST /vectors/batch-index

RAG & Chat
----------

.. autosummary::

   POST /api/chat
   POST /api/chat/stream
   GET /api/models
   POST /api/prompt/test

Pipeline & Classification
--------------------------

.. autosummary::

   POST /api/pipeline
   POST /api/pipeline/scan

Module Reference
================

Core Engine
-----------

.. autosummary::
   :toctree: _autosummary

   phantom.core.cortex
   phantom.core.embeddings
   phantom.core.chunking

RAG Pipeline
------------

.. autosummary::
   :toctree: _autosummary

   phantom.rag.vectors
   phantom.rag.search
   phantom.cerebro

Analysis
--------

.. autosummary::
   :toctree: _autosummary

   phantom.analysis.sentiment_analysis
   phantom.analysis.spectre
   phantom.analysis.viability

Pipeline & Classification
-------------------------

.. autosummary::
   :toctree: _autosummary

   phantom.pipeline.phantom_dag
   phantom.pipeline.classifier

Providers
---------

.. autosummary::
   :toctree: _autosummary

   phantom.providers.base
   phantom.providers.llamacpp

CLI Reference
=============

Document Commands
------------------

.. code-block:: bash

   phantom extract -i <input> -o <output>
   phantom analyze <file>
   phantom classify <directory>
   phantom scan <directory>

RAG Commands
-------------

.. code-block:: bash

   phantom rag query <question>
   phantom rag ingest <directory>

Tools
-----

.. code-block:: bash

   phantom tools vram
   phantom tools prompt
   phantom tools audit <directory>

API Server
----------

.. code-block:: bash

   phantom api serve [--host HOST] [--port PORT]

Configuration
=============

Environment Variables
---------------------

.. code-block:: bash

   # API Configuration
   PORT=8000
   HOST=0.0.0.0
   
   # LLM Provider
   LLAMACPP_BASE_URL=http://localhost:8081
   
   # Logging
   PYTHON_LOG_LEVEL=INFO
   
   # Resources
   VRAM_WARNING_MB=512
   VRAM_CRITICAL_MB=256

Examples
========

Extract Insights from Document
-------------------------------

.. code-block:: python

   from phantom.core.cortex import CortexProcessor
   from pathlib import Path
   
   processor = CortexProcessor(enable_vectors=True)
   insights = processor.process_document(Path("document.md"))
   
   print(f"Themes: {len(insights.themes)}")
   print(f"Patterns: {len(insights.patterns)}")
   print(f"Recommendations: {len(insights.recommendations)}")

Semantic Search with RAG
-------------------------

.. code-block:: python

   from phantom.core.embeddings import EmbeddingGenerator
   from phantom.rag.vectors import FAISSVectorStore
   
   embedder = EmbeddingGenerator()
   store = FAISSVectorStore(embedding_dim=384)
   
   # Add documents
   texts = ["First document", "Second document"]
   embeddings = embedder.encode(texts)
   store.add(embeddings, texts)
   
   # Search
   query_embedding = embedder.encode(["search query"])[0]
   results = store.search(query_embedding, top_k=5)

FAQ
===

What is Phantom?
----------------

Phantom is a local-first AI document intelligence framework that processes
unstructured documents into actionable intelligence using semantic chunking,
LLM classification, and semantic search.

Do I need GPU?
--------------

No, Phantom works with CPU. GPU acceleration is optional for faster processing.

How do I deploy Phantom?
------------------------

See the :doc:`Deployment <deployment/docker>` guide for Docker, systemd, and
cloud platform instructions.

Can I use it offline?
---------------------

Yes! Phantom is designed for local-first processing. You can run everything
locally with llama.cpp.

Glossary
========

.. glossary::

   CORTEX
      Core intelligence engine for document processing and insight extraction

   FAISS
      Facebook AI Similarity Search - vector database for semantic search

   RAG
      Retrieval-Augmented Generation - combining search with LLM generation

   Embeddings
      Vector representations of text for similarity search

   Semantic Chunking
      Intelligent text splitting that preserves document structure

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. toctree::
   :hidden:

   changelog
   license
