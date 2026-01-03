"""
Alfred Scheduler - Background job management using APScheduler

Handles:
- Morning briefings per user's preferred time
- Evening reviews per user's preferred time
- Habit reminders at configured times
- Proactive checks (stale projects, overdue tasks)
"""

import os
import logging
from datetime import datetime, time, timedelta
from typing import Optional, Callable, Any
from contextlib import asynccontextmanager

# APScheduler imports
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logging.warning("APScheduler not installed. Background jobs will be disabled.")

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional['AlfredScheduler'] = None


class AlfredScheduler:
    """
    Manages all background scheduled jobs for Alfred.
    """

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.storage = None
        self.proactive_engine = None
        self.push_service = None
        self._initialized = False

    def initialize(
        self,
        storage,
        proactive_engine=None,
        push_service=None
    ):
        """Initialize the scheduler with required dependencies."""
        if not APSCHEDULER_AVAILABLE:
            logger.error("Cannot initialize scheduler: APScheduler not installed")
            return False

        self.storage = storage
        self.proactive_engine = proactive_engine
        self.push_service = push_service

        # Create scheduler with memory job store
        jobstores = {
            'default': MemoryJobStore()
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            timezone='UTC'  # Store in UTC, convert for users
        )

        self._initialized = True
        logger.info("Alfred Scheduler initialized")
        return True

    def start(self):
        """Start the scheduler and add default jobs."""
        if not self._initialized or not self.scheduler:
            logger.error("Scheduler not initialized")
            return False

        try:
            # Add global jobs
            self._add_default_jobs()

            # Start scheduler
            self.scheduler.start()
            logger.info("Alfred Scheduler started")
            return True
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            return False

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Alfred Scheduler shutdown")

    def _add_default_jobs(self):
        """Add default background jobs."""

        # Proactive check every 5 minutes
        self.scheduler.add_job(
            self._run_proactive_checks,
            trigger=IntervalTrigger(minutes=5),
            id='proactive_checks',
            name='Proactive Checks',
            replace_existing=True
        )

        # Notification dispatch every minute
        self.scheduler.add_job(
            self._dispatch_pending_notifications,
            trigger=IntervalTrigger(minutes=1),
            id='notification_dispatch',
            name='Notification Dispatch',
            replace_existing=True
        )

        # Daily scheduling job (runs at midnight UTC)
        self.scheduler.add_job(
            self._schedule_daily_jobs,
            trigger=CronTrigger(hour=0, minute=0),
            id='daily_scheduling',
            name='Daily Job Scheduling',
            replace_existing=True
        )

        logger.info("Default jobs added to scheduler")

    # ------------------------------------------
    # JOB IMPLEMENTATIONS
    # ------------------------------------------

    async def _run_proactive_checks(self):
        """Run proactive checks for all users."""
        if not self.storage or not self.proactive_engine:
            return

        try:
            # In production, paginate this query
            users = await self._get_active_users()

            for user in users:
                try:
                    user_id = user.get('user_id')
                    nudges = await self.proactive_engine.check_for_nudges(user_id)

                    for nudge in nudges:
                        # Store nudge for later display or send as notification
                        await self._handle_nudge(user_id, nudge)

                except Exception as e:
                    logger.error(f"Error checking nudges for user {user.get('user_id')}: {e}")

        except Exception as e:
            logger.error(f"Error in proactive checks: {e}")

    async def _dispatch_pending_notifications(self):
        """Send notifications that are due."""
        if not self.storage or not self.push_service:
            return

        try:
            now = datetime.utcnow()

            # Get notifications due in the next minute
            pending = self.storage.get_due_notifications(now)

            for notification in pending:
                try:
                    user_id = notification.get('user_id')
                    push_token = self.storage.get_user_push_token(user_id)

                    if push_token:
                        await self.push_service.send_notification(
                            push_token=push_token,
                            title=notification.get('title'),
                            body=notification.get('content'),
                            data=notification.get('context', {})
                        )

                        # Mark as sent
                        self.storage.mark_notification_sent(notification.get('notification_id'))
                        logger.info(f"Sent notification {notification.get('notification_id')} to user {user_id}")

                except Exception as e:
                    logger.error(f"Error sending notification: {e}")

        except Exception as e:
            logger.error(f"Error dispatching notifications: {e}")

    async def _schedule_daily_jobs(self):
        """Schedule per-user jobs for the day."""
        if not self.storage or not self.proactive_engine:
            return

        try:
            users = await self._get_active_users()

            for user in users:
                try:
                    user_id = user.get('user_id')
                    await self.proactive_engine.schedule_daily_notifications(user_id)
                    logger.info(f"Scheduled daily notifications for user {user_id}")
                except Exception as e:
                    logger.error(f"Error scheduling for user {user.get('user_id')}: {e}")

        except Exception as e:
            logger.error(f"Error in daily scheduling: {e}")

    # ------------------------------------------
    # USER-SPECIFIC JOB SCHEDULING
    # ------------------------------------------

    def schedule_user_briefing(
        self,
        user_id: str,
        briefing_type: str,
        hour: int,
        minute: int
    ):
        """Schedule a briefing for a specific user at their preferred time."""
        if not self.scheduler:
            return None

        job_id = f"{briefing_type}_{user_id}"

        async def briefing_job():
            await self._send_briefing(user_id, briefing_type)

        self.scheduler.add_job(
            briefing_job,
            trigger=CronTrigger(hour=hour, minute=minute),
            id=job_id,
            name=f"{briefing_type.title()} Briefing for {user_id}",
            replace_existing=True
        )

        logger.info(f"Scheduled {briefing_type} briefing for user {user_id} at {hour:02d}:{minute:02d}")
        return job_id

    def schedule_habit_reminder(
        self,
        user_id: str,
        habit_id: str,
        habit_name: str,
        hour: int,
        minute: int
    ):
        """Schedule a habit reminder for a specific user."""
        if not self.scheduler:
            return None

        job_id = f"habit_{habit_id}_{user_id}"

        async def reminder_job():
            await self._send_habit_reminder(user_id, habit_id, habit_name)

        self.scheduler.add_job(
            reminder_job,
            trigger=CronTrigger(hour=hour, minute=minute),
            id=job_id,
            name=f"Habit Reminder: {habit_name}",
            replace_existing=True
        )

        logger.info(f"Scheduled habit reminder '{habit_name}' for user {user_id} at {hour:02d}:{minute:02d}")
        return job_id

    def cancel_job(self, job_id: str):
        """Cancel a scheduled job."""
        if self.scheduler:
            try:
                self.scheduler.remove_job(job_id)
                logger.info(f"Cancelled job: {job_id}")
                return True
            except Exception:
                return False
        return False

    # ------------------------------------------
    # HELPER METHODS
    # ------------------------------------------

    async def _get_active_users(self):
        """Get list of active users. Override in production."""
        # Placeholder - in production, query active users from database
        try:
            if hasattr(self.storage, 'get_all_users'):
                return self.storage.get_all_users() or []
        except Exception:
            pass
        return []

    async def _handle_nudge(self, user_id: str, nudge: dict):
        """Handle a proactive nudge - store or send notification."""
        if not self.storage:
            return

        # Store as a proactive card for display in the app
        # The mobile app can fetch these via /proactive/cards endpoint
        logger.debug(f"Nudge for {user_id}: {nudge.get('message')}")

    async def _send_briefing(self, user_id: str, briefing_type: str):
        """Generate and send a briefing."""
        if not self.proactive_engine or not self.push_service:
            return

        try:
            if briefing_type == 'morning':
                briefing = await self.proactive_engine.generate_morning_briefing(user_id)
                title = "Good Morning, Sir"
            else:
                briefing = await self.proactive_engine.generate_evening_review(user_id)
                title = "Evening Review"

            push_token = self.storage.get_user_push_token(user_id)
            if push_token:
                await self.push_service.send_notification(
                    push_token=push_token,
                    title=title,
                    body=briefing.narrative[:200] if briefing.narrative else "Your briefing is ready.",
                    data={'type': briefing_type, 'screen': 'Today'}
                )

        except Exception as e:
            logger.error(f"Error sending {briefing_type} briefing to {user_id}: {e}")

    async def _send_habit_reminder(self, user_id: str, habit_id: str, habit_name: str):
        """Send a habit reminder notification."""
        if not self.storage or not self.push_service:
            return

        try:
            # Get current streak
            habit = self.storage.get_habit(habit_id, user_id)
            streak = habit.get('current_streak', 0) if habit else 0

            push_token = self.storage.get_user_push_token(user_id)
            if push_token:
                await self.push_service.send_notification(
                    push_token=push_token,
                    title=f"Habit: {habit_name}",
                    body=f"Time for {habit_name}! Current streak: {streak} days.",
                    data={'type': 'habit_reminder', 'habit_id': habit_id}
                )

        except Exception as e:
            logger.error(f"Error sending habit reminder: {e}")


def get_scheduler() -> Optional[AlfredScheduler]:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AlfredScheduler()
    return _scheduler


@asynccontextmanager
async def scheduler_lifespan(app):
    """Context manager for scheduler lifecycle in FastAPI."""
    scheduler = get_scheduler()

    # Get dependencies from app state
    storage = getattr(app.state, 'storage', None)
    proactive_engine = getattr(app.state, 'proactive_engine', None)
    push_service = getattr(app.state, 'push_service', None)

    if storage:
        scheduler.initialize(
            storage=storage,
            proactive_engine=proactive_engine,
            push_service=push_service
        )
        scheduler.start()

    yield

    scheduler.shutdown()
