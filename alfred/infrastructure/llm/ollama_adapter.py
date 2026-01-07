"""
Ollama Local LLM Provider.

Supports local Ollama models for offline inference.
"""

import json
from typing import List, Optional, AsyncIterator, Dict, Any

import httpx

from alfred.infrastructure.llm.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    LLMUsage,
    ToolDefinition,
    ToolCall,
)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for local LLM inference.

    Supports:
    - Llama 3, Llama 2
    - Mistral, Mixtral
    - Code Llama
    - And other Ollama-supported models
    """

    DEFAULT_MODEL = "llama3"
    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
        **kwargs: Any,
    ):
        """
        Initialize Ollama provider.

        Args:
            model: Model name (defaults to llama3)
            base_url: Ollama server URL
            timeout: Request timeout in seconds
        """
        self._model = model or self.DEFAULT_MODEL
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def supports_tools(self) -> bool:
        # Ollama has limited tool support
        return False

    def _convert_messages(
        self, messages: List[LLMMessage]
    ) -> List[Dict[str, Any]]:
        """Convert messages to Ollama format."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stop: Optional[List[str]] = None,
    ) -> LLMResponse:
        """Generate completion using Ollama."""
        ollama_messages = self._convert_messages(messages)

        payload = {
            "model": self._model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if stop:
            payload["options"]["stop"] = stop

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                return LLMResponse(
                    content=data["message"]["content"],
                    tool_calls=None,
                    usage=LLMUsage(
                        prompt_tokens=data.get("prompt_eval_count", 0),
                        completion_tokens=data.get("eval_count", 0),
                        total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                    ),
                    model=self._model,
                    finish_reason="stop",
                )
            except httpx.HTTPError as e:
                # Fallback to generate endpoint for older Ollama versions
                return await self._complete_generate(messages, temperature, max_tokens)

    async def _complete_generate(
        self,
        messages: List[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Fallback to /api/generate for older Ollama versions."""
        # Combine messages into a single prompt
        prompt_parts = []
        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"

        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["response"],
                tool_calls=None,
                usage=LLMUsage(
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                    total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                ),
                model=self._model,
                finish_reason="stop",
            )

    async def stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        ollama_messages = self._convert_messages(messages)

        payload = {
            "model": self._model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue


# Legacy adapter for backward compatibility
class OllamaAdapter(OllamaProvider):
    """Legacy adapter name. Use OllamaProvider instead."""

    def __init__(self, model_name: str = "llama3", base_url: str = "http://localhost:11434"):
        super().__init__(model=model_name, base_url=base_url)

    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> str:
        """Legacy interface for simple text generation."""
        import asyncio

        messages = [
            LLMMessage(role=m["role"], content=m["content"])
            for m in history
        ]
        messages.append(LLMMessage(role="user", content=prompt))

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.complete(messages))
        return response.content or ""
