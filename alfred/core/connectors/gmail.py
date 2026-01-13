"""
Gmail Connector.

Integrates with Gmail API for email management.
"""

import os
import base64
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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


logger = logging.getLogger("alfred.connectors.gmail")


@register_connector
class GmailConnector(BaseConnector):
    """
    Gmail connector.

    Capabilities:
    - List and search emails
    - Read email content
    - Send emails
    - Manage labels
    - Subscribe to email changes (webhook via push notifications)
    """

    connector_type = "gmail"
    display_name = "Gmail"
    description = "Access and manage your Gmail inbox"
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
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.labels",
    ]
    icon = "mail"

    # OAuth config
    OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
    API_BASE_URL = "https://gmail.googleapis.com/gmail/v1"

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self._client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        self._http_client = None

    async def connect(self) -> bool:
        """Connect to Gmail API."""
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

        # Verify connection by fetching profile
        try:
            profile = await self._api_request("GET", "/users/me/profile")
            if profile:
                self._set_status(ConnectorStatus.CONNECTED)
                logger.info(f"Connected to Gmail for user {self.user_id}")
                return True
        except Exception as e:
            self._set_status(ConnectorStatus.ERROR, str(e))
            logger.error(f"Failed to connect to Gmail: {e}")

        return False

    async def disconnect(self) -> bool:
        """Disconnect from Gmail."""
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
            profile = await self._api_request("GET", "/users/me/profile")
            return {
                "healthy": True,
                "status": "connected",
                "email": profile.get("emailAddress"),
                "messages_total": profile.get("messagesTotal"),
            }
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
            }

    async def get_resources(self) -> List[Dict[str, Any]]:
        """List available Gmail resources."""
        if not self.is_connected:
            return []

        resources = []

        # Add inbox as a resource
        resources.append(
            MCPResource(
                uri="gmail://inbox",
                name="Inbox",
                description="Primary inbox",
                mime_type="application/json",
                metadata={"type": "mailbox", "label": "INBOX"},
            ).to_dict()
        )

        # Get labels
        labels = await self._api_request("GET", "/users/me/labels")
        for label in labels.get("labels", []):
            resources.append(
                MCPResource(
                    uri=f"gmail://labels/{label['id']}",
                    name=label.get("name", "Unnamed Label"),
                    description=f"Label: {label.get('name')}",
                    mime_type="application/json",
                    metadata={
                        "label_id": label["id"],
                        "type": label.get("type", "user"),
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
                    },
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.config.auth.token = data["access_token"]
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
                "/users/me/messages",
                params={
                    "maxResults": "50",
                    "labelIds": "INBOX",
                },
            )

            synced_messages = len(messages.get("messages", []))

            return {
                "synced": True,
                "messages_synced": synced_messages,
            }

        except Exception as e:
            logger.error(f"Gmail sync failed: {e}")
            return {"synced": False, "error": str(e)}

    def get_oauth_url(self, redirect_uri: str, state: str) -> Optional[str]:
        """Generate OAuth authorization URL."""
        if not self._client_id:
            return None

        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.required_scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
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

    # Gmail-specific methods

    async def list_messages(
        self,
        label_ids: Optional[List[str]] = None,
        query: Optional[str] = None,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        List messages from Gmail.

        Args:
            label_ids: Filter by labels (e.g., ["INBOX", "UNREAD"])
            query: Gmail search query (e.g., "from:john subject:meeting")
            max_results: Maximum number of messages to return
        """
        if not self.is_connected:
            return []

        params = {"maxResults": str(max_results)}
        if label_ids:
            params["labelIds"] = ",".join(label_ids)
        if query:
            params["q"] = query

        result = await self._api_request("GET", "/users/me/messages", params=params)
        return result.get("messages", [])

    async def get_message(
        self,
        message_id: str,
        format: str = "full",
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific email message.

        Args:
            message_id: The message ID
            format: "full", "minimal", "raw", or "metadata"
        """
        if not self.is_connected:
            return None

        return await self._api_request(
            "GET",
            f"/users/me/messages/{message_id}",
            params={"format": format},
        )

    async def get_message_content(self, message_id: str) -> Dict[str, Any]:
        """Get message with parsed content."""
        message = await self.get_message(message_id, format="full")
        if not message:
            return {}

        headers = {}
        for header in message.get("payload", {}).get("headers", []):
            headers[header["name"].lower()] = header["value"]

        body = ""
        payload = message.get("payload", {})

        # Extract body from parts or directly
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    body = base64.urlsafe_b64decode(data).decode("utf-8")
                    break
        elif "body" in payload:
            data = payload["body"].get("data", "")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8")

        return {
            "id": message_id,
            "thread_id": message.get("threadId"),
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "subject": headers.get("subject", ""),
            "date": headers.get("date", ""),
            "body": body,
            "labels": message.get("labelIds", []),
            "snippet": message.get("snippet", ""),
        }

    async def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Send an email message.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            cc: CC recipients
            bcc: BCC recipients
            html: Whether body is HTML
        """
        if not self.is_connected:
            return None

        # Create message
        message = MIMEMultipart() if html else MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        if cc:
            message["cc"] = ", ".join(cc)
        if bcc:
            message["bcc"] = ", ".join(bcc)

        if html:
            message.attach(MIMEText(body, "html"))

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        return await self._api_request(
            "POST",
            "/users/me/messages/send",
            json={"raw": raw_message},
        )

    async def search_messages(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for messages using Gmail query syntax.

        Args:
            query: Gmail search query (e.g., "from:john after:2024/01/01")
            max_results: Maximum number of results
        """
        return await self.list_messages(query=query, max_results=max_results)

    async def get_unread_count(self) -> int:
        """Get count of unread messages in inbox."""
        if not self.is_connected:
            return 0

        messages = await self.list_messages(
            label_ids=["INBOX", "UNREAD"],
            max_results=100,
        )
        return len(messages)

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        if not self.is_connected:
            return False

        try:
            await self._api_request(
                "POST",
                f"/users/me/messages/{message_id}/modify",
                json={"removeLabelIds": ["UNREAD"]},
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
                "POST",
                f"/users/me/messages/{message_id}/modify",
                json={"addLabelIds": ["UNREAD"]},
            )
            return True
        except Exception:
            return False

    async def archive_message(self, message_id: str) -> bool:
        """Archive a message (remove from inbox)."""
        if not self.is_connected:
            return False

        try:
            await self._api_request(
                "POST",
                f"/users/me/messages/{message_id}/modify",
                json={"removeLabelIds": ["INBOX"]},
            )
            return True
        except Exception:
            return False

    async def trash_message(self, message_id: str) -> bool:
        """Move a message to trash."""
        if not self.is_connected:
            return False

        try:
            await self._api_request(
                "POST",
                f"/users/me/messages/{message_id}/trash",
            )
            return True
        except Exception:
            return False

    async def list_labels(self) -> List[Dict[str, Any]]:
        """List all labels."""
        if not self.is_connected:
            return []

        result = await self._api_request("GET", "/users/me/labels")
        return result.get("labels", [])

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

                return await response.json()
