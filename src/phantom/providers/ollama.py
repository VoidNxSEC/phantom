"""
Ollama Provider - Local Ollama server.
"""

import os
import time
import logging
from typing import Optional

import requests

from phantom.providers.base import (
    AIProvider,
    ProviderConfig,
    ProviderStatus,
    GenerationResult,
)

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """Ollama local server provider."""
    
    DEFAULT_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.2"
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        config: Optional[ProviderConfig] = None,
    ):
        if config is None:
            config = ProviderConfig(
                base_url=base_url or os.environ.get("OLLAMA_URL", self.DEFAULT_URL),
                model=model or os.environ.get("OLLAMA_MODEL", self.DEFAULT_MODEL),
            )
        super().__init__(config)
    
    @property
    def name(self) -> str:
        return "ollama"
    
    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = requests.get(f"{self.config.base_url}/api/tags", timeout=5)
            available = response.status_code == 200
            self._status = ProviderStatus.AVAILABLE if available else ProviderStatus.UNAVAILABLE
            return available
        except Exception:
            self._status = ProviderStatus.UNAVAILABLE
            return False
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> GenerationResult:
        """Generate text using Ollama."""
        start_time = time.time()
        
        payload = {
            "model": kwargs.get("model", self.config.model),
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens or self.config.max_tokens,
                "temperature": temperature or self.config.temperature,
            }
        }
        
        try:
            response = requests.post(
                f"{self.config.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            data = response.json()
            
            latency = (time.time() - start_time) * 1000
            
            return GenerationResult(
                text=data.get("response", ""),
                tokens_used=data.get("eval_count", 0),
                model=data.get("model", self.config.model),
                finish_reason="stop",
                latency_ms=latency,
            )
        except requests.RequestException as e:
            logger.error(f"Ollama generation failed: {e}")
            self._status = ProviderStatus.ERROR
            raise RuntimeError(f"Generation failed: {e}") from e
