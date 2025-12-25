from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from alfred.api.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])


# Pydantic Models
class ProjectCreate(BaseModel):
    name: str
    organization: Optional[str] = ""
    role: Optional[str] = "contributor"  # founder, coo, pm, developer, contributor
    description: Optional[str] = ""
    integrations: Optional[Dict[str, str]] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    organization: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None  # active, on_hold, completed, archived
    description: Optional[str] = None
    integrations: Optional[Dict[str, str]] = None


class ProjectUpdateLog(BaseModel):
    content: str
    update_type: Optional[str] = "progress"  # progress, blocker, decision, note, milestone
    action_items: Optional[List[str]] = None
    blockers: Optional[List[str]] = None


# Dependency to get storage
def get_storage():
    from alfred.main import storage_provider
    if not storage_provider:
        raise HTTPException(status_code=503, detail="Storage not available")
    return storage_provider


# Routes
@router.post("")
async def create_project(
    project: ProjectCreate,
    user_id: str = Depends(get_current_user)
):
    """Create a new project."""
    storage = get_storage()
    project_id = storage.create_project(
        user_id=user_id,
        name=project.name,
        organization=project.organization or "",
        role=project.role or "contributor",
        description=project.description or "",
        integrations=project.integrations
    )

    if not project_id:
        raise HTTPException(status_code=500, detail="Failed to create project")

    return {
        "project_id": project_id,
        "message": "Project created successfully"
    }


@router.get("")
async def list_projects(
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Get all projects for the current user."""
    storage = get_storage()
    projects = storage.get_projects(user_id, status=status)
    return {"projects": projects}


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get a specific project by ID."""
    storage = get_storage()
    project = storage.get_project(project_id, user_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    updates: ProjectUpdate,
    user_id: str = Depends(get_current_user)
):
    """Update a project."""
    storage = get_storage()

    # Filter out None values
    update_data = {k: v for k, v in updates.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")

    success = storage.update_project(project_id, user_id, update_data)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update project")

    return {"message": "Project updated successfully"}


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user_id: str = Depends(get_current_user)
):
    """Archive a project (soft delete)."""
    storage = get_storage()
    success = storage.delete_project(project_id, user_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to archive project")

    return {"message": "Project archived successfully"}


# Project Updates (Daily Logs)
@router.post("/{project_id}/updates")
async def add_project_update(
    project_id: str,
    update: ProjectUpdateLog,
    user_id: str = Depends(get_current_user)
):
    """Add an update/log entry to a project."""
    storage = get_storage()

    # Verify project exists
    project = storage.get_project(project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_id = storage.add_project_update(
        project_id=project_id,
        user_id=user_id,
        content=update.content,
        update_type=update.update_type or "progress",
        action_items=update.action_items,
        blockers=update.blockers
    )

    if not update_id:
        raise HTTPException(status_code=500, detail="Failed to add update")

    return {
        "update_id": update_id,
        "message": "Update added successfully"
    }


@router.get("/{project_id}/updates")
async def get_project_updates(
    project_id: str,
    limit: int = 20,
    user_id: str = Depends(get_current_user)
):
    """Get update history for a project."""
    storage = get_storage()

    # Verify project exists
    project = storage.get_project(project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    updates = storage.get_project_updates(project_id, user_id, limit=limit)
    return {"updates": updates}


@router.get("/{project_id}/tasks")
async def get_project_tasks(
    project_id: str,
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Get all tasks for a specific project."""
    storage = get_storage()

    # Verify project exists
    project = storage.get_project(project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = storage.get_tasks(user_id, project_id=project_id, status=status)
    return {"tasks": tasks}
