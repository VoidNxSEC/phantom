# Changelog

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

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
