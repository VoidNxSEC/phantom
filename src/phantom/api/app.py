"""
Phantom API - FastAPI REST endpoints.
"""


from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str


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

    app = FastAPI(
        title="Phantom API",
        description="AI-Powered Document Intelligence & Classification Pipeline",
        version=__version__,
    )

    @app.get("/health", response_model=HealthResponse)
    async def health():
        """Health check endpoint."""
        return HealthResponse(
            status="operational",
            version=__version__,
        )

    @app.post("/extract", response_model=ExtractResponse)
    async def extract(request: ExtractRequest):
        """Extract insights from markdown content."""
        import time
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

    return app


# For uvicorn direct import
app = create_app()


def serve():
    """Entry point for phantom-api script."""
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    serve()
