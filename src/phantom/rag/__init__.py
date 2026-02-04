"""
Phantom RAG - Retrieval-Augmented Generation pipeline.

Provides semantic search and LLM-powered Q&A over documents.
"""

from phantom.rag.vectors import (
    FAISSVectorStore,
    NumpyVectorStore,
    SearchResult,
    VectorStore,
    create_vector_store,
)

__all__ = [
    # Vector stores
    "VectorStore",
    "FAISSVectorStore",
    "NumpyVectorStore",
    "SearchResult",
    "create_vector_store",
    # Chunking
    "MarkdownChunker",
    "ChunkStrategy",
    "Chunk",
    # Embeddings
    "EmbeddingManager",
    "EmbeddingGenerator",
]


def __getattr__(name):
    if name in ("MarkdownChunker", "ChunkStrategy", "Chunk"):
        from phantom.rag import cortex_chunker

        return getattr(cortex_chunker, name)
    if name in ("EmbeddingManager", "EmbeddingGenerator"):
        from phantom.rag import cortex_embeddings

        return getattr(cortex_embeddings, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
