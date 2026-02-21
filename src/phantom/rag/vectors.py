"""
Phantom RAG - Vector Store implementations.

Supports FAISS (default) and NumPy fallback.
Hybrid search: BM25 (sparse) + FAISS cosine (dense) fused via Reciprocal Rank Fusion.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

try:
    from rank_bm25 import BM25Okapi

    _BM25_AVAILABLE = True
except ImportError:
    _BM25_AVAILABLE = False
    logging.getLogger(__name__).debug("rank_bm25 not installed; hybrid search will use dense-only")

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with metadata."""

    chunk_id: int
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.score:.3f}] {self.text[:100]}..."


class VectorStore:
    """Abstract base for vector stores."""

    def add(
        self,
        embeddings: np.ndarray,
        texts: list[str],
        metadata: list[dict] | None = None,
    ) -> None:
        """Add embeddings to the store."""
        raise NotImplementedError

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """Search for similar embeddings."""
        raise NotImplementedError

    def hybrid_search(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        top_k: int = 10,
        alpha: float = 0.5,
    ) -> list[SearchResult]:
        """Hybrid BM25 + dense search fused with RRF. Falls back to dense if BM25 unavailable."""
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

        # IndexFlatIP with L2-normalised vectors = cosine similarity
        self.index = faiss.IndexFlatIP(embedding_dim)

        if use_gpu:
            try:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                logger.info("FAISS using GPU")
            except Exception as e:
                logger.warning(f"GPU not available, using CPU: {e}")

        # Storage for texts and metadata
        self.texts: list[str] = []
        self.metadata: list[dict] = []

        # BM25 sparse index (built lazily, invalidated on every add())
        self._bm25_index: Any = None
        self._bm25_dirty: bool = True

    def add(
        self,
        embeddings: np.ndarray,
        texts: list[str],
        metadata: list[dict] | None = None,
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
        self._bm25_dirty = True  # Invalidate BM25 index

        logger.debug(f"Added {len(texts)} vectors, total: {len(self)}")

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
    ) -> list[SearchResult]:
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
        for score, idx in zip(scores[0], indices[0], strict=False):
            if idx < 0:  # FAISS returns -1 for not found
                continue
            results.append(
                SearchResult(
                    chunk_id=int(idx),
                    text=self.texts[idx],
                    score=float(score),
                    metadata=self.metadata[idx],
                )
            )

        return results

    # ── Hybrid search helpers ──────────────────────────────────────────────────

    def _get_bm25(self) -> Any:
        """Return a BM25Okapi index over stored texts, rebuilding if dirty."""
        if not _BM25_AVAILABLE:
            return None
        if self._bm25_dirty or self._bm25_index is None:
            corpus = [t.lower().split() for t in self.texts]
            self._bm25_index = BM25Okapi(corpus)
            self._bm25_dirty = False
            logger.debug(f"BM25 index rebuilt ({len(self.texts)} docs)")
        return self._bm25_index

    def _bm25_search(self, query_text: str, top_k: int) -> list[SearchResult]:
        """Sparse keyword search using BM25Okapi."""
        bm25 = self._get_bm25()
        if bm25 is None or not self.texts:
            return []

        tokens = query_text.lower().split()
        scores = bm25.get_scores(tokens)

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append(
                    SearchResult(
                        chunk_id=int(idx),
                        text=self.texts[idx],
                        score=float(scores[idx]),
                        metadata=self.metadata[idx],
                    )
                )
        return results

    @staticmethod
    def _rrf_combine(
        dense: list[SearchResult],
        sparse: list[SearchResult],
        top_k: int,
        k: int = 60,
    ) -> list[SearchResult]:
        """
        Reciprocal Rank Fusion of dense and sparse result lists.

        RRF score = 1/(k + rank_dense) + 1/(k + rank_sparse)
        Documents missing from one list get rank = len(list) + 1.
        """
        rrf: dict[int, float] = {}

        for rank, r in enumerate(dense, start=1):
            rrf[r.chunk_id] = rrf.get(r.chunk_id, 0.0) + 1.0 / (k + rank)

        sparse_rank_miss = len(dense) + 1
        for rank, r in enumerate(sparse, start=1):
            rrf[r.chunk_id] = rrf.get(r.chunk_id, 0.0) + 1.0 / (k + rank)

        # Propagate dense score for documents only in dense
        idx_to_result: dict[int, SearchResult] = {r.chunk_id: r for r in dense}
        for r in sparse:
            if r.chunk_id not in idx_to_result:
                idx_to_result[r.chunk_id] = r

        sorted_ids = sorted(rrf, key=lambda cid: rrf[cid], reverse=True)[:top_k]
        return [
            SearchResult(
                chunk_id=cid,
                text=idx_to_result[cid].text,
                score=rrf[cid],
                metadata=idx_to_result[cid].metadata,
            )
            for cid in sorted_ids
            if cid in idx_to_result
        ]

    def hybrid_search(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        top_k: int = 10,
        alpha: float = 0.5,
    ) -> list[SearchResult]:
        """
        Hybrid search: BM25 (sparse) + FAISS cosine (dense) fused with RRF.

        Better than pure dense for technical content (code, Nix expressions,
        exact package names) where keyword precision matters alongside semantics.

        Falls back to dense-only if rank_bm25 is not installed.

        Args:
            query_text:      Raw query string (for BM25 tokenisation).
            query_embedding: Pre-computed query vector (for FAISS).
            top_k:           Number of final results.
            alpha:           Unused (RRF is weightless by design), kept for API compatibility.
        """
        dense = self.search(query_embedding, top_k=top_k * 2)

        if not _BM25_AVAILABLE or not self.texts:
            return dense[:top_k]

        sparse = self._bm25_search(query_text, top_k=top_k * 2)
        return self._rrf_combine(dense, sparse, top_k=top_k)

    # ── Persistence ───────────────────────────────────────────────────────────

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
        self.embeddings: list[np.ndarray] = []
        self.texts: list[str] = []
        self.metadata: list[dict] = []
        self._bm25_index: Any = None
        self._bm25_dirty: bool = True

    def add(
        self,
        embeddings: np.ndarray,
        texts: list[str],
        metadata: list[dict] | None = None,
    ) -> None:
        """Add embeddings."""
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)

        for _i, emb in enumerate(embeddings):
            # Normalize
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            self.embeddings.append(emb)

        self.texts.extend(texts)
        self.metadata.extend(metadata or [{}] * len(texts))
        self._bm25_dirty = True

    def hybrid_search(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        top_k: int = 10,
        alpha: float = 0.5,
    ) -> list[SearchResult]:
        """Hybrid BM25 + cosine search (delegates RRF to FAISSVectorStore helper)."""
        dense = self.search(query_embedding, top_k=top_k * 2)
        if not _BM25_AVAILABLE or not self.texts:
            return dense[:top_k]

        if self._bm25_dirty or self._bm25_index is None:
            corpus = [t.lower().split() for t in self.texts]
            self._bm25_index = BM25Okapi(corpus)
            self._bm25_dirty = False

        tokens = query_text.lower().split()
        bm25_scores = self._bm25_index.get_scores(tokens)
        top_sparse_idx = np.argsort(bm25_scores)[::-1][:top_k * 2]
        sparse = [
            SearchResult(
                chunk_id=int(i),
                text=self.texts[i],
                score=float(bm25_scores[i]),
                metadata=self.metadata[i],
            )
            for i in top_sparse_idx
            if bm25_scores[i] > 0
        ]
        return FAISSVectorStore._rrf_combine(dense, sparse, top_k=top_k)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
    ) -> list[SearchResult]:
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
            results.append(
                SearchResult(
                    chunk_id=int(idx),
                    text=self.texts[idx],
                    score=float(scores[idx]),
                    metadata=self.metadata[idx],
                )
            )

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
