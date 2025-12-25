from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import date, datetime, timedelta

from alfred.api.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# Dependency to get storage
def get_storage():
    from alfred.main import storage_provider
    if not storage_provider:
        raise HTTPException(status_code=503, detail="Storage not available")
    return storage_provider


@router.get("/today")
async def get_today_overview(
    user_id: str = Depends(get_current_user)
):
    """
    Get today's overview including:
    - Priority tasks
    - Due today tasks
    - Habit status
    - Project updates needed
    """
    storage = get_storage()
    today = date.today()

    # Get tasks
    all_tasks = storage.get_tasks(user_id)
    pending_tasks = [t for t in all_tasks if t.get("status") not in ["completed", "cancelled"]]

    # Categorize tasks
    high_priority = [t for t in pending_tasks if t.get("priority") == "high"]
    due_today = []
    overdue = []

    for task in pending_tasks:
        due_date = task.get("due_date")
        if due_date:
            due_date_obj = datetime.fromisoformat(due_date).date() if isinstance(due_date, str) else due_date.date()
            if due_date_obj < today:
                overdue.append(task)
            elif due_date_obj == today:
                due_today.append(task)

    # Get habits
    habits = storage.get_habits(user_id, active_only=True)
    habits_pending = []
    habits_completed = []

    for habit in habits:
        last_logged = habit.get("last_logged")
        if last_logged:
            last_logged_date = date.fromisoformat(last_logged) if isinstance(last_logged, str) else last_logged
            if last_logged_date >= today:
                habits_completed.append(habit)
            else:
                habits_pending.append(habit)
        else:
            habits_pending.append(habit)

    # Get projects
    projects = storage.get_projects(user_id, status="active")

    # Identify projects needing attention (no updates in 3+ days)
    projects_needing_attention = []
    for project in projects:
        updates = storage.get_project_updates(project["project_id"], user_id, limit=1)
        if updates:
            last_update = datetime.fromisoformat(updates[0]["created_at"])
            if (datetime.now() - last_update).days >= 3:
                projects_needing_attention.append({
                    **project,
                    "days_since_update": (datetime.now() - last_update).days
                })
        else:
            projects_needing_attention.append({
                **project,
                "days_since_update": None
            })

    return {
        "date": today.isoformat(),
        "greeting": _get_greeting(),
        "focus": {
            "high_priority_tasks": high_priority[:5],
            "due_today": due_today,
            "overdue": overdue
        },
        "habits": {
            "pending": habits_pending,
            "completed": habits_completed,
            "total_streaks": sum(h.get("current_streak", 0) for h in habits)
        },
        "projects": {
            "active_count": len(projects),
            "needing_attention": projects_needing_attention
        },
        "stats": {
            "tasks_pending": len(pending_tasks),
            "tasks_overdue": len(overdue),
            "habits_completed_today": len(habits_completed),
            "habits_pending_today": len(habits_pending)
        }
    }


@router.get("/week")
async def get_week_overview(
    user_id: str = Depends(get_current_user)
):
    """Get a weekly overview."""
    storage = get_storage()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # Get all tasks
    all_tasks = storage.get_tasks(user_id)

    # Tasks due this week
    tasks_this_week = []
    for task in all_tasks:
        if task.get("status") in ["completed", "cancelled"]:
            continue
        due_date = task.get("due_date")
        if due_date:
            due_date_obj = datetime.fromisoformat(due_date).date() if isinstance(due_date, str) else due_date.date()
            if week_start <= due_date_obj <= week_end:
                tasks_this_week.append(task)

    # Group by day
    tasks_by_day = {}
    for i in range(7):
        day = week_start + timedelta(days=i)
        tasks_by_day[day.isoformat()] = []

    for task in tasks_this_week:
        due_date = task.get("due_date")
        if due_date:
            due_date_str = datetime.fromisoformat(due_date).date().isoformat() if isinstance(due_date, str) else due_date.date().isoformat()
            if due_date_str in tasks_by_day:
                tasks_by_day[due_date_str].append(task)

    # Get projects health
    projects = storage.get_project_health(user_id)

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "tasks_by_day": tasks_by_day,
        "total_tasks_this_week": len(tasks_this_week),
        "projects_health": projects
    }


