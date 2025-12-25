from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
import uuid


# ============================================
# ENUMS
# ============================================

class ProjectRole(str, Enum):
    FOUNDER = "founder"
    COO = "coo"
    PM = "pm"
    DEVELOPER = "developer"
    CONTRIBUTOR = "contributor"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class HabitFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    WEEKDAYS = "weekdays"
    CUSTOM = "custom"


class UpdateType(str, Enum):
    PROGRESS = "progress"
    BLOCKER = "blocker"
    DECISION = "decision"
    NOTE = "note"
    MILESTONE = "milestone"


class NotificationType(str, Enum):
    MORNING_BRIEFING = "morning_briefing"
    EVENING_REVIEW = "evening_review"
    HABIT_REMINDER = "habit_reminder"
    TASK_DUE = "task_due"
    PROJECT_UPDATE = "project_update"
    PROACTIVE_NUDGE = "proactive_nudge"


# ============================================
# CORE ENTITIES
# ============================================

@dataclass
class Message:
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserPreference:
    key: str
    value: str
    confidence: float = 1.0
    learned_at: datetime = field(default_factory=datetime.now)


@dataclass
class Learning:
    topic: str
    content: str
    original_query: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserProfile:
    bio: str = ""
    work_type: str = ""
    voice_id: str = "default"
    personality_prompt: str = "Standard Butler"
    interaction_type: str = "formal"  # formal, casual, terse

    # Notification preferences
    morning_briefing_time: str = "08:00"
    evening_review_time: str = "18:00"
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"

    # Proactivity settings
    proactivity_level: str = "medium"  # low, medium, high
    reminder_style: str = "gentle"  # gentle, persistent


@dataclass
class UserCredentials:
    email: str
    password_hash: str


@dataclass
class UserContext:
    user_id: str
    preferences: Dict[str, str] = field(default_factory=dict)
    profile: Optional[UserProfile] = None


# ============================================
# PROJECT MANAGEMENT
# ============================================

@dataclass
class Project:
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    name: str = ""
    organization: str = ""
    role: ProjectRole = ProjectRole.CONTRIBUTOR
    status: ProjectStatus = ProjectStatus.ACTIVE
    description: str = ""

    # Integration links
    integrations: Dict[str, str] = field(default_factory=dict)  # {"trello": "board_id", "slack": "channel_id"}

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Computed/Cached
    task_count: int = 0
    completed_task_count: int = 0
    health_score: float = 100.0  # Percentage


@dataclass
class ProjectUpdate:
    update_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    user_id: str = ""
    content: str = ""
    update_type: UpdateType = UpdateType.PROGRESS

    # Extracted entities
    action_items: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)


# ============================================
# TASK MANAGEMENT
# ============================================

@dataclass
class Task:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    project_id: Optional[str] = None  # None = personal task

    title: str = ""
    description: str = ""

    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING

    due_date: Optional[datetime] = None
    recurrence: Optional[str] = None  # "daily", "weekly", etc.

    # Context
    blockers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Source tracking
    source: str = "user"  # "user", "alfred", "integration"
    source_ref: Optional[str] = None  # External reference ID

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


# ============================================
# HABIT TRACKING
# ============================================

@dataclass
class Habit:
    habit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    name: str = ""
    description: str = ""
    frequency: HabitFrequency = HabitFrequency.DAILY

    # Scheduling
    time_preference: Optional[str] = None  # "08:00"
    days_of_week: List[int] = field(default_factory=list)  # 0=Monday, 6=Sunday

    # Streaks
    current_streak: int = 0
    best_streak: int = 0
    total_completions: int = 0
    last_logged: Optional[date] = None

    # Motivation
    motivation: str = ""
    category: str = "general"  # fitness, productivity, learning, etc.

    # Status
    active: bool = True
    reminder_enabled: bool = True

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class HabitLog:
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    habit_id: str = ""
    user_id: str = ""

    logged_date: date = field(default_factory=date.today)
    notes: str = ""
    duration_minutes: Optional[int] = None  # For timed habits

    created_at: datetime = field(default_factory=datetime.now)


# ============================================
# PROACTIVE ENGINE
# ============================================

@dataclass
class ScheduledNotification:
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    notification_type: NotificationType = NotificationType.PROACTIVE_NUDGE
    title: str = ""
    content: str = ""

    trigger_time: datetime = field(default_factory=datetime.now)

    # Context for generation
    context: Dict[str, Any] = field(default_factory=dict)

    # Status
    status: str = "pending"  # pending, sent, read, dismissed
    sent_at: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DailyBriefing:
    """Generated content for morning/evening briefings"""
    user_id: str = ""
    briefing_type: str = "morning"  # "morning" or "evening"
    date: date = field(default_factory=date.today)

    # Content sections
    greeting: str = ""
    priority_tasks: List[Dict[str, Any]] = field(default_factory=list)
    project_updates: List[Dict[str, Any]] = field(default_factory=list)
    habit_status: List[Dict[str, Any]] = field(default_factory=list)
    calendar_events: List[Dict[str, Any]] = field(default_factory=list)

    # For evening
    completed_today: List[Dict[str, Any]] = field(default_factory=list)
    carried_forward: List[Dict[str, Any]] = field(default_factory=list)

    # Generated narrative
    narrative: str = ""

    generated_at: datetime = field(default_factory=datetime.now)


# ============================================
# KNOWLEDGE GRAPH (for future Neo4j integration)
# ============================================

@dataclass
class KnowledgeFact:
    fact_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    category: str = ""  # preference, fact, decision, pattern
    subject: str = ""
    predicate: str = ""
    object_value: str = ""

    confidence: float = 1.0
    source: str = "conversation"  # conversation, integration, explicit

    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)


@dataclass
class Decision:
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    project_id: Optional[str] = None

    description: str = ""
    context: str = ""
    outcome: str = ""

    created_at: datetime = field(default_factory=datetime.now)


# ============================================
# DASHBOARD & ANALYTICS
# ============================================

@dataclass
class DashboardData:
    """Aggregated data for dashboard display"""
    user_id: str = ""
    generated_at: datetime = field(default_factory=datetime.now)

    # Today's focus
    priority_tasks: List[Task] = field(default_factory=list)
    due_today: List[Task] = field(default_factory=list)

    # Project health
    projects: List[Project] = field(default_factory=list)

    # Habits
    habits: List[Habit] = field(default_factory=list)
    habits_due_today: List[Habit] = field(default_factory=list)

    # Recent activity
    recent_updates: List[ProjectUpdate] = field(default_factory=list)

    # Stats
    tasks_completed_today: int = 0
    tasks_pending: int = 0
    active_projects: int = 0
    current_streaks: Dict[str, int] = field(default_factory=dict)
