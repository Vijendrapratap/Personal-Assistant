"""
Unit tests for TaskService.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, date


class MockTaskStorage:
    """Mock storage for task testing."""

    def __init__(self):
        self.tasks = {}
        self.task_counter = 0

    def create_task(
        self,
        user_id: str,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date=None,
        project_id: str = None,
        tags: list = None,
        source: str = "user",
    ) -> str:
        self.task_counter += 1
        task_id = f"task-{self.task_counter}"
        self.tasks[task_id] = {
            "id": task_id,
            "user_id": user_id,
            "title": title,
            "description": description,
            "priority": priority,
            "due_date": due_date,
            "project_id": project_id,
            "tags": tags or [],
            "source": source,
            "status": "pending",
            "created_at": datetime.now(),
            "completed_at": None,
        }
        return task_id

    def get_task(self, task_id: str, user_id: str):
        task = self.tasks.get(task_id)
        if task and task["user_id"] == user_id:
            return task
        return None

    def get_tasks(
        self,
        user_id: str,
        status: str = None,
        priority: str = None,
        project_id: str = None,
        due_before=None,
    ) -> list:
        result = []
        for task in self.tasks.values():
            if task["user_id"] != user_id:
                continue
            if status and task["status"] != status:
                continue
            if priority and task["priority"] != priority:
                continue
            if project_id and task.get("project_id") != project_id:
                continue
            if due_before and task.get("due_date"):
                if task["due_date"] >= due_before:
                    continue
            result.append(task)
        return result

    def get_tasks_due_today(self, user_id: str) -> list:
        today = date.today()
        result = []
        for task in self.tasks.values():
            if task["user_id"] != user_id:
                continue
            if task["status"] != "pending":
                continue
            if task.get("due_date"):
                due = task["due_date"]
                if isinstance(due, datetime):
                    due = due.date()
                if due == today:
                    result.append(task)
        return result

    def update_task(self, task_id: str, user_id: str, updates: dict) -> bool:
        task = self.tasks.get(task_id)
        if task and task["user_id"] == user_id:
            task.update(updates)
            return True
        return False

    def complete_task(self, task_id: str, user_id: str) -> bool:
        task = self.tasks.get(task_id)
        if task and task["user_id"] == user_id:
            task["status"] = "completed"
            task["completed_at"] = datetime.now()
            return True
        return False

    def delete_task(self, task_id: str, user_id: str) -> bool:
        task = self.tasks.get(task_id)
        if task and task["user_id"] == user_id:
            del self.tasks[task_id]
            return True
        return False


class TestTaskService:
    """Tests for TaskService."""

    @pytest.fixture
    def mock_storage(self):
        return MockTaskStorage()

    @pytest.fixture
    def task_service(self, mock_storage):
        """Create TaskService instance with mock storage."""
        from alfred.core.services.task_service import TaskService

        return TaskService(storage=mock_storage)

    @pytest.mark.unit
    def test_task_service_instantiation(self, task_service):
        """TaskService should instantiate with storage."""
        assert task_service is not None
        assert task_service.storage is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_task_returns_task_id(self, task_service):
        """create_task should return a task ID."""
        task_id = await task_service.create_task(
            user_id="user-123",
            title="Test task",
        )

        assert task_id is not None
        assert task_id.startswith("task-")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_task_with_all_fields(self, task_service):
        """create_task should accept all optional fields."""
        due_date = datetime.now() + timedelta(days=1)

        task_id = await task_service.create_task(
            user_id="user-123",
            title="Complete project",
            description="Finish the Alfred project",
            priority="high",
            due_date=due_date,
            project_id="proj-456",
            tags=["work", "important"],
            source="alfred",
        )

        assert task_id is not None

        task = await task_service.get_task("user-123", task_id)
        assert task["title"] == "Complete project"
        assert task["description"] == "Finish the Alfred project"
        assert task["priority"] == "high"
        assert task["due_date"] == due_date
        assert task["project_id"] == "proj-456"
        assert "work" in task["tags"]
        assert task["source"] == "alfred"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_task_by_id(self, task_service):
        """get_task should retrieve task by ID."""
        task_id = await task_service.create_task(
            user_id="user-123",
            title="My task",
        )

        task = await task_service.get_task("user-123", task_id)

        assert task is not None
        assert task["id"] == task_id
        assert task["title"] == "My task"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_task_wrong_user(self, task_service):
        """get_task should not return tasks for wrong user."""
        task_id = await task_service.create_task(
            user_id="user-123",
            title="Private task",
        )

        task = await task_service.get_task("user-999", task_id)

        assert task is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tasks_returns_all(self, task_service):
        """get_tasks should return all user's tasks."""
        await task_service.create_task(user_id="user-123", title="Task 1")
        await task_service.create_task(user_id="user-123", title="Task 2")
        await task_service.create_task(user_id="user-123", title="Task 3")

        tasks = await task_service.get_tasks(user_id="user-123")

        assert len(tasks) == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tasks_filter_by_status(self, task_service):
        """get_tasks should filter by status."""
        task_id = await task_service.create_task(
            user_id="user-123", title="Task 1"
        )
        await task_service.create_task(user_id="user-123", title="Task 2")
        await task_service.complete_task("user-123", task_id)

        pending_tasks = await task_service.get_tasks(
            user_id="user-123", status="pending"
        )
        completed_tasks = await task_service.get_tasks(
            user_id="user-123", status="completed"
        )

        assert len(pending_tasks) == 1
        assert len(completed_tasks) == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tasks_filter_by_priority(self, task_service):
        """get_tasks should filter by priority."""
        await task_service.create_task(
            user_id="user-123", title="High task", priority="high"
        )
        await task_service.create_task(
            user_id="user-123", title="Low task", priority="low"
        )

        high_tasks = await task_service.get_tasks(
            user_id="user-123", priority="high"
        )

        assert len(high_tasks) == 1
        assert high_tasks[0]["title"] == "High task"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tasks_respects_limit(self, task_service):
        """get_tasks should respect limit parameter."""
        for i in range(10):
            await task_service.create_task(user_id="user-123", title=f"Task {i}")

        tasks = await task_service.get_tasks(user_id="user-123", limit=5)

        assert len(tasks) == 5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tasks_due_today(self, task_service, mock_storage):
        """get_tasks_due_today should return today's tasks."""
        today = datetime.combine(date.today(), datetime.min.time())
        tomorrow = today + timedelta(days=1)

        await task_service.create_task(
            user_id="user-123", title="Due today", due_date=today
        )
        await task_service.create_task(
            user_id="user-123", title="Due tomorrow", due_date=tomorrow
        )

        today_tasks = await task_service.get_tasks_due_today("user-123")

        assert len(today_tasks) == 1
        assert today_tasks[0]["title"] == "Due today"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_task(self, task_service):
        """update_task should modify task fields."""
        task_id = await task_service.create_task(
            user_id="user-123", title="Original title"
        )

        success = await task_service.update_task(
            user_id="user-123",
            task_id=task_id,
            updates={"title": "Updated title", "priority": "high"},
        )

        assert success is True

        task = await task_service.get_task("user-123", task_id)
        assert task["title"] == "Updated title"
        assert task["priority"] == "high"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_task_wrong_user(self, task_service):
        """update_task should fail for wrong user."""
        task_id = await task_service.create_task(
            user_id="user-123", title="Private task"
        )

        success = await task_service.update_task(
            user_id="user-999",
            task_id=task_id,
            updates={"title": "Hacked!"},
        )

        assert success is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_complete_task(self, task_service):
        """complete_task should mark task as completed."""
        task_id = await task_service.create_task(
            user_id="user-123", title="To complete"
        )

        success = await task_service.complete_task("user-123", task_id)

        assert success is True

        task = await task_service.get_task("user-123", task_id)
        assert task["status"] == "completed"
        assert task["completed_at"] is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_complete_task_wrong_user(self, task_service):
        """complete_task should fail for wrong user."""
        task_id = await task_service.create_task(
            user_id="user-123", title="Private task"
        )

        success = await task_service.complete_task("user-999", task_id)

        assert success is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_task(self, task_service):
        """delete_task should remove task."""
        task_id = await task_service.create_task(
            user_id="user-123", title="To delete"
        )

        success = await task_service.delete_task("user-123", task_id)

        assert success is True

        task = await task_service.get_task("user-123", task_id)
        assert task is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_task_wrong_user(self, task_service):
        """delete_task should fail for wrong user."""
        task_id = await task_service.create_task(
            user_id="user-123", title="Private task"
        )

        success = await task_service.delete_task("user-999", task_id)

        assert success is False

        # Task should still exist
        task = await task_service.get_task("user-123", task_id)
        assert task is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_task_stats(self, task_service):
        """get_task_stats should return task statistics."""
        # Create tasks
        task1 = await task_service.create_task(
            user_id="user-123", title="Task 1"
        )
        task2 = await task_service.create_task(
            user_id="user-123", title="Task 2"
        )
        await task_service.create_task(user_id="user-123", title="Task 3")

        # Complete some
        await task_service.complete_task("user-123", task1)
        await task_service.complete_task("user-123", task2)

        stats = await task_service.get_task_stats("user-123")

        assert stats["total_tasks"] == 3
        assert stats["pending_tasks"] == 1
        assert stats["completed_tasks"] == 2
        assert stats["completion_rate"] == pytest.approx(66.67, rel=0.1)


class TestTaskServiceEdgeCases:
    """Edge case tests for TaskService."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_without_storage_raises_error(self):
        """Service without storage should raise RuntimeError."""
        from alfred.core.services.task_service import TaskService

        service = TaskService(storage=None)

        with pytest.raises(RuntimeError, match="Storage not configured"):
            await service.create_task(user_id="user-123", title="Test")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tasks_empty(self):
        """get_tasks should return empty list for new user."""
        from alfred.core.services.task_service import TaskService

        service = TaskService(storage=MockTaskStorage())

        tasks = await service.get_tasks(user_id="new-user")

        assert tasks == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self):
        """get_task should return None for nonexistent task."""
        from alfred.core.services.task_service import TaskService

        service = TaskService(storage=MockTaskStorage())

        task = await service.get_task("user-123", "nonexistent-task-id")

        assert task is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_task_stats_empty(self):
        """get_task_stats should handle empty task list."""
        from alfred.core.services.task_service import TaskService

        service = TaskService(storage=MockTaskStorage())

        stats = await service.get_task_stats("user-123")

        assert stats["total_tasks"] == 0
        assert stats["completion_rate"] == 0
