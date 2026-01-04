"""
Alfred Orchestrator

Central brain that coordinates all agents:
1. Analyzes user intent
2. Routes to appropriate agents
3. Executes agents (parallel when possible)
4. Synthesizes unified response
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from alfred.core.agents.base import (
    BaseAgent,
    AgentType,
    AgentContext,
    AgentResult,
    RoutingDecision
)
from alfred.core.agents.task_agent import TaskAgent
from alfred.core.agents.memory_agent import MemoryAgent
from alfred.core.agents.planning_agent import PlanningAgent


@dataclass
class OrchestratorConfig:
    """Orchestrator configuration."""
    max_parallel_agents: int = 5
    response_timeout_seconds: int = 30
    enable_learning: bool = True


class IntentRouter:
    """Routes user requests to appropriate agents."""

    ROUTING_PATTERNS = {
        "task": [
            (r"(?:create|add|new) (?:a )?task", [AgentType.TASK, AgentType.MEMORY]),
            (r"(?:mark|complete|done|finish)", [AgentType.TASK, AgentType.MEMORY]),
            (r"(?:my |today'?s? )?tasks", [AgentType.TASK, AgentType.MEMORY]),
            (r"(?:what|show).+(?:pending|todo|to-do)", [AgentType.TASK, AgentType.MEMORY]),
            (r"remind me to", [AgentType.TASK, AgentType.MEMORY]),
        ],
        "planning": [
            (r"how (?:should|do|can) (?:i|we)", [AgentType.PLANNING, AgentType.MEMORY]),
            (r"help me (?:plan|prepare|organize)", [AgentType.PLANNING, AgentType.MEMORY, AgentType.TASK]),
            (r"prioritize", [AgentType.PLANNING, AgentType.TASK, AgentType.MEMORY]),
            (r"break.+down", [AgentType.PLANNING, AgentType.MEMORY]),
            (r"what.+(?:first|next|start)", [AgentType.PLANNING, AgentType.MEMORY]),
        ],
        "memory": [
            (r"(?:who|what) is (\w+)", [AgentType.MEMORY]),
            (r"(?:do you )?remember", [AgentType.MEMORY]),
            (r"tell me about", [AgentType.MEMORY]),
            (r"what do you know about", [AgentType.MEMORY]),
        ],
        "project": [
            (r"project (?:update|status)", [AgentType.PROJECT, AgentType.MEMORY]),
            (r"(?:my |all )?projects", [AgentType.PROJECT, AgentType.MEMORY]),
        ],
    }

    ROUTING_PROMPT = """Classify this user message for agent routing.

User: {user_input}

Agents:
- TASK: Creating/updating/managing tasks
- MEMORY: Recalling information, preferences, past conversations
- PLANNING: Breaking down goals, strategy, prioritization
- CALENDAR: Scheduling, availability (when integrated)
- EMAIL: Email operations (when integrated)
- PROJECT: Project updates and management

Return JSON:
{{"intent": "brief description", "topic": "main subject", "required_agents": ["AGENT1"], "priority": "high|medium|low"}}"""

    def __init__(self, llm):
        self.llm = llm

    async def route(self, user_input: str, context: Dict[str, Any] = None) -> RoutingDecision:
        """Determine which agents handle this request."""
        result = self._fast_route(user_input.lower())
        if result:
            return result
        return await self._llm_route(user_input)

    def _fast_route(self, text: str) -> Optional[RoutingDecision]:
        """Fast keyword-based routing."""
        for intent_type, patterns in self.ROUTING_PATTERNS.items():
            for pattern, agents in patterns:
                match = re.search(pattern, text)
                if match:
                    return RoutingDecision(
                        intent=intent_type,
                        topic=match.group(1) if match.groups() else "",
                        required_agents=agents,
                        priority="medium",
                        confidence=0.85
                    )
        return None

    async def _llm_route(self, user_input: str) -> RoutingDecision:
        """LLM-based routing for complex cases."""
        try:
            response = self.llm.generate_response(
                self.ROUTING_PROMPT.format(user_input=user_input), []
            )

            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                agents = []
                for agent_str in data.get("required_agents", []):
                    try:
                        agents.append(AgentType(agent_str.lower()))
                    except ValueError:
                        pass

                if AgentType.MEMORY not in agents:
                    agents.append(AgentType.MEMORY)

                return RoutingDecision(
                    intent=data.get("intent", "general"),
                    topic=data.get("topic", ""),
                    required_agents=agents,
                    priority=data.get("priority", "medium"),
                    confidence=0.9
                )
        except Exception as e:
            print(f"LLM routing error: {e}")

        return RoutingDecision(
            intent="general",
            topic="",
            required_agents=[AgentType.MEMORY],
            priority="medium",
            confidence=0.5
        )


class Orchestrator:
    """Coordinates all Alfred agents."""

    SYNTHESIS_PROMPT = """You are Alfred, the butler. Synthesize these results into one response.

User said: "{user_input}"

Results:
{agent_results}

