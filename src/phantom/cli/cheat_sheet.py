"""One-page CLI quick reference (also used by `just cheat`)."""

from rich.console import Console

CHEAT_SHEET = """\
[bold cyan]Phantom CLI[/bold cyan] — quick reference
[dim]────────────────────────────────────────────────────────────────[/dim]

[bold]Getting started[/bold]
  [cyan]phantom demo[/cyan] [--doc financial|tech|quantum] [--no-rag]   full pipeline showcase
  [cyan]phantom doctor[/cyan] [--providers-only] [--verbose]          stack diagnostics
  [cyan]phantom cheat[/cyan]                                      show this sheet

[bold]Documents & pipeline[/bold]
  [cyan]phantom extract[/cyan] -i DIR -o out.jsonl           CORTEX insights (md/txt/…)
  [cyan]phantom analyze[/cyan] FILE [--no-sentiment]        single-file insights + sentiment
  [cyan]phantom classify[/cyan] DIR [-o OUT] [--dry-run]     DAG classification run
  [cyan]phantom scan[/cyan] [DIR]                           sensitive-pattern scan

[bold]RAG (local FAISS)[/bold]
  [cyan]phantom rag ingest[/cyan] DIR [-c COLLECTION]       build index under [dim]data/[/dim]
  [cyan]phantom rag query[/cyan] "…" [-c COLLECTION] [-k 5]   semantic search over index

[bold]Tools[/bold]
  [cyan]phantom tools vram[/cyan] [-m MODEL]               GPU/RAM snapshot
  [cyan]phantom tools audit[/cyan] [DIR]                   classify + sensitivity counts
  [cyan]phantom tools prompt[/cyan]                        interactive template fill

[bold]Server[/bold]
  [cyan]phantom api serve[/cyan] [--host H] [--port P] [--reload]   FastAPI (:8000)

[bold]Chain of custody[/bold]
  [cyan]phantom resolve[/cyan] -o DAG_OUT PSEUDONYM [--verify] [--list] [--map PATH]

[bold]Meta[/bold]
  [cyan]phantom version[/cyan]
  [cyan]phantom --install-completion[/cyan]                 bash / zsh / fish

[bold]Just recipes[/bold]   [dim](repo root)[/dim]
  [cyan]just demo[/cyan]   [cyan]just doctor[/cyan]   [cyan]just api[/cyan]   [cyan]just up[/cyan]   [cyan]just ps[/cyan]
  [cyan]just playground[/cyan]   [cyan]just test[/cyan]

[dim]Docs: README.md · docs/SPRINT.md · phantom <cmd> --help[/dim]
"""


def print_cheat() -> None:
    """Print the cheat sheet (Rich-formatted when stdout is a TTY)."""
    Console().print(CHEAT_SHEET)
