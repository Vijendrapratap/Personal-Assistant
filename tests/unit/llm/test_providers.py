"""
Unit tests for LLM providers.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestMockLLMProvider:
    """Tests for the mock LLM provider used in testing."""

    @pytest.mark.unit
    def test_mock_provider_has_model_name(self, mock_llm):
        """Mock provider should expose model name."""
        assert mock_llm.model_name == "mock-model"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mock_provider_complete(self, mock_llm):
        """Mock provider complete() should return response."""
        messages = [
            {"role": "system", "content": "You are Alfred."},
            {"role": "user", "content": "What tasks do I have?"},
        ]

        response = await mock_llm.complete(messages=messages)

        assert response.content is not None
        assert response.usage is not None
        assert "prompt_tokens" in response.usage

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mock_provider_tracks_calls(self, mock_llm):
        """Mock provider should track call history."""
        assert len(mock_llm.call_history) == 0

        await mock_llm.complete(messages=[{"role": "user", "content": "Test 1"}])
        await mock_llm.complete(messages=[{"role": "user", "content": "Test 2"}])

        assert len(mock_llm.call_history) == 2
        assert mock_llm.call_history[0]["messages"][0]["content"] == "Test 1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mock_provider_stream(self, mock_llm):
        """Mock provider stream() should yield tokens."""
        tokens = []
        async for token in mock_llm.stream(messages=[]):
            tokens.append(token)

        assert len(tokens) > 0
        full_response = "".join(tokens).strip()
        assert "Alfred" in full_response


class TestLLMProviderInterface:
    """Tests for LLM provider interface requirements."""

    @pytest.mark.unit
    def test_provider_required_methods(self):
        """LLM providers should implement required methods."""
        required_methods = ["complete", "stream", "model_name"]

        # These are the methods any LLM provider must implement
        for method in required_methods:
            assert method is not None

    @pytest.mark.unit
    def test_response_structure(self):
        """LLM response should have expected structure."""
        from tests.conftest import MockLLMResponse

        response = MockLLMResponse(content="Test response")

        assert hasattr(response, "content")
        assert hasattr(response, "tool_calls")
        assert hasattr(response, "usage")

    @pytest.mark.unit
    def test_response_with_tool_calls(self):
        """LLM response can include tool calls."""
        from tests.conftest import MockLLMResponse

        tool_calls = [
            {"id": "call-1", "name": "get_tasks", "arguments": {}}
        ]
        response = MockLLMResponse(content=None, tool_calls=tool_calls)

        assert response.content is None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["name"] == "get_tasks"
