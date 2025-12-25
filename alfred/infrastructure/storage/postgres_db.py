from typing import List, Dict, Optional
import os
import psycopg
from alfred.core.interfaces import MemoryStorage

class PostgresAdapter(MemoryStorage):
    def __init__(self, db_url: str):
        self.db_url = db_url
        self._init_db()

    def _init_db(self):
        # Create necessary tables if not exist
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255),
                        role VARCHAR(50),
                        content TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        user_id VARCHAR(255),
                        key VARCHAR(255),
                        value TEXT,
                        PRIMARY KEY (user_id, key)
                    );
                """)
            conn.commit()

    def save_chat(self, user_id: str, role: str, content: str):
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_history (user_id, role, content) VALUES (%s, %s, %s)",
                    (user_id, role, content)
                )

    def get_chat_history(self, user_id: str, limit: int = 10) -> List[Dict[str, str]]:
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role, content FROM chat_history 
                    WHERE user_id = %s 
                    ORDER BY created_at ASC
                    """,
                    (user_id,)
                )
                rows = cur.fetchall()
                # Return standard dict format
                return [{"role": row[0], "content": row[1]} for row in rows]

    def save_preference(self, user_id: str, key: str, value: str):
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO user_preferences (user_id, key, value)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, key) 
                    DO UPDATE SET value = EXCLUDED.value
                    """,
                    (user_id, key, value)
                )

    def get_preferences(self, user_id: str) -> Dict[str, str]:
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT key, value FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                return {row[0]: row[1] for row in cur.fetchall()}
