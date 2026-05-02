"""
Provider Registry — Factory for LLM provider instances.

Provides a single entry point to create and discover available providers
based on environment configuration.  New providers registered here are
automatically exposed through the API and CLI.

Usage:
    from phantom.providers.registry import get_provider, get_available_providers

    provider = get_provider("openai")
    result = provider.generate("Hello!")

    available = get_available_providers()
    # -> {"local": [...], "openai": [...], "anthropic": [...], "deepseek": [...]}
"""

import logging
from typing import Any

from phantom.providers.base import AIProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Registry — mapping of provider names to their constructor & model info
# ---------------------------------------------------------------------------

_ProviderConstructor = Any  # A callable that returns an AIProvider instance


def _build_llamacpp(**kwargs: Any) -> AIProvider:
    """Build a local LlamaCpp provider."""
    from phantom.providers.llamacpp import LlamaCppProvider

    return LlamaCppProvider(**kwargs)


def _build_openai(**kwargs: Any) -> AIProvider:
    """Build an OpenAI provider."""
    from phantom.providers.openai_provider import OpenAIProvider

    return OpenAIProvider(**kwargs)


def _build_anthropic(**kwargs: Any) -> AIProvider:
    """Build an Anthropic provider."""
    from phantom.providers.anthropic_provider import AnthropicProvider

    return AnthropicProvider(**kwargs)


def _build_deepseek(**kwargs: Any) -> AIProvider:
    """Build a DeepSeek provider."""
    from phantom.providers.deepseek_provider import DeepSeekProvider

    return DeepSeekProvider(**kwargs)


# Each entry: (constructor, default_config_overrides, model_list_getter)
_PROVIDER_REGISTRY: dict[str, dict[str, Any]] = {
    "local": {
        "constructor": _build_llamacpp,
        "models": lambda: (
            [
                {"id": "local-default", "name": "Local LLM (llama.cpp)"},
                {"id": "qwen-30b", "name": "Qwen 30B"},
                {"id": "llama-3-8b", "name": "Llama 3 8B"},
            ]
            if _is_local_available()
            else []
        ),
        "needs_api_key": False,
    },
    "openai": {
        "constructor": _build_openai,
        "models": lambda: [
            {"id": "gpt-4o", "name": "GPT-4o", "context_length": 128_000},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context_length": 128_000},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context_length": 128_000},
            {"id": "gpt-4", "name": "GPT-4", "context_length": 8_192},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context_length": 16_385},
        ],
        "needs_api_key": True,
        "env_key": "OPENAI_API_KEY",
    },
    "anthropic": {
        "constructor": _build_anthropic,
        "models": lambda: [
            {
                "id": "claude-3-5-sonnet-20241022",
                "name": "Claude 3.5 Sonnet",
                "context_length": 200_000,
            },
            {
                "id": "claude-3-5-haiku-20241022",
                "name": "Claude 3.5 Haiku",
                "context_length": 200_000,
            },
            {
                "id": "claude-3-opus-20240229",
                "name": "Claude 3 Opus",
                "context_length": 200_000,
            },
            {
                "id": "claude-3-sonnet-20240229",
                "name": "Claude 3 Sonnet",
                "context_length": 200_000,
            },
            {
                "id": "claude-3-haiku-20240307",
                "name": "Claude 3 Haiku",
                "context_length": 200_000,
            },
            {"id": "claude-2.1", "name": "Claude 2.1", "context_length": 200_000},
            {"id": "claude-2.0", "name": "Claude 2", "context_length": 100_000},
        ],
        "needs_api_key": True,
        "env_key": "ANTHROPIC_API_KEY",
    },
    "deepseek": {
        "constructor": _build_deepseek,
        "models": lambda: [
            {"id": "deepseek-chat", "name": "DeepSeek Chat (V3)", "context_length": 64_000},
            {
                "id": "deepseek-reasoner",
                "name": "DeepSeek Reasoner (R1)",
                "context_length": 64_000,
            },
        ],
        "needs_api_key": True,
        "env_key": "DEEPSEEK_API_KEY",
    },
}


def _is_local_available() -> bool:
    """Quick check if the local llama.cpp server might be reachable."""
    try:
        import requests  # noqa: F401
    except ImportError:
        return False
    return True


# Keep a cache of instantiated providers for reuse
_provider_cache: dict[str, AIProvider] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_provider(name: str, **kwargs: Any) -> AIProvider:
    """Get or create an LLM provider by name.

    Parameters
    ----------
    name : str
        One of ``"local"``, ``"openai"``, ``"anthropic"``, ``"deepseek"``.
    **kwargs
        Additional arguments forwarded to the provider constructor
        (e.g. *api_key*, *model*, *base_url*).

    Returns
    -------
    AIProvider
        A configured provider instance.

    Raises
    ------
    ValueError
        If *name* is not a recognised provider.
    RuntimeError
        If the provider's constructor fails.
    """
    if name in _provider_cache and not kwargs:
        return _provider_cache[name]

    entry = _PROVIDER_REGISTRY.get(name)
    if entry is None:
        raise ValueError(
            f"Unknown provider {name!r}. Available: {', '.join(sorted(_PROVIDER_REGISTRY))}"
        )

    try:
        provider = entry["constructor"](**kwargs)
    except Exception as exc:
        logger.error("Failed to construct provider %r: %s", name, exc)
        raise RuntimeError(f"Failed to construct provider {name!r}: {exc}") from exc

    # Cache only if no overrides were passed
    if not kwargs:
        _provider_cache[name] = provider

    return provider


def get_available_providers() -> dict[str, list[dict[str, Any]]]:
    """Return models grouped by provider, excluding unavailable ones.

    A provider is considered *available* when:
      - ``needs_api_key`` is *False*, OR
      - the environment variable named by ``env_key`` is set and non-empty.

    Returns
    -------
    dict[str, list[dict]]
        Keys are provider names (``"local"``, ``"openai"``, etc.).
        Values are lists of model descriptors ``{"id": …, "name": …}``.
    """
    import os

    result: dict[str, list[dict[str, Any]]] = {}
    for name, entry in _PROVIDER_REGISTRY.items():
        # Skip if it needs an API key and the env var is not set
        if entry["needs_api_key"]:
            env_key = entry.get("env_key", "")
            if not env_key or not os.environ.get(env_key, "").strip():
                continue

        # Quick availability check for local provider
        if name == "local":
            try:
                provider = get_provider(name)
                if not provider.is_available():
                    continue
            except Exception:
                continue

        try:
            models = entry["models"]()
            if models:
                result[name] = models
        except Exception as exc:
            logger.debug("Failed to get models for provider %r: %s", name, exc)
            continue

    return result


def clear_provider_cache() -> None:
    """Clear the provider instance cache.

    Call this if environment variables change at runtime
    (e.g. after settings are updated via the API).
    """
    _provider_cache.clear()
    logger.debug("Provider cache cleared")


__all__ = [
    "get_provider",
    "get_available_providers",
    "clear_provider_cache",
]
