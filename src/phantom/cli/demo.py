#!/usr/bin/env python3
"""
phantom demo — One-command showcase.

Runs the full Phantom pipeline on sample documents — fully offline:

  1. Semantic chunking (structure-preserving, no LLM needed)
  2. Vector embedding via sentence-transformers
  3. FAISS indexing
  4. Semantic search
  5. RAG chat (optional — requires a running LLM provider)

Usage:
    phantom demo                    Full pipeline with defaults
    phantom demo --no-rag           Skip RAG chat
    phantom demo --doc tech         Run on a different sample
    phantom demo --doc quantum -v   Verbose output
"""

import time
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

app = typer.Typer(help="One-command demo of the full Phantom pipeline")
console = Console()

# ── Paths ───────────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent.parent.parent.parent
DEMO_INPUT = HERE / "demo_input"

SAMPLE_DOCS: dict[str, str] = {
    "financial": "financial_report.md",
    "tech": "technical_blog.md",
    "quantum": "research_note.md",
}

QUERIES: dict[str, str] = {
    "financial": "What was NovaTech's revenue growth and what are the main risks?",
    "tech": "What chunking strategies are recommended for RAG pipelines?",
    "quantum": "What are the main challenges in quantum error correction?",
}

CHAT_QUESTIONS: dict[str, str] = {
    "financial": "Summarize NovaTech's financial outlook for Q1 2025.",
    "tech": "Compare FAISS, Pinecone and Weaviate for vector search.",
    "quantum": "Why is quantum error correction considered the main bottleneck?",
}


# ── Rich helpers ────────────────────────────────────────────────────


def _step(msg: str, style: str = "bold cyan") -> None:
    console.print()
    console.print(Rule(style="dim"))
    console.print(Text(msg, style=style))
    console.print(Rule(style="dim"))


def _ok(msg: str) -> None:
    console.print(f"  [green]✓[/] {msg}")


def _warn(msg: str) -> None:
    console.print(f"  [yellow]⚠[/] {msg}")


def _fail(msg: str) -> None:
    console.print(f"  [red]✗[/] {msg}")


# ── Domain helpers ──────────────────────────────────────────────────


def _validate_doc(doc_name: str) -> Path:
    """Resolve and validate the sample document path."""
    filename = SAMPLE_DOCS.get(doc_name)
    if not filename:
        console.print(
            f"[red]Unknown document '{doc_name}'. Choose from: {', '.join(SAMPLE_DOCS)}[/]"
        )
        raise typer.Exit(1)

    doc_path = DEMO_INPUT / filename
    if not doc_path.exists():
        console.print(
            f"[red]Demo document not found at {doc_path}.[/]\n"
            f"  Make sure 'demo_input/' exists alongside the source tree."
        )
        raise typer.Exit(1)

    return doc_path


# ── Pipeline steps ─────────────────────────────────────────────────


def _step_chunk(content: str, doc_name: str, verbose: bool) -> list[Any]:
    """Step 1: Semantic chunking (no LLM needed — works fully offline)."""
    from phantom.core.cortex import SemanticChunker

    _step("🧩 Step 1: Semantic Chunking")

    with console.status("[cyan]Chunking document…", spinner="dots"):
        chunker = SemanticChunker(max_tokens=1024, overlap=128)
        chunks = chunker.chunk_text(content, source_file=doc_name)

    _ok(f"Document split into [bold]{len(chunks)}[/] semantic chunks")

    if chunks and verbose:
        sample = chunks[0]
        console.print(
            Panel(
                sample.text[:300] + ("…" if len(sample.text) > 300 else ""),
                title=f"[bold]Sample Chunk ({sample.chunk_id})",
                border_style="blue",
                width=80,
            )
        )

    return chunks


