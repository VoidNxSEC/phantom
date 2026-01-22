#!/usr/bin/env python3
"""
CEREBRO - RAG Engine

Motor de Retrieval-Augmented Generation para ADRs.
Usa embeddings + FAISS para busca semântica.
"""

import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

from phantom.cerebro.knowledge_loader import ADRDocument, ADRKnowledgeLoader
from phantom.rag.vectors import FAISSVectorStore, SearchResult

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger("cerebro.rag_engine")


class CerebroRAG:
    """
    RAG Engine especializado em ADRs

    Workflow:
    1. Carrega knowledge_base.json
    2. Gera embeddings para cada ADR
    3. Indexa no FAISS
    4. Provê query semântica
    """

    def __init__(
        self,
        knowledge_base_path: str,
        embedding_model: str = "all-MiniLM-L6-v2",
        index_cache_path: str | None = None,
    ):
        """
        Inicializar Cerebro RAG

        Args:
            knowledge_base_path: Caminho para knowledge_base.json
            embedding_model: Modelo sentence-transformers (default: all-MiniLM-L6-v2)
            index_cache_path: Path para salvar/carregar índice FAISS
        """
        self.knowledge_base_path = knowledge_base_path
        self.embedding_model_name = embedding_model
        self.index_cache_path = Path(index_cache_path) if index_cache_path else None

        # Components
        self.loader = ADRKnowledgeLoader(knowledge_base_path)
        self.documents: list[ADRDocument] = []
        self.encoder: "SentenceTransformer | None" = None
        self.vector_store: FAISSVectorStore | None = None

        logger.info(
            f"CerebroRAG initialized - kb_path={knowledge_base_path}, "
            f"model={embedding_model}"
        )

    def initialize(self) -> None:
        """
        Inicializar RAG: carregar docs, gerar embeddings, indexar

        Pode ser chamado manualmente ou no primeiro query.
        """
        logger.info("Initializing Cerebro RAG...")

        # 1. Carregar documentos
        self.documents = self.loader.load()
        logger.info(f"Loaded {len(self.documents)} ADR documents")

        # 2. Inicializar encoder
        self._init_encoder()

        # 3. Tentar carregar índice do cache
        if self.index_cache_path and self.index_cache_path.exists():
            logger.info(f"Loading cached index from {self.index_cache_path}")
            try:
                self._load_index()
                logger.info("Index loaded from cache")
                return
            except Exception as e:
                logger.warning(f"Failed to load cached index: {e}")

        # 4. Criar índice do zero
        self._build_index()
        logger.info("Cerebro RAG initialized successfully")

    def _init_encoder(self) -> None:
        """Inicializar sentence transformer"""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers required: pip install sentence-transformers"
            )

        logger.info(f"Loading embedding model: {self.embedding_model_name}")
        self.encoder = SentenceTransformer(self.embedding_model_name)  # type: ignore[assignment]
        logger.info(
            f"Model loaded - dimension: {self.encoder.get_sentence_embedding_dimension()}"  # type: ignore[union-attr]
        )

    def _build_index(self) -> None:
        """Gerar embeddings e criar índice FAISS"""
        if not self.encoder:
            raise RuntimeError("Encoder not initialized")

        if not self.documents:
            raise RuntimeError("No documents loaded")

        # Extrair textos
        texts = [doc.text for doc in self.documents]
        logger.info(f"Generating embeddings for {len(texts)} documents...")

        # Gerar embeddings
        embeddings = self.encoder.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True,
            normalize_embeddings=True,  # Para cosine similarity
        )

        # Criar vector store
        embedding_dim = embeddings.shape[1]
        self.vector_store = FAISSVectorStore(embedding_dim=embedding_dim)

        # Adicionar ao índice
        metadata = [doc.metadata for doc in self.documents]
        self.vector_store.add(embeddings, texts, metadata)

        logger.info(f"Index built with {len(self.vector_store)} vectors")

        # Salvar cache se configurado
        if self.index_cache_path:
            self._save_index()

    def _save_index(self) -> None:
        """Salvar índice em disco"""
        if not self.vector_store or not self.index_cache_path:
            return

        try:
            self.index_cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.vector_store.save(self.index_cache_path)
            logger.info(f"Index saved to {self.index_cache_path}")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def _load_index(self) -> None:
        """Carregar índice de disco"""
        if not self.index_cache_path or not self.index_cache_path.exists():
            raise FileNotFoundError("Index cache not found")

        # Dimension from encoder
        if not self.encoder:
            self._init_encoder()

        embedding_dim = self.encoder.get_sentence_embedding_dimension()  # type: ignore[union-attr]
        self.vector_store = FAISSVectorStore(embedding_dim=embedding_dim)
        self.vector_store = self.vector_store.load(self.index_cache_path)  # type: ignore[assignment]

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        min_score: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Buscar ADRs relevantes para query

        Args:
            query_text: Texto da query (ex: "thermal management")
            top_k: Número máximo de resultados
            min_score: Score mínimo (0-1, similarity threshold)

        Returns:
            Lista de dicts com: {id, title, score, text, metadata}
        """
        # Lazy initialization
        if self.vector_store is None:
            self.initialize()

        if not self.encoder or not self.vector_store:
            raise RuntimeError("RAG not initialized")

        # Gerar embedding da query
        query_embedding = self.encoder.encode(
            [query_text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]

        # Buscar similares
        results: list[SearchResult] = self.vector_store.search(
            query_embedding, top_k=top_k
        )

        # Filtrar por score e formatar
        relevant_results = []
        for result in results:
            if result.score >= min_score:
                # Encontrar documento correspondente
                doc = self.documents[result.chunk_id]

                relevant_results.append(
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "status": doc.status,
                        "score": float(result.score),
                        "text": result.text,
                        "metadata": result.metadata,
                    }
                )

        logger.info(
            f"Query '{query_text[:50]}...' returned {len(relevant_results)} results "
            f"(filtered from {len(results)})"
        )

        return relevant_results

    def get_stats(self) -> dict[str, Any]:
        """Estatísticas do RAG"""
        return {
            "documents_loaded": len(self.documents),
            "index_size": len(self.vector_store) if self.vector_store else 0,
            "embedding_model": self.embedding_model_name,
            "embedding_dim": (
                self.encoder.get_sentence_embedding_dimension()
                if self.encoder
                else None
            ),
            "knowledge_base_path": self.knowledge_base_path,
        }


if __name__ == "__main__":
    # Test RAG
    logging.basicConfig(level=logging.INFO)

    kb_path = "/home/kernelcore/arch/adr-ledger/knowledge/knowledge_base.json"
    cache_path = "/tmp/cerebro-faiss-index"

    rag = CerebroRAG(
        knowledge_base_path=kb_path,
        index_cache_path=cache_path,
    )

    print("\n🧠 Initializing Cerebro RAG...")
    rag.initialize()

    print("\nStats:")
    stats = rag.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test queries
    test_queries = [
        "thermal management and temperature monitoring",
        "memory usage and RAM optimization",
        "CEREBRO knowledge management system",
    ]

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        results = rag.query(query, top_k=3, min_score=0.3)

        for i, result in enumerate(results, 1):
            print(f"  {i}. [{result['id']}] {result['title']}")
            print(f"     Score: {result['score']:.3f}")
