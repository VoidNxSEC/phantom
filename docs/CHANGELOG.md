# Changelog - Phantom Classifier / Vortex Project

## [2.1.0] - 2025-12-10

### Infrastructure & Configuration (`flake.nix`)
- **Dependency Resolution**:
  - Removed broken dependency `vadersentiment`.
  - Removed unused/conflicting dependencies `rich` and `tqdm` to streamline the build.
  - Added `click` for robust CLI development.
  - Added `pytest` for test automation.
- **Nix Overlay Implementation**:
  - Implemented a complex overlay to resolve a "diamond dependency" conflict between `spacy` (via `weasel`) and the Python environment's `typer` version.
  - Aliased `typer-slim` to `typer` to force package deduplication.
  - Patched `weasel` build process to relax strict metadata checks (`pythonRuntimeDepsCheck`), allowing it to accept the aliased `typer` package.

### New Features
- **Sentiment Analysis Engine (`sentiment_analysis.py`)**:
  - Implemented a hybrid sentiment analysis class `SentimentEngine`.
  - **Core Logic**: Uses NLTK's VADER for robust, rule-based sentiment scoring.
  - **Advanced Preprocessing**: Optional integration with `spacy` for lemmatization and stopword removal (gracefully degrades if model is missing).
  - **Metrics**: Built-in calculation of Precision, Recall, and F1-Score using `scikit-learn`.
  - **Type Safety**: Fully typed using Python `dataclasses` and type hints.

### Quality Assurance
- **Automated Testing**:
  - Created `tests/test_sentiment.py` using `pytest`.
  - Implemented tests for positive/negative/neutral classification, metrics calculation, and flag handling.
- **Documentation**:
  - Created `SENTIMENT_DOCS.md` with usage guides and architectural overview.

### Refactoring
- Cleaned up the Python environment definition to focus on industrial-grade NLP libraries (`spacy`, `nltk`, `scikit-learn`) rather than ad-hoc scripts.
