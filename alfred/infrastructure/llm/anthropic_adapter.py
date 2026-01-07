"""
Anthropic Claude LLM Provider.

Supports Claude models with tool calling capabilities.
"""

import json
import logging
from typing import List, Optional, AsyncIterator, Dict, Any

from alfred.infrastructure.llm.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    LLMUsage,
    ToolDefinition,
    ToolCall,
)


logger = logging.getLogger("alfred.llm.anthropic")


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude provider.

    Supports:
    - Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
    - Tool calling (function calling)
    - Streaming
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        max_retries: int = 3,
        **kwargs: Any,
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model name (defaults to Claude 3.5 Sonnet)
            max_retries: Number of retries for failed requests
        """
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        self._model = model or self.DEFAULT_MODEL
        self.client = AsyncAnthropic(
            api_key=api_key,
            max_retries=max_retries,
        )

    @property
    def model_name(self) -> str:
        return self._model

    def _convert_messages(
        self, messages: List[LLMMessage]
    ) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Convert messages to Anthropic format, extracting system message."""
        system_message = None
        anthropic_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            elif msg.role == "tool":
                # Tool results in Anthropic format
                anthropic_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content,
                        }
                    ],
                })
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        return system_message, anthropic_messages

    def _convert_tools(
        self, tools: Optional[List[ToolDefinition]]
    ) -> Optional[List[Dict[str, Any]]]:
        """Convert tools to Anthropic format."""
        if not tools:
            return None

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in tools
        ]

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse Anthropic response to our format."""
        content = None
        tool_calls = None

        # Extract content blocks
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input,
                    )
                )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=LLMUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            ),
            model=response.model,
            finish_reason=response.stop_reason or "",
        )

    async def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Generate completion using Claude."""
        system, anthropic_messages = self._convert_messages(messages)
        anthropic_tools = self._convert_tools(tools)

        kwargs = {
            "model": self._model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            kwargs["system"] = system

        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        if stop:
            kwargs["stop_sequences"] = stop

        response = await self.client.messages.create(**kwargs)
        return self._parse_response(response)

    async def stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        system, anthropic_messages = self._convert_messages(messages)
        anthropic_tools = self._convert_tools(tools)

        kwargs = {
            "model": self._model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            kwargs["system"] = system

        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def stream_with_tools(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream completion with tool call support.

        Yields events for both text and tool calls:
        - {"type": "text", "content": "..."}
        - {"type": "tool_use", "id": "...", "name": "...", "input": {...}}
        - {"type": "done", "response": LLMResponse}
        """
        system, anthropic_messages = self._convert_messages(messages)
        anthropic_tools = self._convert_tools(tools)

        kwargs = {
            "model": self._model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            kwargs["system"] = system

        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        try:
            async with self.client.messages.stream(**kwargs) as stream:
                current_tool = None
                current_tool_input = ""

                async for event in stream:
                    if hasattr(event, 'type'):
                        if event.type == 'content_block_start':
                            block = event.content_block
                            if hasattr(block, 'type'):
                                if block.type == 'tool_use':
                                    current_tool = {
                                        "id": block.id,
                                        "name": block.name,
                                    }
                                    current_tool_input = ""

                        elif event.type == 'content_block_delta':
                            delta = event.delta
                            if hasattr(delta, 'type'):
                                if delta.type == 'text_delta':
                                    yield {"type": "text", "content": delta.text}
                                elif delta.type == 'input_json_delta':
                                    current_tool_input += delta.partial_json

                        elif event.type == 'content_block_stop':
                            if current_tool:
                                try:
                                    tool_input = json.loads(current_tool_input) if current_tool_input else {}
                                except json.JSONDecodeError:
                                    tool_input = {}

                                yield {
                                    "type": "tool_use",
                                    "id": current_tool["id"],
                                    "name": current_tool["name"],
                                    "input": tool_input,
                                }
                                current_tool = None
                                current_tool_input = ""

                # Get final message for usage info
                final_message = await stream.get_final_message()
                yield {
                    "type": "done",
                    "response": self._parse_response(final_message),
                }

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {"type": "error", "error": str(e)}

    async def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Note: This is an approximation. For exact counts, use the API.
        """
        # Rough approximation: ~4 chars per token for English
        return len(text) // 4

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        model_info = {
            "claude-sonnet-4-20250514": {
                "name": "Claude Sonnet 4",
                "context_window": 200000,
                "max_output": 8192,
                "supports_vision": True,
                "supports_tools": True,
            },
            "claude-3-5-sonnet-20241022": {
                "name": "Claude 3.5 Sonnet",
                "context_window": 200000,
                "max_output": 8192,
                "supports_vision": True,
                "supports_tools": True,
            },
            "claude-3-opus-20240229": {
                "name": "Claude 3 Opus",
                "context_window": 200000,
                "max_output": 4096,
                "supports_vision": True,
                "supports_tools": True,
            },
            "claude-3-haiku-20240307": {
                "name": "Claude 3 Haiku",
                "context_window": 200000,
                "max_output": 4096,
                "supports_vision": True,
                "supports_tools": True,
            },
        }

        return model_info.get(self._model, {
            "name": self._model,
            "context_window": 200000,
            "max_output": 4096,
            "supports_vision": True,
            "supports_tools": True,
        })
