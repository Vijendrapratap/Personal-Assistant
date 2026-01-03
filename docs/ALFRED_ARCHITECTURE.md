# Alfred Technical Architecture
## From Current State to Minimal, Goal-Oriented PA

---

## 1. Current State Analysis

### What's Built (60-65% Complete)

| Layer | Status | Notes |
|-------|--------|-------|
| **Backend API** | ✅ Solid | FastAPI, PostgreSQL, JWT auth |
| **Core Domain** | ✅ Complete | Entities, interfaces, clean architecture |
| **Database** | ✅ Complete | Full schema with indexes |
| **LLM Integration** | ✅ Working | OpenAI + Ollama fallback |
| **Mobile App** | ⚠️ Basic | React Native, functional but dated UI |
| **Proactive Engine** | ⚠️ Scaffolded | Code exists, not running |
| **Knowledge Graph** | ⚠️ Scaffolded | Neo4j code exists, not integrated |
| **Voice** | ❌ Missing | Only voice_id in profile |
| **Integrations** | ❌ Missing | No calendar/email sync |

### What Needs Redesign

1. **Mobile UI** - Complete redesign to match minimal design system
2. **Navigation** - From 5 tabs to 4 focused screens
3. **Conversation UX** - From chat screen to universal input
4. **Proactive Layer** - From passive to initiating

---

## 2. Target Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         MOBILE APP                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │  Today   │ │    Do    │ │  Focus   │ │   You    │            │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │
│       │            │            │            │                    │
│       └────────────┴────────────┴────────────┘                    │
│                         │                                         │
│                  ┌──────┴──────┐                                  │
│                  │ Alfred SDK  │  (unified client layer)          │
│                  │ • API calls │                                  │
│                  │ • Caching   │                                  │
│                  │ • Offline   │                                  │
│                  │ • Push      │                                  │
│                  └──────┬──────┘                                  │
└─────────────────────────┼────────────────────────────────────────┘
                          │
                    HTTPS/WSS
                          │
┌─────────────────────────┼────────────────────────────────────────┐
│                    BACKEND API                                    │
│  ┌──────────────────────┴─────────────────────────┐              │
│  │                   FastAPI                       │              │
│  │  /chat  /tasks  /habits  /projects  /dashboard  │              │
│  └──────────────────────┬─────────────────────────┘              │
│                         │                                         │
│  ┌──────────────────────┼─────────────────────────┐              │
│  │              CORE DOMAIN                        │              │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐          │              │
│  │  │ Alfred  │ │Proactive│ │ Memory  │          │              │
│  │  │ Brain   │ │ Engine  │ │ Manager │          │              │
│  │  └────┬────┘ └────┬────┘ └────┬────┘          │              │
│  │       └───────────┼───────────┘                │              │
│  └───────────────────┼────────────────────────────┘              │
│                      │                                            │
│  ┌───────────────────┼────────────────────────────┐              │
│  │           INFRASTRUCTURE                        │              │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │              │
│  │  │Postgres│ │  Neo4j │ │ Qdrant │ │  Redis │  │              │
│  │  │  Data  │ │ Graph  │ │ Vector │ │ Queue  │  │              │
│  │  └────────┘ └────────┘ └────────┘ └────────┘  │              │
│  │                                                 │              │
│  │  ┌────────┐ ┌────────┐ ┌────────┐             │              │
│  │  │ OpenAI │ │ Whisper│ │  Expo  │             │              │
│  │  │  LLM   │ │  STT   │ │  Push  │             │              │
│  │  └────────┘ └────────┘ └────────┘             │              │
│  └─────────────────────────────────────────────────┘              │
│                                                                    │
│  ┌─────────────────────────────────────────────────┐              │
│  │              BACKGROUND WORKERS                  │              │
│  │  • Morning Briefing Generator (scheduled)       │              │
│  │  • Evening Review Trigger (scheduled)           │              │
│  │  • Habit Reminder Sender (cron)                 │              │
│  │  • Proactive Nudge Engine (event-based)         │              │
│  │  • Pattern Detector (daily batch)               │              │
│  └─────────────────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Mobile App Architecture