Guidelines:
- Professional British tone, address as "Sir" or "Ma'am"
- Be concise but thorough
- Include actions taken
- Offer relevant suggestions"""

    def __init__(self, llm, storage, config: OrchestratorConfig = None):
        self.llm = llm
        self.storage = storage
        self.config = config or OrchestratorConfig()
        self.router = IntentRouter(llm)
        self.agents: Dict[AgentType, BaseAgent] = {}
        self._init_agents()

    def _init_agents(self):
        """Initialize available agents."""
        agent_classes = [
            (AgentType.TASK, TaskAgent),
            (AgentType.MEMORY, MemoryAgent),
            (AgentType.PLANNING, PlanningAgent),
        ]

        for agent_type, agent_class in agent_classes:
            try:
                self.agents[agent_type] = agent_class(
                    llm=self.llm,
                    storage=self.storage,
                    config=self.config
                )
            except Exception as e:
                print(f"Failed to init {agent_type.value}: {e}")

    async def process(self, user_input: str, user_id: str) -> str:
        """Process user request through agent pipeline."""
        try:
            routing = await self.router.route(user_input)
            context = await self._build_context(user_id, user_input, routing)

            # Execute memory agent first for context
            memory_context = {}
            if AgentType.MEMORY in self.agents:
                try:
                    result = await self.agents[AgentType.MEMORY].execute(context)
                    memory_context = result.data.get("context", {})
                    context.user_preferences = memory_context.get("preferences", {})
                    context.related_projects = memory_context.get("related_projects", [])
                    context.related_tasks = memory_context.get("related_tasks", [])
                except Exception as e:
                    print(f"Memory agent error: {e}")

            # Execute other agents in parallel
            other_agents = [
                a for a in routing.required_agents
                if a != AgentType.MEMORY and a in self.agents
            ]

            results = []
            if other_agents:
                tasks = [self.agents[t].execute(context) for t in other_agents]
                agent_results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, result in enumerate(agent_results):
                    if isinstance(result, AgentResult):
                        results.append(result)

            # Synthesize response
            response = await self._synthesize(
                user_input, user_id, results, memory_context
            )

            # Store interaction
            if self.config.enable_learning:
                await self._store_interaction(user_id, user_input, response, results)

            return response

        except Exception as e:
            return f"I apologize, Sir, but I encountered an issue: {str(e)}"

    async def _build_context(
        self, user_id: str, user_input: str, routing: RoutingDecision
    ) -> AgentContext:
        """Build context for agents."""
        context = AgentContext(
            user_id=user_id,
            user_input=user_input,
            intent=routing.intent,
            topic=routing.topic,
            entities=routing.entities
        )

        if self.storage:
            try:
                profile = self.storage.get_user_profile(user_id)
                if profile:
                    context.user_profile = profile
                context.conversation_history = self.storage.get_chat_history(
                    user_id, limit=10
                )
            except Exception:
                pass

        return context

    async def _synthesize(
        self,
        user_input: str,
        user_id: str,
        results: List[AgentResult],
        memory_context: Dict[str, Any]
    ) -> str:
        """Synthesize agent results into response."""
        if not results or all(not r.response_fragments for r in results):
            return await self._simple_response(user_input, user_id, memory_context)

        all_fragments = []
        all_actions = []
        all_suggestions = []

        for result in results:
            all_fragments.extend(result.response_fragments)
            all_actions.extend(result.actions_taken)
            all_suggestions.extend(result.suggestions)

        # Simple synthesis for straightforward results
        if len(all_fragments) <= 5 and not all_suggestions:
            parts = ["Very good, Sir." if all_actions else "Certainly, Sir."]
            parts.extend(all_fragments)
            if all_suggestions:
                parts.extend(all_suggestions[:2])
            return "\n".join(parts)

        # LLM synthesis for complex results
        results_text = []
        for r in results:
            agent = r.agent_type.value.title()
            results_text.append(f"\n{agent}: {', '.join(r.response_fragments)}")
            if r.actions_taken:
                results_text.append(f"  Actions: {', '.join(r.actions_taken)}")

        prompt = self.SYNTHESIS_PROMPT.format(
            user_input=user_input,
            agent_results="\n".join(results_text)
        )

        return self.llm.generate_response(prompt, [])

    async def _simple_response(
        self, user_input: str, user_id: str, memory_context: Dict[str, Any]
    ) -> str:
        """Generate simple conversational response."""
        user_name = "Sir"
        if self.storage:
            try:
                profile = self.storage.get_user_profile(user_id)
                if profile and profile.get("name"):
                    user_name = profile["name"]
            except Exception:
                pass

        prompt = f"""You are Alfred, the butler. Respond conversationally.

User ({user_name}) said: "{user_input}"

Guidelines:
- Be helpful and personable
- Keep response concise (2-4 sentences)
- Professional British tone"""

        return self.llm.generate_response(prompt, [])

    async def _store_interaction(
        self, user_id: str, user_input: str, response: str, results: List[AgentResult]
    ):
        """Store interaction for learning."""
        if AgentType.MEMORY in self.agents:
            try:
                actions = [r.actions_taken for r in results]
                await self.agents[AgentType.MEMORY].store_interaction(
                    user_id=user_id,
                    user_input=user_input,
                    response=response,
                    actions=actions
                )
            except Exception as e:
                print(f"Failed to store interaction: {e}")

    def get_available_agents(self) -> List[AgentType]:
        """Get available agent types."""
        return list(self.agents.keys())


def create_orchestrator(llm, storage, config: OrchestratorConfig = None) -> Orchestrator:
    """Create orchestrator instance."""
    return Orchestrator(llm=llm, storage=storage, config=config)
