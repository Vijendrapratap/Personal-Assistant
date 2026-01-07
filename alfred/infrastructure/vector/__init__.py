"""
Vector Search Infrastructure.

Provides semantic search capabilities using vector embeddings.
"""

from alfred.infrastructure.vector.base import (
    BaseVectorStore,
    VectorDocument,
    SearchResult,
    EmbeddingProvider,
)
from alfred.infrastructure.vector.qdrant import QdrantVectorStore
from alfred.infrastructure.vector.embeddings import (
    OpenAIEmbeddings,
    get_embedding_provider,
)

__all__ = [
    "BaseVectorStore",
    "VectorDocument",
    "SearchResult",
    "EmbeddingProvider",
    "QdrantVectorStore",
    "OpenAIEmbeddings",
    "get_embedding_provider",
]
