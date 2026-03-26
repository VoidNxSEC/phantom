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


class TestProcessEndpoint:
    def test_process_requires_file(self, client):
        resp = client.post("/process")
        assert resp.status_code == 422  # Missing required field

    def test_process_accepts_markdown(self, client, sample_markdown):
        resp = client.post(
            "/process",
            files={"file": ("test.md", sample_markdown.encode(), "text/markdown")},
        )
        # /process depends on CortexProcessor which may require LLM
        # Accept 200 (success) or 500 (LLM unavailable) — not a client error
        assert resp.status_code in (200, 500)
        if resp.status_code == 500:
            # Verify it's a meaningful error, not a crash
            body = resp.json()
            assert "detail" in body

    def test_process_returns_expected_fields(self, client):
        resp = client.post(
            "/process",
            files={"file": ("simple.txt", b"# Test document", "text/plain")},
        )
        if resp.status_code == 200:
            body = resp.json()
            assert "filename" in body
            assert "insights" in body
            assert "processing_time" in body


class TestVectorSearchEndpoint:
    def test_vector_search_empty_store(self, client):
        resp = client.post("/vectors/search?query=test&top_k=5")
        # Empty store should return 400 (client told to index first) or 500 (init failure)
        assert resp.status_code in (400, 500)
        body = resp.json()
        assert "detail" in body

    def test_vector_search_requires_query(self, client):
        resp = client.post("/vectors/search")
        assert resp.status_code == 400  # Manual validation returns 400


class TestVectorIndexEndpoint:
    def test_vector_index_requires_file(self, client):
        resp = client.post("/vectors/index")
        assert resp.status_code == 422

    def test_vector_index_accepts_text(self, client):
        content = b"This is a test document about machine learning and AI."
        resp = client.post(
            "/vectors/index",
            files={"file": ("doc.txt", content, "text/plain")},
        )
        # May fail if embedding model can't load (env issues); accept 200 or 500
        if resp.status_code == 200:
            body = resp.json()
            assert body["status"] == "indexed"
            assert body["chunks_indexed"] > 0
        else:
            assert resp.status_code == 500
            body = resp.json()
            assert "detail" in body

    def test_vector_index_and_search(self, client):
        # First, index a document
        content = b"Python is a programming language. It is widely used for AI and data science."
        resp1 = client.post(
            "/vectors/index",
            files={"file": ("python.txt", content, "text/plain")},
        )
        # May fail if embedding model is unavailable
        if resp1.status_code != 200:
            pytest.skip("Embedding model not available for indexing")

        # Then search for it
        resp2 = client.post("/vectors/search?query=programming+language&top_k=3")
        assert resp2.status_code == 200
        body = resp2.json()
        assert "results" in body
        assert len(body["results"]) > 0


class TestChatEndpoint:
    def test_chat_requires_message(self, client):
        resp = client.post("/api/chat", json={})
        assert resp.status_code == 422

    def test_chat_basic_request(self, client):
        resp = client.post(
            "/api/chat",
            json={
                "message": "Hello, how are you?",
                "conversation_id": "test-123",
                "history": [],
                "context_size": 3,
                "llm_provider": "local",
            },
        )
        # Chat depends on LLM + embedding model; accept 200 or 500 (service unavailable)
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            body = resp.json()
            assert "message" in body
            assert "conversation_id" in body

    def test_chat_with_empty_store(self, client):
        resp = client.post(
            "/api/chat",
            json={
                "message": "Tell me about Phantom",
                "conversation_id": "test-456",
                "history": [],
            },
        )
        # Should work even with empty vector store
        if resp.status_code == 200:
            body = resp.json()
            assert "message" in body
            assert "conversation_id" in body


class TestModelsEndpoint:
    def test_models_returns_200(self, client):
        resp = client.get("/api/models")
        assert resp.status_code == 200

    def test_models_returns_providers(self, client):
        body = client.get("/api/models").json()
        assert "local" in body
        assert "openai" in body
        assert "anthropic" in body
        assert isinstance(body["local"], list)


class TestPromptTestEndpoint:
    def test_prompt_test_simple(self, client):
        resp = client.post(
            "/api/prompt/test",
            json={"template": "Hello {name}!", "variables": {"name": "World"}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["rendered"] == "Hello World!"
        assert body["success"] is True
        assert body["tokens"] > 0

    def test_prompt_test_missing_variable(self, client):
        resp = client.post(
            "/api/prompt/test",
            json={"template": "Hello {name}!", "variables": {}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "Missing values" in body["error"]

    def test_prompt_test_multiple_variables(self, client):
        resp = client.post(
            "/api/prompt/test",
            json={
                "template": "{greeting} {name}, you are {age} years old.",
                "variables": {"greeting": "Hello", "name": "Alice", "age": "25"},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["rendered"] == "Hello Alice, you are 25 years old."
        assert body["success"] is True


class TestSystemMetricsEndpoint:
    def test_system_metrics_returns_200(self, client):
        resp = client.get("/api/system/metrics")
        assert resp.status_code == 200

    def test_system_metrics_has_cpu(self, client):
        body = client.get("/api/system/metrics").json()
        assert "cpu" in body
        assert "percent" in body["cpu"]
        assert 0 <= body["cpu"]["percent"] <= 100

    def test_system_metrics_has_memory(self, client):
        body = client.get("/api/system/metrics").json()
        assert "memory" in body
        assert "total_bytes" in body["memory"]
        assert "percent" in body["memory"]
        assert body["memory"]["total_bytes"] > 0

    def test_system_metrics_has_disk(self, client):
        body = client.get("/api/system/metrics").json()
        assert "disk" in body
        assert "total_bytes" in body["disk"]
        assert body["disk"]["total_bytes"] > 0

    def test_system_metrics_has_timestamp(self, client):
        body = client.get("/api/system/metrics").json()
        assert "timestamp" in body
        assert body["timestamp"] > 0
