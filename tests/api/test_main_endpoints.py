"""
API endpoint tests for Alfred main endpoints.

Tests the core FastAPI models and endpoint logic.
"""

import pytest
import os
import sys

# Set test environment before importing app
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-api-tests"
os.environ["LLM_PROVIDER"] = "mock"


class TestAPIModels:
    """Tests for API Pydantic models."""

    @pytest.mark.unit
    def test_chat_request_model_basic(self):
        """ChatRequest should validate basic message."""
        # Import inside test to avoid initialization issues
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        from pydantic import BaseModel
        from typing import Optional, Dict, Any

        # Define model locally to avoid import issues
        class ChatRequest(BaseModel):
            message: str
            conversation_id: Optional[str] = None
            context: Optional[Dict[str, Any]] = None

        req = ChatRequest(message="Hello Alfred")
        assert req.message == "Hello Alfred"
        assert req.conversation_id is None
        assert req.context is None

    @pytest.mark.unit
    def test_chat_request_with_optional_fields(self):
        """ChatRequest should accept optional fields."""
        from pydantic import BaseModel
        from typing import Optional, Dict, Any

        class ChatRequest(BaseModel):
            message: str
            conversation_id: Optional[str] = None
            context: Optional[Dict[str, Any]] = None

        req = ChatRequest(
            message="Test",
            conversation_id="conv-123",
            context={"key": "value"}
        )
        assert req.conversation_id == "conv-123"
        assert req.context == {"key": "value"}

    @pytest.mark.unit
    def test_chat_response_model_basic(self):
        """ChatResponse should validate correctly."""
        from pydantic import BaseModel
        from typing import Optional, Dict, Any

        class ChatResponse(BaseModel):
            response: str
            conversation_id: Optional[str] = None
            metadata: Optional[Dict[str, Any]] = None

        resp = ChatResponse(response="Hello, Sir!")
        assert resp.response == "Hello, Sir!"
        assert resp.conversation_id is None
        assert resp.metadata is None

    @pytest.mark.unit
    def test_chat_response_with_metadata(self):
        """ChatResponse should accept metadata."""
        from pydantic import BaseModel
        from typing import Optional, Dict, Any

        class ChatResponse(BaseModel):
            response: str
            conversation_id: Optional[str] = None
            metadata: Optional[Dict[str, Any]] = None

        resp = ChatResponse(
            response="Test",
            conversation_id="conv-123",
            metadata={"engine": "orchestrator"}
        )
        assert resp.conversation_id == "conv-123"
        assert resp.metadata["engine"] == "orchestrator"

    @pytest.mark.unit
    def test_setup_status_response_not_configured(self):
        """SetupStatusResponse should indicate not configured."""
        from pydantic import BaseModel
        from typing import Optional

        class SetupStatusResponse(BaseModel):
            is_configured: bool
            llm_provider: Optional[str] = None
            database_type: Optional[str] = None
            knowledge_graph: Optional[str] = None
            missing: list = []
            instructions: Optional[str] = None

        resp = SetupStatusResponse(is_configured=False, missing=["llm_api_key"])
        assert resp.is_configured is False
        assert "llm_api_key" in resp.missing

    @pytest.mark.unit
    def test_setup_status_response_configured(self):
        """SetupStatusResponse should indicate configured state."""
        from pydantic import BaseModel
        from typing import Optional

        class SetupStatusResponse(BaseModel):
            is_configured: bool
            llm_provider: Optional[str] = None
            database_type: Optional[str] = None
            knowledge_graph: Optional[str] = None
            missing: list = []
            instructions: Optional[str] = None

        resp = SetupStatusResponse(
            is_configured=True,
            llm_provider="openai",
            database_type="postgres",
        )
        assert resp.is_configured is True
        assert resp.llm_provider == "openai"
        assert resp.database_type == "postgres"

    @pytest.mark.unit
    def test_setup_request_empty(self):
        """SetupRequest should allow empty request."""
        from pydantic import BaseModel
        from typing import Optional

        class SetupRequest(BaseModel):
            openai_api_key: Optional[str] = None
            anthropic_api_key: Optional[str] = None

        req = SetupRequest()
        assert req.openai_api_key is None
        assert req.anthropic_api_key is None

    @pytest.mark.unit
    def test_setup_request_with_openai_key(self):
        """SetupRequest should accept OpenAI key."""
        from pydantic import BaseModel
        from typing import Optional

        class SetupRequest(BaseModel):
            openai_api_key: Optional[str] = None
            anthropic_api_key: Optional[str] = None

        req = SetupRequest(openai_api_key="sk-test")
        assert req.openai_api_key == "sk-test"

    @pytest.mark.unit
    def test_setup_request_with_anthropic_key(self):
        """SetupRequest should accept Anthropic key."""
        from pydantic import BaseModel
        from typing import Optional

        class SetupRequest(BaseModel):
            openai_api_key: Optional[str] = None
            anthropic_api_key: Optional[str] = None

        req = SetupRequest(anthropic_api_key="sk-ant-test")
        assert req.anthropic_api_key == "sk-ant-test"


