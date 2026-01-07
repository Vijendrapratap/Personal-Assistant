"""
Briefing Service.

Generates morning briefings and evening reviews.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta

from alfred.core.services.base import BaseService


class BriefingService(BaseService):
    """
    Briefing generation service.

    Handles:
    - Morning briefings
    - Evening reviews
    - Day/week summaries
    """

    async def generate_morning_briefing(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Generate morning briefing for a user.

        Includes:
        - Greeting based on time of day
        - Today's tasks and priorities
        - Habits due today
        - Calendar events (if connected)
        - Proactive suggestions
        """
        self._ensure_storage()

        # Get user profile for personalization
        profile = self.storage.get_user_profile(user_id) or {}
        user_name = profile.get("name", "there")

        # Get today's data
        tasks_today = self.storage.get_tasks_due_today(user_id)
        habits_today = self.storage.get_habits_due_today(user_id)

        # Get overdue items
        overdue_tasks = self._get_overdue_tasks(user_id)

        # Get project health
        project_health = self.storage.get_project_health(user_id)
        stale_projects = [p for p in project_health if p.get("health") == "stale"]

        # Identify top priority
        top_priority = self._identify_top_priority(tasks_today, overdue_tasks)

        # Generate greeting
        hour = datetime.now().hour
        if hour < 12:
            greeting = f"Good morning, {user_name}!"
        elif hour < 17:
            greeting = f"Good afternoon, {user_name}!"
        else:
            greeting = f"Good evening, {user_name}!"

        # Build briefing
        briefing = {
            "greeting": greeting,
            "date": date.today().isoformat(),
            "day_of_week": datetime.now().strftime("%A"),
            "summary": self._build_summary(
                tasks_today, habits_today, overdue_tasks
            ),
            "top_priority": top_priority,
            "tasks": {
                "due_today": tasks_today,
                "overdue": overdue_tasks,
                "count": len(tasks_today),
            },
            "habits": {
                "due_today": habits_today,
                "count": len(habits_today),
            },
            "projects": {
                "stale": stale_projects,
                "needs_attention": len(stale_projects),
            },
            "proactive_cards": self._generate_proactive_cards(
                user_id, tasks_today, habits_today, stale_projects
            ),
        }

        self._log_action("GENERATE_BRIEFING", user_id, "type=morning")
        return briefing

    async def generate_evening_review(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Generate evening review for a user.

        Includes:
        - Tasks completed today
        - Habits completed today
        - Tomorrow's preview
        - Reflection prompts
        """
        self._ensure_storage()

        # Get today's completions
        today_start = datetime.combine(date.today(), datetime.min.time())
        all_tasks = self.storage.get_tasks(user_id=user_id)

        completed_today = [
            t for t in all_tasks
            if t.get("status") == "completed"
            and t.get("completed_at")
            and t["completed_at"] >= today_start
        ]

        # Get habits completed today
        habits = self.storage.get_habits_due_today(user_id)
        habits_completed = [h for h in habits if h.get("completed_today")]

        # Get tomorrow's tasks
        tomorrow = date.today() + timedelta(days=1)
        tomorrow_end = datetime.combine(tomorrow, datetime.max.time())
        tasks_tomorrow = self.storage.get_tasks(
            user_id=user_id,
            status="pending",
            due_before=tomorrow_end,
        )
        tasks_tomorrow = [
            t for t in tasks_tomorrow
            if t.get("due_date") and t["due_date"].date() == tomorrow
        ]

        return {
            "date": date.today().isoformat(),
            "summary": f"You completed {len(completed_today)} tasks and {len(habits_completed)} habits today.",
            "completed": {
                "tasks": completed_today,
                "habits": habits_completed,
                "task_count": len(completed_today),
                "habit_count": len(habits_completed),
            },
            "tomorrow_preview": {
                "tasks": tasks_tomorrow,
                "count": len(tasks_tomorrow),
            },
            "reflection_prompts": [
                "What was your biggest win today?",
                "What could you improve tomorrow?",
                "Is there anything you're grateful for?",
            ],
        }

    async def get_week_summary(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Generate weekly summary."""
        self._ensure_storage()

        # Calculate week boundaries
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        # Get tasks completed this week
        all_tasks = self.storage.get_tasks(user_id=user_id)
        completed_this_week = [
            t for t in all_tasks
            if t.get("status") == "completed"
            and t.get("completed_at")
            and week_start <= t["completed_at"].date() <= week_end
        ]

        # Get habit stats
        habits = self.storage.get_habits(user_id, active_only=True)
        total_habit_completions = 0
        for habit in habits:
            logs = self.storage.get_habit_logs(
                habit["id"],
                user_id,
                start_date=week_start,
                end_date=week_end,
            )
            total_habit_completions += len(logs)

        return {
            "week_of": week_start.isoformat(),
            "tasks_completed": len(completed_this_week),
            "habit_completions": total_habit_completions,
            "most_productive_day": self._find_most_productive_day(
                completed_this_week
            ),
        }

    def _get_overdue_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get overdue tasks."""
        now = datetime.now()
        today_start = datetime.combine(date.today(), datetime.min.time())

        tasks = self.storage.get_tasks(
            user_id=user_id,
            status="pending",
            due_before=now,
        )

        return [
            t for t in tasks
            if t.get("due_date") and t["due_date"] < today_start
        ]

    def _identify_top_priority(
        self,
        tasks_today: List[Dict[str, Any]],
        overdue_tasks: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Identify the single most important task."""
        # Prioritize overdue urgent/high tasks
        for task in overdue_tasks:
            if task.get("priority") in ["urgent", "high"]:
                return task

        # Then today's urgent/high tasks
        for task in tasks_today:
            if task.get("priority") in ["urgent", "high"]:
                return task

        # Then any overdue task
        if overdue_tasks:
            return overdue_tasks[0]

        # Then any task due today
        if tasks_today:
            return tasks_today[0]

        return None

    def _build_summary(
        self,
        tasks_today: List[Dict[str, Any]],
        habits_today: List[Dict[str, Any]],
        overdue_tasks: List[Dict[str, Any]],
    ) -> str:
        """Build a human-readable summary."""
        parts = []

        if tasks_today:
            parts.append(f"{len(tasks_today)} tasks due today")
        if habits_today:
            parts.append(f"{len(habits_today)} habits to complete")
        if overdue_tasks:
            parts.append(f"{len(overdue_tasks)} overdue tasks")

        if not parts:
            return "Your day is clear! Time for deep work or relaxation."

        return ", ".join(parts) + "."

    def _generate_proactive_cards(
        self,
        user_id: str,
        tasks_today: List[Dict[str, Any]],
        habits_today: List[Dict[str, Any]],
        stale_projects: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate proactive suggestion cards."""
        cards = []

        # Stale project reminders
        for project in stale_projects[:2]:
            cards.append({
                "id": f"stale-{project['id']}",
                "type": "stale_project",
                "title": f"No update on {project['name']}",
                "message": f"It's been {project.get('days_since_update', '?')} days since you updated this project.",
                "actions": [
                    {"label": "Update Now", "action": "update_project"},
                    {"label": "Snooze", "action": "snooze"},
                ],
                "project_id": project["id"],
            })

        # Habit streak encouragement
        for habit in habits_today:
            streak = habit.get("current_streak", 0)
            if streak >= 5 and not habit.get("completed_today"):
                cards.append({
                    "id": f"streak-{habit['id']}",
                    "type": "habit_streak",
                    "title": f"Keep your {habit['name']} streak!",
                    "message": f"You're on a {streak}-day streak. Don't break it!",
                    "actions": [
                        {"label": "Log Now", "action": "log_habit"},
                    ],
                    "habit_id": habit["id"],
                })

        return cards

    def _find_most_productive_day(
        self,
        completed_tasks: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Find the most productive day of the week."""
        if not completed_tasks:
            return None

        day_counts: Dict[str, int] = {}
        for task in completed_tasks:
            completed_at = task.get("completed_at")
            if completed_at:
                day = completed_at.strftime("%A")
                day_counts[day] = day_counts.get(day, 0) + 1

        if day_counts:
            return max(day_counts.keys(), key=lambda d: day_counts[d])
        return None
