# Alfred - The Digital Butler
## Complete Product Specification

---

## 1. Vision & Mission

### Vision
To provide a digital personal assistant that **proactively** helps users manage their time, habits, and tasks while maintaining the persona of a professional, polite, and slightly witty butler.

### Mission
To move from a static, rule-based script to an **Agentic AI system** that uses long-term memory and external tools to solve complex problems like a real personal assistant.

### Core Differentiator
Unlike ChatGPT, Gemini, or Claude which are **passive chat assistants** (user asks, AI answers), Alfred is a **proactive agent** that:
- Initiates conversations
- Sends reminders and nudges
- Asks for updates
- Tracks state across projects and time
- Builds understanding of the user over time
- Acts on behalf of the user with connected tools

---

## 2. User Persona

### Primary User: Pratap

**Roles:**
| Role | Organization | Responsibility |
|------|--------------|----------------|
| COO | Codesstellar | Managing all operations |
| Founder | Pratap.ai | Team management, vision setting |
| Founder | Civic Vigilance | Building app from scratch solo |
| Project Manager | Muay Thai Tickets | Website/app development |
| Project Manager | No Excuse | Website/app development |
| Project Manager | PlantOgram | Marketing + WordPress site |
| Project Manager | RSN | Website/app development |
| Personal | Brand Building | Tools, automations, content |

**Pain Points:**
- Managing 7+ concurrent projects across different roles
- Daily task breakdown and updates for each project
- Communicating with multiple teams
- Personal discipline (workout, video recording, writing)
- Context switching between PM, Founder, and COO mindsets

**Needs:**
- Single dashboard showing all tasks across projects
- Daily planning and review rituals
- Project-specific update tracking
- Habit tracking with streaks
- Proactive reminders without manual setup
- Learning assistant that adapts to patterns

---

## 3. Core Features

### 3.1 Proactive Daily Rituals

#### Morning Briefing (Automated)
```
Alfred: "Good morning, Sir. Here's your day at a glance:

📋 TODAY'S PRIORITIES:
1. [No Excuse] Client demo at 2 PM - slides need review
2. [PlantOgram] WordPress update due to client
3. [Personal] Day 5 of workout streak at risk

📬 OVERNIGHT UPDATES:
- 3 emails requiring response
- Notion update from Muay Thai team
- Trello card moved to review in RSN

Shall I walk through each, or would you prefer to start with the most urgent?"
```

#### Throughout Day
- Contextual nudges based on calendar
- "Sir, the No Excuse demo is in 30 minutes. Shall I pull up the latest notes?"
- Proactive check-ins: "It's been 4 hours since PlantOgram update was due. Shall I draft a message?"

#### Evening Review (Automated)
```
Alfred: "Good evening, Sir. Let's review the day:

✅ COMPLETED:
- [No Excuse] Client demo - successful
- [Personal] Workout logged - streak: 5 days

⏳ CARRIED FORWARD:
- [PlantOgram] WordPress update - moved to tomorrow
- [Pratap.ai] Team vision doc - in progress

📊 PROJECT HEALTH:
- Muay Thai Tickets: On track
- No Excuse: Ahead of schedule
- PlantOgram: Needs attention (2 overdue items)

Anything to add before I update the records?"
```

### 3.2 Project Management

#### Project Structure
```
Project
├── name: "No Excuse"
├── role: "Project Manager"
├── organization: "Codesstellar"
├── status: "Active"
├── team: ["Dev1", "Designer", "Client"]
├── integrations: ["Trello:board_id", "Slack:channel"]
├── tasks: [...]
├── updates: [...]  // Daily log
├── decisions: [...] // Key decisions made
└── context: {...}  // Learned project knowledge
```

#### Features:
- Add/update projects via conversation
- Track tasks per project
- Log daily updates (Alfred asks, user responds)
- View project health dashboard
- Role-aware context (PM vs Founder behavior)

### 3.3 Task Management