def _step_index(chunks: list[Any], doc_name: str) -> Any:
    """Step 2: Embedding generation + Step 3: FAISS indexing."""
    from phantom.core.embeddings import EmbeddingGenerator
    from phantom.rag.vectors import FAISSVectorStore

    _step("📐 Step 2: Embedding + FAISS Indexing")

    with console.status("[cyan]Loading embedding model (sentence-transformers)…", spinner="dots"):
        embedder = EmbeddingGenerator()

    _ok(f"Embedding model: [bold]{embedder.model_name}[/]")
    _ok(f"Embedding dimension: [bold]{embedder.dimension}[/]")

    texts = [c.text for c in chunks]
    metadata = [
        {
            "source": doc_name,
            "chunk_id": c.chunk_id,
            "source_file": c.source_file,
        }
        for c in chunks
    ]

    with console.status("[cyan]Generating embeddings…", spinner="dots"):
        start = time.perf_counter()
        embeddings = embedder.encode(texts)
        elapsed = time.perf_counter() - start

    _ok(f"Generated [bold]{len(embeddings)}[/] embeddings in {elapsed:.2f}s")

    with console.status("[cyan]Building FAISS index…", spinner="dots"):
        store = FAISSVectorStore(embedding_dim=embedder.dimension)
        store.add(embeddings, texts, metadata)

    _ok(f"FAISS index built with [bold]{len(store)}[/] vectors")

    return {"store": store, "chunks": chunks, "embedder": embedder}


def _step_search(store: Any, query: str) -> list[Any]:
    """Step 4: Semantic search."""
    from phantom.core.embeddings import EmbeddingGenerator

    _step("🔎 Step 4: Semantic Search")

    embedder = EmbeddingGenerator()

    with console.status(f"[cyan]Searching for: {query}", spinner="dots"):
        start = time.perf_counter()
        query_vec = embedder.encode([query])[0]
        results = store.search(query_vec, top_k=3)
        elapsed = time.perf_counter() - start

    _ok(f"Search completed in [bold]{elapsed:.3f}s[/] — {len(results)} result(s)")

    if not results:
        _warn("No results found. The index might be empty.")
        return []

    tbl = Table(title="Top Search Results")
    tbl.add_column("#", style="dim")
    tbl.add_column("Score", style="green")
    tbl.add_column("Snippet", style="white", width=70)
    tbl.add_column("Source", style="cyan")

    for i, r in enumerate(results, 1):
        score_color = "green" if r.score > 0.7 else "yellow" if r.score > 0.4 else "red"
        snippet = r.text[:120].replace("\n", " ") + ("…" if len(r.text) > 120 else "")
        src = r.metadata.get("source", "?") if hasattr(r, "metadata") else "?"
        tbl.add_row(str(i), f"[{score_color}]{r.score:.4f}[/]", snippet, src)

    console.print(tbl)
    return results


def _step_chat(question: str, context_chunks: list[Any]) -> None:
    """Step 5 (optional): RAG chat with an LLM provider."""
    from phantom.providers.registry import get_available_providers, get_provider

    _step("💬 Step 5: RAG Chat")

    available = get_available_providers()

    # Prefer local, fall back to any cloud provider
    chosen_provider: str | None = None
    chosen_model: str | None = None

    for provider_name in ("local", "openai", "anthropic", "deepseek"):
        models = available.get(provider_name, [])
        if models:
            chosen_provider = provider_name
            chosen_model = models[0]["id"]
            break

    if not chosen_provider or not chosen_model:
        _warn("No LLM provider available — skipping RAG chat.")
        _warn(
            "  Start a local llama.cpp server or set "
            "OPENAI_API_KEY / ANTHROPIC_API_KEY / DEEPSEEK_API_KEY"
        )
        return

    # Build context from search results
    context = (
        "\n\n".join(f"[Source: {r.metadata.get('source', '?')}]\n{r.text}" for r in context_chunks)
        if context_chunks
        else ""
    )

    system_prompt = (
        "You are a helpful assistant. Answer the user's question based "
        "strictly on the provided context. If the context doesn't contain "
        "the answer, say so."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        },
    ]

    try:
        provider = get_provider(chosen_provider)
        _ok(f"Using provider: [bold]{chosen_provider}[/] / model: [bold]{chosen_model}[/]")

        with console.status("[cyan]Generating answer…", spinner="dots"):
            start = time.perf_counter()
            response = provider.generate(messages=messages, model=chosen_model)
            elapsed = time.perf_counter() - start

        answer = response.get("content", response.get("text", str(response)))
        _ok(f"Generated in {elapsed:.2f}s")

        console.print(
            Panel(
                Markdown(answer),
                title=f"[bold]{question}[/]",
                border_style="magenta",
                width=80,
            )
        )

    except Exception as exc:
        _fail(f"RAG chat failed: {exc}")
        _warn("The core pipeline (chunk → embed → index → search) completed successfully!")
        _warn("The RAG chat step requires a running LLM provider.")


