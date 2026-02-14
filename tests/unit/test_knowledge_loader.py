"""
Unit tests for CEREBRO Knowledge Loader module.

Tests: ADRDocument, ADRKnowledgeLoader loading, querying, and stats.
"""

import json

import pytest

from phantom.cerebro.knowledge_loader import ADRDocument, ADRKnowledgeLoader

pytestmark = pytest.mark.unit


SAMPLE_KNOWLEDGE_BASE = {
    "meta": {"total_decisions": 3, "version": "1.0"},
    "decisions": [
        {
            "id": "ADR-0001",
            "title": "Use NixOS for Reproducibility",
            "status": "accepted",
            "summary": "Adopt NixOS for reproducible builds.",
            "knowledge": {
                "what": "NixOS provides reproducible environments.",
                "why": "Eliminates works-on-my-machine problems.",
                "implications": {
                    "positive": ["Reproducibility", "Consistency"],
                },
            },
            "keywords": ["nixos", "reproducibility", "devops"],
            "concepts": ["infrastructure"],
            "questions": ["How to adopt Nix?"],
        },
        {
            "id": "ADR-0002",
            "title": "FAISS for Vector Search",
            "status": "accepted",
            "summary": "Use FAISS for semantic search.",
            "knowledge": {
                "what": "FAISS is a vector similarity library.",
                "why": "Fast approximate nearest-neighbor search.",
            },
            "keywords": ["faiss", "vectors", "search"],
            "concepts": ["ml"],
            "questions": [],
        },
        {
            "id": "ADR-0003",
            "title": "Evaluate Redis Cache",
            "status": "proposed",
            "summary": "Consider Redis for caching.",
            "knowledge": {},
            "keywords": ["redis", "cache"],
            "concepts": [],
            "questions": [],
        },
    ],
}


class TestADRDocument:
    """Test ADRDocument dataclass."""

    def test_construction(self):
        doc = ADRDocument(
            id="ADR-0001",
            title="Test",
            status="accepted",
            summary="A test",
            text="Full text here",
            metadata={"keywords": ["test"]},
        )
        assert doc.id == "ADR-0001"
        assert doc.title == "Test"
        assert doc.status == "accepted"

    def test_str_representation(self):
        doc = ADRDocument(
            id="ADR-0001",
            title="Test ADR",
            status="accepted",
            summary="",
            text="",
            metadata={},
        )
        result = str(doc)
        assert "ADR-0001" in result
        assert "Test ADR" in result
        assert "accepted" in result


class TestADRKnowledgeLoader:
    """Test ADRKnowledgeLoader class."""

    @pytest.fixture
    def kb_file(self, tmp_path):
        """Create a temporary knowledge base JSON file."""
        kb_path = tmp_path / "knowledge_base.json"
        kb_path.write_text(json.dumps(SAMPLE_KNOWLEDGE_BASE))
        return kb_path

    def test_load_success(self, kb_file):
        loader = ADRKnowledgeLoader(str(kb_file))
        docs = loader.load()
        assert len(docs) == 3

    def test_load_file_not_found(self, tmp_path):
        loader = ADRKnowledgeLoader(str(tmp_path / "missing.json"))
        with pytest.raises(FileNotFoundError, match="Knowledge base not found"):
            loader.load()

    def test_load_populates_documents(self, kb_file):
        loader = ADRKnowledgeLoader(str(kb_file))
        loader.load()
        assert len(loader.documents) == 3
        assert loader.documents[0].id == "ADR-0001"
        assert loader.documents[1].id == "ADR-0002"

    def test_decision_to_document_fields(self, kb_file):
        loader = ADRKnowledgeLoader(str(kb_file))
        docs = loader.load()
        doc = docs[0]
        assert doc.id == "ADR-0001"
        assert doc.title == "Use NixOS for Reproducibility"
        assert doc.status == "accepted"
        assert doc.summary == "Adopt NixOS for reproducible builds."

    def test_decision_text_contains_fields(self, kb_file):
        loader = ADRKnowledgeLoader(str(kb_file))
        docs = loader.load()
        text = docs[0].text
        assert "ADR-0001" in text
        assert "NixOS provides reproducible environments" in text
        assert "Reproducibility" in text
        assert "nixos" in text

    def test_decision_text_without_knowledge(self, kb_file):
        loader = ADRKnowledgeLoader(str(kb_file))
        docs = loader.load()
        # ADR-0003 has empty knowledge dict
        text = docs[2].text
        assert "ADR-0003" in text
        assert "redis" in text

    def test_metadata_populated(self, kb_file):
        loader = ADRKnowledgeLoader(str(kb_file))
        docs = loader.load()
        meta = docs[0].metadata
        assert meta["id"] == "ADR-0001"
        assert meta["status"] == "accepted"
        assert "nixos" in meta["keywords"]
        assert "infrastructure" in meta["concepts"]

    def test_get_by_id_found(self, kb_file):
        loader = ADRKnowledgeLoader(str(kb_file))
        loader.load()
        doc = loader.get_by_id("ADR-0002")
        assert doc is not None
        assert doc.title == "FAISS for Vector Search"

    def test_get_by_id_not_found(self, kb_file):
        loader = ADRKnowledgeLoader(str(kb_file))
        loader.load()
        assert loader.get_by_id("ADR-9999") is None

    def test_get_by_status(self, kb_file):
        loader = ADRKnowledgeLoader(str(kb_file))
        loader.load()
        accepted = loader.get_by_status("accepted")
        assert len(accepted) == 2
        proposed = loader.get_by_status("proposed")
        assert len(proposed) == 1
        assert proposed[0].id == "ADR-0003"

    def test_get_by_status_empty(self, kb_file):
        loader = ADRKnowledgeLoader(str(kb_file))
        loader.load()
        assert loader.get_by_status("rejected") == []

    def test_get_stats(self, kb_file):
        loader = ADRKnowledgeLoader(str(kb_file))
        loader.load()
        stats = loader.get_stats()
        assert stats["total_decisions"] == 3
        assert stats["by_status"]["accepted"] == 2
        assert stats["by_status"]["proposed"] == 1
        assert stats["total_keywords"] == 8  # 3 + 3 + 2
        assert str(kb_file) in stats["knowledge_base_path"]

    def test_get_stats_empty(self, tmp_path):
        kb_path = tmp_path / "empty.json"
        kb_path.write_text(json.dumps({"meta": {"total_decisions": 0}, "decisions": []}))
        loader = ADRKnowledgeLoader(str(kb_path))
        loader.load()
        stats = loader.get_stats()
        assert stats["total_decisions"] == 0

    def test_raw_data_stored(self, kb_file):
        loader = ADRKnowledgeLoader(str(kb_file))
        loader.load()
        assert loader.raw_data["meta"]["total_decisions"] == 3
