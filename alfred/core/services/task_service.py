"""
Task Service.

Business logic for task management.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
import uuid

from alfred.core.services.base import BaseService


class TaskService(BaseService):
    """
    Task management service.

    Handles:
    - Task CRUD operations
    - Task filtering and queries
    - Task completion and status updates
    - Task analytics
    """

    async def create_task(
        self,
        user_id: str,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: Optional[datetime] = None,
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: str = "user",
    ) -> Optional[str]:
        """
        Create a new task.

        Returns:
            task_id if successful, None otherwise
        """
        self._ensure_storage()

        task_id = self.storage.create_task(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            project_id=project_id,
            tags=tags,
            source=source,
        )

        if task_id:
            self._log_action("CREATE_TASK", user_id, f"task_id={task_id}")

        return task_id

    async def get_task(
        self,
        user_id: str,
        task_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a single task by ID."""
        self._ensure_storage()
        return self.storage.get_task(task_id, user_id)

    async def get_tasks(
        self,
        user_id: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        project_id: Optional[str] = None,
        due_before: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get tasks with filters.

        Args:
            user_id: User ID
            status: Filter by status (pending, completed, etc.)
            priority: Filter by priority
            project_id: Filter by project
            due_before: Filter by due date
            limit: Maximum results

        Returns:
            List of tasks
        """
        self._ensure_storage()

        tasks = self.storage.get_tasks(
            user_id=user_id,
            status=status,
            priority=priority,
            project_id=project_id,
            due_before=due_before,
        )

        return tasks[:limit]

    async def get_tasks_due_today(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tasks due today."""
        self._ensure_storage()
        return self.storage.get_tasks_due_today(user_id)

    async def get_overdue_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all overdue tasks."""
        self._ensure_storage()

        now = datetime.now()
        tasks = self.storage.get_tasks(
            user_id=user_id,
            status="pending",
            due_before=now,
        )

        # Filter to only overdue (not due today)
        today_start = datetime.combine(date.today(), datetime.min.time())
        return [t for t in tasks if t.get("due_date") and t["due_date"] < today_start]

    async def update_task(
        self,
        user_id: str,
        task_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update a task."""
        self._ensure_storage()

        success = self.storage.update_task(task_id, user_id, updates)
        if success:
            self._log_action("UPDATE_TASK", user_id, f"task_id={task_id}")
        return success

    async def complete_task(
        self,
        user_id: str,
        task_id: str,
    ) -> bool:
        """Mark a task as completed."""
        self._ensure_storage()

        success = self.storage.complete_task(task_id, user_id)
        if success:
            self._log_action("COMPLETE_TASK", user_id, f"task_id={task_id}")

            # Check if this was a project task and update project
            task = self.storage.get_task(task_id, user_id)
            if task and task.get("project_id"):
                # Could trigger project progress update here
                pass

        return success

    async def delete_task(
        self,
        user_id: str,
        task_id: str,
    ) -> bool:
        """Delete a task."""
        self._ensure_storage()

        success = self.storage.delete_task(task_id, user_id)
        if success:
            self._log_action("DELETE_TASK", user_id, f"task_id={task_id}")
        return success

    async def get_task_stats(
        self,
        user_id: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get task statistics for the user.

        Returns stats like:
        - Tasks completed this week
        - Completion rate
        - Most productive day
        """
        self._ensure_storage()

        # Get all tasks
        all_tasks = self.storage.get_tasks(user_id=user_id)
        pending_tasks = [t for t in all_tasks if t.get("status") == "pending"]
        completed_tasks = [t for t in all_tasks if t.get("status") == "completed"]

        # Calculate recent completions
        cutoff = datetime.now() - timedelta(days=days)
        recent_completed = [
            t for t in completed_tasks
            if t.get("completed_at") and t["completed_at"] > cutoff
        ]

        return {
            "total_tasks": len(all_tasks),
            "pending_tasks": len(pending_tasks),
            "completed_tasks": len(completed_tasks),
            "completed_this_week": len(recent_completed),
            "completion_rate": (
                len(completed_tasks) / len(all_tasks) * 100
                if all_tasks else 0
            ),
        }
