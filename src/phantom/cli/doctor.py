#!/usr/bin/env python3
"""
phantom doctor — Comprehensive diagnostic toolkit.

Checks every component of the Phantom stack and reports health status
in a colour-coded table.  Exits with a non-zero code if any critical
component is unavailable.

Usage:
    phantom doctor                    Full diagnostics
    phantom doctor --verbose          Include detailed error messages
    phantom doctor --providers-only   Only check LLM providers
"""

import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import typer
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

app = typer.Typer(help="Diagnose Phantom stack health")
console = Console()

# ── Severity levels ─────────────────────────────────────────────────

CRITICAL = "critical"
HIGH = "high"
MEDIUM = "medium"
LOW = "low"

SEVERITY_ORDER = {CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3}


@dataclass
class CheckResult:
    """Result of a single diagnostic check."""

    name: str
    status: bool | None  # True=ok, False=fail, None=skipped
    detail: str = ""
    severity: str = MEDIUM
    duration: float = 0.0
    suggestion: str = ""


# ── Render helpers ──────────────────────────────────────────────────


def _make_group(title: str, icon: str) -> None:
    console.print()
    console.print(Rule(style="dim"))
    console.print(f"  {icon} [bold]{title}[/]")
    console.print(Rule(style="dim"))


def _render_results(results: list[CheckResult], group_title: str) -> None:
    """Render a list of checks as a compact table."""
    tbl = Table(show_header=False, box=None, padding=(0, 2))
    tbl.add_column("Status", width=4)
    tbl.add_column("Check", style="bold", width=24)
    tbl.add_column("Detail", width=60, no_wrap=False)

    for r in results:
        if r.status is True:
            status_str = "[green]✅[/]"
        elif r.status is False:
            status_str = "[red]❌[/]"
        else:
            status_str = "[dim]⬜[/]"

        detail = r.detail
        if not r.status and r.suggestion:
            detail += f"  [dim]({r.suggestion})[/]"

        tbl.add_row(status_str, r.name, detail)

    console.print(tbl)


def _critical_count(results: list[CheckResult]) -> int:
    """Count critical failures."""
    return sum(1 for r in results if r.status is False and r.severity == CRITICAL)


def _failure_count(results: list[CheckResult]) -> int:
    """Count all failures."""
    return sum(1 for r in results if r.status is False)


def _ok(msg: str) -> None:
    console.print(f"  [green]✓[/] {msg}")


def _warn(msg: str) -> None:
    console.print(f"  [yellow]⚠[/] {msg}")


def _fail(msg: str) -> None:
    console.print(f"  [red]✗[/] {msg}")


# ── Individual checks ───────────────────────────────────────────────


def _check_python() -> CheckResult:
    """Python version & platform."""
    v = sys.version_info
    ok = v.major >= 3 and v.minor >= 10
    return CheckResult(
        name="Python",
        status=ok,
        detail=f"{v.major}.{v.minor}.{v.micro} ({platform.machine()})",
        severity=CRITICAL,
        suggestion="Install Python 3.10+ (recommended: 3.11 or 3.12)" if not ok else "",
    )


def _check_platform() -> CheckResult:
    """OS info."""
    return CheckResult(
        name="Platform",
        status=True,
        detail=f"{platform.system()} {platform.release()}",
        severity=LOW,
    )


def _check_ram() -> CheckResult:
    """RAM usage."""
    try:
        import psutil

        mem = psutil.virtual_memory()
        used_gb = mem.used / 1024**3
        total_gb = mem.total / 1024**3
        pct = mem.percent
        ok = pct < 90
        return CheckResult(
            name="RAM",
            status=ok,
            detail=f"{used_gb:.1f} / {total_gb:.1f} GB ({pct:.0f}%)",
            severity=HIGH,
            suggestion="Free memory or add swap" if not ok else "",
        )
    except ImportError:
        return CheckResult(name="RAM", status=None, detail="psutil not installed", severity=LOW)


