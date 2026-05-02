"""
Phantom Providers — LLM backend providers.

Available providers:
    LlamaCppProvider   — Local llama.cpp server (TURBO)
    OpenAIProvider     — OpenAI GPT-4o, GPT-4, GPT-3.5 (cloud)
    AnthropicProvider  — Anthropic Claude 3.5, Claude 3, Claude 2 (cloud)
    DeepSeekProvider   — DeepSeek Chat (V3) & Reasoner (R1) (cloud)

Registry:
    get_provider(name)        — Factory: get or create a provider by name
    get_available_providers() — List models grouped by available provider
    clear_provider_cache()    — Reset the provider instance cache
"""

from phantom.providers.base import AIProvider, GenerationResult, ProviderConfig, ProviderStatus
from phantom.providers.registry import (
    clear_provider_cache,
    get_available_providers,
    get_provider,
)


def __getattr__(name: str):
    """Lazy-load provider classes to avoid expensive imports at module level."""
    _lazy_map = {
        "LlamaCppProvider": ("phantom.providers.llamacpp", "LlamaCppProvider"),
        "OpenAIProvider": ("phantom.providers.openai_provider", "OpenAIProvider"),
        "AnthropicProvider": ("phantom.providers.anthropic_provider", "AnthropicProvider"),
        "DeepSeekProvider": ("phantom.providers.deepseek_provider", "DeepSeekProvider"),
    }
    if name in _lazy_map:
        module_path, class_name = _lazy_map[name]
        import importlib

        mod = importlib.import_module(module_path)
        return getattr(mod, class_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Base
    "AIProvider",
    "ProviderConfig",
    "GenerationResult",
    "ProviderStatus",
    # Concrete providers
    "LlamaCppProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "DeepSeekProvider",
    # Registry
    "get_provider",
    "get_available_providers",
    "clear_provider_cache",
]
