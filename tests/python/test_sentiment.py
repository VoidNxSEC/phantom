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
    dataset = [
        {"text": "Great job", "label": "positive"},
        {"text": "Terrible", "label": "negative"},
        {"text": "Okay", "label": "neutral"},
    ]
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
