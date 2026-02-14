"""
Unit tests for the SPECTRE analysis module.

Tests: Lexicons, VADERAnalyzer, MarkdownParser, KeywordExtractor,
       EntityExtractor, TaxonomyManager, SpectreAnalyzer.
"""

import pytest

from phantom.analysis.spectre import (
    CorpusInsights,
    DocumentAnalysis,
    Entity,
    EntityExtractor,
    KeywordExtractor,
    MarkdownParser,
    MultiDimensionalSentiment,
    SentimentLabel,
    SentimentLexicons,
    SentimentScore,
    SpectreAnalyzer,
    TaxonomyManager,
    TopicMatch,
    VADERAnalyzer,
)

pytestmark = pytest.mark.unit


class TestSentimentLexicons:
    """Test SentimentLexicons class."""

    def test_get_all_lexicons(self):
        lexicons = SentimentLexicons.get_all_lexicons()
        assert "technical" in lexicons
        assert "market" in lexicons
        assert "community" in lexicons
        assert "innovation" in lexicons
        assert "risk" in lexicons

    def test_technical_confidence_has_entries(self):
        assert len(SentimentLexicons.TECHNICAL_CONFIDENCE) > 0
        assert SentimentLexicons.TECHNICAL_CONFIDENCE["proven"] > 0
        assert SentimentLexicons.TECHNICAL_CONFIDENCE["vulnerable"] < 0

    def test_market_sentiment_has_entries(self):
        assert SentimentLexicons.MARKET_SENTIMENT["bullish"] > 0
        assert SentimentLexicons.MARKET_SENTIMENT["bearish"] < 0


class TestSentimentLabel:
    """Test SentimentLabel enum."""

    def test_from_compound_very_positive(self):
        assert SentimentLabel.from_compound(0.7) == SentimentLabel.VERY_POSITIVE

    def test_from_compound_positive(self):
        assert SentimentLabel.from_compound(0.3) == SentimentLabel.POSITIVE

    def test_from_compound_neutral(self):
        assert SentimentLabel.from_compound(0.0) == SentimentLabel.NEUTRAL

    def test_from_compound_negative(self):
        assert SentimentLabel.from_compound(-0.3) == SentimentLabel.NEGATIVE

    def test_from_compound_very_negative(self):
        assert SentimentLabel.from_compound(-0.7) == SentimentLabel.VERY_NEGATIVE

    def test_boundary_values(self):
        assert SentimentLabel.from_compound(0.5) == SentimentLabel.VERY_POSITIVE
        assert SentimentLabel.from_compound(0.1) == SentimentLabel.POSITIVE
        assert SentimentLabel.from_compound(-0.1) == SentimentLabel.NEGATIVE
        assert SentimentLabel.from_compound(-0.5) == SentimentLabel.VERY_NEGATIVE


