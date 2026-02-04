"""
Phantom API - FastAPI REST endpoints.
"""

import time

from fastapi import FastAPI, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from phantom.logging import configure_logging, get_logger

# ── Prometheus metrics ──────────────────────────────────────────────

REQUEST_COUNT = Counter(
    "phantom_requests_total",
    "Total number of HTTP requests",
    labelnames=["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "phantom_request_latency_seconds",
    "HTTP request latency in seconds",
    labelnames=["endpoint"],
)

logger = get_logger("api")


class HealthResponse(BaseModel):
    status: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    checks: dict


class ExtractRequest(BaseModel):
    content: str
    filename: str | None = "input.md"


class ExtractResponse(BaseModel):
    filename: str
    insights: dict
    processing_time_seconds: float


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    from phantom import __version__

    configure_logging()

    app = FastAPI(
        title="Phantom API",
        description="AI-Powered Document Intelligence & Classification Pipeline",
        version=__version__,
    )

    # ── Middleware: instrument every request ────────────────────────

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(response.status_code),
        ).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

        return response

    # ── Health & readiness ──────────────────────────────────────────

    @app.get("/health", response_model=HealthResponse)
    async def health():
        """Liveness probe — always 200 if the process is running."""
        return HealthResponse(status="operational", version=__version__)

    @app.get("/ready", response_model=ReadyResponse)
    async def ready():
        """Readiness probe — checks downstream dependencies."""
        checks: dict = {}

        # Vector store availability (lazy: only checked if previously initialised)
        try:
            from phantom.rag.vectors import FAISSVectorStore  # noqa: F811

            checks["vector_store"] = True
        except Exception:
            checks["vector_store"] = False

        all_ok = all(checks.values()) if checks else True
        return ReadyResponse(
            status="ready" if all_ok else "not_ready",
            checks=checks,
        )

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post("/extract", response_model=ExtractResponse)
    async def extract(request: ExtractRequest):
        """Extract insights from markdown content."""
        start = time.time()

        # TODO: Implement using CortexProcessor
        insights = {
            "themes": [],
            "patterns": [],
            "learnings": [],
            "concepts": [],
            "recommendations": [],
        }

        return ExtractResponse(
            filename=request.filename or "input.md",
            insights=insights,
            processing_time_seconds=time.time() - start,
        )

    @app.post("/upload")
    async def upload_file(file: UploadFile):
        """Upload and process a file."""
        if not file.filename:
            raise HTTPException(400, "Filename required")

        content = await file.read()

        # TODO: Process file
        return {
            "filename": file.filename,
            "size": len(content),
            "status": "uploaded",
        }

    @app.post("/rag/query")
    async def rag_query(question: str, collection: str = "default", top_k: int = 5):
        """Query the RAG pipeline."""
        # TODO: Implement RAG query
        return {
            "question": question,
            "answer": "RAG pipeline not yet implemented",
            "sources": [],
        }

    # Integration with AI-Agent-OS
    from phantom.api.judge_api import (
        PhantomGateBundle,
        PhantomGateResponse,
        get_judgment_engine,
    )

    @app.post("/judge", response_model=PhantomGateResponse)
    async def judge_bundle(bundle: PhantomGateBundle):
        """
        Judge system metrics bundle from AI-OS-Agent.
        Analyzes metrics, logs, and alerts to provide insights and recommendations.
        """
        try:
            engine = get_judgment_engine()
            return engine.judge(bundle)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


# For uvicorn direct import
app = create_app()


def serve():
    """Entry point for phantom-api script."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    serve()
