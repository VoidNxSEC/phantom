"""
Phantom RAG - Vector Store implementations.

Supports FAISS (default) and NumPy fallback.
"""

import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with metadata."""
    chunk_id: int
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"[{self.score:.3f}] {self.text[:100]}..."


class VectorStore:
    """Abstract base for vector stores."""
    
    def add(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        metadata: Optional[List[Dict]] = None,
    ) -> None:
        """Add embeddings to the store."""
        raise NotImplementedError
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
    ) -> List[SearchResult]:
        """Search for similar embeddings."""
        raise NotImplementedError
    
    def save(self, filepath: Path) -> None:
        """Save index to disk."""
        raise NotImplementedError
    
    @classmethod
    def load(cls, filepath: Path) -> "VectorStore":
        """Load index from disk."""
        raise NotImplementedError
    
    def __len__(self) -> int:
        raise NotImplementedError


class FAISSVectorStore(VectorStore):
    """FAISS-based vector store for fast similarity search."""
    
    def __init__(self, embedding_dim: int, use_gpu: bool = False):
        """
        Initialize FAISS index.
        
        Args:
            embedding_dim: Dimension of embeddings
            use_gpu: Use GPU acceleration if available
        """
        try:
            import faiss
        except ImportError:
            raise ImportError("FAISS required: pip install faiss-cpu or faiss-gpu")
        
        self.embedding_dim = embedding_dim
        self.use_gpu = use_gpu
        
        # Create index with L2 distance
        self.index = faiss.IndexFlatIP(embedding_dim)  # Inner product for cosine sim
        
        if use_gpu:
            try:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                logger.info("FAISS using GPU")
            except Exception as e:
                logger.warning(f"GPU not available, using CPU: {e}")
        
        # Storage for texts and metadata
        self.texts: List[str] = []
        self.metadata: List[Dict] = []
    
    def add(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        metadata: Optional[List[Dict]] = None,
    ) -> None:
        """Add embeddings to index."""
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)
        
        # Normalize for cosine similarity
        faiss = __import__("faiss")
        faiss.normalize_L2(embeddings)
        
        self.index.add(embeddings.astype(np.float32))
        self.texts.extend(texts)
        self.metadata.extend(metadata or [{}] * len(texts))
        
        logger.debug(f"Added {len(texts)} vectors, total: {len(self)}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
    ) -> List[SearchResult]:
        """Search for similar embeddings."""
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize query
        faiss = __import__("faiss")
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(
            query_embedding.astype(np.float32),
            min(top_k, len(self)),
        )
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:  # FAISS returns -1 for not found
                continue
            results.append(SearchResult(
                chunk_id=int(idx),
                text=self.texts[idx],
                score=float(score),
                metadata=self.metadata[idx],
            ))
        
        return results
    
    def save(self, filepath: Path) -> None:
        """Save index and metadata to disk."""
        import faiss
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(filepath.with_suffix(".faiss")))
        
        # Save metadata
        metadata = {
            "embedding_dim": self.embedding_dim,
            "texts": self.texts,
            "metadata": self.metadata,
        }
        with open(filepath.with_suffix(".json"), "w") as f:
            json.dump(metadata, f)
        
        logger.info(f"Saved vector store to {filepath}")
    
    @classmethod
    def load(cls, filepath: Path) -> "FAISSVectorStore":
        """Load index from disk."""
        import faiss
        
        filepath = Path(filepath)
        
        # Load metadata first to get dimension
        with open(filepath.with_suffix(".json")) as f:
            metadata = json.load(f)
        
        store = cls(metadata["embedding_dim"])
        store.index = faiss.read_index(str(filepath.with_suffix(".faiss")))
        store.texts = metadata["texts"]
        store.metadata = metadata["metadata"]
        
        logger.info(f"Loaded vector store with {len(store)} vectors")
        return store
    
    def __len__(self) -> int:
        return self.index.ntotal


class NumpyVectorStore(VectorStore):
    """Simple numpy-based vector store (fallback when FAISS unavailable)."""
    
    def __init__(self, embedding_dim: int):
        self.embedding_dim = embedding_dim
        self.embeddings: List[np.ndarray] = []
        self.texts: List[str] = []
        self.metadata: List[Dict] = []
    
    def add(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        metadata: Optional[List[Dict]] = None,
    ) -> None:
        """Add embeddings."""
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)
        
        for i, emb in enumerate(embeddings):
            # Normalize
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            self.embeddings.append(emb)
        
        self.texts.extend(texts)
        self.metadata.extend(metadata or [{}] * len(texts))
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
    ) -> List[SearchResult]:
        """Search using cosine similarity."""
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize query
        query = query_embedding[0]
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm
        
        # Calculate similarities
        if not self.embeddings:
            return []
        
        embeddings_matrix = np.array(self.embeddings)
        scores = np.dot(embeddings_matrix, query)
        
        # Get top-k
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append(SearchResult(
                chunk_id=int(idx),
                text=self.texts[idx],
                score=float(scores[idx]),
                metadata=self.metadata[idx],
            ))
        
        return results
    
    def save(self, filepath: Path) -> None:
        """Save to disk."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "embedding_dim": self.embedding_dim,
            "embeddings": [e.tolist() for e in self.embeddings],
            "texts": self.texts,
            "metadata": self.metadata,
        }
        with open(filepath.with_suffix(".json"), "w") as f:
            json.dump(data, f)
    
    @classmethod
    def load(cls, filepath: Path) -> "NumpyVectorStore":
        """Load from disk."""
        with open(Path(filepath).with_suffix(".json")) as f:
            data = json.load(f)
        
        store = cls(data["embedding_dim"])
        store.embeddings = [np.array(e) for e in data["embeddings"]]
        store.texts = data["texts"]
        store.metadata = data["metadata"]
        return store
    
    def __len__(self) -> int:
        return len(self.embeddings)


def create_vector_store(
    embedding_dim: int,
    backend: str = "auto",
    use_gpu: bool = False,
) -> VectorStore:
    """
    Create a vector store.
    
    Args:
        embedding_dim: Dimension of embeddings
        backend: "faiss", "numpy", or "auto" (tries FAISS first)
        use_gpu: Use GPU if available (FAISS only)
    """
    if backend == "auto":
        try:
            return FAISSVectorStore(embedding_dim, use_gpu=use_gpu)
        except ImportError:
            logger.warning("FAISS not available, using NumPy fallback")
            return NumpyVectorStore(embedding_dim)
    elif backend == "faiss":
        return FAISSVectorStore(embedding_dim, use_gpu=use_gpu)
    elif backend == "numpy":
        return NumpyVectorStore(embedding_dim)
    else:
        raise ValueError(f"Unknown backend: {backend}")
