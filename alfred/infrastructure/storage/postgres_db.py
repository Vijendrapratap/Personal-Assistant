from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
import uuid
import psycopg
from psycopg.types.json import Json
from alfred.core.interfaces import MemoryStorage


class PostgresAdapter(MemoryStorage):
    """
    PostgreSQL implementation of the MemoryStorage interface.
    Handles all persistent storage for Alfred.
    """

    def __init__(self, db_url: str):
        self.db_url = db_url
        self._init_db()

    def _get_conn(self):
        """Get a database connection."""
        return psycopg.connect(self.db_url)

    def _init_db(self):
        """Create all necessary tables if they don't exist."""
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                # Users table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id VARCHAR(255) PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        profile JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Chat history
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255),
                        role VARCHAR(50),
                        content TEXT,
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat_history(user_id);
                """)

                # User preferences
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        user_id VARCHAR(255),
                        key VARCHAR(255),
                        value TEXT,
                        confidence FLOAT DEFAULT 1.0,
                        learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, key)
                    );
                """)

                # Projects table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        project_id VARCHAR(255) PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        organization VARCHAR(255) DEFAULT '',
                        role VARCHAR(50) DEFAULT 'contributor',
                        status VARCHAR(50) DEFAULT 'active',
                        description TEXT DEFAULT '',
                        integrations JSONB DEFAULT '{}',
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
                    CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
                """)

                # Project updates
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS project_updates (
                        update_id VARCHAR(255) PRIMARY KEY,
                        project_id VARCHAR(255) NOT NULL,
                        user_id VARCHAR(255) NOT NULL,
                        content TEXT NOT NULL,
                        update_type VARCHAR(50) DEFAULT 'progress',
                        action_items JSONB DEFAULT '[]',
                        blockers JSONB DEFAULT '[]',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_updates_project ON project_updates(project_id);
                """)

                # Tasks table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id VARCHAR(255) PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        project_id VARCHAR(255),
                        title TEXT NOT NULL,
                        description TEXT DEFAULT '',
                        priority VARCHAR(20) DEFAULT 'medium',
                        status VARCHAR(20) DEFAULT 'pending',
                        due_date TIMESTAMP,
                        recurrence VARCHAR(50),
                        blockers JSONB DEFAULT '[]',
                        tags JSONB DEFAULT '[]',
                        source VARCHAR(50) DEFAULT 'user',
                        source_ref VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
                    CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
                    CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                    CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
                """)

                # Habits table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS habits (
                        habit_id VARCHAR(255) PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        description TEXT DEFAULT '',
                        frequency VARCHAR(50) DEFAULT 'daily',
                        time_preference VARCHAR(10),
                        days_of_week JSONB DEFAULT '[]',
                        current_streak INT DEFAULT 0,
                        best_streak INT DEFAULT 0,
                        total_completions INT DEFAULT 0,
                        last_logged DATE,
                        motivation TEXT DEFAULT '',
                        category VARCHAR(50) DEFAULT 'general',
                        active BOOLEAN DEFAULT true,
                        reminder_enabled BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_habits_user_id ON habits(user_id);
                """)

                # Habit logs
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS habit_logs (
                        log_id VARCHAR(255) PRIMARY KEY,
                        habit_id VARCHAR(255) NOT NULL,
                        user_id VARCHAR(255) NOT NULL,
                        logged_date DATE NOT NULL,
                        notes TEXT DEFAULT '',
                        duration_minutes INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(habit_id, logged_date)
                    );
                    CREATE INDEX IF NOT EXISTS idx_habit_logs_habit ON habit_logs(habit_id);
                """)

                # Scheduled notifications
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS scheduled_notifications (
                        notification_id VARCHAR(255) PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        notification_type VARCHAR(50) NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        trigger_time TIMESTAMP NOT NULL,
                        context JSONB DEFAULT '{}',
                        status VARCHAR(20) DEFAULT 'pending',
                        sent_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_notifications_user ON scheduled_notifications(user_id);
                    CREATE INDEX IF NOT EXISTS idx_notifications_trigger ON scheduled_notifications(trigger_time);
                    CREATE INDEX IF NOT EXISTS idx_notifications_status ON scheduled_notifications(status);
                """)

                # Knowledge/learnings table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS learnings (
                        learning_id VARCHAR(255) PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        topic VARCHAR(255) DEFAULT 'general',
                        content TEXT NOT NULL,
                        original_query TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_learnings_user ON learnings(user_id);
                """)

            conn.commit()

    # ------------------------------------------
    # USER MANAGEMENT
    # ------------------------------------------

    def create_user(self, user_id: str, email: str, password_hash: str) -> bool:
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (user_id, email, password_hash) VALUES (%s, %s, %s)",
                        (user_id, email, password_hash)
                    )
            return True
        except psycopg.errors.UniqueViolation:
            return False
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    def get_user_credentials(self, email: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, password_hash FROM users WHERE email = %s",
                    (email,)
                )
                row = cur.fetchone()
                if row:
                    return {"user_id": row[0], "password_hash": row[1]}
        return None

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT profile FROM users WHERE user_id = %s",
                    (user_id,)
                )
                row = cur.fetchone()
                if row:
                    return row[0] if row[0] else {}
        return None

    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT profile FROM users WHERE user_id = %s", (user_id,))
                    row = cur.fetchone()
                    current_profile = row[0] if row and row[0] else {}
                    updated_profile = {**current_profile, **profile_data}
                    cur.execute(
                        "UPDATE users SET profile = %s WHERE user_id = %s",
                        (Json(updated_profile), user_id)
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
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO chat_history (user_id, role, content, metadata) VALUES (%s, %s, %s, %s)",
                        (user_id, role, content, Json(metadata or {}))
                    )
            return True
        except Exception as e:
            print(f"Error saving chat: {e}")
            return False

    def get_chat_history(self, user_id: str, limit: int = 20) -> List[Dict[str, str]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role, content FROM chat_history
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (user_id, limit)
                )
                rows = cur.fetchall()
                # Reverse to get chronological order
                return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

    # ------------------------------------------
    # PREFERENCES & LEARNING
    # ------------------------------------------

    def save_preference(self, user_id: str, key: str, value: str, confidence: float = 1.0) -> bool:
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO user_preferences (user_id, key, value, confidence)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (user_id, key)
                        DO UPDATE SET value = EXCLUDED.value, confidence = EXCLUDED.confidence,
                                      learned_at = CURRENT_TIMESTAMP
                        """,
                        (user_id, key, value, confidence)
                    )
            return True
        except Exception as e:
            print(f"Error saving preference: {e}")
            return False

    def get_preferences(self, user_id: str) -> Dict[str, str]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT key, value FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                return {row[0]: row[1] for row in cur.fetchall()}

    def save_learning(self, user_id: str, content: str, original_query: Optional[str] = None) -> bool:
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO learnings (learning_id, user_id, content, original_query)
                        VALUES (%s, %s, %s, %s)
                        """,
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
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO projects (project_id, user_id, name, organization, role, description, integrations)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (project_id, user_id, name, organization, role, description, Json(integrations or {}))
                    )
            return project_id
        except Exception as e:
            print(f"Error creating project: {e}")
            return None

    def get_project(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT project_id, user_id, name, organization, role, status,
                           description, integrations, metadata, created_at, updated_at
                    FROM projects
                    WHERE project_id = %s AND user_id = %s
                    """,
                    (project_id, user_id)
                )
                row = cur.fetchone()
                if row:
                    # Get task counts
                    cur.execute(
                        "SELECT COUNT(*), SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) FROM tasks WHERE project_id = %s",
                        (project_id,)
                    )
                    task_row = cur.fetchone()
                    task_count = task_row[0] or 0
                    completed_count = task_row[1] or 0

                    return {
                        "project_id": row[0],
                        "user_id": row[1],
                        "name": row[2],
                        "organization": row[3],
                        "role": row[4],
                        "status": row[5],
                        "description": row[6],
                        "integrations": row[7],
                        "metadata": row[8],
                        "created_at": row[9].isoformat() if row[9] else None,
                        "updated_at": row[10].isoformat() if row[10] else None,
                        "task_count": task_count,
                        "completed_task_count": completed_count,
                        "health_score": (completed_count / task_count * 100) if task_count > 0 else 100
                    }
        return None

    def get_projects(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                if status:
                    cur.execute(
                        """
                        SELECT project_id, name, organization, role, status, description, created_at
                        FROM projects
                        WHERE user_id = %s AND status = %s
                        ORDER BY updated_at DESC
                        """,
                        (user_id, status)
                    )
                else:
                    cur.execute(
                        """
                        SELECT project_id, name, organization, role, status, description, created_at
                        FROM projects
                        WHERE user_id = %s
                        ORDER BY updated_at DESC
                        """,
                        (user_id,)
                    )
                projects = []
                for row in cur.fetchall():
                    # Get task counts for each project
                    cur.execute(
                        "SELECT COUNT(*), SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) FROM tasks WHERE project_id = %s",
                        (row[0],)
                    )
                    task_row = cur.fetchone()
                    task_count = task_row[0] or 0
                    completed_count = task_row[1] or 0

                    projects.append({
                        "project_id": row[0],
                        "name": row[1],
                        "organization": row[2],
                        "role": row[3],
                        "status": row[4],
                        "description": row[5],
                        "created_at": row[6].isoformat() if row[6] else None,
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
                with conn.cursor() as cur:
                    set_clauses = []
                    values = []
                    for key, value in updates.items():
                        set_clauses.append(f"{key} = %s")
                        if key in ['integrations', 'metadata']:
                            values.append(Json(value))
                        else:
                            values.append(value)

                    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                    values.extend([project_id, user_id])

                    query = f"UPDATE projects SET {', '.join(set_clauses)} WHERE project_id = %s AND user_id = %s"
                    cur.execute(query, values)
            return True
        except Exception as e:
            print(f"Error updating project: {e}")
            return False

    def delete_project(self, project_id: str, user_id: str) -> bool:
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE projects SET status = 'archived' WHERE project_id = %s AND user_id = %s",
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
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO project_updates (update_id, project_id, user_id, content, update_type, action_items, blockers)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (update_id, project_id, user_id, content, update_type,
                         Json(action_items or []), Json(blockers or []))
                    )
                    # Update the project's updated_at timestamp
                    cur.execute(
                        "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE project_id = %s",
                        (project_id,)
                    )
            return update_id
        except Exception as e:
            print(f"Error adding project update: {e}")
            return None

    def get_project_updates(self, project_id: str, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT update_id, content, update_type, action_items, blockers, created_at
                    FROM project_updates
                    WHERE project_id = %s AND user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (project_id, user_id, limit)
                )
                return [{
                    "update_id": row[0],
                    "content": row[1],
                    "update_type": row[2],
                    "action_items": row[3],
                    "blockers": row[4],
                    "created_at": row[5].isoformat() if row[5] else None
                } for row in cur.fetchall()]

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
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO tasks (task_id, user_id, project_id, title, description, priority, due_date, tags, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (task_id, user_id, project_id, title, description, priority, due_date, Json(tags or []), source)
                    )
            return task_id
        except Exception as e:
            print(f"Error creating task: {e}")
            return None

    def get_task(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT t.task_id, t.user_id, t.project_id, t.title, t.description,
                           t.priority, t.status, t.due_date, t.recurrence, t.blockers,
                           t.tags, t.source, t.created_at, t.completed_at,
                           p.name as project_name
                    FROM tasks t
                    LEFT JOIN projects p ON t.project_id = p.project_id
                    WHERE t.task_id = %s AND t.user_id = %s
                    """,
                    (task_id, user_id)
                )
                row = cur.fetchone()
                if row:
                    return {
                        "task_id": row[0],
                        "user_id": row[1],
                        "project_id": row[2],
                        "title": row[3],
                        "description": row[4],
                        "priority": row[5],
                        "status": row[6],
                        "due_date": row[7].isoformat() if row[7] else None,
                        "recurrence": row[8],
                        "blockers": row[9],
                        "tags": row[10],
                        "source": row[11],
                        "created_at": row[12].isoformat() if row[12] else None,
                        "completed_at": row[13].isoformat() if row[13] else None,
                        "project_name": row[14]
                    }
        return None

    def get_tasks(self, user_id: str, project_id: Optional[str] = None,
                  status: Optional[str] = None, priority: Optional[str] = None,
                  due_before: Optional[datetime] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT t.task_id, t.project_id, t.title, t.description,
                           t.priority, t.status, t.due_date, t.tags, t.created_at,
                           p.name as project_name
                    FROM tasks t
                    LEFT JOIN projects p ON t.project_id = p.project_id
                    WHERE t.user_id = %s
                """
                params = [user_id]

                if project_id:
                    query += " AND t.project_id = %s"
                    params.append(project_id)
                if status:
                    query += " AND t.status = %s"
                    params.append(status)
                if priority:
                    query += " AND t.priority = %s"
                    params.append(priority)
                if due_before:
                    query += " AND t.due_date <= %s"
                    params.append(due_before)

                query += " ORDER BY t.due_date ASC NULLS LAST, t.priority DESC, t.created_at DESC"

                cur.execute(query, params)
                return [{
                    "task_id": row[0],
                    "project_id": row[1],
                    "title": row[2],
                    "description": row[3],
                    "priority": row[4],
                    "status": row[5],
                    "due_date": row[6].isoformat() if row[6] else None,
                    "tags": row[7],
                    "created_at": row[8].isoformat() if row[8] else None,
                    "project_name": row[9]
                } for row in cur.fetchall()]

    def update_task(self, task_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        allowed_fields = ['title', 'description', 'priority', 'status', 'due_date', 'recurrence', 'blockers', 'tags', 'project_id']
        updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not updates:
            return False

        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    set_clauses = []
                    values = []
                    for key, value in updates.items():
                        set_clauses.append(f"{key} = %s")
                        if key in ['blockers', 'tags']:
                            values.append(Json(value))
                        else:
                            values.append(value)

                    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                    values.extend([task_id, user_id])

                    query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE task_id = %s AND user_id = %s"
                    cur.execute(query, values)
            return True
        except Exception as e:
            print(f"Error updating task: {e}")
            return False

    def complete_task(self, task_id: str, user_id: str) -> bool:
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE tasks
                        SET status = 'completed', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                        WHERE task_id = %s AND user_id = %s
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
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM tasks WHERE task_id = %s AND user_id = %s",
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
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO habits (habit_id, user_id, name, description, frequency, time_preference, motivation, category)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (habit_id, user_id, name, description, frequency, time_preference, motivation, category)
                    )
            return habit_id
        except Exception as e:
            print(f"Error creating habit: {e}")
            return None

    def get_habit(self, habit_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT habit_id, user_id, name, description, frequency, time_preference,
                           current_streak, best_streak, total_completions, last_logged,
                           motivation, category, active, reminder_enabled, created_at
                    FROM habits
                    WHERE habit_id = %s AND user_id = %s
                    """,
                    (habit_id, user_id)
                )
                row = cur.fetchone()
                if row:
                    return {
                        "habit_id": row[0],
                        "user_id": row[1],
                        "name": row[2],
                        "description": row[3],
                        "frequency": row[4],
                        "time_preference": row[5],
                        "current_streak": row[6],
                        "best_streak": row[7],
                        "total_completions": row[8],
                        "last_logged": row[9].isoformat() if row[9] else None,
                        "motivation": row[10],
                        "category": row[11],
                        "active": row[12],
                        "reminder_enabled": row[13],
                        "created_at": row[14].isoformat() if row[14] else None
                    }
        return None

    def get_habits(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT habit_id, name, description, frequency, time_preference,
                           current_streak, best_streak, total_completions, last_logged,
                           motivation, category, active, reminder_enabled
                    FROM habits
                    WHERE user_id = %s
                """
                if active_only:
                    query += " AND active = true"
                query += " ORDER BY created_at ASC"

                cur.execute(query, (user_id,))
                return [{
                    "habit_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "frequency": row[3],
                    "time_preference": row[4],
                    "current_streak": row[5],
                    "best_streak": row[6],
                    "total_completions": row[7],
                    "last_logged": row[8].isoformat() if row[8] else None,
                    "motivation": row[9],
                    "category": row[10],
                    "active": row[11],
                    "reminder_enabled": row[12]
                } for row in cur.fetchall()]

    def update_habit(self, habit_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        allowed_fields = ['name', 'description', 'frequency', 'time_preference', 'motivation', 'category', 'active', 'reminder_enabled']
        updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not updates:
            return False

        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    set_clauses = [f"{key} = %s" for key in updates.keys()]
                    values = list(updates.values())
                    values.extend([habit_id, user_id])

                    query = f"UPDATE habits SET {', '.join(set_clauses)} WHERE habit_id = %s AND user_id = %s"
                    cur.execute(query, values)
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
                with conn.cursor() as cur:
                    # Insert the log
                    cur.execute(
                        """
                        INSERT INTO habit_logs (log_id, habit_id, user_id, logged_date, notes, duration_minutes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (habit_id, logged_date) DO UPDATE SET notes = EXCLUDED.notes, duration_minutes = EXCLUDED.duration_minutes
                        """,
                        (log_id, habit_id, user_id, logged_date, notes, duration_minutes)
                    )

                    # Get current habit data
                    cur.execute(
                        "SELECT current_streak, best_streak, total_completions, last_logged FROM habits WHERE habit_id = %s",
                        (habit_id,)
                    )
                    row = cur.fetchone()
                    if row:
                        current_streak = row[0] or 0
                        best_streak = row[1] or 0
                        total_completions = row[2] or 0
                        last_logged = row[3]

                        # Calculate new streak
                        if last_logged:
                            days_diff = (logged_date - last_logged).days
                            if days_diff == 1:
                                current_streak += 1
                            elif days_diff > 1:
                                current_streak = 1
                            # If same day, don't change streak
                        else:
                            current_streak = 1

                        # Update best streak if needed
                        if current_streak > best_streak:
                            best_streak = current_streak

                        # Update habit
                        cur.execute(
                            """
                            UPDATE habits
                            SET current_streak = %s, best_streak = %s, total_completions = %s, last_logged = %s
                            WHERE habit_id = %s
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
            with conn.cursor() as cur:
                query = """
                    SELECT log_id, logged_date, notes, duration_minutes, created_at
                    FROM habit_logs
                    WHERE habit_id = %s AND user_id = %s
                """
                params = [habit_id, user_id]

                if start_date:
                    query += " AND logged_date >= %s"
                    params.append(start_date)
                if end_date:
                    query += " AND logged_date <= %s"
                    params.append(end_date)

                query += " ORDER BY logged_date DESC"

                cur.execute(query, params)
                return [{
                    "log_id": row[0],
                    "logged_date": row[1].isoformat() if row[1] else None,
                    "notes": row[2],
                    "duration_minutes": row[3],
                    "created_at": row[4].isoformat() if row[4] else None
                } for row in cur.fetchall()]

    def delete_habit(self, habit_id: str, user_id: str) -> bool:
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE habits SET active = false WHERE habit_id = %s AND user_id = %s",
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
            with conn.cursor() as cur:
                # Tasks stats
                cur.execute(
                    """
                    SELECT
                        COUNT(*) FILTER (WHERE status != 'completed' AND status != 'cancelled') as pending,
                        COUNT(*) FILTER (WHERE status = 'completed' AND completed_at >= %s AND completed_at <= %s) as completed_today
                    FROM tasks WHERE user_id = %s
                    """,
                    (today_start, today_end, user_id)
                )
                task_row = cur.fetchone()
                tasks_pending = task_row[0] or 0
                tasks_completed_today = task_row[1] or 0

                # Active projects
                cur.execute(
                    "SELECT COUNT(*) FROM projects WHERE user_id = %s AND status = 'active'",
                    (user_id,)
                )
                active_projects = cur.fetchone()[0] or 0

                # Current streaks
                cur.execute(
                    "SELECT name, current_streak FROM habits WHERE user_id = %s AND active = true",
                    (user_id,)
                )
                current_streaks = {row[0]: row[1] for row in cur.fetchall()}

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
                last_logged_date = date.fromisoformat(last_logged) if isinstance(last_logged, str) else last_logged
                if last_logged_date < today:
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
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO scheduled_notifications
                        (notification_id, user_id, notification_type, title, content, trigger_time, context)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (notification_id, user_id, notification_type, title, content, trigger_time, Json(context or {}))
                    )
            return notification_id
        except Exception as e:
            print(f"Error scheduling notification: {e}")
            return None

    def get_pending_notifications(self, user_id: Optional[str] = None,
                                   before: Optional[datetime] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT notification_id, user_id, notification_type, title, content, trigger_time, context
                    FROM scheduled_notifications
                    WHERE status = 'pending'
                """
                params = []

                if user_id:
                    query += " AND user_id = %s"
                    params.append(user_id)
                if before:
                    query += " AND trigger_time <= %s"
                    params.append(before)

                query += " ORDER BY trigger_time ASC"

                cur.execute(query, params)
                return [{
                    "notification_id": row[0],
                    "user_id": row[1],
                    "notification_type": row[2],
                    "title": row[3],
                    "content": row[4],
                    "trigger_time": row[5].isoformat() if row[5] else None,
                    "context": row[6]
                } for row in cur.fetchall()]

    def mark_notification_sent(self, notification_id: str) -> bool:
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE scheduled_notifications SET status = 'sent', sent_at = CURRENT_TIMESTAMP WHERE notification_id = %s",
                        (notification_id,)
                    )
            return True
        except Exception as e:
            print(f"Error marking notification sent: {e}")
            return False
