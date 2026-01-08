"""
CORTEX - Cloud Provider Integration

Support for OpenAI, Anthropic, and other cloud LLM providers
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

# Optional imports
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class LLMConfig:
    """LLM configuration"""

    provider: str  # "local", "openai", "anthropic"
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    api_key: str | None = None


class CloudProviderClient:
    """Unified interface for cloud LLM providers"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize provider-specific client"""
        if self.config.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                )

            api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not provided")

            self.client = openai.OpenAI(api_key=api_key)

        elif self.config.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError(
                    "anthropic package not installed. Run: pip install anthropic"
                )

            api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not provided")

            self.client = Anthropic(api_key=api_key)

    def generate(self, prompt: str) -> str:
        """Generate completion"""
        if self.config.provider == "openai":
            return self._generate_openai(prompt)
        elif self.config.provider == "anthropic":
            return self._generate_anthropic(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def _generate_openai(self, prompt: str) -> str:
        """OpenAI completion"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model or "gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
            )

            return response.choices[0].message.content

        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            raise

    def _generate_anthropic(self, prompt: str) -> str:
        """Anthropic completion"""
        try:
            message = self.client.messages.create(
                model=self.config.model or "claude-3-5-sonnet-20241022",
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                messages=[{"role": "user", "content": prompt}],
            )

            return message.content[0].text

        except Exception as e:
            logging.error(f"Anthropic API error: {e}")
            raise


# Model presets
MODELS = {
    "local": {
        "qwen-30b": {"name": "Qwen3-Coder-30B-Q4_K_M", "context": 32768},
        "deepseek-r1": {"name": "DeepSeek-R1-Distill-14B", "context": 16384},
    },
    "openai": {
        "gpt-4-turbo": {"name": "gpt-4-turbo-preview", "context": 128000},
        "gpt-4o": {"name": "gpt-4o", "context": 128000},
        "gpt-3.5-turbo": {"name": "gpt-3.5-turbo", "context": 16384},
    },
    "anthropic": {
        "claude-3.5-sonnet": {"name": "claude-3-5-sonnet-20241022", "context": 200000},
        "claude-3-opus": {"name": "claude-3-opus-20240229", "context": 200000},
        "claude-3-haiku": {"name": "claude-3-haiku-20240307", "context": 200000},
    },
}


def get_available_models() -> dict[str, list[dict[str, Any]]]:
    """Get list of available models by provider"""
    result = {}

    # Always include local
    result["local"] = [{"id": k, **v} for k, v in MODELS["local"].items()]

    # OpenAI if available
    if OPENAI_AVAILABLE:
        result["openai"] = [{"id": k, **v} for k, v in MODELS["openai"].items()]

    # Anthropic if available
    if ANTHROPIC_AVAILABLE:
        result["anthropic"] = [{"id": k, **v} for k, v in MODELS["anthropic"].items()]

    return result
