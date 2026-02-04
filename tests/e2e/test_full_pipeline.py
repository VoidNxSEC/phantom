"""
End-to-end pipeline smoke tests.

These tests verify the full request→response path using realistic payloads.
They do NOT require external services (no LLM, no DB).
"""

import pytest
from fastapi.testclient import TestClient

from phantom.api.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.mark.e2e
class TestDocumentProcessingFlow:
    """Simulate a document arriving, being extracted, and returned."""

    REALISTIC_DOC = """
    # Architecture Decision: Switching to PostgreSQL

    ## Context
    Our current SQLite-based storage does not scale horizontally.
    The team has evaluated MySQL, PostgreSQL, and CockroachDB.

    ## Decision
    We will migrate to PostgreSQL 16 with pgvector for embedding storage.

    ## Consequences
    - Connection pooling via PgBouncer is required
    - Migrations managed by Alembic
    - pgvector enables native vector similarity search
    """

    def test_upload_then_extract(self, client):
        # Step 1: upload
        upload_resp = client.post(
            "/upload",
            files={"file": ("decision.md", self.REALISTIC_DOC.encode(), "text/markdown")},
        )
        assert upload_resp.status_code == 200
        assert upload_resp.json()["size"] > 0

        # Step 2: extract insights from same content
        extract_resp = client.post("/extract", json={
            "content": self.REALISTIC_DOC,
            "filename": "decision.md",
        })
        assert extract_resp.status_code == 200
        body = extract_resp.json()
        assert body["filename"] == "decision.md"
        assert "insights" in body

    def test_health_before_and_after(self, client):
        """Health endpoint must stay green throughout a flow."""
        assert client.get("/health").status_code == 200

        client.post("/extract", json={"content": "# test"})

        assert client.get("/health").status_code == 200
