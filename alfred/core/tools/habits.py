"""
Habit Tracking Tools.

Tools for creating, logging, and querying habits.
"""

from typing import List, Optional
from datetime import date

from alfred.core.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ToolCategory,
)
from alfred.core.tools.registry import register_tool


@register_tool
class GetHabitsTool(BaseTool):
    """Get user's habits."""

    name = "get_habits"
    description = "Get the user's habits and their current streaks."
    category = ToolCategory.HABITS
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="active_only",
                type="boolean",
                description="Only return active habits",
                required=False,
                default=True,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            habits = storage.get_habits(
                user_id=user_id,
                active_only=kwargs.get("active_only", True),
            )

            return ToolResult.ok(
                data={
                    "habits": habits,
                    "count": len(habits),
                }
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to get habits: {str(e)}")


@register_tool
class CreateHabitTool(BaseTool):
    """Create a new habit."""

    name = "create_habit"
    description = "Create a new habit for the user to track."
    category = ToolCategory.HABITS
    is_write = True

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="name",
                type="string",
                description="Name of the habit",
                required=True,
            ),
            ToolParameter(
                name="frequency",
                type="string",
                description="How often the habit should be done",
                required=False,
                default="daily",
                enum=["daily", "weekly", "weekdays", "weekends"],
            ),
            ToolParameter(
                name="description",
                type="string",
                description="Description of the habit",
                required=False,
            ),
            ToolParameter(
                name="time_preference",
                type="string",
                description="Preferred time to do the habit",
                required=False,
                enum=["morning", "afternoon", "evening", "anytime"],
            ),
            ToolParameter(
                name="category",
                type="string",
                description="Category of the habit",
                required=False,
                default="general",
                enum=["health", "fitness", "learning", "productivity", "mindfulness", "general"],
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            habit_id = storage.create_habit(
                user_id=user_id,
                name=kwargs["name"],
                frequency=kwargs.get("frequency", "daily"),
                description=kwargs.get("description", ""),
                time_preference=kwargs.get("time_preference"),
                category=kwargs.get("category", "general"),
            )

            if habit_id:
                return ToolResult.ok(
                    data={
                        "habit_id": habit_id,
                        "message": f"Created habit: {kwargs['name']}",
                    }
                )
            else:
                return ToolResult.fail("Failed to create habit")

        except Exception as e:
            return ToolResult.fail(f"Failed to create habit: {str(e)}")


@register_tool
class LogHabitTool(BaseTool):
    """Log a habit completion."""

    name = "log_habit"
    description = "Log that the user completed a habit. This updates their streak."
    category = ToolCategory.HABITS
    is_write = True

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="habit_id",
                type="string",
                description="The ID of the habit to log",
                required=True,
            ),
            ToolParameter(
                name="date",
                type="string",
                description="Date of completion (ISO format: YYYY-MM-DD). Defaults to today.",
                required=False,
            ),
            ToolParameter(
                name="notes",
                type="string",
                description="Optional notes about this completion",
                required=False,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            # Parse date if provided
            logged_date = None
            if kwargs.get("date"):
                logged_date = date.fromisoformat(kwargs["date"])

            success = storage.log_habit(
                habit_id=kwargs["habit_id"],
                user_id=user_id,
                logged_date=logged_date,
                notes=kwargs.get("notes", ""),
            )

            if success:
                # Get updated habit info
                habit = storage.get_habit(kwargs["habit_id"], user_id)
                streak_info = ""
                if habit:
                    streak_info = f" Current streak: {habit.get('current_streak', 0)} days!"

                return ToolResult.ok(
                    data={
                        "message": f"Habit logged successfully!{streak_info}",
                        "habit_id": kwargs["habit_id"],
                    }
                )
            else:
                return ToolResult.fail("Failed to log habit")

        except Exception as e:
            return ToolResult.fail(f"Failed to log habit: {str(e)}")


@register_tool
class GetHabitsDueTodayTool(BaseTool):
    """Get habits due today."""

    name = "get_habits_due_today"
    description = "Get all habits that should be completed today."
    category = ToolCategory.HABITS
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return []

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            habits = storage.get_habits_due_today(user_id=user_id)

            return ToolResult.ok(
                data={
                    "habits": habits,
                    "count": len(habits),
                    "date": date.today().isoformat(),
                }
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to get today's habits: {str(e)}")


@register_tool
class GetHabitStreakTool(BaseTool):
    """Get habit streak information."""

    name = "get_habit_streak"
    description = "Get detailed streak information for a specific habit."
    category = ToolCategory.HABITS
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="habit_id",
                type="string",
                description="The ID of the habit",
                required=True,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            habit = storage.get_habit(kwargs["habit_id"], user_id)

            if not habit:
                return ToolResult.fail("Habit not found")

            return ToolResult.ok(
                data={
                    "habit_name": habit.get("name"),
                    "current_streak": habit.get("current_streak", 0),
                    "longest_streak": habit.get("longest_streak", 0),
                    "frequency": habit.get("frequency"),
                }
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to get streak info: {str(e)}")
