"""
Notion Connector.

Integrates with Notion for notes and database management.
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


logger = logging.getLogger("alfred.connectors.notion")


@register_connector
class NotionConnector(BaseConnector):
    """
    Notion connector for workspace knowledge management.

    Capabilities:
    - List and search pages/databases
    - Read page content
    - Create and update pages
    - Query databases
    """

    connector_type = "notion"
    display_name = "Notion"
    description = "Connect your Notion workspace for notes and databases"
    category = ConnectorCategory.PRODUCTIVITY
    capabilities = [
        ConnectorCapability.READ,
        ConnectorCapability.LIST,
        ConnectorCapability.CREATE,
        ConnectorCapability.UPDATE,
        ConnectorCapability.SEARCH,
        ConnectorCapability.OAUTH,
    ]
    required_scopes = []  # Notion uses integration tokens
    icon = "file-text"

    # OAuth config
    OAUTH_AUTH_URL = "https://api.notion.com/v1/oauth/authorize"
    OAUTH_TOKEN_URL = "https://api.notion.com/v1/oauth/token"
    API_BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client_id = os.getenv("NOTION_CLIENT_ID", "")
        self._client_secret = os.getenv("NOTION_CLIENT_SECRET", "")
        self._workspace_info: Optional[Dict] = None

    async def connect(self) -> bool:
        """Connect to Notion API."""
        self._set_status(ConnectorStatus.CONNECTING)

        if not self.config.auth or not self.config.auth.token:
            self._set_status(ConnectorStatus.ERROR, "No authentication token")
            return False

        try:
            # Verify connection by getting user info
            users = await self._api_request("GET", "/users/me")
            if users:
                self._workspace_info = {
                    "bot_id": users.get("id"),
                    "name": users.get("name"),
                    "type": users.get("type"),
                }
                self._set_status(ConnectorStatus.CONNECTED)
                logger.info(
                    f"Connected to Notion as {users.get('name')} "
                    f"for user {self.user_id}"
                )
                return True
            else:
                self._set_status(ConnectorStatus.ERROR, "Failed to get user info")
                return False

        except Exception as e:
            self._set_status(ConnectorStatus.ERROR, str(e))
            logger.error(f"Failed to connect to Notion: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Notion."""
        self._set_status(ConnectorStatus.DISCONNECTED)
        self._workspace_info = None
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
            users = await self._api_request("GET", "/users/me")
            return {
                "healthy": True,
                "status": "connected",
                "workspace": self._workspace_info,
            }
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
            }

    async def get_resources(self) -> List[Dict[str, Any]]:
        """List available Notion resources (pages and databases)."""
        if not self.is_connected:
            return []

        resources = []

        # Search for all accessible pages and databases
        results = await self.search(query="", filter_type=None)

        for item in results:
            obj_type = item.get("object")

            if obj_type == "page":
                title = self._extract_title(item)
                resources.append(
                    MCPResource(
                        uri=f"notion://pages/{item['id']}",
                        name=title or "Untitled",
                        description="Notion page",
                        mime_type="application/json",
                        metadata={
                            "page_id": item["id"],
                            "type": "page",
                            "url": item.get("url"),
                        },
                    ).to_dict()
                )

            elif obj_type == "database":
                title = self._extract_database_title(item)
                resources.append(
                    MCPResource(
                        uri=f"notion://databases/{item['id']}",
                        name=title or "Untitled Database",
                        description="Notion database",
                        mime_type="application/json",
                        metadata={
                            "database_id": item["id"],
                            "type": "database",
                            "url": item.get("url"),
                        },
                    ).to_dict()
                )

        return resources

    async def sync(self) -> Dict[str, Any]:
        """Sync Notion data."""
        if not self.is_connected:
            return {"synced": False, "error": "Not connected"}

        try:
            # Get all accessible content
            results = await self.search(query="")

            pages = [r for r in results if r.get("object") == "page"]
            databases = [r for r in results if r.get("object") == "database"]

            return {
                "synced": True,
                "pages_found": len(pages),
                "databases_found": len(databases),
            }

        except Exception as e:
            logger.error(f"Notion sync failed: {e}")
            return {"synced": False, "error": str(e)}

    def get_oauth_url(self, redirect_uri: str, state: str) -> Optional[str]:
        """Generate OAuth authorization URL."""
        if not self._client_id:
            return None

        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "owner": "user",
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
            import base64

            # Notion requires Basic auth for token exchange
            credentials = base64.b64encode(
                f"{self._client_id}:{self._client_secret}".encode()
            ).decode()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.OAUTH_TOKEN_URL,
                    headers={
                        "Authorization": f"Basic {credentials}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                    },
                ) as response:
                    data = await response.json()
                    if "access_token" in data:
                        return ConnectorAuth(
                            auth_type="oauth2",
                            token=data["access_token"],
                            credentials={
                                "workspace_id": data.get("workspace_id"),
                                "workspace_name": data.get("workspace_name"),
                                "bot_id": data.get("bot_id"),
                            },
                        )
                    logger.error(f"OAuth exchange failed: {data}")
                    return None
        except Exception as e:
            logger.error(f"OAuth exchange error: {e}")
            return None

    # Notion-specific methods

    async def search(
        self,
        query: str = "",
        filter_type: Optional[str] = None,  # "page" or "database"
        sort_direction: str = "descending",
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search for pages and databases."""
        if not self.is_connected:
            return []

        body = {
            "query": query,
            "page_size": page_size,
            "sort": {
                "direction": sort_direction,
                "timestamp": "last_edited_time",
            },
        }

        if filter_type:
            body["filter"] = {"property": "object", "value": filter_type}

        result = await self._api_request("POST", "/search", json=body)
        return result.get("results", [])

    async def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a page by ID."""
        if not self.is_connected:
            return None

        return await self._api_request("GET", f"/pages/{page_id}")

    async def get_page_content(self, page_id: str) -> List[Dict[str, Any]]:
        """Get all blocks (content) of a page."""
        if not self.is_connected:
            return []

        result = await self._api_request(
            "GET",
            f"/blocks/{page_id}/children",
            params={"page_size": 100},
        )
        return result.get("results", [])

    async def create_page(
        self,
        parent_id: str,
        title: str,
        content: Optional[List[Dict]] = None,
        properties: Optional[Dict] = None,
        is_database_page: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Create a new page."""
        if not self.is_connected:
            return None

        # Build parent reference
        if is_database_page:
            parent = {"database_id": parent_id}
        else:
            parent = {"page_id": parent_id}

        # Build properties
        if properties is None:
            properties = {}

        # Add title property
        if is_database_page:
            properties["Name"] = {"title": [{"text": {"content": title}}]}
        else:
            properties["title"] = {"title": [{"text": {"content": title}}]}

        body = {
            "parent": parent,
            "properties": properties,
        }

        # Add content blocks
        if content:
            body["children"] = content

        return await self._api_request("POST", "/pages", json=body)

    async def update_page(
        self,
        page_id: str,
        properties: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update page properties."""
        if not self.is_connected:
            return None

        return await self._api_request(
            "PATCH",
            f"/pages/{page_id}",
            json={"properties": properties},
        )

    async def append_blocks(
        self,
        page_id: str,
        blocks: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Append blocks to a page."""
        if not self.is_connected:
            return None

        return await self._api_request(
            "PATCH",
            f"/blocks/{page_id}/children",
            json={"children": blocks},
        )

    async def get_database(self, database_id: str) -> Optional[Dict[str, Any]]:
        """Get a database by ID."""
        if not self.is_connected:
            return None

        return await self._api_request("GET", f"/databases/{database_id}")

    async def query_database(
        self,
        database_id: str,
        filter: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query a database."""
        if not self.is_connected:
            return []

        body = {"page_size": page_size}
        if filter:
            body["filter"] = filter
        if sorts:
            body["sorts"] = sorts

        result = await self._api_request(
            "POST",
            f"/databases/{database_id}/query",
            json=body,
        )
        return result.get("results", [])

    # Helper methods

    def create_paragraph_block(self, text: str) -> Dict[str, Any]:
        """Create a paragraph block."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            },
        }

    def create_heading_block(
        self, text: str, level: int = 1
    ) -> Dict[str, Any]:
        """Create a heading block."""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            },
        }

    def create_todo_block(
        self, text: str, checked: bool = False
    ) -> Dict[str, Any]:
        """Create a to-do block."""
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "checked": checked,
            },
        }

    # Private helpers

    async def _api_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated API request."""
        import aiohttp

        url = f"{self.API_BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {self.config.auth.token}",
            "Notion-Version": self.API_VERSION,
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
            ) as response:
                if response.status == 401:
                    raise AuthenticationError(
                        "Authentication failed",
                        self.connector_type,
                    )

                if response.status >= 400:
                    error_data = await response.json()
                    raise ConnectorError(
                        error_data.get("message", "Unknown error"),
                        self.connector_type,
                        error_data,
                    )

                return await response.json()

    def _extract_title(self, page: Dict[str, Any]) -> str:
        """Extract title from a page object."""
        properties = page.get("properties", {})

        # Try common title property names
        for prop_name in ["title", "Title", "Name", "name"]:
            prop = properties.get(prop_name, {})
            if prop.get("type") == "title":
                title_items = prop.get("title", [])
                if title_items:
                    return title_items[0].get("plain_text", "")

        return ""

    def _extract_database_title(self, database: Dict[str, Any]) -> str:
        """Extract title from a database object."""
        title_items = database.get("title", [])
        if title_items:
            return title_items[0].get("plain_text", "")
        return ""