### 3.1 New Screen Structure

```
mobile/
├── src/
│   ├── app/                    # Expo Router app directory
│   │   ├── (auth)/             # Auth screens
│   │   │   ├── login.tsx
│   │   │   ├── signup.tsx
│   │   │   └── onboarding.tsx
│   │   ├── (tabs)/             # Main tab navigation
│   │   │   ├── _layout.tsx     # Tab bar configuration
│   │   │   ├── today.tsx       # Today/Briefing screen
│   │   │   ├── do.tsx          # Tasks + Habits
│   │   │   ├── focus.tsx       # Calendar + Voice
│   │   │   └── you.tsx         # Profile + Memory
│   │   ├── (modals)/           # Modal screens
│   │   │   ├── voice.tsx       # Full-screen voice UI
│   │   │   ├── evening.tsx     # Evening review
│   │   │   └── project/[id].tsx
│   │   ├── _layout.tsx         # Root layout
│   │   └── index.tsx           # Entry point
│   │
│   ├── components/
│   │   ├── alfred/             # Alfred-specific components
│   │   │   ├── AlfredAvatar.tsx
│   │   │   ├── TransparencyPanel.tsx
│   │   │   ├── ProactiveCard.tsx
│   │   │   └── GreetingHeader.tsx
│   │   ├── input/
│   │   │   ├── ConversationInput.tsx
│   │   │   └── VoiceButton.tsx
│   │   ├── tasks/
│   │   │   ├── TaskCard.tsx
│   │   │   └── TaskList.tsx
│   │   ├── habits/
│   │   │   ├── HabitChip.tsx
│   │   │   ├── StreakBadge.tsx
│   │   │   └── HabitRow.tsx
│   │   ├── calendar/
│   │   │   ├── DayStrip.tsx
│   │   │   ├── EventCard.tsx
│   │   │   └── TimelineView.tsx
│   │   └── common/
│   │       ├── Card.tsx
│   │       ├── Button.tsx
│   │       ├── Badge.tsx
│   │       └── EmptyState.tsx
│   │
│   ├── lib/
│   │   ├── alfred-sdk/         # API client layer
│   │   │   ├── client.ts       # Axios instance
│   │   │   ├── auth.ts
│   │   │   ├── tasks.ts
│   │   │   ├── habits.ts
│   │   │   ├── projects.ts
│   │   │   ├── chat.ts
│   │   │   └── dashboard.ts
│   │   ├── hooks/              # React hooks
│   │   │   ├── useAlfred.ts    # Main Alfred hook
│   │   │   ├── useTasks.ts
│   │   │   ├── useHabits.ts
│   │   │   ├── useBriefing.ts
│   │   │   └── useVoice.ts
│   │   └── store/              # State management
│   │       ├── auth.ts
│   │       └── preferences.ts
│   │
│   ├── theme/
│   │   ├── tokens.ts           # Design tokens
│   │   ├── colors.ts
│   │   └── typography.ts
│   │
│   └── utils/
│       ├── date.ts
│       └── formatters.ts
│
├── app.json
├── package.json
└── tsconfig.json
```

### 3.2 Key Component Specifications

#### AlfredAvatar
```tsx
interface AlfredAvatarProps {
  state: 'idle' | 'listening' | 'thinking' | 'speaking' | 'working';
  size: 'sm' | 'md' | 'lg';
  showGlow?: boolean;
  progress?: number; // For 'working' state
}

// Size mapping
// sm: 32px - inline use
// md: 48px - cards, headers
// lg: 96px - voice screen, onboarding
```

