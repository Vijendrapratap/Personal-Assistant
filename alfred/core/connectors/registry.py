"""
Connector Registry.

Central registry for all available connectors.
"""

from typing import Dict, Type, List, Optional, Any
from functools import wraps
import logging

from alfred.core.connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorCategory,
    ConnectorCapability,
)


logger = logging.getLogger("alfred.connectors")


class ConnectorRegistry:
    """
    Registry of available connectors.

    Manages connector types and their instantiation.
    """

    _instance: Optional["ConnectorRegistry"] = None

    def __init__(self):
        self._connectors: Dict[str, Type[BaseConnector]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_instance(cls) -> "ConnectorRegistry":
        """Get singleton registry instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(
        self,
        connector_class: Type[BaseConnector],
        override: bool = False,
    ) -> None:
        """
        Register a connector type.

        Args:
            connector_class: The connector class to register
            override: If True, allow overriding existing registration
        """
        connector_type = connector_class.connector_type

        if connector_type in self._connectors and not override:
            raise ValueError(f"Connector '{connector_type}' is already registered")

        self._connectors[connector_type] = connector_class
        self._metadata[connector_type] = {
            "display_name": connector_class.display_name,
            "description": connector_class.description,
            "category": connector_class.category,
            "capabilities": connector_class.capabilities,
            "required_scopes": connector_class.required_scopes,
            "icon": connector_class.icon,
        }

        logger.info(f"Registered connector: {connector_type}")

    def unregister(self, connector_type: str) -> bool:
        """Unregister a connector type."""
        if connector_type in self._connectors:
            del self._connectors[connector_type]
            del self._metadata[connector_type]
            return True
        return False

    def get_connector_class(
        self,
        connector_type: str,
    ) -> Optional[Type[BaseConnector]]:
        """Get connector class by type."""
        return self._connectors.get(connector_type)

    def create_connector(
        self,
        connector_type: str,
        config: ConnectorConfig,
    ) -> Optional[BaseConnector]:
        """
        Create a connector instance.

        Args:
            connector_type: Type of connector to create
            config: Configuration for the connector

        Returns:
            Connector instance or None if type not found
        """
        connector_class = self._connectors.get(connector_type)
        if connector_class is None:
            logger.warning(f"Unknown connector type: {connector_type}")
            return None

        return connector_class(config)

    def list_connectors(self) -> List[Dict[str, Any]]:
        """List all registered connectors with metadata."""
        return [
            {
                "type": connector_type,
                **metadata,
                "category": metadata["category"].value if isinstance(
                    metadata["category"], ConnectorCategory
                ) else metadata["category"],
                "capabilities": [
                    c.value if isinstance(c, ConnectorCapability) else c
                    for c in metadata["capabilities"]
                ],
            }
            for connector_type, metadata in self._metadata.items()
        ]

    def list_by_category(
        self,
        category: ConnectorCategory,
    ) -> List[Dict[str, Any]]:
        """List connectors in a specific category."""
        return [
            connector for connector in self.list_connectors()
            if connector["category"] == category.value
        ]

    def list_with_capability(
        self,
        capability: ConnectorCapability,
    ) -> List[Dict[str, Any]]:
        """List connectors with a specific capability."""
        return [
            connector for connector in self.list_connectors()
            if capability.value in connector["capabilities"]
        ]

    def is_registered(self, connector_type: str) -> bool:
        """Check if a connector type is registered."""
        return connector_type in self._connectors

    @property
    def connector_types(self) -> List[str]:
        """Get list of all registered connector types."""
        return list(self._connectors.keys())


def get_connector_registry() -> ConnectorRegistry:
    """Get the global connector registry."""
    return ConnectorRegistry.get_instance()


def register_connector(cls: Type[BaseConnector]) -> Type[BaseConnector]:
    """
    Decorator to register a connector class.

    Usage:
        @register_connector
        class GoogleCalendarConnector(BaseConnector):
            connector_type = "google_calendar"
            ...
    """
    registry = get_connector_registry()
    registry.register(cls)
    return cls


class ConnectorCatalog:
    """
    Static catalog of available connectors with metadata.

    Used for displaying available integrations to users.
    """

    PRODUCTIVITY = [
        {
            "type": "google_calendar",
            "name": "Google Calendar",
            "description": "Sync events and manage your calendar",
            "icon": "calendar",
            "auth_type": "oauth2",
        },
        {
            "type": "google_tasks",
            "name": "Google Tasks",
            "description": "Sync tasks from Google Tasks",
            "icon": "check-square",
            "auth_type": "oauth2",
        },
        {
            "type": "notion",
            "name": "Notion",
            "description": "Connect your Notion workspace",
            "icon": "file-text",
            "auth_type": "oauth2",
        },
        {
            "type": "todoist",
            "name": "Todoist",
            "description": "Sync tasks from Todoist",
            "icon": "check-circle",
            "auth_type": "oauth2",
        },
    ]

    COMMUNICATION = [
        {
            "type": "gmail",
            "name": "Gmail",
            "description": "Access your email",
            "icon": "mail",
            "auth_type": "oauth2",
        },
        {
            "type": "slack",
            "name": "Slack",
            "description": "Connect your Slack workspace",
            "icon": "message-square",
            "auth_type": "oauth2",
        },
        {
            "type": "discord",
            "name": "Discord",
            "description": "Connect your Discord server",
            "icon": "message-circle",
            "auth_type": "oauth2",
        },
    ]

    DEVELOPMENT = [
        {
            "type": "github",
            "name": "GitHub",
            "description": "Connect your GitHub repositories",
            "icon": "github",
            "auth_type": "oauth2",
        },
        {
            "type": "linear",
            "name": "Linear",
            "description": "Sync issues from Linear",
            "icon": "target",
            "auth_type": "oauth2",
        },
        {
            "type": "jira",
            "name": "Jira",
            "description": "Connect your Jira projects",
            "icon": "trello",
            "auth_type": "oauth2",
        },
    ]

    SMART_HOME = [
        {
            "type": "home_assistant",
            "name": "Home Assistant",
            "description": "Control your smart home",
            "icon": "home",
            "auth_type": "api_key",
        },
        {
            "type": "philips_hue",
            "name": "Philips Hue",
            "description": "Control your Hue lights",
            "icon": "sun",
            "auth_type": "oauth2",
        },
    ]

    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        """Get all available connectors."""
        all_connectors = []
        for category in [
            cls.PRODUCTIVITY,
            cls.COMMUNICATION,
            cls.DEVELOPMENT,
            cls.SMART_HOME,
        ]:
            all_connectors.extend(category)
        return all_connectors

    @classmethod
    def get_by_category(cls, category: str) -> List[Dict[str, Any]]:
        """Get connectors by category name."""
        category_map = {
            "productivity": cls.PRODUCTIVITY,
            "communication": cls.COMMUNICATION,
            "development": cls.DEVELOPMENT,
            "smart_home": cls.SMART_HOME,
        }
        return category_map.get(category.lower(), [])
