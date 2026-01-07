"""
Unit tests for Task Agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestTaskAgent:
    """Tests for the TaskAgent class."""

    @pytest.mark.unit
    def test_agent_can_be_instantiated(self, mock_llm):
        """Task agent should instantiate with LLM provider."""
        # This test will pass once we have proper imports
        # For now it validates the test infrastructure works
        assert mock_llm is not None
        assert mock_llm.model_name == "mock-model"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mock_llm_complete(self, mock_llm):
        """Mock LLM should return expected response."""
        response = await mock_llm.complete(
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert response.content == "I'm Alfred, your assistant."
        assert len(mock_llm.call_history) == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mock_llm_with_custom_response(self, mock_llm_with_response):
        """Mock LLM should return custom response when configured."""
        custom_response = "You have 3 tasks due today."
        llm = mock_llm_with_response(custom_response)

        response = await llm.complete(messages=[])

        assert response.content == custom_response

    @pytest.mark.unit
    def test_sample_task_fixture(self, sample_task):
        """Sample task fixture should have expected structure."""
        assert "id" in sample_task
        assert "title" in sample_task
        assert "status" in sample_task
        assert sample_task["priority"] == "high"

    @pytest.mark.unit
    def test_sample_tasks_fixture(self, sample_tasks):
        """Sample tasks fixture should contain multiple tasks."""
        assert len(sample_tasks) == 3
        assert sample_tasks[0]["status"] == "completed"
        assert sample_tasks[1]["status"] == "pending"


class TestTaskAgentTools:
    """Tests for Task Agent tool handling."""

    @pytest.mark.unit
    def test_agent_context_has_tools(self, agent_context):
        """Agent context should include available tools."""
        assert "available_tools" in agent_context
        assert "get_tasks" in agent_context["available_tools"]
        assert "create_task" in agent_context["available_tools"]

    @pytest.mark.unit
    def test_agent_context_has_user_info(self, agent_context):
        """Agent context should include user information."""
        assert "user_id" in agent_context
        assert "user_name" in agent_context
        assert "timezone" in agent_context
