# SPECTRE

**Sentiment & Pattern Extraction for Contextual Text Research Engine — a component of [Phantom](https://github.com/kernelcore/phantom)**

---

## What is SPECTRE?

SPECTRE is a multi-dimensional sentiment analysis pipeline for technical documentation. Instead of a single positive/negative score, it evaluates text across five dimensions simultaneously:

| Dimension | What it measures |
|-----------|-----------------|
| Technical | Technical confidence, security posture, robustness |
| Market | Bullish/bearish signals, adoption trends |
| Community | Community health, engagement levels |
| Innovation | Progress, novelty, stagnation indicators |
| Risk | Risk profile, vulnerability indicators |

SPECTRE uses a customized VADER implementation with domain-specific lexicons (currently tuned for blockchain/Web3 documentation) and taxonomy-based topic extraction.

The core implementation lives in `src/phantom/analysis/spectre.py` (~2200 lines), which provides `SpectreAnalyzer` and `SpectrePipeline` classes.

---

## Architecture

```
Document(s) → Ingest → Parse (Markdown sections) → Analyze (multi-dimensional sentiment)
                                                          → Enrich (entity extraction, knowledge graph)
                                                          → Output (JSON reports, CSV, markdown summary)
```

### Pipeline Stages

1. **Ingest** — file discovery, metadata extraction
2. **Parse** — markdown AST, section splitting
3. **Analyze** — VADER-based sentiment scoring across 5 dimensions, topic frequency mapping
4. **Enrich** — entity extraction, co-occurrence tracking
5. **Output** — per-document JSON, corpus-level insights, sentiment CSV for visualization

### Output Structure

```
output/
├── documents/                    # Per-document analysis
│   ├── doc1_analysis.json
│   └── doc2_analysis.json
└── reports/
    ├── corpus_insights_*.json    # Aggregated insights
    ├── summary_report_*.md       # Human-readable report
    └── sentiment_data_*.csv      # Data for visualization
```

---

## Usage

SPECTRE is part of Phantom's analysis module. It has its own Nix flake for standalone use:

```bash
cd spectre
nix develop

# Analyze a directory of markdown files
spectre -i ./docs -o ./analysis -t taxonomy.txt -v

# Quick single-file analysis
spectre-quick document.md

# Topic frequency scan
spectre-scan ./docs taxonomy.txt

# Corpus statistics
spectre-stats ./docs

# ASCII sentiment heatmap
spectre-heatmap sentiment_data.csv
```

### From Python

```python
from phantom.analysis.spectre import SpectreAnalyzer, SpectrePipeline

# Single document
analyzer = SpectreAnalyzer()
result = analyzer.analyze(text)

# Corpus pipeline
pipeline = SpectrePipeline(input_dir="./docs", output_dir="./analysis")
pipeline.run()
```

---

## Sentiment Lexicons

SPECTRE uses domain-specific lexicons in addition to VADER's general-purpose dictionary. Examples:

**Technical confidence:**
- positive: `audited` (+0.85), `battle-tested` (+0.85), `secure` (+0.7)
- negative: `vulnerable` (-0.8), `unaudited` (-0.8), `exploit` (-0.9)

**Risk assessment:**
- low risk: `insured` (+0.55), `collateralized` (+0.45)
- high risk: `liquidation` (-0.6), `flashloan attack` (-0.8)

Lexicons are extensible — add terms to the `SentimentLexicons` class in `spectre.py`.

---

## Metrics

### Per Document

| Metric | Description |
|--------|-------------|
| `compound` | Normalized score [-1, 1] |
| `pos/neg/neu` | Proportion of each polarity |
| `confidence` | Classification certainty |
| `dominant_dimension` | Most expressed dimension |
| `sentiment_divergence` | Deviation across dimensions |

### Per Corpus

| Metric | Description |
|--------|-------------|
| `topic_frequency` | Taxonomy term frequency |
| `topic_sentiment` | Average sentiment per topic |
| `sentiment_trend` | Sentiment evolution across documents |
| `entity_network` | Entity co-occurrence map |

---

## Limitations

- Lexicons are currently tuned for blockchain/Web3 — other domains will need custom lexicons
- CLI tools (`spectre`, `spectre-quick`, etc.) are defined in the SPECTRE flake, not in the main Phantom `pyproject.toml`
- No multilingual support — English only
- VADER-based approach has known limitations with sarcasm, negation chains, and domain-specific jargon not in the lexicon

---

## License

Apache License 2.0 — see [LICENSE](../LICENSE).
