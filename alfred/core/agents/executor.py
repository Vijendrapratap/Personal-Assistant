"""
Agent Executor.

The core execution loop for Alfred agents. Handles the think-act-observe cycle
with tool calling capabilities.
"""

from typing import List, Optional, Dict, Any, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

from alfred.infrastructure.llm.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    ToolDefinition,
)
from alfred.core.tools.base import BaseTool, ToolResult
from alfred.core.tools.registry import ToolRegistry, get_tool_registry

logger = logging.getLogger(__name__)


@dataclass
class ExecutionStep:
    """A single step in the agent execution."""
    step_number: int
    thought: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[ToolResult] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "thought": self.thought,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "tool_result": self.tool_result.to_string() if self.tool_result else None,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ExecutionResult:
    """Result of agent execution."""
    success: bool
    response: str
    steps: List[ExecutionStep] = field(default_factory=list)
    tool_calls_made: int = 0
    total_tokens: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "response": self.response,
            "steps": [s.to_dict() for s in self.steps],
            "tool_calls_made": self.tool_calls_made,
            "total_tokens": self.total_tokens,
            "error": self.error,
        }


@dataclass
class AgentContext:
    """Context for agent execution."""
    user_id: str
    user_name: Optional[str] = None
    timezone: str = "UTC"
    storage: Any = None  # MemoryStorage instance
    knowledge_graph: Any = None  # KnowledgeGraphProvider instance
    notification_provider: Any = None
    conversation_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    max_iterations: int = 10
    rag_context: str = ""  # Relevant context from vector store (RAG)

    def to_tool_context(self) -> Dict[str, Any]:
        """Convert to context dict for tools."""
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "timezone": self.timezone,
            "storage": self.storage,
            "knowledge_graph": self.knowledge_graph,
            "notification_provider": self.notification_provider,
        }

    def get_system_context(self) -> str:
        """Get formatted context for system prompt."""
        parts = []
        if self.rag_context:
            parts.append(f"## Relevant Context\n{self.rag_context}")
        return "\n\n".join(parts)