def _check_cpu() -> CheckResult:
    """CPU cores & load."""
    try:
        import psutil

        cores = psutil.cpu_count()
        load = psutil.getloadavg()
        # load average relative to core count
        ok = load[0] < cores * 1.5 if cores else True
        return CheckResult(
            name="CPU",
            status=ok,
            detail=f"{cores} cores, load: {load[0]:.1f} / {load[1]:.1f} / {load[2]:.1f}",
            severity=HIGH,
            suggestion="Close background processes" if not ok else "",
        )
    except ImportError:
        return CheckResult(name="CPU", status=None, detail="psutil not installed", severity=LOW)


def _check_disk() -> CheckResult:
    """Disk usage on the project partition."""
    try:
        import psutil

        # Check the partition where the phantom package lives
        path = Path(__file__).resolve()
        while path.parent != path:
            if path.is_mount():
                break
            path = path.parent
        usage = psutil.disk_usage(str(path))
        free_gb = usage.free / 1024**3
        pct = usage.percent
        ok = pct < 90
        return CheckResult(
            name="Disk",
            status=ok,
            detail=f"{free_gb:.1f} GB free ({pct:.0f}% used)",
            severity=HIGH,
            suggestion="Free up disk space" if not ok else "",
        )
    except ImportError:
        return CheckResult(name="Disk", status=None, detail="psutil not installed", severity=LOW)


def _check_gpu() -> CheckResult:
    """GPU / VRAM via nvidia-smi."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,driver_version",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return CheckResult(
                name="GPU",
                status=None,
                detail="No NVIDIA GPU detected",
                severity=LOW,
            )
        lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        if not lines:
            return CheckResult(name="GPU", status=None, detail="No GPU data", severity=LOW)
        parts = lines[0].split(", ")
        if len(parts) >= 4:
            name, total_mb, used_mb, driver = parts[0], parts[1], parts[2], parts[3]
            used_gb = float(used_mb) / 1024
            total_gb = float(total_mb) / 1024
            pct = (float(used_mb) / float(total_mb) * 100) if float(total_mb) > 0 else 0
            ok = pct < 90
            return CheckResult(
                name="GPU",
                status=ok,
                detail=f"{name} · {used_gb:.1f}/{total_gb:.1f} GB · driver {driver}",
                severity=MEDIUM,
                suggestion="" if ok else "Free GPU memory",
            )
        return CheckResult(name="GPU", status=None, detail=lines[0][:60], severity=LOW)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return CheckResult(name="GPU", status=None, detail="nvidia-smi not available", severity=LOW)
    except Exception as exc:
        return CheckResult(name="GPU", status=None, detail=f"Error: {exc}", severity=LOW)


# ── Provider checks ─────────────────────────────────────────────────


def _check_local_llm() -> CheckResult:
    """Check local llama.cpp server."""
    base_url = os.environ.get("LLAMACPP_URL", "http://localhost:8080")
    try:
        import httpx

        start = time.perf_counter()
        r = httpx.get(f"{base_url}/health", timeout=3.0)
        elapsed = time.perf_counter() - start
        if r.status_code == 200:
            return CheckResult(
                name="Local LLM",
                status=True,
                detail=f"{base_url} · {elapsed * 1000:.0f} ms",
                severity=MEDIUM,
            )
        return CheckResult(
            name="Local LLM",
            status=False,
            detail=f"{base_url} → HTTP {r.status_code}",
            severity=MEDIUM,
            suggestion="Check if llama.cpp server is running",
        )
    except ImportError:
        return CheckResult(
            name="Local LLM",
            status=None,
            detail="httpx not installed — cannot check connectivity",
            severity=LOW,
        )
    except Exception as exc:
        return CheckResult(
            name="Local LLM",
            status=False,
            detail=str(exc).split(":")[0][:50],
            severity=MEDIUM,
            suggestion="Start llama.cpp or set LLAMACPP_URL",
        )


def _check_provider_api_key(name: str, env_key: str, label: str) -> CheckResult:
    """Check if a cloud provider's API key is set."""
    value = os.environ.get(env_key, "").strip()
    if not value:
        return CheckResult(
            name=label,
            status=None,
            detail=f"${env_key} not set",
            severity=MEDIUM,
            suggestion=f"Set {env_key}=sk-…",
        )
    # Sanity check: key should look plausible
    if len(value) < 8:
        return CheckResult(
            name=label,
            status=False,
            detail=f"${env_key} looks invalid (too short)",
            severity=MEDIUM,
        )
    # Mask the key for display
    masked = value[:8] + "…" + value[-4:] if len(value) > 14 else "(set)"
    return CheckResult(
        name=label,
        status=True,
        detail=f"${env_key} {masked}",
        severity=MEDIUM,
    )


