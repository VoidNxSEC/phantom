#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  CORTEX UNIFIED v2.0 - Intelligent Document Intelligence Engine ║
║  ─────────────────────────────────────────────────────────────── ║
║  MERGED: v1 Pydantic Models + v2 Unified Pipeline                ║
║  Features:                                                        ║
║  • Semantic chunking with intelligent splitting                   ║
║  • FAISS vector embeddings for RAG (local-first)                  ║
║  • Parallel LLM classification with retry logic                   ║
║  • VRAM/RAM monitoring with auto-throttling                       ║
║  • Pydantic validation for all extracted insights                 ║
║  • llama.cpp TURBO inference (OpenAI-compatible)                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import psutil

# Pydantic for validation
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Rich for beautiful output
from rich.console import Console

# Internal imports
try:
    from phantom.core.embeddings import EmbeddingGenerator
    from phantom.providers.base import AIProvider
    from phantom.providers.llamacpp import LlamaCppProvider
    from phantom.rag.vectors import FAISSVectorStore, SearchResult, create_vector_store

    PHANTOM_AVAILABLE = True
except ImportError:
    PHANTOM_AVAILABLE = False
    logging.debug("Phantom modules not available, using standalone mode")


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

VERSION = "2.0.0"
CODENAME = "CORTEX-UNIFIED"

# Processing defaults
DEFAULT_CHUNK_SIZE = 1024
DEFAULT_CHUNK_OVERLAP = 128
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.3
DEFAULT_WORKERS = 4
DEFAULT_BATCH_SIZE = 10
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 2.0

# Resource monitoring
VRAM_WARNING_MB = 512
VRAM_CRITICAL_MB = 256
RAM_WARNING_MB = 512


# ═══════════════════════════════════════════════════════════════
# PYDANTIC MODELS - Strict JSON Schema Validation
# ═══════════════════════════════════════════════════════════════


