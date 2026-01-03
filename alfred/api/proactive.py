"""
Proactive Intelligence API
Generates and manages Alfred's proactive suggestions and cards.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime, date, timedelta
import uuid

from alfred.api.auth import get_current_user

router = APIRouter(prefix="/proactive", tags=["Proactive"])


# ============================================================================
# MODELS
# ============================================================================

class ProactiveCard(BaseModel):
    id: str
    type: Literal["warning", "insight", "reminder", "celebration"]
    title: str
    description: str
    actions: List[str]
    entity_id: Optional[str] = None
    entity_type: Optional[Literal["task", "habit", "project", "event"]] = None
    priority: int = 5  # 1-10, higher = more important
    created_at: str


class DismissRequest(BaseModel):
    card_id: str
    reason: Optional[str] = None


class SnoozeRequest(BaseModel):
    card_id: str
    snooze_until: Optional[str] = None  # ISO datetime, default = 1 hour


# ============================================================================
# STORAGE DEPENDENCY
# ============================================================================

def get_storage():
    from alfred.main import storage_provider
    if not storage_provider:
        raise HTTPException(status_code=503, detail="Storage not available")
    return storage_provider


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/cards", response_model=List[ProactiveCard])
async def get_proactive_cards(
    limit: int = 10,
    user_id: str = Depends(get_current_user)
):
    """
    Get proactive suggestion cards for the user.

    Cards are generated based on:
    - Stale projects (no updates in 3+ days)
    - Streaks at risk (habit not logged today, evening)
    - Overdue tasks
    - Upcoming meetings needing prep
    - Achievement celebrations
    """
    storage = get_storage()
    cards = []
    today = date.today()
    now = datetime.now()

    # --- STALE PROJECTS ---
    projects = storage.get_projects(user_id, status="active")
    for project in projects:
        updates = storage.get_project_updates(project["project_id"], user_id, limit=1)
        if updates:
            last_update = datetime.fromisoformat(updates[0]["created_at"])
            days_since = (now - last_update).days
            if days_since >= 3:
                cards.append(ProactiveCard(
                    id=f"stale-project-{project['project_id']}",
                    type="warning",
                    title=f"{project['name']} - No update in {days_since}d",
                    description="This project hasn't been updated recently. Is everything on track?",
                    actions=["Update Now", "Pause Project", "Dismiss"],
                    entity_id=project["project_id"],
                    entity_type="project",
                    priority=7 if days_since >= 7 else 5,
                    created_at=now.isoformat()
                ))
        else:
            # Project has never been updated
            cards.append(ProactiveCard(
                id=f"stale-project-{project['project_id']}",
                type="warning",
                title=f"{project['name']} - Never updated",
                description="This project has no updates yet. Add one to track progress.",
                actions=["Add Update", "Dismiss"],
                entity_id=project["project_id"],
                entity_type="project",
                priority=6,
                created_at=now.isoformat()
            ))

    # --- STREAKS AT RISK ---
    # Only show in evening (after 6 PM)
    if now.hour >= 18:
        habits = storage.get_habits(user_id, active_only=True)
        for habit in habits:
            last_logged = habit.get("last_logged")
            streak = habit.get("current_streak", 0)

            # Check if habit logged today
            logged_today = False
            if last_logged:
                last_logged_date = date.fromisoformat(last_logged) if isinstance(last_logged, str) else last_logged
                logged_today = last_logged_date >= today

            if not logged_today and streak > 0:
                cards.append(ProactiveCard(
                    id=f"streak-risk-{habit['habit_id']}",
                    type="reminder",
                    title=f"{habit['name']} - Streak at risk!",
                    description=f"Your {streak}-day streak will break if not logged today.",
                    actions=["Log Now", "Skip Today"],
                    entity_id=habit["habit_id"],
                    entity_type="habit",
                    priority=8,  # High priority for streaks
                    created_at=now.isoformat()
                ))

    # --- STREAK CELEBRATIONS ---
    habits = storage.get_habits(user_id, active_only=True)
    for habit in habits:
        streak = habit.get("current_streak", 0)
        # Celebrate milestones
        if streak in [7, 14, 21, 30, 60, 90, 100, 365]:
            cards.append(ProactiveCard(
                id=f"streak-celebration-{habit['habit_id']}-{streak}",
                type="celebration",
                title=f"{streak}-day streak!",
                description=f"Amazing! You've maintained {habit['name']} for {streak} days.",
                actions=["Celebrate", "Share"],
                entity_id=habit["habit_id"],
                entity_type="habit",
                priority=6,
                created_at=now.isoformat()
            ))
        # Near best streak
        best_streak = habit.get("best_streak", 0)
        if streak > 0 and best_streak > 0 and streak == best_streak - 1:
            cards.append(ProactiveCard(
                id=f"near-best-{habit['habit_id']}",
                type="insight",
                title=f"One day from your best!",
                description=f"Complete {habit['name']} tomorrow to beat your record of {best_streak} days.",
                actions=["Got it"],
                entity_id=habit["habit_id"],
                entity_type="habit",
                priority=5,
                created_at=now.isoformat()
            ))

    # --- OVERDUE TASKS ---
    tasks = storage.get_tasks(user_id)
    for task in tasks:
        if task.get("status") in ["completed", "cancelled"]:
            continue
        due_date = task.get("due_date")
        if due_date:
            due_date_obj = datetime.fromisoformat(due_date).date() if isinstance(due_date, str) else due_date.date()
            if due_date_obj < today:
                days_overdue = (today - due_date_obj).days
                cards.append(ProactiveCard(
                    id=f"overdue-task-{task['task_id']}",
                    type="warning",
                    title=f"Overdue: {task['title']}",
                    description=f"This task is {days_overdue} day(s) overdue.",
                    actions=["Complete", "Reschedule", "Cancel"],
                    entity_id=task["task_id"],
                    entity_type="task",
                    priority=9,  # High priority for overdue
                    created_at=now.isoformat()
                ))

    # Sort by priority (highest first) and limit
    cards.sort(key=lambda c: -c.priority)
    return cards[:limit]


@router.post("/dismiss")
async def dismiss_card(
    request: DismissRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Dismiss a proactive card.
    Optionally store the reason to improve future suggestions.
    """
    # In a full implementation, store this in database
    # For now, just acknowledge
    return {
        "success": True,
        "card_id": request.card_id,
        "message": "Card dismissed"
    }


