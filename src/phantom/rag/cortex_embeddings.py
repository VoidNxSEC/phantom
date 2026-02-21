#!/usr/bin/env python3
"""
CORTEX v2.0 - Embeddings & Vector Storage Module

Generate semantic embeddings and enable similarity search for document chunks
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Embeddings
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available")

# Vector storage
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("faiss not available, using numpy fallback")


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DEFAULT_MODEL = "all-MiniLM-L6-v2"  # 384 dim, fast, good quality
BATCH_SIZE = 32


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════


@dataclass
class SearchResult:
    """Search result with metadata"""

    chunk_id: int
    text: str
    score: float
    metadata: dict

    def __str__(self) -> str:
        return f"SearchResult[{self.score:.3f}]: {self.text[:100]}..."


# ═══════════════════════════════════════════════════════════════
# EMBEDDING GENERATOR
# ═══════════════════════════════════════════════════════════════


class EmbeddingGenerator:
    """Generate embeddings using sentence-transformers"""

    def __init__(self, model_name: str = DEFAULT_MODEL, device: str = "cpu"):
        """
        Initialize embedding model

        Args:
            model_name: HuggingFace model name
            device: "cpu" or "cuda"
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers required. Install with: pip install sentence-transformers"
            )

        self.model_name = model_name
        self.device = device

        logging.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

        logging.info(f"Model loaded: {self.embedding_dim} dimensions, device={device}")

    def encode(
        self,
        texts: list[str],
        batch_size: int = BATCH_SIZE,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Generate embeddings for texts

        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

        return embeddings

    def encode_single(self, text: str) -> np.ndarray:
        """Encode single text"""
        return self.encode([text])[0]


# ═══════════════════════════════════════════════════════════════
# VECTOR STORE - FAISS
# ═══════════════════════════════════════════════════════════════


class FAISSVectorStore:
    """FAISS-based vector store for fast similarity search"""

    def __init__(self, embedding_dim: int):
        """
        Initialize FAISS index

        Args:
            embedding_dim: Dimension of embeddings
        """
        if not FAISS_AVAILABLE:
            raise ImportError("faiss required. Install with: pip install faiss-cpu")

        self.embedding_dim = embedding_dim

        # IndexFlatIP (inner product) with L2-normalised vectors = cosine similarity.
        # Consistent with vectors.py; produces scores in [-1, 1] where 1 = identical.
        self.index = faiss.IndexFlatIP(embedding_dim)

        # Metadata storage (separate from FAISS)
        self.texts: list[str] = []
        self.metadata: list[dict] = []

    def add(
        self,
        embeddings: np.ndarray,
        texts: list[str],
        metadata: list[dict] | None = None,
    ):
        """
        Add embeddings to index

        Args:
            embeddings: numpy array of shape (n, embedding_dim)
            texts: List of texts corresponding to embeddings
            metadata: Optional metadata for each embedding
        """
        if embeddings.shape[1] != self.embedding_dim:
            raise ValueError(
                f"Expected embeddings of dim {self.embedding_dim}, got {embeddings.shape[1]}"
            )

        # L2-normalise so IndexFlatIP computes cosine similarity
        embeddings = embeddings.astype("float32")
        faiss.normalize_L2(embeddings)

        self.index.add(embeddings)
        self.texts.extend(texts)

        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(texts))

    def search(
        self, query_embedding: np.ndarray, top_k: int = 10
    ) -> list[SearchResult]:
        """
        Search for similar embeddings

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of SearchResult objects
        """
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # L2-normalise query to match indexed vectors (cosine similarity via IP)
        query_embedding = query_embedding.astype("float32")
        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(query_embedding, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0], strict=False):
            if idx >= 0 and idx < len(self.texts):  # Valid index
                results.append(
                    SearchResult(
                        chunk_id=int(idx),
                        text=self.texts[idx],
                        score=float(score),
                        metadata=self.metadata[idx],
                    )
                )

        return results

    def save(self, filepath: Path):
        """Save index and metadata to disk"""
        import pickle

        # Save FAISS index
        faiss.write_index(self.index, str(filepath) + ".index")

        # Save metadata
        with open(str(filepath) + ".meta", "wb") as f:
            pickle.dump(
                {
                    "texts": self.texts,
                    "metadata": self.metadata,
                    "embedding_dim": self.embedding_dim,
                },
                f,
            )

        logging.info(f"Saved vector store to {filepath}")

    @classmethod
    def load(cls, filepath: Path) -> "FAISSVectorStore":
        """Load index and metadata from disk"""
        import pickle

        # Load metadata first to get embedding_dim
        with open(str(filepath) + ".meta", "rb") as f:
            data = pickle.load(f)

        # Create instance
        store = cls(data["embedding_dim"])

        # Load FAISS index
        store.index = faiss.read_index(str(filepath) + ".index")
        store.texts = data["texts"]
        store.metadata = data["metadata"]

        logging.info(
            f"Loaded vector store from {filepath} ({len(store.texts)} vectors)"
        )
        return store

    def __len__(self) -> int:
        return self.index.ntotal