class ExtractionLevel(str, Enum):
    """Confidence/priority level"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Theme(BaseModel):
    """Extracted theme from content"""

    model_config = ConfigDict(extra="ignore")

    title: str = Field(
        ..., min_length=1, max_length=100, description="Theme title (2-5 words)"
    )
    description: str = Field(..., min_length=1, description="Brief theme description")
    confidence: ExtractionLevel = Field(default=ExtractionLevel.MEDIUM)
    keywords: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("keywords", mode="before")
    @classmethod
    def limit_keywords(cls, v):
        if isinstance(v, list):
            return v[:10]
        return v


class Pattern(BaseModel):
    """Identified pattern"""

    model_config = ConfigDict(extra="ignore")

    pattern_type: str = Field(..., description="Type: code, workflow, concept, etc")
    description: str = Field(...)
    examples: list[str] = Field(default_factory=list, max_length=3)
    frequency: int = Field(default=1, ge=1)

    @field_validator("examples", mode="before")
    @classmethod
    def limit_examples(cls, v):
        if isinstance(v, list):
            return v[:3]
        return v


class Learning(BaseModel):
    """Key learning or insight"""

    model_config = ConfigDict(extra="ignore")

    title: str = Field(...)
    description: str = Field(...)
    category: str = Field(..., description="Category: technical, process, concept")
    actionable: bool = Field(default=False)


class Concept(BaseModel):
    """Core concept"""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(...)
    definition: str = Field(...)
    related_concepts: list[str] = Field(default_factory=list, max_length=5)
    complexity: ExtractionLevel = Field(default=ExtractionLevel.MEDIUM)


class Recommendation(BaseModel):
    """Actionable recommendation"""

    model_config = ConfigDict(extra="ignore")

    title: str = Field(...)
    description: str = Field(...)
    priority: ExtractionLevel = Field(...)
    category: str = Field(
        ..., description="Category: best_practice, optimization, security"
    )
    implementation_effort: str = Field(..., description="Effort: low, medium, high")


class DocumentInsights(BaseModel):
    """Complete insights from a document"""

    model_config = ConfigDict(extra="ignore")

    file_path: str = Field(...)
    file_name: str = Field(...)
    processed_at: str = Field(...)
    word_count: int = Field(ge=0)

    # Extracted data
    themes: list[Theme] = Field(default_factory=list)
    patterns: list[Pattern] = Field(default_factory=list)
    learnings: list[Learning] = Field(default_factory=list)
    concepts: list[Concept] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)

    # Metadata
    processing_time_seconds: float = Field(ge=0)
    model_used: str = Field(default="local")
    chunk_count: int = Field(default=1)
    vector_indexed: bool = Field(default=False)
    confidence: ExtractionLevel = Field(default=ExtractionLevel.MEDIUM)


# ═══════════════════════════════════════════════════════════════
# SYSTEM MONITOR - VRAM/RAM Checking
# ═══════════════════════════════════════════════════════════════


class SystemMonitor:
    """Monitor system resources for safe processing"""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.last_check = 0.0
        self.check_interval = 5.0  # seconds

    def get_vram_usage(self) -> dict[str, Any]:
        """Get GPU VRAM usage via nvidia-smi"""
        try:
            import subprocess

            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.used,memory.total,memory.free",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                used, total, free = map(int, result.stdout.strip().split(","))
                return {
                    "used_mb": used,
                    "total_mb": total,
                    "free_mb": free,
                    "usage_percent": (used / total) * 100 if total > 0 else 0,
                    "available": True,
                }
        except Exception:
            pass
        return {"free_mb": float("inf"), "available": False}

    def get_ram_usage(self) -> dict[str, Any]:
        """Get system RAM usage"""
        mem = psutil.virtual_memory()
        return {
            "used_mb": mem.used // (1024 * 1024),
            "total_mb": mem.total // (1024 * 1024),
            "free_mb": mem.available // (1024 * 1024),
            "usage_percent": mem.percent,
        }

    def check_resources(self, pause_on_critical: bool = True) -> bool:
        """
        Check if resources are safe for processing.
        Returns True if OK, False if critical.
        """
        now = time.time()
        if now - self.last_check < self.check_interval:
            return True
        self.last_check = now

        vram = self.get_vram_usage()
        ram = self.get_ram_usage()

        # Check VRAM
        if vram.get("available", False):
            free = vram["free_mb"]
            if free < VRAM_CRITICAL_MB:
                self.console.print(f"[red]⚠️ CRITICAL: VRAM low ({free}MB)[/red]")
                if pause_on_critical:
                    time.sleep(5)
                return False
            elif free < VRAM_WARNING_MB:
                self.console.print(f"[yellow]⚠️ VRAM warning ({free}MB)[/yellow]")

        # Check RAM
        if ram["free_mb"] < RAM_WARNING_MB:
            self.console.print(f"[yellow]⚠️ RAM warning ({ram['free_mb']}MB)[/yellow]")

        return True


# ═══════════════════════════════════════════════════════════════
# PROMPT ENGINEERING - Optimized for extraction
# ═══════════════════════════════════════════════════════════════


class PromptBuilder:
    """Build structured prompts for LLM extraction"""

    SYSTEM_PROMPT = """You are an expert analyst extracting structured insights from documentation.

Extract:
1. **Themes**: Main topics (2-5 word titles)
2. **Patterns**: Recurring structures, workflows, code patterns
3. **Learnings**: Key insights and knowledge
4. **Concepts**: Core ideas with definitions
5. **Recommendations**: Actionable best practices

OUTPUT: Valid JSON only, no markdown blocks.

Schema:
{
  "themes": [{"title": str, "description": str, "confidence": "high|medium|low", "keywords": [str]}],
  "patterns": [{"pattern_type": str, "description": str, "examples": [str], "frequency": int}],
  "learnings": [{"title": str, "description": str, "category": str, "actionable": bool}],
  "concepts": [{"name": str, "definition": str, "related_concepts": [str], "complexity": "high|medium|low"}],
  "recommendations": [{"title": str, "description": str, "priority": "high|medium|low", "category": str, "implementation_effort": "low|medium|high"}]
}"""

    @classmethod
    def build_extraction_prompt(
        cls, content: str, file_name: str, chunk_info: str = ""
    ) -> str:
        """Build complete extraction prompt"""
        # Truncate if needed
        max_chars = DEFAULT_MAX_TOKENS * 3
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[... truncated ...]"

        context = f"SOURCE: {file_name}"
        if chunk_info:
            context += f" | {chunk_info}"

        return f"""{cls.SYSTEM_PROMPT}

