"""
Base Connector Classes.

Defines the interface for all external service connectors.
Follows Model Context Protocol (MCP) patterns.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


class ConnectorStatus(str, Enum):
    """Connector connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


class ConnectorCapability(str, Enum):
    """Capabilities a connector can provide."""
    # Read operations
    READ = "read"
    LIST = "list"
    SEARCH = "search"

    # Write operations
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

    # Real-time
    SUBSCRIBE = "subscribe"
    WEBHOOK = "webhook"

    # Special
    OAUTH = "oauth"
    SYNC = "sync"
    BATCH = "batch"


class ConnectorCategory(str, Enum):
    """Connector categories."""
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    DEVELOPMENT = "development"
    SMART_HOME = "smart_home"
    FINANCE = "finance"
    HEALTH = "health"
    ENTERTAINMENT = "entertainment"
    TRAVEL = "travel"
    SOCIAL = "social"
    STORAGE = "storage"


@dataclass
class ConnectorAuth:
    """Authentication configuration for a connector."""
    auth_type: str  # oauth2, api_key, basic, custom
    credentials: Dict[str, Any] = field(default_factory=dict)
    token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scopes: List[str] = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        """Check if authentication is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excludes sensitive data)."""
        return {
            "auth_type": self.auth_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scopes": self.scopes,
            "has_token": bool(self.token),
            "has_refresh_token": bool(self.refresh_token),
        }


@dataclass
class ConnectorConfig:
    """Configuration for a connector instance."""
    connector_type: str
    user_id: str
    enabled: bool = True
    auth: Optional[ConnectorAuth] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Sync settings
    sync_enabled: bool = True
    sync_interval_minutes: int = 15
    last_sync_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "connector_type": self.connector_type,
            "user_id": self.user_id,
            "enabled": self.enabled,
            "auth": self.auth.to_dict() if self.auth else None,
            "settings": self.settings,
            "sync_enabled": self.sync_enabled,
            "sync_interval_minutes": self.sync_interval_minutes,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
        }


class ConnectorError(Exception):
    """Base exception for connector errors."""

    def __init__(self, message: str, connector_type: str, details: Optional[Dict] = None):
        self.message = message
        self.connector_type = connector_type
        self.details = details or {}
        super().__init__(message)


class ConnectionError(ConnectorError):
    """Failed to connect to external service."""
    pass


class AuthenticationError(ConnectorError):
    """Authentication with external service failed."""
    pass


class RateLimitError(ConnectorError):
    """Rate limit exceeded for external service."""

    def __init__(
        self,
        message: str,
        connector_type: str,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message, connector_type)
        self.retry_after = retry_after


class BaseConnector(ABC):
    """
    Abstract base class for all connectors.

    Connectors integrate Alfred with external services following MCP patterns.

    Each connector must implement:
    - connect(): Establish connection
    - disconnect(): Clean up connection
    - health_check(): Verify connection is alive
    - get_resources(): List available resources

    Optionally implement:
    - sync(): Synchronize data from the service
    - handle_webhook(): Process incoming webhooks
    """

    # Class attributes - override in subclasses
    connector_type: str = "base"
    display_name: str = "Base Connector"
    description: str = ""
    category: ConnectorCategory = ConnectorCategory.PRODUCTIVITY
    capabilities: List[ConnectorCapability] = []
    required_scopes: List[str] = []
    icon: str = "plug"

    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._status = ConnectorStatus.DISCONNECTED
        self._last_error: Optional[str] = None
        self._connected_at: Optional[datetime] = None

    @property
    def status(self) -> ConnectorStatus:
        """Get current connection status."""
        return self._status

    @property
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self._status == ConnectorStatus.CONNECTED

    @property
    def user_id(self) -> str:
        """Get user ID for this connector instance."""
        return self.config.user_id

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the external service.

        Returns:
            True if connection successful, False otherwise.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the external service.

        Returns:
            True if disconnection successful.
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check connection health.

        Returns:
            Dict with health status and details.
        """
        pass

    @abstractmethod
    async def get_resources(self) -> List[Dict[str, Any]]:
        """
        List available resources from this connector.

        MCP-style resource listing.

        Returns:
            List of resource descriptors.
        """
        pass

    async def refresh_auth(self) -> bool:
        """
        Refresh authentication if needed.

        Override in connectors that support token refresh.
        """
        if not self.config.auth or not self.config.auth.refresh_token:
            return False
        # Subclass implements actual refresh logic
        return True

    async def sync(self) -> Dict[str, Any]:
        """
        Synchronize data from the external service.

        Override in connectors that support data sync.

        Returns:
            Sync result with counts and any errors.
        """
        return {"synced": False, "message": "Sync not implemented"}

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming webhook from the external service.

        Override in connectors that support webhooks.
        """
        return {"handled": False, "message": "Webhooks not implemented"}

    def get_oauth_url(self, redirect_uri: str, state: str) -> Optional[str]:
        """
        Get OAuth authorization URL.

        Override in connectors that use OAuth.
        """
        return None

    async def exchange_oauth_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> Optional[ConnectorAuth]:
        """
        Exchange OAuth authorization code for tokens.

        Override in connectors that use OAuth.
        """
        return None

    def _set_status(self, status: ConnectorStatus, error: Optional[str] = None):
        """Update connector status."""
        self._status = status
        self._last_error = error
        if status == ConnectorStatus.CONNECTED:
            self._connected_at = datetime.utcnow()

    def get_info(self) -> Dict[str, Any]:
        """Get connector information and current status."""
        return {
            "type": self.connector_type,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.value,
            "capabilities": [c.value for c in self.capabilities],
            "status": self._status.value,
            "last_error": self._last_error,
            "connected_at": self._connected_at.isoformat() if self._connected_at else None,
            "config": {
                "enabled": self.config.enabled,
                "sync_enabled": self.config.sync_enabled,
                "last_sync_at": (
                    self.config.last_sync_at.isoformat()
                    if self.config.last_sync_at else None
                ),
            },
        }


class MCPResource:
    """
    Model Context Protocol Resource representation.

    Resources are things the connector can provide (files, data, etc).
    """

    def __init__(
        self,
        uri: str,
        name: str,
        description: str = "",
        mime_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.uri = uri
        self.name = name
        self.description = description
        self.mime_type = mime_type
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
            "metadata": self.metadata,
        }


class MCPTool:
    """
    Model Context Protocol Tool representation.

    Tools are actions the connector can perform.
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: callable,
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }
