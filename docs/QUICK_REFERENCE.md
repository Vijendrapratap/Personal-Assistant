# Alfred - Quick Reference Guide

> Fast lookup for developers debugging and updating features

## Quick Links

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Full system architecture |
| [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) | PostgreSQL tables & queries |
| [VECTOR_AND_KNOWLEDGE_GRAPH.md](./VECTOR_AND_KNOWLEDGE_GRAPH.md) | Qdrant & Neo4j integration |

---

## Service Ports

```
┌────────────────────┬───────┬─────────────────────┐
│ Service            │ Port  │ URL                 │
├────────────────────┼───────┼─────────────────────┤
│ FastAPI Backend    │ 8000  │ http://localhost:8000│
│ PostgreSQL         │ 5432  │ localhost:5432      │
│ Neo4j Bolt         │ 7687  │ bolt://localhost:7687│
│ Neo4j Browser      │ 7474  │ http://localhost:7474│
│ Qdrant             │ 6333  │ http://localhost:6333│
│ Ollama             │ 11434 │ http://localhost:11434│
└────────────────────┴───────┴─────────────────────┘
```

---

## Key Files by Feature

### Backend Core

| Feature | File |
|---------|------|
| FastAPI Entry | `alfred/api/main.py` |
| Butler Brain | `alfred/core/butler.py` |
| Proactive Engine | `alfred/core/proactive_engine.py` |
| Data Models | `alfred/core/entities.py` |
| Interfaces | `alfred/core/interfaces.py` |

### API Routes

| Route | File |
|-------|------|
| Authentication | `alfred/api/auth.py` |
| Projects | `alfred/api/projects.py` |
| Tasks | `alfred/api/tasks.py` |
| Habits | `alfred/api/habits.py` |
| Dashboard | `alfred/api/dashboard.py` |
| Notifications | `alfred/api/notifications.py` |

### Infrastructure

| Service | File |
|---------|------|
| PostgreSQL | `alfred/infrastructure/storage/postgres_db.py` |
| OpenAI LLM | `alfred/infrastructure/llm/openai_adapter.py` |
| Ollama LLM | `alfred/infrastructure/llm/ollama_adapter.py` |
| Neo4j Graph | `alfred/infrastructure/knowledge/neo4j_graph.py` |
| Expo Push | `alfred/infrastructure/notifications/expo_push.py` |

### Mobile App

| Component | File |
|-----------|------|
| App Shell | `mobile/App.tsx` |
| API Client | `mobile/src/api/client.ts` |
| API Services | `mobile/src/api/services.ts` |
| Dashboard | `mobile/src/screens/DashboardScreen.tsx` |
| Chat | `mobile/src/screens/ChatScreen.tsx` |

---

## API Endpoints Cheat Sheet

### Auth
```bash
POST /auth/signup       # Register
POST /auth/login        # Login (returns JWT)
GET  /auth/profile      # Get profile
PUT  /auth/profile      # Update profile
```

### Chat
```bash
POST /chat              # Chat with Alfred
     Body: {"message": "..."}
```

### Projects
```bash
GET    /projects                    # List
POST   /projects                    # Create
GET    /projects/{id}               # Get one
PUT    /projects/{id}               # Update
DELETE /projects/{id}               # Delete
POST   /projects/{id}/updates       # Add update
GET    /projects/{id}/updates       # Get updates
```

### Tasks
```bash
GET    /tasks                       # List (filters: project_id, status, priority)
POST   /tasks                       # Create
GET    /tasks/{id}                  # Get one
PUT    /tasks/{id}                  # Update
POST   /tasks/{id}/complete         # Mark complete
DELETE /tasks/{id}                  # Delete
```

### Habits
```bash
GET    /habits                      # List
POST   /habits                      # Create
GET    /habits/{id}                 # Get one
PUT    /habits/{id}                 # Update
POST   /habits/{id}/log             # Log completion
GET    /habits/{id}/history         # Get history
DELETE /habits/{id}                 # Delete
```

### Dashboard
```bash
GET /dashboard/today              # Today's overview
GET /dashboard/week               # Weekly overview
GET /dashboard/project-health     # Project health
GET /dashboard/stats              # Statistics
GET /dashboard/briefing/morning   # Morning briefing
GET /dashboard/briefing/evening   # Evening review
```