@router.post("/snooze")
async def snooze_card(
    request: SnoozeRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Snooze a proactive card until a specific time.
    Default: 1 hour from now.
    """
    snooze_until = request.snooze_until
    if not snooze_until:
        snooze_until = (datetime.now() + timedelta(hours=1)).isoformat()

    # In a full implementation, store this in database
    return {
        "success": True,
        "card_id": request.card_id,
        "snoozed_until": snooze_until
    }


@router.post("/act/{card_id}")
async def act_on_card(
    card_id: str,
    action: str,
    user_id: str = Depends(get_current_user)
):
    """
    Take action on a proactive card.
    This is a convenience endpoint that routes to the appropriate action.
    """
    storage = get_storage()

    # Parse card ID to determine type and entity
    parts = card_id.split("-", 2)
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid card ID format")

    card_type = parts[0]

    if card_type == "stale" and parts[1] == "project":
        entity_id = parts[2]
        # Action: Update Now, Pause Project, Dismiss
        if action == "Pause Project":
            storage.update_project(entity_id, user_id, {"status": "on_hold"})
            return {"success": True, "action": "Project paused"}
        elif action == "Update Now":
            return {"success": True, "action": "redirect", "target": f"/projects/{entity_id}"}

    elif card_type == "streak" and parts[1] == "risk":
        entity_id = parts[2]
        if action == "Log Now":
            storage.log_habit(entity_id, user_id)
            return {"success": True, "action": "Habit logged"}
        elif action == "Skip Today":
            return {"success": True, "action": "Skipped"}

    elif card_type == "overdue" and parts[1] == "task":
        entity_id = parts[2]
        if action == "Complete":
            storage.complete_task(entity_id, user_id)
            return {"success": True, "action": "Task completed"}
        elif action == "Cancel":
            storage.update_task(entity_id, user_id, {"status": "cancelled"})
            return {"success": True, "action": "Task cancelled"}

    # Default: just dismiss
    return {"success": True, "action": "dismissed"}


# ============================================================================
# EVENING REVIEW MODELS
# ============================================================================

class EveningReviewData(BaseModel):
    incomplete_tasks: List[dict]
    completed_tasks: List[dict]
    habits_completed: int
    habits_pending: int
    suggested_accomplishments: List[str]


class EveningReviewSubmission(BaseModel):
    accomplishments: List[str]
    blockers: List[str]
    tomorrow_focus: List[str]
    mood: Literal["great", "good", "okay", "tired", "stressed"]
    tasks_to_move: List[str]  # task IDs to move to tomorrow
    notes: Optional[str] = None


class MoveTasksRequest(BaseModel):
    task_ids: List[str]


# ============================================================================
# EVENING REVIEW ENDPOINTS
# ============================================================================

@router.get("/evening-review/data", response_model=EveningReviewData)
async def get_evening_review_data(
    user_id: str = Depends(get_current_user)
):
    """
    Get data needed for the evening review:
    - Incomplete tasks from today
    - Completed tasks from today
    - Habit completion status
    - Suggested accomplishments based on today's activity
    """
    storage = get_storage()
    today = date.today()

    # Get all tasks
    all_tasks = storage.get_tasks(user_id) or []

    # Separate completed vs incomplete
    completed_tasks = []
    incomplete_tasks = []

    for task in all_tasks:
        due_date = task.get("due_date")
        status = task.get("status", "pending")

        # Check if task is due today or overdue
        is_today_or_overdue = False
        if due_date:
            try:
                due_date_obj = datetime.fromisoformat(due_date).date() if isinstance(due_date, str) else due_date
                is_today_or_overdue = due_date_obj <= today
            except (ValueError, TypeError):
                pass

        if status == "completed":
            # Check if completed today (based on created_at for now)
            completed_tasks.append(task)
        elif status not in ["cancelled"] and is_today_or_overdue:
            incomplete_tasks.append(task)

    # Get habits status
    habits = storage.get_habits(user_id, active_only=True) or []
    habits_completed = 0
    habits_pending = 0

    for habit in habits:
        last_logged = habit.get("last_logged")
        if last_logged:
            try:
                last_logged_date = date.fromisoformat(last_logged) if isinstance(last_logged, str) else last_logged
                if last_logged_date >= today:
                    habits_completed += 1
                else:
                    habits_pending += 1
            except (ValueError, TypeError):
                habits_pending += 1
        else:
            habits_pending += 1

    # Generate suggested accomplishments
    suggested_accomplishments = []
    for task in completed_tasks[:3]:
        suggested_accomplishments.append(f"Completed: {task.get('title', 'Unknown task')}")
    if habits_completed > 0:
        suggested_accomplishments.append(f"Maintained {habits_completed} habit(s)")

    return EveningReviewData(
        incomplete_tasks=incomplete_tasks[:10],  # Limit to 10
        completed_tasks=completed_tasks[:10],
        habits_completed=habits_completed,
        habits_pending=habits_pending,
        suggested_accomplishments=suggested_accomplishments
    )


@router.post("/evening-review/submit")
async def submit_evening_review(
    submission: EveningReviewSubmission,
    user_id: str = Depends(get_current_user)
):
    """
    Submit the evening review reflection.
    - Stores the review for tracking mood and productivity over time
    - Moves selected tasks to tomorrow
    """
    storage = get_storage()
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # Move selected tasks to tomorrow
    tasks_moved = 0
    for task_id in submission.tasks_to_move:
        try:
            storage.update_task(task_id, user_id, {
                "due_date": tomorrow.isoformat()
            })
            tasks_moved += 1
        except Exception:
            pass  # Skip if task doesn't exist

    # Store the review (in production, save to database)
    review_id = str(uuid.uuid4())

    # For now, just log it
    print(f"Evening review from {user_id}:")
    print(f"  Mood: {submission.mood}")
    print(f"  Accomplishments: {submission.accomplishments}")
    print(f"  Blockers: {submission.blockers}")
    print(f"  Tomorrow: {submission.tomorrow_focus}")
    print(f"  Tasks moved: {tasks_moved}")

    return {
        "message": "Evening review submitted successfully",
        "tasks_moved": tasks_moved,
        "review_id": review_id
    }


@router.post("/evening-review/move-tasks")
async def move_tasks_to_tomorrow(
    request: MoveTasksRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Move specific tasks to tomorrow.
    """
    storage = get_storage()
    tomorrow = date.today() + timedelta(days=1)

    moved = 0
    for task_id in request.task_ids:
        try:
            storage.update_task(task_id, user_id, {
                "due_date": tomorrow.isoformat()
            })
            moved += 1
        except Exception:
            pass

    return {"moved": moved}


@router.get("/evening-review/history")
async def get_evening_review_history(
    limit: int = 7,
    user_id: str = Depends(get_current_user)
):
    """
    Get past evening reviews for mood tracking and reflection.
    """
    # In production, fetch from database
    # For now, return empty list
    return []
