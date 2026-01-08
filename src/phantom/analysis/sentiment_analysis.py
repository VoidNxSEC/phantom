"""
Sentiment Analysis Module using NLTK and SpaCy.
"""

import sys
from dataclasses import dataclass
from typing import Any

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.metrics import f1_score, precision_score, recall_score

try:
    import spacy
except ImportError:
    spacy = None


@dataclass
class SentimentMetrics:
    precision: float
    recall: float
    f1: float


@dataclass
class SentimentResult:
    text: str
    label: str  # 'positive', 'negative', 'neutral'
    score: float
    details: dict[str, Any]


class SentimentEngine:
    """
    Sentiment Analysis Engine supporting NLTK VADER.
    SpaCy is used for preprocessing.
    """

    def __init__(self, use_spacy: bool = True):
        self.use_spacy = use_spacy

        # Initialize NLTK VADER
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            print("Downloading NLTK VADER lexicon...", file=sys.stderr)
            nltk.download("vader_lexicon", quiet=True)

        self.sia = SentimentIntensityAnalyzer()

        # Initialize SpaCy (optional, for advanced preprocessing)
        if self.use_spacy:
            if spacy is None:
                print(
                    "SpaCy library not found. Disabling SpaCy preprocessing.",
                    file=sys.stderr,
                )
                self.use_spacy = False
            else:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except OSError:
                    print(
                        "SpaCy model 'en_core_web_sm' not found. Disabling SpaCy preprocessing.",
                        file=sys.stderr,
                    )
                    self.use_spacy = False

    def preprocess(self, text: str) -> str:
        """Clean and lemmatize text using SpaCy if available."""
        if not self.use_spacy:
            return text.strip()

        doc = self.nlp(text)
        # Filter stopwords and punctuation, return lemmas
        tokens = [
            token.lemma_ for token in doc if not token.is_stop and not token.is_punct
        ]
        return " ".join(tokens)

    def analyze(self, text: str, preprocess: bool = False) -> SentimentResult:
        """Analyze sentiment of a single text."""
        input_text = self.preprocess(text) if preprocess else text
        scores = self.sia.polarity_scores(input_text)
        compound = scores["compound"]

        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        return SentimentResult(text=text, label=label, score=compound, details=scores)

    def evaluate(self, dataset: list[dict[str, str]]) -> SentimentMetrics:
        """
        Evaluate performance against a labeled dataset.
        dataset format: [{'text': '...', 'label': 'positive'}, ...]
        """
        y_true = []
        y_pred = []

        for item in dataset:
            # Map labels to match VADER output if necessary
            # Assuming dataset labels are 'positive', 'negative', 'neutral'
            true_label = item["label"].lower()
            if true_label not in ["positive", "negative", "neutral"]:
                continue

            pred = self.analyze(item["text"]).label

            y_true.append(true_label)
            y_pred.append(pred)

        if not y_true:
            return SentimentMetrics(0.0, 0.0, 0.0)

        return SentimentMetrics(
            precision=precision_score(
                y_true, y_pred, average="weighted", zero_division=0
            ),
            recall=recall_score(y_true, y_pred, average="weighted", zero_division=0),
            f1=f1_score(y_true, y_pred, average="weighted", zero_division=0),
        )


def main():
    # Simple CLI test
    engine = SentimentEngine(
        use_spacy=False
    )  # Default false to avoid model error if not present

    test_texts = [
        "I absolutely love this product! It's fantastic.",
        "The service was terrible and I am very angry.",
        "The package arrived on Tuesday.",
        "Not bad, but could be better.",
    ]

    print(f"{'Text':<50} | {'Sentiment':<10} | {'Score':<5}")
    print("-" * 75)
    print(f"Using SpaCy: {engine.use_spacy}")

    for text in test_texts:
        res = engine.analyze(text)
        print(f"{res.text[:47] + '...':<50} | {res.label:<10} | {res.score:.2f}")


if __name__ == "__main__":
    main()