class TestVADERAnalyzer:
    """Test VADERAnalyzer sentiment analysis."""

    @pytest.fixture
    def analyzer(self):
        return VADERAnalyzer(SentimentLexicons.TECHNICAL_CONFIDENCE)

    def test_analyze_empty_text(self, analyzer):
        result = analyzer.analyze("")
        assert result["compound"] == 0.0
        assert result["neu"] == 1.0

    def test_analyze_positive_text(self, analyzer):
        result = analyzer.analyze("This project is proven and verified.")
        assert result["compound"] > 0

    def test_analyze_negative_text(self, analyzer):
        result = analyzer.analyze("This is vulnerable and untested.")
        assert result["compound"] < 0

    def test_analyze_neutral_text(self, analyzer):
        result = analyzer.analyze("The weather is nice today.")
        assert result["compound"] == 0.0

    def test_negation_detection(self, analyzer):
        positive = analyzer.analyze("This is secure.")
        negated = analyzer.analyze("This is not secure.")
        assert negated["compound"] < positive["compound"]

    def test_booster_amplification(self, analyzer):
        normal = analyzer.analyze("This is proven.")
        boosted = analyzer.analyze("This is extremely proven.")
        assert abs(boosted["compound"]) >= abs(normal["compound"])

    def test_caps_emphasis(self, analyzer):
        normal = analyzer.analyze("This is proven.")
        caps = analyzer.analyze("This is PROVEN.")
        assert abs(caps["compound"]) >= abs(normal["compound"])

    def test_result_keys(self, analyzer):
        result = analyzer.analyze("Test text secure")
        assert "pos" in result
        assert "neg" in result
        assert "neu" in result
        assert "compound" in result

    def test_compound_normalized(self, analyzer):
        result = analyzer.analyze("proven verified audited secure tested validated")
        assert -1 <= result["compound"] <= 1

    def test_tokenize(self, analyzer):
        tokens = analyzer._tokenize("Hello, world! This is a test.")
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_is_negated(self, analyzer):
        tokens = ["this", "is", "not", "good"]
        assert analyzer._is_negated(tokens, 3) is True
        assert analyzer._is_negated(tokens, 1) is False

    def test_punctuation_emphasis(self, analyzer):
        normal = analyzer.analyze("This is proven.")
        emphatic = analyzer.analyze("This is proven!")
        # Exclamation should amplify
        assert abs(emphatic["compound"]) >= abs(normal["compound"])


class TestMarkdownParser:
    """Test MarkdownParser."""

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    def test_parse_with_headers(self, parser):
        content = "# Title\n\nContent here.\n\n## Section\n\nMore content."
        title, sections = parser.parse(content)
        assert title == "Title"
        assert len(sections) >= 2

    def test_parse_no_headers(self, parser):
        content = "Just plain text without any headers."
        title, sections = parser.parse(content)
        assert title == "Untitled"
        assert len(sections) == 1
        assert sections[0].title == "Content"

    def test_parse_with_filepath(self, parser):
        content = "No headers here."
        title, sections = parser.parse(content, filepath="my-document.md")
        assert title == "My Document"

    def test_section_word_count(self, parser):
        content = "# Title\n\nOne two three four five."
        title, sections = parser.parse(content)
        assert sections[0].word_count > 0

    def test_clean_content_strips_code_blocks(self, parser):
        content = "Text before\n```python\nprint('hello')\n```\nText after"
        cleaned = parser._clean_content(content)
        assert "print" not in cleaned
        assert "Text before" in cleaned

    def test_clean_content_strips_links(self, parser):
        content = "Check [this link](http://example.com) here."
        cleaned = parser._clean_content(content)
        assert "this link" in cleaned
        assert "http" not in cleaned

    def test_clean_content_strips_bold(self, parser):
        content = "This is **bold** text."
        cleaned = parser._clean_content(content)
        assert "bold" in cleaned
        assert "**" not in cleaned

    def test_extract_links(self, parser):
        content = "[Link1](http://a.com) and [Link2](http://b.com)"
        links = parser.extract_links(content)
        assert len(links) == 2
        assert links[0] == ("Link1", "http://a.com")

    def test_extract_code_blocks(self, parser):
        content = "Before\n```python\ncode\n```\nAfter\n```js\nmore\n```"
        blocks = parser.extract_code_blocks(content)
        assert len(blocks) == 2

    def test_extract_title_h1(self, parser):
        assert parser._extract_title("# My Title\n\nContent", "") == "My Title"

    def test_extract_title_fallback(self, parser):
        assert parser._extract_title("No headers", "my-doc.md") == "My Doc"


