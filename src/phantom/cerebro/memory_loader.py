#!/usr/bin/env python3
"""
CEREBRO - Memory Loader

Carrega memory entries (transitions, integrations, learnings) do adr-ledger
e prepara documentos para indexação no FAISS, paralelo ao ADRKnowledgeLoader.

Ver ADR-0019 para schema do frontmatter e regra de uso.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("cerebro.memory_loader")

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


@dataclass
class MemoryDocument:
    """Representação de uma memory entry para RAG."""

    id: str
    type: str  # transition | integration | learning
    title: str
    date: str  # ISO 8601
    repos_affected: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    supersedes_adrs: list[str] = field(default_factory=list)
    related_adrs: list[str] = field(default_factory=list)
    related_memories: list[str] = field(default_factory=list)
    body: str = ""
    text: str = ""  # title + body, prepared for embedding
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[memory:{self.type}] {self.id} ({self.date})"


class MemoryKnowledgeLoader:
    """Carrega e processa memory entries do adr-ledger memory layer."""

    def __init__(self, memory_dir: str | Path):
        self.memory_dir = Path(memory_dir)
        self.documents: list[MemoryDocument] = []

    def load(self) -> list[MemoryDocument]:
        """Varre memory_dir/* (recursivo), parseia frontmatter + body."""
        if not self.memory_dir.exists():
            logger.warning("Memory dir not found: %s", self.memory_dir)
            return []

        self.documents = []
        for md_path in sorted(self.memory_dir.rglob("*.md")):
            if md_path.name == "INDEX.md":
                continue
            try:
                doc = self._file_to_document(md_path)
                if doc is not None:
                    self.documents.append(doc)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to parse %s: %s", md_path, exc)

        logger.info("Loaded %d memory documents from %s", len(self.documents), self.memory_dir)
        return self.documents

    def _file_to_document(self, path: Path) -> MemoryDocument | None:
        raw = path.read_text(encoding="utf-8")
        match = _FRONTMATTER_RE.match(raw)
        if match is None:
            logger.warning("No frontmatter in %s; skipping", path)
            return None

        fm = yaml.safe_load(match.group(1)) or {}
        body = match.group(2).strip()

        doc_id = fm.get("id") or path.stem
        title = fm.get("title", doc_id)
        text = "\n\n".join(
            [
                f"Memory ID: {doc_id}",
                f"Type: {fm.get('type', 'unknown')}",
                f"Title: {title}",
                f"Date: {fm.get('date', '')}",
                f"Repos: {', '.join(fm.get('repos_affected', []))}",
                f"Tags: {', '.join(fm.get('tags', []))}",
                body,
            ]
        )

        return MemoryDocument(
            id=doc_id,
            type=fm.get("type", "unknown"),
            title=title,
            date=str(fm.get("date", "")),
            repos_affected=list(fm.get("repos_affected", [])),
            tags=list(fm.get("tags", [])),
            supersedes_adrs=list(fm.get("supersedes_adrs", [])),
            related_adrs=list(fm.get("related_adrs", [])),
            related_memories=list(fm.get("related_memories", [])),
            body=body,
            text=text,
            metadata=fm,
        )

    def get_by_id(self, memory_id: str) -> MemoryDocument | None:
        for doc in self.documents:
            if doc.id == memory_id:
                return doc
        return None

    def get_by_type(self, type_: str) -> list[MemoryDocument]:
        return [doc for doc in self.documents if doc.type == type_]

    def get_by_repo(self, repo: str) -> list[MemoryDocument]:
        return [doc for doc in self.documents if repo in doc.repos_affected]

    def get_recent(self, since: str) -> list[MemoryDocument]:
        """since: ISO date string (YYYY-MM-DD). Returns docs with date >= since."""
        try:
            threshold = datetime.fromisoformat(since)
        except ValueError:
            logger.warning("Invalid 'since' date: %s", since)
            return []
        recent = []
        for doc in self.documents:
            try:
                doc_date = datetime.fromisoformat(doc.date)
            except (ValueError, TypeError):
                continue
            if doc_date >= threshold:
                recent.append(doc)
        return sorted(recent, key=lambda d: d.date, reverse=True)

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_memories": len(self.documents),
            "by_type": self._count_by("type"),
            "by_repo": self._count_by_repo(),
            "memory_dir": str(self.memory_dir),
        }

    def _count_by(self, attr: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for doc in self.documents:
            key = getattr(doc, attr)
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _count_by_repo(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for doc in self.documents:
            for repo in doc.repos_affected:
                counts[repo] = counts.get(repo, 0) + 1
        return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loader = MemoryKnowledgeLoader("docs/architecture/adr/memory")
    docs = loader.load()
    print(f"\nLoaded {len(docs)} memory documents")
    for doc in docs:
        print(f"  {doc}")
    print("\nStats:")
    for key, value in loader.get_stats().items():
        print(f"  {key}: {value}")
