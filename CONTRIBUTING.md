# The Art of Contributing

Great infrastructure is built through deliberate, thoughtful collaboration—the kind that emerges when curious minds align to solve complex problems.

This document isn't a rigid bureaucratic rulebook. It is a map of our engineering culture, outlining how we build and how we expect partners like you to collaborate within the Phantom ecosystem.

## The Mutual Agreement

When you contribute, you enter a professional dialogue. We expect clarity, intellectual honesty, and adherence to our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## The Landscape (Getting Started)

### Prerequisites

- **Python 3.11+**
- **Git**
- **Nix** (recommended — provides a complete, reproducible environment)
- **Rust 1.75+** (only needed for IntelAgent or desktop app work)

### Setup

```bash
git clone https://github.com/kernelcore/phantom.git
cd phantom

# Option A: Nix (recommended)
nix develop
pre-commit install

# Option B: pip
python3.11 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

Verify:

```bash
pytest
ruff check src/
```

---

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/my-feature
# or: fix/bug-description, docs/update-x, refactor/cleanup-y
```

### 2. Make Changes

- Read the relevant code before modifying it
- Follow the [code guidelines](#code-guidelines) below
- Write tests for new functionality

### 3. Test

```bash
pytest                                   # all tests
pytest --cov=phantom --cov-report=html   # with coverage
pytest tests/unit/ -v                    # unit tests only
pytest -k "test_sentiment"              # by pattern

ruff check src/       # lint
ruff format src/      # format
mypy src/             # type check
```

Coverage minimum: 70% (enforced in CI).

### 4. Commit

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat(rag): add hybrid search mode"
git commit -m "fix(core): handle empty document in chunker"
git commit -m "test(api): add vector search endpoint tests"
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`

**Scopes:** `core`, `rag`, `analysis`, `pipeline`, `api`, `cli`, `docs`, `tests`

### 5. Submit a Pull Request

```bash
git push origin feature/my-feature
```

PR checklist:

- [ ] Tests pass (`pytest`)
- [ ] No lint errors (`ruff check`)
- [ ] Code formatted (`ruff format`)
- [ ] Types valid (`mypy`)
- [ ] No merge conflicts with `main`

---

## Code Guidelines

### Python Style

- **PEP 8** via Ruff
- **Type hints** on all function signatures
- **Pydantic models** for data validation
- **Google-style docstrings** for public APIs
- Line length: 100 characters

### Import Order

```python
# Standard library
import os
from pathlib import Path

# Third-party
from pydantic import BaseModel
from fastapi import FastAPI

# Local
from phantom.core.cortex import CortexProcessor
from phantom.rag.vectors import FAISSVectorStore
```

### Error Handling

- Use specific exceptions, not bare `except`
- Use `structlog` / `logging`, not `print`
- Provide actionable error messages

```python
from phantom.logging import get_logger

logger = get_logger(__name__)

def process_document(path: Path) -> DocumentInsights:
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    try:
        return extract_insights(path)
    except Exception as e:
        logger.error(f"Failed to process {path}: {e}")
        raise
```

---

## Writing Tests

```python
import pytest
from phantom.core.cortex import CortexProcessor

@pytest.fixture
def processor():
    return CortexProcessor(chunk_size=512, workers=1)

def test_chunking_produces_output(processor):
    chunks = processor.chunk("Some text content here.")
    assert len(chunks) > 0

@pytest.mark.slow
def test_large_document(processor):
    # runs with: pytest -m slow
    ...
```

### Test Location

| Test type | Directory | Marker |
|-----------|-----------|--------|
| Unit | `tests/unit/` | (default) |
| Integration | `tests/integration/` | `@pytest.mark.integration` |
| End-to-end | `tests/e2e/` | `@pytest.mark.e2e` |
| Slow | anywhere | `@pytest.mark.slow` |

---

## Pull Request Review

1. CI checks must pass
2. At least one maintainer review
3. Address feedback, push updates
4. Squash if commit history is noisy
5. Maintainer merges when approved

---

## Reporting Issues

Before opening an issue, check if it already exists. Include:

- Steps to reproduce
- Expected vs actual behavior
- Python version, OS, relevant environment details
- Stack trace or error output

Use the "Bug Report" or "Feature Request" issue templates.

---

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
