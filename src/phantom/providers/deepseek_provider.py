"""
DeepSeek Provider - Cloud LLM provider for DeepSeek models.

Supports deepseek-chat and deepseek-reasoner models.
Uses the OpenAI-compatible API format (can reuse openai package or direct HTTP).
Requires an API key set in the DEEPSEEK_API_KEY environment variable.
"""

import json
import logging
import os
import time
from collections.abc import AsyncIterator

import httpx

from phantom.providers.base import (
    AIProvider,
    GenerationResult,
    ProviderConfig,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class DeepSeekProvider(AIProvider):
    """
    DeepSeek API provider.

    Connects to the DeepSeek REST API for chat completion.
    DeepSeek uses an OpenAI-compatible API format, so this provider makes
    direct HTTP requests (avoiding the openai package dependency).

    Environment variables:
        DEEPSEEK_API_KEY  — API key (required for availability)
        DEEPSEEK_BASE_URL — Custom base URL (default: https://api.deepseek.com)
        DEEPSEEK_MODEL    — Default model (default: deepseek-chat)
    """

    MODELS = [
        {"id": "deepseek-chat", "name": "DeepSeek Chat (V3)", "context_length": 64_000},
        {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner (R1)", "context_length": 64_000},
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
                api_key=api_key or os.environ.get("DEEPSEEK_API_KEY", ""),
                base_url=base_url
                or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                model=model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
                timeout=timeout,
            )
        super().__init__(config)
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return "deepseek"

    def is_available(self) -> bool:
        """Check if the provider is configured with a valid API key.

        Does NOT make a network request; only checks for the presence of
        an API key in the config.
        """
        if self._available is not None:
            return self._available

        if not self.config.api_key:
            logger.debug("DeepSeek: no API key configured")
            self._available = False
            self._status = ProviderStatus.UNAVAILABLE
            return False

        self._available = True
        self._status = ProviderStatus.AVAILABLE
        return True

    def _get_headers(self) -> dict[str, str]:
        """Build headers for DeepSeek API requests."""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    def _build_chat_params(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stream: bool = False,
        **kwargs,
    ) -> dict:
        """Build the request payload for the chat completions API."""
        model = kwargs.pop("model", self.config.model)

        messages = kwargs.pop("messages", None)
        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
            "stream": stream,
        }

        # Pass through optional parameters
        for key in ("top_p", "stop", "presence_penalty", "frequency_penalty"):
            if key in kwargs:
                params[key] = kwargs.pop(key)

        return params

    def _parse_response(self, data: dict, start_time: float) -> GenerationResult:
        """Parse a DeepSeek API response into a GenerationResult."""
        latency = (time.time() - start_time) * 1000
        choice = data.get("choices", [{}])[0] if data.get("choices") else {}

        return GenerationResult(
            text=choice.get("message", {}).get("content", ""),
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            model=data.get("model", self.config.model),
            finish_reason=choice.get("finish_reason", "stop"),
            latency_ms=latency,
        )

    def generate(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs,
    ) -> GenerationResult:
        """Generate text using DeepSeek chat completions API.

        Args:
            prompt: The input prompt for generation.
            max_tokens: Maximum tokens to generate (default: from config).
            temperature: Sampling temperature (default: from config).
            **kwargs: Additional arguments passed to the API
                      (e.g. top_p, stop, presence_penalty, frequency_penalty).

        Returns:
            GenerationResult with the generated text and metadata.

        Raises:
            RuntimeError: If generation fails.
        """
        start_time = time.time()

        params = self._build_chat_params(prompt, max_tokens, temperature, stream=False, **kwargs)

        try:
            response = httpx.post(
                f"{self.config.base_url}/v1/chat/completions",
                headers=self._get_headers(),
                json=params,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            data = response.json()

            return self._parse_response(data, start_time)

        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek generation failed (HTTP {e.response.status_code}): {e}")
            if e.response.status_code == 429:
                self._status = ProviderStatus.RATE_LIMITED
            else:
                self._status = ProviderStatus.ERROR
            raise RuntimeError(f"DeepSeek generation failed: {e}") from e
        except httpx.RequestError as e:
            logger.error(f"DeepSeek generation failed (connection error): {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"DeepSeek generation failed: {e}") from e
        except Exception as e:
            logger.error(f"DeepSeek generation failed: {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"DeepSeek generation failed: {e}") from e

    async def agenerate(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs,
    ) -> GenerationResult:
        """Async generation using DeepSeek chat completions API."""
        start_time = time.time()

        params = self._build_chat_params(prompt, max_tokens, temperature, stream=False, **kwargs)

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/v1/chat/completions",
                    headers=self._get_headers(),
                    json=params,
                )
                response.raise_for_status()
                data = response.json()

            return self._parse_response(data, start_time)

        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek async generation failed (HTTP {e.response.status_code}): {e}")
            if e.response.status_code == 429:
                self._status = ProviderStatus.RATE_LIMITED
            else:
                self._status = ProviderStatus.ERROR
            raise RuntimeError(f"DeepSeek async generation failed: {e}") from e
        except httpx.RequestError as e:
            logger.error(f"DeepSeek async generation failed (connection error): {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"DeepSeek async generation failed: {e}") from e
        except Exception as e:
            logger.error(f"DeepSeek async generation failed: {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"DeepSeek async generation failed: {e}") from e

    async def stream(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream tokens from DeepSeek chat completions API using SSE.

        Yields content tokens as they are generated.
        """
        params = self._build_chat_params(prompt, max_tokens, temperature, stream=True, **kwargs)

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.config.base_url}/v1/chat/completions",
                    headers=self._get_headers(),
                    json=params,
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = (
                                    data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                )
                                if delta:
                                    yield delta
                            except (ValueError, KeyError, IndexError):
                                continue

        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek streaming failed (HTTP {e.response.status_code}): {e}")
            if e.response.status_code == 429:
                self._status = ProviderStatus.RATE_LIMITED
            else:
                self._status = ProviderStatus.ERROR
            raise RuntimeError(f"DeepSeek streaming failed: {e}") from e
        except httpx.RequestError as e:
            logger.error(f"DeepSeek streaming failed (connection error): {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"DeepSeek streaming failed: {e}") from e
        except Exception as e:
            logger.error(f"DeepSeek streaming failed: {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"DeepSeek streaming failed: {e}") from e
