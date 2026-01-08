"""
Phantom Core - Embeddings Generator.

Uses sentence-transformers for semantic embeddings.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Default model - good balance of quality and speed
DEFAULT_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 32


@dataclass
class EmbeddingResult:
    """Result from embedding generation."""
    embeddings: np.ndarray
    model: str
    dimension: int
    count: int


class EmbeddingGenerator:
    """
    Generate embeddings using sentence-transformers.
    
    Supports multiple backends and models for flexibility.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str = "cpu",
        cache_dir: Path | None = None,
    ):
        """
        Initialize embedding model.
        
        Args:
            model_name: HuggingFace model name
            device: "cpu" or "cuda"
            cache_dir: Optional cache directory for models
        """
        self.model_name = model_name
        self.device = device
        self.cache_dir = cache_dir
        self._model = None
        self._dimension: int | None = None

    @property
    def model(self):
        """Lazy load model on first use."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    cache_folder=str(self.cache_dir) if self.cache_dir else None,
                )
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Loaded embedding model: {self.model_name} (dim={self._dimension})")
            except ImportError:
                raise ImportError("sentence-transformers required: pip install sentence-transformers")
        return self._model

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None:
            _ = self.model  # Trigger lazy load
        return self._dimension  # type: ignore

    def encode(
        self,
        texts: list[str],
        batch_size: int = BATCH_SIZE,
        show_progress: bool = False,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            normalize: L2 normalize embeddings
            
        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
        )
        return embeddings

    def encode_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """Encode single text."""
        return self.encode([text], normalize=normalize)[0]

    def encode_with_metadata(
        self,
        texts: list[str],
        batch_size: int = BATCH_SIZE,
    ) -> EmbeddingResult:
        """Encode texts and return with metadata."""
        embeddings = self.encode(texts, batch_size=batch_size)
        return EmbeddingResult(
            embeddings=embeddings,
            model=self.model_name,
            dimension=self.dimension,
            count=len(texts),
        )
