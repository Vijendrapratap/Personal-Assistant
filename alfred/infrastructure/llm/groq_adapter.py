"""
Groq LLM Provider.

Supports fast inference with Llama and other models.
"""

import json
from typing import List, Optional, AsyncIterator, Dict, Any

from alfred.infrastructure.llm.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    LLMUsage,
    ToolDefinition,
    ToolCall,
)


class GroqProvider(BaseLLMProvider):
    """
    Groq provider for fast LLM inference.

    Supports:
    - Llama 3.1 70B, 8B
    - Mixtral
    - Gemma
    - Tool calling
    """

    DEFAULT_MODEL = "llama-3.1-70b-versatile"

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize Groq provider.

        Args:
            api_key: Groq API key
            model: Model name
        """
        try:
            from groq import AsyncGroq
        except ImportError:
            raise ImportError(
                "groq package not installed. "
                "Install with: pip install groq"
            )

        self._model = model or self.DEFAULT_MODEL
        self.client = AsyncGroq(api_key=api_key)

    @property
    def model_name(self) -> str:
        return self._model

    def _convert_messages(
        self, messages: List[LLMMessage]
    ) -> List[Dict[str, Any]]:
        """Convert messages to Groq format."""
        groq_messages = []

        for msg in messages:
            if msg.role == "tool":
                groq_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content,
                })
            else:
                groq_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        return groq_messages

    def _convert_tools(
        self, tools: Optional[List[ToolDefinition]]
    ) -> Optional[List[Dict[str, Any]]]:
        """Convert tools to Groq format (OpenAI-compatible)."""
        if not tools:
            return None

        return [tool.to_dict() for tool in tools]

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse Groq response."""
        message = response.choices[0].message
        content = message.content
        tool_calls = None

        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                )
                for tc in message.tool_calls
            ]

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=LLMUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ),
            model=response.model,
            finish_reason=response.choices[0].finish_reason or "",
        )

    async def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Generate completion using Groq."""
        groq_messages = self._convert_messages(messages)
        groq_tools = self._convert_tools(tools)

        kwargs = {
            "model": self._model,
            "messages": groq_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if groq_tools:
            kwargs["tools"] = groq_tools

        if stop:
            kwargs["stop"] = stop

        response = await self.client.chat.completions.create(**kwargs)
        return self._parse_response(response)

    async def stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        groq_messages = self._convert_messages(messages)

        kwargs = {
            "model": self._model,
            "messages": groq_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        stream = await self.client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
