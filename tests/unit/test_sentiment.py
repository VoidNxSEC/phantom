import pytest

from phantom.analysis.sentiment_analysis import SentimentEngine


@pytest.fixture
def engine():
    return SentimentEngine(use_spacy=False)


def test_sentiment_positive(engine):
    result = engine.analyze("I love this product, it is amazing!")
    assert result.label == "positive"
    assert result.score > 0.5


def test_sentiment_negative(engine):
    result = engine.analyze("This is a terrible mistake and I hate it.")
    assert result.label == "negative"
    assert result.score < -0.5


def test_sentiment_neutral(engine):
    result = engine.analyze("The box is made of cardboard.")
    assert result.label == "neutral" or abs(result.score) < 0.1


def test_metrics_perfect(engine):
    # Note: VADER might classify 'Okay' as positive, so we adjust expectation or input
    # 'Okay' is often positive. 'Average' is neutral?
    # Let's use clear examples
    metrics = engine.evaluate(
        [
            {"text": "I love it", "label": "positive"},
            {"text": "I hate it", "label": "negative"},
        ]
    )
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1 == 1.0


def test_preprocessing_flag(engine):
    # Just check it runs without error
    res = engine.analyze("Test", preprocess=True)
    assert res.text == "Test"


def test_sentiment_result_details(engine):
    result = engine.analyze("I love this product!")
    assert "pos" in result.details
    assert "neg" in result.details
    assert "neu" in result.details
    assert "compound" in result.details


def test_analyze_compound_score_range(engine):
    result = engine.analyze("This is a test sentence.")
    assert -1.0 <= result.score <= 1.0


def test_evaluate_empty_dataset(engine):
    metrics = engine.evaluate([])
    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0


def test_evaluate_invalid_labels_skipped(engine):
    metrics = engine.evaluate([
        {"text": "Hello", "label": "invalid_label"},
    ])
    assert metrics.precision == 0.0


def test_evaluate_mixed_results(engine):
    dataset = [
        {"text": "I love it, amazing!", "label": "positive"},
        {"text": "Terrible, awful experience.", "label": "negative"},
        {"text": "The package arrived.", "label": "neutral"},
    ]
    metrics = engine.evaluate(dataset)
    assert 0.0 <= metrics.precision <= 1.0
    assert 0.0 <= metrics.recall <= 1.0
    assert 0.0 <= metrics.f1 <= 1.0


def test_preprocess_without_spacy():
    engine = SentimentEngine(use_spacy=False)
    result = engine.preprocess("  Hello World  ")
    assert result == "Hello World"


def test_sentiment_metrics_dataclass():
    from phantom.analysis.sentiment_analysis import SentimentMetrics
    m = SentimentMetrics(precision=0.9, recall=0.85, f1=0.87)
    assert m.precision == 0.9
    assert m.recall == 0.85
    assert m.f1 == 0.87
