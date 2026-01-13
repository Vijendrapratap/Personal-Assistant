"""
Unit tests for HabitService.
"""

import pytest
from datetime import datetime, date, timedelta


class MockHabitStorage:
    """Mock storage for habit testing."""

    def __init__(self):
        self.habits = {}
        self.habit_logs = []
        self.habit_counter = 0

    def create_habit(
        self,
        user_id: str,
        name: str,
        frequency: str = "daily",
        description: str = "",
        time_preference: str = None,
        motivation: str = "",
        category: str = "general",
    ) -> str:
        self.habit_counter += 1
        habit_id = f"habit-{self.habit_counter}"
        self.habits[habit_id] = {
            "id": habit_id,
            "user_id": user_id,
            "name": name,
            "frequency": frequency,
            "description": description,
            "time_preference": time_preference,
            "motivation": motivation,
            "category": category,
            "current_streak": 0,
            "longest_streak": 0,
            "active": True,
            "created_at": datetime.now(),
            "completed_today": False,
        }
        return habit_id

    def get_habit(self, habit_id: str, user_id: str):
        habit = self.habits.get(habit_id)
        if habit and habit["user_id"] == user_id:
            # Check if completed today
            today = date.today()
            habit["completed_today"] = any(
                log["habit_id"] == habit_id and log["logged_date"] == today
                for log in self.habit_logs
            )
            return habit
        return None

    def get_habits(self, user_id: str, active_only: bool = True) -> list:
        result = []
        for habit in self.habits.values():
            if habit["user_id"] != user_id:
                continue
            if active_only and not habit.get("active", True):
                continue
            result.append(habit)
        return result

    def get_habits_due_today(self, user_id: str) -> list:
        today = date.today()
        result = []
        for habit in self.habits.values():
            if habit["user_id"] != user_id:
                continue
            if not habit.get("active", True):
                continue
            # Check if already completed today
            completed_today = any(
                log["habit_id"] == habit["id"] and log["logged_date"] == today
                for log in self.habit_logs
            )
            habit_copy = habit.copy()
            habit_copy["completed_today"] = completed_today
            result.append(habit_copy)
        return result

    def log_habit(
        self,
        habit_id: str,
        user_id: str,
        logged_date: date = None,
        notes: str = "",
        duration_minutes: int = None,
    ) -> bool:
        habit = self.habits.get(habit_id)
        if not habit or habit["user_id"] != user_id:
            return False

        log_date = logged_date or date.today()

        # Check if already logged today
        already_logged = any(
            log["habit_id"] == habit_id and log["logged_date"] == log_date
            for log in self.habit_logs
        )
        if already_logged:
            return False

        self.habit_logs.append({
            "habit_id": habit_id,
            "user_id": user_id,
            "logged_date": log_date,
            "notes": notes,
            "duration_minutes": duration_minutes,
            "logged_at": datetime.now(),
        })

        # Update streak
        habit["current_streak"] += 1
        if habit["current_streak"] > habit["longest_streak"]:
            habit["longest_streak"] = habit["current_streak"]

        return True

    def get_habit_logs(
        self,
        habit_id: str,
        user_id: str,
        start_date: date = None,
        end_date: date = None,
    ) -> list:
        result = []
        for log in self.habit_logs:
            if log["habit_id"] != habit_id or log["user_id"] != user_id:
                continue
            if start_date and log["logged_date"] < start_date:
                continue
            if end_date and log["logged_date"] > end_date:
                continue
            result.append(log)
        return result

    def update_habit(self, habit_id: str, user_id: str, updates: dict) -> bool:
        habit = self.habits.get(habit_id)
        if habit and habit["user_id"] == user_id:
            habit.update(updates)
            return True
        return False

    def delete_habit(self, habit_id: str, user_id: str) -> bool:
        habit = self.habits.get(habit_id)
        if habit and habit["user_id"] == user_id:
            habit["active"] = False
            return True
        return False