#### Task Properties
```
Task
├── id
├── title
├── project_id (optional - can be personal)
├── priority: "high" | "medium" | "low"
├── status: "pending" | "in_progress" | "blocked" | "completed"
├── due_date
├── recurrence: "daily" | "weekly" | null
├── context: {} // Why this matters
├── blockers: []
└── created_from: "user" | "alfred" | "integration"
```

#### Intelligent Task Handling:
- Alfred can create tasks from conversation
- "I need to send the proposal to client" → Creates task
- Automatic priority suggestion based on deadlines
- Blocker detection: "What's stopping this from completing?"

### 3.4 Habit Tracking

#### Habit Structure
```
Habit
├── name: "Daily Workout"
├── frequency: "daily"
├── time_preference: "morning"
├── current_streak: 5
├── best_streak: 12
├── last_logged: "2024-12-25"
├── reminders: true
└── motivation: "Building discipline for long-term health"
```

#### Features:
- Alfred proactively asks about habits at preferred times
- Streak tracking with celebration at milestones
- Recovery encouragement if streak breaks
- Pattern detection: "Sir, you tend to skip workouts on Mondays. Shall we adjust?"

### 3.5 Integration Hub

#### Supported Integrations (via MCP)
| Integration | Purpose | Data Extracted |
|-------------|---------|----------------|
| Gmail | Email context | Unread count, important emails, action items |
| Google Calendar | Schedule awareness | Today's events, conflicts, free slots |
| Notion | Documentation | Page updates, database entries |
| Trello | Task boards | Card movements, assignments |
| Slack | Team communication | Mentions, DMs, channel activity |
| GitHub | Code context | PRs, issues, commits |

#### How Integrations Work:
1. User connects integration (OAuth)
2. Alfred periodically syncs data via MCP tools
3. Information feeds into daily briefings
4. Can query: "Any updates from the Muay Thai Trello board?"

### 3.6 Knowledge Graph & Memory

#### Memory Tiers

```
┌─────────────────────────────────────────────────────────────┐
│                    WORKING MEMORY                           │
│  Current conversation context, active task, immediate goal  │
│  (In-context, refreshed each session)                       │
├─────────────────────────────────────────────────────────────┤
│                   SHORT-TERM MEMORY                         │
│  Recent interactions, today's updates, pending items        │
│  (PostgreSQL, 7-day rolling window)                         │
├─────────────────────────────────────────────────────────────┤
│                    LONG-TERM MEMORY                         │
│  User preferences, project knowledge, learned patterns      │
│  (Knowledge Graph + Vector DB)                              │
└─────────────────────────────────────────────────────────────┘
```

#### Knowledge Graph Structure (Neo4j)

```
Nodes:
- User (Pratap)
- Project (No Excuse, PlantOgram, ...)
- Person (Team members, clients)
- Organization (Codesstellar, Pratap.ai)
- Task
- Habit
- Preference
- Fact (learned information)
- Decision (key decisions made)
- Update (daily logs)

Relationships:
- User -[MANAGES]-> Project
- User -[HAS_ROLE]-> Organization {role: "COO"}
- Project -[BELONGS_TO]-> Organization
- Person -[WORKS_ON]-> Project
- User -[PREFERS]-> Preference
- User -[DECIDED]-> Decision {date, context}
- Task -[PART_OF]-> Project
- User -[HAS_HABIT]-> Habit
```

#### What Alfred Learns Over Time:
- Communication preferences ("User prefers bullet points")
- Work patterns ("Most productive between 9-11 AM")
- Project rhythms ("PlantOgram client expects weekly updates")
- Relationships ("Dev1 is reliable, Designer needs follow-up")
- Decision history ("Last time this happened, user chose X")

### 3.7 Personalization & Tuning

