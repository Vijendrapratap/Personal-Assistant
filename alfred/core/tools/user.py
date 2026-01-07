"""
User Context Tools.

Tools for accessing user information, preferences, and context.
"""

from typing import List

from alfred.core.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ToolCategory,
)
from alfred.core.tools.registry import register_tool


@register_tool
class GetUserProfileTool(BaseTool):
    """Get user profile information."""

    name = "get_user_profile"
    description = "Get the user's profile information including name, preferences, and settings."
    category = ToolCategory.USER
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return []

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            profile = storage.get_user_profile(user_id=user_id)

            if profile:
                return ToolResult.ok(data=profile)
            else:
                return ToolResult.fail("User profile not found")

        except Exception as e:
            return ToolResult.fail(f"Failed to get profile: {str(e)}")


@register_tool
class GetUserPreferencesTool(BaseTool):
    """Get user preferences."""

    name = "get_user_preferences"
    description = "Get the user's learned preferences and settings."
    category = ToolCategory.USER
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return []

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            preferences = storage.get_preferences(user_id=user_id)
            return ToolResult.ok(data={"preferences": preferences})

        except Exception as e:
            return ToolResult.fail(f"Failed to get preferences: {str(e)}")


@register_tool
class GetDashboardTool(BaseTool):
    """Get dashboard overview."""

    name = "get_dashboard"
    description = "Get the user's dashboard overview including today's tasks, habits, and project status."
    category = ToolCategory.USER
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return []

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            dashboard = storage.get_dashboard_data(user_id=user_id)
            return ToolResult.ok(data=dashboard)

        except Exception as e:
            return ToolResult.fail(f"Failed to get dashboard: {str(e)}")


@register_tool
class SavePreferenceTool(BaseTool):
    """Save a user preference."""

    name = "save_preference"
    description = "Save a learned preference about the user. Use this to remember things the user tells you."
    category = ToolCategory.USER
    is_write = True

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="key",
                type="string",
                description="The preference key (e.g., 'preferred_meeting_time', 'communication_style')",
                required=True,
            ),
            ToolParameter(
                name="value",
                type="string",
                description="The preference value",
                required=True,
            ),
            ToolParameter(
                name="confidence",
                type="number",
                description="Confidence level (0-1) in this preference",
                required=False,
                default=1.0,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            success = storage.save_preference(
                user_id=user_id,
                key=kwargs["key"],
                value=kwargs["value"],
                confidence=kwargs.get("confidence", 1.0),
            )

            if success:
                return ToolResult.ok(
                    data={"message": f"Saved preference: {kwargs['key']}"}
                )
            else:
                return ToolResult.fail("Failed to save preference")

        except Exception as e:
            return ToolResult.fail(f"Failed to save preference: {str(e)}")


@register_tool
class GetCurrentTimeTool(BaseTool):
    """Get current time in user's timezone."""

    name = "get_current_time"
    description = "Get the current date and time in the user's timezone."
    category = ToolCategory.USER
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return []

    async def execute(self, **kwargs) -> ToolResult:
        from datetime import datetime
        import pytz

        # Get user's timezone from context or default to UTC
        user_timezone = self.context.get("timezone", "UTC")

        try:
            tz = pytz.timezone(user_timezone)
            now = datetime.now(tz)

            return ToolResult.ok(
                data={
                    "datetime": now.isoformat(),
                    "date": now.date().isoformat(),
                    "time": now.time().isoformat(),
                    "day_of_week": now.strftime("%A"),
                    "timezone": user_timezone,
                }
            )
        except Exception as e:
            # Fallback to UTC
            now = datetime.utcnow()
            return ToolResult.ok(
                data={
                    "datetime": now.isoformat(),
                    "date": now.date().isoformat(),
                    "time": now.time().isoformat(),
                    "day_of_week": now.strftime("%A"),
                    "timezone": "UTC",
                }
            )
