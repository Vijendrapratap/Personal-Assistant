"""
SQLite Storage Adapter - Zero-Config Database

A drop-in replacement for PostgresAdapter that uses SQLite.
No external database server required - perfect for single-user deployment.
"""

import sqlite3
import json
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
from pathlib import Path
from contextlib import contextmanager

from alfred.core.interfaces import MemoryStorage


class SQLiteAdapter(MemoryStorage):
    """
    SQLite implementation of the MemoryStorage interface.

    Features:
    - Zero configuration required
    - Single file database
    - Full compatibility with PostgresAdapter interface
    - Automatic schema creation
    """

    def __init__(self, db_path: str = None):
        """
        Initialize SQLite adapter.

        Args:
            db_path: Path to database file. Defaults to ~/.alfred/alfred.db
        """
        if db_path is None:
            db_path = str(Path.home() / ".alfred" / "alfred.db")

        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    @contextmanager
    def _get_conn(self):
        """Get a database connection with proper handling."""
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Create all necessary tables if they don't exist."""
        with self._get_conn() as conn:
            cur = conn.cursor()

            # Users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    profile TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Chat history
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    role TEXT,
                    content TEXT,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat_history(user_id)")

            # User preferences
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT,
                    key TEXT,
                    value TEXT,
                    confidence REAL DEFAULT 1.0,
                    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, key)
                )
            """)

            # Projects table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    organization TEXT DEFAULT '',
                    role TEXT DEFAULT 'contributor',
                    status TEXT DEFAULT 'active',
                    description TEXT DEFAULT '',
                    integrations TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)")

            # Project updates
            cur.execute("""
                CREATE TABLE IF NOT EXISTS project_updates (
                    update_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    update_type TEXT DEFAULT 'progress',
                    action_items TEXT DEFAULT '[]',
                    blockers TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_updates_project ON project_updates(project_id)")

            # Tasks table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    project_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    due_date TIMESTAMP,
                    recurrence TEXT,
                    blockers TEXT DEFAULT '[]',
                    tags TEXT DEFAULT '[]',
                    source TEXT DEFAULT 'user',
                    source_ref TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")

            # Habits table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS habits (
                    habit_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    frequency TEXT DEFAULT 'daily',
                    time_preference TEXT,
                    days_of_week TEXT DEFAULT '[]',
                    current_streak INTEGER DEFAULT 0,
                    best_streak INTEGER DEFAULT 0,
                    total_completions INTEGER DEFAULT 0,
                    last_logged DATE,
                    motivation TEXT DEFAULT '',
                    category TEXT DEFAULT 'general',
                    active INTEGER DEFAULT 1,
                    reminder_enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_habits_user_id ON habits(user_id)")

            # Habit logs
            cur.execute("""
                CREATE TABLE IF NOT EXISTS habit_logs (
                    log_id TEXT PRIMARY KEY,
                    habit_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    logged_date DATE NOT NULL,
                    notes TEXT DEFAULT '',
                    duration_minutes INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(habit_id, logged_date)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_habit ON habit_logs(habit_id)")

            # Scheduled notifications
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_notifications (
                    notification_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    trigger_time TIMESTAMP NOT NULL,
                    context TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'pending',
                    sent_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON scheduled_notifications(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_trigger ON scheduled_notifications(trigger_time)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_status ON scheduled_notifications(status)")

            # Knowledge/learnings table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS learnings (
                    learning_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    topic TEXT DEFAULT 'general',
                    content TEXT NOT NULL,
                    original_query TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_learnings_user ON learnings(user_id)")

            # Knowledge graph entities (embedded graph)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    attributes TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_entities_user ON entities(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(user_id, type)")

            # Knowledge graph relationships
            cur.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    relationship_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    from_entity TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    to_entity TEXT NOT NULL,
                    properties TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_rels_from ON relationships(from_entity)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_rels_to ON relationships(to_entity)")

            # Facts table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    fact_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object_value TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(user_id, subject)")

            # Integration credentials (OAuth tokens)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS integration_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    integration_name TEXT NOT NULL,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_type TEXT DEFAULT 'Bearer',
                    expires_at TIMESTAMP,
                    scope TEXT,
                    credentials TEXT DEFAULT '{}',
                    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, integration_name)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_integration_user ON integration_credentials(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_integration_name ON integration_credentials(integration_name)")

    def _json_loads(self, value: str) -> Any:
        """Safely load JSON."""
        if value is None:
            return {}
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}

    def _json_dumps(self, value: Any) -> str:
        """Safely dump to JSON."""
        return json.dumps(value) if value else '{}'

    # ------------------------------------------
    # USER MANAGEMENT
    # ------------------------------------------

    def create_user(self, user_id: str, email: str, password_hash: str) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO users (user_id, email, password_hash) VALUES (?, ?, ?)",
                    (user_id, email, password_hash)
                )
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    def get_user_credentials(self, email: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT user_id, password_hash FROM users WHERE email = ?",
                (email,)
            ).fetchone()
            if row:
                return {"user_id": row["user_id"], "password_hash": row["password_hash"]}
        return None

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT profile FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            if row:
                return self._json_loads(row["profile"])
        return None

    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        try:
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT profile FROM users WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
                current_profile = self._json_loads(row["profile"]) if row else {}
                updated_profile = {**current_profile, **profile_data}
                conn.execute(
                    "UPDATE users SET profile = ? WHERE user_id = ?",
                    (self._json_dumps(updated_profile), user_id)
                )
            return True
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False

    # ------------------------------------------
    # CHAT HISTORY
    # ------------------------------------------

    def save_chat(self, user_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO chat_history (user_id, role, content, metadata) VALUES (?, ?, ?, ?)",
                    (user_id, role, content, self._json_dumps(metadata or {}))
                )
            return True
        except Exception as e:
            print(f"Error saving chat: {e}")
            return False

    def get_chat_history(self, user_id: str, limit: int = 20) -> List[Dict[str, str]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT role, content FROM chat_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit)
            ).fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    # ------------------------------------------
    # PREFERENCES & LEARNING
    # ------------------------------------------

    def save_preference(self, user_id: str, key: str, value: str, confidence: float = 1.0) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO user_preferences (user_id, key, value, confidence, learned_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (user_id, key, value, confidence)
                )
            return True
        except Exception as e:
            print(f"Error saving preference: {e}")
            return False

    def get_preferences(self, user_id: str) -> Dict[str, str]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT key, value FROM user_preferences WHERE user_id = ?",
                (user_id,)
            ).fetchall()
            return {row["key"]: row["value"] for row in rows}

    def save_learning(self, user_id: str, content: str, original_query: Optional[str] = None) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO learnings (learning_id, user_id, content, original_query) VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), user_id, content, original_query)
                )
            return True
        except Exception as e:
            print(f"Error saving learning: {e}")
            return False

    # ------------------------------------------
    # PROJECT MANAGEMENT
    # ------------------------------------------

    def create_project(self, user_id: str, name: str, organization: str = "",
                       role: str = "contributor", description: str = "",
                       integrations: Optional[Dict] = None) -> Optional[str]:
        project_id = str(uuid.uuid4())
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO projects (project_id, user_id, name, organization, role, description, integrations)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (project_id, user_id, name, organization, role, description, self._json_dumps(integrations or {}))
                )
            return project_id
        except Exception as e:
            print(f"Error creating project: {e}")
            return None

    def get_project(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT project_id, user_id, name, organization, role, status,
                       description, integrations, metadata, created_at, updated_at
                FROM projects
                WHERE project_id = ? AND user_id = ?
                """,
                (project_id, user_id)
            ).fetchone()

            if row:
                # Get task counts
                task_row = conn.execute(
                    """
                    SELECT COUNT(*), SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
                    FROM tasks WHERE project_id = ?
                    """,
                    (project_id,)
                ).fetchone()
                task_count = task_row[0] or 0
                completed_count = task_row[1] or 0

                return {
                    "project_id": row["project_id"],
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "organization": row["organization"],
                    "role": row["role"],
                    "status": row["status"],
                    "description": row["description"],
                    "integrations": self._json_loads(row["integrations"]),
                    "metadata": self._json_loads(row["metadata"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "task_count": task_count,
                    "completed_task_count": completed_count,
                    "health_score": (completed_count / task_count * 100) if task_count > 0 else 100
                }
        return None

    def get_projects(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            if status:
                rows = conn.execute(
                    """
                    SELECT project_id, name, organization, role, status, description, created_at
                    FROM projects WHERE user_id = ? AND status = ?
                    ORDER BY updated_at DESC
                    """,
                    (user_id, status)
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT project_id, name, organization, role, status, description, created_at
                    FROM projects WHERE user_id = ?
                    ORDER BY updated_at DESC
                    """,
                    (user_id,)
                ).fetchall()

            projects = []
            for row in rows:
                task_row = conn.execute(
                    """
                    SELECT COUNT(*), SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
                    FROM tasks WHERE project_id = ?
                    """,
                    (row["project_id"],)
                ).fetchone()
                task_count = task_row[0] or 0
                completed_count = task_row[1] or 0

                projects.append({
                    "project_id": row["project_id"],
                    "name": row["name"],
                    "organization": row["organization"],
                    "role": row["role"],
                    "status": row["status"],
                    "description": row["description"],
                    "created_at": row["created_at"],
                    "task_count": task_count,
                    "completed_task_count": completed_count,
                    "health_score": (completed_count / task_count * 100) if task_count > 0 else 100
                })
            return projects

    def update_project(self, project_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        allowed_fields = ['name', 'organization', 'role', 'status', 'description', 'integrations', 'metadata']
        updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not updates:
            return False

        try:
            with self._get_conn() as conn:
                set_clauses = []
                values = []
                for key, value in updates.items():
                    set_clauses.append(f"{key} = ?")
                    if key in ['integrations', 'metadata']:
                        values.append(self._json_dumps(value))
                    else:
                        values.append(value)

                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                values.extend([project_id, user_id])

                query = f"UPDATE projects SET {', '.join(set_clauses)} WHERE project_id = ? AND user_id = ?"
                conn.execute(query, values)
            return True
        except Exception as e:
            print(f"Error updating project: {e}")
            return False

    def delete_project(self, project_id: str, user_id: str) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "UPDATE projects SET status = 'archived' WHERE project_id = ? AND user_id = ?",
                    (project_id, user_id)
                )
            return True
        except Exception as e:
            print(f"Error deleting project: {e}")
            return False

    def add_project_update(self, project_id: str, user_id: str, content: str,
                           update_type: str = "progress", action_items: Optional[List] = None,
                           blockers: Optional[List] = None) -> Optional[str]:
        update_id = str(uuid.uuid4())
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO project_updates (update_id, project_id, user_id, content, update_type, action_items, blockers)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (update_id, project_id, user_id, content, update_type,
                     self._json_dumps(action_items or []), self._json_dumps(blockers or []))
                )
                conn.execute(
                    "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE project_id = ?",
                    (project_id,)
                )
            return update_id
        except Exception as e:
            print(f"Error adding project update: {e}")
            return None

    def get_project_updates(self, project_id: str, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT update_id, content, update_type, action_items, blockers, created_at
                FROM project_updates
                WHERE project_id = ? AND user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (project_id, user_id, limit)
            ).fetchall()

            return [{
                "update_id": row["update_id"],
                "content": row["content"],
                "update_type": row["update_type"],
                "action_items": self._json_loads(row["action_items"]),
                "blockers": self._json_loads(row["blockers"]),
                "created_at": row["created_at"]
            } for row in rows]

    # ------------------------------------------
    # TASK MANAGEMENT
    # ------------------------------------------

    def create_task(self, user_id: str, title: str, project_id: Optional[str] = None,
                    description: str = "", priority: str = "medium",
                    due_date: Optional[datetime] = None, tags: Optional[List] = None,
                    source: str = "user") -> Optional[str]:
        task_id = str(uuid.uuid4())
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO tasks (task_id, user_id, project_id, title, description, priority, due_date, tags, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (task_id, user_id, project_id, title, description, priority, due_date, self._json_dumps(tags or []), source)
                )
            return task_id
        except Exception as e:
            print(f"Error creating task: {e}")
            return None

    def get_task(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT t.task_id, t.user_id, t.project_id, t.title, t.description,
                       t.priority, t.status, t.due_date, t.recurrence, t.blockers,
                       t.tags, t.source, t.created_at, t.completed_at,
                       p.name as project_name
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.project_id
                WHERE t.task_id = ? AND t.user_id = ?
                """,
                (task_id, user_id)
            ).fetchone()

            if row:
                return {
                    "task_id": row["task_id"],
                    "user_id": row["user_id"],
                    "project_id": row["project_id"],
                    "title": row["title"],
                    "description": row["description"],
                    "priority": row["priority"],
                    "status": row["status"],
                    "due_date": row["due_date"],
                    "recurrence": row["recurrence"],
                    "blockers": self._json_loads(row["blockers"]),
                    "tags": self._json_loads(row["tags"]),
                    "source": row["source"],
                    "created_at": row["created_at"],
                    "completed_at": row["completed_at"],
                    "project_name": row["project_name"]
                }
        return None

    def get_tasks(self, user_id: str, project_id: Optional[str] = None,
                  status: Optional[str] = None, priority: Optional[str] = None,
                  due_before: Optional[datetime] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            query = """
                SELECT t.task_id, t.project_id, t.title, t.description,
                       t.priority, t.status, t.due_date, t.tags, t.created_at,
                       p.name as project_name
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.project_id
                WHERE t.user_id = ?
            """
            params = [user_id]

            if project_id:
                query += " AND t.project_id = ?"
                params.append(project_id)
            if status:
                query += " AND t.status = ?"
                params.append(status)
            if priority:
                query += " AND t.priority = ?"
                params.append(priority)
            if due_before:
                query += " AND t.due_date <= ?"
                params.append(due_before)

            query += " ORDER BY t.due_date ASC, t.priority DESC, t.created_at DESC"

            rows = conn.execute(query, params).fetchall()
            return [{
                "task_id": row["task_id"],
                "project_id": row["project_id"],
                "title": row["title"],
                "description": row["description"],
                "priority": row["priority"],
                "status": row["status"],
                "due_date": row["due_date"],
                "tags": self._json_loads(row["tags"]),
                "created_at": row["created_at"],
                "project_name": row["project_name"]
            } for row in rows]

    def update_task(self, task_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        allowed_fields = ['title', 'description', 'priority', 'status', 'due_date', 'recurrence', 'blockers', 'tags', 'project_id']
        updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not updates:
            return False

        try:
            with self._get_conn() as conn:
                set_clauses = []
                values = []
                for key, value in updates.items():
                    set_clauses.append(f"{key} = ?")
                    if key in ['blockers', 'tags']:
                        values.append(self._json_dumps(value))
                    else:
                        values.append(value)

                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                values.extend([task_id, user_id])

                query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE task_id = ? AND user_id = ?"
                conn.execute(query, values)
            return True
        except Exception as e:
            print(f"Error updating task: {e}")
            return False

    def complete_task(self, task_id: str, user_id: str) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    UPDATE tasks
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE task_id = ? AND user_id = ?
                    """,
                    (task_id, user_id)
                )
            return True
        except Exception as e:
            print(f"Error completing task: {e}")
            return False

    def delete_task(self, task_id: str, user_id: str) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "DELETE FROM tasks WHERE task_id = ? AND user_id = ?",
                    (task_id, user_id)
                )
            return True
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False

    # ------------------------------------------
    # HABIT TRACKING
    # ------------------------------------------

    def create_habit(self, user_id: str, name: str, frequency: str = "daily",
                     description: str = "", time_preference: Optional[str] = None,
                     motivation: str = "", category: str = "general") -> Optional[str]:
        habit_id = str(uuid.uuid4())
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO habits (habit_id, user_id, name, description, frequency, time_preference, motivation, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (habit_id, user_id, name, description, frequency, time_preference, motivation, category)
                )
            return habit_id
        except Exception as e:
            print(f"Error creating habit: {e}")
            return None

    def get_habit(self, habit_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT habit_id, user_id, name, description, frequency, time_preference,
                       current_streak, best_streak, total_completions, last_logged,
                       motivation, category, active, reminder_enabled, created_at
                FROM habits
                WHERE habit_id = ? AND user_id = ?
                """,
                (habit_id, user_id)
            ).fetchone()

            if row:
                return {
                    "habit_id": row["habit_id"],
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "description": row["description"],
                    "frequency": row["frequency"],
                    "time_preference": row["time_preference"],
                    "current_streak": row["current_streak"],
                    "best_streak": row["best_streak"],
                    "total_completions": row["total_completions"],
                    "last_logged": row["last_logged"],
                    "motivation": row["motivation"],
                    "category": row["category"],
                    "active": bool(row["active"]),
                    "reminder_enabled": bool(row["reminder_enabled"]),
                    "created_at": row["created_at"]
                }
        return None

    def get_habits(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            query = """
                SELECT habit_id, name, description, frequency, time_preference,
                       current_streak, best_streak, total_completions, last_logged,
                       motivation, category, active, reminder_enabled
                FROM habits WHERE user_id = ?
            """
            if active_only:
                query += " AND active = 1"
            query += " ORDER BY created_at ASC"

            rows = conn.execute(query, (user_id,)).fetchall()
            return [{
                "habit_id": row["habit_id"],
                "name": row["name"],
                "description": row["description"],
                "frequency": row["frequency"],
                "time_preference": row["time_preference"],
                "current_streak": row["current_streak"],
                "best_streak": row["best_streak"],
                "total_completions": row["total_completions"],
                "last_logged": row["last_logged"],
                "motivation": row["motivation"],
                "category": row["category"],
                "active": bool(row["active"]),
                "reminder_enabled": bool(row["reminder_enabled"])
            } for row in rows]

    def update_habit(self, habit_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        allowed_fields = ['name', 'description', 'frequency', 'time_preference', 'motivation', 'category', 'active', 'reminder_enabled']
        updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not updates:
            return False

        try:
            with self._get_conn() as conn:
                set_clauses = [f"{key} = ?" for key in updates.keys()]
                values = list(updates.values())
                values.extend([habit_id, user_id])

                query = f"UPDATE habits SET {', '.join(set_clauses)} WHERE habit_id = ? AND user_id = ?"
                conn.execute(query, values)
            return True
        except Exception as e:
            print(f"Error updating habit: {e}")
            return False

    def log_habit(self, habit_id: str, user_id: str, logged_date: Optional[date] = None,
                  notes: str = "", duration_minutes: Optional[int] = None) -> bool:
        if logged_date is None:
            logged_date = date.today()

        log_id = str(uuid.uuid4())
        try:
            with self._get_conn() as conn:
                # Insert or update the log
                conn.execute(
                    """
                    INSERT OR REPLACE INTO habit_logs (log_id, habit_id, user_id, logged_date, notes, duration_minutes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (log_id, habit_id, user_id, logged_date, notes, duration_minutes)
                )

                # Get current habit data
                row = conn.execute(
                    "SELECT current_streak, best_streak, total_completions, last_logged FROM habits WHERE habit_id = ?",
                    (habit_id,)
                ).fetchone()

                if row:
                    current_streak = row["current_streak"] or 0
                    best_streak = row["best_streak"] or 0
                    total_completions = row["total_completions"] or 0
                    last_logged = row["last_logged"]

                    # Calculate new streak
                    if last_logged:
                        if isinstance(last_logged, str):
                            last_logged = date.fromisoformat(last_logged)
                        days_diff = (logged_date - last_logged).days
                        if days_diff == 1:
                            current_streak += 1
                        elif days_diff > 1:
                            current_streak = 1
                    else:
                        current_streak = 1

                    if current_streak > best_streak:
                        best_streak = current_streak

                    # Update habit
                    conn.execute(
                        """
                        UPDATE habits
                        SET current_streak = ?, best_streak = ?, total_completions = ?, last_logged = ?
                        WHERE habit_id = ?
                        """,
                        (current_streak, best_streak, total_completions + 1, logged_date, habit_id)
                    )
            return True
        except Exception as e:
            print(f"Error logging habit: {e}")
            return False

    def get_habit_logs(self, habit_id: str, user_id: str,
                       start_date: Optional[date] = None,
                       end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            query = """
                SELECT log_id, logged_date, notes, duration_minutes, created_at
                FROM habit_logs
                WHERE habit_id = ? AND user_id = ?
            """
            params = [habit_id, user_id]

            if start_date:
                query += " AND logged_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND logged_date <= ?"
                params.append(end_date)

            query += " ORDER BY logged_date DESC"

            rows = conn.execute(query, params).fetchall()
            return [{
                "log_id": row["log_id"],
                "logged_date": row["logged_date"],
                "notes": row["notes"],
                "duration_minutes": row["duration_minutes"],
                "created_at": row["created_at"]
            } for row in rows]

    def delete_habit(self, habit_id: str, user_id: str) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "UPDATE habits SET active = 0 WHERE habit_id = ? AND user_id = ?",
                    (habit_id, user_id)
                )
            return True
        except Exception as e:
            print(f"Error deleting habit: {e}")
            return False

    # ------------------------------------------
    # DASHBOARD & ANALYTICS
    # ------------------------------------------

    def get_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        with self._get_conn() as conn:
            # Tasks stats
            task_row = conn.execute(
                """
                SELECT
                    COUNT(CASE WHEN status != 'completed' AND status != 'cancelled' THEN 1 END) as pending,
                    COUNT(CASE WHEN status = 'completed' AND completed_at >= ? AND completed_at <= ? THEN 1 END) as completed_today
                FROM tasks WHERE user_id = ?
                """,
                (today_start, today_end, user_id)
            ).fetchone()

            tasks_pending = task_row["pending"] or 0
            tasks_completed_today = task_row["completed_today"] or 0

            # Active projects
            project_row = conn.execute(
                "SELECT COUNT(*) as count FROM projects WHERE user_id = ? AND status = 'active'",
                (user_id,)
            ).fetchone()
            active_projects = project_row["count"] or 0

            # Current streaks
            streak_rows = conn.execute(
                "SELECT name, current_streak FROM habits WHERE user_id = ? AND active = 1",
                (user_id,)
            ).fetchall()
            current_streaks = {row["name"]: row["current_streak"] for row in streak_rows}

        return {
            "tasks_pending": tasks_pending,
            "tasks_completed_today": tasks_completed_today,
            "active_projects": active_projects,
            "current_streaks": current_streaks,
            "generated_at": datetime.now().isoformat()
        }

    def get_tasks_due_today(self, user_id: str) -> List[Dict[str, Any]]:
        today = date.today()
        today_end = datetime.combine(today, datetime.max.time())
        return self.get_tasks(user_id, status=None, due_before=today_end)

    def get_habits_due_today(self, user_id: str) -> List[Dict[str, Any]]:
        today = date.today()
        habits = self.get_habits(user_id, active_only=True)

        due_today = []
        for habit in habits:
            last_logged = habit.get("last_logged")
            if last_logged:
                if isinstance(last_logged, str):
                    last_logged = date.fromisoformat(last_logged)
                if last_logged < today:
                    habit["logged_today"] = False
                    due_today.append(habit)
            else:
                habit["logged_today"] = False
                due_today.append(habit)

        return due_today

    def get_project_health(self, user_id: str) -> List[Dict[str, Any]]:
        projects = self.get_projects(user_id, status="active")
        return [{
            "project_id": p["project_id"],
            "name": p["name"],
            "role": p["role"],
            "task_count": p["task_count"],
            "completed_task_count": p["completed_task_count"],
            "health_score": p["health_score"]
        } for p in projects]

    # ------------------------------------------
    # NOTIFICATIONS & SCHEDULING
    # ------------------------------------------

    def schedule_notification(self, user_id: str, notification_type: str,
                              title: str, content: str, trigger_time: datetime,
                              context: Optional[Dict] = None) -> Optional[str]:
        notification_id = str(uuid.uuid4())
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO scheduled_notifications
                    (notification_id, user_id, notification_type, title, content, trigger_time, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (notification_id, user_id, notification_type, title, content, trigger_time, self._json_dumps(context or {}))
                )
            return notification_id
        except Exception as e:
            print(f"Error scheduling notification: {e}")
            return None

    def get_pending_notifications(self, user_id: Optional[str] = None,
                                   before: Optional[datetime] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            query = """
                SELECT notification_id, user_id, notification_type, title, content, trigger_time, context
                FROM scheduled_notifications
                WHERE status = 'pending'
            """
            params = []

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            if before:
                query += " AND trigger_time <= ?"
                params.append(before)

            query += " ORDER BY trigger_time ASC"

            rows = conn.execute(query, params).fetchall()
            return [{
                "notification_id": row["notification_id"],
                "user_id": row["user_id"],
                "notification_type": row["notification_type"],
                "title": row["title"],
                "content": row["content"],
                "trigger_time": row["trigger_time"],
                "context": self._json_loads(row["context"])
            } for row in rows]

    def mark_notification_sent(self, notification_id: str) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "UPDATE scheduled_notifications SET status = 'sent', sent_at = CURRENT_TIMESTAMP WHERE notification_id = ?",
                    (notification_id,)
                )
            return True
        except Exception as e:
            print(f"Error marking notification sent: {e}")
            return False

    # ------------------------------------------
    # INTEGRATION CREDENTIALS (OAuth)
    # ------------------------------------------

    def save_integration_credentials(
        self,
        user_id: str,
        integration_name: str,
        credentials: Dict[str, Any]
    ) -> bool:
        """Save OAuth credentials for an integration."""
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO integration_credentials
                    (user_id, integration_name, access_token, refresh_token, token_type,
                     expires_at, scope, credentials, connected_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        user_id,
                        integration_name,
                        credentials.get("access_token"),
                        credentials.get("refresh_token"),
                        credentials.get("token_type", "Bearer"),
                        credentials.get("expires_at"),
                        credentials.get("scope", ""),
                        self._json_dumps(credentials),
                        credentials.get("connected_at", datetime.now().isoformat())
                    )
                )
            return True
        except Exception as e:
            print(f"Error saving integration credentials: {e}")
            return False

    def get_integration_credentials(
        self,
        user_id: str,
        integration_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get OAuth credentials for an integration."""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT access_token, refresh_token, token_type, expires_at,
                       scope, credentials, connected_at, updated_at
                FROM integration_credentials
                WHERE user_id = ? AND integration_name = ?
                """,
                (user_id, integration_name)
            ).fetchone()

            if row:
                result = self._json_loads(row["credentials"])
                result.update({
                    "access_token": row["access_token"],
                    "refresh_token": row["refresh_token"],
                    "token_type": row["token_type"],
                    "expires_at": row["expires_at"],
                    "scope": row["scope"],
                    "connected_at": row["connected_at"],
                    "updated_at": row["updated_at"]
                })
                return result
        return None

    def delete_integration_credentials(
        self,
        user_id: str,
        integration_name: str
    ) -> bool:
        """Delete OAuth credentials for an integration."""
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "DELETE FROM integration_credentials WHERE user_id = ? AND integration_name = ?",
                    (user_id, integration_name)
                )
            return True
        except Exception as e:
            print(f"Error deleting integration credentials: {e}")
            return False

    def get_user_integrations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all connected integrations for a user."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT integration_name, connected_at, updated_at, scope
                FROM integration_credentials
                WHERE user_id = ?
                ORDER BY connected_at DESC
                """,
                (user_id,)
            ).fetchall()

            return [{
                "integration_name": row["integration_name"],
                "connected_at": row["connected_at"],
                "updated_at": row["updated_at"],
                "scope": row["scope"]
            } for row in rows]