#### ConversationInput
```tsx
interface ConversationInputProps {
  placeholder: string;
  onSubmit: (message: string) => void;
  onVoiceStart?: () => void;
  onVoiceEnd?: (transcript: string) => void;
  suggestions?: string[];
  disabled?: boolean;
  autoFocus?: boolean;
}
```

#### TransparencyPanel
```tsx
interface Step {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'complete' | 'error';
  detail?: string;
}

interface TransparencyPanelProps {
  steps: Step[];
  title?: string;
  onCancel?: () => void;
}
```

### 3.3 State Management

Using Zustand for lightweight state:

```tsx
// stores/alfredStore.ts
interface AlfredStore {
  // User
  user: User | null;
  setUser: (user: User) => void;

  // Briefing
  briefing: Briefing | null;
  loadBriefing: () => Promise<void>;

  // Tasks
  tasks: Task[];
  loadTasks: () => Promise<void>;
  completeTask: (id: string) => Promise<void>;

  // Habits
  habits: Habit[];
  loadHabits: () => Promise<void>;
  logHabit: (id: string) => Promise<void>;

  // Alfred State
  alfredState: 'idle' | 'listening' | 'thinking' | 'speaking';
  setAlfredState: (state: AlfredState) => void;

  // Proactive
  proactiveCards: ProactiveCard[];
  dismissCard: (id: string) => void;
}
```

---

## 4. Backend Enhancements

### 4.1 New Endpoints Needed

```python
# Transparency/Streaming
POST /chat/stream          # SSE stream for real-time thinking
GET  /chat/thinking/{id}   # Get thinking steps for a response

# Proactive
GET  /proactive/cards      # Get pending proactive suggestions
POST /proactive/dismiss    # Dismiss a card
POST /proactive/snooze     # Snooze a card

# Voice
POST /voice/transcribe     # Whisper STT
POST /voice/synthesize     # TTS (optional)

# Knowledge
GET  /knowledge/entities   # List all entities (people, companies)
GET  /knowledge/entity/{id}# Get entity details
GET  /knowledge/search     # Semantic search

# Integrations (Phase 2)
POST /integrations/google/connect
GET  /integrations/google/calendar
POST /integrations/google/disconnect
```

### 4.2 Proactive Engine Implementation

```python
# alfred/services/proactive_engine.py

class ProactiveEngine:
    """
    Generates proactive suggestions based on:
    - Time-based triggers (morning, evening, deadlines)
    - Pattern-based triggers (stale projects, broken streaks)
    - Contextual triggers (pre-meeting prep, follow-ups)
    """

    async def generate_cards(self, user_id: str) -> List[ProactiveCard]:
        cards = []

        # Check stale projects
        stale_projects = await self._get_stale_projects(user_id)
        for project in stale_projects:
            cards.append(ProactiveCard(
                type="warning",
                title=f"{project.name} - No update in {project.days_stale}d",
                description="Everything okay with this project?",
                actions=["Update", "Pause", "Dismiss"],
                entity_id=project.id,
                entity_type="project"
            ))

        # Check streak at risk
        at_risk_habits = await self._get_streaks_at_risk(user_id)
        for habit in at_risk_habits:
            cards.append(ProactiveCard(
                type="reminder",
                title=f"{habit.name} not logged today",
                description=f"Your streak is at {habit.current_streak} days",
                actions=["Log Now", "Skip Today"],
                entity_id=habit.id,
                entity_type="habit"
            ))

        # Check upcoming meetings needing prep
        upcoming = await self._get_meetings_needing_prep(user_id)
        for meeting in upcoming:
            cards.append(ProactiveCard(
                type="insight",
                title=f"{meeting.title} in {meeting.hours_until}h",
                description=self._generate_prep_context(meeting),
                actions=["Review Context", "Add Notes"],
                entity_id=meeting.id,
                entity_type="event"
            ))

        return cards
```

### 4.3 Background Worker Setup

