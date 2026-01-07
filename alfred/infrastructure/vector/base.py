"""
Base Vector Store Interface.

Defines the abstract interface for vector stores.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Types of documents that can be stored."""
    NOTE = "note"
    TASK = "task"
    PROJECT = "project"
    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    FILE = "file"
    WEB = "web"


@dataclass
class VectorDocument:
    """
    Document to be stored in vector store.

    Attributes:
        id: Unique document identifier
        content: Text content to embed
        metadata: Additional metadata (type, user_id, timestamps, etc.)
        embedding: Pre-computed embedding vector (optional)
    """
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

    def __post_init__(self):
        # Ensure required metadata
        if "created_at" not in self.metadata:
            self.metadata["created_at"] = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
        }


@dataclass
class SearchResult:
    """
    Result from vector search.

    Attributes:
        document: The matched document
        score: Similarity score (higher is better)
        highlights: Optional highlighted text snippets
    """
    document: VectorDocument
    score: float
    highlights: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.document.id,
            "content": self.document.content,
            "metadata": self.document.metadata,
            "score": self.score,
            "highlights": self.highlights,
        }


class EmbeddingProvider(ABC):
    """
    Abstract embedding provider.

    Generates vector embeddings from text.
    """

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this provider."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name of the embedding model."""
        pass

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass


class BaseVectorStore(ABC):
    """
    Abstract vector store interface.

    Provides semantic search capabilities over documents.
    """

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the vector store.

        Creates collections/indexes if needed.

        Returns:
            True if initialization successful
        """
        pass

    @abstractmethod
    async def add_document(self, document: VectorDocument) -> bool:
        """
        Add a single document to the store.

        Args:
            document: Document to add

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def add_documents(self, documents: List[VectorDocument]) -> int:
        """
        Add multiple documents to the store.

        Args:
            documents: Documents to add

        Returns:
            Number of documents successfully added
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0,
    ) -> List[SearchResult]:
        """
        Search for similar documents.

        Args:
            query: Search query text
            limit: Maximum number of results
            filter: Metadata filter conditions
            score_threshold: Minimum similarity score

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def search_by_vector(
        self,
        vector: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0,
    ) -> List[SearchResult]:
        """
        Search using a pre-computed vector.

        Args:
            vector: Query embedding vector
            limit: Maximum number of results
            filter: Metadata filter conditions
            score_threshold: Minimum similarity score

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """
        Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_document(
        self,
        doc_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update a document.

        Args:
            doc_id: Document ID
            content: New content (re-embeds if provided)
            metadata: Updated metadata

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def delete_by_filter(self, filter: Dict[str, Any]) -> int:
        """
        Delete documents matching a filter.

        Args:
            filter: Metadata filter conditions

        Returns:
            Number of documents deleted
        """
        pass

    @abstractmethod
    async def count(self, filter: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents in the store.

        Args:
            filter: Optional filter conditions

        Returns:
            Document count
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        Check vector store health.

        Returns:
            Health status and details
        """
        try:
            count = await self.count()
            return {
                "healthy": True,
                "document_count": count,
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }
