# Database Schema

Alfred uses PostgreSQL for persistent storage of all user data, projects, tasks, habits, and conversation history.

## Tables Overview

| Table | Purpose |
|-------|---------|
| `users` | User accounts and profiles |
| `chat_history` | Conversation messages |
| `user_preferences` | Learned user preferences |
| `projects` | Project tracking |
| `project_updates` | Daily project logs |
| `tasks` | Task management |
| `habits` | Habit tracking |
| `habit_logs` | Habit completion records |
| `scheduled_notifications` | Proactive notifications |
| `learnings` | Knowledge/learnings storage |

---

## Table Definitions

### 1. users
Stores authentication and profile data.

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | `VARCHAR(255)` | Primary Key |
| `email` | `VARCHAR(255)` | Unique email |
| `password_hash` | `TEXT` | Bcrypt hashed password |
| `profile` | `JSONB` | User profile settings |
| `created_at` | `TIMESTAMP` | Creation time |

**Profile JSONB Structure:**
```json
{
  "bio": "COO of Codesstellar...",
  "work_type": "Operations",
  "voice_id": "british_butler",
  "personality_prompt": "Witty Butler",
  "interaction_type": "formal",
  "morning_briefing_time": "08:00",
  "evening_review_time": "18:00",
  "proactivity_level": "medium",
  "reminder_style": "gentle"
}
```

---

### 2. projects
Stores project information.

| Column | Type | Description |
|--------|------|-------------|
| `project_id` | `VARCHAR(255)` | Primary Key (UUID) |
| `user_id` | `VARCHAR(255)` | Owner |
| `name` | `VARCHAR(255)` | Project name |
| `organization` | `VARCHAR(255)` | Organization/company |
| `role` | `VARCHAR(50)` | User's role (founder, coo, pm, etc.) |
| `status` | `VARCHAR(50)` | active, on_hold, completed, archived |
| `description` | `TEXT` | Project description |
| `integrations` | `JSONB` | External tool links |
| `metadata` | `JSONB` | Additional metadata |
| `created_at` | `TIMESTAMP` | Creation time |
| `updated_at` | `TIMESTAMP` | Last update time |

**Indexes:**
- `idx_projects_user_id` on `user_id`
- `idx_projects_status` on `status`

---

### 3. project_updates
Daily logs/updates for projects.

| Column | Type | Description |
|--------|------|-------------|
| `update_id` | `VARCHAR(255)` | Primary Key (UUID) |
| `project_id` | `VARCHAR(255)` | Project reference |
| `user_id` | `VARCHAR(255)` | Author |
| `content` | `TEXT` | Update content |
| `update_type` | `VARCHAR(50)` | progress, blocker, decision, note, milestone |
| `action_items` | `JSONB` | Extracted action items |
| `blockers` | `JSONB` | Identified blockers |
| `created_at` | `TIMESTAMP` | Creation time |

**Indexes:**
- `idx_updates_project` on `project_id`

---

### 4. tasks
Task management.

| Column | Type | Description |
|--------|------|-------------|
| `task_id` | `VARCHAR(255)` | Primary Key (UUID) |
| `user_id` | `VARCHAR(255)` | Owner |
| `project_id` | `VARCHAR(255)` | Project (nullable for personal tasks) |
| `title` | `TEXT` | Task title |
| `description` | `TEXT` | Task description |
| `priority` | `VARCHAR(20)` | high, medium, low |
| `status` | `VARCHAR(20)` | pending, in_progress, blocked, completed, cancelled |
| `due_date` | `TIMESTAMP` | Due date/time |
| `recurrence` | `VARCHAR(50)` | Recurrence pattern |
| `blockers` | `JSONB` | List of blockers |
| `tags` | `JSONB` | Tags array |
| `source` | `VARCHAR(50)` | user, alfred, integration |
| `source_ref` | `VARCHAR(255)` | External reference ID |
| `created_at` | `TIMESTAMP` | Creation time |
| `updated_at` | `TIMESTAMP` | Last update time |
| `completed_at` | `TIMESTAMP` | Completion time |

**Indexes:**
- `idx_tasks_user_id` on `user_id`
- `idx_tasks_project` on `project_id`
- `idx_tasks_status` on `status`
- `idx_tasks_due_date` on `due_date`

---

### 5. habits
Habit tracking.

| Column | Type | Description |
|--------|------|-------------|
| `habit_id` | `VARCHAR(255)` | Primary Key (UUID) |
| `user_id` | `VARCHAR(255)` | Owner |
| `name` | `VARCHAR(255)` | Habit name |
| `description` | `TEXT` | Description |
| `frequency` | `VARCHAR(50)` | daily, weekly, weekdays, custom |
| `time_preference` | `VARCHAR(10)` | Preferred time (HH:MM) |
| `days_of_week` | `JSONB` | Days for custom frequency |
| `current_streak` | `INT` | Current streak count |
| `best_streak` | `INT` | Best streak achieved |
| `total_completions` | `INT` | Total times completed |
| `last_logged` | `DATE` | Last completion date |
| `motivation` | `TEXT` | Why this habit matters |
| `category` | `VARCHAR(50)` | fitness, productivity, learning, etc. |
| `active` | `BOOLEAN` | Is habit active |
| `reminder_enabled` | `BOOLEAN` | Send reminders |
| `created_at` | `TIMESTAMP` | Creation time |

**Indexes:**
- `idx_habits_user_id` on `user_id`

---

### 6. habit_logs
Individual habit completion records.

| Column | Type | Description |
|--------|------|-------------|
| `log_id` | `VARCHAR(255)` | Primary Key (UUID) |
| `habit_id` | `VARCHAR(255)` | Habit reference |
| `user_id` | `VARCHAR(255)` | Owner |
| `logged_date` | `DATE` | Completion date |
| `notes` | `TEXT` | Optional notes |
| `duration_minutes` | `INT` | Duration (for timed habits) |
| `created_at` | `TIMESTAMP` | Log creation time |

**Constraints:**
- `UNIQUE(habit_id, logged_date)` - One log per day per habit

**Indexes:**
- `idx_habit_logs_habit` on `habit_id`

---

### 7. chat_history
Conversation messages.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `SERIAL` | Primary Key |
| `user_id` | `VARCHAR(255)` | Owner |
| `role` | `VARCHAR(50)` | user, assistant, system |
| `content` | `TEXT` | Message content |
| `metadata` | `JSONB` | Additional metadata |
| `created_at` | `TIMESTAMP` | Message time |

**Indexes:**
- `idx_chat_user_id` on `user_id`

---

### 8. user_preferences
Learned user preferences (key-value).

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | `VARCHAR(255)` | Owner (PK part) |
| `key` | `VARCHAR(255)` | Preference key (PK part) |
| `value` | `TEXT` | Preference value |
| `confidence` | `FLOAT` | Confidence level (0-1) |
| `learned_at` | `TIMESTAMP` | When learned |

**Primary Key:** `(user_id, key)`

---

### 9. scheduled_notifications
Proactive notifications queue.

| Column | Type | Description |
|--------|------|-------------|
| `notification_id` | `VARCHAR(255)` | Primary Key (UUID) |
| `user_id` | `VARCHAR(255)` | Target user |
| `notification_type` | `VARCHAR(50)` | Type (morning_briefing, habit_reminder, etc.) |
| `title` | `TEXT` | Notification title |
| `content` | `TEXT` | Notification content |
| `trigger_time` | `TIMESTAMP` | When to send |
| `context` | `JSONB` | Additional context |
| `status` | `VARCHAR(20)` | pending, sent, read, dismissed |
| `sent_at` | `TIMESTAMP` | When sent |
| `created_at` | `TIMESTAMP` | Creation time |

**Indexes:**
- `idx_notifications_user` on `user_id`
- `idx_notifications_trigger` on `trigger_time`
- `idx_notifications_status` on `status`

---

### 10. learnings
Knowledge and learnings storage.

| Column | Type | Description |
|--------|------|-------------|
| `learning_id` | `VARCHAR(255)` | Primary Key (UUID) |
| `user_id` | `VARCHAR(255)` | Owner |
| `topic` | `VARCHAR(255)` | Topic category |
| `content` | `TEXT` | Learning content |
| `original_query` | `TEXT` | Original user query |
| `created_at` | `TIMESTAMP` | Creation time |

**Indexes:**
- `idx_learnings_user` on `user_id`

---

## Entity Relationships

```
users
  │
  ├── projects (1:N)
  │     └── project_updates (1:N)
  │     └── tasks (1:N)
  │
  ├── tasks (1:N) [personal tasks without project]
  │
  ├── habits (1:N)
  │     └── habit_logs (1:N)
  │
  ├── chat_history (1:N)
  │
  ├── user_preferences (1:N)
  │
  ├── scheduled_notifications (1:N)
  │
  └── learnings (1:N)
```

---

## Enums Reference

### Project Role
- `founder` - Founder/Owner
- `coo` - Chief Operating Officer
- `pm` - Project Manager
- `developer` - Developer
- `contributor` - General Contributor

### Project Status
- `active` - Currently active
- `on_hold` - Temporarily paused
- `completed` - Successfully finished
- `archived` - Archived/deleted

### Task Priority
- `high` - High priority
- `medium` - Medium priority
- `low` - Low priority

### Task Status
- `pending` - Not started
- `in_progress` - Currently working on
- `blocked` - Blocked by something
- `completed` - Done
- `cancelled` - Cancelled

### Habit Frequency
- `daily` - Every day
- `weekly` - Once a week
- `weekdays` - Monday to Friday
- `custom` - Custom days

### Update Type
- `progress` - Progress update
- `blocker` - Blocker identified
- `decision` - Decision made
- `note` - General note
- `milestone` - Milestone reached

### Notification Type
- `morning_briefing` - Morning briefing
- `evening_review` - Evening review
- `habit_reminder` - Habit reminder
- `task_due` - Task due reminder
- `project_update` - Project needs update
- `proactive_nudge` - General proactive nudge
