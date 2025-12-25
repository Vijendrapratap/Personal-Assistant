"""
Knowledge Graph infrastructure for Alfred.
Provides long-term memory and contextual understanding.
"""

from .neo4j_graph import Neo4jKnowledgeGraph

__all__ = ["Neo4jKnowledgeGraph"]