class TestKeywordExtractor:
    """Test KeywordExtractor."""

    @pytest.fixture
    def extractor(self):
        return KeywordExtractor()

    def test_extract_keywords(self, extractor):
        text = "blockchain consensus protocol security audit verification"
        keywords = extractor.extract(text, top_n=5)
        assert len(keywords) > 0
        assert all(isinstance(k, tuple) and len(k) == 2 for k in keywords)

    def test_extract_empty_text(self, extractor):
        assert extractor.extract("") == []

    def test_extract_scores_ordered(self, extractor):
        text = "python python python rust go python"
        keywords = extractor.extract(text, top_n=5)
        scores = [k[1] for k in keywords]
        assert scores == sorted(scores, reverse=True)

    def test_extract_phrases(self, extractor):
        text = "machine learning model training deep learning neural network"
        phrases = extractor.extract_phrases(text, top_n=5)
        assert isinstance(phrases, list)

    def test_extract_phrases_short_text(self, extractor):
        assert extractor.extract_phrases("word") == []

    def test_stop_words_filtered(self, extractor):
        text = "the and but for with from"
        keywords = extractor.extract(text, top_n=10)
        assert len(keywords) == 0

    def test_tokenize(self, extractor):
        tokens = extractor._tokenize("Hello World foo-bar")
        assert "hello" in tokens
        assert "world" in tokens
        assert "foo-bar" in tokens


class TestEntityExtractor:
    """Test EntityExtractor."""

    @pytest.fixture
    def extractor(self):
        return EntityExtractor()

    def test_extract_protocols(self, extractor):
        text = "Ethereum and Bitcoin are leading blockchain protocols."
        entities = extractor.extract(text)
        names = [e.text for e in entities]
        assert "Ethereum" in names
        assert "Bitcoin" in names

    def test_extract_tokens(self, extractor):
        text = "Buy ETH and BTC for your portfolio."
        entities = extractor.extract(text)
        token_entities = [e for e in entities if e.entity_type == "TOKEN"]
        token_names = [e.text for e in token_entities]
        assert "ETH" in token_names
        assert "BTC" in token_names

    def test_extract_empty_text(self, extractor):
        entities = extractor.extract("No entities here.")
        assert len(entities) == 0

    def test_entity_frequency(self, extractor):
        text = "Ethereum is great. Ethereum has smart contracts. Ethereum rocks."
        entities = extractor.extract(text)
        eth = [e for e in entities if e.text == "Ethereum"]
        assert len(eth) == 1
        assert eth[0].frequency == 3

    def test_find_co_occurrences(self, extractor):
        text = "Ethereum and Bitcoin are both blockchain protocols."
        entities = extractor.extract(text)
        extractor.find_co_occurrences(entities, text)
        if len(entities) >= 2:
            has_co = any(len(e.co_occurrences) > 0 for e in entities)
            assert has_co


class TestTaxonomyManager:
    """Test TaxonomyManager."""

    @pytest.fixture
    def taxonomy(self):
        tm = TaxonomyManager()
        tm.load_taxonomy([
            "blockchain", "smart contract", "defi",
            "token", "governance", "consensus",
        ])
        return tm

    def test_load_taxonomy(self, taxonomy):
        assert len(taxonomy.terms) == 6
        assert "blockchain" in taxonomy.terms

    def test_categorize_term(self, taxonomy):
        assert taxonomy.term_to_category["blockchain"] == "blockchain_core"
        assert taxonomy.term_to_category["smart contract"] == "smart_contracts"
        assert taxonomy.term_to_category["defi"] == "defi"
        assert taxonomy.term_to_category["governance"] == "governance"

    def test_match_terms(self, taxonomy):
        text = "The blockchain uses smart contracts for governance."
        matches = taxonomy.match_terms(text)
        terms = [m.term for m in matches]
        assert "blockchain" in terms
        assert "governance" in terms

    def test_match_terms_frequency(self, taxonomy):
        text = "blockchain blockchain blockchain smart contract"
        matches = taxonomy.match_terms(text)
        bc = [m for m in matches if m.term == "blockchain"]
        assert bc[0].frequency == 3

    def test_get_categories(self, taxonomy):
        cats = taxonomy.get_categories()
        assert isinstance(cats, dict)
        assert "blockchain_core" in cats

    def test_load_empty_terms(self):
        tm = TaxonomyManager()
        tm.load_taxonomy(["", "  ", ""])
        assert len(tm.terms) == 0


