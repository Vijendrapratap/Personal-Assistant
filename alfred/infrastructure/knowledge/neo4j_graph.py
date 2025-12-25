"""
Neo4j Knowledge Graph Provider for Alfred.

This module provides a knowledge graph implementation using Neo4j for:
- Storing and retrieving user knowledge/learnings
- Understanding relationships between projects, tasks, people, and concepts
- Building long-term memory that improves over time
- Enabling intelligent context retrieval for conversations

Graph Structure:
- User nodes: The user profile and preferences
- Project nodes: Projects the user is involved with
- Person nodes: People the user interacts with
- Concept nodes: Topics, skills, interests
- Task nodes: Tasks with context
- Learning nodes: Things Alfred has learned about the user

Relationships:
- (User)-[:WORKS_ON]->(Project)
- (User)-[:KNOWS]->(Person)
- (User)-[:INTERESTED_IN]->(Concept)
- (Project)-[:HAS_MEMBER]->(Person)
- (Task)-[:BELONGS_TO]->(Project)
- (Learning)-[:ABOUT]->(Entity)
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import neo4j, handle gracefully if not installed
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j package not installed. Knowledge graph features disabled.")


class Neo4jKnowledgeGraph:
    """
    Knowledge Graph implementation using Neo4j.

    Provides methods for:
    - Storing user learnings and preferences
    - Building relationship graphs
    - Retrieving contextual knowledge for conversations
    - Understanding patterns in user behavior
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI (default: from env NEO4J_URI)
            username: Neo4j username (default: from env NEO4J_USER)
            password: Neo4j password (default: from env NEO4J_PASSWORD)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")

        self.driver = None
        self.enabled = False

        if NEO4J_AVAILABLE:
            try:
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password)
                )
                # Verify connection
                self.driver.verify_connectivity()
                self.enabled = True
                logger.info("Connected to Neo4j knowledge graph")
            except Exception as e:
                logger.warning(f"Failed to connect to Neo4j: {e}")
                self.enabled = False

    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()

    def _run_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute a Cypher query and return results."""
        if not self.enabled:
            return []

        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    # ============================================
    # USER MANAGEMENT
    # ============================================

    def create_user_node(self, user_id: str, email: str, profile: Dict = None) -> bool:
        """Create or update a user node in the graph."""
        query = """
        MERGE (u:User {user_id: $user_id})
        SET u.email = $email,
            u.updated_at = datetime()
        """
        if profile:
            query += """
            SET u.bio = $bio,
                u.work_type = $work_type,
                u.personality = $personality
            """

        params = {
            "user_id": user_id,
            "email": email,
            "bio": profile.get("bio", "") if profile else "",
            "work_type": profile.get("work_type", "") if profile else "",
            "personality": profile.get("personality_prompt", "") if profile else "",
        }

        try:
            self._run_query(query, params)
            return True
        except Exception as e:
            logger.error(f"Failed to create user node: {e}")
            return False

    # ============================================
    # LEARNING STORAGE
    # ============================================

    def store_learning(
        self,
        user_id: str,
        topic: str,
        content: str,
        source: str = "conversation",
        confidence: float = 0.8,
        related_entities: List[str] = None,
    ) -> Optional[str]:
        """
        Store a learning/knowledge item in the graph.

        Args:
            user_id: The user ID
            topic: Topic category (preference, fact, pattern, etc.)
            content: The actual learning content
            source: Where this was learned from
            confidence: Confidence level (0-1)
            related_entities: List of entity names this learning relates to

        Returns:
            Learning ID if successful, None otherwise
        """
        import uuid
        learning_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {user_id: $user_id})
        CREATE (l:Learning {
            learning_id: $learning_id,
            topic: $topic,
            content: $content,
            source: $source,
            confidence: $confidence,
            created_at: datetime()
        })
        CREATE (u)-[:HAS_LEARNING]->(l)
        RETURN l.learning_id as id
        """

        params = {
            "user_id": user_id,
            "learning_id": learning_id,
            "topic": topic,
            "content": content,
            "source": source,
            "confidence": confidence,
        }

        try:
            result = self._run_query(query, params)

            # Connect to related entities
            if related_entities:
                for entity in related_entities:
                    self._link_learning_to_entity(learning_id, entity)

            return learning_id if result else None
        except Exception as e:
            logger.error(f"Failed to store learning: {e}")
            return None

    def _link_learning_to_entity(self, learning_id: str, entity_name: str):
        """Link a learning to an entity (creates entity if doesn't exist)."""
        query = """
        MATCH (l:Learning {learning_id: $learning_id})
        MERGE (e:Entity {name: $entity_name})
        MERGE (l)-[:ABOUT]->(e)
        """
        self._run_query(query, {"learning_id": learning_id, "entity_name": entity_name})

    def get_learnings(
        self,
        user_id: str,
        topic: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Retrieve learnings for a user."""
        query = """
        MATCH (u:User {user_id: $user_id})-[:HAS_LEARNING]->(l:Learning)
        """
        if topic:
            query += "WHERE l.topic = $topic "

        query += """
        RETURN l.learning_id as learning_id,
               l.topic as topic,
               l.content as content,
               l.confidence as confidence,
               l.created_at as created_at
        ORDER BY l.created_at DESC
        LIMIT $limit
        """

        return self._run_query(query, {
            "user_id": user_id,
            "topic": topic,
            "limit": limit,
        })

    # ============================================
    # PROJECT RELATIONSHIPS
    # ============================================

    def add_project(
        self,
        user_id: str,
        project_id: str,
        name: str,
        organization: str = "",
        role: str = "",
    ) -> bool:
        """Add a project node and connect to user."""
        query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (p:Project {project_id: $project_id})
        SET p.name = $name,
            p.organization = $organization,
            p.updated_at = datetime()
        MERGE (u)-[r:WORKS_ON]->(p)
        SET r.role = $role
        """

        try:
            self._run_query(query, {
                "user_id": user_id,
                "project_id": project_id,
                "name": name,
                "organization": organization,
                "role": role,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to add project: {e}")
            return False

    def get_project_context(self, user_id: str, project_id: str) -> Dict:
        """Get full context for a project including related people, tasks, and learnings."""
        query = """
        MATCH (u:User {user_id: $user_id})-[:WORKS_ON]->(p:Project {project_id: $project_id})
        OPTIONAL MATCH (p)-[:HAS_MEMBER]->(person:Person)
        OPTIONAL MATCH (l:Learning)-[:ABOUT]->(p)
        RETURN p.name as name,
               p.organization as organization,
               collect(DISTINCT person.name) as team_members,
               collect(DISTINCT l.content) as related_learnings
        """

        results = self._run_query(query, {
            "user_id": user_id,
            "project_id": project_id,
        })

        return results[0] if results else {}

    # ============================================
    # PERSON/CONTACT MANAGEMENT
    # ============================================

    def add_person(
        self,
        user_id: str,
        name: str,
        relationship: str = "contact",
        organization: str = "",
        notes: str = "",
    ) -> bool:
        """Add a person node and connect to user."""
        query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (p:Person {name: $name, user_id: $user_id})
        SET p.organization = $organization,
            p.notes = $notes,
            p.updated_at = datetime()
        MERGE (u)-[r:KNOWS]->(p)
        SET r.relationship = $relationship
        """

        try:
            self._run_query(query, {
                "user_id": user_id,
                "name": name,
                "relationship": relationship,
                "organization": organization,
                "notes": notes,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to add person: {e}")
            return False

    def link_person_to_project(
        self,
        user_id: str,
        person_name: str,
        project_id: str,
        role: str = "member",
    ) -> bool:
        """Link a person to a project."""
        query = """
        MATCH (p:Person {name: $person_name, user_id: $user_id})
        MATCH (proj:Project {project_id: $project_id})
        MERGE (proj)-[r:HAS_MEMBER]->(p)
        SET r.role = $role
        """

        try:
            self._run_query(query, {
                "user_id": user_id,
                "person_name": person_name,
                "project_id": project_id,
                "role": role,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to link person to project: {e}")
            return False

    # ============================================
    # CONTEXTUAL RETRIEVAL
    # ============================================

    def get_relevant_context(
        self,
        user_id: str,
        query_text: str,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Get relevant context from the knowledge graph based on query text.

        This searches for:
        - Matching learnings
        - Related projects
        - Related people
        - Relevant concepts

        In a production system, this would use vector similarity search.
        For now, we use simple text matching.
        """
        # Extract potential keywords from query
        keywords = query_text.lower().split()

        context = {
            "learnings": [],
            "projects": [],
            "people": [],
        }

        # Search learnings
        for keyword in keywords[:5]:  # Limit to first 5 keywords
            query = """
            MATCH (u:User {user_id: $user_id})-[:HAS_LEARNING]->(l:Learning)
            WHERE toLower(l.content) CONTAINS $keyword
            RETURN l.content as content, l.topic as topic
            LIMIT $limit
            """
            results = self._run_query(query, {
                "user_id": user_id,
                "keyword": keyword,
                "limit": limit,
            })
            context["learnings"].extend(results)

        # Search projects
        for keyword in keywords[:3]:
            query = """
            MATCH (u:User {user_id: $user_id})-[:WORKS_ON]->(p:Project)
            WHERE toLower(p.name) CONTAINS $keyword
               OR toLower(p.organization) CONTAINS $keyword
            RETURN p.name as name, p.organization as organization
            LIMIT $limit
            """
            results = self._run_query(query, {
                "user_id": user_id,
                "keyword": keyword,
                "limit": limit,
            })
            context["projects"].extend(results)

        # Search people
        for keyword in keywords[:3]:
            query = """
            MATCH (u:User {user_id: $user_id})-[:KNOWS]->(p:Person)
            WHERE toLower(p.name) CONTAINS $keyword
            RETURN p.name as name, p.organization as organization
            LIMIT $limit
            """
            results = self._run_query(query, {
                "user_id": user_id,
                "keyword": keyword,
                "limit": limit,
            })
            context["people"].extend(results)

        # Deduplicate
        context["learnings"] = list({d["content"]: d for d in context["learnings"]}.values())
        context["projects"] = list({d["name"]: d for d in context["projects"]}.values())
        context["people"] = list({d["name"]: d for d in context["people"]}.values())

        return context

    # ============================================
    # USER PREFERENCES LEARNING
    # ============================================

    def learn_preference(
        self,
        user_id: str,
        preference_key: str,
        preference_value: str,
        source: str = "inferred",
    ) -> bool:
        """Store a learned user preference."""
        return self.store_learning(
            user_id=user_id,
            topic="preference",
            content=f"{preference_key}: {preference_value}",
            source=source,
            confidence=0.7,
        ) is not None

    def learn_fact(
        self,
        user_id: str,
        fact: str,
        related_entities: List[str] = None,
    ) -> bool:
        """Store a learned fact about the user or their world."""
        return self.store_learning(
            user_id=user_id,
            topic="fact",
            content=fact,
            source="conversation",
            confidence=0.85,
            related_entities=related_entities,
        ) is not None

    def learn_pattern(
        self,
        user_id: str,
        pattern: str,
        confidence: float = 0.6,
    ) -> bool:
        """Store a learned behavioral pattern."""
        return self.store_learning(
            user_id=user_id,
            topic="pattern",
            content=pattern,
            source="observation",
            confidence=confidence,
        ) is not None

    # ============================================
    # ANALYTICS
    # ============================================

    def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of user's knowledge graph."""
        query = """
        MATCH (u:User {user_id: $user_id})
        OPTIONAL MATCH (u)-[:HAS_LEARNING]->(l:Learning)
        OPTIONAL MATCH (u)-[:WORKS_ON]->(p:Project)
        OPTIONAL MATCH (u)-[:KNOWS]->(person:Person)
        RETURN u.email as email,
               count(DISTINCT l) as total_learnings,
               count(DISTINCT p) as total_projects,
               count(DISTINCT person) as total_contacts
        """

        results = self._run_query(query, {"user_id": user_id})
        return results[0] if results else {}

    def get_recent_insights(self, user_id: str, days: int = 7) -> List[Dict]:
        """Get recent learnings and insights."""
        query = """
        MATCH (u:User {user_id: $user_id})-[:HAS_LEARNING]->(l:Learning)
        WHERE l.created_at > datetime() - duration({days: $days})
        RETURN l.topic as topic,
               l.content as content,
               l.confidence as confidence,
               l.created_at as created_at
        ORDER BY l.created_at DESC
        LIMIT 20
        """

        return self._run_query(query, {"user_id": user_id, "days": days})