class TestHabitService:
    """Tests for HabitService."""

    @pytest.fixture
    def mock_storage(self):
        return MockHabitStorage()

    @pytest.fixture
    def habit_service(self, mock_storage):
        """Create HabitService instance with mock storage."""
        from alfred.core.services.habit_service import HabitService

        return HabitService(storage=mock_storage)

    @pytest.mark.unit
    def test_habit_service_instantiation(self, habit_service):
        """HabitService should instantiate with storage."""
        assert habit_service is not None
        assert habit_service.storage is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_habit_returns_id(self, habit_service):
        """create_habit should return a habit ID."""
        habit_id = await habit_service.create_habit(
            user_id="user-123",
            name="Morning meditation",
        )

        assert habit_id is not None
        assert habit_id.startswith("habit-")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_habit_with_all_fields(self, habit_service):
        """create_habit should accept all optional fields."""
        habit_id = await habit_service.create_habit(
            user_id="user-123",
            name="Exercise",
            frequency="daily",
            description="30 minutes of cardio",
            time_preference="morning",
            motivation="Stay healthy",
            category="health",
        )

        assert habit_id is not None

        habit = await habit_service.get_habit("user-123", habit_id)
        assert habit["name"] == "Exercise"
        assert habit["frequency"] == "daily"
        assert habit["description"] == "30 minutes of cardio"
        assert habit["time_preference"] == "morning"
        assert habit["motivation"] == "Stay healthy"
        assert habit["category"] == "health"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_habit_by_id(self, habit_service):
        """get_habit should retrieve habit by ID."""
        habit_id = await habit_service.create_habit(
            user_id="user-123",
            name="Read books",
        )

        habit = await habit_service.get_habit("user-123", habit_id)

        assert habit is not None
        assert habit["id"] == habit_id
        assert habit["name"] == "Read books"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_habit_wrong_user(self, habit_service):
        """get_habit should not return habits for wrong user."""
        habit_id = await habit_service.create_habit(
            user_id="user-123",
            name="Private habit",
        )

        habit = await habit_service.get_habit("user-999", habit_id)

        assert habit is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_habits_returns_all(self, habit_service):
        """get_habits should return all active habits."""
        await habit_service.create_habit(user_id="user-123", name="Habit 1")
        await habit_service.create_habit(user_id="user-123", name="Habit 2")
        await habit_service.create_habit(user_id="user-123", name="Habit 3")

        habits = await habit_service.get_habits(user_id="user-123")

        assert len(habits) == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_habits_excludes_inactive(self, habit_service):
        """get_habits should exclude inactive habits by default."""
        habit_id = await habit_service.create_habit(
            user_id="user-123", name="Habit 1"
        )
        await habit_service.create_habit(user_id="user-123", name="Habit 2")
        await habit_service.delete_habit("user-123", habit_id)

        active_habits = await habit_service.get_habits(
            user_id="user-123", active_only=True
        )
        all_habits = await habit_service.get_habits(
            user_id="user-123", active_only=False
        )

        assert len(active_habits) == 1
        assert len(all_habits) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_habits_due_today(self, habit_service):
        """get_habits_due_today should return today's habits."""
        await habit_service.create_habit(
            user_id="user-123", name="Daily habit", frequency="daily"
        )

        habits = await habit_service.get_habits_due_today("user-123")

        assert len(habits) == 1
        assert habits[0]["name"] == "Daily habit"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_log_habit_success(self, habit_service):
        """log_habit should mark habit as completed."""
        habit_id = await habit_service.create_habit(
            user_id="user-123", name="Test habit"
        )

        result = await habit_service.log_habit("user-123", habit_id)

        assert result["success"] is True
        assert result["current_streak"] == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_log_habit_updates_streak(self, habit_service):
        """log_habit should update streak correctly."""
        habit_id = await habit_service.create_habit(
            user_id="user-123", name="Streak habit"
        )

        # Log habit on multiple days
        yesterday = date.today() - timedelta(days=1)
        await habit_service.log_habit("user-123", habit_id, logged_date=yesterday)
        result = await habit_service.log_habit("user-123", habit_id)

        assert result["current_streak"] == 2
        assert result["longest_streak"] == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_log_habit_with_notes(self, habit_service, mock_storage):
        """log_habit should store notes."""
        habit_id = await habit_service.create_habit(
            user_id="user-123", name="Test habit"
        )

        await habit_service.log_habit(
            "user-123",
            habit_id,
            notes="Felt great today!",
            duration_minutes=30,
        )

        logs = mock_storage.get_habit_logs(habit_id, "user-123")
        assert len(logs) == 1
        assert logs[0]["notes"] == "Felt great today!"
        assert logs[0]["duration_minutes"] == 30

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_log_habit_wrong_user(self, habit_service):
        """log_habit should fail for wrong user."""
        habit_id = await habit_service.create_habit(
            user_id="user-123", name="Private habit"
        )

        result = await habit_service.log_habit("user-999", habit_id)

        assert result["success"] is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_habit_history(self, habit_service):
        """get_habit_history should return logs."""
        habit_id = await habit_service.create_habit(
            user_id="user-123", name="Test habit"
        )

        day1 = date.today() - timedelta(days=2)
        day2 = date.today() - timedelta(days=1)
        await habit_service.log_habit("user-123", habit_id, logged_date=day1)
        await habit_service.log_habit("user-123", habit_id, logged_date=day2)
        await habit_service.log_habit("user-123", habit_id)

        history = await habit_service.get_habit_history("user-123", habit_id)

        assert len(history) == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_habit_history_with_date_range(self, habit_service):
        """get_habit_history should filter by date range."""
        habit_id = await habit_service.create_habit(
            user_id="user-123", name="Test habit"
        )

        day1 = date.today() - timedelta(days=10)
        day2 = date.today() - timedelta(days=5)
        day3 = date.today()

        await habit_service.log_habit("user-123", habit_id, logged_date=day1)
        await habit_service.log_habit("user-123", habit_id, logged_date=day2)
        await habit_service.log_habit("user-123", habit_id, logged_date=day3)

        # Only get last 7 days
        start = date.today() - timedelta(days=7)
        history = await habit_service.get_habit_history(
            "user-123", habit_id, start_date=start
        )

        assert len(history) == 2  # day2 and day3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_habit(self, habit_service):
        """update_habit should modify habit fields."""
        habit_id = await habit_service.create_habit(
            user_id="user-123", name="Original name"
        )

        success = await habit_service.update_habit(
            user_id="user-123",
            habit_id=habit_id,
            updates={"name": "Updated name", "frequency": "weekly"},
        )

        assert success is True

        habit = await habit_service.get_habit("user-123", habit_id)
        assert habit["name"] == "Updated name"
        assert habit["frequency"] == "weekly"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_habit_wrong_user(self, habit_service):
        """update_habit should fail for wrong user."""
        habit_id = await habit_service.create_habit(
            user_id="user-123", name="Private habit"
        )

        success = await habit_service.update_habit(
            user_id="user-999",
            habit_id=habit_id,
            updates={"name": "Hacked!"},
        )

        assert success is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_habit(self, habit_service):
        """delete_habit should deactivate habit."""
        habit_id = await habit_service.create_habit(
            user_id="user-123", name="To delete"
        )

        success = await habit_service.delete_habit("user-123", habit_id)

        assert success is True

        # Should not appear in active habits
        active_habits = await habit_service.get_habits("user-123", active_only=True)
        assert len(active_habits) == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_habit_wrong_user(self, habit_service):
        """delete_habit should fail for wrong user."""
        habit_id = await habit_service.create_habit(
            user_id="user-123", name="Private habit"
        )

        success = await habit_service.delete_habit("user-999", habit_id)

        assert success is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_habit_stats(self, habit_service):
        """get_habit_stats should return statistics."""
        # Create habits
        habit1 = await habit_service.create_habit(
            user_id="user-123", name="Habit 1", frequency="daily"
        )
        habit2 = await habit_service.create_habit(
            user_id="user-123", name="Habit 2", frequency="daily"
        )

        # Log some completions
        await habit_service.log_habit("user-123", habit1)
        await habit_service.log_habit("user-123", habit2)

        stats = await habit_service.get_habit_stats("user-123")

        assert stats["total_habits"] == 2
        assert stats["total_current_streak"] == 2
        assert "weekly_completion_rate" in stats
        assert "best_streak" in stats


