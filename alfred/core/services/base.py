"""
Base Service Class.

All services inherit from this base class which provides
common functionality and dependency injection.
"""

from typing import Optional, Any
from abc import ABC
import logging


class BaseService(ABC):
    """
    Abstract base class for all services.

    Provides:
    - Storage access
    - Logging
    - Common error handling patterns
    """

    def __init__(
        self,
        storage: Any = None,
        knowledge_graph: Any = None,
        notification_provider: Any = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize service with dependencies.

        Args:
            storage: MemoryStorage instance for data access
            knowledge_graph: KnowledgeGraphProvider for entity queries
            notification_provider: For sending push notifications
            logger: Optional custom logger
        """
        self.storage = storage
        self.knowledge_graph = knowledge_graph
        self.notification_provider = notification_provider
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def _ensure_storage(self) -> None:
        """Raise error if storage not configured."""
        if not self.storage:
            raise RuntimeError("Storage not configured for this service")

    def _log_action(self, action: str, user_id: str, details: str = "") -> None:
        """Log a service action."""
        msg = f"[{action}] user={user_id}"
        if details:
            msg += f" {details}"
        self.logger.info(msg)