@router.get("/project-health")
async def get_project_health(
    user_id: str = Depends(get_current_user)
):
    """Get health metrics for all active projects."""
    storage = get_storage()
    projects = storage.get_project_health(user_id)

    # Enrich with recent activity
    enriched = []
    for project in projects:
        updates = storage.get_project_updates(project["project_id"], user_id, limit=1)
        last_update = None
        days_since_update = None

        if updates:
            last_update = updates[0]["created_at"]
            last_update_dt = datetime.fromisoformat(last_update)
            days_since_update = (datetime.now() - last_update_dt).days

        enriched.append({
            **project,
            "last_update": last_update,
            "days_since_update": days_since_update,
            "status": "healthy" if (days_since_update is None or days_since_update < 3) else "needs_attention"
        })

    return {"projects": enriched}


@router.get("/stats")
async def get_stats(
    user_id: str = Depends(get_current_user)
):
    """Get overall statistics."""
    storage = get_storage()

    dashboard_data = storage.get_dashboard_data(user_id)
    projects = storage.get_projects(user_id)
    habits = storage.get_habits(user_id, active_only=True)

    # Calculate additional stats
    total_tasks = len(storage.get_tasks(user_id))
    completed_tasks = len(storage.get_tasks(user_id, status="completed"))

    return {
        **dashboard_data,
        "total_projects": len(projects),
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        "total_habits": len(habits),
        "longest_streak": max((h.get("current_streak", 0) for h in habits), default=0)
    }


@router.get("/briefing/morning")
async def get_morning_briefing(
    user_id: str = Depends(get_current_user)
):
    """
    Generate a morning briefing.
    Returns structured data that can be used to generate Alfred's spoken briefing.
    """
    storage = get_storage()
    today = date.today()

    # Get today's data
    overview = await get_today_overview(user_id=user_id)

    # Get profile for personalization
    profile = storage.get_user_profile(user_id)

    # Build briefing structure
    briefing = {
        "type": "morning",
        "date": today.isoformat(),
        "greeting": _get_personalized_greeting(profile),
        "sections": []
    }

    # Priority section
    if overview["focus"]["overdue"]:
        briefing["sections"].append({
            "title": "Overdue Items",
            "priority": "high",
            "items": [t["title"] for t in overview["focus"]["overdue"][:3]]
        })

    if overview["focus"]["high_priority_tasks"]:
        briefing["sections"].append({
            "title": "Today's Priorities",
            "priority": "high",
            "items": [t["title"] for t in overview["focus"]["high_priority_tasks"][:3]]
        })

    # Habits section
    if overview["habits"]["pending"]:
        briefing["sections"].append({
            "title": "Habits to Complete",
            "priority": "medium",
            "items": [h["name"] for h in overview["habits"]["pending"]]
        })

    # Projects needing attention
    if overview["projects"]["needing_attention"]:
        briefing["sections"].append({
            "title": "Projects Needing Updates",
            "priority": "medium",
            "items": [p["name"] for p in overview["projects"]["needing_attention"][:3]]
        })

    return briefing


@router.get("/briefing/evening")
async def get_evening_briefing(
    user_id: str = Depends(get_current_user)
):
    """
    Generate an evening review.
    Summarizes what was accomplished and what carries forward.
    """
    storage = get_storage()
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    # Get today's completed tasks
    all_tasks = storage.get_tasks(user_id)
    completed_today = []
    for task in all_tasks:
        if task.get("status") == "completed":
            completed_at = task.get("completed_at")
            if completed_at:
                completed_dt = datetime.fromisoformat(completed_at) if isinstance(completed_at, str) else completed_at
                if today_start <= completed_dt <= today_end:
                    completed_today.append(task)

    # Get remaining tasks
    pending = [t for t in all_tasks if t.get("status") in ["pending", "in_progress", "blocked"]]

    # Get habits status
    habits = storage.get_habits(user_id, active_only=True)
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
    review = {
        "type": "evening",
        "date": today.isoformat(),
        "summary": {
            "tasks_completed": len(completed_today),
            "tasks_remaining": len(pending),
            "habits_completed": len(habits_completed),
            "habits_missed": len(habits_missed)
        },
        "completed": {
            "tasks": [t["title"] for t in completed_today],
            "habits": [h["name"] for h in habits_completed]
        },
        "carried_forward": {
            "tasks": [t["title"] for t in pending[:5]],
            "habits_missed": [h["name"] for h in habits_missed]
        },
        "streaks": {
            h["name"]: h.get("current_streak", 0)
            for h in habits if h.get("current_streak", 0) > 0
        }
    }

    return review


def _get_greeting():
    """Get time-appropriate greeting."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


def _get_personalized_greeting(profile):
    """Get personalized greeting based on user profile."""
    base = _get_greeting()
    if profile and profile.get("bio"):
        # Could extract name from bio or use other personalization
        return f"{base}, Sir"
    return f"{base}, Sir"
