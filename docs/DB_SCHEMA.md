# Database Schema

Alfred uses PostgreSQL for persistent storage of conversation history and optional structured learnings.

## Tables

### 1. alfred_conversations
Managed automatically by `agno.storage.agent.postgres.PostgresAgentStorage`.

| Column | Type | Description |
| :--- | :--- | :--- |
| `session_id` | `VARCHAR` | Unique identifier for the chat session |
| `user_id` | `VARCHAR` | ID of the user |
| `memory` | `JSONB` | serialized memory/messages |
| `created_at` | `TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMP` | Last update timestamp |

### 2. learnings (Proposed)
Stores user feedback and corrections for self-improvement.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Unique ID |
| `user_id` | `VARCHAR` | User who provided the feedback |
| `topic` | `VARCHAR` | Optional topic/category |
| `content` | `TEXT` | The knowledge/correction to remember |
| `original_query` | `TEXT` | The question that prompted the correction |
| `created_at` | `TIMESTAMP` | Timestamp |

## Connection
- **URL**: `postgresql+psycopg://user:password@localhost:5432/alfred_db`
- **Library**: `psycopg` (v3)