### Notifications
```bash
POST   /notifications/register-token     # Register push token
DELETE /notifications/unregister-token   # Unregister
GET    /notifications/preferences        # Get prefs
PUT    /notifications/preferences        # Update prefs
GET    /notifications/pending            # Get pending
POST   /notifications/{id}/read          # Mark read
POST   /notifications/{id}/dismiss       # Dismiss
POST   /notifications/test               # Test push
```

---

## Database Quick Queries

### User Data
```sql
-- Get user
SELECT * FROM users WHERE email = 'user@example.com';

-- Get user preferences
SELECT * FROM user_preferences WHERE user_id = 'uuid';

-- Recent chat history
SELECT role, content, created_at
FROM chat_history
WHERE user_id = 'uuid'
ORDER BY created_at DESC LIMIT 10;
```

### Tasks
```sql
-- Today's priority tasks
SELECT task_id, title, priority, due_date
FROM tasks
WHERE user_id = 'uuid' AND status = 'pending'
  AND due_date <= CURRENT_DATE + 1
ORDER BY priority, due_date;

-- Overdue tasks
SELECT * FROM tasks
WHERE user_id = 'uuid' AND status = 'pending'
  AND due_date < CURRENT_DATE;
```

### Habits
```sql
-- Today's habits with status
SELECT h.name, h.current_streak,
       CASE WHEN hl.logged_date = CURRENT_DATE THEN true ELSE false END as done
FROM habits h
LEFT JOIN habit_logs hl ON h.habit_id = hl.habit_id
  AND hl.logged_date = CURRENT_DATE
WHERE h.user_id = 'uuid' AND h.active = true;

-- Streaks at risk
SELECT name, current_streak, last_logged
FROM habits
WHERE user_id = 'uuid' AND current_streak > 0
  AND last_logged < CURRENT_DATE;
```

### Projects
```sql
-- Active projects with last update
SELECT p.name, p.status, MAX(pu.created_at) as last_update
FROM projects p
LEFT JOIN project_updates pu ON p.project_id = pu.project_id
WHERE p.user_id = 'uuid' AND p.status = 'active'
GROUP BY p.project_id;

-- Stale projects (no updates in 7 days)
SELECT p.name FROM projects p
LEFT JOIN project_updates pu ON p.project_id = pu.project_id
WHERE p.user_id = 'uuid' AND p.status = 'active'
GROUP BY p.project_id
HAVING MAX(pu.created_at) < CURRENT_DATE - 7 OR MAX(pu.created_at) IS NULL;
```

---

## Neo4j Quick Queries

```cypher
-- User's full context
MATCH (u:User {user_id: $user_id})
OPTIONAL MATCH (u)-[:WORKS_ON]->(p:Project)
OPTIONAL MATCH (u)-[:KNOWS]->(person:Person)
OPTIONAL MATCH (u)-[:INTERESTED_IN]->(c:Concept)
RETURN u, collect(p), collect(person), collect(c)

-- Project team
MATCH (p:Project {name: $name})<-[:WORKS_ON]-(u:User)
OPTIONAL MATCH (p)-[:HAS_MEMBER]->(person:Person)
RETURN u, collect(person)

-- Related concepts
MATCH (l:Learning)-[:RELATES_TO]->(c:Concept {name: $concept})
RETURN l.content, l.topic
```

---

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/alfred_db
OPENAI_API_KEY=sk-...
SECRET_KEY=your-secret-key

# Optional
ALFRED_MODEL_TYPE=OPENAI                 # or OLLAMA
OLLAMA_BASE_URL=http://localhost:11434
QDRANT_URL=http://localhost:6333
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
EXPO_ACCESS_TOKEN=your-token
BRAVE_API_KEY=your-key
```

---

## Common Debug Commands

### Start Services
```bash
# Backend
cd alfred && uvicorn api.main:app --reload --port 8000

# Mobile
cd mobile && npx expo start

