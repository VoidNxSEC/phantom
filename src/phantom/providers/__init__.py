"""
Phantom Providers - LLM backend providers.

Classes:
    AIProvider - Abstract base for all providers
    LlamaCppProvider - Local llama.cpp server (TURBO)
    OpenAIProvider - OpenAI API
    AnthropicProvider - Anthropic Claude API
    DeepSeekProvider - DeepSeek API
"""

from phantom.providers.base import AIProvider, ProviderConfig

def __getattr__(name):
    if name == "LlamaCppProvider":
        from phantom.providers.llamacpp import LlamaCppProvider
        return LlamaCppProvider
    if name == "OpenAIProvider":
        from phantom.providers.openai import OpenAIProvider
        return OpenAIProvider
    if name == "AnthropicProvider":
        from phantom.providers.anthropic import AnthropicProvider
        return AnthropicProvider
    if name == "DeepSeekProvider":
        from phantom.providers.deepseek import DeepSeekProvider
        return DeepSeekProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "AIProvider",
    "ProviderConfig",
    "LlamaCppProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "DeepSeekProvider",
]

