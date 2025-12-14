"""
Phantom Analysis - Sentiment, entities, topics, and viability scoring.

Classes:
    SentimentAnalyzer - Multi-dimensional sentiment analysis
    EntityExtractor - Named entity recognition
    TopicModeler - Topic modeling and extraction
    ViabilityScorer - Project viability assessment
"""

def __getattr__(name):
    if name == "SentimentAnalyzer":
        from phantom.analysis.sentiment import SentimentAnalyzer
        return SentimentAnalyzer
    if name == "EntityExtractor":
        from phantom.analysis.entities import EntityExtractor
        return EntityExtractor
    if name == "TopicModeler":
        from phantom.analysis.topics import TopicModeler
        return TopicModeler
    if name == "ViabilityScorer":
        from phantom.analysis.viability import ViabilityScorer
        return ViabilityScorer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "SentimentAnalyzer",
    "EntityExtractor", 
    "TopicModeler",
    "ViabilityScorer",
]
