#!/usr/bin/env python3
"""
CORTEX API - FastAPI Backend for Cortex Desktop
Exposes Cortex and Spectre engines via HTTP endpoints.
"""

import logging
import os
import shutil
import sys
import tempfile
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import Core Engines
try:
    from phantom.analysis.spectre import DocumentAnalysis, SpectreAnalyzer
    from phantom.core.cortex import CortexProcessor as MarkdownProcessor
    from phantom.core.cortex import DocumentInsights as MarkdownInsights
except ImportError as e:
    print(f"CRITICAL: Failed to import core engines: {e}")
    sys.exit(1)

# Configuration
TEMP_DIR = Path(".phantom/staging")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cortex_api")

# App Definition
app = FastAPI(
    title="Cortex API",
    description="Backend API for Cortex Desktop (Tauri integration)",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════


class ProcessResponse(BaseModel):
    filename: str
    insights: dict[str, Any]
    processing_time: float


class AnalyzeResponse(BaseModel):
    filename: str
    sentiment: dict[str, Any]
    entities: list[dict[str, Any]]
    topics: list[dict[str, Any]]


# ═══════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════


def save_upload_file(upload_file: UploadFile) -> Path:
    try:
        filename = upload_file.filename or "upload"
        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix, dir=TEMP_DIR
        ) as tmp:
            shutil.copyfileobj(upload_file.file, tmp)
            tmp_path = Path(tmp.name)
        return tmp_path
    finally:
        upload_file.file.close()


def cleanup_file(path: Path) -> None:
    if path.exists():
        try:
            os.remove(path)
        except Exception as e:
            logger.error(f"Failed to delete temp file {path}: {e}")


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════


@app.get("/health")
async def health_check():
    return {
        "status": "operational",
        "version": "1.0.0",
        "engines": {"cortex": "loaded", "spectre": "loaded"},
    }


