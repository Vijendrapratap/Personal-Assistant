from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, date


# ============================================
# LLM PROVIDER INTERFACE
# ============================================

class LLMProvider(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> str:
        """Takes text + history, returns text."""
        pass


# ============================================
# VECTOR DB PROVIDER INTERFACE
# ============================================

class VectorDBProvider(ABC):
    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Takes a query, returns relevant context documents."""
        pass

    @abstractmethod
    def upsert(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """Insert or update a document in the vector store."""
        pass


# ============================================
# MEMORY STORAGE INTERFACE (Extended)
# ============================================

class MemoryStorage(ABC):
    """
    Abstract interface for all storage operations.
    Implementations can be PostgreSQL, SQLite, or any other database.
    """

    # ------------------------------------------
    # USER MANAGEMENT
    # ------------------------------------------

    @abstractmethod
    def create_user(self, user_id: str, email: str, password_hash: str) -> bool:
        """Create a new user. Returns True if successful."""
        pass

    @abstractmethod
    def get_user_credentials(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user credentials by email (returns dict with user_id, password_hash)."""
        pass

    @abstractmethod
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile as a dictionary."""
        pass

    @abstractmethod
    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile fields."""
        pass

    # ------------------------------------------
    # CHAT HISTORY
    # ------------------------------------------

    @abstractmethod
    def save_chat(self, user_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Save a chat message."""
        pass

    @abstractmethod
    def get_chat_history(self, user_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """Get recent chat history for a user."""
        pass

    # ------------------------------------------
    # PREFERENCES & LEARNING
    # ------------------------------------------

    @abstractmethod
    def save_preference(self, user_id: str, key: str, value: str, confidence: float = 1.0) -> bool:
        """Save a user preference."""
        pass

    @abstractmethod
    def get_preferences(self, user_id: str) -> Dict[str, str]:
        """Get all preferences for a user."""
        pass

    @abstractmethod
    def save_learning(self, user_id: str, content: str, original_query: Optional[str] = None) -> bool:
        """Save a learning/knowledge item."""
        pass

    # ------------------------------------------
    # PROJECT MANAGEMENT
    # ------------------------------------------

    @abstractmethod
    def create_project(self, user_id: str, name: str, organization: str = "",
                       role: str = "contributor", description: str = "",
                       integrations: Optional[Dict] = None) -> Optional[str]:
        """Create a new project. Returns project_id if successful."""
        pass

    @abstractmethod
    def get_project(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a single project by ID."""
        pass

    @abstractmethod
    def get_projects(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all projects for a user, optionally filtered by status."""
        pass

    @abstractmethod
    def update_project(self, project_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update project fields."""
        pass

    @abstractmethod
    def delete_project(self, project_id: str, user_id: str) -> bool:
        """Archive/delete a project."""
        pass

    @abstractmethod
    def add_project_update(self, project_id: str, user_id: str, content: str,
                           update_type: str = "progress", action_items: Optional[List] = None,
                           blockers: Optional[List] = None) -> Optional[str]:
        """Add an update to a project. Returns update_id."""
        pass

    @abstractmethod
    def get_project_updates(self, project_id: str, user_id: str,
                            limit: int = 20) -> List[Dict[str, Any]]:
        """Get updates for a project."""
        pass

    # ------------------------------------------
    # TASK MANAGEMENT
    # ------------------------------------------

    @abstractmethod
    def create_task(self, user_id: str, title: str, project_id: Optional[str] = None,
                    description: str = "", priority: str = "medium",
                    due_date: Optional[datetime] = None, tags: Optional[List] = None,
                    source: str = "user") -> Optional[str]:
        """Create a new task. Returns task_id if successful."""
        pass

    @abstractmethod
    def get_task(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a single task by ID."""
        pass

    @abstractmethod
    def get_tasks(self, user_id: str, project_id: Optional[str] = None,
                  status: Optional[str] = None, priority: Optional[str] = None,
                  due_before: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get tasks with various filters."""
        pass

    @abstractmethod
    def update_task(self, task_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update task fields."""
        pass

    @abstractmethod
    def complete_task(self, task_id: str, user_id: str) -> bool:
        """Mark a task as completed."""
        pass

    @abstractmethod
    def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task."""
        pass

    # ------------------------------------------
    # HABIT TRACKING
    # ------------------------------------------

    @abstractmethod
    def create_habit(self, user_id: str, name: str, frequency: str = "daily",
                     description: str = "", time_preference: Optional[str] = None,
                     motivation: str = "", category: str = "general") -> Optional[str]:
        """Create a new habit. Returns habit_id if successful."""
        pass

    @abstractmethod
    def get_habit(self, habit_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a single habit by ID."""
        pass

    @abstractmethod
    def get_habits(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all habits for a user."""
        pass

    @abstractmethod
    def update_habit(self, habit_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update habit fields."""
        pass

    @abstractmethod
    def log_habit(self, habit_id: str, user_id: str, logged_date: Optional[date] = None,
                  notes: str = "", duration_minutes: Optional[int] = None) -> bool:
        """Log a habit completion. Updates streak automatically."""
        pass

    @abstractmethod
    def get_habit_logs(self, habit_id: str, user_id: str,
                       start_date: Optional[date] = None,
                       end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get habit logs within a date range."""
        pass

    @abstractmethod
    def delete_habit(self, habit_id: str, user_id: str) -> bool:
        """Delete a habit."""
        pass

    # ------------------------------------------
    # DASHBOARD & ANALYTICS
    # ------------------------------------------

    @abstractmethod
    def get_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get aggregated data for dashboard."""
        pass

    @abstractmethod
    def get_tasks_due_today(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tasks due today."""
        pass

    @abstractmethod
    def get_habits_due_today(self, user_id: str) -> List[Dict[str, Any]]:
        """Get habits that should be completed today."""
        pass

    @abstractmethod
    def get_project_health(self, user_id: str) -> List[Dict[str, Any]]:
        """Get health metrics for all projects."""
        pass

    # ------------------------------------------
    # NOTIFICATIONS & SCHEDULING
    # ------------------------------------------

    @abstractmethod
    def schedule_notification(self, user_id: str, notification_type: str,
                              title: str, content: str, trigger_time: datetime,
                              context: Optional[Dict] = None) -> Optional[str]:
        """Schedule a notification. Returns notification_id."""
        pass

    @abstractmethod
    def get_pending_notifications(self, user_id: Optional[str] = None,
                                   before: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get pending notifications, optionally filtered by user and time."""
        pass

    @abstractmethod
    def mark_notification_sent(self, notification_id: str) -> bool:
        """Mark a notification as sent."""
        pass


# ============================================
# KNOWLEDGE GRAPH INTERFACE (for Neo4j)
# ============================================

class KnowledgeGraphProvider(ABC):
    """Abstract interface for knowledge graph operations."""

    @abstractmethod
    def add_fact(self, user_id: str, subject: str, predicate: str,
                 object_value: str, category: str = "fact",
                 confidence: float = 1.0) -> Optional[str]:
        """Add a fact to the knowledge graph."""
        pass

    @abstractmethod
    def query_facts(self, user_id: str, subject: Optional[str] = None,
                    predicate: Optional[str] = None,
                    category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query facts from the knowledge graph."""
        pass

    @abstractmethod
    def add_relationship(self, user_id: str, from_entity: str, relationship: str,
                         to_entity: str, properties: Optional[Dict] = None) -> bool:
        """Add a relationship between entities."""
        pass

    @abstractmethod
    def get_related_entities(self, user_id: str, entity: str,
                             relationship: Optional[str] = None,
                             direction: str = "both") -> List[Dict[str, Any]]:
        """Get entities related to a given entity."""
        pass

    @abstractmethod
    def get_user_context(self, user_id: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """Get relevant context for a user based on their knowledge graph."""
        pass


# ============================================
# NOTIFICATION PROVIDER INTERFACE
# ============================================

class NotificationProvider(ABC):
    """Abstract interface for sending notifications."""

    @abstractmethod
    def send_push(self, user_id: str, title: str, body: str,
                  data: Optional[Dict] = None) -> bool:
        """Send a push notification."""
        pass

    @abstractmethod
    def send_email(self, user_id: str, subject: str, body: str,
                   html: Optional[str] = None) -> bool:
        """Send an email notification."""
        pass

    @abstractmethod
    def register_device(self, user_id: str, device_token: str,
                        platform: str = "mobile") -> bool:
        """Register a device for push notifications."""
        pass