#### User-Controllable Settings
```
PersonalitySettings:
├── tone: "formal" | "casual" | "witty"
├── verbosity: "concise" | "detailed"
├── proactivity: "high" | "medium" | "low"
├── humor_level: 0-10
├── butler_mode: true | false
└── custom_prompt: "..." // Override personality

NotificationSettings:
├── morning_briefing_time: "08:00"
├── evening_review_time: "18:00"
├── reminder_frequency: "gentle" | "persistent"
├── quiet_hours: ["22:00", "07:00"]
└── channels: ["push", "email", "in_app"]

FocusAreas:
├── work_life_balance: true
├── fitness_tracking: true
├── content_creation: true
├── project_management: true
└── custom_areas: [...]
```

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ALFRED SYSTEM                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │   MOBILE APP     │  │    WEB APP       │  │  NOTIFICATION    │   │
│  │  (React Native)  │  │   (React/Vite)   │  │    SERVICE       │   │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘   │
│           │                     │                     │              │
│           └─────────────────────┼─────────────────────┘              │
│                                 │                                    │
│                    ┌────────────▼────────────┐                       │
│                    │       API GATEWAY       │                       │
│                    │       (FastAPI)         │                       │
│                    └────────────┬────────────┘                       │
│                                 │                                    │
│  ┌──────────────────────────────┼──────────────────────────────────┐ │
│  │                    CORE DOMAIN LAYER                            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │ │
│  │  │   ALFRED    │  │  PROACTIVE  │  │   MEMORY    │              │ │
│  │  │   BUTLER    │  │   ENGINE    │  │   MANAGER   │              │ │
│  │  │  (Agno AI)  │  │ (Scheduler) │  │ (KG + Vec)  │              │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │ │
│  └──────────────────────────────┼──────────────────────────────────┘ │
│                                 │                                    │
│  ┌──────────────────────────────┼──────────────────────────────────┐ │
│  │                   INFRASTRUCTURE LAYER                          │ │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │ │
│  │  │OpenAI  │ │Postgres│ │ Neo4j  │ │ Qdrant │ │  MCP   │        │ │
│  │  │ LLM    │ │  SQL   │ │   KG   │ │ Vector │ │ Tools  │        │ │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    EXTERNAL INTEGRATIONS                        │ │
│  │    Gmail │ Calendar │ Notion │ Trello │ Slack │ GitHub          │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Core Components

#### A. Alfred Butler (Agno Agent)
The conversational AI core that:
- Processes user messages
- Maintains persona (butler character)
- Orchestrates tool calls
- Generates responses
- Learns from interactions

#### B. Proactive Engine
Background service that:
- Runs on schedule (cron-based)
- Checks triggers and conditions
- Generates proactive messages
- Manages notification delivery
- Tracks engagement patterns

```python
class ProactiveEngine:
    def __init__(self, user_id: str):
        self.scheduler = APScheduler()
        self.triggers = TriggerManager()

    async def run_morning_briefing(self):
        # Gather context from all sources
        tasks = await self.get_pending_tasks()
        calendar = await self.get_today_events()
        emails = await self.get_important_emails()
        habits = await self.get_habit_status()

        # Generate briefing via Alfred
        briefing = await alfred.generate_briefing(
            tasks, calendar, emails, habits
        )

        # Send notification
        await self.notify(briefing)

    async def check_triggers(self):
        # Periodic check for proactive nudges
        overdue = await self.get_overdue_items()
        upcoming = await self.get_upcoming_deadlines()
        patterns = await self.detect_patterns()

        for trigger in [overdue, upcoming, patterns]:
            if trigger.should_notify():
                await self.notify(trigger.message)
```

#### C. Memory Manager
Handles all memory operations:
- Short-term: PostgreSQL for recent data
- Long-term: Neo4j knowledge graph + Qdrant vectors
- Consolidation: Periodic migration from short to long-term

```python
class MemoryManager:
    def __init__(self):
        self.postgres = PostgresStorage()
        self.neo4j = Neo4jKnowledgeGraph()
        self.qdrant = QdrantVectorDB()

    async def remember(self, fact: Fact, importance: str):
        if importance == "immediate":
            await self.postgres.store(fact)
        elif importance == "permanent":
            await self.neo4j.add_node(fact)
            embedding = await self.embed(fact.content)
            await self.qdrant.upsert(fact.id, embedding)

    async def recall(self, query: str, context: dict) -> List[Memory]:
        # Semantic search in vector DB
        similar = await self.qdrant.search(query)

        # Graph traversal for relationships
        related = await self.neo4j.query_related(context)

        # Recent items from SQL
        recent = await self.postgres.get_recent(context['user_id'])

        return self.rank_and_merge(similar, related, recent)

    async def consolidate(self):
        # Nightly job: move important short-term to long-term
        important = await self.postgres.get_important_last_24h()
        for item in important:
            await self.neo4j.add_node(item)
```

