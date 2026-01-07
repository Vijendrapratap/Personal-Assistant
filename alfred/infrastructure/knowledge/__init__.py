"""
Knowledge Graph Infrastructure.

Provides graph-based knowledge storage and querying.
Supports long-term memory and contextual understanding.
"""

from alfred.infrastructure.knowledge.base import (
    BaseKnowledgeGraph,
    Entity,
    Relationship,
    EntityType,
    RelationType,
)
from alfred.infrastructure.knowledge.neo4j_graph import Neo4jKnowledgeGraph

__all__ = [
    "BaseKnowledgeGraph",
    "Entity",
    "Relationship",
    "EntityType",
    "RelationType",
    "Neo4jKnowledgeGraph",
]