class AgentExecutor:
    """
    Main agent execution loop.

    Implements the think-act-observe cycle:
    1. Build context from user input and history
    2. Call LLM for decision
    3. If tool call requested, execute tool
    4. Add observation to context
    5. Repeat until LLM provides final response

    Based on the Manus CodeAct paradigm.
    """

    def __init__(
        self,
        llm: BaseLLMProvider,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10,
    ):
        """
        Initialize agent executor.

        Args:
            llm: LLM provider instance
            tools: List of available tools (uses registry if not provided)
            system_prompt: System prompt for the agent
            max_iterations: Maximum tool call iterations
        """
        self.llm = llm
        self.max_iterations = max_iterations
        self.system_prompt = system_prompt or self._default_system_prompt()

        # Build tool registry
        self._tools: Dict[str, BaseTool] = {}
        if tools:
            for tool in tools:
                self._tools[tool.name] = tool

    def _default_system_prompt(self) -> str:
        """Default Alfred system prompt."""
        return """You are Alfred, a proactive AI personal assistant. Your role is to help the user manage their tasks, projects, habits, and daily life.

Key traits:
- **Proactive**: Anticipate needs, don't just react
- **Knowledgeable**: Remember user preferences and context
- **Helpful**: Take action to help, not just provide information
- **Concise**: Be efficient with words while being warm and personable

You have access to tools that let you:
- Manage tasks (create, update, complete)
- Track habits and streaks
- Manage projects and updates
- Access user context and preferences
- Schedule reminders and notifications

When the user asks you to do something:
1. Understand their intent
2. Use the appropriate tool(s) to help
3. Confirm what you've done
4. Proactively suggest next steps if relevant

Always be helpful, efficient, and proactive. You are Alfred - the user's trusted digital butler."""

    def _build_messages(
        self,
        user_input: str,
        context: AgentContext,
        steps: List[ExecutionStep],
    ) -> List[LLMMessage]:
        """Build message list for LLM call."""
        messages = [
            LLMMessage(role="system", content=self.system_prompt)
        ]

        # Add conversation history
        for msg in context.conversation_history[-10:]:  # Last 10 messages
            messages.append(LLMMessage(
                role=msg["role"],
                content=msg["content"],
            ))

        # Add current user input
        messages.append(LLMMessage(role="user", content=user_input))

        # Add execution steps as tool calls and results
        for step in steps:
            if step.tool_name and step.tool_result:
                # Add assistant's tool call
                messages.append(LLMMessage(
                    role="assistant",
                    content=f"Using tool: {step.tool_name}",
                ))
                # Add tool result
                messages.append(LLMMessage(
                    role="tool",
                    content=step.tool_result.to_string(),
                    tool_call_id=f"call_{step.step_number}",
                    name=step.tool_name,
                ))

        return messages

    def _get_tool_definitions(self) -> List[ToolDefinition]:
        """Get tool definitions for LLM."""
        definitions = []
        for tool in self._tools.values():
            schema = tool.get_json_schema()
            definitions.append(ToolDefinition(
                name=tool.name,
                description=tool.description,
                parameters=schema,
            ))
        return definitions

    async def _execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: AgentContext,
    ) -> ToolResult:
        """Execute a tool by name."""
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult.fail(f"Unknown tool: {tool_name}")

        # Update tool context
        tool.context = context.to_tool_context()

        # Execute safely
        return await tool.safe_execute(**arguments)

    async def run(
        self,
        user_input: str,
        context: AgentContext,
    ) -> ExecutionResult:
        """
        Run the agent execution loop.

        Args:
            user_input: User's message
            context: Execution context

        Returns:
            ExecutionResult with response and execution details
        """
        steps: List[ExecutionStep] = []
        total_tokens = 0
        max_iterations = min(self.max_iterations, context.max_iterations)

        logger.info(f"Starting agent execution for user {context.user_id}")

        for iteration in range(max_iterations):
            step = ExecutionStep(step_number=iteration + 1)

            try:
                # Build messages
                messages = self._build_messages(user_input, context, steps)

                # Get LLM decision
                tool_definitions = self._get_tool_definitions() if self._tools else None
                response = await self.llm.complete(
                    messages=messages,
                    tools=tool_definitions,
                    temperature=0.7,
                )

                total_tokens += response.usage.total_tokens

                # Check for tool calls
                if response.has_tool_calls:
                    tool_call = response.tool_calls[0]  # Process one at a time
                    step.tool_name = tool_call.name
                    step.tool_args = tool_call.arguments

                    logger.info(f"Executing tool: {tool_call.name}")

                    # Execute tool
                    result = await self._execute_tool(
                        tool_call.name,
                        tool_call.arguments,
                        context,
                    )
                    step.tool_result = result

                    steps.append(step)

                    # Continue loop for next iteration
                    continue

                else:
                    # Final response - no more tool calls
                    step.thought = response.content
                    steps.append(step)

                    logger.info(f"Agent completed in {iteration + 1} iterations")

                    return ExecutionResult(
                        success=True,
                        response=response.content or "I've completed the task.",
                        steps=steps,
                        tool_calls_made=len([s for s in steps if s.tool_name]),
                        total_tokens=total_tokens,
                    )

            except Exception as e:
                logger.error(f"Error in agent execution: {str(e)}")
                return ExecutionResult(
                    success=False,
                    response=f"I encountered an error: {str(e)}",
                    steps=steps,
                    tool_calls_made=len([s for s in steps if s.tool_name]),
                    total_tokens=total_tokens,
                    error=str(e),
                )

        # Reached max iterations
        logger.warning(f"Agent reached max iterations ({max_iterations})")
        return ExecutionResult(
            success=False,
            response="I wasn't able to complete this task within the allowed steps. Please try breaking it into smaller requests.",
            steps=steps,
            tool_calls_made=len([s for s in steps if s.tool_name]),
            total_tokens=total_tokens,
            error="Max iterations reached",
        )

    async def run_streaming(
        self,
        user_input: str,
        context: AgentContext,
    ) -> AsyncIterator[str]:
        """
        Run agent with streaming response.

        Yields tokens as they're generated for the final response.
        Tool execution happens synchronously before streaming starts.
        """
        steps: List[ExecutionStep] = []
        max_iterations = min(self.max_iterations, context.max_iterations)

        for iteration in range(max_iterations):
            step = ExecutionStep(step_number=iteration + 1)

            try:
                messages = self._build_messages(user_input, context, steps)
                tool_definitions = self._get_tool_definitions() if self._tools else None

                # Non-streaming call first to check for tool calls
                response = await self.llm.complete(
                    messages=messages,
                    tools=tool_definitions,
                    temperature=0.7,
                )

                if response.has_tool_calls:
                    tool_call = response.tool_calls[0]
                    step.tool_name = tool_call.name
                    step.tool_args = tool_call.arguments

                    # Yield thinking indicator
                    yield f"[Using {tool_call.name}...]\n"

                    result = await self._execute_tool(
                        tool_call.name,
                        tool_call.arguments,
                        context,
                    )
                    step.tool_result = result
                    steps.append(step)
                    continue

                else:
                    # Stream final response
                    async for token in self.llm.stream(
                        messages=messages,
                        temperature=0.7,
                    ):
                        yield token
                    return

            except Exception as e:
                yield f"\nError: {str(e)}"
                return

        yield "\nI couldn't complete this task within the allowed steps."

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool for use by the agent."""
        self._tools[tool.name] = tool

    def register_tools_from_registry(
        self,
        context: AgentContext,
        registry: Optional[ToolRegistry] = None,
    ) -> None:
        """Register all tools from a registry."""
        if registry is None:
            registry = get_tool_registry()

        tool_context = context.to_tool_context()
        for name in registry.list_tools():
            tool = registry.get(name, context=tool_context)
            if tool:
                self._tools[tool.name] = tool
