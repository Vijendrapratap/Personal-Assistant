from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

from alfred.api.auth import get_current_user

router = APIRouter(prefix="/habits", tags=["Habits"])


# Pydantic Models
class HabitCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    frequency: Optional[str] = "daily"  # daily, weekly, weekdays, custom
    time_preference: Optional[str] = None  # "08:00"
    motivation: Optional[str] = ""
    category: Optional[str] = "general"  # fitness, productivity, learning, health, etc.


class HabitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    time_preference: Optional[str] = None
    motivation: Optional[str] = None
    category: Optional[str] = None
    active: Optional[bool] = None
    reminder_enabled: Optional[bool] = None


class HabitLogEntry(BaseModel):
    logged_date: Optional[date] = None  # Defaults to today
    notes: Optional[str] = ""
    duration_minutes: Optional[int] = None


# Dependency to get storage
def get_storage():
    from alfred.main import storage_provider
    if not storage_provider:
        raise HTTPException(status_code=503, detail="Storage not available")
    return storage_provider


# Routes
@router.post("")
async def create_habit(
    habit: HabitCreate,
    user_id: str = Depends(get_current_user)
):
    """Create a new habit to track."""
    storage = get_storage()

    habit_id = storage.create_habit(
        user_id=user_id,
        name=habit.name,
        description=habit.description or "",
        frequency=habit.frequency or "daily",
        time_preference=habit.time_preference,
        motivation=habit.motivation or "",
        category=habit.category or "general"
    )

    if not habit_id:
        raise HTTPException(status_code=500, detail="Failed to create habit")

    return {
        "habit_id": habit_id,
        "message": "Habit created successfully"
    }


@router.get("")
async def list_habits(
    active_only: bool = True,
    user_id: str = Depends(get_current_user)
):
    """Get all habits for the current user."""
    storage = get_storage()
    habits = storage.get_habits(user_id, active_only=active_only)
    return {"habits": habits}


@router.get("/today")
async def get_habits_due_today(
    user_id: str = Depends(get_current_user)
):
    """Get habits that need to be completed today."""
    storage = get_storage()
    habits = storage.get_habits_due_today(user_id)

    # Categorize by status
    pending = []
    completed = []
    today = date.today()

    all_habits = storage.get_habits(user_id, active_only=True)
    for habit in all_habits:
        last_logged = habit.get("last_logged")
        if last_logged:
            last_logged_date = date.fromisoformat(last_logged) if isinstance(last_logged, str) else last_logged
            if last_logged_date >= today:
                completed.append(habit)
            else:
                pending.append(habit)
        else:
            pending.append(habit)

    return {
        "pending": pending,
        "completed": completed,
        "total_streaks": sum(h.get("current_streak", 0) for h in all_habits)
    }


@router.get("/streaks")
async def get_streaks(
    user_id: str = Depends(get_current_user)
):
    """Get streak information for all habits."""
    storage = get_storage()
    habits = storage.get_habits(user_id, active_only=True)

    streaks = []
    for habit in habits:
        streaks.append({
            "habit_id": habit["habit_id"],
            "name": habit["name"],
            "current_streak": habit.get("current_streak", 0),
            "best_streak": habit.get("best_streak", 0),
            "total_completions": habit.get("total_completions", 0),
            "last_logged": habit.get("last_logged")
        })

    # Sort by current streak descending
    streaks.sort(key=lambda x: x["current_streak"], reverse=True)

    return {"streaks": streaks}


@router.get("/{habit_id}")
async def get_habit(
    habit_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get a specific habit by ID."""
    storage = get_storage()
    habit = storage.get_habit(habit_id, user_id)

    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    return habit


@router.put("/{habit_id}")
async def update_habit(
    habit_id: str,
    updates: HabitUpdate,
    user_id: str = Depends(get_current_user)
):
    """Update a habit."""
    storage = get_storage()

    # Verify habit exists
    habit = storage.get_habit(habit_id, user_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    # Filter out None values
    update_data = {k: v for k, v in updates.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")

    success = storage.update_habit(habit_id, user_id, update_data)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update habit")

    return {"message": "Habit updated successfully"}


@router.post("/{habit_id}/log")
async def log_habit(
    habit_id: str,
    log_entry: HabitLogEntry,
    user_id: str = Depends(get_current_user)
):
    """Log a habit completion."""
    storage = get_storage()

    # Verify habit exists
    habit = storage.get_habit(habit_id, user_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    success = storage.log_habit(
        habit_id=habit_id,
        user_id=user_id,
        logged_date=log_entry.logged_date,
        notes=log_entry.notes or "",
        duration_minutes=log_entry.duration_minutes
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to log habit")

    # Get updated habit to return streak info
    updated_habit = storage.get_habit(habit_id, user_id)

    return {
        "message": "Habit logged successfully",
        "current_streak": updated_habit.get("current_streak", 0),
        "best_streak": updated_habit.get("best_streak", 0),
        "total_completions": updated_habit.get("total_completions", 0)
    }


@router.get("/{habit_id}/history")
async def get_habit_history(
    habit_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: str = Depends(get_current_user)
):
    """Get completion history for a habit."""
    storage = get_storage()

    # Verify habit exists
    habit = storage.get_habit(habit_id, user_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    logs = storage.get_habit_logs(habit_id, user_id, start_date, end_date)

    return {
        "habit": {
            "habit_id": habit["habit_id"],
            "name": habit["name"],
            "current_streak": habit.get("current_streak", 0),
            "best_streak": habit.get("best_streak", 0)
        },
        "logs": logs
    }


@router.delete("/{habit_id}")
async def delete_habit(
    habit_id: str,
    user_id: str = Depends(get_current_user)
):
    """Deactivate a habit (soft delete)."""
    storage = get_storage()

    # Verify habit exists
    habit = storage.get_habit(habit_id, user_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    success = storage.delete_habit(habit_id, user_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete habit")

    return {"message": "Habit deactivated successfully"}
