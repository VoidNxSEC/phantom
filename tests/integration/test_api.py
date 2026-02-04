"""
Integration tests for Phantom REST API.

Uses FastAPI TestClient — no real server is started.
"""

import pytest
from fastapi.testclient import TestClient

from phantom.api.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_payload_shape(self, client):
        body = client.get("/health").json()
        assert "status" in body
        assert "version" in body
        assert body["status"] == "operational"

    def test_health_version_is_string(self, client):
        assert isinstance(client.get("/health").json()["version"], str)


class TestReadyEndpoint:
    def test_ready_returns_200(self, client):
        resp = client.get("/ready")
        assert resp.status_code == 200

    def test_ready_has_status_and_checks(self, client):
        body = client.get("/ready").json()
        assert "status" in body
        assert "checks" in body
        assert body["status"] in ("ready", "not_ready")


class TestMetricsEndpoint:
    def test_metrics_returns_200(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_metrics_content_type_is_prometheus(self, client):
        resp = client.get("/metrics")
        assert "text/plain" in resp.headers["content-type"]

    def test_metrics_tracks_requests(self, client):
        # Hit health first to generate a metric
        client.get("/health")
        body = client.get("/metrics").text
        assert "phantom_requests_total" in body
        assert "phantom_request_latency_seconds" in body


class TestExtractEndpoint:
    def test_extract_returns_200(self, client, sample_markdown):
        resp = client.post("/extract", json={
            "content": sample_markdown,
            "filename": "test.md",
        })
        assert resp.status_code == 200

    def test_extract_response_has_insights(self, client, sample_markdown):
        body = client.post("/extract", json={
            "content": sample_markdown,
        }).json()
        assert "insights" in body
        assert "processing_time_seconds" in body
        assert body["processing_time_seconds"] >= 0

    def test_extract_filename_defaults(self, client):
        body = client.post("/extract", json={"content": "# Hello"}).json()
        assert body["filename"] == "input.md"

    def test_extract_filename_custom(self, client):
        body = client.post("/extract", json={
            "content": "# Hi",
            "filename": "custom.md",
        }).json()
        assert body["filename"] == "custom.md"

    def test_extract_empty_content(self, client):
        resp = client.post("/extract", json={"content": ""})
        # Should still return 200 — empty input is valid
        assert resp.status_code == 200


class TestUploadEndpoint:
    def test_upload_returns_filename(self, client):
        resp = client.post(
            "/upload",
            files={"file": ("report.md", b"# Hello", "text/markdown")},
        )
        assert resp.status_code == 200
        assert resp.json()["filename"] == "report.md"

    def test_upload_reports_size(self, client):
        content = b"x" * 1024
        body = client.post(
            "/upload",
            files={"file": ("data.bin", content, "application/octet-stream")},
        ).json()
        assert body["size"] == 1024

    def test_upload_no_filename_returns_error(self, client):
        # Sending a file without a name — FastAPI may reject before handler (422)
        # or handler raises 400; both are valid client-error rejections.
        resp = client.post(
            "/upload",
            files={"file": ("", b"data", "text/plain")},
        )
        assert resp.status_code in (400, 422)


class TestRAGQueryEndpoint:
    def test_rag_query_returns_200(self, client):
        resp = client.get("/rag/query?question=What+is+Phantom?")
        assert resp.status_code == 200

    def test_rag_query_echoes_question(self, client):
        body = client.get("/rag/query?question=test+question").json()
        assert body["question"] == "test question"

    def test_rag_query_returns_sources_list(self, client):
        body = client.get("/rag/query?question=hello").json()
        assert isinstance(body["sources"], list)