```python
# alfred/workers/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Morning briefing - personalized per user
@scheduler.scheduled_job('cron', hour=7, minute=0)
async def trigger_morning_briefings():
    """Send morning briefings based on user preferences."""
    users = await get_users_for_morning_briefing()
    for user in users:
        briefing = await proactive_engine.generate_morning_briefing(user.id)
        await notification_service.send_briefing(user.id, briefing)

# Evening review prompt
@scheduler.scheduled_job('cron', hour=20, minute=0)
async def trigger_evening_reviews():
    """Prompt users for evening review."""
    users = await get_users_for_evening_review()
    for user in users:
        await notification_service.send_evening_prompt(user.id)

# Habit reminders - per-habit schedule
@scheduler.scheduled_job('interval', minutes=15)
async def check_habit_reminders():
    """Send habit reminders at configured times."""
    due_reminders = await get_due_habit_reminders()
    for reminder in due_reminders:
        await notification_service.send_habit_reminder(
            reminder.user_id,
            reminder.habit
        )

# Pattern detection - daily batch
@scheduler.scheduled_job('cron', hour=3, minute=0)
async def run_pattern_detection():
    """Detect patterns and store insights."""
    users = await get_all_active_users()
    for user in users:
        await pattern_detector.analyze_user(user.id)
```

---

## 5. Voice Integration

### 5.1 Voice Flow

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  User Taps Mic    User Speaks     Audio Sent    Transcribed │
│       │               │               │              │      │
│       ▼               ▼               ▼              ▼      │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ Listen  │───►│ Record  │───►│ Upload  │───►│ Whisper │  │
│  │  State  │    │  Audio  │    │  to API │    │   STT   │  │
│  └─────────┘    └─────────┘    └─────────┘    └────┬────┘  │
│                                                     │       │
│  Alfred         Alfred          LLM               Text     │
│  Responds       Speaking       Processes         Returned  │
│       ▲               ▲               ▲              │      │
│       │               │               │              ▼      │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │  Done   │◄───│   TTS   │◄───│  Chat   │◄───│ Process │  │
│  │         │    │(optional)│    │   API   │    │  Input  │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Voice API

```python
# alfred/api/voice.py

@router.post("/voice/transcribe")
async def transcribe_audio(
    audio: UploadFile,
    user: User = Depends(get_current_user)
):
    """
    Transcribe audio using Whisper API.
    Returns transcript and optional chat response.
    """
    # Validate audio format
    if audio.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(400, "Invalid audio format")

    # Transcribe with Whisper
    transcript = await whisper_client.transcribe(
        audio.file,
        language="en"
    )

    return {
        "transcript": transcript.text,
        "confidence": transcript.confidence
    }


@router.post("/voice/chat")
async def voice_chat(
    audio: UploadFile,
    user: User = Depends(get_current_user)
):
    """
    Full voice interaction: transcribe + process + respond.
    Streams response via SSE.
    """
    # Transcribe
    transcript = await whisper_client.transcribe(audio.file)

    # Process with Alfred
    response = await alfred.chat(
        user_id=user.id,
        message=transcript.text
    )

    return {
        "input": transcript.text,
        "response": response.content,
        "actions_taken": response.actions,
        "thinking_steps": response.thinking_steps
    }
```

---

## 6. Transparency Implementation

### 6.1 Thinking Steps Model

```python
# alfred/core/entities.py

class ThinkingStep(BaseModel):
    id: str
    label: str
    status: Literal["pending", "active", "complete", "error"]
    detail: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AlfredResponse(BaseModel):
    content: str
    thinking_steps: List[ThinkingStep]
    actions_taken: List[str]
    entities_referenced: List[Entity]
    suggestions: List[str]
```

### 6.2 Streaming Response

