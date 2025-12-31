# PHANTOM

```
╔══════════════════════════════════════════════════════════════════╗
║  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗ ║
║  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║ ║
║  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║ ║
║  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║ ║
║  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║ ║
║  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝ ║
╚══════════════════════════════════════════════════════════════════╝
```

**Living Machine Learning Framework**
*Production-grade document intelligence, RAG pipeline, and AI classification system*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![NixOS](https://img.shields.io/badge/NixOS-declarative-5277C3.svg)](https://nixos.org/)

---

## What is Phantom?

Phantom is a **living ML framework** that transforms unstructured documents into actionable intelligence. Built on a foundation of semantic chunking, vector embeddings, and parallel LLM inference, Phantom provides production-ready tools for document classification, insight extraction, and RAG-powered question answering.

### Core Philosophy

- **Living Framework**: Continuously evolving components that adapt to your data
- **Local-First**: Runs entirely on your infrastructure with llama.cpp
- **Declarative**: Fully reproducible Nix-based environment
- **Production-Grade**: VRAM monitoring, resource throttling, parallel processing
- **Modular**: Use individual components or the complete pipeline

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         PHANTOM v2.0                            │
│                  Living ML Framework Pipeline                   │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        ┌─────▼─────┐   ┌────▼────┐   ┌─────▼──────┐
        │   CORE    │   │   RAG   │   │  ANALYSIS  │
        ├───────────┤   ├─────────┤   ├────────────┤
        │ Cortex    │   │ Vectors │   │ Sentiment  │
        │ Chunking  │   │ FAISS   │   │ Entities   │
        │ Embeddings│   │ Search  │   │ Topics     │
        └─────┬─────┘   └────┬────┘   └─────┬──────┘
              │              │              │
              └──────┬───────┴──────┬───────┘
                     │              │
              ┌──────▼──────┐  ┌───▼────────┐
              │  PIPELINE   │  │ PROVIDERS  │
              ├─────────────┤  ├────────────┤
              │ DAG Exec    │  │ llama.cpp  │
              │ Classifier  │  │ OpenAI     │
              │ Sanitizer   │  │ DeepSeek   │
              └──────┬──────┘  └────────────┘
                     │
         ┌───────────┼───────────┐
         │                       │
    ┌────▼─────┐          ┌─────▼────┐
    │   CLI    │          │   API    │
    ├──────────┤          ├──────────┤
    │ Typer    │          │ FastAPI  │
    │ Rich UI  │          │ REST     │
    └──────────┘          └──────────┘
```

---

## Features

### Document Intelligence (CORTEX)

- **Semantic Chunking**: Intelligent text splitting that preserves context
- **Parallel Classification**: Multi-threaded LLM inference with retry logic
- **Insight Extraction**: Themes, patterns, learnings, concepts, recommendations
- **Pydantic Validation**: Strict schema enforcement for all extracted data

### RAG Pipeline

- **Vector Embeddings**: sentence-transformers with local inference
- **FAISS Indexing**: Blazing-fast similarity search (CPU/GPU)
- **Semantic Caching**: Reduce redundant computations
- **Hybrid Search**: Combine vector and keyword search

### Resource Management

- **VRAM Monitoring**: Real-time GPU memory tracking via nvidia-smi
- **Auto-Throttling**: Pause processing when resources are low
- **Parallel Execution**: ThreadPool-based concurrent processing
- **Progress Tracking**: Rich terminal UI with live updates

### Production Features

- **Declarative Environment**: Fully reproducible Nix flake
- **Type Safety**: Complete Pydantic models for all data structures
- **API Server**: FastAPI REST endpoints with async support
- **CLI Interface**: Feature-rich Typer CLI with beautiful output
- **Testing**: Comprehensive pytest suite

---

## Quick Start

### NixOS (Recommended)

```bash
# Clone repository
git clone https://github.com/kernelcore/phantom.git
cd phantom

# Enter development shell (auto-installs all dependencies)
nix develop

# Process a document
phantom process input.md -o output.json

# Start API server
phantom-api serve
```

### Standard Python

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install
pip install -e .

# Run
phantom process --help
```

---

## Usage

### CLI

```bash
# Process single document with full pipeline
phantom process document.md \
  --output insights.json \
  --enable-vectors \
  --workers 8

# Batch process directory
phantom batch-process ./documents/ \
  --output-dir ./insights/ \
  --chunk-size 1024 \
  --chunk-overlap 128

# Semantic search
phantom search "What are the main security patterns?" \
  --index ./phantom_index \
  --top-k 5

# Start interactive REPL
phantom repl --index ./phantom_index
```

### Python API

```python
from phantom import CortexProcessor
from phantom.providers.llamacpp import LlamaCppProvider

# Initialize processor
processor = CortexProcessor(
    provider=LlamaCppProvider(base_url="http://localhost:8080"),
    chunk_size=1024,
    chunk_overlap=128,
    workers=4,
    enable_vectors=True,
    embedding_model="all-MiniLM-L6-v2",
    verbose=True
)

# Process document
insights = processor.process_document("document.md")

# Access extracted data
for theme in insights.themes:
    print(f"{theme.title}: {theme.description}")

# Semantic search
results = processor.search("security best practices", top_k=5)
for result in results:
    print(f"Score: {result.score:.3f} | {result.text[:100]}...")

# Save vector index
processor.save_index("./phantom_index")
```

### REST API

```bash
# Start server
uvicorn phantom.api.app:app --host 0.0.0.0 --port 8000

# Process document
curl -X POST http://localhost:8000/process \
  -F "file=@document.md" \
  -F "enable_vectors=true"

# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "security patterns", "top_k": 5}'
```

---

## Module Reference

### `phantom.core`

**CortexProcessor** - Main intelligence engine
- Semantic chunking with tiktoken
- Parallel LLM classification
- FAISS vector indexing
- Resource monitoring

**EmbeddingGenerator** - Vector embeddings
- sentence-transformers models
- Batch processing
- GPU acceleration support

**SemanticChunker** - Intelligent text splitting
- Markdown-aware splitting
- Token counting with tiktoken
- Configurable overlap

### `phantom.rag`

**FAISSVectorStore** - Vector database
- CPU/GPU FAISS support
- Metadata filtering
- Persistence to disk

**SearchResult** - Typed search results
- Distance scores
- Metadata extraction
- Ranking utilities

### `phantom.analysis`

**SentimentAnalyzer** - Sentiment detection
**EntityExtractor** - Named entity recognition
**TopicModeler** - LDA topic modeling

### `phantom.pipeline`

**DAGPipeline** - Directed acyclic graph execution
**FileClassifier** - Document classification
**DataSanitizer** - PII removal and sanitization

### `phantom.providers`

**LlamaCppProvider** - llama.cpp integration (TURBO)
**OpenAIProvider** - OpenAI API
**DeepSeekProvider** - DeepSeek API

---

## Configuration

### Environment Variables

```bash
# LLM Provider
export PHANTOM_LLAMACPP_URL="http://localhost:8080"
export PHANTOM_OPENAI_API_KEY="sk-..."

# Resource Limits
export PHANTOM_VRAM_WARNING_MB=512
export PHANTOM_VRAM_CRITICAL_MB=256
export PHANTOM_MAX_WORKERS=8

# Processing
export PHANTOM_CHUNK_SIZE=1024
export PHANTOM_CHUNK_OVERLAP=128
export PHANTOM_BATCH_SIZE=10

# Embeddings
export PHANTOM_EMBEDDING_MODEL="all-MiniLM-L6-v2"
export PHANTOM_VECTOR_BACKEND="faiss"  # or "chromadb"
```

### NixOS Configuration

```nix
# flake.nix integration
{
  inputs.phantom.url = "github:kernelcore/phantom";

  outputs = { self, nixpkgs, phantom }: {
    nixosConfigurations.myhost = nixpkgs.lib.nixosSystem {
      modules = [
        phantom.nixosModules.default
        {
          services.phantom = {
            enable = true;
            api.port = 8000;
            workers = 8;
          };
        }
      ];
    };
  };
}
```

---

## Development

### Project Structure

```
phantom/
├── src/phantom/
│   ├── core/          # CORTEX engine, embeddings, chunking
│   ├── rag/           # Vector stores, search
│   ├── analysis/      # Sentiment, entities, topics
│   ├── pipeline/      # DAG, classification, sanitization
│   ├── providers/     # LLM integrations
│   ├── api/           # FastAPI REST server
│   ├── cli/           # Typer CLI interface
│   └── tools/         # Utilities (VRAM calc, workbench)
├── tests/             # Pytest test suite
├── docs/              # Documentation
├── nix/               # Nix modules and overlays
└── flake.nix          # Reproducible environment
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=phantom --cov-report=html

# Specific module
pytest tests/test_cortex.py -v
```

### Code Quality

```bash
# Format code
ruff format src/

# Lint
ruff check src/

# Type checking
mypy src/
```

---

## Performance

### Benchmarks (RTX 4090, Ryzen 9 7950X)

| Task                    | Documents | Avg Time/Doc | Throughput    |
|-------------------------|-----------|--------------|---------------|
| Semantic Chunking       | 100       | 0.05s        | 2000 docs/min |
| LLM Classification      | 100       | 2.1s         | 28 docs/min   |
| Vector Embedding        | 100       | 0.3s         | 333 docs/min  |
| FAISS Indexing          | 10,000    | 0.001s       | 60k docs/min  |
| End-to-End Pipeline     | 100       | 2.5s         | 24 docs/min   |

### Resource Usage

- **VRAM**: ~4GB (llama.cpp + embedding model)
- **RAM**: ~2GB base + 500MB per worker
- **Disk**: ~100MB per 10k documents (FAISS index)

---

## Roadmap

- [ ] **Multimodal Support**: Image and PDF processing
- [ ] **Streaming API**: Server-Sent Events for real-time updates
- [ ] **Distributed Processing**: Celery/Ray integration
- [ ] **Advanced RAG**: Query rewriting, hypothetical documents
- [ ] **Fine-tuning Tools**: LoRA training for custom classifiers
- [ ] **Desktop App**: Tauri-based GUI (in progress)
- [ ] **Cloud Deployment**: Docker + Kubernetes manifests
- [ ] **Plugin System**: Custom analyzers and processors

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes with tests
4. Run quality checks (`pytest && ruff check`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **llama.cpp**: Fast LLM inference
- **sentence-transformers**: Local embedding models
- **FAISS**: Efficient similarity search
- **Nix**: Reproducible environments
- **FastAPI**: Modern Python web framework

---

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/kernelcore/phantom/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kernelcore/phantom/discussions)

---

Built with **NixOS** | Powered by **llama.cpp TURBO** | Licensed under **MIT**

```
Last updated: 2025-12-30
Version: 2.0.0 (PHANTOM CLASSIFIER)
Codename: CORTEX-UNIFIED
```
