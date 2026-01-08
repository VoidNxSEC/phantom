#!/usr/bin/env python3
"""
CORTEX v2.0 - Unified Pipeline with Chunking + Embeddings + Classification

Integrates semantic chunking, embeddings, and LLM classification into a single pipeline
with support for RAG and API integrations.
"""

import argparse
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

# Import v2 modules
from cortex_chunker import Chunk, ChunkStrategy, MarkdownChunker
from cortex_embeddings import EmbeddingManager, SearchResult

# Import v1 components
try:
    from cortex import (
        Concept,
        Learning,
        LlamaCppClient,
        MarkdownInsights,
        Pattern,
        PromptBuilder,
        Recommendation,
        Theme,
    )

    CORTEX_V1_AVAILABLE = True
except ImportError:
    CORTEX_V1_AVAILABLE = False
    logging.warning("CORTEX v1.0 modules not available, some features disabled")

from rich.console import Console
from rich.panel import Panel

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

VERSION = "2.0.0"
DEFAULT_CHUNK_SIZE = 1024
DEFAULT_CHUNK_OVERLAP = 128
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_WORKERS = 4


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════


@dataclass
class ChunkInsights:
    """Insights extracted from a single chunk"""

    chunk_id: int
    chunk_text: str
    themes: list[dict]
    patterns: list[dict]
    learnings: list[dict]
    concepts: list[dict]
    recommendations: list[dict]
    processing_time: float


@dataclass
class DocumentInsights:
    """Aggregated insights from all document chunks"""

    file_path: str
    file_name: str
    num_chunks: int
    total_tokens: int

    # Aggregated insights
    themes: list[dict]
    patterns: list[dict]
    learnings: list[dict]
    concepts: list[dict]
    recommendations: list[dict]

    # Metadata
    processed_at: str
    processing_time_total: float
    model_used: str
    chunking_strategy: str

    # v2.0 specific
    vector_db_path: str | None = None
    chunk_insights: list[ChunkInsights] = None


# ═══════════════════════════════════════════════════════════════
# CORTEX v2.0 PIPELINE
# ═══════════════════════════════════════════════════════════════


