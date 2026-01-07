"""
Habit Service.

Business logic for habit tracking.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta

from alfred.core.services.base import BaseService


class HabitService(BaseService):
    """
    Habit tracking service.

    Handles:
    - Habit CRUD operations
    - Habit logging
    - Streak calculations
    - Habit analytics
    """

    async def create_habit(
        self,
        user_id: str,
        name: str,
        frequency: str = "daily",
        description: str = "",
        time_preference: Optional[str] = None,
        motivation: str = "",
        category: str = "general",
    ) -> Optional[str]:
        """Create a new habit."""
        self._ensure_storage()

        habit_id = self.storage.create_habit(
            user_id=user_id,
            name=name,
            frequency=frequency,
            description=description,
            time_preference=time_preference,
            motivation=motivation,
            category=category,
        )

        if habit_id:
            self._log_action("CREATE_HABIT", user_id, f"habit_id={habit_id}")

        return habit_id

    async def get_habit(
        self,
        user_id: str,
        habit_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a single habit by ID."""
        self._ensure_storage()
        return self.storage.get_habit(habit_id, user_id)

    async def get_habits(
        self,
        user_id: str,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get all habits for a user."""
        self._ensure_storage()
        return self.storage.get_habits(user_id, active_only=active_only)

    async def get_habits_due_today(self, user_id: str) -> List[Dict[str, Any]]:
        """Get habits that should be completed today."""
        self._ensure_storage()
        return self.storage.get_habits_due_today(user_id)

    async def log_habit(
        self,
        user_id: str,
        habit_id: str,
        logged_date: Optional[date] = None,
        notes: str = "",
        duration_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Log a habit completion.

        Returns:
            Dict with updated streak info
        """
        self._ensure_storage()

        success = self.storage.log_habit(
            habit_id=habit_id,
            user_id=user_id,
            logged_date=logged_date,
            notes=notes,
            duration_minutes=duration_minutes,
        )

        if success:
            self._log_action("LOG_HABIT", user_id, f"habit_id={habit_id}")

            # Get updated habit info
            habit = self.storage.get_habit(habit_id, user_id)
            if habit:
                return {
                    "success": True,
                    "current_streak": habit.get("current_streak", 0),
                    "longest_streak": habit.get("longest_streak", 0),
                    "is_new_record": (
                        habit.get("current_streak", 0) ==
                        habit.get("longest_streak", 0)
                    ),
                }

        return {"success": False}

    async def get_habit_history(
        self,
        user_id: str,
        habit_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Get habit completion history."""
        self._ensure_storage()

        return self.storage.get_habit_logs(
            habit_id=habit_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

    async def update_habit(
        self,
        user_id: str,
        habit_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update a habit."""
        self._ensure_storage()

        success = self.storage.update_habit(habit_id, user_id, updates)
        if success:
            self._log_action("UPDATE_HABIT", user_id, f"habit_id={habit_id}")
        return success

    async def delete_habit(
        self,
        user_id: str,
        habit_id: str,
    ) -> bool:
        """Delete (deactivate) a habit."""
        self._ensure_storage()

        success = self.storage.delete_habit(habit_id, user_id)
        if success:
            self._log_action("DELETE_HABIT", user_id, f"habit_id={habit_id}")
        return success

    async def get_habit_stats(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Get habit statistics for the user.

        Returns:
        - Total habits
        - Active streaks
        - Best streak
        - Completion rate this week
        """
        self._ensure_storage()

        habits = self.storage.get_habits(user_id, active_only=True)

        total_current_streak = sum(h.get("current_streak", 0) for h in habits)
        best_streak = max((h.get("longest_streak", 0) for h in habits), default=0)

        # Calculate completion rate for this week
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        total_possible = 0
        total_completed = 0

        for habit in habits:
            # Simplified: assume daily habits
            if habit.get("frequency") == "daily":
                total_possible += 7
                logs = self.storage.get_habit_logs(
                    habit["id"],
                    user_id,
                    start_date=week_start,
                    end_date=today,
                )
                total_completed += len(logs)

        return {
            "total_habits": len(habits),
            "total_current_streak": total_current_streak,
            "best_streak": best_streak,
            "weekly_completion_rate": (
                total_completed / total_possible * 100
                if total_possible > 0 else 0
            ),
            "habits_completed_today": len([
                h for h in self.storage.get_habits_due_today(user_id)
                if h.get("completed_today")
            ]),
        }