### 4.3 Database Schema (Extended)

#### PostgreSQL Tables

```sql
-- Core User Data
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Projects
CREATE TABLE projects (
    project_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    name VARCHAR(255) NOT NULL,
    organization VARCHAR(255),
    role VARCHAR(50), -- 'founder', 'pm', 'coo'
    status VARCHAR(20) DEFAULT 'active',
    integrations JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tasks
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    project_id UUID REFERENCES projects(project_id),
    title TEXT NOT NULL,
    description TEXT,
    priority VARCHAR(10) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'pending',
    due_date TIMESTAMP,
    recurrence VARCHAR(20),
    blockers JSONB DEFAULT '[]',
    source VARCHAR(50) DEFAULT 'user', -- 'user', 'alfred', 'integration'
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Project Updates (Daily Log)
CREATE TABLE project_updates (
    update_id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(project_id),
    user_id UUID REFERENCES users(user_id),
    content TEXT NOT NULL,
    update_type VARCHAR(50), -- 'progress', 'blocker', 'decision', 'note'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Habits
CREATE TABLE habits (
    habit_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    name VARCHAR(255) NOT NULL,
    frequency VARCHAR(20) DEFAULT 'daily',
    time_preference TIME,
    current_streak INT DEFAULT 0,
    best_streak INT DEFAULT 0,
    last_logged DATE,
    motivation TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Habit Logs
CREATE TABLE habit_logs (
    log_id UUID PRIMARY KEY,
    habit_id UUID REFERENCES habits(habit_id),
    logged_at DATE NOT NULL,
    notes TEXT,
    UNIQUE(habit_id, logged_at)
);

-- Chat History (Short-term)
CREATE TABLE chat_history (
    message_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scheduled Notifications
CREATE TABLE scheduled_notifications (
    notification_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    trigger_type VARCHAR(50), -- 'morning_briefing', 'habit_reminder', 'task_due'
    trigger_time TIMESTAMP NOT NULL,
    content TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- User Preferences (Key-Value)
CREATE TABLE user_preferences (
    user_id UUID REFERENCES users(user_id),
    key VARCHAR(255) NOT NULL,
    value TEXT,
    learned_at TIMESTAMP DEFAULT NOW(),
    confidence FLOAT DEFAULT 1.0,
    PRIMARY KEY (user_id, key)
);

-- Integration Tokens
CREATE TABLE integrations (
    integration_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    provider VARCHAR(50) NOT NULL, -- 'gmail', 'notion', 'trello'
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    settings JSONB DEFAULT '{}',
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Neo4j Knowledge Graph Schema

```cypher
// Node Types
(:User {id, name, email})
(:Project {id, name, status})
(:Organization {id, name})
(:Person {id, name, relationship}) // Team members, clients
(:Task {id, title, status})
(:Habit {id, name, streak})
(:Preference {key, value, confidence})
(:Fact {id, content, category, source})
(:Decision {id, description, date, outcome})
(:Pattern {id, description, frequency})

