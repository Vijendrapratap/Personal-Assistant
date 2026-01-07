"""
Embedding Providers.

Generate vector embeddings from text using various models.
"""

import os
import logging
from typing import List, Optional

from alfred.infrastructure.vector.base import EmbeddingProvider


logger = logging.getLogger("alfred.vector.embeddings")


class OpenAIEmbeddings(EmbeddingProvider):
    """
    OpenAI embeddings provider.

    Uses text-embedding-3-small by default (1536 dimensions).
    """

    MODELS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
    ):
        """
        Initialize OpenAI embeddings.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Embedding model name
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "openai package not installed. "
                "Install with: pip install openai"
            )

        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError("OpenAI API key required")

        self._model = model
        self._dimension = self.MODELS.get(model, 1536)
        self.client = AsyncOpenAI(api_key=self._api_key)

    @property
    def embedding_dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        response = await self.client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        # OpenAI supports batching
        response = await self.client.embeddings.create(
            model=self._model,
            input=texts,
        )
        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]


class AnthropicVoyageEmbeddings(EmbeddingProvider):
    """
    Voyage AI embeddings (recommended for use with Claude).

    Uses voyage-2 by default (1024 dimensions).
    """

    MODELS = {
        "voyage-2": 1024,
        "voyage-large-2": 1536,
        "voyage-code-2": 1536,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "voyage-2",
    ):
        """
        Initialize Voyage embeddings.

        Args:
            api_key: Voyage API key (defaults to VOYAGE_API_KEY env var)
            model: Embedding model name
        """
        self._api_key = api_key or os.getenv("VOYAGE_API_KEY")
        if not self._api_key:
            raise ValueError("Voyage API key required")

        self._model = model
        self._dimension = self.MODELS.get(model, 1024)

    @property
    def embedding_dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.voyageai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "input": text,
                },
            ) as response:
                data = await response.json()
                return data["data"][0]["embedding"]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.voyageai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "input": texts,
                },
            ) as response:
                data = await response.json()
                sorted_data = sorted(data["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in sorted_data]


class LocalEmbeddings(EmbeddingProvider):
    """
    Local embeddings using sentence-transformers.

    Good for offline use or cost savings.
    """

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        """
        Initialize local embeddings.

        Args:
            model: Sentence transformer model name
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers package not installed. "
                "Install with: pip install sentence-transformers"
            )

        self._model_name = model
        self._model = SentenceTransformer(model)
        self._dimension = self._model.get_sentence_embedding_dimension()

    @property
    def embedding_dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        import asyncio
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self._model.encode(text).tolist()
        )
        return embedding

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        import asyncio
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(texts).tolist()
        )
        return embeddings


def get_embedding_provider(
    provider: str = "openai",
    **kwargs,
) -> EmbeddingProvider:
    """
    Factory function to get an embedding provider.

    Args:
        provider: Provider name ("openai", "voyage", "local")
        **kwargs: Provider-specific arguments

    Returns:
        Embedding provider instance
    """
    providers = {
        "openai": OpenAIEmbeddings,
        "voyage": AnthropicVoyageEmbeddings,
        "local": LocalEmbeddings,
    }

    provider_class = providers.get(provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown embedding provider: {provider}")

    return provider_class(**kwargs)
