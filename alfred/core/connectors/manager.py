"""
Connector Manager.

Manages connector lifecycle and user connections.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from alfred.core.connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorStatus,
    ConnectorAuth,
    ConnectorError,
)
from alfred.core.connectors.registry import get_connector_registry


logger = logging.getLogger("alfred.connectors.manager")


class ConnectorManager:
    """
    Manages connector instances for users.

    Responsibilities:
    - Create and manage connector instances per user
    - Handle connector lifecycle (connect, disconnect, reconnect)
    - Schedule and run sync operations
    - Manage OAuth flows
    """

    def __init__(self, storage: Any = None):
        """
        Initialize connector manager.

        Args:
            storage: Storage provider for persisting connector configs
        """
        self.storage = storage
        self._connectors: Dict[str, Dict[str, BaseConnector]] = {}  # user_id -> {type -> connector}
        self._sync_tasks: Dict[str, asyncio.Task] = {}
        self._registry = get_connector_registry()

    async def initialize(self) -> None:
        """Initialize manager and restore saved connections."""
        if not self.storage:
            logger.warning("No storage provider - connectors won't persist")
            return

        # Load saved connector configs and reconnect
        # Implementation depends on storage interface
        pass

    async def shutdown(self) -> None:
        """Shutdown manager and disconnect all connectors."""
        # Cancel all sync tasks
        for task in self._sync_tasks.values():
            task.cancel()

        # Disconnect all connectors
        for user_connectors in self._connectors.values():
            for connector in user_connectors.values():
                try:
                    await connector.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting {connector.connector_type}: {e}")

        self._connectors.clear()
        self._sync_tasks.clear()

    async def add_connector(
        self,
        user_id: str,
        connector_type: str,
        auth: Optional[ConnectorAuth] = None,
        settings: Optional[Dict[str, Any]] = None,
        auto_connect: bool = True,
    ) -> Optional[BaseConnector]:
        """
        Add a new connector for a user.

        Args:
            user_id: User ID
            connector_type: Type of connector to add
            auth: Authentication config (if available)
            settings: Connector-specific settings
            auto_connect: Whether to connect immediately

        Returns:
            Connector instance or None if failed
        """
        # Check if connector type exists
        if not self._registry.is_registered(connector_type):
            logger.error(f"Unknown connector type: {connector_type}")
            return None

        # Check if user already has this connector
        if self._get_user_connector(user_id, connector_type):
            logger.warning(f"User {user_id} already has connector {connector_type}")
            return self._get_user_connector(user_id, connector_type)

        # Create config
        config = ConnectorConfig(
            connector_type=connector_type,
            user_id=user_id,
            auth=auth,
            settings=settings or {},
        )

        # Create connector instance
        connector = self._registry.create_connector(connector_type, config)
        if not connector:
            return None

        # Store connector
        if user_id not in self._connectors:
            self._connectors[user_id] = {}
        self._connectors[user_id][connector_type] = connector

        # Save to storage
        if self.storage:
            await self._save_connector_config(user_id, connector_type, config)

        # Connect if requested and auth is available
        if auto_connect and auth:
            try:
                await connector.connect()
            except ConnectorError as e:
                logger.error(f"Failed to connect {connector_type}: {e}")

        logger.info(f"Added connector {connector_type} for user {user_id}")
        return connector

    async def remove_connector(
        self,
        user_id: str,
        connector_type: str,
    ) -> bool:
        """Remove a connector for a user."""
        connector = self._get_user_connector(user_id, connector_type)
        if not connector:
            return False

        # Disconnect
        try:
            await connector.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting {connector_type}: {e}")

        # Remove from memory
        del self._connectors[user_id][connector_type]
        if not self._connectors[user_id]:
            del self._connectors[user_id]

        # Remove from storage
        if self.storage:
            await self._delete_connector_config(user_id, connector_type)

        # Cancel sync task if any
        sync_key = f"{user_id}:{connector_type}"
        if sync_key in self._sync_tasks:
            self._sync_tasks[sync_key].cancel()
            del self._sync_tasks[sync_key]

        logger.info(f"Removed connector {connector_type} for user {user_id}")
        return True

    def get_connector(
        self,
        user_id: str,
        connector_type: str,
    ) -> Optional[BaseConnector]:
        """Get a specific connector for a user."""
        return self._get_user_connector(user_id, connector_type)

    def get_user_connectors(
        self,
        user_id: str,
    ) -> List[BaseConnector]:
        """Get all connectors for a user."""
        return list(self._connectors.get(user_id, {}).values())

    def get_user_connector_info(
        self,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """Get info about all user's connectors."""
        connectors = self.get_user_connectors(user_id)
        return [c.get_info() for c in connectors]

    async def connect(
        self,
        user_id: str,
        connector_type: str,
    ) -> bool:
        """Connect a specific connector."""
        connector = self._get_user_connector(user_id, connector_type)
        if not connector:
            return False

        try:
            return await connector.connect()
        except ConnectorError as e:
            logger.error(f"Connection failed for {connector_type}: {e}")
            return False

    async def disconnect(
        self,
        user_id: str,
        connector_type: str,
    ) -> bool:
        """Disconnect a specific connector."""
        connector = self._get_user_connector(user_id, connector_type)
        if not connector:
            return False

        try:
            return await connector.disconnect()
        except ConnectorError as e:
            logger.error(f"Disconnection failed for {connector_type}: {e}")
            return False

    async def sync_connector(
        self,
        user_id: str,
        connector_type: str,
    ) -> Dict[str, Any]:
        """Manually trigger sync for a connector."""
        connector = self._get_user_connector(user_id, connector_type)
        if not connector:
            return {"success": False, "error": "Connector not found"}

        if not connector.is_connected:
            return {"success": False, "error": "Connector not connected"}

        try:
            result = await connector.sync()
            connector.config.last_sync_at = datetime.utcnow()
            return {"success": True, **result}
        except ConnectorError as e:
            logger.error(f"Sync failed for {connector_type}: {e}")
            return {"success": False, "error": str(e)}

    async def sync_all_user_connectors(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Sync all connectors for a user."""
        results = {}
        for connector in self.get_user_connectors(user_id):
            if connector.is_connected and connector.config.sync_enabled:
                results[connector.connector_type] = await self.sync_connector(
                    user_id,
                    connector.connector_type,
                )
        return results

    async def start_background_sync(
        self,
        user_id: str,
        connector_type: str,
    ) -> bool:
        """Start background sync task for a connector."""
        connector = self._get_user_connector(user_id, connector_type)
        if not connector:
            return False

        sync_key = f"{user_id}:{connector_type}"
        if sync_key in self._sync_tasks:
            return True  # Already running

        async def sync_loop():
            while True:
                try:
                    await asyncio.sleep(connector.config.sync_interval_minutes * 60)
                    if connector.is_connected and connector.config.sync_enabled:
                        await connector.sync()
                        connector.config.last_sync_at = datetime.utcnow()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Background sync error for {connector_type}: {e}")

        self._sync_tasks[sync_key] = asyncio.create_task(sync_loop())
        return True

    async def stop_background_sync(
        self,
        user_id: str,
        connector_type: str,
    ) -> bool:
        """Stop background sync task for a connector."""
        sync_key = f"{user_id}:{connector_type}"
        if sync_key not in self._sync_tasks:
            return False

        self._sync_tasks[sync_key].cancel()
        del self._sync_tasks[sync_key]
        return True

    # OAuth flow helpers

    def get_oauth_url(
        self,
        connector_type: str,
        redirect_uri: str,
        state: str,
    ) -> Optional[str]:
        """
        Get OAuth authorization URL for a connector type.

        Used to initiate OAuth flow before connector is created.
        """
        connector_class = self._registry.get_connector_class(connector_type)
        if not connector_class:
            return None

        # Create temporary instance to get OAuth URL
        temp_config = ConnectorConfig(
            connector_type=connector_type,
            user_id="temp",
        )
        temp_connector = connector_class(temp_config)
        return temp_connector.get_oauth_url(redirect_uri, state)

    async def complete_oauth(
        self,
        user_id: str,
        connector_type: str,
        code: str,
        redirect_uri: str,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Optional[BaseConnector]:
        """
        Complete OAuth flow and create connector.

        Args:
            user_id: User ID
            connector_type: Type of connector
            code: OAuth authorization code
            redirect_uri: Redirect URI used in authorization
            settings: Additional connector settings

        Returns:
            Connected connector instance or None if failed
        """
        connector_class = self._registry.get_connector_class(connector_type)
        if not connector_class:
            return None

        # Create temporary connector to exchange code
        temp_config = ConnectorConfig(
            connector_type=connector_type,
            user_id=user_id,
            settings=settings or {},
        )
        temp_connector = connector_class(temp_config)

        # Exchange code for tokens
        auth = await temp_connector.exchange_oauth_code(code, redirect_uri)
        if not auth:
            logger.error(f"OAuth token exchange failed for {connector_type}")
            return None

        # Create permanent connector with auth
        return await self.add_connector(
            user_id=user_id,
            connector_type=connector_type,
            auth=auth,
            settings=settings,
            auto_connect=True,
        )

    # Webhook handling

    async def handle_webhook(
        self,
        connector_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Route webhook to appropriate connector(s).

        Note: Webhooks may need to be routed to multiple user connectors.
        """
        results = []

        # Find all connectors of this type
        for user_id, user_connectors in self._connectors.items():
            connector = user_connectors.get(connector_type)
            if connector and connector.is_connected:
                try:
                    result = await connector.handle_webhook(payload)
                    results.append({
                        "user_id": user_id,
                        **result,
                    })
                except Exception as e:
                    logger.error(f"Webhook handling error for {user_id}: {e}")

        return {"handled": len(results) > 0, "results": results}

    # Private helpers

    def _get_user_connector(
        self,
        user_id: str,
        connector_type: str,
    ) -> Optional[BaseConnector]:
        """Get connector for a specific user and type."""
        return self._connectors.get(user_id, {}).get(connector_type)

    async def _save_connector_config(
        self,
        user_id: str,
        connector_type: str,
        config: ConnectorConfig,
    ) -> None:
        """Save connector config to storage."""
        if self.storage and hasattr(self.storage, "save_connector_config"):
            await self.storage.save_connector_config(user_id, connector_type, config.to_dict())

    async def _delete_connector_config(
        self,
        user_id: str,
        connector_type: str,
    ) -> None:
        """Delete connector config from storage."""
        if self.storage and hasattr(self.storage, "delete_connector_config"):
            await self.storage.delete_connector_config(user_id, connector_type)
