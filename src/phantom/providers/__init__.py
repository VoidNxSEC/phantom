"""
Phantom Providers - LLM backend providers.

Classes:
    AIProvider - Abstract base for all providers
    ProviderConfig - Provider configuration model
    LlamaCppProvider - Local llama.cpp server (TURBO)

Note:
    Cloud providers (OpenAI, Anthropic, DeepSeek) are not yet implemented.
    Use LlamaCppProvider for local inference or extend AIProvider to add custom providers.
"""

from phantom.providers.base import AIProvider, ProviderConfig


def __getattr__(name):
    if name == "LlamaCppProvider":
        from phantom.providers.llamacpp import LlamaCppProvider

        return LlamaCppProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AIProvider",
    "ProviderConfig",
    "LlamaCppProvider",
]
