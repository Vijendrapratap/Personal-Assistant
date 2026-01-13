"""
Unit tests for ChatService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class MockStorage:
    """Mock storage for testing."""

    def __init__(self):
        self.chat_history = []
        self.preferences = {}

    def get_chat_history(self, user_id: str, limit: int = 20):
        return self.chat_history[-limit:]

    def save_chat(self, user_id: str, role: str, content: str, metadata: dict = None):
        self.chat_history.append({
            "user_id": user_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_preferences(self, user_id: str):
        return self.preferences.get(user_id, {})

    def get_tasks_due_today(self, user_id: str):
        return []

    def get_habits_due_today(self, user_id: str):
        return []


class MockVectorStore:
    """Mock vector store for testing."""

    def __init__(self):
        self.documents = []

    async def get_relevant_context(self, user_id: str, query: str, max_tokens: int = 2000):
        return "Mock relevant context from previous conversations."

    async def add_knowledge(self, user_id: str, content: str, source: str, doc_type: str, tags: list = None):
        self.documents.append({
            "user_id": user_id,
            "content": content,
            "source": source,
            "doc_type": doc_type,
            "tags": tags or [],
        })
        return True


class TestChatService:
    """Tests for ChatService."""

    @pytest.fixture
    def mock_storage(self):
        return MockStorage()

    @pytest.fixture
    def mock_vector_store(self):
        return MockVectorStore()

    @pytest.fixture
    def chat_service(self, mock_llm, mock_storage, mock_vector_store):
        """Create ChatService instance with mocks."""
        from alfred.core.services.chat_service import ChatService

        service = ChatService(
            storage=mock_storage,
            llm_provider=mock_llm,
            knowledge_graph=None,
            notification_provider=None,
            vector_store=mock_vector_store,
        )
        return service

    @pytest.mark.unit
    def test_chat_service_instantiation(self, chat_service):
        """ChatService should instantiate with required dependencies."""
        assert chat_service is not None
        assert chat_service.storage is not None
        assert chat_service.llm_provider is not None
        assert chat_service.vector_store is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_message_returns_response(self, chat_service):
        """process_message should return a response dict."""
        result = await chat_service.process_message(
            user_id="user-123",
            message="Hello Alfred",
        )

        assert "response" in result
        assert "conversation_id" in result
        assert result["conversation_id"] is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_message_saves_to_history(self, chat_service, mock_storage):
        """process_message should save user and assistant messages to history."""
        await chat_service.process_message(
            user_id="user-123",
            message="What are my tasks?",
        )

        # Should have both user and assistant messages
        assert len(mock_storage.chat_history) >= 2

        user_msg = next(m for m in mock_storage.chat_history if m["role"] == "user")
        assert user_msg["content"] == "What are my tasks?"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_message_uses_conversation_id(self, chat_service):
        """process_message should use provided conversation_id."""
        conv_id = "conv-abc-123"

        result = await chat_service.process_message(
            user_id="user-123",
            message="Hello",
            conversation_id=conv_id,
        )

        assert result["conversation_id"] == conv_id

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_rag_context_with_vector_store(self, chat_service):
        """_get_rag_context should retrieve context from vector store."""
        context = await chat_service._get_rag_context("user-123", "Tell me about my projects")

        assert context is not None
        assert "Mock relevant context" in context

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_rag_context_without_vector_store(self, mock_llm, mock_storage):
        """_get_rag_context should return empty string without vector store."""
        from alfred.core.services.chat_service import ChatService

        service = ChatService(
            storage=mock_storage,
            llm_provider=mock_llm,
            vector_store=None,
        )

        context = await service._get_rag_context("user-123", "Hello")
        assert context == ""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_conversation_history(self, chat_service, mock_storage):
        """get_conversation_history should return chat history."""
        # Add some history
        mock_storage.save_chat("user-123", "user", "Hello")
        mock_storage.save_chat("user-123", "assistant", "Hi there!")

        history = await chat_service.get_conversation_history("user-123")

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_suggested_responses(self, chat_service):
        """get_suggested_responses should return list of suggestions."""
        suggestions = await chat_service.get_suggested_responses("user-123")

        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5


class TestChatServiceEdgeCases:
    """Edge case tests for ChatService."""

    @pytest.fixture
    def chat_service_no_llm(self):
        """Create ChatService without LLM provider."""
        from alfred.core.services.chat_service import ChatService

        return ChatService(
            storage=MockStorage(),
            llm_provider=None,
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_message_without_llm(self, chat_service_no_llm):
        """process_message without LLM should return fallback response."""
        result = await chat_service_no_llm.process_message(
            user_id="user-123",
            message="Hello",
        )

        assert "response" in result
        assert "not configured" in result["response"].lower() or "sorry" in result["response"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_message_with_empty_message(self, mock_llm):
        """process_message with empty message should still work."""
        from alfred.core.services.chat_service import ChatService

        service = ChatService(
            storage=MockStorage(),
            llm_provider=mock_llm,
        )

        result = await service.process_message(
            user_id="user-123",
            message="",
        )

        assert "response" in result