// Relationship Types
(:User)-[:MANAGES]->(:Project)
(:User)-[:WORKS_AT {role}]->(:Organization)
(:Project)-[:BELONGS_TO]->(:Organization)
(:Person)-[:WORKS_ON]->(:Project)
(:Person)-[:REPORTS_TO]->(:User)
(:User)-[:HAS_PREFERENCE]->(:Preference)
(:User)-[:KNOWS_FACT]->(:Fact)
(:User)-[:MADE_DECISION]->(:Decision)
(:Decision)-[:ABOUT]->(:Project)
(:User)-[:EXHIBITS_PATTERN]->(:Pattern)
(:Task)-[:PART_OF]->(:Project)
(:User)-[:HAS_HABIT]->(:Habit)
(:Fact)-[:RELATED_TO]->(:Fact)
```

---

## 5. User Flows

### 5.1 Daily Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRATAP'S DAY WITH ALFRED                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  07:30  ┌──────────────────────────────────────────────────┐    │
│    ▼    │ Push Notification: "Good morning, Sir..."       │    │
│         │ Morning briefing ready                           │    │
│         └──────────────────────────────────────────────────┘    │
│                                                                  │
│  08:00  ┌──────────────────────────────────────────────────┐    │
│    ▼    │ Opens App → Sees Dashboard                       │    │
│         │ - Today's tasks across all projects              │    │
│         │ - Priority items highlighted                     │    │
│         │ - Habit streaks visible                          │    │
│         └──────────────────────────────────────────────────┘    │
│                                                                  │
│  08:15  ┌──────────────────────────────────────────────────┐    │
│    ▼    │ Chats with Alfred:                               │    │
│         │ "What's the status on No Excuse?"                │    │
│         │ Alfred pulls project context, recent updates     │    │
│         └──────────────────────────────────────────────────┘    │
│                                                                  │
│  10:00  ┌──────────────────────────────────────────────────┐    │
│    ▼    │ Push: "Sir, the PlantOgram update is overdue.    │    │
│         │ Shall I draft a message to the client?"          │    │
│         └──────────────────────────────────────────────────┘    │
│                                                                  │
│  12:00  ┌──────────────────────────────────────────────────┐    │
│    ▼    │ Push: "Workout reminder - Day 5 of streak."      │    │
│         │ User: "Done, logged 30 min strength training"    │    │
│         │ Alfred updates habit, celebrates streak          │    │
│         └──────────────────────────────────────────────────┘    │
│                                                                  │
│  14:00  ┌──────────────────────────────────────────────────┐    │
│    ▼    │ User: "No Excuse demo went well, client happy"   │    │
│         │ Alfred: Logs update, asks follow-up questions    │    │
│         │ "Excellent! Any action items from the demo?"     │    │
│         └──────────────────────────────────────────────────┘    │
│                                                                  │
│  18:00  ┌──────────────────────────────────────────────────┐    │
│    ▼    │ Push: "Evening review ready, Sir."               │    │
│         │ Opens app → Sees day summary                     │    │
│         │ Confirms completed items, adds notes             │    │
│         └──────────────────────────────────────────────────┘    │
│                                                                  │
│  18:30  ┌──────────────────────────────────────────────────┐    │
│    ▼    │ Alfred: "I noticed RSN has had no updates in     │    │
│         │ 3 days. Everything alright with that project?"   │    │
│         │ → Proactive pattern detection                    │    │
│         └──────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Project Update Flow

```
User: "Update on Muay Thai - finished the booking flow today,
       blocked on payment gateway integration"

Alfred:
1. Parses intent → Project update for Muay Thai Tickets
2. Extracts:
   - Progress: "finished booking flow"
   - Blocker: "payment gateway integration"
3. Creates:
   - Update record in project_updates
   - Updates task status (booking flow → completed)
   - Creates new task (payment gateway) marked as blocker
4. Adds to knowledge graph:
   - (User)-[:UPDATED]->(Project) {date: today}
   - (Task:PaymentGateway)-[:BLOCKED_BY]->(:ExternalDependency)
5. Responds:
   "Noted, Sir. Booking flow marked complete. I've logged
   the payment gateway as a blocker. Would you like me to
   remind you to follow up on this in 2 days?"
```

### 5.3 Learning Flow

```
Conversation:
User: "Send me the summary in bullet points, not paragraphs"
Alfred: "Of course, Sir. I'll format summaries as bullet points going forward."

Behind the scenes:
1. Detects correction/preference signal
2. Calls save_preference("summary_format", "bullet_points")
3. Adds to Neo4j:
   (User)-[:HAS_PREFERENCE]->(:Preference {key: "summary_format", value: "bullet_points"})
