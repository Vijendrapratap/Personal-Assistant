from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from alfred.api.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# Pydantic Models
class TaskCreate(BaseModel):
    title: str
    project_id: Optional[str] = None
    description: Optional[str] = ""
    priority: Optional[str] = "medium"  # high, medium, low
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    project_id: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None  # pending, in_progress, blocked, completed, cancelled
    due_date: Optional[datetime] = None
    recurrence: Optional[str] = None
    blockers: Optional[List[str]] = None
    tags: Optional[List[str]] = None


# Dependency to get storage
def get_storage():
    from alfred.main import storage_provider
    if not storage_provider:
        raise HTTPException(status_code=503, detail="Storage not available")
    return storage_provider


# Routes
@router.post("")
async def create_task(
    task: TaskCreate,
    user_id: str = Depends(get_current_user)
):
    """Create a new task."""
    storage = get_storage()

    # Verify project exists if provided
    if task.project_id:
        project = storage.get_project(task.project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    task_id = storage.create_task(
        user_id=user_id,
        title=task.title,
        project_id=task.project_id,
        description=task.description or "",
        priority=task.priority or "medium",
        due_date=task.due_date,
        tags=task.tags,
        source="user"
    )

    if not task_id:
        raise HTTPException(status_code=500, detail="Failed to create task")

    return {
        "task_id": task_id,
        "message": "Task created successfully"
    }


@router.get("")
async def list_tasks(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Get all tasks with optional filters."""
    storage = get_storage()
    tasks = storage.get_tasks(
        user_id,
        project_id=project_id,
        status=status,
        priority=priority
    )
    return {"tasks": tasks}


@router.get("/today")
async def get_tasks_due_today(
    user_id: str = Depends(get_current_user)
):
    """Get all tasks due today or overdue."""
    storage = get_storage()
    tasks = storage.get_tasks_due_today(user_id)

    # Separate into categories
    overdue = []
    due_today = []
    today = datetime.now().date()

    for task in tasks:
        if task.get("status") in ["completed", "cancelled"]:
            continue

        due_date = task.get("due_date")
        if due_date:
            due_date_obj = datetime.fromisoformat(due_date).date() if isinstance(due_date, str) else due_date.date()
            if due_date_obj < today:
                overdue.append(task)
            else:
                due_today.append(task)

    return {
        "overdue": overdue,
        "due_today": due_today,
        "total": len(overdue) + len(due_today)
    }


@router.get("/pending")
async def get_pending_tasks(
    user_id: str = Depends(get_current_user)
):
    """Get all pending (not completed) tasks."""
    storage = get_storage()
    tasks = storage.get_tasks(user_id, status="pending")
    in_progress = storage.get_tasks(user_id, status="in_progress")
    blocked = storage.get_tasks(user_id, status="blocked")

    return {
        "pending": tasks,
        "in_progress": in_progress,
        "blocked": blocked,
        "total": len(tasks) + len(in_progress) + len(blocked)
    }


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get a specific task by ID."""
    storage = get_storage()
    task = storage.get_task(task_id, user_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.put("/{task_id}")
async def update_task(
    task_id: str,
    updates: TaskUpdate,
    user_id: str = Depends(get_current_user)
):
    """Update a task."""
    storage = get_storage()

    # Verify task exists
    task = storage.get_task(task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Filter out None values
    update_data = {k: v for k, v in updates.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")

    # Verify new project exists if changing
    if "project_id" in update_data and update_data["project_id"]:
        project = storage.get_project(update_data["project_id"], user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    success = storage.update_task(task_id, user_id, update_data)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update task")

    return {"message": "Task updated successfully"}


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """Mark a task as completed."""
    storage = get_storage()

    # Verify task exists
    task = storage.get_task(task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    success = storage.complete_task(task_id, user_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to complete task")

    return {"message": "Task completed successfully"}


@router.post("/{task_id}/start")
async def start_task(
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """Mark a task as in progress."""
    storage = get_storage()

    # Verify task exists
    task = storage.get_task(task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    success = storage.update_task(task_id, user_id, {"status": "in_progress"})

    if not success:
        raise HTTPException(status_code=500, detail="Failed to start task")

    return {"message": "Task started"}


@router.post("/{task_id}/block")
async def block_task(
    task_id: str,
    blocker: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Mark a task as blocked."""
    storage = get_storage()

    # Verify task exists
    task = storage.get_task(task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = {"status": "blocked"}
    if blocker:
        current_blockers = task.get("blockers", []) or []
        current_blockers.append(blocker)
        updates["blockers"] = current_blockers

    success = storage.update_task(task_id, user_id, updates)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to block task")

    return {"message": "Task marked as blocked"}


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a task."""
    storage = get_storage()

    # Verify task exists
    task = storage.get_task(task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    success = storage.delete_task(task_id, user_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete task")

    return {"message": "Task deleted successfully"}
