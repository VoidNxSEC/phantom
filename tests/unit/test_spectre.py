"""
Unit tests for SpectreAnalyzer — multi-dimensional text analysis.

All tests use plain strings; no external services or models required.
"""

import pytest

from phantom.analysis.spectre import SpectreAnalyzer


@pytest.fixture
def analyzer():
    return SpectreAnalyzer()


class TestSpectreInit:
    def test_instantiation(self):
        sa = SpectreAnalyzer()
        assert sa is not None
        assert sa.documents_analyzed == 0
        assert sa.total_words_processed == 0

    def test_instantiation_with_taxonomy(self):
        sa = SpectreAnalyzer(taxonomy_terms=["python", "rust", "ai"])
        assert sa is not None


class TestSpectreAnalyze:
    def test_analyze_returns_result(self, analyzer, sample_markdown):
        result = analyzer.analyze(sample_markdown)
        assert result is not None

    def test_analyze_increments_document_count(self, analyzer):
        analyzer.analyze("Hello world")
        assert analyzer.documents_analyzed == 1
        analyzer.analyze("Another document")
        assert analyzer.documents_analyzed == 2

    def test_analyze_empty_string(self, analyzer):
        result = analyzer.analyze("")
        assert result is not None

    def test_analyze_single_word(self, analyzer):
        result = analyzer.analyze("hello")
        assert result is not None
        assert analyzer.total_words_processed >= 1
