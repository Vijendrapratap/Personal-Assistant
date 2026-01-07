"""
Task Management Tools.

Tools for creating, updating, completing, and querying tasks.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date

from alfred.core.tools.base import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ToolCategory,
    ToolError,
)
from alfred.core.tools.registry import register_tool


@register_tool
class GetTasksTool(BaseTool):
    """Get user's tasks with optional filters."""

    name = "get_tasks"
    description = "Get the user's tasks. Can filter by status, priority, project, or due date."
    category = ToolCategory.TASKS
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="status",
                type="string",
                description="Filter by task status",
                required=False,
                enum=["pending", "in_progress", "completed", "cancelled"],
            ),
            ToolParameter(
                name="priority",
                type="string",
                description="Filter by priority level",
                required=False,
                enum=["low", "medium", "high", "urgent"],
            ),
            ToolParameter(
                name="project_id",
                type="string",
                description="Filter by project ID",
                required=False,
            ),
            ToolParameter(
                name="due_before",
                type="string",
                description="Filter tasks due before this date (ISO format: YYYY-MM-DD)",
                required=False,
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="Maximum number of tasks to return",
                required=False,
                default=20,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            # Parse due_before if provided
            due_before = None
            if kwargs.get("due_before"):
                due_before = datetime.fromisoformat(kwargs["due_before"])

            tasks = storage.get_tasks(
                user_id=user_id,
                status=kwargs.get("status"),
                priority=kwargs.get("priority"),
                project_id=kwargs.get("project_id"),
                due_before=due_before,
            )

            # Apply limit
            limit = kwargs.get("limit", 20)
            tasks = tasks[:limit]

            return ToolResult.ok(
                data={
                    "tasks": tasks,
                    "count": len(tasks),
                },
                query_params=kwargs,
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to get tasks: {str(e)}")


@register_tool
class CreateTaskTool(BaseTool):
    """Create a new task."""

    name = "create_task"
    description = "Create a new task for the user. Use this when the user wants to add something to their to-do list."
    category = ToolCategory.TASKS
    is_write = True

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="title",
                type="string",
                description="The task title/description",
                required=True,
            ),
            ToolParameter(
                name="description",
                type="string",
                description="Additional details about the task",
                required=False,
            ),
            ToolParameter(
                name="priority",
                type="string",
                description="Task priority level",
                required=False,
                default="medium",
                enum=["low", "medium", "high", "urgent"],
            ),
            ToolParameter(
                name="due_date",
                type="string",
                description="Due date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
                required=False,
            ),
            ToolParameter(
                name="project_id",
                type="string",
                description="ID of the project this task belongs to",
                required=False,
            ),
            ToolParameter(
                name="tags",
                type="array",
                description="List of tags for the task",
                required=False,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            # Parse due_date if provided
            due_date = None
            if kwargs.get("due_date"):
                due_date = datetime.fromisoformat(kwargs["due_date"])

            task_id = storage.create_task(
                user_id=user_id,
                title=kwargs["title"],
                description=kwargs.get("description", ""),
                priority=kwargs.get("priority", "medium"),
                due_date=due_date,
                project_id=kwargs.get("project_id"),
                tags=kwargs.get("tags"),
                source="alfred",
            )

            if task_id:
                return ToolResult.ok(
                    data={
                        "task_id": task_id,
                        "message": f"Created task: {kwargs['title']}",
                    }
                )
            else:
                return ToolResult.fail("Failed to create task")

        except Exception as e:
            return ToolResult.fail(f"Failed to create task: {str(e)}")


@register_tool
class CompleteTaskTool(BaseTool):
    """Mark a task as completed."""

    name = "complete_task"
    description = "Mark a task as completed. Use the task ID."
    category = ToolCategory.TASKS
    is_write = True

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="task_id",
                type="string",
                description="The ID of the task to complete",
                required=True,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            success = storage.complete_task(
                task_id=kwargs["task_id"],
                user_id=user_id,
            )

            if success:
                return ToolResult.ok(
                    data={"message": "Task marked as completed"}
                )
            else:
                return ToolResult.fail("Task not found or already completed")

        except Exception as e:
            return ToolResult.fail(f"Failed to complete task: {str(e)}")


@register_tool
class UpdateTaskTool(BaseTool):
    """Update an existing task."""

    name = "update_task"
    description = "Update an existing task's details."
    category = ToolCategory.TASKS
    is_write = True

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="task_id",
                type="string",
                description="The ID of the task to update",
                required=True,
            ),
            ToolParameter(
                name="title",
                type="string",
                description="New task title",
                required=False,
            ),
            ToolParameter(
                name="description",
                type="string",
                description="New task description",
                required=False,
            ),
            ToolParameter(
                name="priority",
                type="string",
                description="New priority level",
                required=False,
                enum=["low", "medium", "high", "urgent"],
            ),
            ToolParameter(
                name="due_date",
                type="string",
                description="New due date (ISO format)",
                required=False,
            ),
            ToolParameter(
                name="status",
                type="string",
                description="New status",
                required=False,
                enum=["pending", "in_progress", "completed", "cancelled"],
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        task_id = kwargs.pop("task_id")

        # Build updates dict
        updates = {}
        for key in ["title", "description", "priority", "status"]:
            if kwargs.get(key):
                updates[key] = kwargs[key]

        if kwargs.get("due_date"):
            updates["due_date"] = datetime.fromisoformat(kwargs["due_date"])

        if not updates:
            return ToolResult.fail("No updates provided")

        try:
            success = storage.update_task(
                task_id=task_id,
                user_id=user_id,
                updates=updates,
            )

            if success:
                return ToolResult.ok(
                    data={"message": f"Task updated successfully"}
                )
            else:
                return ToolResult.fail("Task not found")

        except Exception as e:
            return ToolResult.fail(f"Failed to update task: {str(e)}")


@register_tool
class GetTasksDueTodayTool(BaseTool):
    """Get tasks due today."""

    name = "get_tasks_due_today"
    description = "Get all tasks that are due today."
    category = ToolCategory.TASKS
    is_write = False

    def get_parameters(self) -> List[ToolParameter]:
        return []  # No parameters needed

    async def execute(self, **kwargs) -> ToolResult:
        storage = self.context.get("storage")
        user_id = self.context.get("user_id")

        if not storage or not user_id:
            return ToolResult.fail("Missing storage or user context")

        try:
            tasks = storage.get_tasks_due_today(user_id=user_id)

            return ToolResult.ok(
                data={
                    "tasks": tasks,
                    "count": len(tasks),
                    "date": date.today().isoformat(),
                }
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to get today's tasks: {str(e)}")
