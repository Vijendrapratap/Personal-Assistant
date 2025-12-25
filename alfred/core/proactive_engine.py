"""
Proactive Engine for Alfred

This module handles:
- Scheduled briefings (morning/evening)
- Proactive nudges and reminders
- Pattern detection
- Notification scheduling
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, time, timedelta
from dataclasses import dataclass
import asyncio

from alfred.core.interfaces import MemoryStorage, LLMProvider
from alfred.core.entities import NotificationType, DailyBriefing


@dataclass
class TriggerCondition:
    """Represents a condition that can trigger a proactive action."""
    trigger_type: str
    check_interval_minutes: int = 60
    last_checked: Optional[datetime] = None


class ProactiveEngine:
    """
    The Proactive Engine monitors user data and triggers
    timely notifications, reminders, and briefings.
    """

    def __init__(self, storage: MemoryStorage, llm: Optional[LLMProvider] = None):
        self.storage = storage
        self.llm = llm
        self.running = False
        self._triggers: List[TriggerCondition] = []

    # ------------------------------------------
    # BRIEFING GENERATION
    # ------------------------------------------

    async def generate_morning_briefing(self, user_id: str) -> DailyBriefing:
        """Generate a comprehensive morning briefing."""
        today = date.today()

        # Gather data
        tasks_due = self.storage.get_tasks_due_today(user_id)
        habits_due = self.storage.get_habits_due_today(user_id)
        projects = self.storage.get_projects(user_id, status="active")
        dashboard = self.storage.get_dashboard_data(user_id)

        # Identify priorities
        high_priority = [t for t in tasks_due if t.get("priority") == "high"]
        overdue = [t for t in tasks_due if self._is_overdue(t.get("due_date"))]

        # Identify projects needing attention
        projects_needing_attention = []
        for project in projects:
            updates = self.storage.get_project_updates(project["project_id"], user_id, limit=1)
            if updates:
                last_update = datetime.fromisoformat(updates[0]["created_at"])
                if (datetime.now() - last_update).days >= 3:
                    projects_needing_attention.append(project["name"])
            else:
                projects_needing_attention.append(project["name"])

        # Build briefing
        briefing = DailyBriefing(
            user_id=user_id,
            briefing_type="morning",
            date=today,
            greeting=self._get_greeting(user_id),
            priority_tasks=[{"title": t["title"], "project": t.get("project_name")} for t in high_priority[:5]],
            habit_status=[{"name": h["name"], "streak": h.get("current_streak", 0)} for h in habits_due],
            project_updates=[{"name": p} for p in projects_needing_attention]
        )

        # Generate narrative if LLM available
        if self.llm:
            briefing.narrative = await self._generate_narrative(briefing, "morning")
        else:
            briefing.narrative = self._build_simple_narrative(briefing, "morning")

        return briefing

    async def generate_evening_review(self, user_id: str) -> DailyBriefing:
        """Generate an evening review summarizing the day."""
        today = date.today()
        today_start = datetime.combine(today, time.min)
        today_end = datetime.combine(today, time.max)

        # Get completed tasks today
        all_tasks = self.storage.get_tasks(user_id)
        completed_today = []
        pending = []

        for task in all_tasks:
            if task.get("status") == "completed":
                completed_at = task.get("completed_at")
                if completed_at:
                    completed_dt = datetime.fromisoformat(completed_at) if isinstance(completed_at, str) else completed_at
                    if today_start <= completed_dt <= today_end:
                        completed_today.append(task)
            elif task.get("status") not in ["cancelled"]:
                pending.append(task)

        # Get habit status
        habits = self.storage.get_habits(user_id, active_only=True)
        habits_completed = []
        habits_missed = []

        for habit in habits:
            last_logged = habit.get("last_logged")
            if last_logged:
                last_logged_date = date.fromisoformat(last_logged) if isinstance(last_logged, str) else last_logged
                if last_logged_date >= today:
                    habits_completed.append(habit)
                else:
                    habits_missed.append(habit)
            else:
                habits_missed.append(habit)

        # Build review
        briefing = DailyBriefing(
            user_id=user_id,
            briefing_type="evening",
            date=today,
            greeting=self._get_greeting(user_id),
            completed_today=[{"title": t["title"]} for t in completed_today],
            carried_forward=[{"title": t["title"]} for t in pending[:5]],
            habit_status=[
                {"name": h["name"], "streak": h.get("current_streak", 0), "completed": True}
                for h in habits_completed
            ] + [
                {"name": h["name"], "streak": h.get("current_streak", 0), "completed": False}
                for h in habits_missed
            ]
        )

        # Generate narrative
        if self.llm:
            briefing.narrative = await self._generate_narrative(briefing, "evening")
        else:
            briefing.narrative = self._build_simple_narrative(briefing, "evening")

        return briefing

    # ------------------------------------------
    # PROACTIVE CHECKS
    # ------------------------------------------

    async def check_for_nudges(self, user_id: str) -> List[Dict[str, Any]]:
        """Check for conditions that warrant a proactive nudge."""
        nudges = []
        today = date.today()
        now = datetime.now()

        # Check for overdue tasks
        tasks = self.storage.get_tasks(user_id)
        overdue_count = sum(1 for t in tasks if self._is_overdue(t.get("due_date")) and t.get("status") not in ["completed", "cancelled"])

        if overdue_count > 0:
            nudges.append({
                "type": "overdue_tasks",
                "priority": "high",
                "message": f"Sir, you have {overdue_count} overdue task{'s' if overdue_count > 1 else ''}. Shall we review them?",
                "count": overdue_count
            })

        # Check for habits at risk
        habits = self.storage.get_habits(user_id, active_only=True)
        for habit in habits:
            last_logged = habit.get("last_logged")
            current_streak = habit.get("current_streak", 0)

            if current_streak >= 3:  # Only warn about significant streaks
                if last_logged:
                    last_logged_date = date.fromisoformat(last_logged) if isinstance(last_logged, str) else last_logged
                    if last_logged_date < today:
                        nudges.append({
                            "type": "habit_at_risk",
                            "priority": "medium",
                            "message": f"Your {habit['name']} streak ({current_streak} days) is at risk. Have you completed it today?",
                            "habit_id": habit["habit_id"],
                            "streak": current_streak
                        })

        # Check for projects without recent updates
        projects = self.storage.get_projects(user_id, status="active")
        for project in projects:
            updates = self.storage.get_project_updates(project["project_id"], user_id, limit=1)
            if updates:
                last_update = datetime.fromisoformat(updates[0]["created_at"])
                days_since = (now - last_update).days

                if days_since >= 3:
                    nudges.append({
                        "type": "project_stale",
                        "priority": "medium",
                        "message": f"It's been {days_since} days since the last update on {project['name']}. Everything alright?",
                        "project_id": project["project_id"],
                        "days_since": days_since
                    })

        return nudges

    async def schedule_daily_notifications(self, user_id: str) -> List[str]:
        """Schedule the day's notifications based on user preferences."""
        profile = self.storage.get_user_profile(user_id)
        scheduled = []

        # Default times
        morning_time = profile.get("morning_briefing_time", "08:00") if profile else "08:00"
        evening_time = profile.get("evening_review_time", "18:00") if profile else "18:00"

        today = date.today()

        # Schedule morning briefing
        morning_dt = datetime.combine(today, datetime.strptime(morning_time, "%H:%M").time())
        if morning_dt > datetime.now():
            notification_id = self.storage.schedule_notification(
                user_id=user_id,
                notification_type=NotificationType.MORNING_BRIEFING.value,
                title="Good Morning, Sir",
                content="Your morning briefing is ready.",
                trigger_time=morning_dt,
                context={"type": "morning_briefing"}
            )
            if notification_id:
                scheduled.append(notification_id)

        # Schedule evening review
        evening_dt = datetime.combine(today, datetime.strptime(evening_time, "%H:%M").time())
        if evening_dt > datetime.now():
            notification_id = self.storage.schedule_notification(
                user_id=user_id,
                notification_type=NotificationType.EVENING_REVIEW.value,
                title="Evening Review",
                content="Time to review your day, Sir.",
                trigger_time=evening_dt,
                context={"type": "evening_review"}
            )
            if notification_id:
                scheduled.append(notification_id)

        # Schedule habit reminders
        habits = self.storage.get_habits(user_id, active_only=True)
        for habit in habits:
            if habit.get("reminder_enabled") and habit.get("time_preference"):
                reminder_time = datetime.combine(
                    today,
                    datetime.strptime(habit["time_preference"], "%H:%M").time()
                )
                if reminder_time > datetime.now():
                    notification_id = self.storage.schedule_notification(
                        user_id=user_id,
                        notification_type=NotificationType.HABIT_REMINDER.value,
                        title=f"Habit Reminder: {habit['name']}",
                        content=f"Time for your {habit['name']}. Current streak: {habit.get('current_streak', 0)} days.",
                        trigger_time=reminder_time,
                        context={"habit_id": habit["habit_id"]}
                    )
                    if notification_id:
                        scheduled.append(notification_id)

        return scheduled

    # ------------------------------------------
    # HELPER METHODS
    # ------------------------------------------

    def _is_overdue(self, due_date: Any) -> bool:
        """Check if a due date is overdue."""
        if not due_date:
            return False

        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)

        return due_date.date() < date.today()

    def _get_greeting(self, user_id: str) -> str:
        """Get personalized greeting."""
        hour = datetime.now().hour
        profile = self.storage.get_user_profile(user_id)

        if hour < 12:
            base = "Good morning"
        elif hour < 17:
            base = "Good afternoon"
        else:
            base = "Good evening"

        return f"{base}, Sir"

    def _build_simple_narrative(self, briefing: DailyBriefing, briefing_type: str) -> str:
        """Build a simple narrative without LLM."""
        lines = [briefing.greeting + "."]

        if briefing_type == "morning":
            if briefing.priority_tasks:
                lines.append(f"You have {len(briefing.priority_tasks)} priority items today.")
                for task in briefing.priority_tasks[:3]:
                    lines.append(f"  - {task['title']}")

            if briefing.habit_status:
                at_risk = [h for h in briefing.habit_status if h.get("streak", 0) > 0]
                if at_risk:
                    lines.append(f"You have {len(briefing.habit_status)} habits to complete.")

            if briefing.project_updates:
                lines.append(f"{len(briefing.project_updates)} projects need your attention.")

        else:  # evening
            if briefing.completed_today:
                lines.append(f"You completed {len(briefing.completed_today)} tasks today. Well done.")
            else:
                lines.append("No tasks were completed today.")

            if briefing.carried_forward:
                lines.append(f"{len(briefing.carried_forward)} items carried forward to tomorrow.")

        return " ".join(lines)

    async def _generate_narrative(self, briefing: DailyBriefing, briefing_type: str) -> str:
        """Generate a butler-style narrative using LLM."""
        if not self.llm:
            return self._build_simple_narrative(briefing, briefing_type)

        prompt = f"""You are Alfred, a refined British butler. Generate a brief, elegant {briefing_type} {'briefing' if briefing_type == 'morning' else 'review'}.

Data:
- Priority tasks: {len(briefing.priority_tasks)}
- Habits to complete: {len(briefing.habit_status)}
- Projects needing attention: {len(briefing.project_updates)}
{"- Completed today: " + str(len(briefing.completed_today)) if briefing_type == "evening" else ""}

Keep it concise (2-3 sentences), professional, and slightly witty. Address the user as "Sir"."""

        try:
            response = self.llm.generate_response(prompt, [])
            return response
        except Exception:
            return self._build_simple_narrative(briefing, briefing_type)

    # ------------------------------------------
    # BACKGROUND RUNNER (for future use)
    # ------------------------------------------

    async def run_background_checks(self, interval_seconds: int = 300):
        """Run periodic background checks. Call this in a background task."""
        self.running = True

        while self.running:
            try:
                # Get all users (in production, paginate this)
                # For now, this is a placeholder
                # users = self.storage.get_all_users()
                # for user in users:
                #     await self.check_for_nudges(user["user_id"])
                pass
            except Exception as e:
                print(f"Error in background checks: {e}")

            await asyncio.sleep(interval_seconds)

    def stop(self):
        """Stop background checks."""
        self.running = False
