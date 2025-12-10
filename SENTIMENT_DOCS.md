# Sentiment Analysis Module Documentation

## Overview
This module (`sentiment_analysis.py`) provides a robust sentiment analysis engine capable of classifying text as **Positive**, **Negative**, or **Neutral**. It utilizes NLTK's VADER (Valence Aware Dictionary and sEntiment Reasoner) for scoring and supports SpaCy for advanced text preprocessing.

## Features
- **Hybrid Architecture**: Combines NLTK VADER's rule-based efficiency with SpaCy's linguistic power.
- **Graceful Degradation**: Automatically disables SpaCy preprocessing if the library or model is unavailable, ensuring continuity.
- **Metrics Calculation**: Built-in support for calculating Precision, Recall, and F1-Score using Scikit-learn.
- **Type Safety**: Fully typed codebase using Python `typing` and `dataclasses`.

## Installation
The environment is managed via Nix. Dependencies are defined in `flake.nix`.

```bash
nix develop
```

## Usage

### Basic Analysis
```python
from sentiment_analysis import SentimentEngine

engine = SentimentEngine()
result = engine.analyze("I love this project!")
print(f"Label: {result.label}, Score: {result.score}")
```

### Preprocessing with SpaCy
Enable preprocessing to lemmatize text and remove stopwords before analysis.
```python
# Requires SpaCy library and model (en_core_web_sm) to be available
engine = SentimentEngine(use_spacy=True)
result = engine.analyze("The products were not good.", preprocess=True)
```

### Evaluation
```python
dataset = [
    {'text': 'Excellent', 'label': 'positive'},
    {'text': 'Horrible', 'label': 'negative'}
]
metrics = engine.evaluate(dataset)
print(metrics)
```

## Testing
Run the automated test suite:
```bash
nix develop --command bash -c "export PYTHONPATH=$PYTHONPATH:. && pytest"
```
