"""
Pytest fixtures for Alfred tests.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Generator, AsyncGenerator

# Set test environment
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("LLM_PROVIDER", "mock")


# ============================================
# Mock LLM Provider
# ============================================

class MockLLMResponse:
    """Mock LLM response for testing."""

    def __init__(self, content: str = "Mock response", tool_calls: list = None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.usage = {"prompt_tokens": 10, "completion_tokens": 20}


class MockLLMProvider:
    """Mock LLM provider for testing without API calls."""

    def __init__(self, default_response: str = "I'm Alfred, your assistant."):
        self.default_response = default_response
        self.call_history = []

    @property
    def model_name(self) -> str:
        return "mock-model"

    async def complete(
        self,
        messages: list,
        tools: list = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> MockLLMResponse:
        self.call_history.append({
            "messages": messages,
            "tools": tools,
            "temperature": temperature,
        })
        return MockLLMResponse(content=self.default_response)

    async def stream(self, messages: list, tools: list = None):
        for word in self.default_response.split():
            yield word + " "


@pytest.fixture
def mock_llm() -> MockLLMProvider:
    """Provide a mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def mock_llm_with_response():
    """Factory fixture to create mock LLM with custom response."""
    def _create(response: str):
        return MockLLMProvider(default_response=response)
    return _create


# ============================================
# Database Fixtures
# ============================================

@pytest.fixture
def mock_db():
    """Provide a mock database connection."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    return db


# ============================================
# User Fixtures
# ============================================

@pytest.fixture
def sample_user() -> dict:
    """Provide sample user data."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "name": "Test User",
        "preferences": {
            "morning_briefing_time": "08:00",
            "evening_review_time": "20:00",
            "timezone": "America/New_York",
        }
    }


@pytest.fixture
def sample_user_context(sample_user) -> dict:
    """Provide sample user context for agent."""
    return {
        "user_id": sample_user["id"],
        "user_name": sample_user["name"],
        "timezone": sample_user["preferences"]["timezone"],
        "conversation_history": [],
    }


# ============================================
# Task Fixtures
# ============================================

@pytest.fixture
def sample_task() -> dict:
    """Provide sample task data."""
    return {
        "id": "task-123",
        "user_id": "user-123",
        "title": "Complete project proposal",
        "description": "Write the Q1 project proposal document",
        "status": "pending",
        "priority": "high",
        "due_date": "2026-01-10",
        "project_id": "project-456",
        "tags": ["work", "important"],
    }


@pytest.fixture
def sample_tasks() -> list:
    """Provide list of sample tasks."""
    return [
        {
            "id": "task-1",
            "title": "Morning standup",
            "status": "completed",
            "priority": "medium",
        },
        {
            "id": "task-2",
            "title": "Review PR #123",
            "status": "pending",
            "priority": "high",
        },
        {
            "id": "task-3",
            "title": "Update documentation",
            "status": "pending",
            "priority": "low",
        },
    ]


# ============================================
# Project Fixtures
# ============================================

@pytest.fixture
def sample_project() -> dict:
    """Provide sample project data."""
    return {
        "id": "project-456",
        "user_id": "user-123",
        "name": "Alfred Development",
        "description": "Building the proactive AI assistant",
        "status": "active",
        "color": "#4f46e5",
        "tasks_count": 15,
        "completed_tasks_count": 8,
    }


# ============================================
# Habit Fixtures
# ============================================

@pytest.fixture
def sample_habit() -> dict:
    """Provide sample habit data."""
    return {
        "id": "habit-789",
        "user_id": "user-123",
        "name": "Morning meditation",
        "frequency": "daily",
        "current_streak": 7,
        "longest_streak": 14,
        "completed_today": False,
    }


# ============================================
# Agent Fixtures
# ============================================

@pytest.fixture
def agent_context(sample_user_context) -> dict:
    """Provide agent execution context."""
    return {
        **sample_user_context,
        "available_tools": ["get_tasks", "create_task", "complete_task"],
        "max_iterations": 5,
    }


# ============================================
# API Testing Fixtures
# ============================================

@pytest.fixture
def auth_headers() -> dict:
    """Provide authentication headers for API tests."""
    return {
        "Authorization": "Bearer test-jwt-token",
        "Content-Type": "application/json",
    }


# ============================================
# Async Helpers
# ============================================

@pytest.fixture
def async_mock():
    """Factory to create async mock functions."""
    def _create(return_value=None):
        mock = AsyncMock()
        mock.return_value = return_value
        return mock
    return _create
