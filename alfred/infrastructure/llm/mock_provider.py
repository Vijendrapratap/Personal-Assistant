"""
Mock LLM Provider for Testing.

Provides predictable responses for unit and integration tests.
"""

from typing import List, Optional, AsyncIterator, Dict, Any

from alfred.infrastructure.llm.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    LLMUsage,
    ToolDefinition,
    ToolCall,
)


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM provider for testing.

    Provides configurable responses without making API calls.
    """

    def __init__(
        self,
        default_response: str = "I'm Alfred, your AI assistant. How can I help you today?",
        responses: Optional[List[str]] = None,
        tool_calls: Optional[List[ToolCall]] = None,
        **kwargs: Any,
    ):
        """
        Initialize mock provider.

        Args:
            default_response: Response to return by default
            responses: List of responses to return in sequence
            tool_calls: Optional tool calls to include in response
        """
        self.default_response = default_response
        self.responses = responses or []
        self.configured_tool_calls = tool_calls
        self.call_count = 0
        self.call_history: List[Dict[str, Any]] = []

    @property
    def model_name(self) -> str:
        return "mock-model"

    @property
    def supports_tools(self) -> bool:
        return True

    @property
    def supports_streaming(self) -> bool:
        return True

    async def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Return mock completion."""
        # Track call
        self.call_history.append({
            "messages": [m.to_dict() for m in messages],
            "tools": [t.to_dict() for t in tools] if tools else None,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })

        # Determine response
        if self.responses and self.call_count < len(self.responses):
            content = self.responses[self.call_count]
        else:
            content = self.default_response

        self.call_count += 1

        return LLMResponse(
            content=content if not self.configured_tool_calls else None,
            tool_calls=self.configured_tool_calls,
            usage=LLMUsage(
                prompt_tokens=len(str(messages)) // 4,
                completion_tokens=len(content) // 4,
                total_tokens=len(str(messages)) // 4 + len(content) // 4,
            ),
            model="mock-model",
            finish_reason="stop",
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream mock tokens."""
        response = await self.complete(messages, tools, temperature, max_tokens)
        if response.content:
            # Simulate streaming by yielding word by word
            words = response.content.split()
            for i, word in enumerate(words):
                if i < len(words) - 1:
                    yield word + " "
                else:
                    yield word

    def reset(self) -> None:
        """Reset call tracking."""
        self.call_count = 0
        self.call_history.clear()

    def set_response(self, response: str) -> None:
        """Set the next response."""
        self.responses = [response]
        self.call_count = 0

    def set_responses(self, responses: List[str]) -> None:
        """Set a sequence of responses."""
        self.responses = responses
        self.call_count = 0

    def set_tool_calls(self, tool_calls: List[ToolCall]) -> None:
        """Configure tool calls to return."""
        self.configured_tool_calls = tool_calls

    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """Get the last call made."""
        if self.call_history:
            return self.call_history[-1]
        return None
