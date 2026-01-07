"""
Project Management Tools.

Tools for creating, updating, and querying projects.
"""

from typing import List, Optional

from alfred.core.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ToolCategory,
)
from alfred.core.tools.registry import register_tool


@register_tool
class GetProjectsTool(BaseTool):
    """Get user's projects."""

    name = "get_projects"
    description = "Get the user's projects with their status and progress."
    category = ToolCategory.PROJECTS
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="status",
                type="string",
                description="Filter by project status",
                required=False,
                enum=["active", "completed", "on_hold", "archived"],
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            projects = storage.get_projects(
                user_id=user_id,
                status=kwargs.get("status"),
            )

            return ToolResult.ok(
                data={
                    "projects": projects,
                    "count": len(projects),
                }
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to get projects: {str(e)}")


@register_tool
class GetProjectTool(BaseTool):
    """Get a specific project."""

    name = "get_project"
    description = "Get details of a specific project by ID."
    category = ToolCategory.PROJECTS
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="project_id",
                type="string",
                description="The ID of the project",
                required=True,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            project = storage.get_project(
                project_id=kwargs["project_id"],
                user_id=user_id,
            )

            if project:
                return ToolResult.ok(data=project)
            else:
                return ToolResult.fail("Project not found")

        except Exception as e:
            return ToolResult.fail(f"Failed to get project: {str(e)}")


@register_tool
class CreateProjectTool(BaseTool):
    """Create a new project."""

    name = "create_project"
    description = "Create a new project for the user."
    category = ToolCategory.PROJECTS
    is_write = True

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="name",
                type="string",
                description="Name of the project",
                required=True,
            ),
            ToolParameter(
                name="description",
                type="string",
                description="Description of the project",
                required=False,
            ),
            ToolParameter(
                name="organization",
                type="string",
                description="Organization or company the project is for",
                required=False,
            ),
            ToolParameter(
                name="role",
                type="string",
                description="User's role in the project",
                required=False,
                enum=["owner", "lead", "contributor", "observer"],
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            project_id = storage.create_project(
                user_id=user_id,
                name=kwargs["name"],
                description=kwargs.get("description", ""),
                organization=kwargs.get("organization", ""),
                role=kwargs.get("role", "owner"),
            )

            if project_id:
                return ToolResult.ok(
                    data={
                        "project_id": project_id,
                        "message": f"Created project: {kwargs['name']}",
                    }
                )
            else:
                return ToolResult.fail("Failed to create project")

        except Exception as e:
            return ToolResult.fail(f"Failed to create project: {str(e)}")


@register_tool
class AddProjectUpdateTool(BaseTool):
    """Add an update to a project."""

    name = "add_project_update"
    description = "Add a progress update to a project. Use this to track progress, blockers, or action items."
    category = ToolCategory.PROJECTS
    is_write = True

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="project_id",
                type="string",
                description="The ID of the project",
                required=True,
            ),
            ToolParameter(
                name="content",
                type="string",
                description="The update content",
                required=True,
            ),
            ToolParameter(
                name="update_type",
                type="string",
                description="Type of update",
                required=False,
                default="progress",
                enum=["progress", "blocker", "milestone", "decision"],
            ),
            ToolParameter(
                name="action_items",
                type="array",
                description="List of action items from this update",
                required=False,
            ),
            ToolParameter(
                name="blockers",
                type="array",
                description="List of blockers identified",
                required=False,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            update_id = storage.add_project_update(
                project_id=kwargs["project_id"],
                user_id=user_id,
                content=kwargs["content"],
                update_type=kwargs.get("update_type", "progress"),
                action_items=kwargs.get("action_items"),
                blockers=kwargs.get("blockers"),
            )

            if update_id:
                return ToolResult.ok(
                    data={
                        "update_id": update_id,
                        "message": "Project update added successfully",
                    }
                )
            else:
                return ToolResult.fail("Failed to add update")

        except Exception as e:
            return ToolResult.fail(f"Failed to add project update: {str(e)}")


@register_tool
class GetProjectHealthTool(BaseTool):
    """Get project health metrics."""

    name = "get_project_health"
    description = "Get health metrics for all projects - identifying stale projects, blockers, and deadlines."
    category = ToolCategory.PROJECTS
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return []

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            health = storage.get_project_health(user_id=user_id)

            return ToolResult.ok(
                data={
                    "projects": health,
                    "count": len(health),
                }
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to get project health: {str(e)}")