4. Future summaries automatically use bullets
```

---

## 6. API Endpoints (Extended)

### Authentication
```
POST /auth/signup          # Create account
POST /auth/login           # Get JWT token
GET  /auth/profile         # Get user profile
PUT  /auth/profile         # Update profile & settings
```

### Chat
```
POST /chat                 # Send message to Alfred
GET  /chat/history         # Get conversation history
POST /chat/context         # Add context for current session
```

### Projects
```
GET    /projects                    # List all projects
POST   /projects                    # Create project
GET    /projects/{id}               # Get project details
PUT    /projects/{id}               # Update project
DELETE /projects/{id}               # Archive project
POST   /projects/{id}/updates       # Log project update
GET    /projects/{id}/updates       # Get project updates
GET    /projects/{id}/tasks         # Get project tasks
```

### Tasks
```
GET    /tasks                       # List all tasks (with filters)
POST   /tasks                       # Create task
GET    /tasks/{id}                  # Get task details
PUT    /tasks/{id}                  # Update task
DELETE /tasks/{id}                  # Delete task
POST   /tasks/{id}/complete         # Mark complete
```

### Habits
```
GET    /habits                      # List habits
POST   /habits                      # Create habit
PUT    /habits/{id}                 # Update habit
POST   /habits/{id}/log             # Log habit completion
GET    /habits/{id}/history         # Get habit history
```

### Dashboard
```
GET /dashboard/today                # Today's overview
GET /dashboard/week                 # Week view
GET /dashboard/project-health       # All project statuses
```

### Integrations
```
GET    /integrations                # List connected integrations
POST   /integrations/{provider}/connect     # OAuth connect
DELETE /integrations/{provider}/disconnect  # Disconnect
POST   /integrations/{provider}/sync        # Force sync
```

### Memory (Internal/Debug)
```
GET  /memory/preferences            # View learned preferences
GET  /memory/knowledge              # Query knowledge graph
POST /memory/forget                 # Remove specific memory
```

---

## 7. Mobile App Screens

### 7.1 Navigation Structure

```
├── Auth Stack
│   ├── Login
│   ├── Signup
│   └── Onboarding
│
└── Main Stack (Tab Navigator)
    ├── Dashboard (Home)
    │   ├── Today's Overview
    │   ├── Quick Actions
    │   └── Upcoming
    │
    ├── Chat
    │   └── Alfred Conversation
    │
    ├── Projects
    │   ├── Project List
    │   ├── Project Detail
    │   └── Project Update Form
    │
    ├── Tasks
    │   ├── Task List (filterable)
    │   ├── Task Detail
    │   └── Quick Add
    │
    ├── Habits
    │   ├── Habit List
    │   ├── Habit Detail
    │   └── Log Entry
    │
    └── Settings
        ├── Profile
        ├── Personality Settings
        ├── Notification Settings
        ├── Integrations
        └── Data & Privacy
