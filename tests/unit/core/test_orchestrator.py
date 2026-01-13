"""
Unit tests for Orchestrator and IntentRouter.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from alfred.core.agents.base import (
    AgentType,
    AgentContext,
    AgentResult,
    AgentAction,
    RoutingDecision,
)
from alfred.core.orchestrator import (
    Orchestrator,
    IntentRouter,
    OrchestratorConfig,
    create_orchestrator,
)


class MockLLM:
    """Mock LLM for testing."""

    def __init__(self, default_response: str = "Mock response"):
        self.default_response = default_response
        self.call_count = 0

    def generate_response(self, prompt: str, messages: list) -> str:
        self.call_count += 1
        return self.default_response


class MockStorage:
    """Mock storage for orchestrator testing."""

    def __init__(self):
        self.users = {}
        self.chat_history = []

    def get_user_profile(self, user_id: str):
        return self.users.get(user_id, {"name": "Sir"})

    def get_chat_history(self, user_id: str, limit: int = 10):
        return self.chat_history[-limit:]


class TestIntentRouter:
    """Tests for IntentRouter."""

    @pytest.fixture
    def mock_llm(self):
        return MockLLM()

    @pytest.fixture
    def router(self, mock_llm):
        return IntentRouter(mock_llm)

    @pytest.mark.unit
    def test_router_instantiation(self, router):
        """IntentRouter should instantiate with LLM."""
        assert router is not None
        assert router.llm is not None

    @pytest.mark.unit
    def test_fast_route_create_task(self, router):
        """Fast route should detect task creation."""
        result = router._fast_route("create a task to review code")

        assert result is not None
        assert result.intent == "task"
        assert AgentType.TASK in result.required_agents
        assert result.confidence == 0.85

    @pytest.mark.unit
    def test_fast_route_add_task(self, router):
        """Fast route should detect 'add task' patterns."""
        result = router._fast_route("add task for weekly review")

        assert result is not None
        assert result.intent == "task"
        assert AgentType.TASK in result.required_agents

    @pytest.mark.unit
    def test_fast_route_complete_task(self, router):
        """Fast route should detect task completion."""
        result = router._fast_route("mark the task as complete")

        assert result is not None
        assert result.intent == "task"
        assert AgentType.TASK in result.required_agents

    @pytest.mark.unit
    def test_fast_route_show_tasks(self, router):
        """Fast route should detect task queries."""
        result = router._fast_route("show my tasks for today")

        assert result is not None
        assert result.intent == "task"

    @pytest.mark.unit
    def test_fast_route_planning(self, router):
        """Fast route should detect planning requests."""
        result = router._fast_route("help me plan my week")

        assert result is not None
        assert result.intent == "planning"
        assert AgentType.PLANNING in result.required_agents

    @pytest.mark.unit
    def test_fast_route_break_down(self, router):
        """Fast route should detect breakdown requests."""
        result = router._fast_route("break down this project into steps")

        assert result is not None
        assert result.intent == "planning"

    @pytest.mark.unit
    def test_fast_route_memory(self, router):
        """Fast route should detect memory queries."""
        result = router._fast_route("do you remember my preferences?")

        assert result is not None
        assert result.intent == "memory"
        assert AgentType.MEMORY in result.required_agents

    @pytest.mark.unit
    def test_fast_route_who_is(self, router):
        """Fast route should detect 'who is' queries."""
        result = router._fast_route("who is john")

        assert result is not None
        assert result.intent == "memory"
        assert result.topic == "john"

    @pytest.mark.unit
    def test_fast_route_no_match(self, router):
        """Fast route should return None for no match."""
        result = router._fast_route("what's the weather like?")

        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_llm_route_fallback(self, router, mock_llm):
        """LLM route should be used when fast route fails."""
        mock_llm.default_response = '{"intent": "general", "topic": "weather", "required_agents": ["MEMORY"], "priority": "low"}'

        result = await router._llm_route("what's the weather like?")

        assert result is not None
        assert result.intent == "general"
        assert AgentType.MEMORY in result.required_agents

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_llm_route_always_includes_memory(self, router, mock_llm):
        """LLM route should always include memory agent."""
        mock_llm.default_response = '{"intent": "task", "topic": "coding", "required_agents": ["TASK"], "priority": "high"}'

        result = await router._llm_route("test")

        assert AgentType.MEMORY in result.required_agents

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_llm_route_handles_error(self, router, mock_llm):
        """LLM route should handle invalid JSON gracefully."""
        mock_llm.default_response = "invalid json response"

        result = await router._llm_route("test")

        # Should return fallback routing decision
        assert result is not None
        assert result.confidence == 0.5
        assert AgentType.MEMORY in result.required_agents

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_route_prefers_fast_route(self, router, mock_llm):
        """Route should prefer fast route when available."""
        result = await router.route("create a task to review code")

        # Fast route was used, LLM not called
        assert mock_llm.call_count == 0
        assert result.intent == "task"


class TestOrchestratorConfig:
    """Tests for OrchestratorConfig."""

    @pytest.mark.unit
    def test_default_config(self):
        """Default config should have sensible defaults."""
        config = OrchestratorConfig()

        assert config.max_parallel_agents == 5
        assert config.response_timeout_seconds == 30
        assert config.enable_learning is True

    @pytest.mark.unit
    def test_custom_config(self):
        """Config should accept custom values."""
        config = OrchestratorConfig(
            max_parallel_agents=3,
            response_timeout_seconds=60,
            enable_learning=False,
        )

        assert config.max_parallel_agents == 3
        assert config.response_timeout_seconds == 60
        assert config.enable_learning is False


class TestOrchestrator:
    """Tests for Orchestrator."""

    @pytest.fixture
    def mock_llm(self):
        return MockLLM()

    @pytest.fixture
    def mock_storage(self):
        return MockStorage()

    @pytest.fixture
    def orchestrator(self, mock_llm, mock_storage):
        return Orchestrator(llm=mock_llm, storage=mock_storage)

    @pytest.mark.unit
    def test_orchestrator_instantiation(self, orchestrator):
        """Orchestrator should instantiate with LLM and storage."""
        assert orchestrator is not None
        assert orchestrator.llm is not None
        assert orchestrator.storage is not None
        assert orchestrator.router is not None

    @pytest.mark.unit
    def test_orchestrator_default_config(self, orchestrator):
        """Orchestrator should use default config if none provided."""
        assert orchestrator.config is not None
        assert orchestrator.config.enable_learning is True

    @pytest.mark.unit
    def test_orchestrator_custom_config(self, mock_llm, mock_storage):
        """Orchestrator should accept custom config."""
        config = OrchestratorConfig(enable_learning=False)
        orchestrator = Orchestrator(llm=mock_llm, storage=mock_storage, config=config)

        assert orchestrator.config.enable_learning is False

    @pytest.mark.unit
    def test_agents_initialized(self, orchestrator):
        """Orchestrator should initialize available agents."""
        agents = orchestrator.get_available_agents()

        assert len(agents) > 0
        assert AgentType.TASK in agents
        assert AgentType.MEMORY in agents
        assert AgentType.PLANNING in agents

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_returns_response(self, orchestrator):
        """process should return a response string."""
        response = await orchestrator.process(
            user_input="Hello Alfred",
            user_id="user-123",
        )

        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_handles_exceptions(self, mock_llm, mock_storage):
        """process should handle exceptions gracefully."""
        orchestrator = Orchestrator(llm=mock_llm, storage=mock_storage)

        # Make router raise an exception
        orchestrator.router.route = AsyncMock(side_effect=Exception("Test error"))

        response = await orchestrator.process(
            user_input="trigger error",
            user_id="user-123",
        )

        assert "apologize" in response.lower() or "issue" in response.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_build_context(self, orchestrator):
        """_build_context should create AgentContext with user data."""
        routing = RoutingDecision(
            intent="task",
            topic="coding",
            required_agents=[AgentType.TASK],
        )

        context = await orchestrator._build_context("user-123", "test input", routing)

        assert context is not None
        assert context.user_id == "user-123"
        assert context.user_input == "test input"
        assert context.intent == "task"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_build_context_with_storage(self, orchestrator, mock_storage):
        """_build_context should fetch user profile from storage."""
        mock_storage.users["user-123"] = {"name": "Test User"}

        routing = RoutingDecision(
            intent="task",
            topic="",
            required_agents=[AgentType.TASK],
        )

        context = await orchestrator._build_context("user-123", "test", routing)

        assert context.user_profile["name"] == "Test User"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_synthesize_simple_results(self, orchestrator):
        """_synthesize should combine simple results."""
        results = [
            AgentResult(
                agent_type=AgentType.TASK,
                success=True,
                response_fragments=["Task created successfully"],
                actions=[AgentAction("created_task", "Created task: Review code")],
            )
        ]

        response = await orchestrator._synthesize(
            "create task", "user-123", results, {}
        )

        assert response is not None
        assert "Task created" in response

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_synthesize_empty_results(self, orchestrator):
        """_synthesize should handle empty results."""
        response = await orchestrator._synthesize(
            "hello", "user-123", [], {}
        )

        assert response is not None
        # Should use LLM for simple conversational response

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_simple_response(self, orchestrator, mock_storage):
        """_simple_response should generate conversational response."""
        mock_storage.users["user-123"] = {"name": "John"}

        response = await orchestrator._simple_response(
            "hello there", "user-123", {}
        )

        assert response is not None

    @pytest.mark.unit
    def test_get_available_agents(self, orchestrator):
        """get_available_agents should return list of agent types."""
        agents = orchestrator.get_available_agents()

        assert isinstance(agents, list)
        assert all(isinstance(a, AgentType) for a in agents)


class TestOrchestratorFactory:
    """Tests for create_orchestrator factory function."""

    @pytest.mark.unit
    def test_create_orchestrator_basic(self):
        """create_orchestrator should return Orchestrator instance."""
        llm = MockLLM()
        storage = MockStorage()

        orchestrator = create_orchestrator(llm, storage)

        assert isinstance(orchestrator, Orchestrator)

    @pytest.mark.unit
    def test_create_orchestrator_with_config(self):
        """create_orchestrator should accept config."""
        llm = MockLLM()
        storage = MockStorage()
        config = OrchestratorConfig(enable_learning=False)

        orchestrator = create_orchestrator(llm, storage, config)

        assert orchestrator.config.enable_learning is False


class TestOrchestratorEdgeCases:
    """Edge case tests for Orchestrator."""

    @pytest.mark.unit
    def test_orchestrator_without_storage(self):
        """Orchestrator should work without storage."""
        llm = MockLLM()

        orchestrator = Orchestrator(llm=llm, storage=None)

        assert orchestrator is not None
        agents = orchestrator.get_available_agents()
        assert len(agents) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_without_storage(self):
        """process should work without storage."""
        llm = MockLLM()
        orchestrator = Orchestrator(llm=llm, storage=None)

        response = await orchestrator.process(
            user_input="hello",
            user_id="user-123",
        )

        assert response is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_routing_decision_to_dict(self):
        """RoutingDecision.to_dict should serialize correctly."""
        decision = RoutingDecision(
            intent="task",
            topic="coding",
            required_agents=[AgentType.TASK, AgentType.MEMORY],
            priority="high",
            entities=["project"],
            confidence=0.9,
        )

        d = decision.to_dict()

        assert d["intent"] == "task"
        assert d["topic"] == "coding"
        assert "task" in d["required_agents"]
        assert "memory" in d["required_agents"]
        assert d["priority"] == "high"
        assert d["confidence"] == 0.9
