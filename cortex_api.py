#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORTEX v2.0 - REST API Server

FastAPI server providing REST endpoints for:
- Svelte frontend integration
- RAG system integration (local/cloud)
- Semantic search
- Document processing

Run: uvicorn cortex_api:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
import tempfile
import logging
import asyncio
from datetime import datetime
from functools import lru_cache
import hashlib
import json

# CORTEX modules
from cortex_v2 import CortexV2Pipeline, DocumentInsights
from cortex_embeddings import SearchResult
from prompt_pipeline import PromptPipeline, Source, Message
from latency_optimizer import QueryCache, LatencyMetrics
from prompt_workbench import PromptWorkbench
from cloud_providers import get_available_models

# Cloud providers (optional imports)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

API_VERSION = "2.0.0"
API_TITLE = "CORTEX v2.0 API"
API_DESCRIPTION = """
🔮 CORTEX v2.0 - Intelligent Document Processing API

Features:
- **Semantic Chunking**: Split documents intelligently
- **Embeddings**: Generate vector embeddings
- **Classification**: Extract insights with LLM
- **Semantic Search**: Query processed documents
- **RAG Integration**: Ready for RAG systems
"""

# Global pipeline instance (lazy-loaded)
_pipeline: Optional[CortexV2Pipeline] = None
_pipeline_config = {}

# Global prompt pipeline
_prompt_pipeline: Optional[PromptPipeline] = None

# Simple conversation store (in production, use database)
_conversations: Dict[str, List[ChatMessage]] = {}

# Cloud provider clients (lazy-loaded)
_openai_client = None
_anthropic_client = None

# Provider API keys (set via environment or /api/config)
_provider_keys = {
    'openai': None,
    'anthropic': None
}

# Optimization tools
_query_cache = QueryCache(maxsize=1000, ttl_seconds=3600)
_metrics = LatencyMetrics()
_workbench = PromptWorkbench()

# File processing queue
_processing_queue: Dict[str, Dict] = {}


# ═══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════

class ChunkRequest(BaseModel):
    """Request to chunk text"""
    text: str = Field(..., description="Text to chunk")
    chunk_size: int = Field(1024, description="Max tokens per chunk")
    chunk_overlap: int = Field(128, description="Overlap tokens")
    strategy: str = Field("recursive", description="Chunking strategy")


class EmbedRequest(BaseModel):
    """Request to generate embeddings"""
    texts: List[str] = Field(..., description="Texts to embed")
    model: str = Field("all-MiniLM-L6-v2", description="Embedding model")


class SearchRequest(BaseModel):
    """Semantic search request"""
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, gt=0, le=100, description="Number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")


class ProcessRequest(BaseModel):
    """Document processing request"""
    enable_chunking: bool = Field(True, description="Enable chunking")
    enable_embeddings: bool = Field(True, description="Generate embeddings")
    enable_classification: bool = Field(True, description="LLM classification")
    chunk_size: int = Field(1024, description="Max tokens per chunk")
    chunk_strategy: str = Field("recursive", description="Chunking strategy")


class RAGQueryRequest(BaseModel):
    """RAG query request"""
    question: str = Field(..., description="User question")
    context_size: int = Field(5, description="Number of context chunks")
    llm_provider: str = Field("local", description="LLM provider: local|openai|anthropic")
    model: Optional[str] = Field(None, description="Specific model name")


class ChatMessage(BaseModel):
    """Chat message"""
    role: str = Field(..., description="Message role: user|assistant")
    content: str = Field(..., description="Message content")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="Source citations")


class ChatRequest(BaseModel):
    """Chat request with conversation history"""
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    history: List[ChatMessage] = Field(default_factory=list, description="Conversation history")
    context_size: int = Field(5, description="Number of context chunks for RAG")
    max_history_turns: int = Field(5, description="Max conversation turns to keep")
    llm_provider: str = Field("local", description="LLM provider")


# ═══════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for Svelte frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_pipeline() -> CortexV2Pipeline:
    """Get or create pipeline instance"""
    global _pipeline
    
    if _pipeline is None:
        _pipeline = CortexV2Pipeline(
            llamacpp_url=_pipeline_config.get('llamacpp_url', 'http://localhost:8080'),
            chunk_size=_pipeline_config.get('chunk_size', 1024),
            chunk_overlap=_pipeline_config.get('chunk_overlap', 128),
            chunk_strategy=_pipeline_config.get('chunk_strategy', 'recursive'),
            embedding_model=_pipeline_config.get('embedding_model', 'all-MiniLM-L6-v2'),
            workers=_pipeline_config.get('workers', 4),
            enable_vector_db=_pipeline_config.get('enable_vector_db', True),
            verbose=_pipeline_config.get('verbose', False)
        )
    
    return _pipeline


# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """API root - health check"""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "chunk": "/api/chunk",
            "embed": "/api/embed",
            "search": "/api/search",
            "process": "/api/process",
            "rag": "/api/rag",
            "chat": "/api/chat",
            "stats": "/api/stats"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "pipeline_initialized": _pipeline is not None
    }


@app.post("/api/chunk")
async def chunk_text(request: ChunkRequest):
    """
    Chunk text into semantic segments
    
    Example:
    ```json
    {
        "text": "# Document\\n\\nContent here...",
        "chunk_size": 512,
        "chunk_overlap": 64,
        "strategy": "recursive"
    }
    ```
    """
    try:
        from cortex_chunker import MarkdownChunker, ChunkStrategy
        
        chunker = MarkdownChunker(
            strategy=ChunkStrategy(request.strategy),
            max_tokens=request.chunk_size,
            overlap=request.chunk_overlap
        )
        
        chunks = chunker.chunk_text(request.text, source_file="api_request")
        
        return {
            "num_chunks": len(chunks),
            "chunks": [
                {
                    "chunk_id": c.metadata.chunk_id,
                    "text": c.text,
                    "token_count": c.metadata.token_count,
                    "word_count": c.metadata.word_count,
                    "headers": c.metadata.headers
                }
                for c in chunks
            ],
            "stats": chunker.get_stats(chunks)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/embed")
async def generate_embeddings(request: EmbedRequest):
    """
    Generate embeddings for texts
    
    Example:
    ```json
    {
        "texts": ["First document", "Second document"],
        "model": "all-MiniLM-L6-v2"
    }
    ```
    """
    try:
        from cortex_embeddings import EmbeddingGenerator
        
        generator = EmbeddingGenerator(model_name=request.model)
        embeddings = generator.encode(request.texts)
        
        return {
            "num_texts": len(request.texts),
            "embedding_dim": embeddings.shape[1],
            "embeddings": embeddings.tolist()  # Convert numpy to list
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def semantic_search(request: SearchRequest):
    """
    Perform semantic search on processed documents
    
    Example:
    ```json
    {
        "query": "error handling best practices",
        "top_k": 5
    }
    ```
    """
    try:
        pipeline = get_pipeline()
        results = pipeline.semantic_search(request.query, top_k=request.top_k)
        
        return {
            "query": request.query,
            "num_results": len(results),
            "results": [
                {
                    "chunk_id": r.chunk_id,
                    "text": r.text,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in results
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process")
async def process_document(
    file: UploadFile = File(...),
    request: ProcessRequest = None
):
    """
    Process uploaded markdown file
    
    Returns structured insights with chunking, embeddings, and classification
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        # Process with pipeline
        pipeline = get_pipeline()
        result = pipeline.process_document(tmp_path)
        
        # Clean up
        tmp_path.unlink()
        
        return {
            "success": True,
            "file_name": file.filename,
            "insights": {
                "num_chunks": result.num_chunks,
                "total_tokens": result.total_tokens,
                "themes": result.themes,
                "patterns": result.patterns,
                "learnings": result.learnings,
                "concepts": result.concepts,
                "recommendations": result.recommendations
            },
            "metadata": {
                "model_used": result.model_used,
                "chunking_strategy": result.chunking_strategy,
                "processing_time": result.processing_time_total
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag")
async def rag_query(request: RAGQueryRequest):
    """
    RAG (Retrieval-Augmented Generation) endpoint
    
    1. Semantic search for relevant chunks
    2. Build context from top results
    3. Generate answer with LLM
    
    Example:
    ```json
    {
        "question": "How do I handle errors in Python?",
        "context_size": 5,
        "llm_provider": "local"
    }
    ```
    """
    try:
        pipeline = get_pipeline()
        
        # Step 1: Retrieve relevant chunks
        search_results = pipeline.semantic_search(request.question, top_k=request.context_size)
        
        if not search_results:
            return {
                "answer": "No relevant information found in the knowledge base.",
                "sources": []
            }
        
        # Step 2: Build context
        context = "\n\n".join([
            f"[Source {i+1}]\n{r.text}" 
            for i, r in enumerate(search_results)
        ])
        
        # Step 3: Generate answer (simplified - expand for cloud providers)
        if request.llm_provider == "local" and pipeline.llm_client:
            from cortex import PromptBuilder
            
            rag_prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {request.question}

Answer (be concise and cite sources):"""
            
            answer = pipeline.llm_client.generate(rag_prompt, max_retries=2)
            
            return {
                "answer": answer if answer else "Failed to generate answer",
                "sources": [
                    {
                        "chunk_id": r.chunk_id,
                        "text": r.text[:200] + "...",
                        "score": r.score
                    }
                    for r in search_results
                ],
                "context_used": len(search_results),
                "llm_provider": request.llm_provider
            }
        else:
            return {
                "answer": "Cloud RAG providers not yet implemented. Use llm_provider='local'",
                "sources": [{"text": r.text[:200] + "...", "score": r.score} for r in search_results]
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get vector database statistics"""
    try:
        pipeline = get_pipeline()
        
        if pipeline.embedding_manager and pipeline.embedding_manager.vector_store:
            return {
                "total_vectors": len(pipeline.embedding_manager.vector_store),
                "embedding_dim": pipeline.embedding_manager.generator.embedding_dim,
                "model": pipeline.embedding_manager.generator.model_name
            }
        else:
            return {"message": "Vector database not initialized"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with RAG and conversation memory
    
    Features:
    - Semantic search for context
    - Prompt pipeline with few-shot examples
    - Conversation history management
    - Source citations
    
    Example:
    ```json
    {
        "message": "How do I handle errors?",
        "conversation_id": "conv_123",
        "history": [],
        "context_size": 5
    }
    ```
    """
    try:
        global _prompt_pipeline, _conversations
        
        # Initialize prompt pipeline
        if _prompt_pipeline is None:
            _prompt_pipeline = PromptPipeline()
        
        # Get or create conversation
        conv_id = request.conversation_id or f"conv_{datetime.now().timestamp()}"
        if conv_id not in _conversations:
            _conversations[conv_id] = []
        
        # Add user message to history
        user_msg = ChatMessage(role="user", content=request.message)
        _conversations[conv_id].append(user_msg)
        
        # Get pipeline
        pipeline = get_pipeline()
        
        # Step 1: Semantic search for relevant chunks
        search_results = pipeline.semantic_search(request.message, top_k=request.context_size)
        
        if not search_results:
            answer = "I don't have relevant information in my knowledge base to answer this question."
            sources = []
        else:
            # Step 2: Convert search results to Source objects
            sources = [
                Source(
                    id=i+1,
                    text=r.text,
                    score=r.score,
                    metadata=r.metadata
                )
                for i, r in enumerate(search_results)
            ]
            
            # Step 3: Convert chat history to Message objects
            history_messages = [
                Message(role=msg.role, content=msg.content)
                for msg in _conversations[conv_id][-request.max_history_turns*2:]
            ]
            
            # Step 4: Build prompt with pipeline
            prompt = _prompt_pipeline.build_rag_prompt(
                question=request.message,
                sources=sources,
                history=history_messages[:-1]  # Exclude current user message
            )
            
            # Step 5: Generate answer with LLM
            if request.llm_provider == "local" and pipeline.llm_client:
                answer = pipeline.llm_client.generate(prompt, max_retries=2)
                
                if not answer:
                    answer = "Failed to generate answer. Please try again."
            else:
                answer = "Cloud providers not yet implemented. Use llm_provider='local'"
        
        # Step 6: Create assistant message
        assistant_msg = ChatMessage(
            role="assistant",
            content=answer,
            sources=[
                {
                    "id": s.id,
                    "text": s.text[:200] + "..." if len(s.text) > 200 else s.text,
                    "score": s.score
                }
                for s in sources
            ] if sources else None
        )
        
        # Add to conversation
        _conversations[conv_id].append(assistant_msg)
        
        # Keep conversation size manageable
        if len(_conversations[conv_id]) > request.max_history_turns * 4:
            _conversations[conv_id] = _conversations[conv_id][-request.max_history_turns * 4:]
        
        return {
            "conversation_id": conv_id,
            "message": assistant_msg.dict(),
            "context_used": len(sources),
            "prompt_tokens": _prompt_pipeline.estimate_tokens(prompt) if sources else 0,
            "history_length": len(_conversations[conv_id])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# STARTUP/SHUTDOWN
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logging.info(f"{API_TITLE} v{API_VERSION} starting...")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logging.info("Shutting down...")


# ═══════════════════════════════════════════════════════════════
# MAIN (for uvicorn)
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "cortex_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