# Database services
docker-compose up -d postgres neo4j qdrant
```

### Test API
```bash
# Health check
curl http://localhost:8000/health

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=user@example.com&password=pass" | jq -r .access_token)

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are my tasks?"}'

# Dashboard
curl http://localhost:8000/dashboard/today \
  -H "Authorization: Bearer $TOKEN"
```

### Check Services
```bash
# PostgreSQL
psql -h localhost -U user -d alfred_db -c "SELECT 1"

# Neo4j
curl http://localhost:7474

# Qdrant
curl http://localhost:6333/health

# Ollama
curl http://localhost:11434/api/tags
```

### Logs
```bash
# Backend logs (if using uvicorn)
tail -f /var/log/alfred/backend.log

# Docker logs
docker logs -f alfred-postgres
docker logs -f alfred-neo4j
docker logs -f alfred-qdrant
```

---

## Error Troubleshooting

### "Database connection failed"
```bash
# Check PostgreSQL
sudo systemctl status postgresql
psql -h localhost -U user -d alfred_db

# Reset connection
sudo systemctl restart postgresql
```

### "Neo4j unavailable"
```bash
# Check Neo4j (optional service)
sudo systemctl status neo4j

# Service continues without it
# Check logs for: "Neo4j unavailable, starting without knowledge graph"
```

### "Qdrant connection refused"
```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Check health
curl http://localhost:6333/health
```

### "LLM not responding"
```bash
# OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Ollama
curl http://localhost:11434/api/tags

# Switch LLM
export ALFRED_MODEL_TYPE=OLLAMA  # or OPENAI
```

### "JWT token invalid"
```python
# Decode token to debug
import jwt
token = "your_token"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)  # Check exp, sub fields
```

### "Mobile app can't connect"
```bash
# Check API is running
curl http://localhost:8000/health

# Android emulator uses 10.0.2.2 for localhost
# iOS simulator uses localhost

# Check mobile/src/api/client.ts for correct URL
```

---

## Feature Addition Checklist

### Adding a New Entity

1. **Database** (`alfred/infrastructure/storage/postgres_db.py`)
   - Add CREATE TABLE in `_init_tables()`
   - Add CRUD methods

2. **Entities** (`alfred/core/entities.py`)
   - Add dataclass
   - Add related enums

3. **Interface** (`alfred/core/interfaces.py`)
   - Add methods to `MemoryStorage`

4. **API Route** (`alfred/api/`)
   - Create new route file
   - Add Pydantic models
   - Add to `main.py` router

5. **Mobile** (`mobile/src/`)
   - Add TypeScript interfaces in `api/services.ts`
   - Add API functions
   - Create screen if needed

### Adding a New API Endpoint

1. Create handler in appropriate route file
2. Add Pydantic request/response models
3. Add to services.ts in mobile app
4. Test with curl

### Adding to Knowledge Graph

1. Define node schema in Neo4j
2. Create relationship types
3. Add methods to `neo4j_graph.py`
4. Update `get_user_context()` if needed

### Adding Vector Knowledge

1. Define document structure
2. Add to Qdrant via `add_documents()`
3. Update search filters if needed

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   ALFRED                                         │
│                              The Digital Butler                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────────────────────────────────────────────────┐
│   Mobile     │     │                      BACKEND                             │
│   App        │────►│                                                          │
│  (Expo/RN)   │     │   API Layer ──► Core Layer ──► Infrastructure Layer     │
└──────────────┘     │   (Routes)      (Butler)       (Adapters)               │
                     └──────────────────────────────────────────────────────────┘
                                              │
                     ┌────────────────────────┼────────────────────────┐
                     │                        │                        │
                     ▼                        ▼                        ▼
              ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
              │  PostgreSQL  │        │   Qdrant     │        │    Neo4j     │
              │  (Primary)   │        │  (Vectors)   │        │   (Graph)    │
              └──────────────┘        └──────────────┘        └──────────────┘
                     │
              ┌──────┴──────┐
              │             │
              ▼             ▼
        ┌──────────┐  ┌──────────┐
        │  OpenAI  │  │  Ollama  │
        │   LLM    │  │   LLM    │
        └──────────┘  └──────────┘
```

---

*Quick Reference Guide for Alfred - The Digital Butler*