# ═══════════════════════════════════════════════════════════════
# NUMPY FALLBACK VECTOR STORE
# ═══════════════════════════════════════════════════════════════


class NumpyVectorStore:
    """Simple numpy-based vector store (fallback when FAISS unavailable)"""

    def __init__(self, embedding_dim: int):
        self.embedding_dim = embedding_dim
        self.embeddings: list[np.ndarray] = []
        self.texts: list[str] = []
        self.metadata: list[dict] = []

    def add(
        self,
        embeddings: np.ndarray,
        texts: list[str],
        metadata: list[dict] | None = None,
    ):
        """Add embeddings"""
        for emb in embeddings:
            self.embeddings.append(emb)

        self.texts.extend(texts)

        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(texts))

    def search(
        self, query_embedding: np.ndarray, top_k: int = 10
    ) -> list[SearchResult]:
        """Search using cosine similarity"""
        if not self.embeddings:
            return []

        # Stack embeddings
        all_embeddings = np.vstack(self.embeddings)

        # Normalize for cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        emb_norms = all_embeddings / np.linalg.norm(
            all_embeddings, axis=1, keepdims=True
        )

        # Compute similarities
        similarities = np.dot(emb_norms, query_norm)

        # Get top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append(
                SearchResult(
                    chunk_id=int(idx),
                    text=self.texts[idx],
                    score=float(similarities[idx]),
                    metadata=self.metadata[idx],
                )
            )

        return results

    def __len__(self) -> int:
        return len(self.embeddings)


# ═══════════════════════════════════════════════════════════════
# MAIN EMBEDDING MANAGER
# ═══════════════════════════════════════════════════════════════


class EmbeddingManager:
    """
    Main interface for embedding generation and vector search
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str = "cpu",
        use_faiss: bool = True,
    ):
        """
        Initialize embedding manager

        Args:
            model_name: Sentence transformer model
            device: "cpu" or "cuda"
            use_faiss: Use FAISS if available, else numpy
        """
        self.generator = EmbeddingGenerator(model_name, device)

        # Choose vector store
        if use_faiss and FAISS_AVAILABLE:
            self.vector_store = FAISSVectorStore(self.generator.embedding_dim)
            logging.info("Using FAISS vector store")
        else:
            self.vector_store = NumpyVectorStore(self.generator.embedding_dim)
            logging.info("Using Numpy vector store (fallback)")

    def add_texts(
        self,
        texts: list[str],
        metadata: list[dict] | None = None,
        batch_size: int = BATCH_SIZE,
    ):
        """
        Add texts to vector store

        Args:
            texts: List of texts to embed and store
            metadata: Optional metadata for each text
            batch_size: Batch size for embedding generation
        """
        logging.info(f"Generating embeddings for {len(texts)} texts...")
        embeddings = self.generator.encode(
            texts, batch_size=batch_size, show_progress=True
        )

        logging.info("Adding to vector store...")
        self.vector_store.add(embeddings, texts, metadata)

        logging.info(f"✓ Added {len(texts)} texts (total: {len(self.vector_store)})")

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """
        Search for similar texts

        Args:
            query: Query text
            top_k: Number of results

        Returns:
            List of SearchResult objects
        """
        query_embedding = self.generator.encode_single(query)
        return self.vector_store.search(query_embedding, top_k)

    def save(self, filepath: Path):
        """Save vector store"""
        if isinstance(self.vector_store, FAISSVectorStore):
            self.vector_store.save(filepath)
        else:
            logging.warning("Numpy vector store save not implemented")

    @classmethod
    def load(
        cls, filepath: Path, model_name: str = DEFAULT_MODEL, device: str = "cpu"
    ) -> "EmbeddingManager":
        """Load vector store"""
        manager = cls(model_name, device, use_faiss=True)
        manager.vector_store = FAISSVectorStore.load(filepath)
        return manager


# ═══════════════════════════════════════════════════════════════
# CLI FOR TESTING
# ═══════════════════════════════════════════════════════════════


def main():
    """Test embeddings"""
    import argparse

    parser = argparse.ArgumentParser(description="Test embeddings and vector search")
    parser.add_argument("--texts", nargs="+", required=True, help="Texts to embed")
    parser.add_argument("--query", help="Query text for search")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name")
    parser.add_argument("--top-k", type=int, default=5, help="Top K results")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Create manager
    print(f"🤖 Initializing with model: {args.model}")
    manager = EmbeddingManager(model_name=args.model)

    # Add texts
    print(f"\n📝 Adding {len(args.texts)} texts...")
    manager.add_texts(args.texts)

    # Search if query provided
    if args.query:
        print(f"\n🔍 Searching for: '{args.query}'")
        results = manager.search(args.query, top_k=args.top_k)

        print(f"\n📊 Top {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.3f}")
            print(f"   Text: {result.text[:200]}...")
            print()


if __name__ == "__main__":
    main()