{context}

CONTENT:
{content}

Extract insights (JSON only):"""

    @staticmethod
    def parse_json_response(response: str) -> dict | None:
        """Parse JSON from LLM response, handling markdown blocks"""
        # Strip markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()

        # Find JSON object
        response = response.strip()
        start_idx = response.find("{")
        end_idx = response.rfind("}")

        if start_idx != -1 and end_idx != -1:
            response = response[start_idx : end_idx + 1]

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logging.error(f"JSON parse error: {e}")
            return None


# ═══════════════════════════════════════════════════════════════
# SEMANTIC CHUNKER - Intelligent text splitting
# ═══════════════════════════════════════════════════════════════


@dataclass
class Chunk:
    """A text chunk with metadata"""

    text: str
    chunk_id: int
    source_file: str
    start_line: int = 0
    end_line: int = 0
    token_count: int = 0


class SemanticChunker:
    """Intelligent markdown chunking preserving structure"""

    MARKDOWN_SEPARATORS = [
        "\n## ",  # H2 headers
        "\n### ",  # H3 headers
        "\n#### ",  # H4 headers
        "\n\n---\n",  # Horizontal rules
        "\n\n```",  # Code blocks
        "\n\n",  # Paragraphs
        "\n",  # Lines
        ". ",  # Sentences
    ]

    def __init__(
        self,
        max_tokens: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.max_tokens = max_tokens
        self.overlap = overlap
        self._tokenizer = None

    @property
    def tokenizer(self):
        """Lazy load tiktoken"""
        if self._tokenizer is None:
            try:
                import tiktoken

                self._tokenizer = tiktoken.get_encoding("cl100k_base")
            except ImportError:
                # Fallback: approximate
                self._tokenizer = None
        return self._tokenizer

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        # Fallback: ~4 chars per token
        return len(text) // 4

    def chunk_text(self, text: str, source_file: str) -> list[Chunk]:
        """Split text into semantic chunks"""
        chunks = []
        current_text = text
        chunk_id = 0

        while current_text:
            if self.count_tokens(current_text) <= self.max_tokens:
                # Fits in one chunk
                chunks.append(
                    Chunk(
                        text=current_text.strip(),
                        chunk_id=chunk_id,
                        source_file=source_file,
                        token_count=self.count_tokens(current_text),
                    )
                )
                break

            # Find best split point
            split_point = self._find_split_point(current_text)
            chunk_text = current_text[:split_point].strip()

            if chunk_text:
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        chunk_id=chunk_id,
                        source_file=source_file,
                        token_count=self.count_tokens(chunk_text),
                    )
                )
                chunk_id += 1

            # Handle overlap
            overlap_start = max(0, split_point - self.overlap * 4)  # ~4 chars per token
            current_text = current_text[overlap_start:].strip()

        return chunks

    def _find_split_point(self, text: str) -> int:
        """Find best semantic split point"""
        target_chars = self.max_tokens * 4  # Approximate

        # Try each separator in order of preference
        for sep in self.MARKDOWN_SEPARATORS:
            # Find last occurrence before target
            pos = text.rfind(sep, 0, target_chars + len(sep))
            if pos > 0:
                return pos + len(sep)

        # Fallback: hard split at target
        return min(target_chars, len(text))

    def chunk_file(self, filepath: Path) -> list[Chunk]:
        """Chunk a file"""
        content = filepath.read_text(encoding="utf-8")
        return self.chunk_text(content, str(filepath.name))


# ═══════════════════════════════════════════════════════════════
# CORTEX PROCESSOR - Main Intelligence Engine
# ═══════════════════════════════════════════════════════════════


class CortexProcessor:
    """
    Unified CORTEX Processor - Best of v1 + v2

    Pipeline:
    1. Semantic chunking
    2. Parallel LLM classification
    3. Pydantic validation
    4. FAISS vector indexing
    5. Aggregation and output
    """

    def __init__(
        self,
        provider: AIProvider | None = None,
        llamacpp_url: str = "http://localhost:8080",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        workers: int = DEFAULT_WORKERS,
        enable_vectors: bool = True,
        embedding_model: str = "all-MiniLM-L6-v2",
        vector_path: Path | None = None,
        verbose: bool = False,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.workers = workers
        self.enable_vectors = enable_vectors
        self.vector_path = vector_path
        self.verbose = verbose

        self.console = Console()
        self.monitor = SystemMonitor(self.console)

        # Initialize chunker
        self.chunker = SemanticChunker(
            max_tokens=chunk_size,
            overlap=chunk_overlap,
        )

        # Initialize provider - LlamaCpp only
        if provider:
            self.provider = provider
        else:
            self.provider = LlamaCppProvider(base_url=llamacpp_url)

        # Initialize embeddings and vector store
        self.embeddings: EmbeddingGenerator | None = None
        self.vector_store: FAISSVectorStore | None = None

        if enable_vectors and PHANTOM_AVAILABLE:
            try:
                self.embeddings = EmbeddingGenerator(model_name=embedding_model)
                self.vector_store = create_vector_store(
                    self.embeddings.dimension, backend="auto"
                )
                logging.info(
                    f"Vector store initialized (dim={self.embeddings.dimension})"
                )
            except Exception as e:
                logging.warning(f"Vector store init failed: {e}")

        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )

    def process_document(self, filepath: Path) -> DocumentInsights:
        """
        Process a single document through the full pipeline.
        """
        start_time = time.time()
        filepath = Path(filepath)

        self.console.print(f"\n[cyan]📄 Processing: {filepath.name}[/cyan]")

        # Read content
        content = filepath.read_text(encoding="utf-8")
        word_count = len(content.split())

        # Step 1: Chunk
        self.console.print("  [yellow]1/4 Chunking...[/yellow]")
        chunks = self.chunker.chunk_text(content, filepath.name)
        self.console.print(f"    ✓ {len(chunks)} chunks")

        # Step 2: Classify with LLM
        self.console.print("  [yellow]2/4 Classifying with LLM...[/yellow]")
        chunk_results = self._classify_chunks(chunks)
        self.console.print(f"    ✓ {len(chunk_results)} classified")

        # Step 3: Generate embeddings
        vector_indexed = False
        if self.enable_vectors and self.embeddings and self.vector_store:
            self.console.print("  [yellow]3/4 Generating vectors...[/yellow]")
            try:
                texts = [c.text for c in chunks]
                embeddings = self.embeddings.encode(texts)
                self.vector_store.add(
                    embeddings,
                    texts,
                    [{"chunk_id": c.chunk_id, "source": c.source_file} for c in chunks],
                )
                vector_indexed = True
                self.console.print(f"    ✓ Indexed {len(chunks)} vectors")
            except Exception as e:
                logging.warning(f"Vector indexing failed: {e}")
        else:
            self.console.print("  [dim]3/4 Skipping vectors[/dim]")

        # Step 4: Aggregate
        self.console.print("  [yellow]4/4 Aggregating...[/yellow]")
        insights = self._aggregate_insights(
            chunk_results, filepath, word_count, vector_indexed
        )

        processing_time = time.time() - start_time
        insights.processing_time_seconds = processing_time

        self.console.print(f"[green]✓ Done in {processing_time:.1f}s[/green]")

        return insights

    def _classify_chunks(self, chunks: list[Chunk]) -> list[dict]:
        """Classify chunks in parallel"""
        results = []

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {
                executor.submit(self._classify_single, chunk): chunk for chunk in chunks
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logging.error(f"Classification error: {e}")

        return results

    def _classify_single(self, chunk: Chunk) -> dict | None:
        """Classify a single chunk"""
        # Check resources
        self.monitor.check_resources(pause_on_critical=True)

        # Build prompt
        prompt = PromptBuilder.build_extraction_prompt(
            chunk.text, chunk.source_file, f"Chunk {chunk.chunk_id}"
        )

        # Generate
        try:
            result = self.provider.generate(prompt)
            return PromptBuilder.parse_json_response(result.text)
        except Exception as e:
            logging.error(f"Generation failed for chunk {chunk.chunk_id}: {e}")
            return None

    def _aggregate_insights(
        self,
        chunk_results: list[dict],
        filepath: Path,
        word_count: int,
        vector_indexed: bool,
    ) -> DocumentInsights:
        """Aggregate insights from multiple chunks with deduplication"""

        aggregated = {
            "themes": [],
            "patterns": [],
            "learnings": [],
            "concepts": [],
            "recommendations": [],
        }

        seen = {key: set() for key in aggregated}

        for result in chunk_results:
            if not result:
                continue

            # Themes - dedupe by title
            for item in result.get("themes", []):
                title = item.get("title", "")
                if title and title not in seen["themes"]:
                    try:
                        aggregated["themes"].append(Theme(**item))
                        seen["themes"].add(title)
                    except Exception:
                        pass

            # Concepts - dedupe by name
            for item in result.get("concepts", []):
                name = item.get("name", "")
                if name and name not in seen["concepts"]:
                    try:
                        aggregated["concepts"].append(Concept(**item))
                        seen["concepts"].add(name)
                    except Exception:
                        pass

            # Learnings - dedupe by title
            for item in result.get("learnings", []):
                title = item.get("title", "")
                if title and title not in seen["learnings"]:
                    try:
                        aggregated["learnings"].append(Learning(**item))
                        seen["learnings"].add(title)
                    except Exception:
                        pass

            # Patterns - collect all (merge later)
            for item in result.get("patterns", []):
                try:
                    aggregated["patterns"].append(Pattern(**item))
                except Exception:
                    pass

            # Recommendations - collect all
            for item in result.get("recommendations", []):
                try:
                    aggregated["recommendations"].append(Recommendation(**item))
                except Exception:
                    pass

        return DocumentInsights(
            file_path=str(filepath),
            file_name=filepath.name,
            processed_at=datetime.now(UTC).isoformat(),
            word_count=word_count,
            themes=aggregated["themes"],
            patterns=aggregated["patterns"],
            learnings=aggregated["learnings"],
            concepts=aggregated["concepts"],
            recommendations=aggregated["recommendations"],
            processing_time_seconds=0.0,  # Updated by caller
            model_used=self.provider.name,
            chunk_count=len(chunk_results),
            vector_indexed=vector_indexed,
            confidence=ExtractionLevel.MEDIUM,
        )

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Semantic search over indexed documents"""
        if not self.vector_store or not self.embeddings:
            raise ValueError("Vector search not enabled")

        query_embedding = self.embeddings.encode_single(query)
        return self.vector_store.search(query_embedding, top_k=top_k)

    def save_index(self, filepath: Path | None = None):
        """Save vector index to disk"""
        if self.vector_store:
            path = filepath or self.vector_path or Path("./phantom_index")
            self.vector_store.save(path)
            self.console.print(f"[green]✓ Index saved to {path}[/green]")

    def load_index(self, filepath: Path):
        """Load vector index from disk"""
        if PHANTOM_AVAILABLE:
            self.vector_store = FAISSVectorStore.load(filepath)
            self.console.print(f"[green]✓ Index loaded from {filepath}[/green]")


# ═══════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # Main processor
    "CortexProcessor",
    "SemanticChunker",
    # Data models
    "DocumentInsights",
    "Theme",
    "Pattern",
    "Learning",
    "Concept",
    "Recommendation",
    "ExtractionLevel",
    # Utilities
    "SystemMonitor",
    "PromptBuilder",
    "Chunk",
    # Constants
    "VERSION",
    "CODENAME",
]
