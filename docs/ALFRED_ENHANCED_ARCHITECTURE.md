# Alfred Enhanced Architecture

> Your AI butler that just works. You provide OAuth credentials, users connect their accounts.

---

## Overview

Alfred is a personal AI assistant with:

1. **Zero-Config for Users** - Users just connect their accounts via OAuth
2. **Developer-Managed API Keys** - You configure LLM and OAuth credentials
3. **Multi-Agent System** - Specialized AI agents working together
4. **OAuth Integrations** - Connect Google, Microsoft, Notion, Todoist

---

## 1. Configuration Model

### Developer Configuration (Environment Variables)

| Variable | Purpose | Required |
|----------|---------|----------|
| `OPENAI_API_KEY` | LLM provider (OpenAI) | One LLM required |
| `ANTHROPIC_API_KEY` | LLM provider (Anthropic) | One LLM required |
| `OLLAMA_URL` | LLM provider (Local) | One LLM required |
| `GOOGLE_CLIENT_ID` | Google OAuth | For Google integrations |
| `GOOGLE_CLIENT_SECRET` | Google OAuth | For Google integrations |
| `MICROSOFT_CLIENT_ID` | Microsoft OAuth | For Microsoft integrations |
| `MICROSOFT_CLIENT_SECRET` | Microsoft OAuth | For Microsoft integrations |
| `NOTION_CLIENT_ID` | Notion OAuth | For Notion integration |
| `NOTION_CLIENT_SECRET` | Notion OAuth | For Notion integration |
| `TODOIST_CLIENT_ID` | Todoist OAuth | For Todoist integration |
| `TODOIST_CLIENT_SECRET` | Todoist OAuth | For Todoist integration |

### Auto-Configured Components

| Component | External Option | Embedded Fallback |
|-----------|-----------------|-------------------|
| Database | PostgreSQL (`DATABASE_URL`) | SQLite (`~/.alfred/alfred.db`) |
| Knowledge Graph | Neo4j (`NEO4J_URI`) | DuckDB (`~/.alfred/knowledge.duckdb`) |
| Vector Store | Qdrant (`QDRANT_URL`) | Chroma (`~/.alfred/vectors/`) |
| Secret Key | `SECRET_KEY` env | Auto-generated (`~/.alfred/.secret`) |

---

## 2. OAuth Integration Flow

### How It Works (Like Manus/Claude)

1. **User clicks "Connect"** → App generates OAuth URL with your credentials
2. **User redirects to provider** → Google, Microsoft, etc. login page
3. **User authorizes** → Provider redirects back with authorization code
4. **App exchanges code for tokens** → Stored securely in database
5. **App operates on user's behalf** → Using stored tokens

### User Flow

```
Settings > Integrations > Google Calendar > [Connect]
    ↓
User redirected to Google login
    ↓
User grants calendar permissions
    ↓
Redirected back to Alfred
    ↓
"Google Calendar connected!"
```

### Supported Integrations

| Integration | Capabilities | OAuth Provider |
|-------------|--------------|----------------|
| Google Calendar | Read/create events, check availability | Google |
| Gmail | Read inbox, send emails | Google |
| Outlook Calendar | Read/create events, check availability | Microsoft |
| Outlook Mail | Read inbox, send emails | Microsoft |
| Notion | Read/write pages and databases | Notion |
| Todoist | Read/create tasks and projects | Todoist |

---

## 3. Multi-Agent Architecture

### Agent Types

| Agent | Responsibility |
|-------|----------------|
| **Task Agent** | Create, update, query, complete tasks |
| **Memory Agent** | Recall facts, store preferences, context |
| **Planning Agent** | Break down goals, suggest next steps |
| **Calendar Agent** | Check availability, create events |
| **Email Agent** | Summarize inbox, draft emails |
| **Research Agent** | Web search, compare options |

### Request Flow

```
User Input
    ↓
Intent Router (fast pattern matching → LLM fallback)
    ↓
Orchestrator selects agents
    ↓
Memory Agent runs first (context)
    ↓
Other agents run in parallel
    ↓
Synthesize unified response
    ↓
Store interaction for learning
```

---

## 4. Database Schema

### Core Tables

| Table | Purpose |
|-------|---------|
| `users` | User accounts and profiles |
| `chat_history` | Conversation logs |
| `user_preferences` | Learned preferences |
| `projects` | Project metadata |
| `tasks` | Task management |
| `habits` | Habit tracking |
| `scheduled_notifications` | Proactive notifications |
| `integration_credentials` | OAuth tokens per user |

### Integration Credentials Table