# ── CLI command ─────────────────────────────────────────────────────


@app.callback(invoke_without_command=True)
def demo(
    ctx: typer.Context,
    doc: str = typer.Option(
        "financial",
        "--doc",
        help=f"Sample document to use: {', '.join(SAMPLE_DOCS)}",
    ),
    no_rag: bool = typer.Option(False, "--no-rag", help="Skip the RAG chat step"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed output"),
):
    """
    Run the full Phantom pipeline as an interactive demo.

    Processes a sample document through semantic chunking, FAISS indexing,
    semantic search, and (optionally) RAG chat via an LLM provider.

    Works fully offline for the core pipeline (chunk → embed → index → search).
    Only the RAG chat step requires a running LLM provider.
    """
    doc_path = _validate_doc(doc)
    content = doc_path.read_text(encoding="utf-8")
    query = QUERIES.get(doc, QUERIES["financial"])
    chat_q = CHAT_QUESTIONS.get(doc, CHAT_QUESTIONS["financial"])

    # ── Intro ───────────────────────────────────────────────────────
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]🔮 Phantom Demo Pipeline[/]\n\n"
            "[white]Chunk → Embed → Index → Search → Chat (optional)[/]",
            border_style="cyan",
        )
    )
    wc = len(content.split())
    console.print(f"\n  Document: [bold]{doc_path.name}[/] ({wc} words)")
    console.print(f"  Search query: [italic]{query}[/]")
    console.print(f"  Chat question: [italic]{chat_q}[/]")
    console.print()

    # ── Step 1: Chunk ───────────────────────────────────────────────
    chunks = _step_chunk(content, doc, verbose)

    if not chunks:
        _fail("No chunks produced — cannot continue.")
        raise typer.Exit(1)

    # ── Step 2 & 3: Embed + Index ───────────────────────────────────
    index_result = _step_index(chunks, doc)

    # ── Step 4: Search ──────────────────────────────────────────────
    results = _step_search(index_result["store"], query)

    # ── Step 5: Chat (optional) ─────────────────────────────────────
    if not no_rag:
        _step_chat(chat_q, results)

    # ── Summary ─────────────────────────────────────────────────────
    _step("✅ Demo Complete", style="bold green")
    console.print(
        Panel.fit(
            "[green]The full Phantom pipeline ran successfully![/]\n\n"
            "[bold]What happened:[/]\n"
            "  [cyan]1.[/] Semantic chunker split the document intelligently\n"
            "  [cyan]2.[/] sentence-transformers generated vector embeddings\n"
            "  [cyan]3.[/] FAISS indexed the vectors for fast retrieval\n"
            "  [cyan]4.[/] Semantic search found relevant context\n"
            "  [cyan]5.[/] RAG chat synthesized an answer from context + LLM\n\n"
            "[dim]Try:[/] [bold]phantom demo --doc tech[/]\n"
            "      [bold]phantom demo --doc quantum --no-rag[/]",
            border_style="green",
        )
    )


def main() -> None:
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