def _test_provider_connectivity(name: str) -> CheckResult:
    """Actually test a provider with a tiny prompt, using the registry."""
    try:
        from phantom.providers.registry import get_provider
    except ImportError:
        return CheckResult(
            name=f"  └ test {name}",
            status=None,
            detail="phantom.providers not importable",
            severity=LOW,
        )

    try:
        provider = get_provider(name)
        start = time.perf_counter()
        response = provider.generate(
            messages=[{"role": "user", "content": "Say 'ok'"}],
            max_tokens=10,
        )
        elapsed = time.perf_counter() - start
        text = response.get("content", response.get("text", ""))
        ok = bool(text)
        return CheckResult(
            name=f"  └ test {name}",
            status=ok,
            detail=f"{elapsed * 1000:.0f} ms"
            if ok
            else f"empty response in {elapsed * 1000:.0f} ms",
            severity=MEDIUM,
            suggestion="Check provider credentials or network" if not ok else "",
        )
    except Exception as exc:
        return CheckResult(
            name=f"  └ test {name}",
            status=False,
            detail=str(exc).split(":")[0][:50],
            severity=MEDIUM,
            suggestion="Check provider URL, API key, and network",
        )


# ── Vector store checks ─────────────────────────────────────────────


def _check_faiss() -> CheckResult:
    """Check FAISS library availability."""
    try:
        import faiss  # noqa: F401
    except ImportError:
        return CheckResult(
            name="FAISS lib",
            status=False,
            detail="faiss package not installed",
            severity=HIGH,
            suggestion="pip install faiss-cpu",
        )

    try:
        index = faiss.IndexFlatIP(384)
        index.add(  # pyright: ignore[reportAttributeAccessIssue]
            __import__("numpy").array([[0.5] * 384], dtype="float32")
        )
        return CheckResult(
            name="FAISS lib",
            status=True,
            detail=f"faiss {faiss.__version__} · IndexFlatIP works",
            severity=HIGH,
        )
    except Exception as exc:
        return CheckResult(
            name="FAISS lib",
            status=False,
            detail=f"faiss import failed: {exc}",
            severity=HIGH,
        )


def _check_vector_index() -> CheckResult:
    """Check for existing vector indices on disk."""
    from pathlib import Path

    indices = list(Path("data").glob("*.faiss")) if Path("data").exists() else []
    if not indices:
        return CheckResult(
            name="Vector index",
            status=None,
            detail="No .faiss indices found in data/",
            severity=MEDIUM,
            suggestion="Run 'phantom rag ingest' or POST /vectors/index",
        )

    total = 0
    details: list[str] = []
    for idx_path in sorted(indices):
        try:
            import faiss

            idx = faiss.read_index(str(idx_path))
            n = idx.ntotal
            total += n
            dim = idx.d
            details.append(f"{idx_path.stem}: {n} vec ({dim}d)")
        except Exception:
            details.append(f"{idx_path.stem}: (unreadable)")

    summary = "; ".join(details[:3])
    if len(details) > 3:
        summary += f" … +{len(details) - 3} more"
    return CheckResult(
        name="Vector index",
        status=True if total > 0 else None,
        detail=f"{total} vectors across {len(indices)} index(es): {summary}",
        severity=MEDIUM,
    )


# ── Embedding check ─────────────────────────────────────────────────


