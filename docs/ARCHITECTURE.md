# Alfred - Architecture Documentation

> **The Digital Butler** - An Agentic Personal Assistant with proactive intelligence

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Architecture](#component-architecture)
4. [Database Schema](#database-schema)
5. [Vector Store Integration](#vector-store-integration)
6. [Knowledge Graph Integration](#knowledge-graph-integration)
7. [API Reference](#api-reference)
8. [Data Flow](#data-flow)
9. [Authentication Flow](#authentication-flow)
10. [Mobile App Architecture](#mobile-app-architecture)
11. [MCP Integration](#mcp-integration)
12. [Configuration Reference](#configuration-reference)
13. [Debugging Guide](#debugging-guide)

---

## System Overview

Alfred is a sophisticated **Agentic Personal Assistant** designed as a proactive digital butler. It manages projects, tasks, habits, and learns user preferences over time.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Proactive Notifications** | Morning briefings, evening reviews, habit reminders |
| **Reflexive Memory** | Learns preferences from conversations |
| **Multi-LLM Support** | OpenAI (GPT-4o) or local Ollama (Llama3) |
| **Knowledge Graph** | Neo4j for relationships and context |
| **Vector Search** | Qdrant for semantic knowledge retrieval |
| **MCP Integration** | Filesystem, web search, database access |
| **Cross-Platform** | React Native mobile app |

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ALFRED SYSTEM ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   Mobile App    │
                              │  (React Native) │
                              │     + Expo      │
                              └────────┬────────┘
                                       │ HTTPS/REST
                                       │ JWT Auth
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI BACKEND                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │    Auth     │  │  Projects   │  │    Tasks    │  │   Habits    │            │
│  │   Routes    │  │   Routes    │  │   Routes    │  │   Routes    │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                │                    │
│         └────────────────┴────────────────┴────────────────┘                    │
│                                   │                                             │
│  ┌────────────────────────────────┴────────────────────────────────────┐       │
│  │                         CORE LAYER (Domain)                          │       │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │       │
│  │  │    Alfred    │  │  Proactive   │  │       Entities           │   │       │
│  │  │   (Butler)   │  │   Engine     │  │  (User, Project, Task,   │   │       │
│  │  │              │  │              │  │   Habit, Notification)   │   │       │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘   │       │
│  └─────────────────────────────────────────────────────────────────────┘       │
│                                   │                                             │
│  ┌────────────────────────────────┴────────────────────────────────────┐       │
│  │                    INFRASTRUCTURE LAYER (Adapters)                   │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │       │
│  │  │   LLM    │  │ Storage  │  │Knowledge │  │  Notifications   │    │       │
│  │  │ Adapters │  │ Adapter  │  │  Graph   │  │    (Expo)        │    │       │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘    │       │
│  └───────┼─────────────┼─────────────┼─────────────────┼──────────────┘       │
└──────────┼─────────────┼─────────────┼─────────────────┼──────────────────────┘
           │             │             │                 │
           ▼             ▼             ▼                 ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐     ┌──────────────┐
    │  OpenAI  │  │PostgreSQL│  │  Neo4j   │     │ Expo Push    │
    │  GPT-4o  │  │    DB    │  │  Graph   │     │  Service     │
    └──────────┘  └──────────┘  └──────────┘     └──────────────┘
         │
    ┌──────────┐
    │  Ollama  │
    │  Llama3  │
    └──────────┘


                    ┌─────────────────────────────────┐
                    │         MCP SERVERS             │
                    │  ┌───────────┐ ┌───────────┐   │
                    │  │Filesystem │ │Brave      │   │
                    │  │  Server   │ │Search     │   │
                    │  └───────────┘ └───────────┘   │
                    │  ┌───────────┐                 │
                    │  │ Postgres  │                 │
                    │  │ Memory    │                 │
                    │  └───────────┘                 │
                    └─────────────────────────────────┘


                    ┌─────────────────────────────────┐
                    │     AGNO AGENT (Alternative)    │
                    │  ┌───────────┐ ┌───────────┐   │
                    │  │  Qdrant   │ │ Postgres  │   │
                    │  │   KB      │ │ Storage   │   │
                    │  └───────────┘ └───────────┘   │
                    └─────────────────────────────────┘
```

---

## Component Architecture

### Directory Structure

```
Personal-Assistant/
├── alfred/                          # Backend (Python/FastAPI)
│   ├── api/                         # REST API endpoints
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── auth.py                  # Authentication routes
│   │   ├── projects.py              # Project management
│   │   ├── tasks.py                 # Task management
│   │   ├── habits.py                # Habit tracking
│   │   ├── dashboard.py             # Dashboard aggregations
│   │   └── notifications.py         # Push notifications
│   │
│   ├── core/                        # Domain logic
│   │   ├── entities.py              # Data classes & enums
│   │   ├── interfaces.py            # Abstract interfaces
│   │   ├── butler.py                # Alfred brain
│   │   └── proactive_engine.py      # Scheduled notifications
│   │
│   └── infrastructure/              # External integrations
│       ├── llm/
│       │   ├── openai_adapter.py    # OpenAI integration
│       │   └── ollama_adapter.py    # Local LLM integration
│       ├── storage/
│       │   └── postgres_db.py       # PostgreSQL adapter
│       ├── knowledge/
│       │   └── neo4j_graph.py       # Neo4j integration
│       └── notifications/
│           └── expo_push.py         # Expo push service
│
├── app/                             # Agno agent implementation
│   └── agents/
│       └── alfred_agent.py          # Alternative agent with Qdrant
│
├── mobile/                          # React Native app
│   ├── App.tsx                      # Navigation shell
│   └── src/
│       ├── api/
│       │   ├── client.ts            # Axios HTTP client
│       │   └── services.ts          # API service calls
│       ├── screens/                 # UI screens
│       └── services/
│           └── notifications.ts     # Push notification handling
│
├── docs/                            # Documentation
├── scripts/                         # Utility scripts
├── mcp_config.json                  # MCP server configuration
└── requirements.txt                 # Python dependencies
```

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                        API LAYER                                 │
│  HTTP endpoints, request/response handling, authentication      │
│  Files: alfred/api/*.py                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CORE LAYER                                 │
│  Business logic, entities, interfaces (contracts)               │
│  Files: alfred/core/*.py                                        │
│  - entities.py: Data classes (User, Project, Task, Habit, etc.) │
│  - interfaces.py: Abstract base classes                         │
│  - butler.py: Alfred's conversation logic                       │
│  - proactive_engine.py: Notification scheduling                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                           │
│  External service adapters (database, LLM, notifications)       │
│  Files: alfred/infrastructure/**/*.py                           │
│  - Implements interfaces from core layer                        │
│  - PostgreSQL, OpenAI, Ollama, Neo4j, Expo                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            DATABASE SCHEMA (PostgreSQL)                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│      users       │
├──────────────────┤
│ PK user_id (UUID)│◄───────────────────────────────────────┐
│    email (UNIQ)  │                                        │
│    password_hash │                                        │
│    profile (JSON)│                                        │
│    created_at    │                                        │
└──────────────────┘                                        │
         │                                                   │
         │ 1:N                                               │
         ▼                                                   │
┌──────────────────┐    ┌──────────────────┐               │
│   chat_history   │    │ user_preferences │               │
├──────────────────┤    ├──────────────────┤               │
│ PK id (SERIAL)   │    │ PK user_id + key │               │
│ FK user_id       │───►│    value         │               │
│    role          │    │    confidence    │               │
│    content       │    │    learned_at    │               │
│    metadata(JSON)│    └──────────────────┘               │
│    created_at    │                                        │
└──────────────────┘                                        │
                                                            │
┌──────────────────┐         ┌──────────────────┐          │
│     projects     │         │  project_updates │          │
├──────────────────┤         ├──────────────────┤          │
│ PK project_id    │◄────────│ FK project_id    │          │
│ FK user_id       │─────────│ FK user_id       │──────────┤
│    name          │         │ PK update_id     │          │
│    organization  │         │    content       │          │
│    role          │         │    update_type   │          │
│    status        │         │    action_items  │          │
│    description   │         │    blockers(JSON)│          │
│ integrations(JSON)         │    created_at    │          │
│    metadata(JSON)│         └──────────────────┘          │
│    created_at    │                                        │
│    updated_at    │                                        │
└──────────────────┘                                        │
         │                                                   │
         │ 1:N                                               │
         ▼                                                   │
┌──────────────────┐                                        │
│      tasks       │                                        │
├──────────────────┤                                        │
│ PK task_id (UUID)│                                        │
│ FK user_id       │────────────────────────────────────────┤
│ FK project_id    │ (nullable)                             │
│    title         │                                        │
│    description   │                                        │
│    priority      │ (low/medium/high/urgent)               │
│    status        │ (pending/in_progress/completed/blocked)│
│    due_date      │                                        │
│    recurrence    │                                        │
│    blockers      │                                        │
│    tags (JSON)   │                                        │
│    source        │                                        │
│    completed_at  │                                        │
│    created_at    │                                        │
│    updated_at    │                                        │
└──────────────────┘                                        │
                                                            │
┌──────────────────┐         ┌──────────────────┐          │
│      habits      │         │    habit_logs    │          │
├──────────────────┤         ├──────────────────┤          │
│ PK habit_id(UUID)│◄────────│ FK habit_id      │          │
│ FK user_id       │─────────│ FK user_id       │──────────┤
│    name          │         │ PK log_id        │          │
│    frequency     │         │ logged_date(UNIQ)│          │
│    time_preference         │    notes         │          │
│ days_of_week(JSON)         │ duration_minutes │          │
│    current_streak│         │    created_at    │          │
│    best_streak   │         └──────────────────┘          │
│    total_complete│                                        │
│    last_logged   │                                        │
│    motivation    │                                        │
│    category      │                                        │
│    active        │                                        │
│ reminder_enabled │                                        │
│    created_at    │                                        │
└──────────────────┘                                        │
                                                            │
┌────────────────────────┐                                  │
│ scheduled_notifications│                                  │
├────────────────────────┤                                  │
│ PK notification_id     │                                  │
│ FK user_id             │──────────────────────────────────┤
│    notification_type   │                                  │
│    title               │                                  │
│    content             │                                  │
│    trigger_time        │                                  │
│    context (JSON)      │                                  │
│    status              │                                  │
│    sent_at             │                                  │
│    created_at          │                                  │
└────────────────────────┘                                  │
                                                            │
┌──────────────────┐                                        │
│    learnings     │                                        │
├──────────────────┤                                        │
│ PK learning_id   │                                        │
│ FK user_id       │────────────────────────────────────────┘
│    topic         │
│    content       │
│    original_query│
│    created_at    │
└──────────────────┘
```

### Table Details

#### users
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    profile JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### chat_history
```sql
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    role TEXT NOT NULL,           -- 'user' | 'assistant'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',  -- timestamps, context, etc.
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_chat_user ON chat_history(user_id);
```

#### user_preferences
```sql
CREATE TABLE user_preferences (
    user_id UUID NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,  -- 0.0 to 1.0
    learned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, key)
);
```

#### projects
```sql
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    organization TEXT,
    role TEXT,                    -- 'owner' | 'member' | 'observer'
    status TEXT DEFAULT 'active', -- 'active' | 'on_hold' | 'completed' | 'archived'
    description TEXT,
    integrations JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
```

#### project_updates
```sql
CREATE TABLE project_updates (
    update_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    update_type TEXT,             -- 'progress' | 'blocker' | 'decision' | 'note'
    action_items TEXT,
    blockers JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_updates_project ON project_updates(project_id);
```

#### tasks
```sql
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    project_id UUID,              -- nullable (standalone tasks)
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium', -- 'low' | 'medium' | 'high' | 'urgent'
    status TEXT DEFAULT 'pending',  -- 'pending' | 'in_progress' | 'completed' | 'blocked'
    due_date TIMESTAMP,
    recurrence TEXT,              -- 'daily' | 'weekly' | 'monthly' | NULL
    blockers TEXT,
    tags JSONB DEFAULT '[]',
    source TEXT,                  -- 'manual' | 'conversation' | 'import'
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due ON tasks(due_date);
```

#### habits
```sql
CREATE TABLE habits (
    habit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    frequency TEXT DEFAULT 'daily', -- 'daily' | 'weekly' | 'custom'
    time_preference TEXT,           -- 'morning' | 'afternoon' | 'evening' | 'anytime'
    days_of_week JSONB DEFAULT '[]', -- [1,2,3,4,5] for Mon-Fri
    current_streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    total_completions INTEGER DEFAULT 0,
    last_logged DATE,
    motivation TEXT,
    category TEXT,                  -- 'health' | 'productivity' | 'learning' | etc.
    active BOOLEAN DEFAULT true,
    reminder_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_habits_user ON habits(user_id);
```

#### habit_logs
```sql
CREATE TABLE habit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    habit_id UUID NOT NULL,
    user_id UUID NOT NULL,
    logged_date DATE NOT NULL,
    notes TEXT,
    duration_minutes INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(habit_id, logged_date)
);
CREATE INDEX idx_logs_habit ON habit_logs(habit_id);
```

#### scheduled_notifications
```sql
CREATE TABLE scheduled_notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    notification_type TEXT NOT NULL, -- 'morning_briefing' | 'evening_review' | 'habit_reminder' | 'task_due' | 'nudge'
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    trigger_time TIMESTAMP NOT NULL,
    context JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending',   -- 'pending' | 'sent' | 'read' | 'dismissed'
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_notif_user ON scheduled_notifications(user_id);
CREATE INDEX idx_notif_trigger ON scheduled_notifications(trigger_time);
CREATE INDEX idx_notif_status ON scheduled_notifications(status);
```

#### learnings
```sql
CREATE TABLE learnings (
    learning_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    topic TEXT NOT NULL,
    content TEXT NOT NULL,
    original_query TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_learnings_user ON learnings(user_id);
```

---

## Vector Store Integration

### Overview

Alfred uses **Qdrant** as the vector database for semantic search and knowledge retrieval.

```
┌─────────────────────────────────────────────────────────────────┐
│                    VECTOR STORE ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   User Query     │──────►│ OpenAI Embedder  │──────►│    Qdrant DB     │
│                  │       │  (text-embed-3)  │       │                  │
└──────────────────┘       └──────────────────┘       └──────────────────┘
                                                               │
                                                               ▼
                                                      ┌──────────────────┐
                                                      │  alfred_knowledge│
                                                      │   Collection     │
                                                      ├──────────────────┤
                                                      │  • Documents     │
                                                      │  • Learnings     │
                                                      │  • Preferences   │
                                                      │  • Context       │
                                                      └──────────────────┘
```

### Configuration

**File:** `app/agents/alfred_agent.py`

```python
from agno.knowledge.qdrant import QdrantKnowledgeBase
from agno.embedder.openai import OpenAIEmbedder

knowledge_base = QdrantKnowledgeBase(
    qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    collection_name="alfred_knowledge",
    embedder=OpenAIEmbedder(api_key=os.getenv("OPENAI_API_KEY"))
)
```

### Data Flow

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│  Conversation  │────►│   Extract      │────►│   Generate     │
│    Input       │     │   Knowledge    │     │   Embedding    │
└────────────────┘     └────────────────┘     └────────────────┘
                                                      │
                                                      ▼
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│   Augmented    │◄────│   Retrieve     │◄────│   Store in     │
│   Response     │     │   Similar      │     │   Qdrant       │
└────────────────┘     └────────────────┘     └────────────────┘
```

### Collection Schema

```json
{
  "collection_name": "alfred_knowledge",
  "vectors": {
    "size": 1536,        // OpenAI embedding dimension
    "distance": "Cosine"
  },
  "payload_schema": {
    "user_id": "keyword",
    "content": "text",
    "source": "keyword",  // 'conversation' | 'document' | 'learning'
    "created_at": "datetime",
    "metadata": "json"
  }
}
```

### Use Cases

| Use Case | Description |
|----------|-------------|
| **Semantic Search** | Find relevant past conversations/learnings |
| **Context Retrieval** | Augment LLM responses with user knowledge |
| **Preference Matching** | Match current context with learned preferences |
| **Document RAG** | Retrieve relevant documents for user queries |

---

## Knowledge Graph Integration

### Overview

Alfred uses **Neo4j** for storing relationships between entities and building a semantic knowledge graph.

```
┌─────────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE GRAPH ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────────┘

                         ┌─────────────┐
                         │    User     │
                         │   (Node)    │
                         └──────┬──────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
   │   Project   │      │   Person    │      │  Concept    │
   │   (Node)    │      │   (Node)    │      │   (Node)    │
   └──────┬──────┘      └──────┬──────┘      └─────────────┘
          │                    │
          ▼                    │
   ┌─────────────┐            │
   │    Task     │◄───────────┘
   │   (Node)    │   ASSIGNED_TO
   └─────────────┘


RELATIONSHIPS:
─────────────────────────────────────────
User ──[WORKS_ON]──► Project
User ──[KNOWS]──► Person
User ──[INTERESTED_IN]──► Concept
Project ──[HAS_MEMBER]──► Person
Task ──[BELONGS_TO]──► Project
Person ──[COLLABORATES_WITH]──► Person
Learning ──[RELATES_TO]──► Concept
```

### Node Types

| Node Type | Properties | Purpose |
|-----------|------------|---------|
| **User** | user_id, email, name | Central user entity |
| **Project** | project_id, name, status | Project tracking |
| **Person** | name, organization, relationship | Contact/collaborator |
| **Concept** | name, category | Areas of interest/expertise |
| **Task** | task_id, title, status | Task tracking |
| **Learning** | learning_id, content, topic | Stored knowledge |

### Relationship Types

| Relationship | From | To | Properties |
|--------------|------|-----|------------|
| **WORKS_ON** | User | Project | role, since |
| **KNOWS** | User | Person | relationship_type, strength |
| **INTERESTED_IN** | User | Concept | confidence, since |
| **HAS_MEMBER** | Project | Person | role |
| **BELONGS_TO** | Task | Project | - |
| **ASSIGNED_TO** | Task | Person | - |
| **COLLABORATES_WITH** | Person | Person | context |
| **RELATES_TO** | Learning | Concept | - |

### Implementation

**File:** `alfred/infrastructure/knowledge/neo4j_graph.py`

```python
class Neo4jKnowledgeGraph(KnowledgeGraphProvider):
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    async def add_fact(self, user_id: str, fact: KnowledgeFact):
        # Create nodes and relationships

    async def query_facts(self, user_id: str, query: str) -> List[KnowledgeFact]:
        # Semantic graph traversal

    async def add_relationship(self, user_id: str, from_entity: str,
                               relationship: str, to_entity: str):
        # Create relationship between entities

    async def get_related_entities(self, user_id: str, entity: str,
                                   depth: int = 2) -> List[dict]:
        # Graph traversal for related entities

    async def get_user_context(self, user_id: str) -> dict:
        # Aggregate user's knowledge graph for context
```

### Cypher Queries

```cypher
// Get user's project network
MATCH (u:User {user_id: $user_id})-[:WORKS_ON]->(p:Project)
OPTIONAL MATCH (p)-[:HAS_MEMBER]->(person:Person)
RETURN p, collect(person) as members

// Find related concepts
MATCH (u:User {user_id: $user_id})-[:INTERESTED_IN]->(c:Concept)
OPTIONAL MATCH (l:Learning)-[:RELATES_TO]->(c)
RETURN c.name, collect(l.content) as learnings

// Get collaboration network
MATCH (u:User {user_id: $user_id})-[:KNOWS]->(p:Person)
OPTIONAL MATCH (p)-[:COLLABORATES_WITH]->(other:Person)
RETURN p, collect(DISTINCT other) as collaborators
```

### Context Building

```
┌─────────────────────────────────────────────────────────────────┐
│                 USER CONTEXT FROM KNOWLEDGE GRAPH                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Query: "What should I focus on for the AI project?"       │
│                                                                  │
│  Graph Traversal:                                                │
│  1. User → WORKS_ON → Project (AI Project)                      │
│  2. Project → HAS_MEMBER → Person (team members)                │
│  3. User → INTERESTED_IN → Concept (AI, ML, etc.)               │
│  4. Learning → RELATES_TO → Concept                             │
│                                                                  │
│  Aggregated Context:                                             │
│  - Project status and recent updates                            │
│  - Team members and their roles                                 │
│  - Related learnings and concepts                               │
│  - Historical decisions on similar topics                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Reference

### Authentication Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/signup` | Register new user | No |
| POST | `/auth/login` | Login (returns JWT) | No |
| GET | `/auth/profile` | Get user profile | Yes |
| PUT | `/auth/profile` | Update profile | Yes |

### Chat Endpoint

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/chat` | Chat with Alfred | Yes |

**Request:**
```json
{
  "message": "What are my priorities today?"
}
```

**Response:**
```json
{
  "response": "Good morning! Based on your schedule...",
  "context": {
    "projects_mentioned": [],
    "tasks_created": [],
    "preferences_learned": []
  }
}
```

### Project Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/projects` | Create project | Yes |
| GET | `/projects` | List projects | Yes |
| GET | `/projects/{id}` | Get project | Yes |
| PUT | `/projects/{id}` | Update project | Yes |
| DELETE | `/projects/{id}` | Delete project | Yes |
| POST | `/projects/{id}/updates` | Add update | Yes |
| GET | `/projects/{id}/updates` | Get updates | Yes |

### Task Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/tasks` | Create task | Yes |
| GET | `/tasks` | List tasks | Yes |
| GET | `/tasks/{id}` | Get task | Yes |
| PUT | `/tasks/{id}` | Update task | Yes |
| POST | `/tasks/{id}/complete` | Complete task | Yes |
| DELETE | `/tasks/{id}` | Delete task | Yes |

### Habit Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/habits` | Create habit | Yes |
| GET | `/habits` | List habits | Yes |
| GET | `/habits/{id}` | Get habit | Yes |
| PUT | `/habits/{id}` | Update habit | Yes |
| POST | `/habits/{id}/log` | Log completion | Yes |
| GET | `/habits/{id}/history` | Get history | Yes |
| DELETE | `/habits/{id}` | Delete habit | Yes |

### Dashboard Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/dashboard/today` | Today's overview | Yes |
| GET | `/dashboard/week` | Weekly overview | Yes |
| GET | `/dashboard/project-health` | Project health | Yes |
| GET | `/dashboard/stats` | Statistics | Yes |
| GET | `/dashboard/briefing/morning` | Morning briefing | Yes |
| GET | `/dashboard/briefing/evening` | Evening review | Yes |

### Notification Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/notifications/register-token` | Register push token | Yes |
| DELETE | `/notifications/unregister-token` | Unregister | Yes |
| GET | `/notifications/preferences` | Get preferences | Yes |
| PUT | `/notifications/preferences` | Update preferences | Yes |
| GET | `/notifications/pending` | Get pending | Yes |
| POST | `/notifications/{id}/read` | Mark read | Yes |
| POST | `/notifications/{id}/dismiss` | Dismiss | Yes |
| POST | `/notifications/test` | Test push | Yes |

---

## Data Flow

### Chat Request Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            CHAT REQUEST FLOW                                  │
└──────────────────────────────────────────────────────────────────────────────┘

    Mobile App                    Backend                      External Services
    ──────────                    ───────                      ─────────────────
         │                            │                              │
         │  POST /chat                │                              │
         │  {message, user_id}        │                              │
         │───────────────────────────►│                              │
         │                            │                              │
         │                            │  1. Load user context        │
         │                            │     from PostgreSQL          │
         │                            │────────────────────────────► │
         │                            │◄────────────────────────────│
         │                            │                              │
         │                            │  2. Query knowledge graph    │
         │                            │     (Neo4j)                  │
         │                            │────────────────────────────►│
         │                            │◄────────────────────────────│
         │                            │                              │
         │                            │  3. Vector search for        │
         │                            │     relevant knowledge       │
         │                            │────────────────────────────►│
         │                            │◄────────────────────────────│
         │                            │                              │
         │                            │  4. Build context-rich       │
         │                            │     prompt                   │
         │                            │                              │
         │                            │  5. Call LLM                 │
         │                            │     (OpenAI/Ollama)          │
         │                            │────────────────────────────►│
         │                            │◄────────────────────────────│
         │                            │                              │
         │                            │  6. Extract learnings        │
         │                            │     & preferences            │
         │                            │                              │
         │                            │  7. Store in PostgreSQL      │
         │                            │     & Neo4j                  │
         │                            │────────────────────────────►│
         │                            │                              │
         │  {response, context}       │                              │
         │◄───────────────────────────│                              │
         │                            │                              │
```

### Proactive Notification Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         PROACTIVE NOTIFICATION FLOW                           │
└──────────────────────────────────────────────────────────────────────────────┘

  Scheduler                  Proactive Engine              External Services
  ─────────                  ────────────────              ─────────────────
      │                            │                              │
      │  Trigger (cron)            │                              │
      │───────────────────────────►│                              │
      │                            │                              │
      │                            │  1. Load user data           │
      │                            │     - Active projects        │
      │                            │     - Due tasks              │
      │                            │     - Habit streaks          │
      │                            │────────────────────────────►│
      │                            │◄────────────────────────────│
      │                            │                              │
      │                            │  2. Analyze patterns         │
      │                            │     - Overdue tasks          │
      │                            │     - Streaks at risk        │
      │                            │     - Stale projects         │
      │                            │                              │
      │                            │  3. Generate briefing        │
      │                            │     via LLM                  │
      │                            │────────────────────────────►│
      │                            │◄────────────────────────────│
      │                            │                              │
      │                            │  4. Send push notification   │
      │                            │     via Expo                 │
      │                            │────────────────────────────►│
      │                            │                              │
      │  Schedule next             │                              │
      │◄───────────────────────────│                              │
      │                            │                              │
```

---

## Authentication Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           AUTHENTICATION FLOW                                 │
└──────────────────────────────────────────────────────────────────────────────┘

SIGNUP:
────────
┌──────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Mobile  │─────►│ POST /signup │─────►│ Hash Password│─────►│ Store User   │
│   App    │      │              │      │   (bcrypt)   │      │  PostgreSQL  │
└──────────┘      └──────────────┘      └──────────────┘      └──────────────┘
                                                                      │
                                                                      ▼
                                                              ┌──────────────┐
                                                              │ Generate JWT │
                                                              │   Token      │
                                                              └──────────────┘
                                                                      │
                                                                      ▼
┌──────────┐      ┌──────────────┐
│  Mobile  │◄─────│   Return     │
│   App    │      │ {token, user}│
└──────────┘      └──────────────┘


LOGIN:
──────
┌──────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Mobile  │─────►│ POST /login  │─────►│ Verify Hash  │─────►│ Generate JWT │
│   App    │      │ email, pass  │      │   (bcrypt)   │      │   Token      │
└──────────┘      └──────────────┘      └──────────────┘      └──────────────┘
                                                                      │
                                                                      ▼
┌──────────┐      ┌──────────────┐
│  Mobile  │◄─────│ {access_token│
│   App    │      │  token_type} │
└──────────┘      └──────────────┘


AUTHENTICATED REQUEST:
──────────────────────
┌──────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Mobile  │─────►│ API Request  │─────►│ Validate JWT │─────►│   Execute    │
│   App    │      │ Bearer Token │      │  Extract ID  │      │   Handler    │
└──────────┘      └──────────────┘      └──────────────┘      └──────────────┘


JWT Token Structure:
───────────────────
{
  "sub": "user_id (UUID)",
  "email": "user@example.com",
  "exp": 1234567890  // 30 minutes from issue
}
```

---

## Mobile App Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          MOBILE APP ARCHITECTURE                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              REACT NATIVE + EXPO                                 │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         NAVIGATION (React Navigation)                    │   │
│  │                                                                          │   │
│  │   ┌────────────────────────────────────────────────────────────────┐    │   │
│  │   │                      AUTH NAVIGATOR                             │    │   │
│  │   │   ┌──────────────┐            ┌──────────────┐                 │    │   │
│  │   │   │    Login     │            │    Signup    │                 │    │   │
│  │   │   │   Screen     │            │    Screen    │                 │    │   │
│  │   │   └──────────────┘            └──────────────┘                 │    │   │
│  │   └────────────────────────────────────────────────────────────────┘    │   │
│  │                                     │                                    │   │
│  │                                     ▼ (authenticated)                    │   │
│  │   ┌────────────────────────────────────────────────────────────────┐    │   │
│  │   │                      MAIN NAVIGATOR (Bottom Tabs)               │    │   │
│  │   │                                                                 │    │   │
│  │   │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────┐ │    │   │
│  │   │   │Dashboard │ │ Projects │ │  Tasks   │ │  Habits  │ │Chat │ │    │   │
│  │   │   │  Screen  │ │  Screen  │ │  Screen  │ │  Screen  │ │Scrn │ │    │   │
│  │   │   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └─────┘ │    │   │
│  │   │                                                                 │    │   │
│  │   └────────────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                           API LAYER                                      │   │
│  │                                                                          │   │
│  │   ┌──────────────────────────────────────────────────────────────────┐  │   │
│  │   │                     client.ts (Axios)                             │  │   │
│  │   │  - Base URL configuration (platform-aware)                        │  │   │
│  │   │  - JWT token injection via interceptor                            │  │   │
│  │   │  - SecureStore for token persistence                              │  │   │
│  │   └──────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                          │   │
│  │   ┌──────────────────────────────────────────────────────────────────┐  │   │
│  │   │                     services.ts                                   │  │   │
│  │   │  - authApi: signup, login, logout                                 │  │   │
│  │   │  - dashboardApi: getToday, getStats                              │  │   │
│  │   │  - projectsApi: CRUD operations                                   │  │   │
│  │   │  - tasksApi: CRUD operations                                      │  │   │
│  │   │  - habitsApi: CRUD + logging                                      │  │   │
│  │   └──────────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         SERVICES                                         │   │
│  │   ┌──────────────────────────────────────────────────────────────────┐  │   │
│  │   │                  notifications.ts                                 │  │   │
│  │   │  - Push notification registration                                 │  │   │
│  │   │  - Token management with Expo                                     │  │   │
│  │   │  - Notification handlers                                          │  │   │
│  │   └──────────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Screen Details

| Screen | Features |
|--------|----------|
| **DashboardScreen** | Today's overview, priority tasks, habit progress, project health |
| **ProjectsScreen** | List/create/update projects, view health scores, filter by status |
| **TasksScreen** | Task list with filters, quick complete, priority indicators |
| **HabitsScreen** | Habit tracking, streak display, quick log |
| **ChatScreen** | Gifted Chat UI, conversation with Alfred |
| **ProfileScreen** | User settings, preferences, logout |

---

## MCP Integration

### Model Context Protocol Servers

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MCP ARCHITECTURE                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   Alfred Core   │
│    (Client)     │
└────────┬────────┘
         │
         │ MCP Protocol
         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MCP SERVERS                                         │
│                                                                                  │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐     │
│  │   Filesystem MCP    │  │  Brave Search MCP   │  │   Postgres MCP      │     │
│  │                     │  │                     │  │                     │     │
│  │  - Read files       │  │  - Web search       │  │  - Query database   │     │
│  │  - Write files      │  │  - Get snippets     │  │  - Store memories   │     │
│  │  - List directory   │  │  - Summarize pages  │  │  - Retrieve context │     │
│  │                     │  │                     │  │                     │     │
│  │  Path: user_data/   │  │  API: BRAVE_API_KEY │  │  DB: alfred_memory  │     │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Configuration

**File:** `mcp_config.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/pratap/work/Personal-Assistant/user_data"]
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    },
    "memory": {
      "command": "python",
      "args": ["-m", "mcp_server_postgres", "--connection-string", "postgresql://user:password@localhost/alfred_memory"]
    }
  }
}
```

### Capabilities

| Server | Capability | Use Case |
|--------|------------|----------|
| **Filesystem** | Read/Write files | Store user documents, notes, exports |
| **Brave Search** | Web search | Research, fact-checking, current events |
| **Postgres Memory** | Database queries | Long-term memory, context retrieval |

---

## Configuration Reference

### Environment Variables

```bash
# .env file

# LLM Configuration
ALFRED_MODEL_TYPE=OPENAI          # OPENAI or OLLAMA
OPENAI_API_KEY=sk-...             # OpenAI API key
OLLAMA_BASE_URL=http://localhost:11434  # Local Ollama URL

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/alfred_db

# Vector Store
QDRANT_URL=http://localhost:6333

# Knowledge Graph
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Authentication
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Push Notifications
EXPO_ACCESS_TOKEN=your_expo_token

# MCP
BRAVE_API_KEY=your_brave_api_key
```

### Service Ports

| Service | Default Port | Protocol |
|---------|--------------|----------|
| FastAPI Backend | 8000 | HTTP |
| PostgreSQL | 5432 | TCP |
| Neo4j Bolt | 7687 | Bolt |
| Neo4j HTTP | 7474 | HTTP |
| Qdrant | 6333 | HTTP |
| Ollama | 11434 | HTTP |

---

## Debugging Guide

### Common Issues

#### 1. Database Connection Failed

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U user -d alfred_db

# Common fix: Ensure database exists
createdb alfred_db
```

#### 2. Neo4j Connection Failed

```bash
# Check Neo4j status
sudo systemctl status neo4j

# Test connection (browser)
open http://localhost:7474

# Common fix: Neo4j is optional, service starts without it
# Check logs for: "Neo4j unavailable, starting without knowledge graph"
```

#### 3. Qdrant Connection Failed

```bash
# Start Qdrant with Docker
docker run -p 6333:6333 qdrant/qdrant

# Check health
curl http://localhost:6333/health
```

#### 4. LLM Not Responding

```bash
# For OpenAI: Check API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# For Ollama: Check local service
curl http://localhost:11434/api/tags
```

#### 5. JWT Token Issues

```python
# Decode token for debugging
import jwt
token = "your_token_here"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
```

### Logging

Enable detailed logging:

```python
# In alfred/api/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword"

# Chat (with token)
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are my tasks for today?"}'
```

### Mobile App Debugging

```bash
# Start with debugging
cd mobile
npx expo start --dev-client

# View logs
npx react-native log-android  # Android
npx react-native log-ios      # iOS
```

### Database Queries for Debugging

```sql
-- Check user data
SELECT * FROM users WHERE email = 'user@example.com';

-- Check recent chat history
SELECT * FROM chat_history
WHERE user_id = 'uuid'
ORDER BY created_at DESC
LIMIT 10;

-- Check pending notifications
SELECT * FROM scheduled_notifications
WHERE status = 'pending'
AND trigger_time <= NOW();

-- Check habit streaks
SELECT name, current_streak, best_streak, last_logged
FROM habits
WHERE user_id = 'uuid';
```

### Performance Monitoring

```bash
# Check API response times
time curl http://localhost:8000/dashboard/today \
  -H "Authorization: Bearer TOKEN"

# Database query performance
EXPLAIN ANALYZE SELECT * FROM tasks WHERE user_id = 'uuid';
```

---

## Key File Reference

| Component | File Path |
|-----------|-----------|
| Main FastAPI App | `alfred/api/main.py` |
| Core Butler Logic | `alfred/core/butler.py` |
| Proactive Engine | `alfred/core/proactive_engine.py` |
| Data Models | `alfred/core/entities.py` |
| Interfaces/Contracts | `alfred/core/interfaces.py` |
| PostgreSQL Adapter | `alfred/infrastructure/storage/postgres_db.py` |
| OpenAI LLM | `alfred/infrastructure/llm/openai_adapter.py` |
| Ollama LLM | `alfred/infrastructure/llm/ollama_adapter.py` |
| Neo4j Integration | `alfred/infrastructure/knowledge/neo4j_graph.py` |
| Expo Notifications | `alfred/infrastructure/notifications/expo_push.py` |
| Auth Routes | `alfred/api/auth.py` |
| Project Routes | `alfred/api/projects.py` |
| Task Routes | `alfred/api/tasks.py` |
| Habit Routes | `alfred/api/habits.py` |
| Dashboard Routes | `alfred/api/dashboard.py` |
| Notification Routes | `alfred/api/notifications.py` |
| Agno Agent | `app/agents/alfred_agent.py` |
| Mobile App Shell | `mobile/App.tsx` |
| API Client | `mobile/src/api/client.ts` |
| API Services | `mobile/src/api/services.ts` |
| MCP Config | `mcp_config.json` |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-26 | Initial documentation |

---

*Generated for Alfred - The Digital Butler*
