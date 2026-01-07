"""
Google Gemini LLM Provider.

Supports Gemini models with multimodal capabilities.
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


class GoogleProvider(BaseLLMProvider):
    """
    Google Gemini provider.

    Supports:
    - Gemini 1.5 Pro, Gemini 1.5 Flash
    - Multimodal inputs
    - Tool calling (function calling)
    """

    DEFAULT_MODEL = "gemini-1.5-pro"

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize Google provider.

        Args:
            api_key: Google API key
            model: Model name
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        genai.configure(api_key=api_key)
        self._model = model or self.DEFAULT_MODEL
        self.genai = genai

    @property
    def model_name(self) -> str:
        return self._model

    def _convert_messages(
        self, messages: List[LLMMessage]
    ) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Convert messages to Gemini format."""
        system_instruction = None
        gemini_messages = []

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                gemini_messages.append({
                    "role": "user",
                    "parts": [msg.content],
                })
            elif msg.role == "assistant":
                gemini_messages.append({
                    "role": "model",
                    "parts": [msg.content],
                })
            elif msg.role == "tool":
                gemini_messages.append({
                    "role": "function",
                    "parts": [{
                        "function_response": {
                            "name": msg.name,
                            "response": {"result": msg.content},
                        }
                    }],
                })

        return system_instruction, gemini_messages

    def _convert_tools(
        self, tools: Optional[List[ToolDefinition]]
    ) -> Optional[List[Any]]:
        """Convert tools to Gemini format."""
        if not tools:
            return None

        from google.generativeai.types import FunctionDeclaration, Tool

        function_declarations = [
            FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
            )
            for tool in tools
        ]

        return [Tool(function_declarations=function_declarations)]

    async def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Generate completion using Gemini."""
        system_instruction, gemini_messages = self._convert_messages(messages)
        gemini_tools = self._convert_tools(tools)

        model = self.genai.GenerativeModel(
            model_name=self._model,
            system_instruction=system_instruction,
            tools=gemini_tools,
        )

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        if stop:
            generation_config["stop_sequences"] = stop

        response = await model.generate_content_async(
            gemini_messages,
            generation_config=generation_config,
        )

        # Parse response
        content = None
        tool_calls = None

        if response.candidates:
            candidate = response.candidates[0]
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    content = part.text
                elif hasattr(part, "function_call"):
                    if tool_calls is None:
                        tool_calls = []
                    fc = part.function_call
                    tool_calls.append(
                        ToolCall(
                            id=f"call_{len(tool_calls)}",
                            name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                        )
                    )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=LLMUsage(
                prompt_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                completion_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                total_tokens=response.usage_metadata.total_token_count if response.usage_metadata else 0,
            ),
            model=self._model,
            finish_reason=str(candidate.finish_reason) if response.candidates else "",
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        system_instruction, gemini_messages = self._convert_messages(messages)

        model = self.genai.GenerativeModel(
            model_name=self._model,
            system_instruction=system_instruction,
        )

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        response = await model.generate_content_async(
            gemini_messages,
            generation_config=generation_config,
            stream=True,
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text