class CortexV2Pipeline:
    """
    Unified CORTEX v2.0 pipeline

    Workflow:
    1. Chunk document semantically
    2. Generate embeddings for chunks
    3. Classify each chunk with LLM
    4. Aggregate insights
    5. Store in vector DB for RAG
    """

    def __init__(
        self,
        llamacpp_url: str = "http://localhost:8080",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        chunk_strategy: str = "recursive",
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        workers: int = DEFAULT_WORKERS,
        enable_vector_db: bool = True,
        vector_db_path: Path | None = None,
        verbose: bool = False,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.workers = workers
        self.enable_vector_db = enable_vector_db
        self.vector_db_path = vector_db_path
        self.verbose = verbose

        self.console = Console()

        # Initialize chunker
        self.chunker = MarkdownChunker(
            strategy=ChunkStrategy(chunk_strategy),
            max_tokens=chunk_size,
            overlap=chunk_overlap,
        )

        # Initialize embedding manager
        if enable_vector_db:
            self.embedding_manager = EmbeddingManager(model_name=embedding_model)
        else:
            self.embedding_manager = None

        # Initialize LLM client (if v1 available)
        if CORTEX_V1_AVAILABLE:
            self.llm_client = LlamaCppClient(base_url=llamacpp_url)
        else:
            self.llm_client = None
            logging.warning("LLM classification disabled (cortex v1 not available)")

        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )

    def process_document(self, filepath: Path) -> DocumentInsights:
        """
        Process a single document through the v2 pipeline

        Args:
            filepath: Path to markdown file

        Returns:
            DocumentInsights with aggregated results
        """
        start_time = datetime.now()

        self.console.print(f"\n[cyan]📄 Processing: {filepath.name}[/cyan]")

        # Step 1: Chunk document
        self.console.print("  [yellow]1/4 Chunking document...[/yellow]")
        chunks = self.chunker.chunk_file(filepath)
        stats = self.chunker.get_stats(chunks)

        self.console.print(
            f"    ✓ Created {len(chunks)} chunks ({stats['avg_tokens_per_chunk']:.0f} tokens avg)"
        )

        # Step 2: Generate embeddings
        if self.enable_vector_db and self.embedding_manager:
            self.console.print("  [yellow]2/4 Generating embeddings...[/yellow]")
            chunk_texts = [c.text for c in chunks]
            chunk_metadata = [asdict(c.metadata) for c in chunks]

            self.embedding_manager.add_texts(
                chunk_texts, metadata=chunk_metadata, batch_size=32
            )
            self.console.print(f"    ✓ Generated embeddings for {len(chunks)} chunks")
        else:
            self.console.print("  [dim]2/4 Skipping embeddings (disabled)[/dim]")

        # Step 3: Classify chunks with LLM
        if self.llm_client:
            self.console.print("  [yellow]3/4 Classifying chunks with LLM...[/yellow]")
            chunk_insights = self._classify_chunks_parallel(chunks, filepath.name)
            self.console.print(f"    ✓ Classified {len(chunk_insights)} chunks")
        else:
            self.console.print(
                "  [dim]3/4 Skipping LLM classification (disabled)[/dim]"
            )
            chunk_insights = []

        # Step 4: Aggregate insights
        self.console.print("  [yellow]4/4 Aggregating insights...[/yellow]")
        aggregated = (
            self._aggregate_insights(chunk_insights)
            if chunk_insights
            else self._empty_insights()
        )

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()

        # Build result
        result = DocumentInsights(
            file_path=str(filepath),
            file_name=filepath.name,
            num_chunks=len(chunks),
            total_tokens=stats["total_tokens"],
            themes=aggregated["themes"],
            patterns=aggregated["patterns"],
            learnings=aggregated["learnings"],
            concepts=aggregated["concepts"],
            recommendations=aggregated["recommendations"],
            processed_at=datetime.now(UTC).isoformat(),
            processing_time_total=processing_time,
            model_used=self.llm_client.model if self.llm_client else "N/A",
            chunking_strategy=self.chunker.strategy.value,
            vector_db_path=str(self.vector_db_path) if self.vector_db_path else None,
            chunk_insights=chunk_insights,
        )

        self.console.print(f"[green]✓ Completed in {processing_time:.1f}s[/green]\n")

        return result

    def _classify_chunks_parallel(
        self, chunks: list[Chunk], source_file: str
    ) -> list[ChunkInsights]:
        """Classify chunks in parallel using thread pool"""
        chunk_insights = []

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {
                executor.submit(self._classify_single_chunk, chunk, source_file): chunk
                for chunk in chunks
            }

            for future in as_completed(futures):
                insight = future.result()
                if insight:
                    chunk_insights.append(insight)

        return chunk_insights

    def _classify_single_chunk(
        self, chunk: Chunk, source_file: str
    ) -> ChunkInsights | None:
        """Classify a single chunk with LLM"""
        import time

        start_time = time.time()

        try:
            # Build prompt for chunk
            prompt = PromptBuilder.build_extraction_prompt(
                chunk.text, f"{source_file} [chunk {chunk.metadata.chunk_id}]"
            )

            # Generate with LLM
            response = self.llm_client.generate(prompt)
            if not response:
                return None

            # Parse JSON
            data = PromptBuilder.parse_json_response(response)
            if not data:
                return None

            processing_time = time.time() - start_time

            return ChunkInsights(
                chunk_id=chunk.metadata.chunk_id,
                chunk_text=chunk.text[:200] + "...",  # Preview only
                themes=data.get("themes", []),
                patterns=data.get("patterns", []),
                learnings=data.get("learnings", []),
                concepts=data.get("concepts", []),
                recommendations=data.get("recommendations", []),
                processing_time=processing_time,
            )

        except Exception as e:
            logging.error(f"Error classifying chunk {chunk.metadata.chunk_id}: {e}")
            return None

    def _aggregate_insights(self, chunk_insights: list[ChunkInsights]) -> dict:
        """
        Aggregate insights from multiple chunks

        Strategy:
        - Deduplicate similar themes/concepts
        - Merge patterns by frequency
        - Prioritize high-value learnings/recommendations
        """
        aggregated = {
            "themes": [],
            "patterns": [],
            "learnings": [],
            "concepts": [],
            "recommendations": [],
        }

        # Simple aggregation: collect all, deduplicate by title/name
        seen_themes = set()
        seen_concepts = set()
        seen_learnings = set()

        for chunk in chunk_insights:
            # Themes
            for theme in chunk.themes:
                title = theme.get("title", "")
                if title and title not in seen_themes:
                    aggregated["themes"].append(theme)
                    seen_themes.add(title)

            # Concepts
            for concept in chunk.concepts:
                name = concept.get("name", "")
                if name and name not in seen_concepts:
                    aggregated["concepts"].append(concept)
                    seen_concepts.add(name)

            # Learnings
            for learning in chunk.learnings:
                title = learning.get("title", "")
                if title and title not in seen_learnings:
                    aggregated["learnings"].append(learning)
                    seen_learnings.add(title)

            # Patterns (merge by type, sum frequency)
            aggregated["patterns"].extend(chunk.patterns)

            # Recommendations
            aggregated["recommendations"].extend(chunk.recommendations)

        return aggregated

    def _empty_insights(self) -> dict:
        """Return empty insights structure"""
        return {
            "themes": [],
            "patterns": [],
            "learnings": [],
            "concepts": [],
            "recommendations": [],
        }

    def semantic_search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """
        Perform semantic search on processed documents

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of SearchResult objects
        """
        if not self.embedding_manager:
            raise ValueError("Vector DB not enabled. Set enable_vector_db=True")

        return self.embedding_manager.search(query, top_k=top_k)

    def save_vector_db(self, filepath: Path):
        """Save vector database to disk"""
        if self.embedding_manager:
            self.embedding_manager.save(filepath)

    @classmethod
    def load_vector_db(cls, filepath: Path, **kwargs) -> "CortexV2Pipeline":
        """Load pipeline with existing vector database"""
        pipeline = cls(**kwargs)
        if pipeline.embedding_manager:
            from cortex_embeddings import FAISSVectorStore

            pipeline.embedding_manager.vector_store = FAISSVectorStore.load(filepath)
        return pipeline


