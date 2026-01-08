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
    # Pipeline (to be implemented)
    "RAGPipeline",
    "Retriever",
    "Reranker",
    "Generator",
    "ConversationMemory",
]


def __getattr__(name):
    if name == "RAGPipeline":
        from phantom.rag.pipeline import RAGPipeline

        return RAGPipeline
    if name == "Retriever":
        from phantom.rag.retriever import Retriever

        return Retriever
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
