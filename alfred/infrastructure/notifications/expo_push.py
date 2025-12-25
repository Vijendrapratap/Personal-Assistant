"""
Expo Push Notification Service for Alfred.
Handles sending push notifications via Expo's push notification service.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger(__name__)


class ExpoPushService:
    """
    Service for sending push notifications via Expo.

    Expo Push Notification service is free and works with Expo/React Native apps.
    """

    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

    def __init__(self):
        self.access_token = os.getenv("EXPO_ACCESS_TOKEN")  # Optional for higher rate limits

    async def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        badge: Optional[int] = None,
        sound: str = "default",
        priority: str = "high",
    ) -> bool:
        """
        Send a push notification to a single device.

        Args:
            token: Expo push token (ExponentPushToken[xxx])
            title: Notification title
            body: Notification body text
            data: Optional data payload
            badge: Optional badge count for iOS
            sound: Sound to play (default, null, or custom)
            priority: Notification priority (default, normal, high)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self._is_valid_expo_token(token):
            logger.error(f"Invalid Expo push token: {token}")
            return False

        message = {
            "to": token,
            "title": title,
            "body": body,
            "sound": sound,
            "priority": priority,
        }

        if data:
            message["data"] = data

        if badge is not None:
            message["badge"] = badge

        return await self._send_messages([message])

    async def send_batch(
        self,
        notifications: List[Dict[str, Any]],
    ) -> Dict[str, bool]:
        """
        Send multiple push notifications.

        Args:
            notifications: List of notification dicts with keys:
                - token: Expo push token
                - title: Notification title
                - body: Notification body
                - data: Optional data payload

        Returns:
            Dict mapping token -> success status
        """
        messages = []
        for notif in notifications:
            if not self._is_valid_expo_token(notif.get("token", "")):
                continue

            messages.append({
                "to": notif["token"],
                "title": notif["title"],
                "body": notif["body"],
                "sound": notif.get("sound", "default"),
                "priority": notif.get("priority", "high"),
                "data": notif.get("data", {}),
            })

        if not messages:
            return {}

        success = await self._send_messages(messages)
        return {msg["to"]: success for msg in messages}

    async def _send_messages(self, messages: List[Dict]) -> bool:
        """Send messages to Expo push service."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.EXPO_PUSH_URL,
                    headers=headers,
                    json=messages,
                    timeout=30.0,
                )

                if response.status_code != 200:
                    logger.error(f"Expo push failed: {response.status_code} - {response.text}")
                    return False

                result = response.json()
                data = result.get("data", [])

                # Check for errors in response
                for i, item in enumerate(data):
                    if item.get("status") == "error":
                        logger.error(f"Push error for message {i}: {item.get('message')}")
                        # Handle specific error types
                        if item.get("details", {}).get("error") == "DeviceNotRegistered":
                            # Token is invalid, should be removed
                            logger.warning(f"Device not registered: {messages[i]['to']}")

                return True

        except httpx.TimeoutException:
            logger.error("Timeout sending push notification")
            return False
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False

    def _is_valid_expo_token(self, token: str) -> bool:
        """Validate Expo push token format."""
        if not token:
            return False
        return token.startswith("ExponentPushToken[") and token.endswith("]")


class NotificationScheduler:
    """
    Schedules and manages proactive notifications.
    """

    def __init__(self, storage, push_service: ExpoPushService):
        self.storage = storage
        self.push_service = push_service

    async def schedule_morning_briefing(self, user_id: str, briefing_time: str = "08:00"):
        """Schedule morning briefing notification."""
        from datetime import datetime, timedelta

        # Parse briefing time
        hour, minute = map(int, briefing_time.split(":"))

        # Calculate next briefing time
        now = datetime.now()
        next_briefing = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_briefing <= now:
            next_briefing += timedelta(days=1)

        # Create scheduled notification
        notification_id = self.storage.schedule_notification(
            user_id=user_id,
            notification_type="morning_briefing",
            title="Good morning, Sir",
            content="Your morning briefing is ready. Tap to see today's overview.",
            trigger_time=next_briefing,
            context={"type": "briefing", "period": "morning"},
        )

        return notification_id

    async def schedule_evening_review(self, user_id: str, review_time: str = "18:00"):
        """Schedule evening review notification."""
        from datetime import datetime, timedelta

        hour, minute = map(int, review_time.split(":"))

        now = datetime.now()
        next_review = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_review <= now:
            next_review += timedelta(days=1)

        notification_id = self.storage.schedule_notification(
            user_id=user_id,
            notification_type="evening_review",
            title="Evening Review",
            content="Time to reflect on today's accomplishments. Ready for tomorrow?",
            trigger_time=next_review,
            context={"type": "briefing", "period": "evening"},
        )

        return notification_id

    async def schedule_habit_reminder(
        self,
        user_id: str,
        habit_id: str,
        habit_name: str,
        reminder_time: str,
    ):
        """Schedule a habit reminder."""
        from datetime import datetime, timedelta

        hour, minute = map(int, reminder_time.split(":"))

        now = datetime.now()
        reminder = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if reminder <= now:
            reminder += timedelta(days=1)

        notification_id = self.storage.schedule_notification(
            user_id=user_id,
            notification_type="habit_reminder",
            title=f"Time for: {habit_name}",
            content=f"Don't break your streak! Complete {habit_name} now.",
            trigger_time=reminder,
            context={"habit_id": habit_id, "habit_name": habit_name},
        )

        return notification_id

    async def schedule_task_due_reminder(
        self,
        user_id: str,
        task_id: str,
        task_title: str,
        due_date: "datetime",
        hours_before: int = 2,
    ):
        """Schedule a task due reminder."""
        from datetime import timedelta

        reminder_time = due_date - timedelta(hours=hours_before)

        notification_id = self.storage.schedule_notification(
            user_id=user_id,
            notification_type="task_due",
            title="Task Due Soon",
            content=f"'{task_title}' is due in {hours_before} hours.",
            trigger_time=reminder_time,
            context={"task_id": task_id, "task_title": task_title},
        )

        return notification_id

    async def process_pending_notifications(self):
        """
        Process all pending notifications that are due.
        This should be called by a background worker/cron job.
        """
        from datetime import datetime

        # Get all pending notifications that are due
        pending = self.storage.get_due_notifications()

        sent_count = 0
        for notification in pending:
            user_id = notification["user_id"]
            push_token = self.storage.get_user_preference(user_id, "push_token_expo")

            if not push_token:
                continue

            success = await self.push_service.send_notification(
                token=push_token,
                title=notification["title"],
                body=notification["content"],
                data={
                    "notification_id": notification["notification_id"],
                    "type": notification["notification_type"],
                    "context": notification.get("context", {}),
                },
            )

            if success:
                self.storage.update_notification_status(
                    notification["notification_id"],
                    user_id,
                    "sent"
                )
                sent_count += 1

        return sent_count
