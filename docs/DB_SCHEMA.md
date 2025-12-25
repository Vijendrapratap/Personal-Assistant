# Database Schema

Alfred uses PostgreSQL for persistent storage of conversation history and optional structured learnings.

## Tables

### 1. users
Stores authentication and profile data.

| Column | Type | Description |
| :--- | :--- | :--- |
| `user_id` | `VARCHAR` | Unique ID (PK) |
| `email` | `VARCHAR` | Unique Email |
| `password_hash` | `TEXT` | Hashed Password |
| `profile` | `JSONB` | Stores bio, voice_id, personality settings |
| `created_at` | `TIMESTAMP` | Creation time |

### 2. chat_history
Stores messages.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Unique ID |
| `user_id` | `VARCHAR` | Owner |
| `role` | `VARCHAR` | 'user' or 'assistant' |
| `content` | `TEXT` | Message text |
| `created_at` | `TIMESTAMP` | Timestamp |

### 3. user_preferences
Key-Value store for specific learned preferences.

| Column | Type | Description |
| :--- | :--- | :--- |
| `user_id` | `VARCHAR` | Owner |
| `key` | `VARCHAR` | Preference Key |
| `value` | `TEXT` | Preference Value |
