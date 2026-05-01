# Changelog

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [2.2.0] - 2026-05-01

### Changed
- **Monorepo Reorganization**: Consolidated repository structure for public release.
- **Documentation**: Reorganized `docs/` into categorized subdirectories (Architecture, Development, API, Guides, Reference, History).
- **Nix Flake**: Updated `flake.nix` to use the modern modular CLI (`phantom.cli.main`) instead of deprecated scripts.
- **Root Cleanup**: Moved implementation reports, quickrefs, and standalone scripts to their respective directories (`docs/history/`, `docs/reference/`, `scripts/`).
- **Archive**: Moved deprecated code (`phantom_core`) and old architecture snapshots to `.archive/`.

### Added
- Professional `README.md` overhaul with accurate project status and roadmap.
- Centralized `history` tracking for project milestones.

## [2.1.0] - 2025-12-10

### Infrastructure

- Removed broken dependency `vadersentiment`
- Removed unused dependencies `rich` and `tqdm` from flake
- Added `click` and `pytest` to flake dependencies
- Implemented Nix overlay to resolve `spacy`/`weasel`/`typer` dependency conflict (aliased `typer-slim` to `typer`, patched `weasel` metadata checks)

### Added

- **Sentiment analysis engine** (`sentiment_analysis.py`): hybrid NLTK VADER-based scoring with optional spaCy preprocessing. Includes precision/recall/F1 via scikit-learn.
- Automated tests for sentiment analysis (`tests/test_sentiment.py`)
- Sentiment documentation (`SENTIMENT_DOCS.md`)

### Changed

- Cleaned up Python environment definition in `flake.nix` to focus on NLP libraries (spaCy, NLTK, scikit-learn)