class TestHabitServiceEdgeCases:
    """Edge case tests for HabitService."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_without_storage_raises_error(self):
        """Service without storage should raise RuntimeError."""
        from alfred.core.services.habit_service import HabitService

        service = HabitService(storage=None)

        with pytest.raises(RuntimeError, match="Storage not configured"):
            await service.create_habit(user_id="user-123", name="Test")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_habits_empty(self):
        """get_habits should return empty list for new user."""
        from alfred.core.services.habit_service import HabitService

        service = HabitService(storage=MockHabitStorage())

        habits = await service.get_habits(user_id="new-user")

        assert habits == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_nonexistent_habit(self):
        """get_habit should return None for nonexistent habit."""
        from alfred.core.services.habit_service import HabitService

        service = HabitService(storage=MockHabitStorage())

        habit = await service.get_habit("user-123", "nonexistent-habit-id")

        assert habit is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_habit_stats_empty(self):
        """get_habit_stats should handle empty habit list."""
        from alfred.core.services.habit_service import HabitService

        service = HabitService(storage=MockHabitStorage())

        stats = await service.get_habit_stats("user-123")

        assert stats["total_habits"] == 0
        assert stats["total_current_streak"] == 0
        assert stats["weekly_completion_rate"] == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_log_habit_duplicate_same_day(self):
        """log_habit should not allow duplicate on same day."""
        from alfred.core.services.habit_service import HabitService

        storage = MockHabitStorage()
        service = HabitService(storage=storage)

        habit_id = await service.create_habit(user_id="user-123", name="Test")

        # First log should succeed
        result1 = await service.log_habit("user-123", habit_id)
        assert result1["success"] is True

        # Second log on same day should fail
        result2 = await service.log_habit("user-123", habit_id)
        assert result2["success"] is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_is_new_record_flag(self):
        """log_habit should set is_new_record when streak equals longest."""
        from alfred.core.services.habit_service import HabitService

        storage = MockHabitStorage()
        service = HabitService(storage=storage)

        habit_id = await service.create_habit(user_id="user-123", name="Test")

        # First completion should be a new record
        result = await service.log_habit("user-123", habit_id)
        assert result["is_new_record"] is True
        assert result["current_streak"] == 1
        assert result["longest_streak"] == 1
