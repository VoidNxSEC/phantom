"""
Base classes for AI providers.

All LLM providers inherit from AIProvider and implement the generate method.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, AsyncIterator
from enum import Enum


class ProviderStatus(Enum):
    """Provider availability status."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    timeout: int = 120
    max_tokens: int = 2048
    temperature: float = 0.3
    top_p: float = 0.9
    max_retries: int = 3
    retry_delay: float = 2.0
    headers: dict = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Result from a generation request."""
    text: str
    tokens_used: int = 0
    model: str = ""
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    cached: bool = False


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or ProviderConfig()
        self._status: ProviderStatus = ProviderStatus.UNAVAILABLE
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        ...
    
    @property
    def status(self) -> ProviderStatus:
        """Current provider status."""
        return self._status
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured."""
        ...
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Provider-specific options
            
        Returns:
            GenerationResult with generated text
        """
        ...
    
    async def agenerate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> GenerationResult:
        """Async version of generate. Default implementation wraps sync."""
        import asyncio
        return await asyncio.to_thread(
            self.generate, prompt, max_tokens, temperature, **kwargs
        )
    
    async def stream(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream generation tokens.
        
        Default implementation yields full result as single chunk.
        Providers should override for true streaming.
        """
        result = await self.agenerate(prompt, **kwargs)
        yield result.text
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, status={self.status.value})"
