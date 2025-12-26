# Alfred - Database Schema Documentation

> Complete PostgreSQL database schema with migrations, queries, and maintenance guides

## Table of Contents

1. [Overview](#overview)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Table Definitions](#table-definitions)
4. [Indexes](#indexes)
5. [Sample Queries](#sample-queries)
6. [Migration Scripts](#migration-scripts)
7. [Maintenance](#maintenance)

---

## Overview

Alfred uses **PostgreSQL** as the primary relational database for storing:
- User accounts and authentication
- Chat history and conversations
- Learned user preferences
- Projects and progress updates
- Tasks with priorities and statuses
- Habits with streak tracking
- Scheduled notifications

### Connection Configuration

```python
# Environment variable
DATABASE_URL=postgresql://user:password@localhost:5432/alfred_db

# Connection in code (alfred/infrastructure/storage/postgres_db.py)
self.conn = psycopg.connect(os.getenv("DATABASE_URL"))
```

---

## Entity Relationship Diagram

```
                                    ┌─────────────────────┐
                                    │       users         │
                                    ├─────────────────────┤
                                    │ PK user_id (UUID)   │
                                    │    email (UNIQUE)   │
                                    │    password_hash    │
                                    │    profile (JSONB)  │
                                    │    created_at       │
                                    └──────────┬──────────┘
                                               │
           ┌───────────────┬───────────────┬───┴───┬───────────────┬───────────────┐
           │               │               │       │               │               │
           ▼               ▼               ▼       ▼               ▼               ▼
┌──────────────────┐ ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐
│   chat_history   │ │user_preferences │ │  projects   │ │   tasks     │ │       habits        │
├──────────────────┤ ├─────────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────────────┤
│ PK id (SERIAL)   │ │ PK user_id+key  │ │ PK proj_id  │ │ PK task_id  │ │ PK habit_id         │
│ FK user_id       │ │    value        │ │ FK user_id  │ │ FK user_id  │ │ FK user_id          │
│    role          │ │    confidence   │ │    name     │ │ FK proj_id  │ │    name             │
│    content       │ │    learned_at   │ │    org      │ │    title    │ │    frequency        │
│    metadata      │ └─────────────────┘ │    role     │ │    priority │ │    current_streak   │
│    created_at    │                     │    status   │ │    status   │ │    best_streak      │
└──────────────────┘                     │    desc     │ │    due_date │ │    total_completions│
                                         └──────┬──────┘ └─────────────┘ └──────────┬──────────┘
                                                │                                   │
                                                ▼                                   ▼
                                       ┌──────────────────┐              ┌──────────────────┐
                                       │ project_updates  │              │   habit_logs     │
                                       ├──────────────────┤              ├──────────────────┤
                                       │ PK update_id     │              │ PK log_id        │
                                       │ FK project_id    │              │ FK habit_id      │
                                       │ FK user_id       │              │ FK user_id       │
                                       │    content       │              │    logged_date   │
                                       │    update_type   │              │    notes         │
                                       │    action_items  │              │    duration_min  │
                                       │    blockers      │              │    created_at    │
                                       │    created_at    │              └──────────────────┘
                                       └──────────────────┘

                            ┌─────────────────────────────┐      ┌──────────────────┐
                            │   scheduled_notifications   │      │    learnings     │
                            ├─────────────────────────────┤      ├──────────────────┤
                            │ PK notification_id          │      │ PK learning_id   │
                            │ FK user_id                  │      │ FK user_id       │
                            │    notification_type        │      │    topic         │
                            │    title                    │      │    content       │
                            │    content                  │      │    original_query│
                            │    trigger_time             │      │    created_at    │
                            │    context (JSONB)          │      └──────────────────┘
                            │    status                   │
                            │    sent_at                  │
                            │    created_at               │
                            └─────────────────────────────┘
```

---

## Table Definitions

### 1. users

Stores user accounts and authentication data.

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    profile JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Profile JSONB structure:
{
    "name": "John Doe",
    "timezone": "America/New_York",
    "notification_preferences": {
        "morning_briefing": true,
        "evening_review": true,
        "habit_reminders": true
    },
    "push_tokens": ["ExponentPushToken[xxx]"]
}
```

### 2. chat_history

Stores conversation history between users and Alfred.

```sql
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chat_user ON chat_history(user_id);
CREATE INDEX idx_chat_created ON chat_history(created_at);

-- Metadata JSONB structure:
{
    "preferences_learned": ["prefers_morning_meetings"],
    "tasks_created": ["uuid1", "uuid2"],
    "projects_mentioned": ["Project Alpha"],
    "sentiment": "positive"
}
```

### 3. user_preferences

Stores learned user preferences with confidence scores.

```sql
CREATE TABLE user_preferences (
    user_id UUID NOT NULL REFERENCES users(user_id),
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,  -- 0.0 to 1.0
    learned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, key)
);

-- Example preferences:
-- key: "work_start_time", value: "09:00", confidence: 0.9
-- key: "preferred_llm", value: "gpt-4o", confidence: 0.8
-- key: "communication_style", value: "concise", confidence: 0.7
```

### 4. projects

Stores user projects with status tracking.

```sql
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    name TEXT NOT NULL,
    organization TEXT,
    role TEXT DEFAULT 'owner',  -- 'owner', 'member', 'observer'
    status TEXT DEFAULT 'active',  -- 'active', 'on_hold', 'completed', 'archived'
    description TEXT,
    integrations JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);

-- Integrations JSONB:
{
    "github": {"repo": "owner/repo", "connected": true},
    "jira": {"project_key": "PROJ", "connected": false}
}

-- Metadata JSONB:
{
    "tags": ["ai", "mobile"],
    "priority": "high",
    "deadline": "2025-03-01"
}
```

### 5. project_updates

Stores daily updates and progress logs for projects.

```sql
CREATE TABLE project_updates (
    update_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id),
    content TEXT NOT NULL,
    update_type TEXT,  -- 'progress', 'blocker', 'decision', 'note'
    action_items TEXT,
    blockers JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_updates_project ON project_updates(project_id);
CREATE INDEX idx_updates_created ON project_updates(created_at);

-- Blockers JSONB:
[
    {"description": "Waiting for API access", "assigned_to": "DevOps", "created_at": "2025-01-01"},
    {"description": "Need design review", "assigned_to": "Design Team", "resolved": true}
]
```

### 6. tasks

Stores tasks with priorities, statuses, and due dates.

```sql
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    project_id UUID REFERENCES projects(project_id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium',  -- 'low', 'medium', 'high', 'urgent'
    status TEXT DEFAULT 'pending',   -- 'pending', 'in_progress', 'completed', 'blocked'
    due_date TIMESTAMP,
    recurrence TEXT,  -- 'daily', 'weekly', 'monthly', NULL
    blockers TEXT,
    tags JSONB DEFAULT '[]',
    source TEXT DEFAULT 'manual',  -- 'manual', 'conversation', 'import'
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due ON tasks(due_date);
CREATE INDEX idx_tasks_priority ON tasks(priority);

-- Tags JSONB:
["backend", "api", "urgent"]
```

### 7. habits

Stores habits with frequency and streak tracking.

```sql
CREATE TABLE habits (
    habit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    name TEXT NOT NULL,
    frequency TEXT DEFAULT 'daily',  -- 'daily', 'weekly', 'custom'
    time_preference TEXT,  -- 'morning', 'afternoon', 'evening', 'anytime'
    days_of_week JSONB DEFAULT '[]',  -- [1,2,3,4,5] for Mon-Fri
    current_streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    total_completions INTEGER DEFAULT 0,
    last_logged DATE,
    motivation TEXT,
    category TEXT,  -- 'health', 'productivity', 'learning', 'wellness'
    active BOOLEAN DEFAULT true,
    reminder_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_habits_user ON habits(user_id);
CREATE INDEX idx_habits_active ON habits(active);
```

### 8. habit_logs

Stores daily habit completion logs.

```sql
CREATE TABLE habit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    habit_id UUID NOT NULL REFERENCES habits(habit_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id),
    logged_date DATE NOT NULL,
    notes TEXT,
    duration_minutes INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(habit_id, logged_date)
);

CREATE INDEX idx_logs_habit ON habit_logs(habit_id);
CREATE INDEX idx_logs_date ON habit_logs(logged_date);
```

### 9. scheduled_notifications

Stores proactive notifications and briefings.

```sql
CREATE TABLE scheduled_notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    notification_type TEXT NOT NULL,  -- 'morning_briefing', 'evening_review', 'habit_reminder', 'task_due', 'nudge'
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    trigger_time TIMESTAMP NOT NULL,
    context JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending',  -- 'pending', 'sent', 'read', 'dismissed'
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notif_user ON scheduled_notifications(user_id);
CREATE INDEX idx_notif_trigger ON scheduled_notifications(trigger_time);
CREATE INDEX idx_notif_status ON scheduled_notifications(status);

-- Context JSONB:
{
    "task_ids": ["uuid1", "uuid2"],
    "habit_ids": ["uuid3"],
    "project_id": "uuid4"
}
```

### 10. learnings

Stores knowledge and learnings from conversations.

```sql
CREATE TABLE learnings (
    learning_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    topic TEXT NOT NULL,
    content TEXT NOT NULL,
    original_query TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_learnings_user ON learnings(user_id);
CREATE INDEX idx_learnings_topic ON learnings(topic);
```

---

## Indexes

### Performance Indexes

```sql
-- Composite indexes for common queries
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_user_due ON tasks(user_id, due_date);
CREATE INDEX idx_habits_user_active ON habits(user_id, active);
CREATE INDEX idx_notif_user_status ON scheduled_notifications(user_id, status);
CREATE INDEX idx_chat_user_role ON chat_history(user_id, role);

-- Partial indexes for filtered queries
CREATE INDEX idx_tasks_pending ON tasks(user_id, due_date)
    WHERE status = 'pending';
CREATE INDEX idx_notif_pending ON scheduled_notifications(trigger_time)
    WHERE status = 'pending';
CREATE INDEX idx_habits_reminder ON habits(user_id)
    WHERE reminder_enabled = true AND active = true;

-- JSONB indexes
CREATE INDEX idx_projects_tags ON projects USING GIN (metadata jsonb_path_ops);
CREATE INDEX idx_tasks_tags ON tasks USING GIN (tags);
```

---

## Sample Queries

### Dashboard Queries

```sql
-- Today's priority tasks
SELECT task_id, title, priority, due_date, project_id
FROM tasks
WHERE user_id = $1
  AND status = 'pending'
  AND (due_date IS NULL OR due_date <= CURRENT_DATE + INTERVAL '1 day')
ORDER BY
    CASE priority
        WHEN 'urgent' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        ELSE 4
    END,
    due_date NULLS LAST;

-- Today's habits
SELECT h.habit_id, h.name, h.current_streak, h.time_preference,
       CASE WHEN hl.logged_date = CURRENT_DATE THEN true ELSE false END as completed_today
FROM habits h
LEFT JOIN habit_logs hl ON h.habit_id = hl.habit_id AND hl.logged_date = CURRENT_DATE
WHERE h.user_id = $1 AND h.active = true
ORDER BY h.time_preference, h.name;

-- Project health (days since last update)
SELECT p.project_id, p.name, p.status,
       COALESCE(CURRENT_DATE - MAX(pu.created_at)::date,
                CURRENT_DATE - p.created_at::date) as days_since_update
FROM projects p
LEFT JOIN project_updates pu ON p.project_id = pu.project_id
WHERE p.user_id = $1 AND p.status = 'active'
GROUP BY p.project_id
ORDER BY days_since_update DESC;

-- Weekly statistics
SELECT
    COUNT(DISTINCT t.task_id) FILTER (WHERE t.completed_at >= CURRENT_DATE - INTERVAL '7 days') as tasks_completed,
    COUNT(DISTINCT hl.log_id) FILTER (WHERE hl.logged_date >= CURRENT_DATE - INTERVAL '7 days') as habits_logged,
    COUNT(DISTINCT pu.update_id) FILTER (WHERE pu.created_at >= CURRENT_DATE - INTERVAL '7 days') as project_updates
FROM users u
LEFT JOIN tasks t ON u.user_id = t.user_id
LEFT JOIN habits h ON u.user_id = h.user_id
LEFT JOIN habit_logs hl ON h.habit_id = hl.habit_id
LEFT JOIN projects p ON u.user_id = p.user_id
LEFT JOIN project_updates pu ON p.project_id = pu.project_id
WHERE u.user_id = $1;
```

### Chat Context Queries

```sql
-- Recent conversation history (for LLM context)
SELECT role, content, created_at
FROM chat_history
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 10;

-- User preferences with high confidence
SELECT key, value, confidence
FROM user_preferences
WHERE user_id = $1 AND confidence >= 0.7
ORDER BY learned_at DESC;

-- Active context (projects + tasks)
SELECT 'project' as type, p.name, p.status, NULL as due_date
FROM projects p WHERE p.user_id = $1 AND p.status = 'active'
UNION ALL
SELECT 'task' as type, t.title, t.status, t.due_date
FROM tasks t WHERE t.user_id = $1 AND t.status = 'pending'
ORDER BY type, due_date NULLS LAST;
```

### Proactive Engine Queries

```sql
-- Overdue tasks
SELECT task_id, title, due_date, priority
FROM tasks
WHERE user_id = $1
  AND status = 'pending'
  AND due_date < CURRENT_DATE
ORDER BY due_date, priority;

-- Habits with streaks at risk (not logged today, has streak)
SELECT h.habit_id, h.name, h.current_streak, h.last_logged
FROM habits h
WHERE h.user_id = $1
  AND h.active = true
  AND h.current_streak > 0
  AND (h.last_logged IS NULL OR h.last_logged < CURRENT_DATE)
ORDER BY h.current_streak DESC;

-- Stale projects (no updates in 7+ days)
SELECT p.project_id, p.name, MAX(pu.created_at) as last_update
FROM projects p
LEFT JOIN project_updates pu ON p.project_id = pu.project_id
WHERE p.user_id = $1 AND p.status = 'active'
GROUP BY p.project_id
HAVING MAX(pu.created_at) < CURRENT_DATE - INTERVAL '7 days'
    OR MAX(pu.created_at) IS NULL;

-- Pending notifications to send
SELECT notification_id, notification_type, title, content, context
FROM scheduled_notifications
WHERE user_id = $1
  AND status = 'pending'
  AND trigger_time <= NOW()
ORDER BY trigger_time;
```

### Habit Streak Update

```sql
-- Log habit and update streak (transaction)
BEGIN;

-- Insert log entry
INSERT INTO habit_logs (habit_id, user_id, logged_date, notes, duration_minutes)
VALUES ($1, $2, CURRENT_DATE, $3, $4)
ON CONFLICT (habit_id, logged_date) DO UPDATE SET notes = $3, duration_minutes = $4;

-- Update streak
UPDATE habits
SET
    current_streak = CASE
        WHEN last_logged = CURRENT_DATE - INTERVAL '1 day' THEN current_streak + 1
        WHEN last_logged = CURRENT_DATE THEN current_streak
        ELSE 1
    END,
    best_streak = GREATEST(best_streak,
        CASE
            WHEN last_logged = CURRENT_DATE - INTERVAL '1 day' THEN current_streak + 1
            WHEN last_logged = CURRENT_DATE THEN current_streak
            ELSE 1
        END
    ),
    total_completions = total_completions + 1,
    last_logged = CURRENT_DATE
WHERE habit_id = $1 AND last_logged != CURRENT_DATE;

COMMIT;
```

---

## Migration Scripts

### Initial Schema (v1.0.0)

```sql
-- File: migrations/001_initial_schema.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    profile JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat history
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_chat_user ON chat_history(user_id);

-- User preferences
CREATE TABLE user_preferences (
    user_id UUID NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    learned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, key)
);

-- Projects
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    organization TEXT,
    role TEXT DEFAULT 'owner',
    status TEXT DEFAULT 'active',
    description TEXT,
    integrations JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);

-- Project updates
CREATE TABLE project_updates (
    update_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    update_type TEXT,
    action_items TEXT,
    blockers JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_updates_project ON project_updates(project_id);

-- Tasks
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    project_id UUID,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'pending',
    due_date TIMESTAMP,
    recurrence TEXT,
    blockers TEXT,
    tags JSONB DEFAULT '[]',
    source TEXT DEFAULT 'manual',
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due ON tasks(due_date);

-- Habits
CREATE TABLE habits (
    habit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    frequency TEXT DEFAULT 'daily',
    time_preference TEXT,
    days_of_week JSONB DEFAULT '[]',
    current_streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    total_completions INTEGER DEFAULT 0,
    last_logged DATE,
    motivation TEXT,
    category TEXT,
    active BOOLEAN DEFAULT true,
    reminder_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_habits_user ON habits(user_id);

-- Habit logs
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

-- Scheduled notifications
CREATE TABLE scheduled_notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    trigger_time TIMESTAMP NOT NULL,
    context JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_notif_user ON scheduled_notifications(user_id);
CREATE INDEX idx_notif_trigger ON scheduled_notifications(trigger_time);
CREATE INDEX idx_notif_status ON scheduled_notifications(status);

-- Learnings
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

### Add Foreign Keys (v1.0.1)

```sql
-- File: migrations/002_add_foreign_keys.sql

ALTER TABLE chat_history
ADD CONSTRAINT fk_chat_user
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE user_preferences
ADD CONSTRAINT fk_pref_user
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE projects
ADD CONSTRAINT fk_proj_user
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE project_updates
ADD CONSTRAINT fk_update_project
FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE;

ALTER TABLE project_updates
ADD CONSTRAINT fk_update_user
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE tasks
ADD CONSTRAINT fk_task_user
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE tasks
ADD CONSTRAINT fk_task_project
FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL;

ALTER TABLE habits
ADD CONSTRAINT fk_habit_user
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE habit_logs
ADD CONSTRAINT fk_log_habit
FOREIGN KEY (habit_id) REFERENCES habits(habit_id) ON DELETE CASCADE;

ALTER TABLE habit_logs
ADD CONSTRAINT fk_log_user
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE scheduled_notifications
ADD CONSTRAINT fk_notif_user
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE learnings
ADD CONSTRAINT fk_learning_user
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;
```

---

## Maintenance

### Backup Commands

```bash
# Full database backup
pg_dump -h localhost -U user -d alfred_db > backup_$(date +%Y%m%d).sql

# Backup specific tables
pg_dump -h localhost -U user -d alfred_db -t users -t projects -t tasks > core_backup.sql

# Compressed backup
pg_dump -h localhost -U user -d alfred_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore Commands

```bash
# Restore full database
psql -h localhost -U user -d alfred_db < backup_20250101.sql

# Restore from compressed
gunzip -c backup_20250101.sql.gz | psql -h localhost -U user -d alfred_db
```

### Maintenance Queries

```sql
-- Clean old chat history (older than 90 days)
DELETE FROM chat_history
WHERE created_at < CURRENT_DATE - INTERVAL '90 days';

-- Clean sent notifications (older than 30 days)
DELETE FROM scheduled_notifications
WHERE status IN ('sent', 'read', 'dismissed')
  AND sent_at < CURRENT_DATE - INTERVAL '30 days';

-- Vacuum and analyze tables
VACUUM ANALYZE users;
VACUUM ANALYZE chat_history;
VACUUM ANALYZE tasks;
VACUUM ANALYZE habits;

-- Check table sizes
SELECT
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- Check index usage
SELECT
    indexrelname as index_name,
    idx_scan as times_used,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Health Check Queries

```sql
-- Check for orphaned records
SELECT 'orphaned_tasks' as issue, COUNT(*) as count
FROM tasks t
LEFT JOIN users u ON t.user_id = u.user_id
WHERE u.user_id IS NULL
UNION ALL
SELECT 'orphaned_habits' as issue, COUNT(*) as count
FROM habits h
LEFT JOIN users u ON h.user_id = u.user_id
WHERE u.user_id IS NULL
UNION ALL
SELECT 'orphaned_logs' as issue, COUNT(*) as count
FROM habit_logs hl
LEFT JOIN habits h ON hl.habit_id = h.habit_id
WHERE h.habit_id IS NULL;

-- Check data integrity
SELECT
    'broken_streaks' as issue,
    COUNT(*) as count
FROM habits h
WHERE h.current_streak > 0
  AND h.last_logged < CURRENT_DATE - INTERVAL '1 day';
```

---

*Database schema documentation for Alfred - The Digital Butler*
