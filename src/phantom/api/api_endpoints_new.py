"""
CORTEX API - Additional Endpoints

Add these endpoints to cortex_api.py before the STARTUP/SHUTDOWN section
"""

# ═══════════════════════════════════════════════════════════════
# FILE UPLOAD & PROCESSING
# ═══════════════════════════════════════════════════════════════

@app.post("/api/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload and process multiple files
    
    Supports: PDF, MD, TXT, DOCX
    Returns processing IDs for tracking
    """
    import uuid

    results = []

    for file in files:
        # Validate file type
        ext = Path(file.filename).suffix.lower()
        if ext not in ['.pdf', '.md', '.txt', '.docx']:
            results.append({
                "filename": file.filename,
                "status": "rejected",
                "reason": f"Unsupported file type: {ext}"
            })
            continue

        # Generate processing ID
        proc_id = str(uuid.uuid4())[:8]

        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)

        # Add to processing queue
        _processing_queue[proc_id] = {
            "filename": file.filename,
            "path": str(tmp_path),
            "status": "queued",
            "progress": 0,
            "started_at": datetime.now().isoformat()
        }

        results.append({
            "filename": file.filename,
            "processing_id": proc_id,
            "status": "queued"
        })

    return {
        "uploaded": len([r for r in results if r["status"] == "queued"]),
        "rejected": len([r for r in results if r["status"] == "rejected"]),
        "files": results
    }


@app.get("/api/upload/{processing_id}")
async def get_processing_status(processing_id: str):
    """Get file processing status"""
    if processing_id not in _processing_queue:
        raise HTTPException(status_code=404, detail="Processing ID not found")

    return _processing_queue[processing_id]


# ═══════════════════════════════════════════════════════════════
# MODEL MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@app.get("/api/models")
async def list_models():
    """List available LLM models"""
    return get_available_models()


@app.post("/api/config/keys")
async def set_api_keys(keys: Dict[str, str]):
    """
    Set API keys for cloud providers
    
    Example:
    {
        "openai": "sk-...",
        "anthropic": "sk-ant-..."
    }
    """
    global _provider_keys

    for provider, key in keys.items():
        if provider in _provider_keys:
            _provider_keys[provider] = key

    return {
        "updated": list(keys.keys()),
        "status": "success"
    }


# ═══════════════════════════════════════════════════════════════
# PROMPT WORKBENCH
# ═══════════════════════════════════════════════════════════════

class PromptTestRequest(BaseModel):
    """Prompt test request"""
    template: str
    variables: Dict[str, Any]
    expected_keywords: Optional[List[str]] = None
    max_tokens: int = 2048


@app.post("/api/prompt/test")
async def test_prompt(request: PromptTestRequest):
    """
    Test prompt template
    
    Returns rendered prompt, token count, and validation
    """
    result = _workbench.render_template(
        request.template,
        request.variables
    )

    return result


@app.get("/api/prompt/tests")
async def list_prompt_tests():
    """List saved prompt tests"""
    return {
        "count": len(_workbench.tests),
        "tests": [
            {
                "name": t.name,
                "max_tokens": t.max_tokens
            }
            for t in _workbench.tests
        ]
    }


# ═══════════════════════════════════════════════════════════════
# METRICS & MONITORING
# ═══════════════════════════════════════════════════════════════

@app.get("/api/metrics")
async def get_metrics():
    """Get latency and performance metrics"""
    return {
        "cache": _query_cache.stats(),
        "latency": _metrics.get_stats(),
        "queue_size": len(_processing_queue)
    }


@app.post("/api/cache/clear")
async def clear_cache():
    """Clear query cache"""
    _query_cache.clear()
    return {"status": "cleared"}
