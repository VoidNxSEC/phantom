"""
Anthropic Provider - Cloud LLM provider for Anthropic Claude models.

Supports Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku, and Claude 2 models.
Requires the `anthropic` Python package and an API key set in the
ANTHROPIC_API_KEY environment variable.
"""

import logging
import os
import time
from collections.abc import AsyncIterator

from phantom.providers.base import (
    AIProvider,
    GenerationResult,
    ProviderConfig,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """
    Anthropic API provider.

    Connects to the Anthropic REST API for message completion.
    Falls back gracefully if the anthropic package is not installed.

    Environment variables:
        ANTHROPIC_API_KEY  — API key (required for availability)
        ANTHROPIC_BASE_URL — Custom base URL (default: https://api.anthropic.com)
        ANTHROPIC_MODEL    — Default model (default: claude-3-5-sonnet-20241022)
    """

    MODELS = [
        {
            "id": "claude-3-5-sonnet-20241022",
            "name": "Claude 3.5 Sonnet",
            "context_length": 200_000,
        },
        {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "context_length": 200_000},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context_length": 200_000},
        {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "context_length": 200_000},
        {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "context_length": 200_000},
        {"id": "claude-2.1", "name": "Claude 2.1", "context_length": 200_000},
        {"id": "claude-2.0", "name": "Claude 2", "context_length": 100_000},
    ]

    _API_VERSION = "2023-06-01"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 120,
        config: ProviderConfig | None = None,
    ):
        if config is None:
            config = ProviderConfig(
                api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
                base_url=base_url
                or os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
                model=model or os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
                timeout=timeout,
            )
        super().__init__(config)
        self._client = None
        self._async_client = None
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return "anthropic"

    def is_available(self) -> bool:
        """Check if the provider is configured with a valid API key.

        Does NOT make a network request; only checks for the presence of
        an API key in the config.
        """
        if self._available is not None:
            return self._available

        if not self.config.api_key:
            logger.debug("Anthropic: no API key configured")
            self._available = False
            self._status = ProviderStatus.UNAVAILABLE
            return False

        self._available = True
        self._status = ProviderStatus.AVAILABLE
        return True

    def _get_client(self):
        """Lazy-initialize the Anthropic sync client."""
        if self._client is not None:
            return self._client

        try:
            from anthropic import Anthropic

            self._client = Anthropic(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        except ImportError:
            logger.error("Anthropic package not installed. Install it with: pip install anthropic")
            self._status = ProviderStatus.UNAVAILABLE
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            self._status = ProviderStatus.ERROR
            raise

        return self._client

    def _get_async_client(self):
        """Lazy-initialize the Anthropic async client."""
        if self._async_client is not None:
            return self._async_client

        try:
            from anthropic import AsyncAnthropic

            self._async_client = AsyncAnthropic(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        except ImportError:
            logger.error("Anthropic package not installed. Install it with: pip install anthropic")
            self._status = ProviderStatus.UNAVAILABLE
            raise
        except Exception as e:
            logger.error(f"Failed to initialize AsyncAnthropic client: {e}")
            self._status = ProviderStatus.ERROR
            raise

        return self._async_client

    def _build_messages(self, prompt: str, **kwargs) -> list[dict]:
        """Build the messages list for the Anthropic API.

        If a system prompt is provided via kwargs, it is extracted and
        returned separately.
        """
        messages = kwargs.pop("messages", None)
        if messages is not None:
            return messages

        return [{"role": "user", "content": prompt}]

    def generate(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs,
    ) -> GenerationResult:
        """Generate text using Anthropic messages API.

        Args:
            prompt: The input prompt for generation.
            max_tokens: Maximum tokens to generate (default: from config).
            temperature: Sampling temperature (default: from config).
            **kwargs: Additional arguments passed to the API
                      (e.g. system, stop_sequences, top_p, top_k).

        Returns:
            GenerationResult with the generated text and metadata.

        Raises:
            RuntimeError: If generation fails.
        """
        start_time = time.time()
        client = self._get_client()

        model = kwargs.pop("model", self.config.model)
        system_prompt = kwargs.pop("system", None)

        messages = self._build_messages(prompt, **kwargs)

        params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
        }

        if system_prompt:
            params["system"] = system_prompt

        # Pass through any remaining valid Anthropic parameters
        for key in ("stop_sequences", "top_p", "top_k", "metadata"):
            if key in kwargs:
                params[key] = kwargs.pop(key)

        try:
            response = client.messages.create(**params)

            latency = (time.time() - start_time) * 1000

            # Extract text from content blocks
            content_text = ""
            for block in response.content:
                if block.type == "text":
                    content_text += block.text

            return GenerationResult(
                text=content_text,
                tokens_used=(
                    response.usage.input_tokens + response.usage.output_tokens
                    if response.usage
                    else 0
                ),
                model=response.model,
                finish_reason=response.stop_reason or "stop",
                latency_ms=latency,
            )

        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"Anthropic generation failed: {e}") from e

    async def agenerate(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs,
    ) -> GenerationResult:
        """Async generation using Anthropic messages API."""
        start_time = time.time()
        client = self._get_async_client()

        model = kwargs.pop("model", self.config.model)
        system_prompt = kwargs.pop("system", None)

        messages = self._build_messages(prompt, **kwargs)

        params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
        }

        if system_prompt:
            params["system"] = system_prompt

        for key in ("stop_sequences", "top_p", "top_k", "metadata"):
            if key in kwargs:
                params[key] = kwargs.pop(key)

        try:
            response = await client.messages.create(**params)

            latency = (time.time() - start_time) * 1000

            content_text = ""
            for block in response.content:
                if block.type == "text":
                    content_text += block.text

            return GenerationResult(
                text=content_text,
                tokens_used=(
                    response.usage.input_tokens + response.usage.output_tokens
                    if response.usage
                    else 0
                ),
                model=response.model,
                finish_reason=response.stop_reason or "stop",
                latency_ms=latency,
            )

        except Exception as e:
            logger.error(f"Anthropic async generation failed: {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"Anthropic async generation failed: {e}") from e

    async def stream(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream tokens from Anthropic messages API.

        Yields content tokens as they are generated.
        """
        client = self._get_async_client()

        model = kwargs.pop("model", self.config.model)
        system_prompt = kwargs.pop("system", None)

        messages = self._build_messages(prompt, **kwargs)

        params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
            "stream": True,
        }

        if system_prompt:
            params["system"] = system_prompt

        for key in ("stop_sequences", "top_p", "top_k", "metadata"):
            if key in kwargs:
                params[key] = kwargs.pop(key)

        try:
            async with client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"Anthropic streaming failed: {e}") from e