# ═══════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════


def main():
    """Main entry point for CORTEX v2.0"""
    parser = argparse.ArgumentParser(
        description=f"CORTEX v{VERSION} - Unified Pipeline with Chunking + Embeddings + Classification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Input/Output
    parser.add_argument(
        "-i", "--input", required=True, help="Input markdown file or directory"
    )
    parser.add_argument("-o", "--output", required=True, help="Output JSONL file")

    # Chunking
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Max tokens per chunk",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help="Overlap tokens",
    )
    parser.add_argument(
        "--chunk-strategy",
        choices=["recursive", "sliding", "simple"],
        default="recursive",
    )

    # Embeddings
    parser.add_argument(
        "--enable-vector-db", action="store_true", help="Enable vector database"
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help="Embedding model name",
    )
    parser.add_argument("--vector-db-path", help="Path to save/load vector database")

    # LLM
    parser.add_argument(
        "--llamacpp-url", default="http://localhost:8080", help="LlamaCPP server URL"
    )

    # Processing
    parser.add_argument(
        "--workers", type=int, default=DEFAULT_WORKERS, help="Number of workers"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # Search mode
    parser.add_argument(
        "--search", help="Semantic search query (requires existing vector DB)"
    )
    parser.add_argument("--top-k", type=int, default=5, help="Top K search results")

    args = parser.parse_args()

    # Create pipeline
    pipeline = CortexV2Pipeline(
        llamacpp_url=args.llamacpp_url,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        chunk_strategy=args.chunk_strategy,
        embedding_model=args.embedding_model,
        workers=args.workers,
        enable_vector_db=args.enable_vector_db,
        vector_db_path=Path(args.vector_db_path) if args.vector_db_path else None,
        verbose=args.verbose,
    )

    console = Console()

    # Search mode
    if args.search:
        if not args.vector_db_path:
            console.print("[red]Error: --vector-db-path required for search[/red]")
            sys.exit(1)

        console.print(
            Panel.fit(
                f"[bold cyan]CORTEX v{VERSION} - Semantic Search[/bold cyan]\n\n"
                f"Query: {args.search}",
                border_style="cyan",
            )
        )

        pipeline = CortexV2Pipeline.load_vector_db(
            Path(args.vector_db_path), **vars(args)
        )
        results = pipeline.semantic_search(args.search, top_k=args.top_k)

        console.print(f"\n[green]Found {len(results)} results:[/green]\n")
        for i, result in enumerate(results, 1):
            console.print(f"{i}. [cyan]Score: {result.score:.3f}[/cyan]")
            console.print(f"   {result.text[:200]}...\n")

        return

    # Processing mode
    console.print(
        Panel.fit(
            f"[bold cyan]CORTEX v{VERSION}[/bold cyan]\n"
            f"Unified Pipeline: Chunking + Embeddings + Classification\n\n"
            f"Input: {args.input}\n"
            f"Output: {args.output}",
            border_style="cyan",
        )
    )

    # Process input
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if input_path.is_file():
        # Single file
        result = pipeline.process_document(input_path)

        # Save result
        with open(output_path, "w") as f:
            json.dump(asdict(result), f, ensure_ascii=False)
            f.write("\n")

        console.print(f"[green]✓ Results saved to: {output_path}[/green]")

    elif input_path.is_dir():
        # Directory
        md_files = list(input_path.rglob("*.md"))
        console.print(
            f"\n[yellow]Processing {len(md_files)} markdown files...[/yellow]\n"
        )

        with open(output_path, "w") as f:
            for md_file in md_files:
                result = pipeline.process_document(md_file)
                json.dump(asdict(result), f, ensure_ascii=False)
                f.write("\n")

        console.print(
            f"\n[green]✓ Processed {len(md_files)} files → {output_path}[/green]"
        )

    # Save vector DB if enabled
    if args.enable_vector_db and args.vector_db_path:
        pipeline.save_vector_db(Path(args.vector_db_path))
        console.print(f"[green]✓ Vector DB saved to: {args.vector_db_path}[/green]")


if __name__ == "__main__":
    main()
