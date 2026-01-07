"""
Base LLM Provider Interface.

Defines the abstract interface that all LLM providers must implement.
Supports both simple text generation and tool calling.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, AsyncIterator, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum


class MessageRole(str, Enum):
    """Valid message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class LLMMessage:
    """A message in a conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None  # Tool name for tool messages

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        d = {"role": self.role, "content": self.content}
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        return d


@dataclass
class ToolDefinition:
    """Definition of a tool that can be called by the LLM."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


@dataclass
class ToolCall:
    """A tool call made by the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }


@dataclass
class LLMUsage:
    """Token usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    """Response from an LLM completion."""
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    usage: LLMUsage = field(default_factory=LLMUsage)
    model: str = ""
    finish_reason: str = ""

    @property
    def has_tool_calls(self) -> bool:
        """Check if response includes tool calls."""
        return self.tool_calls is not None and len(self.tool_calls) > 0


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Implementations must provide:
    - model_name: The model identifier
    - complete(): Generate completion from messages
    - stream(): Stream completion tokens (optional)
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier."""
        pass

    @property
    def supports_tools(self) -> bool:
        """Whether this provider supports tool/function calling."""
        return True

    @property
    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming."""
        return True

    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        """
        Generate a completion from messages.

        Args:
            messages: List of conversation messages
            tools: Optional list of tools the model can call
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stop: Optional stop sequences

        Returns:
            LLMResponse with content and/or tool_calls
        """
        pass

    async def stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens.

        Default implementation falls back to non-streaming.
        Override for true streaming support.
        """
        response = await self.complete(
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response.content:
            yield response.content

    # Backward compatibility with old interface
    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> str:
        """
        Legacy interface for simple text generation.
        Deprecated: Use complete() instead.
        """
        import asyncio

        messages = [
            LLMMessage(role=m["role"], content=m["content"])
            for m in history
        ]
        messages.append(LLMMessage(role="user", content=prompt))

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.complete(messages))
        return response.content or ""