def _check_embeddings() -> CheckResult:
    """Check if the embedding model is available."""
    try:
        from sentence_transformers import SentenceTransformer

        # Quick probe — load the model info without full download
        model_name = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        # SentenceTransformer caches on disk; if it's cached this is fast
        # We set a short timeout by checking cache first
        cache_dir = Path.home() / ".cache" / "torch" / "sentence_transformers"
        cached = list(cache_dir.rglob(f"*{model_name}*")) if cache_dir.exists() else []

        if cached:
            return CheckResult(
                name="Embeddings",
                status=True,
                detail=f"{model_name} (cached)",
                severity=HIGH,
            )

        # Model not cached — fast load test
        try:
            model = SentenceTransformer(model_name)
            dim = model.get_sentence_embedding_dimension()
            return CheckResult(
                name="Embeddings",
                status=True,
                detail=f"{model_name} · dim={dim}",
                severity=HIGH,
            )
        except Exception as exc:
            return CheckResult(
                name="Embeddings",
                status=False,
                detail=f"{exc!s}"[:60],
                severity=HIGH,
                suggestion="Check network or set EMBEDDING_MODEL",
            )
    except ImportError:
        return CheckResult(
            name="Embeddings",
            status=False,
            detail="sentence-transformers not installed",
            severity=HIGH,
            suggestion="pip install sentence-transformers",
        )


# ── Server checks ───────────────────────────────────────────────────


def _check_server(url: str, label: str) -> CheckResult:
    """Ping a server health endpoint."""
    try:
        import httpx

        start = time.perf_counter()
        r = httpx.get(url, timeout=3.0)
        elapsed = time.perf_counter() - start
        if r.status_code == 200:
            return CheckResult(
                name=label,
                status=True,
                detail=f"{url} · {elapsed * 1000:.0f} ms",
                severity=HIGH,
            )
        return CheckResult(
            name=label,
            status=False,
            detail=f"{url} → HTTP {r.status_code}",
            severity=HIGH,
            suggestion="Check if the server is running",
        )
    except ImportError:
        return CheckResult(name=label, status=None, detail="httpx not installed", severity=LOW)
    except Exception as exc:
        return CheckResult(
            name=label,
            status=False,
            detail=str(exc).split(":")[0][:50],
            severity=HIGH,
            suggestion=f"Start the server: just {'api' if '8000' in url else 'cortex'}",
        )


# ── NATS check ──────────────────────────────────────────────────────


def _check_nats() -> CheckResult:
    """Check NATS connectivity (non-fatal)."""
    try:
        import nats
    except ImportError:
        return CheckResult(
            name="NATS",
            status=None,
            detail="nats-py not installed (non-fatal)",
            severity=LOW,
        )

    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    try:
        import asyncio

        async def _try_connect() -> bool:
            try:
                nc = await nats.connect(nats_url, timeout=2.0)
                await nc.drain()
                return True
            except Exception:
                return False

        ok = asyncio.run(_try_connect())
        return CheckResult(
            name="NATS",
            status=ok,
            detail=nats_url if ok else f"{nats_url} (unreachable)",
            severity=LOW,
            suggestion="Start NATS server or ignore (optional component)" if not ok else "",
        )
    except Exception as exc:
        return CheckResult(
            name="NATS",
            status=None,
            detail=f"Check error: {exc}"[:60],
            severity=LOW,
        )


# ── Core imports check ──────────────────────────────────────────────


def _check_imports() -> CheckResult:
    """Verify that all critical phantom submodules can be imported."""
    modules = [
        "phantom",
        "phantom.core.cortex",
        "phantom.core.embeddings",
        "phantom.rag.vectors",
        "phantom.providers.registry",
    ]
    failed: list[str] = []
    for mod_name in modules:
        try:
            __import__(mod_name)
        except ImportError as e:
            failed.append(f"{mod_name} ({e})")
        except Exception:
            failed.append(mod_name)

    if not failed:
        return CheckResult(
            name="Core imports",
            status=True,
            detail=f"All {len(modules)} modules loaded",
            severity=CRITICAL,
        )
    detail = ", ".join(failed[:3])
    if len(failed) > 3:
        detail += f" … +{len(failed) - 3} more"
    return CheckResult(
        name="Core imports",
        status=False,
        detail=detail,
        severity=CRITICAL,
        suggestion="Install the phantom package: pip install -e .",
    )


# ── Orchestrator ────────────────────────────────────────────────────


