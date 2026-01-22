#!/usr/bin/env python3
"""
CEREBRO - Knowledge Loader

Carrega knowledge_base.json do ADR-Ledger e prepara documentos para indexação.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("cerebro.knowledge_loader")


@dataclass
class ADRDocument:
    """Representação de uma ADR para RAG"""

    id: str
    title: str
    status: str
    summary: str
    text: str  # Texto completo concatenado para embedding
    metadata: dict[str, Any]

    def __str__(self) -> str:
        return f"[{self.id}] {self.title} ({self.status})"


class ADRKnowledgeLoader:
    """Carrega e processa knowledge base de ADRs"""

    def __init__(self, knowledge_base_path: str):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.raw_data: dict[str, Any] = {}
        self.documents: list[ADRDocument] = []

    def load(self) -> list[ADRDocument]:
        """
        Carregar knowledge_base.json e converter para documentos

        Returns:
            Lista de ADRDocuments prontos para indexação
        """
        if not self.knowledge_base_path.exists():
            logger.error(f"Knowledge base not found: {self.knowledge_base_path}")
            raise FileNotFoundError(
                f"Knowledge base not found: {self.knowledge_base_path}"
            )

        # Carregar JSON
        with open(self.knowledge_base_path) as f:
            self.raw_data = json.load(f)

        logger.info(
            f"Loaded knowledge base: {self.raw_data['meta']['total_decisions']} decisions"
        )

        # Converter decisões para documentos
        self.documents = []
        for decision in self.raw_data.get("decisions", []):
            doc = self._decision_to_document(decision)
            self.documents.append(doc)

        logger.info(f"Processed {len(self.documents)} ADR documents")
        return self.documents

    def _decision_to_document(self, decision: dict[str, Any]) -> ADRDocument:
        """
        Converter decisão JSON para ADRDocument

        Concatena campos relevantes para criar texto completo para embedding.
        """
        # Extrair campos principais
        doc_id = decision.get("id", "UNKNOWN")
        title = decision.get("title", "")
        status = decision.get("status", "unknown")
        summary = decision.get("summary", "")

        # Montar texto completo para embedding
        # Incluir: título, summary, knowledge.what, knowledge.why
        text_parts = [
            f"ADR ID: {doc_id}",
            f"Title: {title}",
            f"Status: {status}",
            f"Summary: {summary}",
        ]

        # Adicionar knowledge sections
        knowledge = decision.get("knowledge", {})
        if "what" in knowledge:
            text_parts.append(f"What: {knowledge['what']}")

        if "why" in knowledge:
            text_parts.append(f"Why: {knowledge['why']}")

        # Adicionar implications positivas
        implications = knowledge.get("implications", {})
        if "positive" in implications:
            positive = implications["positive"]
            text_parts.append(f"Positive Implications: {', '.join(positive)}")

        # Adicionar keywords
        keywords = decision.get("keywords", [])
        if keywords:
            text_parts.append(f"Keywords: {', '.join(keywords)}")

        # Concatenar tudo
        full_text = "\n\n".join(text_parts)

        # Metadata completo
        metadata = {
            "id": doc_id,
            "title": title,
            "status": status,
            "scope": decision.get("scope", {}),
            "keywords": keywords,
            "concepts": decision.get("concepts", []),
            "questions": decision.get("questions", []),
        }

        return ADRDocument(
            id=doc_id,
            title=title,
            status=status,
            summary=summary,
            text=full_text,
            metadata=metadata,
        )

    def get_by_id(self, adr_id: str) -> ADRDocument | None:
        """Buscar ADR por ID"""
        for doc in self.documents:
            if doc.id == adr_id:
                return doc
        return None

    def get_by_status(self, status: str) -> list[ADRDocument]:
        """Buscar ADRs por status (accepted, proposed, etc)"""
        return [doc for doc in self.documents if doc.status == status]

    def get_stats(self) -> dict[str, Any]:
        """Estatísticas do knowledge base"""
        return {
            "total_decisions": len(self.documents),
            "by_status": self._count_by_status(),
            "total_keywords": sum(
                len(doc.metadata["keywords"]) for doc in self.documents
            ),
            "knowledge_base_path": str(self.knowledge_base_path),
        }

    def _count_by_status(self) -> dict[str, int]:
        """Contar ADRs por status"""
        counts: dict[str, int] = {}
        for doc in self.documents:
            counts[doc.status] = counts.get(doc.status, 0) + 1
        return counts


if __name__ == "__main__":
    # Test loading
    logging.basicConfig(level=logging.INFO)

    kb_path = "/home/kernelcore/arch/adr-ledger/knowledge/knowledge_base.json"
    loader = ADRKnowledgeLoader(kb_path)

    try:
        docs = loader.load()
        print(f"\n📚 Loaded {len(docs)} ADR documents")
        print("\nFirst document:")
        print(f"  {docs[0]}")
        print(f"  Text length: {len(docs[0].text)} chars")

        print("\nStats:")
        stats = loader.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

    except Exception as e:
        print(f"❌ Error: {e}")
