"""
CEREBRO - RAG Knowledge System para ADRs

Sistema de Retrieval-Augmented Generation especializado em decisões arquiteturais.
Carrega knowledge_base.json do ADR-Ledger e provê busca semântica.
"""

from phantom.cerebro.knowledge_loader import ADRKnowledgeLoader
from phantom.cerebro.rag_engine import CerebroRAG

__all__ = [
    "ADRKnowledgeLoader",
    "CerebroRAG",
]
