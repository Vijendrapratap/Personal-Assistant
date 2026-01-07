"""
Notification Tools.

Tools for scheduling and managing notifications.
"""

from typing import List
from datetime import datetime

from alfred.core.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ToolCategory,
)
from alfred.core.tools.registry import register_tool


@register_tool
class ScheduleReminderTool(BaseTool):
    """Schedule a reminder notification."""

    name = "schedule_reminder"
    description = "Schedule a reminder notification for the user at a specific time."
    category = ToolCategory.NOTIFICATIONS
    is_write = True

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="title",
                type="string",
                description="Title of the reminder",
                required=True,
            ),
            ToolParameter(
                name="message",
                type="string",
                description="Reminder message content",
                required=True,
            ),
            ToolParameter(
                name="remind_at",
                type="string",
                description="When to send the reminder (ISO format: YYYY-MM-DDTHH:MM:SS)",
                required=True,
            ),
            ToolParameter(
                name="context",
                type="object",
                description="Additional context for the reminder (task_id, project_id, etc.)",
                required=False,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            trigger_time = datetime.fromisoformat(kwargs["remind_at"])

            notification_id = storage.schedule_notification(
                user_id=user_id,
                notification_type="reminder",
                title=kwargs["title"],
                content=kwargs["message"],
                trigger_time=trigger_time,
                context=kwargs.get("context"),
            )

            if notification_id:
                return ToolResult.ok(
                    data={
                        "notification_id": notification_id,
                        "message": f"Reminder scheduled for {kwargs['remind_at']}",
                    }
                )
            else:
                return ToolResult.fail("Failed to schedule reminder")

        except ValueError as e:
            return ToolResult.fail(f"Invalid date format: {str(e)}")
        except Exception as e:
            return ToolResult.fail(f"Failed to schedule reminder: {str(e)}")


@register_tool
class GetPendingNotificationsTool(BaseTool):
    """Get pending notifications."""

    name = "get_pending_notifications"
    description = "Get all pending/scheduled notifications for the user."
    category = ToolCategory.NOTIFICATIONS
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return []

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            notifications = storage.get_pending_notifications(user_id=user_id)

            return ToolResult.ok(
                data={
                    "notifications": notifications,
                    "count": len(notifications),
                }
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to get notifications: {str(e)}")


@register_tool
class SendPushNotificationTool(BaseTool):
    """Send an immediate push notification."""

    name = "send_notification"
    description = "Send an immediate push notification to the user's device."
    category = ToolCategory.NOTIFICATIONS
    is_write = True

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="title",
                type="string",
                description="Notification title",
                required=True,
            ),
            ToolParameter(
                name="body",
                type="string",
                description="Notification body text",
                required=True,
            ),
            ToolParameter(
                name="data",
                type="object",
                description="Additional data to include with the notification",
                required=False,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        notification_provider = self.context.get("notification_provider")
        user_id = self.context.get("user_id")

        if not notification_provider or not user_id:
            return ToolResult.fail("Missing notification provider or user context")

        try:
            success = notification_provider.send_push(
                user_id=user_id,
                title=kwargs["title"],
                body=kwargs["body"],
                data=kwargs.get("data"),
            )

            if success:
                return ToolResult.ok(
                    data={"message": "Notification sent successfully"}
                )
            else:
                return ToolResult.fail("Failed to send notification")

        except Exception as e:
            return ToolResult.fail(f"Failed to send notification: {str(e)}")