```

### 7.2 Key Screens

#### Dashboard
```
┌─────────────────────────────────────┐
│  Good Morning, Pratap         [≡]  │
│  Thursday, December 26              │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🔥 FOCUS TODAY              │   │
│  │                              │   │
│  │ ○ No Excuse: Client call     │   │
│  │ ○ PlantOgram: Send update    │   │
│  │ ○ Workout (Day 5 streak!)    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📊 PROJECT HEALTH            │   │
│  │                              │   │
│  │ Muay Thai    ████████░░ 80%  │   │
│  │ No Excuse    ██████████ 100% │   │
│  │ PlantOgram   ████░░░░░░ 40%  │   │
│  │ RSN          ██████░░░░ 60%  │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 💪 HABITS                    │   │
│  │                              │   │
│  │ Workout     🔥 5 days        │   │
│  │ Writing     ○ Not started    │   │
│  │ Video       ○ Not started    │   │
│  └─────────────────────────────┘   │
│                                     │
├─────────────────────────────────────┤
│  [Dashboard] [Chat] [Projects] [⚙] │
└─────────────────────────────────────┘
```

#### Chat with Alfred
```
┌─────────────────────────────────────┐
│  ← Alfred                     [⋮]  │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────┐     │
│  │ Good morning, Sir. I've    │  🎩 │
│  │ prepared your briefing.    │     │
│  │                            │     │
│  │ 3 priority items today:    │     │
│  │ • No Excuse client call    │     │
│  │ • PlantOgram update due    │     │
│  │ • Workout (streak at 5)    │     │
│  └───────────────────────────┘     │
│                                     │
│       ┌───────────────────────────┐ │
│    🧑 │ What's happening with     │ │
│       │ PlantOgram?               │ │
│       └───────────────────────────┘ │
│                                     │
│  ┌───────────────────────────┐     │
│  │ PlantOgram status:         │  🎩 │
│  │                            │     │
│  │ Last update: 2 days ago    │     │
│  │ Pending: WordPress changes │     │
│  │ Blocker: Client feedback   │     │
│  │                            │     │
│  │ Shall I draft a follow-up  │     │
│  │ message to the client?     │     │
│  └───────────────────────────┘     │
│                                     │
├─────────────────────────────────────┤
│  [Type a message...]        [Send] │
└─────────────────────────────────────┘
```

---

## 8. Technical Implementation Approach

### Phase 1: Foundation (Current → Enhanced)
- [ ] Extend PostgreSQL schema for projects, tasks, habits
- [ ] Implement project and task CRUD APIs
- [ ] Build mobile dashboard screen
- [ ] Enhance Alfred with project-aware context

### Phase 2: Proactive Engine
- [ ] Set up APScheduler for background jobs
- [ ] Implement morning briefing generation
- [ ] Implement evening review generation
- [ ] Add push notification service (Firebase/Expo)
- [ ] Build notification preferences UI

### Phase 3: Knowledge Graph
- [ ] Set up Neo4j instance
- [ ] Implement knowledge graph adapter
- [ ] Build entity extraction from conversations
- [ ] Create memory consolidation job
- [ ] Integrate KG into Alfred context

### Phase 4: Integrations
- [ ] Gmail MCP server setup
- [ ] Google Calendar MCP server
- [ ] Notion MCP integration
- [ ] Trello MCP integration
- [ ] Integration sync scheduler

### Phase 5: Learning & Personalization
- [ ] Implement preference detection in conversations
- [ ] Build pattern recognition (work habits, productivity)
- [ ] Create adaptive personality system
- [ ] Add decision tracking and recall

---

## 9. Technology Stack (Final)

| Layer | Technology | Purpose |
|-------|------------|---------|
| Mobile | React Native + Expo | Cross-platform app |
| Web | React + Vite | Dashboard UI |
| API | FastAPI | REST endpoints |
| Agent | Agno + OpenAI GPT-4o | AI reasoning |
| SQL DB | PostgreSQL | Structured data |
| Graph DB | Neo4j | Knowledge graph |
| Vector DB | Qdrant | Semantic search |
| Scheduler | APScheduler | Background jobs |
| Push | Firebase/Expo Notifications | Proactive alerts |
| Tools | MCP Protocol | External integrations |
| Auth | JWT + bcrypt | Security |
| Hosting | TBD (Railway/Render/AWS) | Deployment |

---

## 10. Success Metrics

| Metric | Target |
|--------|--------|
| Daily active usage | User opens app daily |
| Proactive engagement | 80% of briefings read |
| Task completion rate | Improvement over baseline |
| Habit streak average | Increasing trend |
| Project update frequency | Daily updates logged |
| Learning accuracy | 90% preference recall |
| Response relevance | User satisfaction score |

---

## Appendix: Pratap's Projects Reference

| Project | Organization | Role | Key Activities |
|---------|--------------|------|----------------|
| Muay Thai Tickets | Codesstellar | PM | Website/app dev, client mgmt |
| No Excuse | Codesstellar | PM | Website/app dev, client mgmt |
| PlantOgram | Codesstellar | PM | Marketing, WordPress |
| RSN | Codesstellar | PM | Website/app dev |
| Codesstellar | Codesstellar | COO | Operations management |
| Pratap.ai | Pratap.ai | Founder | Team, vision, strategy |
| Civic Vigilance | Personal | Founder | Solo development |
| Personal Brand | Personal | Creator | Tools, automation, content |
