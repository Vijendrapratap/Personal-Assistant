"""
Outlook/Microsoft Graph Mail Connector.

Integrates with Microsoft Graph API for Outlook email management.
"""

import os
import base64
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
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


logger = logging.getLogger("alfred.connectors.outlook")


@register_connector
class OutlookConnector(BaseConnector):
    """
    Microsoft Outlook connector via Microsoft Graph API.

    Capabilities:
    - List and search emails
    - Read email content
    - Send emails
    - Manage folders
    - Subscribe to email changes (webhook via subscriptions)
    """

    connector_type = "outlook"
    display_name = "Outlook"
    description = "Access and manage your Microsoft Outlook inbox"
    category = ConnectorCategory.COMMUNICATION
    capabilities = [
        ConnectorCapability.READ,
        ConnectorCapability.LIST,
        ConnectorCapability.SEARCH,
        ConnectorCapability.CREATE,
        ConnectorCapability.UPDATE,
        ConnectorCapability.DELETE,
        ConnectorCapability.SYNC,
        ConnectorCapability.OAUTH,
    ]
    required_scopes = [
        "Mail.Read",
        "Mail.Send",
        "Mail.ReadWrite",
        "User.Read",
    ]
    icon = "mail"

    # OAuth config - Microsoft Identity Platform
    OAUTH_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    OAUTH_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    API_BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client_id = os.getenv("MICROSOFT_CLIENT_ID", "")
        self._client_secret = os.getenv("MICROSOFT_CLIENT_SECRET", "")
        self._http_client = None

    async def connect(self) -> bool:
        """Connect to Microsoft Graph API."""
        self._set_status(ConnectorStatus.CONNECTING)

        if not self.config.auth or not self.config.auth.token:
            self._set_status(ConnectorStatus.ERROR, "No authentication token")
            return False

        # Check if token needs refresh
        if self.config.auth.is_expired:
            refreshed = await self.refresh_auth()
            if not refreshed:
                self._set_status(ConnectorStatus.ERROR, "Failed to refresh token")
                return False

        # Verify connection by fetching user profile
        try:
            profile = await self._api_request("GET", "/me")
            if profile:
                self._set_status(ConnectorStatus.CONNECTED)
                logger.info(f"Connected to Outlook for user {self.user_id}")
                return True
        except Exception as e:
            self._set_status(ConnectorStatus.ERROR, str(e))
            logger.error(f"Failed to connect to Outlook: {e}")

        return False

    async def disconnect(self) -> bool:
        """Disconnect from Outlook."""
        self._set_status(ConnectorStatus.DISCONNECTED)
        self._http_client = None
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
            profile = await self._api_request("GET", "/me")
            return {
                "healthy": True,
                "status": "connected",
                "email": profile.get("mail") or profile.get("userPrincipalName"),
                "display_name": profile.get("displayName"),
            }
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
            }

    async def get_resources(self) -> List[Dict[str, Any]]:
        """List available Outlook resources."""
        if not self.is_connected:
            return []

        resources = []

        # Add inbox as a resource
        resources.append(
            MCPResource(
                uri="outlook://inbox",
                name="Inbox",
                description="Primary inbox",
                mime_type="application/json",
                metadata={"type": "mailbox", "folder": "inbox"},
            ).to_dict()
        )

        # Get mail folders
        folders = await self._api_request("GET", "/me/mailFolders")
        for folder in folders.get("value", []):
            resources.append(
                MCPResource(
                    uri=f"outlook://folders/{folder['id']}",
                    name=folder.get("displayName", "Unnamed Folder"),
                    description=f"Mail folder: {folder.get('displayName')}",
                    mime_type="application/json",
                    metadata={
                        "folder_id": folder["id"],
                        "total_count": folder.get("totalItemCount", 0),
                        "unread_count": folder.get("unreadItemCount", 0),
                    },
                ).to_dict()
            )

        return resources

    async def refresh_auth(self) -> bool:
        """Refresh OAuth access token."""
        if not self.config.auth or not self.config.auth.refresh_token:
            return False

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.OAUTH_TOKEN_URL,
                    data={
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "refresh_token": self.config.auth.refresh_token,
                        "grant_type": "refresh_token",
                        "scope": " ".join(self.required_scopes),
                    },
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.config.auth.token = data["access_token"]
                        self.config.auth.refresh_token = data.get(
                            "refresh_token", self.config.auth.refresh_token
                        )
                        self.config.auth.expires_at = datetime.utcnow() + timedelta(
                            seconds=data.get("expires_in", 3600)
                        )
                        return True
                    else:
                        logger.error(f"Token refresh failed: {await response.text()}")
                        return False
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False

    async def sync(self) -> Dict[str, Any]:
        """Sync recent emails."""
        if not self.is_connected:
            return {"synced": False, "error": "Not connected"}

        synced_messages = 0

        try:
            # Get recent messages from inbox
            messages = await self._api_request(
                "GET",
                "/me/mailFolders/inbox/messages",
                params={
                    "$top": "50",
                    "$orderby": "receivedDateTime desc",
                },
            )

            synced_messages = len(messages.get("value", []))

            return {
                "synced": True,
                "messages_synced": synced_messages,
            }

        except Exception as e:
            logger.error(f"Outlook sync failed: {e}")
            return {"synced": False, "error": str(e)}

    def get_oauth_url(self, redirect_uri: str, state: str) -> Optional[str]:
        """Generate OAuth authorization URL."""
        if not self._client_id:
            return None

        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.required_scopes) + " offline_access",
            "state": state,
            "response_mode": "query",
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
                        "grant_type": "authorization_code",
                        "scope": " ".join(self.required_scopes) + " offline_access",
                    },
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return ConnectorAuth(
                            auth_type="oauth2",
                            token=data["access_token"],
                            refresh_token=data.get("refresh_token"),
                            expires_at=datetime.utcnow() + timedelta(
                                seconds=data.get("expires_in", 3600)
                            ),
                            scopes=data.get("scope", "").split(),
                        )
                    else:
                        logger.error(f"OAuth exchange failed: {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"OAuth exchange error: {e}")
            return None

    # Outlook-specific methods

    async def list_messages(
        self,
        folder_id: str = "inbox",
        query: Optional[str] = None,
        max_results: int = 20,
        filter_unread: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List messages from a mail folder.

        Args:
            folder_id: Folder ID or "inbox", "sentitems", "drafts", etc.
            query: OData search query
            max_results: Maximum number of messages to return
            filter_unread: If True, only return unread messages
        """
        if not self.is_connected:
            return []

        params = {
            "$top": str(max_results),
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview",
        }

        if query:
            params["$search"] = f'"{query}"'

        if filter_unread:
            params["$filter"] = "isRead eq false"

        result = await self._api_request(
            "GET",
            f"/me/mailFolders/{folder_id}/messages",
            params=params,
        )
        return result.get("value", [])

    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific email message."""
        if not self.is_connected:
            return None

        return await self._api_request("GET", f"/me/messages/{message_id}")

    async def get_message_content(self, message_id: str) -> Dict[str, Any]:
        """Get message with parsed content."""
        message = await self.get_message(message_id)
        if not message:
            return {}

        body_content = ""
        body = message.get("body", {})
        if body.get("contentType") == "html":
            # Strip HTML tags for plain text
            import re
            body_content = re.sub(r"<[^>]+>", "", body.get("content", ""))
        else:
            body_content = body.get("content", "")

        from_address = message.get("from", {}).get("emailAddress", {})
        to_addresses = [
            r.get("emailAddress", {}).get("address", "")
            for r in message.get("toRecipients", [])
        ]

        return {
            "id": message_id,
            "conversation_id": message.get("conversationId"),
            "from": from_address.get("address", ""),
            "from_name": from_address.get("name", ""),
            "to": to_addresses,
            "subject": message.get("subject", ""),
            "date": message.get("receivedDateTime", ""),
            "body": body_content,
            "is_read": message.get("isRead", False),
            "has_attachments": message.get("hasAttachments", False),
            "importance": message.get("importance", "normal"),
        }

    async def send_message(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
        save_to_sent: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Send an email message.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body (plain text or HTML)
            cc: CC recipients
            bcc: BCC recipients
            html: Whether body is HTML
            save_to_sent: Whether to save to sent items
        """
        if not self.is_connected:
            return None

        # Build recipients
        to_recipients = [{"emailAddress": {"address": addr}} for addr in to]
        cc_recipients = [{"emailAddress": {"address": addr}} for addr in (cc or [])]
        bcc_recipients = [{"emailAddress": {"address": addr}} for addr in (bcc or [])]

        message_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML" if html else "Text",
                    "content": body,
                },
                "toRecipients": to_recipients,
            },
            "saveToSentItems": str(save_to_sent).lower(),
        }

        if cc_recipients:
            message_data["message"]["ccRecipients"] = cc_recipients
        if bcc_recipients:
            message_data["message"]["bccRecipients"] = bcc_recipients

        return await self._api_request("POST", "/me/sendMail", json=message_data)

    async def search_messages(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for messages across all folders.

        Args:
            query: Search query
            max_results: Maximum number of results
        """
        if not self.is_connected:
            return []

        params = {
            "$top": str(max_results),
            "$search": f'"{query}"',
            "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview,parentFolderId",
        }

        result = await self._api_request("GET", "/me/messages", params=params)
        return result.get("value", [])

    async def get_unread_count(self, folder_id: str = "inbox") -> int:
        """Get count of unread messages in a folder."""
        if not self.is_connected:
            return 0

        folder = await self._api_request("GET", f"/me/mailFolders/{folder_id}")
        return folder.get("unreadItemCount", 0)

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        if not self.is_connected:
            return False

        try:
            await self._api_request(
                "PATCH",
                f"/me/messages/{message_id}",
                json={"isRead": True},
            )
            return True
        except Exception:
            return False

    async def mark_as_unread(self, message_id: str) -> bool:
        """Mark a message as unread."""
        if not self.is_connected:
            return False

        try:
            await self._api_request(
                "PATCH",
                f"/me/messages/{message_id}",
                json={"isRead": False},
            )
            return True
        except Exception:
            return False

    async def move_message(self, message_id: str, folder_id: str) -> bool:
        """Move a message to another folder."""
        if not self.is_connected:
            return False

        try:
            await self._api_request(
                "POST",
                f"/me/messages/{message_id}/move",
                json={"destinationId": folder_id},
            )
            return True
        except Exception:
            return False

    async def delete_message(self, message_id: str) -> bool:
        """Delete a message (move to deleted items)."""
        if not self.is_connected:
            return False

        try:
            await self._api_request("DELETE", f"/me/messages/{message_id}")
            return True
        except Exception:
            return False

    async def list_folders(self) -> List[Dict[str, Any]]:
        """List all mail folders."""
        if not self.is_connected:
            return []

        result = await self._api_request("GET", "/me/mailFolders")
        return result.get("value", [])

    async def create_folder(self, display_name: str, parent_folder_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new mail folder."""
        if not self.is_connected:
            return None

        endpoint = "/me/mailFolders"
        if parent_folder_id:
            endpoint = f"/me/mailFolders/{parent_folder_id}/childFolders"

        return await self._api_request(
            "POST",
            endpoint,
            json={"displayName": display_name},
        )

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
                    # Try to refresh token
                    if await self.refresh_auth():
                        headers["Authorization"] = f"Bearer {self.config.auth.token}"
                        async with session.request(
                            method,
                            url,
                            headers=headers,
                            params=params,
                            json=json,
                        ) as retry_response:
                            if retry_response.status >= 400:
                                raise ConnectorError(
                                    await retry_response.text(),
                                    self.connector_type,
                                )
                            if method == "DELETE":
                                return {}
                            return await retry_response.json()
                    raise AuthenticationError(
                        "Authentication failed",
                        self.connector_type,
                    )

                if response.status >= 400:
                    raise ConnectorError(
                        await response.text(),
                        self.connector_type,
                    )

                if method == "DELETE":
                    return {}
                return await response.json()