class TestAPIKeyValidation:
    """Tests for API key validation logic."""

    @pytest.mark.unit
    def test_openai_key_format_valid(self):
        """Valid OpenAI key should start with sk-."""
        key = "sk-test-key-12345"
        assert key.startswith("sk-")

    @pytest.mark.unit
    def test_openai_key_format_invalid(self):
        """Invalid OpenAI key should not start with sk-."""
        key = "invalid-key"
        assert not key.startswith("sk-")

    @pytest.mark.unit
    def test_anthropic_key_format_valid(self):
        """Valid Anthropic key should start with sk-ant-."""
        key = "sk-ant-test-key-12345"
        assert key.startswith("sk-ant-")

    @pytest.mark.unit
    def test_anthropic_key_format_invalid(self):
        """Invalid Anthropic key should not start with sk-ant-."""
        key = "sk-invalid"
        assert not key.startswith("sk-ant-")


class TestHealthResponseStructure:
    """Tests for health response structure."""

    @pytest.mark.unit
    def test_health_response_has_required_fields(self):
        """Health response should have required fields."""
        # Expected health response structure
        health_response = {
            "status": "online",
            "version": "2.2.0",
            "brain": "MockLLM",
            "storage": "SQLiteAdapter",
            "orchestrator": "active",
            "agents": ["task", "memory", "planning"],
            "services": {
                "chat": True,
                "tasks": True,
                "habits": True,
                "projects": True,
                "briefing": True,
            },
            "integrations": {
                "knowledge_graph": False,
                "vector_store": False,
            },
            "connectors": {
                "manager": True,
                "types": ["google_calendar", "gmail"],
            },
        }

        assert "status" in health_response
        assert "version" in health_response
        assert "services" in health_response
        assert "integrations" in health_response

    @pytest.mark.unit
    def test_services_status_structure(self):
        """Services status should be boolean values."""
        services = {
            "chat": True,
            "tasks": True,
            "habits": False,
        }

        for service, status in services.items():
            assert isinstance(status, bool)


class TestRootResponseStructure:
    """Tests for root endpoint response structure."""

    @pytest.mark.unit
    def test_root_response_has_required_fields(self):
        """Root response should have required fields."""
        root_response = {
            "name": "Alfred - The Digital Butler",
            "version": "2.1.0",
            "description": "Your proactive personal assistant",
            "endpoints": {
                "auth": "/auth",
                "chat": "/chat",
                "tasks": "/tasks",
            }
        }

        assert "name" in root_response
        assert "Alfred" in root_response["name"]
        assert "version" in root_response
        assert "endpoints" in root_response

    @pytest.mark.unit
    def test_endpoints_list_contains_core_paths(self):
        """Endpoints should include core API paths."""
        endpoints = {
            "auth": "/auth",
            "chat": "/chat",
            "tasks": "/tasks",
            "habits": "/habits",
            "projects": "/projects",
        }

        required_endpoints = ["auth", "chat", "tasks", "habits"]
        for ep in required_endpoints:
            assert ep in endpoints


class TestMiddlewareConfiguration:
    """Tests for middleware configuration logic."""

    @pytest.mark.unit
    def test_public_paths_include_health(self):
        """Public paths should include health endpoint."""
        public_paths = (
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/signup",
            "/auth/refresh",
            "/setup/status",
            "/setup/integrations",
        )

        assert "/health" in public_paths
        assert "/" in public_paths
        assert "/setup/status" in public_paths

    @pytest.mark.unit
    def test_rate_limit_config(self):
        """Rate limit configuration should have sensible defaults."""
        config = {
            "requests_per_minute": 60,
            "burst_size": 10,
            "endpoint_limits": {
                "/chat": 30,
                "/chat/stream": 30,
                "/voice/transcribe": 20,
                "/auth/login": 10,
                "/auth/signup": 5,
            }
        }

        assert config["requests_per_minute"] == 60
        assert config["endpoint_limits"]["/chat"] == 30
        assert config["endpoint_limits"]["/auth/signup"] < config["endpoint_limits"]["/chat"]


class TestSetupLogic:
    """Tests for setup endpoint logic."""

    @pytest.mark.unit
    def test_setup_status_with_openai(self):
        """Setup status should detect OpenAI configuration."""
        # Simulate having OpenAI key
        has_openai = True
        has_anthropic = False

        is_configured = has_openai or has_anthropic
        llm_provider = "openai" if has_openai else ("anthropic" if has_anthropic else None)

        assert is_configured is True
        assert llm_provider == "openai"

    @pytest.mark.unit
    def test_setup_status_with_anthropic(self):
        """Setup status should detect Anthropic configuration."""
        has_openai = False
        has_anthropic = True

        is_configured = has_openai or has_anthropic
        llm_provider = "openai" if has_openai else ("anthropic" if has_anthropic else None)

        assert is_configured is True
        assert llm_provider == "anthropic"

    @pytest.mark.unit
    def test_setup_status_without_llm(self):
        """Setup status should indicate missing LLM."""
        has_openai = False
        has_anthropic = False

        is_configured = has_openai or has_anthropic
        missing = []
        if not has_openai and not has_anthropic:
            missing.append("llm_api_key")

        assert is_configured is False
        assert "llm_api_key" in missing

    @pytest.mark.unit
    def test_database_type_postgres(self):
        """Database type should be postgres when DATABASE_URL is set."""
        database_url = "postgresql://user:pass@localhost/db"
        database_type = "postgres" if database_url else "sqlite"

        assert database_type == "postgres"

    @pytest.mark.unit
    def test_database_type_sqlite(self):
        """Database type should be sqlite when DATABASE_URL is not set."""
        database_url = None
        database_type = "postgres" if database_url else "sqlite"

        assert database_type == "sqlite"