@app.callback(invoke_without_command=True)
def doctor(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed messages"),
    providers_only: bool = typer.Option(False, "--providers-only", help="Only check LLM providers"),
):
    """
    Run comprehensive diagnostics on the Phantom stack.

    Reports the health of every component — system resources, LLM providers,
    vector store, embeddings, and API servers — with ❌✅ status indicators.

    Exits with code:
      0 if everything is healthy
      1 if non-critical components have issues
      2 if critical components are failing
    """
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]🩺 Phantom Doctor[/]\n[white]Comprehensive stack diagnostics[/]",
            border_style="cyan",
        )
    )

    all_results: list[CheckResult] = []

    # ── System ───────────────────────────────────────────────────────
    if not providers_only:
        _make_group("System", "💻")
        sys_checks = [
            _check_python(),
            _check_platform(),
            _check_ram(),
            _check_cpu(),
            _check_disk(),
            _check_gpu(),
        ]
        _render_results(sys_checks, "System")
        all_results.extend(sys_checks)

        _make_group("Core Libraries", "📦")
        lib_checks = [
            _check_imports(),
            _check_faiss(),
            _check_embeddings(),
        ]
        _render_results(lib_checks, "Core Libraries")
        all_results.extend(lib_checks)

        _make_group("Vector Store", "🗂️")
        vec_checks = [
            _check_vector_index(),
        ]
        _render_results(vec_checks, "Vector Store")
        all_results.extend(vec_checks)

        _make_group("Servers", "🌐")
        srv_checks = [
            _check_server("http://127.0.0.1:8000/health", "Phantom API (8000)"),
            _check_server("http://127.0.0.1:8087/health", "Cortex API (8087)"),
        ]
        _render_results(srv_checks, "Servers")
        all_results.extend(srv_checks)

        _make_group("Event Bus", "📨")
        nats_checks = [_check_nats()]
        _render_results(nats_checks, "Event Bus")
        all_results.extend(nats_checks)

    # ── Providers ────────────────────────────────────────────────────
    _make_group("LLM Providers", "🤖")
    provider_checks: list[CheckResult] = [
        _check_local_llm(),
        _check_provider_api_key("openai", "OPENAI_API_KEY", "OpenAI"),
        _check_provider_api_key("anthropic", "ANTHROPIC_API_KEY", "Anthropic"),
        _check_provider_api_key("deepseek", "DEEPSEEK_API_KEY", "DeepSeek"),
    ]

    # Test connectivity for cloud providers that have keys set
    for pk_name, env_key in [
        ("openai", "OPENAI_API_KEY"),
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("deepseek", "DEEPSEEK_API_KEY"),
    ]:
        if os.environ.get(env_key, "").strip():
            provider_checks.append(_test_provider_connectivity(pk_name))

    _render_results(provider_checks, "LLM Providers")
    all_results.extend(provider_checks)

    # ── Summary ──────────────────────────────────────────────────────
    crit_fails = _critical_count(all_results)
    total_fails = _failure_count(all_results)
    total_checks = len(all_results)
    ok_count = sum(1 for r in all_results if r.status is True)
    skipped = sum(1 for r in all_results if r.status is None)

    console.print()
    console.print(Rule(style="bold"))

    if crit_fails > 0:
        status_icon = "[red]❌[/]"
        status_msg = f"[red]CRITICAL: {crit_fails} critical failure(s)[/]"
        exit_code = 2
    elif total_fails > 0:
        status_icon = "[yellow]⚠️[/]"
        status_msg = f"[yellow]Degraded: {total_fails} non-critical failure(s)[/]"
        exit_code = 1
    else:
        status_icon = "[green]✅[/]"
        status_msg = "[green]All systems operational[/]"
        exit_code = 0

    summary = Panel.fit(
        f"{status_icon}  {status_msg}\n\n"
        f"  [green]{ok_count} passed[/]"
        f"  [red]{total_fails} failed[/]"
        f"  [dim]{skipped} skipped[/]"
        f"  [bold]{total_checks}[/] total checks\n\n"
        + (
            "[dim]Run with -v for details. Set environment variables or start\n"
            "servers to resolve failures.[/]"
            if total_fails > 0
            else "[dim]Nothing to do — everything looks good![/]"
        ),
        border_style="green" if exit_code == 0 else "yellow" if exit_code == 1 else "red",
    )
    console.print(summary)
    console.print()

    raise typer.Exit(code=exit_code)


def main() -> None:
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
