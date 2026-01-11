#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PROJECTPHANTOM - PROJECT AUDITOR                          ║
║              Enterprise-Level Project Audit & Assessment Engine              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Main engine for comprehensive project auditing with:
- Multi-project scanning
- Git analysis
- Tech stack detection
- Code quality metrics
- Security scanning
- AI-powered insights

Usage:
    python project_auditor.py --path ~/dev/Projects/myproject
    python project_auditor.py --scan ~/dev/Projects --format json
    python project_auditor.py --compare proj1 proj2
"""

import argparse
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

try:
    from rich import print as rprint
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from metrics_schema import (
    ActivityMetrics,
    AIInsights,
    CodeMetrics,
    ComplexityMetrics,
    DependencyInfo,
    DependencyMetrics,
    ProjectMetrics,
    ProjectStatus,
    QualityMetrics,
    SecurityMetrics,
    TechCategory,
    TechStackItem,
    TechStackMetrics,
)
from viability_scorer import ViabilityScorer

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

VERSION = "1.0.0"
CODENAME = "PHANTOM-AUDIT"

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Console
console = Console() if RICH_AVAILABLE else None

# Technology signatures for detection
TECH_SIGNATURES = {
    # Languages
    "Cargo.toml": ("Rust", TechCategory.LANGUAGE),
    "package.json": ("JavaScript/Node", TechCategory.LANGUAGE),
    "go.mod": ("Go", TechCategory.LANGUAGE),
    "requirements.txt": ("Python", TechCategory.LANGUAGE),
    "pyproject.toml": ("Python", TechCategory.LANGUAGE),
    "flake.nix": ("Nix", TechCategory.LANGUAGE),
    "*.rs": ("Rust", TechCategory.LANGUAGE),
    "*.py": ("Python", TechCategory.LANGUAGE),
    "*.go": ("Go", TechCategory.LANGUAGE),
    "*.ts": ("TypeScript", TechCategory.LANGUAGE),
    "*.tsx": ("TypeScript", TechCategory.LANGUAGE),
    "*.svelte": ("Svelte", TechCategory.FRAMEWORK),
    # Build tools
    "Makefile": ("Make", TechCategory.BUILD_TOOL),
    "CMakeLists.txt": ("CMake", TechCategory.BUILD_TOOL),
    "meson.build": ("Meson", TechCategory.BUILD_TOOL),
    # Containers
    "Dockerfile": ("Docker", TechCategory.CONTAINER),
    "docker-compose.yml": ("Docker Compose", TechCategory.CONTAINER),
    "docker-compose.yaml": ("Docker Compose", TechCategory.CONTAINER),
    "podman-compose.yml": ("Podman", TechCategory.CONTAINER),
    # CI/CD
    ".github/workflows": ("GitHub Actions", TechCategory.CI_CD),
    ".gitlab-ci.yml": ("GitLab CI", TechCategory.CI_CD),
    "Jenkinsfile": ("Jenkins", TechCategory.CI_CD),
    # Databases
    "prisma/schema.prisma": ("Prisma", TechCategory.DATABASE),
}

# Extension to language mapping
EXT_LANG_MAP = {
    ".py": "Python",
    ".rs": "Rust",
    ".go": "Go",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".nix": "Nix",
    ".svelte": "Svelte",
    ".vue": "Vue",
    ".rb": "Ruby",
    ".java": "Java",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".php": "PHP",
    ".swift": "Swift",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".less": "Less",
    ".md": "Markdown",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
}

# Directories to ignore
IGNORED_DIRS = {
    ".git",
    "node_modules",
    "target",
    "build",
    "dist",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    ".cache",
    ".idea",
    ".vscode",
    "vendor",
    "deps",
    "_build",
    "out",
    ".next",
    ".nuxt",
    "coverage",
}


# ══════════════════════════════════════════════════════════════════════════════
# PROJECT AUDITOR
# ══════════════════════════════════════════════════════════════════════════════


class ProjectAuditor:
    """Enterprise-level project auditor with ML capabilities."""

    def __init__(
        self,
        enable_ai: bool = False,
        ai_url: str = "http://localhost:8080",
        workers: int = 4,
        verbose: bool = False,
    ):
        """
        Initialize ProjectAuditor.

        Args:
            enable_ai: Enable AI-powered analysis
            ai_url: LlamaCpp server URL
            workers: Number of parallel workers
            verbose: Enable verbose output
        """
        self.enable_ai = enable_ai
        self.ai_url = ai_url
        self.workers = workers
        self.verbose = verbose
        self.scorer = ViabilityScorer()

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    def audit_project(self, path: Path) -> ProjectMetrics:
        """
        Run comprehensive audit on a single project.

        Args:
            path: Path to project directory

        Returns:
            Complete ProjectMetrics
        """
        start_time = time.time()
        path = Path(path).resolve()

        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        logger.info(f"Auditing project: {path.name}")

        # Generate unique project ID
        project_id = hashlib.sha256(str(path).encode()).hexdigest()[:12]

        # Initialize metrics
        metrics = ProjectMetrics(project_id=project_id, name=path.name, path=str(path))

        try:
            # Collect all metrics
            metrics.code = self._analyze_code(path)
            metrics.complexity = self._analyze_complexity(path)
            metrics.activity = self._analyze_git(path)
            metrics.quality = self._analyze_quality(path)
            metrics.tech_stack = self._analyze_tech_stack(path)
            metrics.dependencies = self._analyze_dependencies(path)
            metrics.security = self._analyze_security(path)

            # Determine project status
            metrics.status = self._determine_status(metrics)

            # Calculate viability score
            metrics.viability = self.scorer.calculate_score(metrics)

            # AI analysis (optional)
            if self.enable_ai:
                metrics.ai_insights = self._run_ai_analysis(path, metrics)

        except Exception as e:
            logger.error(f"Error auditing {path.name}: {e}")
            metrics.errors.append(str(e))

        # Record timing
        metrics.scan_duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Audit complete: {path.name} ({metrics.scan_duration_ms:.1f}ms)")

        return metrics

    def scan_directory(self, root: Path, max_depth: int = 2) -> list[ProjectMetrics]:
        """
        Scan directory for projects and audit each.

        Args:
            root: Root directory to scan
            max_depth: Maximum directory depth

        Returns:
            List of ProjectMetrics for all discovered projects
        """
        root = Path(root).resolve()
        projects = self._discover_projects(root, max_depth)

        logger.info(f"Discovered {len(projects)} projects in {root}")

        results = []

        if RICH_AVAILABLE and console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            ) as progress:
                task = progress.add_task("Auditing projects...", total=len(projects))

                for project_path in projects:
                    progress.update(
                        task, description=f"Auditing {project_path.name}..."
                    )
                    try:
                        metrics = self.audit_project(project_path)
                        results.append(metrics)
                    except Exception as e:
                        logger.error(f"Failed to audit {project_path}: {e}")
                    progress.advance(task)
        else:
            for i, project_path in enumerate(projects, 1):
                print(f"[{i}/{len(projects)}] Auditing {project_path.name}...")
                try:
                    metrics = self.audit_project(project_path)
                    results.append(metrics)
                except Exception as e:
                    logger.error(f"Failed to audit {project_path}: {e}")

        # Sort by viability score
        results.sort(
            key=lambda m: m.viability.score if m.viability else 0, reverse=True
        )

        return results

    def _discover_projects(self, root: Path, max_depth: int) -> list[Path]:
        """Discover project directories within root."""
        projects = []

        # Project indicators
        indicators = {
            "Cargo.toml",
            "package.json",
            "go.mod",
            "pyproject.toml",
            "requirements.txt",
            "flake.nix",
            "setup.py",
            "pom.xml",
            "build.gradle",
            "Makefile",
            "CMakeLists.txt",
        }

        def scan_dir(path: Path, depth: int):
            if depth > max_depth:
                return
            if path.name in IGNORED_DIRS or path.name.startswith("."):
                return

            try:
                children = list(path.iterdir())
            except PermissionError:
                return

            # Check if this is a project (has project indicator)
            child_names = {c.name for c in children}
            if child_names & indicators:
                projects.append(path)
                return  # Don't scan subdirectories of projects

            # Check for .git as project indicator
            if ".git" in child_names:
                projects.append(path)
                return

            # Recurse into subdirectories
            for child in children:
                if child.is_dir():
                    scan_dir(child, depth + 1)

        scan_dir(root, 0)
        return projects

    # ══════════════════════════════════════════════════════════════════════════
    # CODE ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════

    def _analyze_code(self, path: Path) -> CodeMetrics:
        """Analyze code metrics."""
        metrics = CodeMetrics()
        lines_by_lang: dict[str, int] = {}
        files_by_lang: dict[str, int] = {}
        file_sizes: list[int] = []

        for file in self._iter_files(path):
            ext = file.suffix.lower()
            lang = EXT_LANG_MAP.get(ext, "Other")

            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()

                total = len(lines)
                code = sum(
                    1 for l in lines if l.strip() and not self._is_comment(l, ext)
                )
                comments = sum(1 for l in lines if self._is_comment(l, ext))
                blank = sum(1 for l in lines if not l.strip())

                metrics.total_lines += total
                metrics.code_lines += code
                metrics.comment_lines += comments
                metrics.blank_lines += blank
                metrics.file_count += 1

                file_sizes.append(total)

                lines_by_lang[lang] = lines_by_lang.get(lang, 0) + total
                files_by_lang[lang] = files_by_lang.get(lang, 0) + 1

            except Exception as e:
                logger.debug(f"Error reading {file}: {e}")

        metrics.lines_by_language = lines_by_lang
        metrics.files_by_language = files_by_lang

        if file_sizes:
            metrics.avg_file_size = sum(file_sizes) / len(file_sizes)
            metrics.max_file_size = max(file_sizes)

        return metrics

    def _is_comment(self, line: str, ext: str) -> bool:
        """Check if line is a comment."""
        stripped = line.strip()
        if not stripped:
            return False

        if ext in {".py", ".sh", ".bash", ".yml", ".yaml", ".nix"}:
            return stripped.startswith("#")
        elif ext in {".js", ".ts", ".tsx", ".go", ".rs", ".java", ".c", ".cpp"}:
            return (
                stripped.startswith("//")
                or stripped.startswith("/*")
                or stripped.startswith("*")
            )

        return False

    def _iter_files(self, path: Path):
        """Iterate over source files in path."""
        code_extensions = set(EXT_LANG_MAP.keys())

        for root_dir, dirs, files in os.walk(path):
            # Prune ignored directories
            dirs[:] = [
                d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")
            ]

            for file in files:
                file_path = Path(root_dir) / file
                if file_path.suffix.lower() in code_extensions:
                    yield file_path

    # ══════════════════════════════════════════════════════════════════════════
    # COMPLEXITY ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════

    def _analyze_complexity(self, path: Path) -> ComplexityMetrics:
        """Analyze code complexity."""
        metrics = ComplexityMetrics()

        # Simple complexity estimation based on control flow
        total_cc = 0
        max_cc = 0
        function_count = 0
        class_count = 0

        for file in self._iter_files(path):
            ext = file.suffix.lower()
            if ext not in {".py", ".rs", ".js", ".ts", ".go"}:
                continue

            try:
                content = file.read_text(encoding="utf-8", errors="ignore")

                # Count functions/classes
                if ext == ".py":
                    function_count += len(
                        re.findall(r"^def \w+", content, re.MULTILINE)
                    )
                    class_count += len(re.findall(r"^class \w+", content, re.MULTILINE))
                elif ext == ".rs":
                    function_count += len(re.findall(r"fn \w+", content))
                    class_count += len(re.findall(r"(struct|enum|impl) \w+", content))
                elif ext in {".js", ".ts"}:
                    function_count += len(
                        re.findall(r"function \w+|const \w+ = .*=>", content)
                    )
                    class_count += len(re.findall(r"class \w+", content))
                elif ext == ".go":
                    function_count += len(re.findall(r"func \w+", content))
                    class_count += len(re.findall(r"type \w+ struct", content))

                # Estimate cyclomatic complexity (very rough)
                # Count decision points: if, for, while, case, &&, ||
                cc = 1  # Base
                cc += len(
                    re.findall(r"\bif\b|\bfor\b|\bwhile\b|\bcase\b|\bcatch\b", content)
                )
                cc += len(re.findall(r"&&|\|\|", content))

                total_cc += cc
                max_cc = max(max_cc, cc)

            except Exception as e:
                logger.debug(f"Error analyzing complexity of {file}: {e}")

        metrics.functions_count = function_count
        metrics.classes_count = class_count
        metrics.cyclomatic_complexity_max = max_cc

        if function_count > 0:
            metrics.cyclomatic_complexity_avg = total_cc / function_count
            # Simple maintainability index estimation
            # MI = 171 - 5.2 * ln(aveV) - 0.23 * aveG - 16.2 * ln(aveLOC)
            avg_loc = metrics.cyclomatic_complexity_avg * 10  # Rough estimate
            if avg_loc > 0:
                metrics.maintainability_index = max(
                    0,
                    min(
                        100,
                        171
                        - 5.2 * 3
                        - 0.23 * metrics.cyclomatic_complexity_avg
                        - 16.2 * (avg_loc / 10),
                    ),
                )

        return metrics

    # ══════════════════════════════════════════════════════════════════════════
    # GIT ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════

    def _analyze_git(self, path: Path) -> ActivityMetrics:
        """Analyze git activity."""
        metrics = ActivityMetrics()
        git_dir = path / ".git"

        if not git_dir.exists():
            return metrics

        metrics.is_git_repo = True

        try:
            # Last commit date
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ct"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                ts = int(result.stdout.strip())
                last_commit = datetime.fromtimestamp(ts, tz=UTC)
                metrics.last_commit_date = last_commit
                metrics.days_since_last_commit = (
                    datetime.now(tz=UTC) - last_commit
                ).days

            # Total commits
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                metrics.commits_total = int(result.stdout.strip())

            # Commits by time period
            for days, attr in [
                (7, "commits_last_7_days"),
                (30, "commits_last_30_days"),
                (90, "commits_last_90_days"),
                (365, "commits_last_year"),
            ]:
                result = subprocess.run(
                    ["git", "rev-list", "--count", f"--since={days}.days.ago", "HEAD"],
                    cwd=path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    setattr(metrics, attr, int(result.stdout.strip()))

            # Contributors
            result = subprocess.run(
                ["git", "shortlog", "-sn", "--all"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                contributors = [
                    l for l in result.stdout.strip().split("\n") if l.strip()
                ]
                metrics.total_contributors = len(contributors)

            # Active contributors (last 30 days)
            result = subprocess.run(
                ["git", "shortlog", "-sn", "--since=30.days.ago"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                active = [l for l in result.stdout.strip().split("\n") if l.strip()]
                metrics.active_contributors_30d = len(active)

            # Active contributors (last year)
            result = subprocess.run(
                ["git", "shortlog", "-sn", "--since=1.year.ago"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                active = [l for l in result.stdout.strip().split("\n") if l.strip()]
                metrics.active_contributors_year = len(active)

            # Calculate frequency score
            if metrics.days_since_last_commit < 365 and metrics.commits_last_year > 0:
                # Average commits per day over last year
                metrics.avg_commits_per_day = metrics.commits_last_year / 365
                # Frequency score: more recent + more frequent = higher score
                recency_factor = max(0, 100 - metrics.days_since_last_commit) / 100
                frequency_factor = min(1, metrics.commits_last_year / 100)
                metrics.commit_frequency_score = (
                    recency_factor * 0.5 + frequency_factor * 0.5
                ) * 100

        except Exception as e:
            logger.error(f"Error analyzing git: {e}")
            metrics.is_git_repo = False

        return metrics

    # ══════════════════════════════════════════════════════════════════════════
    # QUALITY ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════

    def _analyze_quality(self, path: Path) -> QualityMetrics:
        """Analyze code quality indicators."""
        metrics = QualityMetrics()

        # Check for documentation files
        readme_candidates = [
            "README.md",
            "readme.md",
            "README.txt",
            "README",
            "README.rst",
        ]
        for readme_name in readme_candidates:
            readme_path = path / readme_name
            if readme_path.exists():
                metrics.readme_exists = True
                metrics.readme_quality = self._score_readme(readme_path)
                break

        metrics.has_changelog = (path / "CHANGELOG.md").exists() or (
            path / "HISTORY.md"
        ).exists()
        metrics.has_contributing = (path / "CONTRIBUTING.md").exists()
        metrics.has_license = any(
            (path / l).exists()
            for l in ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
        )

        # Check for test files
        test_files = 0
        source_files = 0
        for file in self._iter_files(path):
            source_files += 1
            name = file.stem.lower()
            parent = file.parent.name.lower()
            if (
                "test" in name
                or "spec" in name
                or parent in {"tests", "test", "spec", "__tests__"}
            ):
                test_files += 1

        if source_files > 0:
            metrics.test_file_ratio = test_files / source_files
            # Estimate coverage from test ratio (rough heuristic)
            metrics.test_coverage_estimate = min(100, metrics.test_file_ratio * 200)

        # Check for linting/formatting
        linting_files = [
            ".eslintrc",
            ".eslintrc.js",
            ".eslintrc.json",
            "eslint.config.js",
            "ruff.toml",
            "pyproject.toml",
            ".flake8",
            ".pylintrc",
            "rustfmt.toml",
            ".rustfmt.toml",
            "clippy.toml",
            ".prettierrc",
            ".prettierrc.js",
            "biome.json",
        ]
        metrics.linting_configured = any((path / f).exists() for f in linting_files)

        # Type checking
        type_files = ["tsconfig.json", "py.typed", "mypy.ini"]
        metrics.type_checking_configured = any((path / f).exists() for f in type_files)

        # Check pyproject.toml for mypy config
        if (path / "pyproject.toml").exists():
            try:
                content = (path / "pyproject.toml").read_text()
                if "mypy" in content or "pyright" in content:
                    metrics.type_checking_configured = True
            except Exception:
                pass

        # Overall documentation score
        doc_score = 0
        if metrics.readme_exists:
            doc_score += 30 + (metrics.readme_quality * 0.3)
        if metrics.has_changelog:
            doc_score += 15
        if metrics.has_contributing:
            doc_score += 10
        if metrics.has_license:
            doc_score += 10
        if metrics.linting_configured:
            doc_score += 10
        if metrics.type_checking_configured:
            doc_score += 10

        metrics.documentation_score = min(100, doc_score)

        return metrics

    def _score_readme(self, path: Path) -> float:
        """Score README quality (0-100)."""
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            score = 20  # Base score for existing

            length = len(content)
            if length > 500:
                score += 10
            if length > 2000:
                score += 10
            if length > 5000:
                score += 10

            # Has headers
            if re.search(r"^#+\s", content, re.MULTILINE):
                score += 10

            # Has code blocks
            if "```" in content:
                score += 10

            # Has installation section
            if re.search(r"install|setup|getting started", content, re.IGNORECASE):
                score += 10

            # Has usage section
            if re.search(r"usage|example|quick start", content, re.IGNORECASE):
                score += 10

            # Has images/badges
            if "![" in content:
                score += 5

            return min(100, score)
        except Exception:
            return 0

    # ══════════════════════════════════════════════════════════════════════════
    # TECH STACK ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════

    def _analyze_tech_stack(self, path: Path) -> TechStackMetrics:
        """Analyze technology stack."""
        metrics = TechStackMetrics()
        detected: list[TechStackItem] = []

        # Check for tech signatures
        for signature, (name, category) in TECH_SIGNATURES.items():
            if signature.startswith("*."):
                # File extension check
                ext = signature[1:]
                if any(path.rglob(f"*{ext}")):
                    detected.append(TechStackItem(name=name, category=category))
            else:
                # File/dir existence check
                if (path / signature).exists():
                    detected.append(TechStackItem(name=name, category=category))

        # Parse package.json for frameworks
        if (path / "package.json").exists():
            try:
                with open(path / "package.json") as f:
                    pkg = json.load(f)
                    all_deps = {
                        **pkg.get("dependencies", {}),
                        **pkg.get("devDependencies", {}),
                    }

                    framework_map = {
                        "react": "React",
                        "next": "Next.js",
                        "svelte": "Svelte",
                        "vue": "Vue",
                        "@angular/core": "Angular",
                        "express": "Express",
                        "fastify": "Fastify",
                        "nestjs": "NestJS",
                        "tauri": "Tauri",
                        "electron": "Electron",
                        "astro": "Astro",
                    }

                    for dep, framework in framework_map.items():
                        if dep in all_deps:
                            detected.append(
                                TechStackItem(
                                    name=framework, category=TechCategory.FRAMEWORK
                                )
                            )
            except Exception:
                pass

        # Parse Cargo.toml for Rust frameworks
        if (path / "Cargo.toml").exists():
            try:
                content = (path / "Cargo.toml").read_text()
                rust_frameworks = {
                    "axum": "Axum",
                    "actix-web": "Actix",
                    "rocket": "Rocket",
                    "tokio": "Tokio",
                    "tauri": "Tauri",
                    "bevy": "Bevy",
                    "sqlx": "SQLx",
                    "diesel": "Diesel",
                    "sea-orm": "SeaORM",
                }
                for crate, name in rust_frameworks.items():
                    if crate in content:
                        detected.append(
                            TechStackItem(name=name, category=TechCategory.FRAMEWORK)
                        )
            except Exception:
                pass

        # Deduplicate and categorize
        seen = set()
        for item in detected:
            if item.name not in seen:
                seen.add(item.name)
                metrics.all_technologies.append(item)

                if item.category == TechCategory.LANGUAGE:
                    metrics.primary_languages.append(item.name)
                elif item.category == TechCategory.FRAMEWORK:
                    metrics.frameworks.append(item.name)
                elif item.category == TechCategory.BUILD_TOOL:
                    metrics.build_tools.append(item.name)
                elif item.category == TechCategory.CONTAINER:
                    metrics.containers.append(item.name)
                elif item.category == TechCategory.CI_CD:
                    metrics.ci_cd_tools.append(item.name)
                elif item.category == TechCategory.DATABASE:
                    metrics.databases.append(item.name)

        # Calculate modernity score
        modern_tech = {
            "Rust",
            "Go",
            "TypeScript",
            "Svelte",
            "Tauri",
            "Nix",
            "Next.js",
            "Astro",
        }
        modern_count = len(
            set(metrics.primary_languages + metrics.frameworks) & modern_tech
        )
        metrics.stack_modernity_score = min(100, 40 + modern_count * 15)

        return metrics

    # ══════════════════════════════════════════════════════════════════════════
    # DEPENDENCY ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════

    def _analyze_dependencies(self, path: Path) -> DependencyMetrics:
        """Analyze project dependencies."""
        metrics = DependencyMetrics()

        # NPM dependencies
        if (path / "package.json").exists():
            try:
                with open(path / "package.json") as f:
                    pkg = json.load(f)
                    deps = pkg.get("dependencies", {})
                    dev_deps = pkg.get("devDependencies", {})

                    metrics.direct_dependencies = len(deps)
                    metrics.dev_dependencies = len(dev_deps)
                    metrics.total_dependencies = len(deps) + len(dev_deps)

                    for name, version in deps.items():
                        metrics.dependencies.append(
                            DependencyInfo(
                                name=name,
                                version=version.replace("^", "").replace("~", ""),
                            )
                        )
            except Exception:
                pass

        # Cargo dependencies
        if (path / "Cargo.toml").exists():
            try:
                content = (path / "Cargo.toml").read_text()
                # Simple regex to count dependencies
                dep_matches = re.findall(r"^\s*(\w[\w-]*)\s*=", content, re.MULTILINE)
                # Filter out section headers
                dep_count = len(
                    [
                        d
                        for d in dep_matches
                        if d not in ["package", "dependencies", "features", "workspace"]
                    ]
                )
                metrics.total_dependencies = max(metrics.total_dependencies, dep_count)
            except Exception:
                pass

        # Python dependencies
        for req_file in ["requirements.txt", "requirements.in"]:
            if (path / req_file).exists():
                try:
                    content = (path / req_file).read_text()
                    deps = [
                        l.strip()
                        for l in content.splitlines()
                        if l.strip() and not l.strip().startswith("#")
                    ]
                    metrics.total_dependencies = max(
                        metrics.total_dependencies, len(deps)
                    )
                except Exception:
                    pass

        # Simple freshness heuristic (would need API calls for real check)
        # For now, estimate based on last commit
        metrics.dependency_freshness = 50  # Default

        return metrics

    # ══════════════════════════════════════════════════════════════════════════
    # SECURITY ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════

    def _analyze_security(self, path: Path) -> SecurityMetrics:
        """Analyze security indicators."""
        metrics = SecurityMetrics()

        # Check for security files
        metrics.has_security_policy = (path / "SECURITY.md").exists()
        metrics.has_dependabot = (path / ".github" / "dependabot.yml").exists()
        metrics.has_code_scanning = (
            path / ".github" / "workflows" / "codeql.yml"
        ).exists()

        # Simple secrets detection (very basic)
        secret_patterns = [
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'secret[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'password\s*=\s*["\'][^"\']+["\']',
            r'aws_access_key_id\s*=\s*["\'][^"\']+["\']',
            r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
        ]

        secrets_found = 0
        for file in self._iter_files(path):
            # Skip common false positive files
            if file.name in {"package-lock.json", "yarn.lock", "Cargo.lock"}:
                continue

            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
                for pattern in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    secrets_found += len(matches)
            except Exception:
                pass

        metrics.secrets_detected = secrets_found

        # Calculate security score
        score = 100
        if secrets_found > 0:
            score -= min(40, secrets_found * 10)
        if not metrics.has_security_policy:
            score -= 10
        if not metrics.has_dependabot:
            score -= 10

        metrics.security_score = max(0, score)

        return metrics

    # ══════════════════════════════════════════════════════════════════════════
    # AI ANALYSIS (OPTIONAL)
    # ══════════════════════════════════════════════════════════════════════════

    def _run_ai_analysis(
        self, path: Path, metrics: ProjectMetrics
    ) -> AIInsights | None:
        """Run AI-powered analysis using local LLM."""
        # This will be expanded with cortex.py integration
        logger.info("AI analysis is enabled but not yet fully implemented")
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _determine_status(self, metrics: ProjectMetrics) -> ProjectStatus:
        """Determine project lifecycle status."""
        days = metrics.activity.days_since_last_commit
        commits = metrics.activity.commits_last_year

        if days < 180 and commits > 10:
            return ProjectStatus.ACTIVE
        elif days < 365 and commits > 5:
            return ProjectStatus.MAINTENANCE
        elif days > 730:
            return ProjectStatus.DEPRECATED
        elif days > 365:
            return ProjectStatus.ARCHIVED
        else:
            return ProjectStatus.UNKNOWN


# ══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ══════════════════════════════════════════════════════════════════════════════


def generate_report(results: list[ProjectMetrics], format: str = "table") -> str:
    """Generate audit report in specified format."""

    if format == "json":
        return json.dumps(
            [m.model_dump(mode="json") for m in results], indent=2, default=str
        )

    elif format == "markdown":
        lines = ["# Project Audit Report", ""]
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Projects Audited**: {len(results)}")
        lines.append("")

        for m in results:
            score = m.viability.score if m.viability else 0
            grade = m.viability.grade if m.viability else "N/A"
            rec = m.viability.recommendation.value if m.viability else "unknown"

            lines.append(f"## {m.name}")
            lines.append(f"- **Score**: {score:.1f}/100 ({grade})")
            lines.append(f"- **Recommendation**: {rec}")
            lines.append(f"- **Status**: {m.status.value}")
            lines.append(
                f"- **Tech Stack**: {', '.join(m.tech_stack.primary_languages[:3])}"
            )
            lines.append(
                f"- **Last Commit**: {m.activity.days_since_last_commit} days ago"
            )
            lines.append("")

        return "\n".join(lines)

    else:  # table
        if RICH_AVAILABLE and console:
            table = Table(title="Project Audit Results")
            table.add_column("Project", style="cyan")
            table.add_column("Score", justify="right")
            table.add_column("Grade", justify="center")
            table.add_column("Status", style="yellow")
            table.add_column("Tech", style="green")
            table.add_column("Last Commit", justify="right")
            table.add_column("Recommendation", style="magenta")

            for m in results:
                score = m.viability.score if m.viability else 0
                grade = m.viability.grade if m.viability else "N/A"
                rec = m.viability.recommendation.value if m.viability else "unknown"
                tech = ", ".join(m.tech_stack.primary_languages[:2]) or "Unknown"
                days = str(m.activity.days_since_last_commit)

                table.add_row(
                    m.name[:25],
                    f"{score:.1f}",
                    grade,
                    m.status.value,
                    tech[:20],
                    days,
                    rec.replace("_", " ").title(),
                )

            console.print(table)
            return ""
        else:
            lines = []
            lines.append(
                f"{'Project':<25} | {'Score':>6} | {'Grade':^5} | {'Status':<12} | {'Tech':<15} | {'Days':>5} | Recommendation"
            )
            lines.append("-" * 100)

            for m in results:
                score = m.viability.score if m.viability else 0
                grade = m.viability.grade if m.viability else "N/A"
                rec = m.viability.recommendation.value if m.viability else "unknown"
                tech = ", ".join(m.tech_stack.primary_languages[:2])[:15] or "Unknown"

                lines.append(
                    f"{m.name[:25]:<25} | {score:>6.1f} | {grade:^5} | {m.status.value:<12} | "
                    f"{tech:<15} | {m.activity.days_since_last_commit:>5} | {rec}"
                )

            return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ══════════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="ProjectPhantom - Enterprise Project Audit Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --path ~/dev/myproject                  # Audit single project
  %(prog)s --scan ~/dev/Projects                   # Scan multiple projects
  %(prog)s --scan ~/dev --format json -o report.json  # Save JSON report
  %(prog)s --path ~/dev/proj --ai                  # Enable AI analysis
        """,
    )

    parser.add_argument("--path", "-p", help="Path to single project to audit")
    parser.add_argument("--scan", "-s", help="Directory to scan for projects")
    parser.add_argument(
        "--format",
        "-f",
        choices=["table", "json", "markdown"],
        default="table",
        help="Output format",
    )
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--ai", action="store_true", help="Enable AI-powered analysis")
    parser.add_argument(
        "--ai-url", default="http://localhost:8080", help="LlamaCpp server URL"
    )
    parser.add_argument(
        "--max-depth", type=int, default=2, help="Max depth for project discovery"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    args = parser.parse_args()

    if not args.path and not args.scan:
        parser.print_help()
        sys.exit(1)

    auditor = ProjectAuditor(
        enable_ai=args.ai, ai_url=args.ai_url, verbose=args.verbose
    )

    if args.path:
        metrics = auditor.audit_project(Path(args.path))
        results = [metrics]
    else:
        results = auditor.scan_directory(Path(args.scan), max_depth=args.max_depth)

    # Generate report
    report = generate_report(results, args.format)

    if report:  # Table format prints directly
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)

    # Print summary
    if results:
        avg_score = sum(m.viability.score for m in results if m.viability) / len(
            results
        )
        print(
            f"\n📊 Summary: {len(results)} projects audited, avg viability: {avg_score:.1f}/100"
        )


if __name__ == "__main__":
    main()