Stores OAuth tokens securely per user per integration:

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | TEXT | User identifier |
| `integration_name` | TEXT | e.g., "google_calendar" |
| `access_token` | TEXT | OAuth access token |
| `refresh_token` | TEXT | OAuth refresh token |
| `expires_at` | TIMESTAMP | Token expiration |
| `scope` | TEXT | Granted permissions |

---

## 5. API Endpoints

### Authentication

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/signup` | POST | Create account |
| `/auth/login` | POST | Get JWT token |
| `/auth/profile` | GET | Get user profile |

### Chat

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat` | POST | Single-turn chat |
| `/chat/stream` | POST | Streaming chat |

### Integrations

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/integrations` | GET | List available integrations |
| `/api/integrations/user` | GET | User's connected integrations |
| `/api/integrations/{name}/auth` | GET | Get OAuth URL |
| `/api/integrations/callback/{provider}` | GET | OAuth callback handler |
| `/api/integrations/{name}/disconnect` | POST | Disconnect integration |

### Core Features

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/tasks` | GET/POST | Manage tasks |
| `/projects` | GET/POST | Manage projects |
| `/habits` | GET/POST | Manage habits |
| `/dashboard` | GET | Dashboard data |
| `/proactive/briefing` | GET | Morning/evening briefing |

---

## 6. File Structure

```
alfred/
├── core/
│   ├── orchestrator.py      # Agent coordination
│   ├── config_manager.py    # Zero-config setup
│   ├── proactive_engine.py  # Briefings & nudges
│   └── agents/
│       ├── base.py
│       ├── task_agent.py
│       ├── memory_agent.py
│       └── planning_agent.py
│
├── infrastructure/
│   ├── llm/                 # LLM providers
│   ├── storage/             # Database adapters
│   ├── notifications/       # Push notifications
│   └── scheduler/           # Background jobs
│
├── integrations/
│   ├── base.py              # OAuth base classes
│   ├── manager.py           # Integration manager
│   ├── google/              # Google Calendar, Gmail
│   ├── outlook/             # Outlook Calendar, Mail
│   ├── notion/              # Notion
│   └── todoist/             # Todoist
│
└── api/
    ├── auth.py
    ├── tasks.py
    ├── projects.py
    ├── habits.py
    └── integrations.py
```

---

## 7. Deployment Options

### Single User (Embedded)

Everything runs locally:
- SQLite database
- DuckDB knowledge graph
- Chroma vector store
- No external services needed

### Small Team (Server)

Shared PostgreSQL database:
- Users connect their own OAuth accounts
- Shared server infrastructure
- Developer manages OAuth credentials

### Enterprise

Full distributed setup:
- PostgreSQL with replication
- Neo4j knowledge graph
- Qdrant vector store
- Kubernetes deployment

---

## 8. Security

### API Keys

- LLM API keys: Developer-managed via environment
- OAuth credentials: Developer-managed via environment
- Never exposed to users

### User Tokens

- OAuth tokens: Encrypted in database
- JWT tokens: 30-minute expiry
- Refresh tokens: Used for automatic renewal

### Data Privacy

- All data in your database
- No third-party data sharing
- User controls what integrations to connect

---

## 9. Cost Considerations

### LLM Costs (OpenAI GPT-4o)

| Usage Level | Turns/Day | Monthly Cost |
|-------------|-----------|--------------|
| Light | 10 | ~$6-10 |
| Average | 30 | ~$18-30 |
| Heavy | 50+ | ~$30-50 |

### Infrastructure Costs

| Component | Embedded | Managed |
|-----------|----------|---------|
| Database | Free (SQLite) | $10-50/mo (managed Postgres) |
| Vector DB | Free (Chroma) | $20-100/mo (Qdrant Cloud) |
| Graph DB | Free (DuckDB) | $50-200/mo (Neo4j Aura) |

---

## 10. Getting Started

### 1. Set LLM Provider

```bash
export OPENAI_API_KEY="sk-..."
```

### 2. Set OAuth Credentials (Optional)

```bash
# For Google integrations
export GOOGLE_CLIENT_ID="..."
export GOOGLE_CLIENT_SECRET="..."

# For Microsoft integrations
export MICROSOFT_CLIENT_ID="..."
export MICROSOFT_CLIENT_SECRET="..."
```

### 3. Run Alfred

```bash
cd alfred
python -m uvicorn main:app --reload
```

### 4. User Onboarding

1. User creates account
2. User connects desired integrations via OAuth
3. Alfred operates with their connected services

---

*Simple for users. Powerful for you.*
