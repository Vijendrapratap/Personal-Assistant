"""
Task Agent - Handles all task-related operations

Responsibilities:
- Create tasks from conversation
- Update task status and details
- Query and filter tasks
- Prioritize and organize tasks
- Track task completion
"""

from typing import Set, Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import re

from alfred.core.agents.base import (
    BaseAgent,
    AgentType,
    AgentCapability,
    AgentContext,
    AgentResult,
    AgentAction
)


class TaskAgent(BaseAgent):
    """Agent specialized in task management."""

    TASK_KEYWORDS = [
        "task", "todo", "to-do", "to do", "reminder",
        "need to", "have to", "must", "should",
        "deadline", "due", "by tomorrow", "by end of",
        "create", "add", "schedule", "plan",
        "complete", "done", "finish", "completed",
        "priority", "urgent", "important", "critical",
        "pending", "overdue", "upcoming"
    ]

    EXTRACTION_PROMPT = """
    Analyze this message and extract any tasks mentioned.

    User message: {user_input}

    Context:
    - User's current projects: {projects}
    - Recent tasks: {recent_tasks}

    Extract:
    1. Task title (clear, actionable)
    2. Project it belongs to (if mentioned or inferable)
    3. Priority (high/medium/low based on urgency words)
    4. Due date (if mentioned, parse to ISO format)
    5. Action type: create/update/complete/query

    Return JSON:
    {{
        "action": "create|update|complete|query|none",
        "tasks": [
            {{
                "title": "...",
                "project": "project name or null",
                "priority": "high|medium|low",
                "due_date": "YYYY-MM-DD or null",
                "description": "additional context"
            }}
        ],
        "query": {{
            "type": "today|overdue|project|priority|all",
            "filter": "filter value if applicable"
        }}
    }}

    If no task-related content, return {{"action": "none", "tasks": [], "query": null}}
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.TASK

    @property
    def capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.CREATE_TASK,
            AgentCapability.UPDATE_TASK,
            AgentCapability.QUERY_TASKS,
            AgentCapability.PRIORITIZE,
        }

    def _has_relevant_keywords(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.TASK_KEYWORDS)

    async def can_handle(self, context: AgentContext) -> float:
        """Determine confidence for handling this request."""
        text = context.user_input.lower()

        # Check for explicit task keywords
        keyword_matches = sum(1 for kw in self.TASK_KEYWORDS if kw in text)

        if keyword_matches >= 3:
            return 0.95
        elif keyword_matches >= 2:
            return 0.8
        elif keyword_matches >= 1:
            return 0.6

        # Check for task-like patterns
        task_patterns = [
            r"(?:i |we )(?:need|have|must|should) to",
            r"remind me to",
            r"don't forget to",
            r"add .+ to (?:my |the )?(?:list|tasks)",
            r"what.+(?:pending|todo|to-do|tasks)",
        ]

        for pattern in task_patterns:
            if re.search(pattern, text):
                return 0.75

        return 0.0

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute task-related operations."""
        try:
            # Extract task intent using LLM
            extraction = await self._extract_task_intent(context)

            if extraction["action"] == "none":
                return self._create_result(
                    success=True,
                    data={"action": "none"},
                    response_fragments=[]
                )

            # Execute based on action type
            if extraction["action"] == "create":
                return await self._handle_create(context, extraction["tasks"])
            elif extraction["action"] == "update":
                return await self._handle_update(context, extraction["tasks"])
            elif extraction["action"] == "complete":
                return await self._handle_complete(context, extraction["tasks"])
            elif extraction["action"] == "query":
                return await self._handle_query(context, extraction["query"])

            return self._create_result(success=True, data=extraction)

        except Exception as e:
            return self._create_result(
                success=False,
                error=str(e)
            )

    async def _extract_task_intent(self, context: AgentContext) -> Dict[str, Any]:
        """Use LLM to extract task intent from user input."""
        # Get project names for context
        projects = []
        if self.storage:
            try:
                projects = self.storage.get_projects(context.user_id, status="active")
                projects = [p["name"] for p in projects[:10]]
            except Exception:
                pass

        # Get recent tasks for context
        recent_tasks = []
        if context.related_tasks:
            recent_tasks = [t["title"] for t in context.related_tasks[:5]]

        prompt = self.EXTRACTION_PROMPT.format(
            user_input=context.user_input,
            projects=", ".join(projects) if projects else "None",
            recent_tasks=", ".join(recent_tasks) if recent_tasks else "None"
        )

        response = await self._generate_with_llm(prompt)

        # Parse JSON response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        return {"action": "none", "tasks": [], "query": None}

    async def _handle_create(
        self,
        context: AgentContext,
        tasks: List[Dict[str, Any]]
    ) -> AgentResult:
        """Handle task creation."""
        actions = []
        created_tasks = []

        for task_data in tasks:
            try:
                # Find project ID if project name provided
                project_id = None
                if task_data.get("project") and self.storage:
                    projects = self.storage.get_projects(context.user_id)
                    for p in projects:
                        if task_data["project"].lower() in p["name"].lower():
                            project_id = p["project_id"]
                            break

                # Parse due date
                due_date = None
                if task_data.get("due_date"):
                    try:
                        due_date = datetime.fromisoformat(task_data["due_date"])
                    except ValueError:
                        # Try to parse relative dates
                        due_date = self._parse_relative_date(task_data["due_date"])

                # Create the task
                if self.storage:
                    task_id = self.storage.create_task(
                        user_id=context.user_id,
                        title=task_data["title"],
                        project_id=project_id,
                        description=task_data.get("description", ""),
                        priority=task_data.get("priority", "medium"),
                        due_date=due_date,
                        source="alfred"
                    )

                    if task_id:
                        created_tasks.append({
                            "task_id": task_id,
                            "title": task_data["title"],
                            "priority": task_data.get("priority", "medium"),
                            "due_date": due_date.isoformat() if due_date else None
                        })

                        actions.append(AgentAction(
                            action_type="created_task",
                            description=f"Created task: {task_data['title']}",
                            data={"task_id": task_id, "title": task_data["title"]},
                            success=True
                        ))

            except Exception as e:
                actions.append(AgentAction(
                    action_type="create_task_failed",
                    description=f"Failed to create task: {task_data.get('title', 'Unknown')}",
                    data={"error": str(e)},
                    success=False,
                    error=str(e)
                ))

        # Generate response fragment
        fragments = []
        if created_tasks:
            if len(created_tasks) == 1:
                task = created_tasks[0]
                fragment = f"Created task: **{task['title']}**"
                if task.get("due_date"):
                    fragment += f" (due {task['due_date']})"
                fragments.append(fragment)
            else:
                fragments.append(f"Created {len(created_tasks)} tasks:")
                for task in created_tasks:
                    fragments.append(f"  - {task['title']}")

        return self._create_result(
            success=len(created_tasks) > 0,
            data={"created_tasks": created_tasks},
            actions=actions,
            response_fragments=fragments,
            suggestions=["Would you like to set a reminder?"] if created_tasks else []
        )

    async def _handle_update(
        self,
        context: AgentContext,
        tasks: List[Dict[str, Any]]
    ) -> AgentResult:
        """Handle task updates."""
        # Implementation for task updates
        return self._create_result(
            success=True,
            data={"action": "update", "tasks": tasks},
            response_fragments=["Task update functionality"]
        )

    async def _handle_complete(
        self,
        context: AgentContext,
        tasks: List[Dict[str, Any]]
    ) -> AgentResult:
        """Handle marking tasks as complete."""
        actions = []
        completed = []

        for task_data in tasks:
            # Try to find the task by title
            if self.storage:
                all_tasks = self.storage.get_tasks(
                    context.user_id,
                    status="pending"
                )

                for task in all_tasks:
                    if task_data["title"].lower() in task["title"].lower():
                        success = self.storage.complete_task(
                            task["task_id"],
                            context.user_id
                        )
                        if success:
                            completed.append(task["title"])
                            actions.append(AgentAction(
                                action_type="completed_task",
                                description=f"Marked complete: {task['title']}",
                                data={"task_id": task["task_id"]},
                                success=True
                            ))
                        break

        fragments = []
        if completed:
            fragments.append(f"Marked as complete: {', '.join(completed)}")

        return self._create_result(
            success=len(completed) > 0,
            data={"completed": completed},
            actions=actions,
            response_fragments=fragments
        )

    async def _handle_query(
        self,
        context: AgentContext,
        query: Dict[str, Any]
    ) -> AgentResult:
        """Handle task queries."""
        if not self.storage:
            return self._create_result(
                success=False,
                error="Storage not available"
            )

        query_type = query.get("type", "all")
        tasks = []

        try:
            if query_type == "today":
                tasks = self.storage.get_tasks_due_today(context.user_id)
            elif query_type == "overdue":
                all_tasks = self.storage.get_tasks(context.user_id, status="pending")
                today = datetime.now().date()
                tasks = [
                    t for t in all_tasks
                    if t.get("due_date") and
                    datetime.fromisoformat(str(t["due_date"])).date() < today
                ]
            elif query_type == "priority":
                priority = query.get("filter", "high")
                tasks = self.storage.get_tasks(
                    context.user_id,
                    priority=priority,
                    status="pending"
                )
            elif query_type == "project":
                # Find project and get its tasks
                project_name = query.get("filter", "")
                projects = self.storage.get_projects(context.user_id)
                for p in projects:
                    if project_name.lower() in p["name"].lower():
                        tasks = self.storage.get_tasks(
                            context.user_id,
                            project_id=p["project_id"]
                        )
                        break
            else:
                tasks = self.storage.get_tasks(context.user_id, status="pending")

        except Exception as e:
            return self._create_result(success=False, error=str(e))

        # Generate response fragment
        fragments = []
        if tasks:
            fragments.append(f"Found {len(tasks)} task(s):")
            for task in tasks[:5]:  # Limit to 5 for readability
                status_icon = "[ ]" if task.get("status") == "pending" else "[x]"
                priority_icon = {"high": "!", "medium": "-", "low": "."}.get(
                    task.get("priority", "medium"), "-"
                )
                fragments.append(f"  {status_icon} ({priority_icon}) {task['title']}")

            if len(tasks) > 5:
                fragments.append(f"  ... and {len(tasks) - 5} more")
        else:
            fragments.append("No tasks found matching your criteria.")

        return self._create_result(
            success=True,
            data={"tasks": tasks, "count": len(tasks)},
            response_fragments=fragments
        )

    def _parse_relative_date(self, date_str: str) -> Optional[datetime]:
        """Parse relative date strings like 'tomorrow', 'next week'."""
        date_str = date_str.lower().strip()
        today = datetime.now()

        if date_str == "today":
            return today
        elif date_str == "tomorrow":
            return today + timedelta(days=1)
        elif date_str == "next week":
            return today + timedelta(weeks=1)
        elif "end of week" in date_str:
            days_until_friday = (4 - today.weekday()) % 7
            return today + timedelta(days=days_until_friday)
        elif "end of month" in date_str:
            next_month = today.replace(day=28) + timedelta(days=4)
            return next_month.replace(day=1) - timedelta(days=1)

        return None
