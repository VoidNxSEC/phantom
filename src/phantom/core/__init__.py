"""
Phantom Core - Insight extraction, chunking, and embeddings.

Classes:
    CortexProcessor - Extract insights from markdown using LLMs
    SemanticChunker - Intelligent text chunking
    EmbeddingGenerator - Generate vector embeddings
"""


# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == "CortexProcessor":
        from phantom.core.cortex import CortexProcessor

        return CortexProcessor
    if name == "SemanticChunker":
        from phantom.core.cortex import SemanticChunker

        return SemanticChunker
    if name == "EmbeddingGenerator":
        from phantom.core.embeddings import EmbeddingGenerator

        return EmbeddingGenerator
    if name in (
        "DocumentInsights",
        "Theme",
        "Pattern",
        "Learning",
        "Concept",
        "Recommendation",
    ):
        from phantom.core import cortex

        return getattr(cortex, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CortexProcessor",
    "SemanticChunker",
    "EmbeddingGenerator",
    "DocumentInsights",
    "Theme",
    "Pattern",
    "Learning",
    "Concept",
    "Recommendation",
]
