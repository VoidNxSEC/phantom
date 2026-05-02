"""
OpenAI Provider - Cloud LLM provider for OpenAI models.

Supports GPT-4o, GPT-4-turbo, GPT-4, and GPT-3.5-turbo models.
Requires the `openai` Python package and an API key set in the
OPENAI_API_KEY environment variable.
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


class OpenAIProvider(AIProvider):
    """
    OpenAI API provider.

    Connects to the OpenAI REST API for chat completion.
    Falls back gracefully if the openai package is not installed.

    Environment variables:
        OPENAI_API_KEY  — API key (required for availability)
        OPENAI_BASE_URL — Custom base URL (default: https://api.openai.com/v1)
        OPENAI_MODEL    — Default model (default: gpt-4o)
    """

    MODELS = [
        {"id": "gpt-4o", "name": "GPT-4o", "context_length": 128_000},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context_length": 128_000},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context_length": 128_000},
        {"id": "gpt-4", "name": "GPT-4", "context_length": 8_192},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context_length": 16_385},
    ]

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
                api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
                base_url=base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                model=model or os.environ.get("OPENAI_MODEL", "gpt-4o"),
                timeout=timeout,
            )
        super().__init__(config)
        self._client = None
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return "openai"

    def is_available(self) -> bool:
        """Check if the provider is configured with a valid API key.

        Does NOT make a network request; only checks for the presence of
        an API key in the config.
        """
        if self._available is not None:
            return self._available

        if not self.config.api_key:
            logger.debug("OpenAI: no API key configured")
            self._available = False
            self._status = ProviderStatus.UNAVAILABLE
            return False

        self._available = True
        self._status = ProviderStatus.AVAILABLE
        return True

    def _get_client(self):
        """Lazy-initialize the OpenAI client."""
        if self._client is not None:
            return self._client

        try:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        except ImportError:
            logger.error(
                "OpenAI package not installed. Install it with: pip install openai"
            )
            self._status = ProviderStatus.UNAVAILABLE
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self._status = ProviderStatus.ERROR
            raise

        return self._client

    def generate(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs,
    ) -> GenerationResult:
        """Generate text using OpenAI chat completions API.

        Args:
            prompt: The input prompt for generation.
            max_tokens: Maximum tokens to generate (default: from config).
            temperature: Sampling temperature (default: from config).
            **kwargs: Additional arguments passed to the API
                      (e.g. stop, top_p, presence_penalty, frequency_penalty).

        Returns:
            GenerationResult with the generated text and metadata.

        Raises:
            RuntimeError: If generation fails.
        """
        start_time = time.time()
        client = self._get_client()

        model = kwargs.pop("model", self.config.model)
        messages = [{"role": "user", "content": prompt}]

        # Support chat history via kwargs
        if "messages" in kwargs:
            messages = kwargs.pop("messages")

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                top_p=kwargs.pop("top_p", self.config.top_p),
                **kwargs,
            )

            latency = (time.time() - start_time) * 1000
            choice = response.choices[0]

            return GenerationResult(
                text=choice.message.content or "",
                tokens_used=response.usage.total_tokens if response.usage else 0,
                model=response.model,
                finish_reason=choice.finish_reason or "stop",
                latency_ms=latency,
            )

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"OpenAI generation failed: {e}") from e

    async def agenerate(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs,
    ) -> GenerationResult:
        """Async generation using OpenAI async client."""
        start_time = time.time()

        try:
            from openai import AsyncOpenAI

            async_client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        except ImportError:
            logger.error(
                "OpenAI package not installed. Install it with: pip install openai"
            )
            self._status = ProviderStatus.UNAVAILABLE
            raise
        except Exception as e:
            logger.error(f"Failed to initialize AsyncOpenAI client: {e}")
            self._status = ProviderStatus.ERROR
            raise

        model = kwargs.pop("model", self.config.model)
        messages = [{"role": "user", "content": prompt}]
        if "messages" in kwargs:
            messages = kwargs.pop("messages")

        try:
            response = await async_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                top_p=kwargs.pop("top_p", self.config.top_p),
                **kwargs,
            )

            latency = (time.time() - start_time) * 1000
            choice = response.choices[0]

            return GenerationResult(
                text=choice.message.content or "",
                tokens_used=response.usage.total_tokens if response.usage else 0,
                model=response.model,
                finish_reason=choice.finish_reason or "stop",
                latency_ms=latency,
            )

        except Exception as e:
            logger.error(f"OpenAI async generation failed: {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"OpenAI async generation failed: {e}") from e

    async def stream(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream tokens from OpenAI chat completions API.

        Yields content tokens as they are generated.
        """
        try:
            from openai import AsyncOpenAI

            async_client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        except ImportError:
            logger.error(
                "OpenAI package not installed. Install it with: pip install openai"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize AsyncOpenAI client: {e}")
            raise

        model = kwargs.pop("model", self.config.model)
        messages = [{"role": "user", "content": prompt}]
        if "messages" in kwargs:
            messages = kwargs.pop("messages")

        try:
            stream = await async_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                top_p=kwargs.pop("top_p", self.config.top_p),
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"OpenAI streaming failed: {e}") from e