```python
# alfred/api/chat.py

@router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    user: User = Depends(get_current_user)
):
    """
    Stream chat response with thinking steps.
    Uses Server-Sent Events for real-time updates.
    """
    async def generate():
        # Step 1: Understanding
        yield f"data: {json.dumps({'step': 'understanding', 'status': 'active'})}\n\n"
        intent = await alfred.understand_intent(request.message)
        yield f"data: {json.dumps({'step': 'understanding', 'status': 'complete', 'detail': intent})}\n\n"

        # Step 2: Context gathering
        yield f"data: {json.dumps({'step': 'context', 'status': 'active'})}\n\n"
        context = await alfred.gather_context(user.id, intent)
        yield f"data: {json.dumps({'step': 'context', 'status': 'complete'})}\n\n"

        # Step 3: Generate response
        yield f"data: {json.dumps({'step': 'responding', 'status': 'active'})}\n\n"
        response = await alfred.generate_response(intent, context)
        yield f"data: {json.dumps({'step': 'responding', 'status': 'complete'})}\n\n"

        # Final response
        yield f"data: {json.dumps({'type': 'response', 'content': response.content})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

---

## 7. Data Flow Examples

### 7.1 Morning Briefing

```
┌─────────────────────────────────────────────────────────────┐
│ Morning Briefing Data Flow                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Scheduler triggers at user's preferred time            │
│                    │                                        │
│                    ▼                                        │
│  2. ProactiveEngine.generate_morning_briefing(user_id)     │
│     │                                                       │
│     ├── Query today's tasks (priority sorted)              │
│     ├── Query today's calendar events                      │
│     ├── Query habits due today                             │
│     ├── Query projects needing attention                   │
│     ├── Check streak status                                │
│     └── Generate greeting based on time/context            │
│                    │                                        │
│                    ▼                                        │
│  3. Compose Briefing object                                │
│     {                                                       │
│       greeting: "Good morning, Pratap",                    │
│       focus: { top 1-3 priorities with context },          │
│       calendar: { next 4-5 hours },                        │
│       habits: { status and streaks },                      │
│       proactive: { cards if any }                          │
│     }                                                       │
│                    │                                        │
│                    ▼                                        │
│  4. Push notification sent                                 │
│     "Alfred has your morning briefing ready"               │
│                    │                                        │
│                    ▼                                        │
│  5. User opens app → Today screen loads briefing           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Task Creation via Voice

```
┌─────────────────────────────────────────────────────────────┐
│ Voice Task Creation Flow                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "Remind me to review the TechCorp contract by       │
│         Friday, it's high priority"                        │
│                    │                                        │
│                    ▼                                        │
│  1. Audio → Whisper → Text                                 │
│                    │                                        │
│                    ▼                                        │
│  2. Intent Classification                                  │
│     { type: "create_task", confidence: 0.95 }              │
│                    │                                        │
│                    ▼                                        │
│  3. Entity Extraction                                      │
│     {                                                       │
│       task_name: "review the TechCorp contract",           │
│       due_date: "Friday" → 2025-01-17,                     │
│       priority: "high",                                    │
│       entities: [{ name: "TechCorp", type: "company" }]    │
│     }                                                       │
│                    │                                        │
│                    ▼                                        │
│  4. Context Enhancement                                    │
│     - Found TechCorp project in user's projects           │
│     - Link task to TechCorp project                        │
│                    │                                        │
│                    ▼                                        │
│  5. Create Task via API                                    │
│     POST /tasks { ... }                                    │
│                    │                                        │
│                    ▼                                        │
│  6. Generate Response                                      │
│     "Done. I've created a high-priority task to review     │
│      the TechCorp contract, due Friday. I've linked it     │
│      to your TechCorp project."                            │
│                    │                                        │
│                    ▼                                        │
│  7. UI Update                                              │
│     - Task appears in Do screen                            │
│     - Project badge shows new task                         │
│     - Transparency panel shows steps taken                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Performance Considerations

### 8.1 Mobile Optimization

```typescript
// Strategies for smooth UX

