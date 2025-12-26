# Alfred - Vector Store & Knowledge Graph Integration

> Semantic search and relationship-based knowledge management for intelligent context

## Table of Contents

1. [Overview](#overview)
2. [Vector Store (Qdrant)](#vector-store-qdrant)
3. [Knowledge Graph (Neo4j)](#knowledge-graph-neo4j)
4. [Integration Architecture](#integration-architecture)
5. [Data Flow](#data-flow)
6. [API Reference](#api-reference)
7. [Setup & Configuration](#setup--configuration)
8. [Debugging & Maintenance](#debugging--maintenance)

---

## Overview

Alfred uses two complementary knowledge systems:

| System | Purpose | Technology | Data Type |
|--------|---------|------------|-----------|
| **Vector Store** | Semantic similarity search | Qdrant | Embeddings (dense vectors) |
| **Knowledge Graph** | Relationship traversal | Neo4j | Nodes & relationships |

### Why Both?

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        COMPLEMENTARY KNOWLEDGE SYSTEMS                           │
└─────────────────────────────────────────────────────────────────────────────────┘

VECTOR STORE (Qdrant)                    KNOWLEDGE GRAPH (Neo4j)
━━━━━━━━━━━━━━━━━━━━━━                   ━━━━━━━━━━━━━━━━━━━━━━━
• "Find similar concepts"                 • "Show relationships"
• Semantic search                         • Graph traversal
• Document retrieval                      • Entity connections
• Fuzzy matching                          • Structured queries

Example: "What did I learn about APIs?"   Example: "Who works on Project X?"
→ Returns semantically similar docs       → Returns people connected to project

         ┌─────────────────┐
         │   User Query    │
         └────────┬────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
   ┌───────────┐    ┌───────────┐
   │  Qdrant   │    │   Neo4j   │
   │  Vector   │    │   Graph   │
   │  Search   │    │ Traversal │
   └─────┬─────┘    └─────┬─────┘
         │                 │
         └────────┬────────┘
                  ▼
         ┌─────────────────┐
         │ Merged Context  │
         │   for LLM       │
         └─────────────────┘
```

---

## Vector Store (Qdrant)

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           QDRANT VECTOR STORE                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────────────┐
                    │           Qdrant Server              │
                    │         localhost:6333               │
                    │                                      │
                    │  ┌────────────────────────────────┐  │
                    │  │     alfred_knowledge           │  │
                    │  │        Collection              │  │
                    │  │                                │  │
                    │  │  ┌──────────────────────────┐  │  │
                    │  │  │       Vectors            │  │  │
                    │  │  │  • Dimension: 1536       │  │  │
                    │  │  │  • Distance: Cosine      │  │  │
                    │  │  │  • Index: HNSW           │  │  │
                    │  │  └──────────────────────────┘  │  │
                    │  │                                │  │
                    │  │  ┌──────────────────────────┐  │  │
                    │  │  │       Payloads           │  │  │
                    │  │  │  • user_id (keyword)     │  │  │
                    │  │  │  • content (text)        │  │  │
                    │  │  │  • source (keyword)      │  │  │
                    │  │  │  • created_at (datetime) │  │  │
                    │  │  │  • metadata (json)       │  │  │
                    │  │  └──────────────────────────┘  │  │
                    │  │                                │  │
                    │  └────────────────────────────────┘  │
                    │                                      │
                    └──────────────────────────────────────┘
```

### Collection Schema

```python
# Collection configuration
{
    "name": "alfred_knowledge",
    "vectors": {
        "size": 1536,              # OpenAI text-embedding-3-small dimension
        "distance": "Cosine"       # Similarity metric
    },
    "hnsw_config": {
        "m": 16,                   # Number of edges per node
        "ef_construct": 100,       # Index time accuracy
        "full_scan_threshold": 10000
    },
    "payload_schema": {
        "user_id": {
            "type": "keyword",
            "index": True
        },
        "content": {
            "type": "text",
            "index": False
        },
        "source": {
            "type": "keyword",
            "index": True,
            "values": ["conversation", "document", "learning", "preference"]
        },
        "topic": {
            "type": "keyword",
            "index": True
        },
        "created_at": {
            "type": "datetime",
            "index": True
        },
        "metadata": {
            "type": "json"
        }
    }
}
```

### Data Types Stored

| Source Type | Description | Example |
|-------------|-------------|---------|
| `conversation` | Chat exchanges | "User asked about project deadlines" |
| `document` | Uploaded files | PDF content, notes |
| `learning` | Extracted knowledge | "Prefers morning meetings" |
| `preference` | User preferences | "Communication style: concise" |

### Embedding Process

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           EMBEDDING PIPELINE                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

  Input Text                    OpenAI Embedder                    Qdrant Storage
  ──────────                    ───────────────                    ──────────────
       │                              │                                  │
       │  "I prefer meetings         │                                  │
       │   in the morning            │                                  │
       │   before 10 AM"             │                                  │
       │                              │                                  │
       └──────────────────────────────►                                  │
                                      │                                  │
                               ┌──────┴──────┐                          │
                               │   OpenAI    │                          │
                               │  Embedding  │                          │
                               │    API      │                          │
                               │             │                          │
                               │ text-embed- │                          │
                               │  ing-3-small│                          │
                               └──────┬──────┘                          │
                                      │                                  │
                                      │ [0.023, -0.156, 0.089, ...]     │
                                      │ (1536 dimensions)                │
                                      │                                  │
                                      └──────────────────────────────────►
                                                                         │
                                                              ┌──────────▼──────────┐
                                                              │   Store Vector      │
                                                              │   + Payload         │
                                                              │                     │
                                                              │   {                 │
                                                              │     vector: [...],  │
                                                              │     user_id: "xxx", │
                                                              │     content: "...", │
                                                              │     source: "pref"  │
                                                              │   }                 │
                                                              └─────────────────────┘
```

### Search Process

```python
# Semantic search example
async def search_knowledge(user_id: str, query: str, limit: int = 5):
    # 1. Generate embedding for query
    query_embedding = await embedder.embed(query)

    # 2. Search Qdrant with user filter
    results = client.search(
        collection_name="alfred_knowledge",
        query_vector=query_embedding,
        query_filter=Filter(
            must=[
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            ]
        ),
        limit=limit,
        with_payload=True,
        score_threshold=0.7  # Only return relevant results
    )

    # 3. Return ranked results
    return [
        {
            "content": hit.payload["content"],
            "source": hit.payload["source"],
            "score": hit.score,
            "metadata": hit.payload.get("metadata", {})
        }
        for hit in results
    ]
```

### Implementation

**File:** `app/agents/alfred_agent.py`

```python
from agno.knowledge.qdrant import QdrantKnowledgeBase
from agno.embedder.openai import OpenAIEmbedder

class AlfredAgent:
    def __init__(self):
        # Initialize Qdrant knowledge base
        self.knowledge_base = QdrantKnowledgeBase(
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            collection_name="alfred_knowledge",
            embedder=OpenAIEmbedder(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="text-embedding-3-small"  # 1536 dimensions
            )
        )

    async def add_knowledge(self, user_id: str, content: str, source: str):
        """Add new knowledge to vector store"""
        await self.knowledge_base.add_documents([
            {
                "content": content,
                "metadata": {
                    "user_id": user_id,
                    "source": source,
                    "created_at": datetime.utcnow().isoformat()
                }
            }
        ])

    async def query_knowledge(self, user_id: str, query: str):
        """Query relevant knowledge for user"""
        return await self.knowledge_base.search(
            query=query,
            filter={"user_id": user_id},
            limit=5
        )
```

---

## Knowledge Graph (Neo4j)

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NEO4J KNOWLEDGE GRAPH                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

                              ┌───────────┐
                              │   User    │
                              │  (Node)   │
                              └─────┬─────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        │ WORKS_ON                  │ KNOWS                     │ INTERESTED_IN
        ▼                           ▼                           ▼
  ┌───────────┐              ┌───────────┐              ┌───────────┐
  │  Project  │              │  Person   │              │  Concept  │
  │  (Node)   │              │  (Node)   │              │  (Node)   │
  └─────┬─────┘              └─────┬─────┘              └─────┬─────┘
        │                           │                           │
        │ HAS_TASK                  │ COLLABORATES_WITH         │ RELATES_TO
        ▼                           ▼                           ▼
  ┌───────────┐              ┌───────────┐              ┌───────────┐
  │   Task    │              │  Person   │              │ Learning  │
  │  (Node)   │              │  (Node)   │              │  (Node)   │
  └───────────┘              └───────────┘              └───────────┘


Node Types:
━━━━━━━━━━━━
• User       : Central user entity
• Project    : Work projects
• Person     : Contacts, collaborators
• Concept    : Areas of interest/expertise
• Task       : Individual tasks
• Learning   : Stored knowledge items

Relationship Types:
━━━━━━━━━━━━━━━━━━━
• WORKS_ON           : User → Project
• KNOWS              : User → Person
• INTERESTED_IN      : User → Concept
• HAS_MEMBER         : Project → Person
• HAS_TASK           : Project → Task
• ASSIGNED_TO        : Task → Person
• COLLABORATES_WITH  : Person → Person
• RELATES_TO         : Learning → Concept
```

### Node Schemas

```cypher
// User node
(:User {
    user_id: "uuid",
    email: "user@example.com",
    name: "John Doe",
    created_at: datetime()
})

// Project node
(:Project {
    project_id: "uuid",
    name: "Alfred AI Assistant",
    status: "active",
    organization: "Personal",
    created_at: datetime()
})

// Person node
(:Person {
    name: "Jane Smith",
    organization: "Tech Corp",
    relationship_type: "colleague",  // colleague, friend, mentor, etc.
    email: "jane@techcorp.com",
    last_interaction: date()
})

// Concept node
(:Concept {
    name: "Machine Learning",
    category: "technology",  // technology, business, personal, etc.
    confidence: 0.9
})

// Task node
(:Task {
    task_id: "uuid",
    title: "Implement vector search",
    status: "pending",
    priority: "high",
    due_date: date()
})

// Learning node
(:Learning {
    learning_id: "uuid",
    content: "User prefers concise communication",
    topic: "communication",
    source: "conversation",
    created_at: datetime()
})
```

### Relationship Schemas

```cypher
// User works on project with role
(u:User)-[:WORKS_ON {
    role: "owner",          // owner, member, observer
    since: date("2025-01-01"),
    contribution: "primary developer"
}]->(p:Project)

// User knows person
(u:User)-[:KNOWS {
    relationship_type: "colleague",
    strength: 0.8,          // 0.0 to 1.0
    context: "met at conference",
    since: date()
}]->(person:Person)

// User interested in concept
(u:User)-[:INTERESTED_IN {
    confidence: 0.9,
    since: date(),
    source: "learned from conversations"
}]->(c:Concept)

// Project has member
(p:Project)-[:HAS_MEMBER {
    role: "contributor",
    joined: date()
}]->(person:Person)

// Task belongs to project
(t:Task)-[:BELONGS_TO]->(p:Project)

// Task assigned to person
(t:Task)-[:ASSIGNED_TO {
    assigned_at: datetime()
}]->(person:Person)

// Person collaborates with person
(p1:Person)-[:COLLABORATES_WITH {
    project: "Alfred",
    frequency: "weekly"
}]->(p2:Person)

// Learning relates to concept
(l:Learning)-[:RELATES_TO {
    relevance: 0.85
}]->(c:Concept)
```

### Example Graph

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SAMPLE KNOWLEDGE GRAPH                                 │
└─────────────────────────────────────────────────────────────────────────────────┘


                              ┌───────────────────┐
                              │      User         │
                              │   "John Doe"      │
                              └─────────┬─────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           │                            │                            │
           │ WORKS_ON                   │ KNOWS                      │ INTERESTED_IN
           ▼                            ▼                            ▼
   ┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
   │     Project       │      │      Person       │      │     Concept       │
   │ "Alfred AI"       │      │   "Jane Smith"    │      │ "Machine Learning"│
   │ status: active    │      │   org: Tech Corp  │      │ category: tech    │
   └────────┬──────────┘      └─────────┬─────────┘      └─────────┬─────────┘
            │                           │                          │
   ┌────────┴────────┐                  │                          │
   │                 │                  │                          │
   │ HAS_TASK        │ HAS_MEMBER       │ COLLABORATES             │ RELATES_TO
   ▼                 ▼                  │ _WITH                    ▼
┌──────────┐  ┌──────────────┐         ▼              ┌───────────────────────┐
│   Task   │  │    Person    │   ┌──────────┐         │       Learning        │
│"Implement│  │"Bob Johnson" │   │  Person  │         │ "LLMs require careful │
│ search"  │  │role: contrib │   │"Alice Lee"│         │  prompt engineering"  │
└──────────┘  └──────────────┘   └──────────┘         └───────────────────────┘
```

### Implementation

**File:** `alfred/infrastructure/knowledge/neo4j_graph.py`

```python
from neo4j import GraphDatabase
from typing import List, Optional

class Neo4jKnowledgeGraph:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            self.available = True
        except Exception:
            self.available = False
            print("Neo4j unavailable, starting without knowledge graph")

    async def add_fact(self, user_id: str, fact: dict):
        """Add a fact/learning to the graph"""
        if not self.available:
            return

        with self.driver.session() as session:
            session.run("""
                MERGE (u:User {user_id: $user_id})
                CREATE (l:Learning {
                    learning_id: randomUUID(),
                    content: $content,
                    topic: $topic,
                    created_at: datetime()
                })
                MERGE (c:Concept {name: $topic})
                CREATE (u)-[:LEARNED]->(l)
                CREATE (l)-[:RELATES_TO]->(c)
            """, user_id=user_id, content=fact["content"], topic=fact["topic"])

    async def add_project_relationship(self, user_id: str, project: dict):
        """Connect user to project"""
        with self.driver.session() as session:
            session.run("""
                MERGE (u:User {user_id: $user_id})
                MERGE (p:Project {
                    project_id: $project_id,
                    name: $name
                })
                ON CREATE SET p.created_at = datetime()
                MERGE (u)-[:WORKS_ON {role: $role, since: date()}]->(p)
            """, **project, user_id=user_id)

    async def add_person(self, user_id: str, person: dict):
        """Add a person to user's network"""
        with self.driver.session() as session:
            session.run("""
                MERGE (u:User {user_id: $user_id})
                MERGE (p:Person {name: $name})
                ON CREATE SET
                    p.organization = $organization,
                    p.email = $email
                MERGE (u)-[:KNOWS {
                    relationship_type: $relationship_type,
                    strength: $strength
                }]->(p)
            """, user_id=user_id, **person)

    async def get_user_context(self, user_id: str) -> dict:
        """Get comprehensive context for user"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {user_id: $user_id})
                OPTIONAL MATCH (u)-[:WORKS_ON]->(p:Project)
                OPTIONAL MATCH (u)-[:KNOWS]->(person:Person)
                OPTIONAL MATCH (u)-[:INTERESTED_IN]->(c:Concept)
                OPTIONAL MATCH (u)-[:LEARNED]->(l:Learning)
                RETURN
                    collect(DISTINCT {name: p.name, status: p.status}) as projects,
                    collect(DISTINCT {name: person.name, org: person.organization}) as people,
                    collect(DISTINCT c.name) as interests,
                    collect(DISTINCT {content: l.content, topic: l.topic})[..10] as recent_learnings
            """, user_id=user_id)

            record = result.single()
            return {
                "projects": record["projects"],
                "people": record["people"],
                "interests": record["interests"],
                "recent_learnings": record["recent_learnings"]
            }

    async def get_related_entities(self, user_id: str, entity: str, depth: int = 2) -> list:
        """Get entities related to a given entity"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {user_id: $user_id})
                MATCH (start)-[*1..$depth]-(related)
                WHERE start.name = $entity OR start.title = $entity
                RETURN DISTINCT labels(related) as type, related
                LIMIT 20
            """, user_id=user_id, entity=entity, depth=depth)

            return [dict(record["related"]) for record in result]
```

### Cypher Query Examples

```cypher
-- Find all projects and their team members for a user
MATCH (u:User {user_id: $user_id})-[:WORKS_ON]->(p:Project)
OPTIONAL MATCH (p)-[:HAS_MEMBER]->(person:Person)
RETURN p.name as project, collect(person.name) as members
ORDER BY p.name

-- Get user's interest network
MATCH (u:User {user_id: $user_id})-[:INTERESTED_IN]->(c:Concept)
OPTIONAL MATCH (l:Learning)-[:RELATES_TO]->(c)
RETURN c.name as concept, count(l) as learning_count
ORDER BY learning_count DESC

-- Find collaboration opportunities
MATCH (u:User {user_id: $user_id})-[:KNOWS]->(p1:Person)
MATCH (p1)-[:COLLABORATES_WITH]->(p2:Person)
WHERE NOT (u)-[:KNOWS]->(p2)
RETURN p2.name as potential_contact, p1.name as through, p2.organization
LIMIT 10

-- Get project health indicators
MATCH (u:User {user_id: $user_id})-[:WORKS_ON]->(p:Project)
OPTIONAL MATCH (p)-[:HAS_TASK]->(t:Task)
WITH p, count(t) as total_tasks,
     sum(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
RETURN p.name, total_tasks, completed_tasks,
       CASE WHEN total_tasks > 0
            THEN round(100.0 * completed_tasks / total_tasks)
            ELSE 0 END as progress_percent

-- Find knowledge gaps
MATCH (u:User {user_id: $user_id})-[:INTERESTED_IN]->(c:Concept)
WHERE NOT EXISTS {
    MATCH (u)-[:LEARNED]->(l:Learning)-[:RELATES_TO]->(c)
}
RETURN c.name as concept_without_learnings
```

---

## Integration Architecture

### Combined Query Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         COMBINED KNOWLEDGE RETRIEVAL                             │
└─────────────────────────────────────────────────────────────────────────────────┘

  User Query: "What should I focus on for the AI project?"
  ──────────────────────────────────────────────────────

         ┌─────────────────┐
         │   User Query    │
         └────────┬────────┘
                  │
         ┌────────┴────────┐
         │   Query Router   │
         └────────┬────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Qdrant  │  │ Neo4j   │  │Postgres │
│ Search  │  │ Graph   │  │  Query  │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     │ Similar    │ Related    │ Current
     │ Learnings  │ Entities   │ Tasks
     │            │            │
     └────────────┼────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Context Merger  │
         │                 │
         │ • Deduplicate   │
         │ • Rank by       │
         │   relevance     │
         │ • Format for    │
         │   LLM           │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  LLM Response   │
         │  Generation     │
         └─────────────────┘
```

### Context Building Example

```python
async def build_rich_context(user_id: str, query: str) -> dict:
    """Build comprehensive context from all knowledge sources"""

    # 1. Vector search for semantically similar content
    vector_results = await qdrant_search(user_id, query, limit=5)

    # 2. Graph traversal for related entities
    graph_context = await neo4j.get_user_context(user_id)

    # 3. Extract relevant entity from query (e.g., "AI project")
    entity = extract_entity(query)
    if entity:
        related = await neo4j.get_related_entities(user_id, entity)
        graph_context["related_entities"] = related

    # 4. Current state from PostgreSQL
    current_tasks = await postgres.get_pending_tasks(user_id)
    active_projects = await postgres.get_active_projects(user_id)

    # 5. Merge and format context
    return {
        "semantic_knowledge": [r["content"] for r in vector_results],
        "graph_context": {
            "projects": graph_context["projects"],
            "people": graph_context["people"],
            "interests": graph_context["interests"],
            "learnings": graph_context["recent_learnings"]
        },
        "current_state": {
            "pending_tasks": current_tasks,
            "active_projects": active_projects
        },
        "related_entities": graph_context.get("related_entities", [])
    }
```

### Knowledge Extraction Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         KNOWLEDGE EXTRACTION PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────────────┘

  Conversation Input
  ──────────────────
         │
         ▼
  ┌─────────────────┐
  │  LLM Analysis   │
  │                 │
  │  Extract:       │
  │  • Preferences  │
  │  • People       │
  │  • Projects     │
  │  • Concepts     │
  │  • Learnings    │
  └────────┬────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌─────────┐
│ Qdrant  │  │ Neo4j   │
│         │  │         │
│ Store:  │  │ Store:  │
│ • Embed │  │ • Nodes │
│   text  │  │ • Rels  │
└─────────┘  └─────────┘


Example Extraction:
───────────────────
User: "I had a great meeting with Sarah from DevOps about the
       infrastructure migration. She mentioned we should use
       Kubernetes for container orchestration."

Extracted:
• Person: Sarah (org: DevOps, relationship: colleague)
• Project context: infrastructure migration
• Learning: "Use Kubernetes for container orchestration"
• Concept: Kubernetes, container orchestration
```

---

## Data Flow

### Write Path

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              KNOWLEDGE WRITE PATH                                │
└─────────────────────────────────────────────────────────────────────────────────┘

  User Conversation
  ─────────────────
         │
         ▼
  ┌─────────────────┐
  │   Chat API      │
  │   /chat         │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │   Alfred Core   │
  │   (Butler)      │
  └────────┬────────┘
           │
           │ 1. Store chat history
           ├─────────────────────────────────► PostgreSQL (chat_history)
           │
           │ 2. Extract knowledge
           │
           ▼
  ┌─────────────────┐
  │   LLM Extract   │
  │   Preferences   │
  │   & Entities    │
  └────────┬────────┘
           │
           │ 3a. Embed and store
           ├─────────────────────────────────► Qdrant (alfred_knowledge)
           │
           │ 3b. Create graph nodes/edges
           └─────────────────────────────────► Neo4j (Knowledge Graph)
```

### Read Path

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              KNOWLEDGE READ PATH                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

  User Query
  ──────────
         │
         ▼
  ┌─────────────────┐
  │   Alfred Core   │
  │   (Butler)      │
  └────────┬────────┘
           │
           │ Parallel queries
           │
    ┌──────┼──────┬──────────────┐
    │      │      │              │
    ▼      ▼      ▼              ▼
┌──────┐ ┌──────┐ ┌──────┐  ┌──────────┐
│Qdrant│ │Neo4j │ │Postgr│  │Preferences│
│Search│ │Graph │ │Tasks │  │  DB      │
└──┬───┘ └──┬───┘ └──┬───┘  └────┬─────┘
   │        │        │           │
   │        │        │           │
   └────────┴────────┴───────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Context Merger  │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ LLM Generation  │
         │ with Context    │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ User Response   │
         └─────────────────┘
```

---

## API Reference

### Vector Store API

```python
class VectorDBProvider(ABC):
    """Abstract interface for vector database operations"""

    @abstractmethod
    async def add_documents(self, user_id: str, documents: List[dict]) -> None:
        """Add documents to vector store"""
        pass

    @abstractmethod
    async def search(self, user_id: str, query: str, limit: int = 5) -> List[dict]:
        """Search for similar documents"""
        pass

    @abstractmethod
    async def delete(self, user_id: str, document_ids: List[str]) -> None:
        """Delete documents from store"""
        pass
```

### Knowledge Graph API

```python
class KnowledgeGraphProvider(ABC):
    """Abstract interface for knowledge graph operations"""

    @abstractmethod
    async def add_fact(self, user_id: str, fact: KnowledgeFact) -> None:
        """Add a fact/learning to the graph"""
        pass

    @abstractmethod
    async def query_facts(self, user_id: str, query: str) -> List[KnowledgeFact]:
        """Query facts related to a topic"""
        pass

    @abstractmethod
    async def add_relationship(
        self, user_id: str,
        from_entity: str,
        relationship: str,
        to_entity: str,
        properties: dict = None
    ) -> None:
        """Add a relationship between entities"""
        pass

    @abstractmethod
    async def get_related_entities(
        self, user_id: str,
        entity: str,
        depth: int = 2
    ) -> List[dict]:
        """Get entities related to a given entity"""
        pass

    @abstractmethod
    async def get_user_context(self, user_id: str) -> dict:
        """Get comprehensive context for a user"""
        pass
```

---

## Setup & Configuration

### Qdrant Setup

```bash
# Option 1: Docker
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant

# Option 2: Docker Compose
cat > docker-compose.yml << EOF
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
volumes:
  qdrant_storage:
EOF

docker-compose up -d

# Verify
curl http://localhost:6333/health
```

### Neo4j Setup

```bash
# Option 1: Docker
docker run -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    -v neo4j_data:/data \
    neo4j:5

# Option 2: Docker Compose
cat >> docker-compose.yml << EOF
  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/password
    volumes:
      - neo4j_data:/data
volumes:
  neo4j_data:
EOF

docker-compose up -d

# Verify (browser)
open http://localhost:7474
```

### Environment Variables

```bash
# .env file

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=alfred_knowledge

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Collection Initialization

```python
# Initialize Qdrant collection
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(url="http://localhost:6333")

client.create_collection(
    collection_name="alfred_knowledge",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE
    )
)
```

```cypher
// Initialize Neo4j constraints
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.user_id IS UNIQUE;

CREATE CONSTRAINT project_id_unique IF NOT EXISTS
FOR (p:Project) REQUIRE p.project_id IS UNIQUE;

// Create indexes
CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email);
CREATE INDEX project_name IF NOT EXISTS FOR (p:Project) ON (p.name);
CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name);
```

---

## Debugging & Maintenance

### Qdrant Debugging

```bash
# Check collection info
curl http://localhost:6333/collections/alfred_knowledge

# Count points
curl http://localhost:6333/collections/alfred_knowledge/points/count

# Scroll through points
curl -X POST http://localhost:6333/collections/alfred_knowledge/points/scroll \
    -H "Content-Type: application/json" \
    -d '{"limit": 10, "with_payload": true}'

# Search with filter
curl -X POST http://localhost:6333/collections/alfred_knowledge/points/search \
    -H "Content-Type: application/json" \
    -d '{
        "vector": [0.1, 0.2, ...],
        "filter": {"must": [{"key": "user_id", "match": {"value": "uuid"}}]},
        "limit": 5,
        "with_payload": true
    }'
```

### Neo4j Debugging

```cypher
// Count all nodes and relationships
MATCH (n) RETURN labels(n) as type, count(n) as count
UNION
MATCH ()-[r]->() RETURN type(r) as type, count(r) as count

// Find orphaned nodes
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n), n

// User's complete graph
MATCH (u:User {user_id: $user_id})-[r*1..3]-(connected)
RETURN u, r, connected

// Performance analysis
PROFILE MATCH (u:User {user_id: $user_id})-[:WORKS_ON]->(p:Project)
RETURN p.name
```

### Health Checks

```python
async def check_vector_store_health():
    """Check Qdrant health"""
    try:
        response = await httpx.get(f"{QDRANT_URL}/health")
        return response.status_code == 200
    except Exception:
        return False

async def check_knowledge_graph_health():
    """Check Neo4j health"""
    try:
        with driver.session() as session:
            session.run("RETURN 1")
        return True
    except Exception:
        return False
```

### Data Cleanup

```python
# Clean old vector data (older than 90 days)
from datetime import datetime, timedelta

cutoff = (datetime.utcnow() - timedelta(days=90)).isoformat()

client.delete(
    collection_name="alfred_knowledge",
    points_selector=Filter(
        must=[
            FieldCondition(
                key="created_at",
                range=Range(lt=cutoff)
            )
        ]
    )
)
```

```cypher
// Clean old learnings in Neo4j
MATCH (l:Learning)
WHERE l.created_at < datetime() - duration('P90D')
DETACH DELETE l

// Remove orphaned concepts
MATCH (c:Concept)
WHERE NOT (c)--()
DELETE c
```

### Backup & Restore

```bash
# Backup Qdrant (snapshot)
curl -X POST http://localhost:6333/collections/alfred_knowledge/snapshots

# Backup Neo4j
docker exec neo4j neo4j-admin database dump neo4j --to-path=/backups

# Restore Neo4j
docker exec neo4j neo4j-admin database load neo4j --from-path=/backups/neo4j.dump
```

---

*Vector Store & Knowledge Graph documentation for Alfred - The Digital Butler*
