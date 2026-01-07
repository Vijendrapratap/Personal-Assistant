"""
Base Knowledge Graph Interface.

Defines the abstract interface for knowledge graph implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    USER = "user"
    PROJECT = "project"
    TASK = "task"
    PERSON = "person"
    CONCEPT = "concept"
    LEARNING = "learning"
    PREFERENCE = "preference"
    SKILL = "skill"
    ORGANIZATION = "organization"
    EVENT = "event"


class RelationType(str, Enum):
    """Types of relationships between entities."""
    # User relationships
    WORKS_ON = "WORKS_ON"
    KNOWS = "KNOWS"
    INTERESTED_IN = "INTERESTED_IN"
    HAS_LEARNING = "HAS_LEARNING"
    HAS_PREFERENCE = "HAS_PREFERENCE"
    HAS_SKILL = "HAS_SKILL"

    # Project relationships
    HAS_MEMBER = "HAS_MEMBER"
    BELONGS_TO = "BELONGS_TO"
    DEPENDS_ON = "DEPENDS_ON"

    # General
    RELATED_TO = "RELATED_TO"
    ABOUT = "ABOUT"
    MENTIONED_IN = "MENTIONED_IN"


@dataclass
class Entity:
    """
    An entity in the knowledge graph.

    Entities represent nodes with properties and type.
    """
    id: str
    type: EntityType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "properties": self.properties,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class Relationship:
    """
    A relationship between two entities.

    Relationships are directed edges with type and properties.
    """
    id: str
    type: RelationType
    source_id: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "properties": self.properties,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BaseKnowledgeGraph(ABC):
    """
    Abstract base class for knowledge graph implementations.

    Provides interface for:
    - Entity and relationship management
    - Knowledge storage and retrieval
    - Graph traversal and queries
    - Learning from user interactions
    """

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the knowledge graph backend is available."""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the knowledge graph (create indexes, etc.)."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connections and clean up resources."""
        pass

    # Entity operations

    @abstractmethod
    async def create_entity(self, entity: Entity) -> bool:
        """Create a new entity in the graph."""
        pass

    @abstractmethod
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        pass

    @abstractmethod
    async def update_entity(
        self,
        entity_id: str,
        properties: Dict[str, Any],
    ) -> bool:
        """Update entity properties."""
        pass

    @abstractmethod
    async def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and its relationships."""
        pass

    @abstractmethod
    async def find_entities(
        self,
        entity_type: Optional[EntityType] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[Entity]:
        """Find entities matching criteria."""
        pass

    # Relationship operations

    @abstractmethod
    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationType,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create a relationship between entities."""
        pass

    @abstractmethod
    async def get_relationships(
        self,
        entity_id: str,
        direction: str = "both",  # "outgoing", "incoming", "both"
        rel_type: Optional[RelationType] = None,
    ) -> List[Relationship]:
        """Get relationships for an entity."""
        pass

    @abstractmethod
    async def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship."""
        pass

    # Knowledge operations

    @abstractmethod
    async def store_learning(
        self,
        user_id: str,
        topic: str,
        content: str,
        source: str = "conversation",
        confidence: float = 0.8,
        related_entities: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Store a learning/knowledge item."""
        pass

    @abstractmethod
    async def get_learnings(
        self,
        user_id: str,
        topic: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Retrieve learnings for a user."""
        pass

    @abstractmethod
    async def get_relevant_context(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """Get relevant context for a query."""
        pass

    # Graph queries

    @abstractmethod
    async def traverse(
        self,
        start_entity_id: str,
        rel_types: Optional[List[RelationType]] = None,
        max_depth: int = 2,
    ) -> List[Dict[str, Any]]:
        """Traverse the graph from a starting entity."""
        pass

    @abstractmethod
    async def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 4,
    ) -> Optional[List[Dict[str, Any]]]:
        """Find a path between two entities."""
        pass

    # Analytics

    @abstractmethod
    async def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary statistics for a user's knowledge graph."""
        pass

    async def health_check(self) -> Dict[str, Any]:
        """Check knowledge graph health."""
        return {
            "healthy": self.is_available,
            "type": self.__class__.__name__,
        }