@app.post("/process", response_model=ProcessResponse)
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_strategy: str | None = Query(
        None, description="Chunking strategy: recursive, sliding, simple"
    ),
    chunk_size: int = 1024,
):
    """
    Process a document using CORTEX (LLM Extraction).
    """
    logger.info(f"Processing upload: {file.filename}")

    tmp_path = save_upload_file(file)
    background_tasks.add_task(cleanup_file, tmp_path)

    try:
        # Initialize Processor
        # Note: In a real app, we might want to reuse the processor or use a queue
        # For now, we instantiate per request but point to a dummy output file
        dummy_output = TEMP_DIR / f"{uuid.uuid4()}.jsonl"

        processor = MarkdownProcessor(
            input_dir=str(
                TEMP_DIR
            ),  # Dummy, not used for single file logic refactor might be needed
            output_file=str(dummy_output),
            chunking_strategy=chunk_strategy,
            chunk_size=chunk_size,
            verbose=False,
        )

        # We need to hack/refactor MarkdownProcessor slightly or use internal method
        # The current CORTEX implementation scans a directory.
        # Let's call the internal method directly.

        insights = processor.process_single_file(tmp_path)

        if not insights:
            raise HTTPException(status_code=500, detail="Failed to extract insights")

        # Clean up the dummy output if created
        if dummy_output.exists():
            os.remove(dummy_output)

        return ProcessResponse(
            filename=file.filename,
            insights=insights.dict(),
            processing_time=insights.processing_time_seconds,
        )

    except Exception as e:
        logger.error(f"Error processing {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_document(
    background_tasks: BackgroundTasks, file: UploadFile = File(...)
):
    """
    Analyze a document using SPECTRE (Sentiment & Entities).
    """
    logger.info(f"Analyzing upload: {file.filename}")

    tmp_path = save_upload_file(file)
    background_tasks.add_task(cleanup_file, tmp_path)

    try:
        analyzer = SpectreAnalyzer()
        analysis = analyzer.analyze_document(tmp_path)

        if not analysis:
            raise HTTPException(status_code=500, detail="Analysis failed")

        return AnalyzeResponse(
            filename=file.filename,
            sentiment=analysis.sentiment.to_dict() if analysis.sentiment else {},
            entities=[asdict(e) for e in analysis.entities],
            topics=[asdict(t) for t in analysis.topics],
        )

    except Exception as e:
        logger.error(f"Error analyzing {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# JUDGE ENDPOINT (AI-OS-Agent Integration)
# ═══════════════════════════════════════════════════════════════

from phantom.api.judge_api import (
    PhantomGateBundle,
    PhantomGateResponse,
    get_judgment_engine,
)


@app.post("/judge", response_model=PhantomGateResponse)
async def judge_bundle(bundle: PhantomGateBundle):
    """
    Julgar bundle de métricas do AI-OS-Agent

    Recebe:
    - Métricas do sistema (CPU, RAM, thermal, disk, network)
    - Alertas detectados
    - Logs recentes (journald)

    Retorna:
    - Severidade geral (info/warning/critical)
    - Insights sobre o estado do sistema
    - ADRs relevantes consultadas
    - Recomendações de ações
    """
    logger.info(
        f"Received bundle from {bundle.hostname}: "
        f"{len(bundle.alerts)} alerts, {len(bundle.logs)} logs"
    )

    try:
        engine = get_judgment_engine()
        result = engine.judge(bundle)

        logger.info(
            f"Judgment complete: severity={result.severity}, "
            f"insights={len(result.insights)}, "
            f"adrs={len(result.relevant_adrs)}"
        )

        return result

    except Exception as e:
        logger.error(f"Error judging bundle: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════
# LLM / CHAT ENDPOINTS
# ═══════════════════════════════════════════════════════════════

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: str
    history: list[ChatMessage] = []
    context_size: int = 5
    llm_provider: str = "tensor_forge"

class ChatResponse(BaseModel):
    message: dict[str, Any]
    conversation_id: str

@app.get("/api/models")
async def list_models():
    """List available mock models for UI options."""
    return {
        "tensor_forge": [
            {"id": "local-llamacpp", "name": "Local LLaMA 3 8B"},
            {"id": "qwen3-vl-8b", "name": "Qwen 3 VL"}
        ],
        "openai": [
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
        ],
        "anthropic": [
            {"id": "claude-3-opus", "name": "Claude 3 Opus"},
            {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet"},
        ]
    }

@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(request: ChatRequest):
    import requests
    
    # Base configuration
    provider = request.llm_provider
    
    # Flatten history
    messages = []
    for msg in request.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    content = ""
    try:
        if provider == "tensor_forge" or provider == "local":
            # Assume Llama.cpp / Tensor Forge running on 8081 with OpenAI-compatible schema
            payload = {
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024
            }
            res = requests.post("http://localhost:8081/v1/chat/completions", json=payload, timeout=60)
            if res.ok:
                content = res.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                # Fallback to direct completion API if /v1/chat/completions doesn't exist
                prompt = ""
                for m in messages:
                    prompt += f"{m['role'].capitalize()}: {m['content']}\n"
                prompt += "Assistant: "
                
                res = requests.post("http://localhost:8081/completion", json={"prompt": prompt, "n_predict": 1024}, timeout=60)
                if res.ok:
                    content = res.json().get("content", "")
                else:
                    raise Exception(f"Tensor Forge API Error: {res.text}")

        elif provider == "openai":
            import os
            headers = {"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', '')}"}
            payload = {"model": "gpt-4o", "messages": messages}
            res = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=60)
            if res.ok:
                content = res.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                 raise Exception(f"OpenAI API Error: {res.text}")

        elif provider == "anthropic":
            import os
            headers = {
                "x-api-key": os.environ.get("ANTHROPIC_API_KEY", ""),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            # Anthropic schema differs slightly
            system_msg = "; ".join([m["content"] for m in messages if m["role"] == "system"])
            anthropic_msgs = [m for m in messages if m["role"] != "system"]
            payload = {
                "model": "claude-3-opus-20240229",
                "max_tokens": 1024,
                "messages": anthropic_msgs
            }
            if system_msg:
                payload["system"] = system_msg
                
            res = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=60)
            if res.ok:
                content = res.json().get("content", [{}])[0].get("text", "")
            else:
                 raise Exception(f"Anthropic API Error: {res.text}")
        else:
            raise Exception(f"Unknown provider: {provider}")

    except Exception as e:
        logger.error(f"Chat generation failed: {e}")
        content = f"Error generating text: {str(e)}"

    return ChatResponse(
        message={"content": content, "sources": []},
        conversation_id=request.conversation_id
    )

if __name__ == "__main__":
    import uuid

    import uvicorn

    # Dev server
    uvicorn.run(app, host="0.0.0.0", port=8087)