// 1. Optimistic updates
const completeTask = async (taskId: string) => {
  // Update UI immediately
  updateTaskLocally(taskId, { status: 'completed' });

  try {
    await api.tasks.complete(taskId);
  } catch (error) {
    // Rollback on failure
    revertTaskLocally(taskId);
    showError('Failed to complete task');
  }
};

// 2. Prefetching
useEffect(() => {
  // Prefetch likely next screens
  prefetch('/dashboard/briefing');
  prefetch('/tasks/today');
  prefetch('/habits/today');
}, []);

// 3. Skeleton loading
const TodayScreen = () => {
  const { briefing, loading } = useBriefing();

  if (loading) return <BriefingSkeleton />;
  return <Briefing data={briefing} />;
};

// 4. Image/avatar caching
const CachedAvatar = memo(({ uri, size }) => (
  <Image
    source={{ uri }}
    style={{ width: size, height: size }}
    cachePolicy="memory-disk"
  />
));
```

### 8.2 API Optimization

```python
# Backend optimizations

# 1. Batch endpoints
@router.get("/dashboard/today")
async def get_today_dashboard(user: User = Depends(get_current_user)):
    """Single endpoint returns all today data."""
    tasks, habits, calendar, briefing = await asyncio.gather(
        get_tasks_due_today(user.id),
        get_habits_due_today(user.id),
        get_calendar_today(user.id),
        get_morning_briefing(user.id)
    )
    return {
        "tasks": tasks,
        "habits": habits,
        "calendar": calendar,
        "briefing": briefing
    }

# 2. Caching with Redis
@router.get("/briefing/morning")
@cache(ttl=300)  # 5 minute cache
async def get_morning_briefing(user: User = Depends(get_current_user)):
    return await generate_briefing(user.id)

# 3. Pagination
@router.get("/tasks")
async def get_tasks(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None
):
    return await db.get_tasks(limit=limit, offset=offset, status=status)
```

---

## 9. Security Considerations

### 9.1 Mobile Security

```typescript
// Secure token storage
import * as SecureStore from 'expo-secure-store';

const storeToken = async (token: string) => {
  await SecureStore.setItemAsync('auth_token', token, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY
  });
};

// Certificate pinning
const api = axios.create({
  baseURL: API_URL,
  // Add SSL pinning in production
});

// Biometric auth for sensitive actions
const confirmSensitiveAction = async () => {
  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Confirm with biometrics',
    cancelLabel: 'Cancel'
  });
  return result.success;
};
```

### 9.2 API Security

```python
# Rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_user_id)

@router.post("/chat")
@limiter.limit("30/minute")
async def chat(request: ChatRequest):
    pass

# Input validation
from pydantic import validator

class TaskCreate(BaseModel):
    title: str

    @validator('title')
    def sanitize_title(cls, v):
        # Remove potential XSS
        return bleach.clean(v, strip=True)

# Audit logging
@router.delete("/data")
async def delete_user_data(user: User = Depends(get_current_user)):
    await audit_log.record(
        user_id=user.id,
        action="data_deletion",
        ip=request.client.host
    )
    await db.delete_user_data(user.id)
```

---

## 10. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRODUCTION                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                     CDN / Edge                           │    │
│  │              (Static assets, API gateway)                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │                     Load Balancer                         │  │
│  └───────────────────────────┼───────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │                    API Servers (x3)                       │  │
│  │                     FastAPI + Uvicorn                     │  │
│  └───────────────────────────┼───────────────────────────────┘  │
│                              │                                   │
│  ┌────────────┬──────────────┼──────────────┬────────────────┐  │
│  │            │              │              │                │  │
│  │ PostgreSQL │    Redis     │    Neo4j     │    Qdrant      │  │
│  │ (Primary)  │   (Cache)    │   (Graph)    │   (Vector)     │  │
│  │            │              │              │                │  │
│  └────────────┴──────────────┴──────────────┴────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Background Workers                     │    │
│  │        APScheduler / Celery on separate instances       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Next Steps

See `ALFRED_ROADMAP.md` for implementation phases.
