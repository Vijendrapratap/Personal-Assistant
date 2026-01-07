"""
Project Service.

Business logic for project management.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from alfred.core.services.base import BaseService


class ProjectService(BaseService):
    """
    Project management service.

    Handles:
    - Project CRUD operations
    - Project updates and progress tracking
    - Project health monitoring
    """

    async def create_project(
        self,
        user_id: str,
        name: str,
        description: str = "",
        organization: str = "",
        role: str = "owner",
        integrations: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Create a new project."""
        self._ensure_storage()

        project_id = self.storage.create_project(
            user_id=user_id,
            name=name,
            description=description,
            organization=organization,
            role=role,
            integrations=integrations,
        )

        if project_id:
            self._log_action("CREATE_PROJECT", user_id, f"project_id={project_id}")

        return project_id

    async def get_project(
        self,
        user_id: str,
        project_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a single project by ID."""
        self._ensure_storage()
        return self.storage.get_project(project_id, user_id)

    async def get_projects(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all projects for a user."""
        self._ensure_storage()
        return self.storage.get_projects(user_id, status=status)

    async def update_project(
        self,
        user_id: str,
        project_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update a project."""
        self._ensure_storage()

        success = self.storage.update_project(project_id, user_id, updates)
        if success:
            self._log_action("UPDATE_PROJECT", user_id, f"project_id={project_id}")
        return success

    async def add_update(
        self,
        user_id: str,
        project_id: str,
        content: str,
        update_type: str = "progress",
        action_items: Optional[List[str]] = None,
        blockers: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Add an update to a project."""
        self._ensure_storage()

        update_id = self.storage.add_project_update(
            project_id=project_id,
            user_id=user_id,
            content=content,
            update_type=update_type,
            action_items=action_items,
            blockers=blockers,
        )

        if update_id:
            self._log_action(
                "ADD_PROJECT_UPDATE",
                user_id,
                f"project_id={project_id} update_id={update_id}"
            )

        return update_id

    async def get_updates(
        self,
        user_id: str,
        project_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get updates for a project."""
        self._ensure_storage()
        return self.storage.get_project_updates(project_id, user_id, limit=limit)

    async def delete_project(
        self,
        user_id: str,
        project_id: str,
    ) -> bool:
        """Archive/delete a project."""
        self._ensure_storage()

        success = self.storage.delete_project(project_id, user_id)
        if success:
            self._log_action("DELETE_PROJECT", user_id, f"project_id={project_id}")
        return success

    async def get_project_health(
        self,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get health metrics for all projects.

        Identifies:
        - Stale projects (no updates recently)
        - Projects with blockers
        - Projects with overdue tasks
        """
        self._ensure_storage()
        return self.storage.get_project_health(user_id)

    async def get_stale_projects(
        self,
        user_id: str,
        days_threshold: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get projects that haven't been updated recently."""
        self._ensure_storage()

        projects = self.storage.get_projects(user_id, status="active")
        cutoff = datetime.now() - timedelta(days=days_threshold)

        stale = []
        for project in projects:
            last_update = project.get("last_update_at") or project.get("updated_at")
            if last_update and last_update < cutoff:
                project["days_since_update"] = (datetime.now() - last_update).days
                stale.append(project)

        return sorted(stale, key=lambda p: p.get("days_since_update", 0), reverse=True)

    async def get_project_summary(
        self,
        user_id: str,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        Get a summary of a project including tasks and recent activity.
        """
        self._ensure_storage()

        project = self.storage.get_project(project_id, user_id)
        if not project:
            return {}

        # Get project tasks
        tasks = self.storage.get_tasks(user_id=user_id, project_id=project_id)
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]

        # Get recent updates
        updates = self.storage.get_project_updates(project_id, user_id, limit=5)

        return {
            "project": project,
            "task_summary": {
                "total": len(tasks),
                "pending": len(pending_tasks),
                "completed": len(completed_tasks),
                "completion_rate": (
                    len(completed_tasks) / len(tasks) * 100 if tasks else 0
                ),
            },
            "recent_updates": updates,
            "health": self._calculate_project_health(project, tasks, updates),
        }

    def _calculate_project_health(
        self,
        project: Dict[str, Any],
        tasks: List[Dict[str, Any]],
        updates: List[Dict[str, Any]],
    ) -> str:
        """Calculate project health status."""
        # Check for blockers
        has_blockers = any(
            u.get("update_type") == "blocker" for u in updates[:3]
        )
        if has_blockers:
            return "blocked"

        # Check for staleness
        last_update = project.get("last_update_at") or project.get("updated_at")
        if last_update:
            days_since = (datetime.now() - last_update).days
            if days_since > 7:
                return "stale"
            elif days_since > 3:
                return "needs_attention"

        # Check task completion
        pending = [t for t in tasks if t.get("status") == "pending"]
        overdue = [
            t for t in pending
            if t.get("due_date") and t["due_date"] < datetime.now()
        ]
        if len(overdue) > 2:
            return "at_risk"

        return "healthy"
