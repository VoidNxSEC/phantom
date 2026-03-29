"""
╔══════════════════════════════════════════════════════════════════╗
║  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗ ║
║  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║ ║
║  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║ ║
║  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║ ║
║  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║ ║
║  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝ ║
╚══════════════════════════════════════════════════════════════════╝

Phantom - AI-Powered Document Intelligence & Classification Pipeline

Modules:
    core     - Insight extraction, chunking, embeddings
    analysis - Sentiment, entities, topics, viability
    pipeline - DAG execution, classification, sanitization
    providers - LLM providers (llama.cpp TURBO, OpenAI, DeepSeek, etc)
    rag      - RAG pipeline with semantic caching
    tools    - VRAM calculator, prompt workbench, auditor
    api      - FastAPI REST endpoints
    cli      - Typer CLI interface
"""

__version__ = "0.0.1"
__codename__ = "PHANTOM"

# Core exports
# Analysis exports
from phantom.analysis import (
    SentimentEngine,
    SpectreAnalyzer,
    ViabilityScorer,
)
from phantom.core import (
    CortexProcessor,
    EmbeddingGenerator,
    SemanticChunker,
)

# Pipeline exports
from phantom.pipeline import (
    DAGPipeline,
    DataSanitizer,
    FileClassifier,
    PhantomPipeline,
)

__all__ = [
    # Version info
    "__version__",
    "__codename__",
    # Core
    "CortexProcessor",
    "SemanticChunker",
    "EmbeddingGenerator",
    # Analysis
    "SentimentEngine",
    "SpectreAnalyzer",
    "ViabilityScorer",
    # Pipeline
    "DAGPipeline",
    "PhantomPipeline",
    "FileClassifier",
    "DataSanitizer",
]
