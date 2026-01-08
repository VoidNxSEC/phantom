# Contributing to Phantom

First off, thank you for considering contributing to Phantom! It's people like you that make Phantom such a great framework for document intelligence and ML pipelines.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Workflow](#development-workflow)
- [Code Guidelines](#code-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Code of Conduct

This project and everyone participating in it is governed by the [Phantom Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

---

## Getting Started

### Prerequisites

- **NixOS** (recommended) or any Linux/macOS with Nix installed
- **Python 3.11+**
- **Git**
- **Just** command runner (optional but recommended)
- **Rust** (for desktop app development)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/marcosfpina/phantom.git
cd phantom

# Enter development environment (NixOS)
nix develop

# Or using standard Python
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Check code quality
ruff check src/
mypy src/
```

---

## Development Environment

Phantom uses a **reproducible Nix-based development environment** for consistency across all contributors.

### Using Nix (Recommended)

```bash
# Enter dev shell with all dependencies
nix develop

# The shell includes:
# - Python 3.13 with all dependencies
# - Rust toolchain
# - Development tools (ruff, mypy, pytest)
# - System utilities (jq, ripgrep, etc.)
```

### Using Just

If you have `just` installed, use these convenient commands:

```bash
just dev          # Enter dev environment
just test         # Run tests
just lint         # Run linters
just fmt          # Format code
just ci           # Run full CI locally
```

See `justfile` for all available commands.

---

## How Can I Contribute?

### Reporting Bugs

**Before submitting a bug report:**

- Check the [Issues](https://github.com/marcosfpina/phantom/issues) to see if it's already reported
- Collect information about the bug:
  - Stack trace
  - OS and Python version
  - Steps to reproduce
  - Expected vs actual behavior

**Submit a bug report:**

1. Use the "Bug Report" issue template
2. Provide a clear, descriptive title
3. Include all reproduction steps
4. Add relevant logs and screenshots

### Suggesting Enhancements

**Before submitting an enhancement:**

- Check if it's already in the [Roadmap](ROADMAP.md)
- Search existing [Issues](https://github.com/marcosfpina/phantom/issues)

**Submit an enhancement:**

1. Use the "Feature Request" issue template
2. Explain the problem it solves
3. Describe the proposed solution
4. Consider alternative solutions

### Contributing Code

1. **Find an issue** to work on (look for "good first issue" labels)
2. **Comment** on the issue to let others know you're working on it
3. **Fork** the repository
4. **Create a branch** from `main`: `git checkout -b feature/your-feature-name`
5. **Make your changes** following our guidelines
6. **Write tests** for your changes
7. **Ensure all tests pass**: `pytest`
8. **Submit a pull request**

---

## Development Workflow

### 1. Set Up Your Environment

```bash
git clone https://github.com/YOUR_USERNAME/phantom.git
cd phantom
nix develop  # or setup Python venv
pre-commit install
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/amazing-feature
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `refactor/` - Code refactoring
- `test/` - Adding tests
- `perf/` - Performance improvements

### 3. Make Your Changes

- Write clear, concise code
- Follow PEP 8 and project style guidelines
- Add docstrings to all public functions/classes
- Update documentation if needed

### 4. Test Your Changes

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=phantom --cov-report=html

# Run specific test
pytest tests/python/test_sentiment.py -v

# Run linters
ruff check src/
mypy src/
```

### 5. Commit Your Changes

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add semantic search caching"
git commit -m "fix: resolve VRAM calculation for multi-GPU"
git commit -m "docs: update API documentation"
```

### 6. Push and Create PR

```bash
git push origin feature/amazing-feature
```

Then create a Pull Request on GitHub.

---

## Code Guidelines

### Python Style

- Follow **PEP 8**
- Use **type hints** for all functions
- Maximum line length: **88 characters** (Black/Ruff default)
- Use **Pydantic models** for data validation
- Prefer **async/await** for I/O operations

### Code Organization

```python
# Standard library imports
import os
from pathlib import Path
from typing import Optional

# Third-party imports
import pandas as pd
from pydantic import BaseModel, Field

# Local imports
from phantom.core import CortexProcessor
from phantom.rag import FAISSVectorStore
```

### Docstrings

Use **Google-style docstrings**:

```python
def calculate_embedding(
    text: str,
    model: str = "all-MiniLM-L6-v2",
    device: str = "cpu"
) -> np.ndarray:
    """
    Generate vector embedding for input text.

    Args:
        text: Input text to embed
        model: Sentence-transformers model name
        device: Device to use ('cpu' or 'cuda')

    Returns:
        NumPy array of shape (embedding_dim,)

    Raises:
        ValueError: If text is empty
        RuntimeError: If model fails to load

    Example:
        >>> embedding = calculate_embedding("Hello world")
        >>> embedding.shape
        (384,)
    """
```

### Error Handling

- Use **specific exceptions**
- Provide **helpful error messages**
- Use **logging** instead of print statements

```python
import logging

logger = logging.getLogger(__name__)

def process_document(path: Path) -> DocumentInsights:
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    try:
        insights = extract_insights(path)
        logger.info(f"Processed {path}: {len(insights.themes)} themes")
        return insights
    except Exception as e:
        logger.error(f"Failed to process {path}: {e}")
        raise RuntimeError(f"Processing failed: {e}") from e
```

### Type Hints

Always use type hints:

```python
from typing import Optional, Union
from pathlib import Path

def load_model(
    model_path: Union[str, Path],
    device: Optional[str] = None
) -> ModelType:
    ...
```

---

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) for clear, automated changelogs.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Code style (formatting, no logic change)
- **refactor**: Code refactoring
- **perf**: Performance improvement
- **test**: Adding/updating tests
- **chore**: Maintenance (deps, build, etc.)
- **ci**: CI/CD changes

### Examples

```bash
feat(rag): add semantic caching to vector search

Implement LRU cache for frequently searched queries.
Reduces latency by 60% for repeated searches.

Closes #123

fix(core): resolve memory leak in parallel processing

ThreadPoolExecutor wasn't being properly cleaned up.
Now using context manager to ensure cleanup.

Fixes #456

docs: update API authentication examples

Added examples for JWT and API key authentication.
```

### Scope

Common scopes:
- `core` - Core processing engine
- `rag` - RAG pipeline
- `analysis` - Analysis modules
- `pipeline` - ETL pipeline
- `api` - REST API
- `cli` - CLI interface
- `docs` - Documentation
- `tests` - Test suite

---

## Pull Request Process

### Before Submitting

- [ ] All tests pass (`pytest`)
- [ ] Code is formatted (`ruff format`)
- [ ] No linter errors (`ruff check`)
- [ ] Type hints validated (`mypy`)
- [ ] Documentation updated
- [ ] Changelog updated (if applicable)
- [ ] No merge conflicts with `main`

### PR Title

Use conventional commit format:

```
feat(rag): add multi-modal embedding support
fix(core): resolve chunking edge case for code blocks
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation and Context
Why is this change needed? What problem does it solve?

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that breaks existing functionality)
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran to verify your changes.

## Screenshots (if applicable)

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly hard-to-understand areas
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **Code review** from at least one maintainer
3. **Address feedback** and update PR
4. **Squash commits** if needed
5. **Merge** when approved

---

## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=phantom --cov-report=html

# Specific markers
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests
pytest -m slow          # Slow tests
pytest -m gpu           # GPU tests

# Specific file
pytest tests/python/test_sentiment.py -v

# Match pattern
pytest -k "test_sentiment"
```

### Writing Tests

```python
import pytest
from phantom.core import CortexProcessor

@pytest.fixture
def processor():
    """Fixture providing a configured processor."""
    return CortexProcessor(
        provider=MockProvider(),
        chunk_size=512,
        workers=1
    )

def test_document_processing(processor):
    """Test basic document processing."""
    insights = processor.process_document("test.md")

    assert insights is not None
    assert len(insights.themes) > 0
    assert insights.processing_time > 0

@pytest.mark.slow
def test_large_document_processing(processor):
    """Test processing of large documents."""
    # This test takes significant time
    ...

@pytest.mark.gpu
def test_gpu_acceleration():
    """Test GPU-accelerated embedding."""
    # Requires GPU
    ...
```

### Test Coverage Goals

- **Minimum**: 70% overall coverage
- **Core modules**: 80%+ coverage
- **Critical paths**: 90%+ coverage

---

## Documentation

### Code Documentation

- **Docstrings** for all public functions/classes
- **Type hints** for all function signatures
- **Examples** in docstrings where helpful
- **Comments** for complex logic only

### User Documentation

Located in `/docs/`:

- **Guides**: Step-by-step tutorials
- **Reference**: API documentation
- **Architecture**: System design docs
- **Examples**: Usage examples

### Updating Documentation

When adding features:

1. Add docstrings to code
2. Update relevant `/docs/` files
3. Add examples if applicable
4. Update README.md if needed

---

## Questions?

- **GitHub Issues**: For bugs and features
- **GitHub Discussions**: For questions and ideas
- **Email**: [your-email@example.com] (for security issues)

---

## Recognition

Contributors are recognized in:

- `README.md` Contributors section
- Git commit history
- Release notes

Thank you for contributing to Phantom! 🎉

---

**License**: By contributing, you agree that your contributions will be licensed under the MIT License.
