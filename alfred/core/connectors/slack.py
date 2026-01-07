"""
Slack Connector.

Integrates with Slack for messaging and notifications.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlencode

from alfred.core.connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorStatus,
    ConnectorCapability,
    ConnectorCategory,
    ConnectorAuth,
    ConnectorError,
    AuthenticationError,
    MCPResource,
)
from alfred.core.connectors.registry import register_connector


logger = logging.getLogger("alfred.connectors.slack")


@register_connector
class SlackConnector(BaseConnector):
    """
    Slack connector for workspace communication.

    Capabilities:
    - List channels and direct messages
    - Send and read messages
    - React to messages
    - Search messages
    - Receive real-time events via webhooks
    """

    connector_type = "slack"
    display_name = "Slack"
    description = "Connect your Slack workspace for messaging and notifications"
    category = ConnectorCategory.COMMUNICATION
    capabilities = [
        ConnectorCapability.READ,
        ConnectorCapability.LIST,
        ConnectorCapability.CREATE,
        ConnectorCapability.SEARCH,
        ConnectorCapability.WEBHOOK,
        ConnectorCapability.SUBSCRIBE,
        ConnectorCapability.OAUTH,
    ]
    required_scopes = [
        "channels:read",
        "channels:history",
        "chat:write",
        "users:read",
        "search:read",
        "reactions:read",
        "reactions:write",
    ]
    icon = "slack"

    # OAuth config
    OAUTH_AUTH_URL = "https://slack.com/oauth/v2/authorize"
    OAUTH_TOKEN_URL = "https://slack.com/api/oauth.v2.access"
    API_BASE_URL = "https://slack.com/api"

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client_id = os.getenv("SLACK_CLIENT_ID", "")
        self._client_secret = os.getenv("SLACK_CLIENT_SECRET", "")
        self._team_info: Optional[Dict] = None
        self._user_info: Optional[Dict] = None

    async def connect(self) -> bool:
        """Connect to Slack API."""
        self._set_status(ConnectorStatus.CONNECTING)

        if not self.config.auth or not self.config.auth.token:
            self._set_status(ConnectorStatus.ERROR, "No authentication token")
            return False

        try:
            # Verify connection by getting auth info
            auth_test = await self._api_request("auth.test")
            if auth_test.get("ok"):
                self._team_info = {
                    "team_id": auth_test.get("team_id"),
                    "team": auth_test.get("team"),
                }
                self._user_info = {
                    "user_id": auth_test.get("user_id"),
                    "user": auth_test.get("user"),
                }
                self._set_status(ConnectorStatus.CONNECTED)
                logger.info(
                    f"Connected to Slack workspace {auth_test.get('team')} "
                    f"for user {self.user_id}"
                )
                return True
            else:
                self._set_status(ConnectorStatus.ERROR, auth_test.get("error"))
                return False

        except Exception as e:
            self._set_status(ConnectorStatus.ERROR, str(e))
            logger.error(f"Failed to connect to Slack: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Slack."""
        self._set_status(ConnectorStatus.DISCONNECTED)
        self._team_info = None
        self._user_info = None
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Check connection health."""
        if not self.is_connected:
            return {
                "healthy": False,
                "status": self._status.value,
                "error": self._last_error,
            }

        try:
            result = await self._api_request("auth.test")
            return {
                "healthy": result.get("ok", False),
                "status": "connected",
                "team": self._team_info,
                "user": self._user_info,
            }
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
            }

    async def get_resources(self) -> List[Dict[str, Any]]:
        """List available Slack resources (channels)."""
        if not self.is_connected:
            return []

        resources = []

        # Get channels
        channels = await self.list_channels()
        for channel in channels:
            resources.append(
                MCPResource(
                    uri=f"slack://channels/{channel['id']}",
                    name=f"#{channel.get('name', 'unknown')}",
                    description=channel.get("purpose", {}).get("value", ""),
                    mime_type="application/json",
                    metadata={
                        "channel_id": channel["id"],
                        "is_private": channel.get("is_private", False),
                        "num_members": channel.get("num_members", 0),
                    },
                ).to_dict()
            )

        return resources

    async def sync(self) -> Dict[str, Any]:
        """Sync recent Slack activity."""
        if not self.is_connected:
            return {"synced": False, "error": "Not connected"}

        try:
            # Get recent messages from channels user is in
            channels = await self.list_channels()
            total_messages = 0

            for channel in channels[:5]:  # Limit to 5 channels
                messages = await self.get_channel_history(
                    channel["id"],
                    limit=20,
                )
                total_messages += len(messages)

            return {
                "synced": True,
                "channels_synced": len(channels),
                "messages_synced": total_messages,
            }

        except Exception as e:
            logger.error(f"Slack sync failed: {e}")
            return {"synced": False, "error": str(e)}

    def get_oauth_url(self, redirect_uri: str, state: str) -> Optional[str]:
        """Generate OAuth authorization URL."""
        if not self._client_id:
            return None

        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "scope": ",".join(self.required_scopes),
            "state": state,
        }

        return f"{self.OAUTH_AUTH_URL}?{urlencode(params)}"

    async def exchange_oauth_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> Optional[ConnectorAuth]:
        """Exchange authorization code for tokens."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.OAUTH_TOKEN_URL,
                    data={
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri,
                    },
                ) as response:
                    data = await response.json()
                    if data.get("ok"):
                        return ConnectorAuth(
                            auth_type="oauth2",
                            token=data["access_token"],
                            scopes=data.get("scope", "").split(","),
                            credentials={
                                "team_id": data.get("team", {}).get("id"),
                                "team_name": data.get("team", {}).get("name"),
                            },
                        )
                    logger.error(f"OAuth exchange failed: {data.get('error')}")
                    return None
        except Exception as e:
            logger.error(f"OAuth exchange error: {e}")
            return None

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Slack webhook events."""
        event_type = payload.get("type")

        if event_type == "url_verification":
            # Respond to Slack's URL verification challenge
            return {"challenge": payload.get("challenge")}

        if event_type == "event_callback":
            event = payload.get("event", {})
            return await self._handle_event(event)

        return {"handled": True, "event_type": event_type}

    # Slack-specific methods

    async def list_channels(
        self,
        types: str = "public_channel,private_channel",
    ) -> List[Dict[str, Any]]:
        """List channels the bot/user has access to."""
        if not self.is_connected:
            return []

        result = await self._api_request(
            "conversations.list",
            params={"types": types, "limit": 200},
        )
        return result.get("channels", [])

    async def get_channel_history(
        self,
        channel_id: str,
        limit: int = 100,
        oldest: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get message history from a channel."""
        if not self.is_connected:
            return []

        params = {"channel": channel_id, "limit": limit}
        if oldest:
            params["oldest"] = oldest

        result = await self._api_request("conversations.history", params=params)
        return result.get("messages", [])

    async def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a message to a channel."""
        if not self.is_connected:
            return None

        data = {
            "channel": channel,
            "text": text,
        }

        if thread_ts:
            data["thread_ts"] = thread_ts
        if blocks:
            data["blocks"] = blocks

        result = await self._api_request("chat.postMessage", json=data)
        if result.get("ok"):
            return {
                "ts": result.get("ts"),
                "channel": result.get("channel"),
            }
        return None

    async def search_messages(
        self,
        query: str,
        count: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search messages."""
        if not self.is_connected:
            return []

        result = await self._api_request(
            "search.messages",
            params={"query": query, "count": count},
        )
        return result.get("messages", {}).get("matches", [])

    async def add_reaction(
        self,
        channel: str,
        timestamp: str,
        emoji: str,
    ) -> bool:
        """Add a reaction to a message."""
        if not self.is_connected:
            return False

        result = await self._api_request(
            "reactions.add",
            json={
                "channel": channel,
                "timestamp": timestamp,
                "name": emoji,
            },
        )
        return result.get("ok", False)

    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a user."""
        if not self.is_connected:
            return None

        result = await self._api_request(
            "users.info",
            params={"user": user_id},
        )
        return result.get("user")

    # Private helpers

    async def _api_request(
        self,
        method: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated API request."""
        import aiohttp

        url = f"{self.API_BASE_URL}/{method}"
        headers = {
            "Authorization": f"Bearer {self.config.auth.token}",
        }

        async with aiohttp.ClientSession() as session:
            if json:
                headers["Content-Type"] = "application/json"
                async with session.post(
                    url,
                    headers=headers,
                    json=json,
                ) as response:
                    return await response.json()
            else:
                async with session.get(
                    url,
                    headers=headers,
                    params=params,
                ) as response:
                    return await response.json()

    async def _handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a Slack event."""
        event_type = event.get("type")

        if event_type == "message":
            return {
                "handled": True,
                "event": "message",
                "channel": event.get("channel"),
                "user": event.get("user"),
                "text": event.get("text", "")[:100],  # Truncate for safety
            }

        return {"handled": True, "event": event_type}
