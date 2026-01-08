"""
Phantom Analysis - Sentiment, AI analysis, and viability scoring.

Classes:
    SentimentEngine - Sentiment analysis engine
    SpectreAnalyzer - Comprehensive document analysis
    ViabilityScorer - Project viability assessment
    AIAnalyzer - AI-powered analysis
    LatencyOptimizer - Performance optimization
"""

def __getattr__(name):
    if name == "SentimentEngine" or name == "SentimentAnalyzer":
        from phantom.analysis.sentiment_analysis import SentimentEngine
        return SentimentEngine
    if name == "SpectreAnalyzer":
        from phantom.analysis.spectre import SpectreAnalyzer
        return SpectreAnalyzer
    if name == "ViabilityScorer":
        from phantom.analysis.viability_scorer import ViabilityScorer
        return ViabilityScorer
    if name == "AIAnalyzer":
        from phantom.analysis.ai_analyzer import AIAnalyzer
        return AIAnalyzer
    if name == "LatencyOptimizer":
        from phantom.analysis.latency_optimizer import LatencyOptimizer
        return LatencyOptimizer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "SentimentEngine",
    "SentimentAnalyzer",  # Alias for SentimentEngine
    "SpectreAnalyzer",
    "ViabilityScorer",
    "AIAnalyzer",
    "LatencyOptimizer",
]
