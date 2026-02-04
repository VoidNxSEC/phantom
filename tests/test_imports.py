"""
Test all public imports to prevent circular dependencies and broken references.

This test suite ensures that all modules declared in __all__ can be imported
without errors. It catches issues like:
- Missing module files (e.g., phantom.providers.openai doesn't exist)
- Circular import dependencies
- Runtime import errors
"""

import pytest


class TestCoreImports:
    """Test core module imports."""

    def test_phantom_main_imports(self):
        """Verify main phantom module imports work."""
        from phantom import (
            __version__,
            __codename__,
            CortexProcessor,
            SemanticChunker,
            EmbeddingGenerator,
            SentimentEngine,
            SpectreAnalyzer,
            ViabilityScorer,
            DAGPipeline,
            PhantomPipeline,
            FileClassifier,
            DataSanitizer,
        )

        assert __version__ == "2.0.0"
        assert __codename__ == "PHANTOM"
        assert CortexProcessor is not None
        assert SemanticChunker is not None
        assert EmbeddingGenerator is not None

    def test_core_module_imports(self):
        """Verify phantom.core module imports work."""
        from phantom.core import (
            CortexProcessor,
            SemanticChunker,
            EmbeddingGenerator,
            DocumentInsights,
            Theme,
            Pattern,
            Learning,
            Concept,
            Recommendation,
        )

        assert CortexProcessor is not None
        assert SemanticChunker is not None
        assert EmbeddingGenerator is not None
        assert DocumentInsights is not None

    def test_analysis_module_imports(self):
        """Verify phantom.analysis module imports work."""
        from phantom.analysis import (
            SentimentEngine,
            SentimentAnalyzer,
            SpectreAnalyzer,
            ViabilityScorer,
            AIAnalyzer,
            LatencyOptimizer,
        )

        assert SentimentEngine is not None
        assert SentimentAnalyzer is SentimentEngine  # Should be alias
        assert SpectreAnalyzer is not None
        assert ViabilityScorer is not None

    def test_pipeline_module_imports(self):
        """Verify phantom.pipeline module imports work."""
        from phantom.pipeline import (
            DAGPipeline,
            PhantomPipeline,
            FileClassifier,
            DataSanitizer,
        )

        assert DAGPipeline is PhantomPipeline  # Should be alias
        assert PhantomPipeline is not None
        assert FileClassifier is not None
        assert DataSanitizer is not None

    def test_providers_module_imports(self):
        """Verify phantom.providers module imports work."""
        from phantom.providers import (
            AIProvider,
            ProviderConfig,
            LlamaCppProvider,
        )

        assert AIProvider is not None
        assert ProviderConfig is not None
        assert LlamaCppProvider is not None

    def test_providers_no_broken_references(self):
        """Verify removed providers don't accidentally get imported."""
        from phantom.providers import __all__

        # These should NOT be in __all__ anymore (missing implementation)
        assert "OpenAIProvider" not in __all__
        assert "AnthropicProvider" not in __all__
        assert "DeepSeekProvider" not in __all__

        # Only these should exist
        assert "AIProvider" in __all__
        assert "ProviderConfig" in __all__
        assert "LlamaCppProvider" in __all__


class TestRAGImports:
    """Test RAG module imports."""

    def test_rag_module_basic_import(self):
        """Verify phantom.rag module can be imported."""
        import phantom.rag

        assert phantom.rag is not None

    def test_vector_store_import(self):
        """Verify vector store can be imported."""
        from phantom.rag.vectors import FAISSVectorStore

        assert FAISSVectorStore is not None


class TestAPIImports:
    """Test API module imports."""

    def test_api_module_can_import(self):
        """Verify phantom.api module exists and can be imported."""
        import phantom.api

        assert phantom.api is not None


class TestCLIImports:
    """Test CLI module imports."""

    def test_cli_module_can_import(self):
        """Verify phantom.cli module exists and can be imported."""
        import phantom.cli

        assert phantom.cli is not None


class TestCircularImports:
    """Test for circular import issues."""

    def test_no_circular_imports_on_star_import(self):
        """Verify 'from phantom import *' doesn't cause circular imports."""
        # This should complete without hanging or raising ImportError
        from phantom import *  # noqa: F403

        # If we get here, no circular imports occurred
        assert True

    def test_all_submodules_can_be_imported_together(self):
        """Verify all submodules can be imported in sequence."""
        import phantom
        import phantom.core
        import phantom.analysis
        import phantom.pipeline
        import phantom.providers
        import phantom.rag
        import phantom.api
        import phantom.cli

        assert phantom is not None
        assert phantom.core is not None
        assert phantom.analysis is not None
        assert phantom.pipeline is not None
        assert phantom.providers is not None
        assert phantom.rag is not None
        assert phantom.api is not None
        assert phantom.cli is not None
