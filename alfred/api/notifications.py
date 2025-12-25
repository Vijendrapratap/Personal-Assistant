"""
Alfred Notifications API
Handles push notification registration and delivery.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from alfred.core.dependencies import get_current_user, get_storage
from alfred.core.interfaces import MemoryStorage

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class RegisterPushTokenRequest(BaseModel):
    push_token: str
    device_type: str = "expo"  # expo, fcm, apns


class NotificationPreferences(BaseModel):
    morning_briefing: bool = True
    evening_review: bool = True
    habit_reminders: bool = True
    task_due_reminders: bool = True
    project_nudges: bool = True


class NotificationResponse(BaseModel):
    notification_id: str
    notification_type: str
    title: str
    content: str
    trigger_time: str
    status: str
    created_at: str


# ============================================
# ENDPOINTS
# ============================================

@router.post("/register-token")
async def register_push_token(
    request: RegisterPushTokenRequest,
    user_id: str = Depends(get_current_user),
    storage: MemoryStorage = Depends(get_storage),
):
    """Register a push notification token for the user."""
    try:
        storage.save_user_preference(
            user_id,
            f"push_token_{request.device_type}",
            request.push_token
        )
        return {"message": "Push token registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/unregister-token")
async def unregister_push_token(
    device_type: str = "expo",
    user_id: str = Depends(get_current_user),
    storage: MemoryStorage = Depends(get_storage),
):
    """Unregister push notification token."""
    try:
        storage.save_user_preference(
            user_id,
            f"push_token_{device_type}",
            None
        )
        return {"message": "Push token unregistered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences")
async def get_notification_preferences(
    user_id: str = Depends(get_current_user),
    storage: MemoryStorage = Depends(get_storage),
):
    """Get user's notification preferences."""
    prefs = storage.get_user_preference(user_id, "notification_preferences")
    if prefs:
        import json
        return json.loads(prefs)
    return NotificationPreferences().model_dump()


@router.put("/preferences")
async def update_notification_preferences(
    preferences: NotificationPreferences,
    user_id: str = Depends(get_current_user),
    storage: MemoryStorage = Depends(get_storage),
):
    """Update notification preferences."""
    import json
    storage.save_user_preference(
        user_id,
        "notification_preferences",
        json.dumps(preferences.model_dump())
    )
    return {"message": "Preferences updated", "preferences": preferences.model_dump()}


@router.get("/pending", response_model=List[NotificationResponse])
async def get_pending_notifications(
    user_id: str = Depends(get_current_user),
    storage: MemoryStorage = Depends(get_storage),
):
    """Get pending notifications for the user."""
    notifications = storage.get_scheduled_notifications(user_id, status="pending")
    return [
        NotificationResponse(
            notification_id=n["notification_id"],
            notification_type=n["notification_type"],
            title=n["title"],
            content=n["content"],
            trigger_time=n["trigger_time"].isoformat() if n["trigger_time"] else "",
            status=n["status"],
            created_at=n["created_at"].isoformat() if n["created_at"] else "",
        )
        for n in notifications
    ]


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(get_current_user),
    storage: MemoryStorage = Depends(get_storage),
):
    """Mark a notification as read."""
    success = storage.update_notification_status(notification_id, user_id, "read")
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}


@router.post("/{notification_id}/dismiss")
async def dismiss_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user),
    storage: MemoryStorage = Depends(get_storage),
):
    """Dismiss a notification."""
    success = storage.update_notification_status(notification_id, user_id, "dismissed")
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification dismissed"}


@router.post("/test")
async def send_test_notification(
    user_id: str = Depends(get_current_user),
    storage: MemoryStorage = Depends(get_storage),
):
    """Send a test push notification to verify setup."""
    from alfred.infrastructure.notifications.expo_push import ExpoPushService

    push_token = storage.get_user_preference(user_id, "push_token_expo")
    if not push_token:
        raise HTTPException(status_code=400, detail="No push token registered")

    push_service = ExpoPushService()
    success = await push_service.send_notification(
        token=push_token,
        title="Alfred Test",
        body="Your notifications are working, Sir!",
        data={"type": "test"}
    )

    if success:
        return {"message": "Test notification sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send notification")