class TestSentimentScore:
    """Test SentimentScore dataclass."""

    def test_construction(self):
        score = SentimentScore(
            dimension="technical", compound=0.5, positive=0.3,
            negative=0.1, neutral=0.6, label="positive",
            confidence=0.5, word_count=10,
        )
        assert score.compound == 0.5
        assert score.dimension == "technical"

    def test_to_dict(self):
        score = SentimentScore(
            dimension="market", compound=0.0, positive=0.0,
            negative=0.0, neutral=1.0, label="neutral",
            confidence=0.0, word_count=5,
        )
        d = score.to_dict()
        assert d["dimension"] == "market"
        assert isinstance(d, dict)


class TestSpectreAnalyzer:
    """Test SpectreAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        return SpectreAnalyzer(taxonomy_terms=["blockchain", "security", "defi"])

    def test_instantiation(self):
        sa = SpectreAnalyzer()
        assert sa.documents_analyzed == 0
        assert sa.total_words_processed == 0

    def test_instantiation_with_taxonomy(self):
        sa = SpectreAnalyzer(taxonomy_terms=["python", "rust", "ai"])
        assert sa is not None

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

    def test_analyze_text(self, analyzer):
        result = analyzer.analyze("This blockchain project is proven and secure.")
        assert isinstance(result, MultiDimensionalSentiment)
        assert hasattr(result, "technical")
        assert hasattr(result, "market")
        assert hasattr(result, "overall")
        assert result.dominant_dimension != ""

    def test_analyze_text_updates_stats(self, analyzer):
        analyzer.analyze("Test text for analysis.")
        assert analyzer.documents_analyzed == 1
        assert analyzer.total_words_processed > 0

    def test_analyze_document(self, analyzer, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text(
            "# Test Document\n\nThis is a proven and secure blockchain protocol."
            "\n\n## Details\n\nMore content about verified smart contracts."
        )
        analysis = analyzer.analyze_document(md_file)
        assert isinstance(analysis, DocumentAnalysis)
        assert analysis.title == "Test Document"
        assert analysis.word_count > 0
        assert analysis.sentiment is not None

    def test_analyze_document_sections(self, analyzer, tmp_path):
        md_file = tmp_path / "sections.md"
        md_file.write_text(
            "# Title\n\nIntro text here.\n\n## Section One\n\n"
            "Content about blockchain security.\n\n## Section Two\n\n"
            "More information about defi protocols."
        )
        analysis = analyzer.analyze_document(md_file)
        assert len(analysis.sections) >= 2

    def test_sentiment_divergence(self, analyzer):
        result = analyzer.analyze("bullish proven but risky and vulnerable")
        assert isinstance(result.sentiment_divergence, float)

    def test_generate_corpus_insights_empty(self, analyzer):
        insights = analyzer.generate_corpus_insights([])
        assert isinstance(insights, CorpusInsights)
        assert insights.total_documents == 0

    def test_generate_corpus_insights(self, analyzer, tmp_path):
        analyses = []
        for i in range(3):
            md = tmp_path / f"doc{i}.md"
            md.write_text(
                f"# Document {i}\n\nThis proven blockchain is secure and verified."
            )
            analyses.append(analyzer.analyze_document(md))
        insights = analyzer.generate_corpus_insights(analyses)
        assert insights.total_documents == 3
        assert insights.total_words > 0
        assert len(insights.key_findings) > 0

    def test_overall_sentiment_dimensions(self, analyzer):
        result = analyzer.analyze("secure proven verified audited robust")
        assert result.technical.compound > 0
        assert result.overall.compound > 0


class TestTopicMatch:
    """Test TopicMatch dataclass."""

    def test_construction(self):
        match = TopicMatch(
            term="blockchain", category="blockchain_core",
            frequency=5, contexts=["...using blockchain..."],
        )
        assert match.term == "blockchain"
        assert match.frequency == 5


class TestEntity:
    """Test Entity dataclass."""

    def test_construction(self):
        entity = Entity(
            text="Ethereum", entity_type="PROTOCOL",
            frequency=3, sentiment_association=0.5,
        )
        assert entity.text == "Ethereum"
        assert entity.frequency == 3
        assert entity.co_occurrences == []
