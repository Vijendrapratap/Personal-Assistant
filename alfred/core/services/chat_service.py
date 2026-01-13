"""
Chat Service.

Handles chat/conversation logic and integrates with the agent system.
"""

from typing import Optional, Dict, Any, List, AsyncIterator
from datetime import datetime
import uuid

from alfred.core.services.base import BaseService
from alfred.core.agents.executor import AgentExecutor, AgentContext, ExecutionResult
from alfred.core.agents.context import ContextBuilder
from alfred.infrastructure.llm.base import BaseLLMProvider
from alfred.core.tools.registry import get_tool_registry


class ChatService(BaseService):
    """
    Chat and conversation service.

    Handles:
    - Message processing through agent system
    - Conversation history management
    - Streaming responses
    - RAG context retrieval from vector store
    """

    def __init__(
        self,
        storage: Any = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        knowledge_graph: Any = None,
        notification_provider: Any = None,
        vector_store: Any = None,
        **kwargs,
    ):
        super().__init__(
            storage=storage,
            knowledge_graph=knowledge_graph,
            notification_provider=notification_provider,
            **kwargs,
        )
        self.llm_provider = llm_provider
        self.vector_store = vector_store
        self._agent_executor: Optional[AgentExecutor] = None

    def _get_executor(self) -> AgentExecutor:
        """Get or create agent executor."""
        if self._agent_executor is None and self.llm_provider:
            self._agent_executor = AgentExecutor(
                llm=self.llm_provider,
                max_iterations=10,
            )
        return self._agent_executor

    async def _get_rag_context(self, user_id: str, message: str) -> str:
        """
        Get relevant context from vector store using RAG.

        Args:
            user_id: User ID
            message: User's message to find relevant context for

        Returns:
            Formatted context string for injection into conversation
        """
        if not self.vector_store:
            return ""

        try:
            context = await self.vector_store.get_relevant_context(
                user_id=user_id,
                query=message,
                max_tokens=2000,
            )
            return context
        except Exception as e:
            print(f"Error getting RAG context: {e}")
            return ""

    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a response.

        Args:
            user_id: User ID
            message: User's message
            conversation_id: Optional conversation ID for context

        Returns:
            Response dict with message and metadata
        """
        self._ensure_storage()

        # Get or create conversation
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # Get conversation history
        history = self.storage.get_chat_history(user_id, limit=20)

        # Get RAG context from vector store
        rag_context = await self._get_rag_context(user_id, message)

        # Save user message
        self.storage.save_chat(
            user_id=user_id,
            role="user",
            content=message,
            metadata={"conversation_id": conversation_id},
        )

        # Build agent context with RAG context
        context = AgentContext(
            user_id=user_id,
            storage=self.storage,
            knowledge_graph=self.knowledge_graph,
            notification_provider=self.notification_provider,
            conversation_id=conversation_id,
            conversation_history=history,
            rag_context=rag_context,  # Include RAG context
        )

        # Get executor and register tools
        executor = self._get_executor()
        if executor:
            executor.register_tools_from_registry(context)

            # Run agent
            result = await executor.run(message, context)

            # Save assistant response
            self.storage.save_chat(
                user_id=user_id,
                role="assistant",
                content=result.response,
                metadata={
                    "conversation_id": conversation_id,
                    "tool_calls": result.tool_calls_made,
                    "tokens": result.total_tokens,
                },
            )

            self._log_action(
                "CHAT",
                user_id,
                f"tools={result.tool_calls_made} tokens={result.total_tokens}"
            )

            return {
                "response": result.response,
                "conversation_id": conversation_id,
                "tool_calls_made": result.tool_calls_made,
                "steps": [s.to_dict() for s in result.steps],
            }
        else:
            # No LLM provider - return simple response
            response = "I'm sorry, the AI service is not configured. Please check your settings."
            self.storage.save_chat(
                user_id=user_id,
                role="assistant",
                content=response,
            )
            return {
                "response": response,
                "conversation_id": conversation_id,
                "tool_calls_made": 0,
                "steps": [],
            }

    async def process_message_streaming(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Process a message with streaming response.

        Yields response tokens as they're generated.
        """
        self._ensure_storage()

        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        history = self.storage.get_chat_history(user_id, limit=20)

        # Save user message
        self.storage.save_chat(
            user_id=user_id,
            role="user",
            content=message,
            metadata={"conversation_id": conversation_id},
        )

        # Build context
        context = AgentContext(
            user_id=user_id,
            storage=self.storage,
            knowledge_graph=self.knowledge_graph,
            notification_provider=self.notification_provider,
            conversation_id=conversation_id,
            conversation_history=history,
        )

        executor = self._get_executor()
        if executor:
            executor.register_tools_from_registry(context)

            full_response = []
            async for token in executor.run_streaming(message, context):
                full_response.append(token)
                yield token

            # Save complete response
            self.storage.save_chat(
                user_id=user_id,
                role="assistant",
                content="".join(full_response),
                metadata={"conversation_id": conversation_id, "streamed": True},
            )
        else:
            yield "I'm sorry, the AI service is not configured."

    async def get_conversation_history(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get conversation history."""
        self._ensure_storage()
        return self.storage.get_chat_history(user_id, limit=limit)

    async def clear_conversation(
        self,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        """Clear a conversation's history."""
        # This would need storage method implementation
        self._log_action("CLEAR_CONVERSATION", user_id, f"conv={conversation_id}")
        return True

    async def get_suggested_responses(
        self,
        user_id: str,
        context: Optional[str] = None,
    ) -> List[str]:
        """
        Get suggested quick responses based on context.

        Returns common actions the user might want to take.
        """
        self._ensure_storage()

        suggestions = []

        # Check for pending tasks
        tasks_today = self.storage.get_tasks_due_today(user_id)
        if tasks_today:
            suggestions.append("What tasks do I have today?")

        # Check for incomplete habits
        habits_today = self.storage.get_habits_due_today(user_id)
        incomplete_habits = [h for h in habits_today if not h.get("completed_today")]
        if incomplete_habits:
            suggestions.append(f"Log my {incomplete_habits[0]['name']} habit")

        # Standard suggestions
        suggestions.extend([
            "Create a new task",
            "Show my projects",
            "What should I focus on?",
        ])

        return suggestions[:5]
