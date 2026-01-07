"""
LLM Provider Factory.

Creates and configures LLM providers based on configuration.
Supports multiple providers with easy switching.
"""

import os
from typing import Optional, Dict, Any, Type
from enum import Enum

from alfred.infrastructure.llm.base import BaseLLMProvider


class LLMProviderType(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    GROQ = "groq"
    TOGETHER = "together"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    MISTRAL = "mistral"
    QWEN = "qwen"
    MOCK = "mock"  # For testing


# Provider registry
_PROVIDER_REGISTRY: Dict[str, Type[BaseLLMProvider]] = {}


def register_provider(name: str):
    """Decorator to register a provider class."""
    def decorator(cls: Type[BaseLLMProvider]):
        _PROVIDER_REGISTRY[name] = cls
        return cls
    return decorator


class LLMFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create(
        provider: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider: Provider name (anthropic, openai, ollama, etc.)
            api_key: API key (will read from env if not provided)
            model: Model name (uses provider default if not specified)
            **kwargs: Additional provider-specific arguments

        Returns:
            Configured LLM provider instance

        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower()

        # Try registered providers first
        if provider in _PROVIDER_REGISTRY:
            provider_class = _PROVIDER_REGISTRY[provider]
            return provider_class(api_key=api_key, model=model, **kwargs)

        # Built-in providers
        if provider == LLMProviderType.ANTHROPIC:
            from alfred.infrastructure.llm.anthropic_adapter import AnthropicProvider
            key = api_key or os.getenv("ANTHROPIC_API_KEY")
            return AnthropicProvider(api_key=key, model=model, **kwargs)

        elif provider == LLMProviderType.OPENAI:
            from alfred.infrastructure.llm.openai_adapter import OpenAIProvider
            key = api_key or os.getenv("OPENAI_API_KEY")
            return OpenAIProvider(api_key=key, model=model, **kwargs)

        elif provider == LLMProviderType.OLLAMA:
            from alfred.infrastructure.llm.ollama_adapter import OllamaProvider
            base_url = kwargs.get("base_url", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
            return OllamaProvider(model=model, base_url=base_url, **kwargs)

        elif provider == LLMProviderType.GROQ:
            from alfred.infrastructure.llm.groq_adapter import GroqProvider
            key = api_key or os.getenv("GROQ_API_KEY")
            return GroqProvider(api_key=key, model=model, **kwargs)

        elif provider == LLMProviderType.GOOGLE:
            from alfred.infrastructure.llm.google_adapter import GoogleProvider
            key = api_key or os.getenv("GOOGLE_API_KEY")
            return GoogleProvider(api_key=key, model=model, **kwargs)

        elif provider == LLMProviderType.MOCK:
            from alfred.infrastructure.llm.mock_provider import MockLLMProvider
            return MockLLMProvider(**kwargs)

        else:
            available = list(LLMProviderType.__members__.keys())
            raise ValueError(
                f"Unknown LLM provider: {provider}. "
                f"Available providers: {available}"
            )

    @staticmethod
    def from_config(config: Dict[str, Any]) -> BaseLLMProvider:
        """
        Create provider from configuration dictionary.

        Config should include:
        - provider: Provider name
        - api_key: Optional API key
        - model: Optional model name
        - Any provider-specific settings
        """
        provider = config.pop("provider")
        return LLMFactory.create(provider, **config)


def get_llm_provider(
    provider: Optional[str] = None,
    **kwargs: Any,
) -> BaseLLMProvider:
    """
    Get an LLM provider instance.

    Convenience function that reads from environment if provider not specified.

    Args:
        provider: Provider name (defaults to LLM_PROVIDER env var)
        **kwargs: Provider configuration

    Returns:
        Configured LLM provider
    """
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "openai")

    return LLMFactory.create(provider, **kwargs)


def get_default_model(provider: str) -> str:
    """Get the default model for a provider."""
    defaults = {
        "anthropic": "claude-sonnet-4-20250514",
        "openai": "gpt-4o",
        "google": "gemini-1.5-pro",
        "groq": "llama-3.1-70b-versatile",
        "together": "meta-llama/Llama-3-70b-chat-hf",
        "ollama": "llama3",
        "deepseek": "deepseek-chat",
        "mistral": "mistral-large-latest",
        "qwen": "qwen-max",
    }
    return defaults.get(provider.lower(), "gpt-4o")
