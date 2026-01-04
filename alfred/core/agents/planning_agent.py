"""
Planning Agent - Strategic thinking and goal breakdown

Responsibilities:
- Break down large goals into actionable steps
- Suggest next steps based on context
- Help prioritize competing demands
- Provide strategic advice
- Estimate effort for tasks
"""

from typing import Set, Dict, Any, List
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


class PlanningAgent(BaseAgent):
    """Agent specialized in planning and strategy."""

    PLANNING_KEYWORDS = [
        "plan", "planning", "strategy", "strategize",
        "how should", "how do i", "how can i",
        "what should", "where do i start",
        "break down", "steps", "roadmap",
        "prioritize", "priority", "first",
        "overwhelmed", "too much", "don't know where",
        "goal", "achieve", "accomplish",
        "prepare", "preparation", "get ready"
    ]

    PLANNING_PROMPT = """
    You are a strategic planning assistant. The user needs help planning or strategizing.

    User request: {user_input}

    Context:
    - Current projects: {projects}
    - Pending high-priority tasks: {high_priority_tasks}
    - Today's tasks: {today_tasks}
    - User's role/work type: {work_type}

    Provide strategic advice:
    1. Break down the goal into concrete steps if it's a large undertaking
    2. Suggest prioritization if there are competing demands
    3. Identify dependencies and blockers
    4. Recommend next immediate action

    Return JSON:
    {{
        "goal_summary": "What the user wants to achieve",
        "steps": [
            {{
                "order": 1,
                "title": "Step title",
                "description": "What to do",
                "estimated_time": "time estimate",
                "dependencies": ["what needs to be done first"],
                "priority": "high|medium|low"
            }}
        ],
        "immediate_action": "The very next thing to do",
        "potential_blockers": ["possible issues to watch for"],
        "success_criteria": "How to know when done",
        "strategic_notes": "Additional strategic advice"
    }}
    """

    PRIORITIZATION_PROMPT = """
    Help prioritize these competing demands for the user.

    User's question: {user_input}

    Current tasks:
    {tasks}

    Current projects:
    {projects}

    User context: {context}

    Consider:
    1. Deadlines and urgency
    2. Impact and importance
    3. Dependencies
    4. User's energy and focus patterns (if known)

    Return JSON:
    {{
        "prioritized_list": [
            {{
                "item": "task or project name",
                "priority_rank": 1,
                "reasoning": "why this priority",
                "suggested_time": "when to work on this",
                "time_needed": "estimated duration"
            }}
        ],
        "recommendation": "Overall recommendation",
        "things_to_defer": ["items that can wait"],
        "things_to_delegate": ["items that could be delegated if possible"]
    }}
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.PLANNING

    @property
    def capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.BREAK_DOWN_GOAL,
            AgentCapability.SUGGEST_NEXT_STEPS,
            AgentCapability.ESTIMATE_EFFORT,
            AgentCapability.PRIORITIZE,
        }

    def _has_relevant_keywords(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.PLANNING_KEYWORDS)

    async def can_handle(self, context: AgentContext) -> float:
        """Determine confidence for handling this request."""
        text = context.user_input.lower()

        # Check for explicit planning keywords
        keyword_matches = sum(1 for kw in self.PLANNING_KEYWORDS if kw in text)

        if keyword_matches >= 2:
            return 0.9
        elif keyword_matches >= 1:
            return 0.7

        # Check for planning-like patterns
        planning_patterns = [
            r"how (?:should|do|can) (?:i|we)",
            r"what.+(?:first|next|start)",
            r"help me (?:plan|prepare|organize)",
            r"(?:too much|overwhelmed|don't know)",
            r"break.+down",
            r"step.+by.+step",
        ]

        for pattern in planning_patterns:
            if re.search(pattern, text):
                return 0.8

        return 0.0

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute planning operations."""
        try:
            # Determine if this is a goal breakdown or prioritization request
            is_prioritization = self._is_prioritization_request(context.user_input)

            if is_prioritization:
                return await self._handle_prioritization(context)
            else:
                return await self._handle_planning(context)

        except Exception as e:
            return self._create_result(
                success=False,
                error=str(e)
            )

    def _is_prioritization_request(self, text: str) -> bool:
        """Check if this is a prioritization request vs goal planning."""
        prioritization_signals = [
            "prioritize", "priority", "first",
            "what should i do", "where should i start",
            "too much", "overwhelmed", "focus on"
        ]
        return any(signal in text.lower() for signal in prioritization_signals)

    async def _handle_planning(self, context: AgentContext) -> AgentResult:
        """Handle goal breakdown and planning requests."""
        # Gather context
        projects = []
        high_priority = []
        today_tasks = []
        work_type = "professional"

        if self.storage:
            try:
                projects = self.storage.get_projects(context.user_id, status="active")
                projects = [{"name": p["name"], "role": p.get("role")} for p in projects[:5]]

                tasks = self.storage.get_tasks(context.user_id, priority="high")
                high_priority = [t["title"] for t in tasks if t.get("status") == "pending"][:5]

                today = self.storage.get_tasks_due_today(context.user_id)
                today_tasks = [t["title"] for t in today][:5]

                profile = self.storage.get_user_profile(context.user_id)
                work_type = profile.get("work_type", "professional") if profile else "professional"
            except Exception:
                pass

        prompt = self.PLANNING_PROMPT.format(
            user_input=context.user_input,
            projects=json.dumps(projects) if projects else "None",
            high_priority_tasks=", ".join(high_priority) if high_priority else "None",
            today_tasks=", ".join(today_tasks) if today_tasks else "None",
            work_type=work_type
        )

        response = await self._generate_with_llm(prompt)

        # Parse the plan
        plan = self._parse_json_response(response)

        if not plan:
            return self._create_result(
                success=True,
                data={"raw_response": response},
                response_fragments=[response]
            )

        # Build response fragments
        fragments = []

        if plan.get("goal_summary"):
            fragments.append(f"**Goal:** {plan['goal_summary']}")

        if plan.get("steps"):
            fragments.append("\n**Action Plan:**")
            for step in plan["steps"]:
                order = step.get("order", "")
                title = step.get("title", "")
                time_est = step.get("estimated_time", "")
                priority = step.get("priority", "")

                priority_icon = {"high": "[!]", "medium": "[-]", "low": "[.]"}.get(priority, "")
                time_str = f" (~{time_est})" if time_est else ""

                fragments.append(f"{order}. {priority_icon} {title}{time_str}")

                if step.get("description") and step["description"] != title:
                    fragments.append(f"   {step['description']}")

        if plan.get("immediate_action"):
            fragments.append(f"\n**Start with:** {plan['immediate_action']}")

        if plan.get("potential_blockers"):
            blockers = plan["potential_blockers"]
            if blockers and blockers[0]:  # Check not empty
                fragments.append("\n**Watch out for:**")
                for blocker in blockers[:3]:
                    fragments.append(f"  - {blocker}")

        if plan.get("strategic_notes"):
            fragments.append(f"\n**Note:** {plan['strategic_notes']}")

        # Create suggested tasks from the plan
        suggestions = []
        if plan.get("steps"):
            first_step = plan["steps"][0]
            suggestions.append(
                f"Would you like me to create a task for: {first_step.get('title', 'the first step')}?"
            )

        return self._create_result(
            success=True,
            data={"plan": plan},
            response_fragments=fragments,
            suggestions=suggestions
        )

    async def _handle_prioritization(self, context: AgentContext) -> AgentResult:
        """Handle prioritization requests."""
        # Gather all tasks and projects
        tasks = []
        projects = []
        user_context = ""

        if self.storage:
            try:
                all_tasks = self.storage.get_tasks(context.user_id, status="pending")
                tasks = [
                    {
                        "title": t["title"],
                        "priority": t.get("priority", "medium"),
                        "due_date": str(t.get("due_date", "")),
                        "project": t.get("project_name", "")
                    }
                    for t in all_tasks[:15]
                ]

                all_projects = self.storage.get_projects(context.user_id, status="active")
                projects = [
                    {
                        "name": p["name"],
                        "role": p.get("role", ""),
                        "status": p.get("status", "")
                    }
                    for p in all_projects[:10]
                ]

                # Get user context
                profile = self.storage.get_user_profile(context.user_id)
                if profile:
                    user_context = f"Work type: {profile.get('work_type', 'Unknown')}"
                    if profile.get("bio"):
                        user_context += f", Bio: {profile['bio'][:100]}"

            except Exception:
                pass

        if not tasks and not projects:
            return self._create_result(
                success=True,
                data={},
                response_fragments=[
                    "You don't have any pending tasks or active projects to prioritize.",
                    "Would you like to add some tasks first?"
                ]
            )

        prompt = self.PRIORITIZATION_PROMPT.format(
            user_input=context.user_input,
            tasks=json.dumps(tasks, indent=2),
            projects=json.dumps(projects, indent=2),
            context=user_context
        )

        response = await self._generate_with_llm(prompt)
        prioritization = self._parse_json_response(response)

        if not prioritization:
            return self._create_result(
                success=True,
                data={"raw_response": response},
                response_fragments=[response]
            )

        # Build response
        fragments = []

        if prioritization.get("recommendation"):
            fragments.append(f"**My recommendation:** {prioritization['recommendation']}")

        if prioritization.get("prioritized_list"):
            fragments.append("\n**Priority order:**")
            for item in prioritization["prioritized_list"][:5]:
                rank = item.get("priority_rank", "")
                name = item.get("item", "")
                time_needed = item.get("time_needed", "")
                reasoning = item.get("reasoning", "")

                fragments.append(f"{rank}. **{name}**")
                if time_needed:
                    fragments.append(f"   Time needed: {time_needed}")
                if reasoning:
                    fragments.append(f"   Reason: {reasoning}")

        if prioritization.get("things_to_defer"):
            defer_list = [d for d in prioritization["things_to_defer"] if d]
            if defer_list:
                fragments.append("\n**Can wait:**")
                for item in defer_list[:3]:
                    fragments.append(f"  - {item}")

        return self._create_result(
            success=True,
            data={"prioritization": prioritization},
            response_fragments=fragments
        )

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        return {}

    async def suggest_next_steps(
        self,
        user_id: str,
        current_focus: str = None
    ) -> List[str]:
        """
        Suggest next steps based on current state.
        Can be called proactively by the system.
        """
        if not self.storage:
            return []

        try:
            # Get pending high priority tasks
            tasks = self.storage.get_tasks(user_id, priority="high", status="pending")

            # Get overdue tasks
            all_tasks = self.storage.get_tasks(user_id, status="pending")
            today = datetime.now().date()
            overdue = [
                t for t in all_tasks
                if t.get("due_date") and
                datetime.fromisoformat(str(t["due_date"])).date() < today
            ]

            suggestions = []

            if overdue:
                suggestions.append(
                    f"You have {len(overdue)} overdue task(s). "
                    f"Consider addressing: {overdue[0]['title']}"
                )

            if tasks:
                top_task = tasks[0]
                suggestions.append(
                    f"Your top priority: {top_task['title']}"
                )

            return suggestions

        except Exception:
            return []
