"""
Qdrant Vector Store Implementation.

High-performance vector search using Qdrant.
"""

import os
import logging
import uuid
from typing import List, Optional, Dict, Any

from alfred.infrastructure.vector.base import (
    BaseVectorStore,
    VectorDocument,
    SearchResult,
    EmbeddingProvider,
)


logger = logging.getLogger("alfred.vector.qdrant")


class QdrantVectorStore(BaseVectorStore):
    """
    Qdrant vector store implementation.

    Features:
    - High-performance similarity search
    - Metadata filtering
    - Payload storage
    - Horizontal scaling
    """

    DEFAULT_COLLECTION = "alfred_knowledge"

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: str = DEFAULT_COLLECTION,
        prefer_grpc: bool = True,
    ):
        """
        Initialize Qdrant vector store.

        Args:
            embedding_provider: Provider for generating embeddings
            url: Qdrant server URL (defaults to QDRANT_URL env var)
            api_key: Qdrant API key (defaults to QDRANT_API_KEY env var)
            collection_name: Name of the collection to use
            prefer_grpc: Use gRPC for better performance
        """
        try:
            from qdrant_client import QdrantClient, AsyncQdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError:
            raise ImportError(
                "qdrant-client package not installed. "
                "Install with: pip install qdrant-client"
            )

        self._url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self._api_key = api_key or os.getenv("QDRANT_API_KEY")
        self._collection_name = collection_name
        self._embedding_provider = embedding_provider
        self._prefer_grpc = prefer_grpc

        # Initialize client
        self.client = AsyncQdrantClient(
            url=self._url,
            api_key=self._api_key,
            prefer_grpc=prefer_grpc,
        )

        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the vector store and create collection if needed."""
        from qdrant_client.models import Distance, VectorParams

        try:
            # Check if collection exists
            collections = await self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self._collection_name not in collection_names:
                # Create collection with appropriate vector size
                await self.client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(
                        size=self._embedding_provider.embedding_dimension,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: {self._collection_name}")

            self._initialized = True
            logger.info(f"Qdrant vector store initialized: {self._url}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            return False

    async def add_document(self, document: VectorDocument) -> bool:
        """Add a single document to the store."""
        from qdrant_client.models import PointStruct

        try:
            # Generate embedding if not provided
            if document.embedding is None:
                document.embedding = await self._embedding_provider.embed_text(
                    document.content
                )

            # Create point
            point = PointStruct(
                id=document.id,
                vector=document.embedding,
                payload={
                    "content": document.content,
                    **document.metadata,
                },
            )

            # Upsert to collection
            await self.client.upsert(
                collection_name=self._collection_name,
                points=[point],
            )

            return True

        except Exception as e:
            logger.error(f"Failed to add document {document.id}: {e}")
            return False

    async def add_documents(self, documents: List[VectorDocument]) -> int:
        """Add multiple documents to the store."""
        from qdrant_client.models import PointStruct

        if not documents:
            return 0

        try:
            # Get embeddings for documents without them
            texts_to_embed = []
            embed_indices = []

            for i, doc in enumerate(documents):
                if doc.embedding is None:
                    texts_to_embed.append(doc.content)
                    embed_indices.append(i)

            if texts_to_embed:
                embeddings = await self._embedding_provider.embed_texts(texts_to_embed)
                for i, embedding in zip(embed_indices, embeddings):
                    documents[i].embedding = embedding

            # Create points
            points = [
                PointStruct(
                    id=doc.id,
                    vector=doc.embedding,
                    payload={
                        "content": doc.content,
                        **doc.metadata,
                    },
                )
                for doc in documents
            ]

            # Batch upsert
            await self.client.upsert(
                collection_name=self._collection_name,
                points=points,
            )

            return len(documents)

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return 0

    async def search(
        self,
        query: str,
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0,
    ) -> List[SearchResult]:
        """Search for similar documents."""
        # Generate query embedding
        query_embedding = await self._embedding_provider.embed_text(query)
        return await self.search_by_vector(
            vector=query_embedding,
            limit=limit,
            filter=filter,
            score_threshold=score_threshold,
        )

    async def search_by_vector(
        self,
        vector: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0,
    ) -> List[SearchResult]:
        """Search using a pre-computed vector."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        try:
            # Build filter if provided
            qdrant_filter = None
            if filter:
                conditions = []
                for key, value in filter.items():
                    if isinstance(value, list):
                        # Match any value in list
                        for v in value:
                            conditions.append(
                                FieldCondition(key=key, match=MatchValue(value=v))
                            )
                    else:
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                if conditions:
                    qdrant_filter = Filter(should=conditions)

            # Perform search
            results = await self.client.search(
                collection_name=self._collection_name,
                query_vector=vector,
                limit=limit,
                query_filter=qdrant_filter,
                score_threshold=score_threshold,
            )

            # Convert to SearchResult objects
            search_results = []
            for result in results:
                payload = result.payload or {}
                doc = VectorDocument(
                    id=str(result.id),
                    content=payload.pop("content", ""),
                    metadata=payload,
                )
                search_results.append(
                    SearchResult(
                        document=doc,
                        score=result.score,
                    )
                )

            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get a document by ID."""
        try:
            results = await self.client.retrieve(
                collection_name=self._collection_name,
                ids=[doc_id],
                with_payload=True,
                with_vectors=True,
            )

            if not results:
                return None

            point = results[0]
            payload = point.payload or {}

            return VectorDocument(
                id=str(point.id),
                content=payload.pop("content", ""),
                metadata=payload,
                embedding=point.vector if hasattr(point, "vector") else None,
            )

        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None

    async def update_document(
        self,
        doc_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update a document."""
        try:
            # Get existing document
            existing = await self.get_document(doc_id)
            if not existing:
                return False

            # Update content and re-embed if needed
            if content is not None:
                existing.content = content
                existing.embedding = await self._embedding_provider.embed_text(content)

            # Update metadata
            if metadata is not None:
                existing.metadata.update(metadata)

            # Re-add document
            return await self.add_document(existing)

        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            return False

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        try:
            await self.client.delete(
                collection_name=self._collection_name,
                points_selector=[doc_id],
            )
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False

    async def delete_by_filter(self, filter: Dict[str, Any]) -> int:
        """Delete documents matching a filter."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        try:
            # Build filter
            conditions = []
            for key, value in filter.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )

            if not conditions:
                return 0

            qdrant_filter = Filter(must=conditions)

            # Delete by filter
            result = await self.client.delete(
                collection_name=self._collection_name,
                points_selector=qdrant_filter,
            )

            # Qdrant doesn't return count, estimate from status
            return 1 if result else 0

        except Exception as e:
            logger.error(f"Failed to delete by filter: {e}")
            return 0

    async def count(self, filter: Optional[Dict[str, Any]] = None) -> int:
        """Count documents in the store."""
        try:
            collection_info = await self.client.get_collection(
                collection_name=self._collection_name
            )
            return collection_info.points_count

        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0

    async def health_check(self) -> Dict[str, Any]:
        """Check Qdrant health."""
        try:
            # Get collection info
            collection_info = await self.client.get_collection(
                collection_name=self._collection_name
            )

            return {
                "healthy": True,
                "url": self._url,
                "collection": self._collection_name,
                "document_count": collection_info.points_count,
                "vector_dimension": self._embedding_provider.embedding_dimension,
                "embedding_model": self._embedding_provider.model_name,
            }

        except Exception as e:
            return {
                "healthy": False,
                "url": self._url,
                "error": str(e),
            }

    # Alfred-specific convenience methods

    async def add_knowledge(
        self,
        user_id: str,
        content: str,
        source: str = "user",
        doc_type: str = "knowledge",
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Add a knowledge entry for a user.

        Returns the document ID.
        """
        doc_id = str(uuid.uuid4())
        doc = VectorDocument(
            id=doc_id,
            content=content,
            metadata={
                "user_id": user_id,
                "source": source,
                "type": doc_type,
                "tags": tags or [],
            },
        )

        await self.add_document(doc)
        return doc_id

    async def search_user_knowledge(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        doc_type: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search knowledge for a specific user.
        """
        filter_dict = {"user_id": user_id}
        if doc_type:
            filter_dict["type"] = doc_type

        return await self.search(
            query=query,
            limit=limit,
            filter=filter_dict,
        )

    async def get_relevant_context(
        self,
        user_id: str,
        query: str,
        max_tokens: int = 2000,
    ) -> str:
        """
        Get relevant context for a query, formatted for LLM consumption.

        Retrieves and formats the most relevant documents.
        """
        results = await self.search_user_knowledge(
            user_id=user_id,
            query=query,
            limit=10,
        )

        if not results:
            return ""

        # Build context string with token budget
        context_parts = []
        estimated_tokens = 0

        for result in results:
            content = result.document.content
            # Rough token estimate
            content_tokens = len(content) // 4

            if estimated_tokens + content_tokens > max_tokens:
                break

            context_parts.append(
                f"[Source: {result.document.metadata.get('source', 'unknown')}, "
                f"Score: {result.score:.2f}]\n{content}"
            )
            estimated_tokens += content_tokens

        return "\n\n---\n\n".join(context_parts)
