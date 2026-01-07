"""
Connectors Module.

Provides integrations with external services via Model Context Protocol (MCP).

Connector Categories:
- Productivity: Calendar, Email, Tasks, Notes
- Communication: Slack, Discord, WhatsApp
- Development: GitHub, Jira, Linear
- Smart Home: Home Assistant, Philips Hue
- Finance: Banks, Crypto exchanges
- Health: Fitness trackers, sleep monitors
- Entertainment: Spotify, Netflix
- Travel: Flights, Hotels
"""

from alfred.core.connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorStatus,
    ConnectorCapability,
    ConnectorAuth,
    ConnectorError,
    ConnectionError,
    AuthenticationError,
    RateLimitError,
)
from alfred.core.connectors.registry import (
    ConnectorRegistry,
    get_connector_registry,
    register_connector,
)
from alfred.core.connectors.manager import (
    ConnectorManager,
)

__all__ = [
    # Base
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorStatus",
    "ConnectorCapability",
    "ConnectorAuth",
    # Errors
    "ConnectorError",
    "ConnectionError",
    "AuthenticationError",
    "RateLimitError",
    # Registry
    "ConnectorRegistry",
    "get_connector_registry",
    "register_connector",
    # Manager
    "ConnectorManager",
]
