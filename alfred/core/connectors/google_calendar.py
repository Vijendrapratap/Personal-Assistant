"""
Google Calendar Connector.

Integrates with Google Calendar API for event management.
"""

import os
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
    ConnectionError,
    AuthenticationError,
    MCPResource,
)
from alfred.core.connectors.registry import register_connector


logger = logging.getLogger("alfred.connectors.google_calendar")


@register_connector
class GoogleCalendarConnector(BaseConnector):
    """
    Google Calendar connector.

    Capabilities:
    - List calendars and events
    - Create, update, delete events
    - Subscribe to event changes (webhook)
    - Sync calendar data
    """

    connector_type = "google_calendar"
    display_name = "Google Calendar"
    description = "Sync events and manage your Google Calendar"
    category = ConnectorCategory.PRODUCTIVITY
    capabilities = [
        ConnectorCapability.READ,
        ConnectorCapability.LIST,
        ConnectorCapability.CREATE,
        ConnectorCapability.UPDATE,
        ConnectorCapability.DELETE,
        ConnectorCapability.SYNC,
        ConnectorCapability.WEBHOOK,
        ConnectorCapability.OAUTH,
    ]
    required_scopes = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ]
    icon = "calendar"

    # OAuth config
    OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
    API_BASE_URL = "https://www.googleapis.com/calendar/v3"

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self._client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        self._http_client = None

    async def connect(self) -> bool:
        """Connect to Google Calendar API."""
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

        # Verify connection by fetching calendar list
        try:
            calendars = await self._api_request("GET", "/users/me/calendarList")
            if calendars:
                self._set_status(ConnectorStatus.CONNECTED)
                logger.info(f"Connected to Google Calendar for user {self.user_id}")
                return True
        except Exception as e:
            self._set_status(ConnectorStatus.ERROR, str(e))
            logger.error(f"Failed to connect to Google Calendar: {e}")

        return False

    async def disconnect(self) -> bool:
        """Disconnect from Google Calendar."""
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
            # Simple API call to verify connection
            result = await self._api_request("GET", "/colors")
            return {
                "healthy": True,
                "status": "connected",
                "calendars_accessible": True,
            }
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
            }

    async def get_resources(self) -> List[Dict[str, Any]]:
        """List available calendar resources."""
        if not self.is_connected:
            return []

        resources = []

        # Get calendar list
        calendars = await self._api_request("GET", "/users/me/calendarList")
        for cal in calendars.get("items", []):
            resources.append(
                MCPResource(
                    uri=f"gcal://calendars/{cal['id']}",
                    name=cal.get("summary", "Unnamed Calendar"),
                    description=cal.get("description", ""),
                    mime_type="application/json",
                    metadata={
                        "calendar_id": cal["id"],
                        "primary": cal.get("primary", False),
                        "access_role": cal.get("accessRole", "reader"),
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
        """Sync calendar events."""
        if not self.is_connected:
            return {"synced": False, "error": "Not connected"}

        synced_events = 0
        synced_calendars = 0

        try:
            # Get primary calendar events for the next 30 days
            now = datetime.utcnow()
            time_min = now.isoformat() + "Z"
            time_max = (now + timedelta(days=30)).isoformat() + "Z"

            events = await self._api_request(
                "GET",
                "/calendars/primary/events",
                params={
                    "timeMin": time_min,
                    "timeMax": time_max,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "maxResults": 250,
                },
            )

            synced_events = len(events.get("items", []))
            synced_calendars = 1

            # Here you would save events to local storage
            # self.storage.save_events(self.user_id, events["items"])

            return {
                "synced": True,
                "events_synced": synced_events,
                "calendars_synced": synced_calendars,
            }

        except Exception as e:
            logger.error(f"Calendar sync failed: {e}")
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

    # Calendar-specific methods

    async def list_calendars(self) -> List[Dict[str, Any]]:
        """List all accessible calendars."""
        if not self.is_connected:
            return []

        result = await self._api_request("GET", "/users/me/calendarList")
        return result.get("items", [])

    async def get_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get events from a calendar."""
        if not self.is_connected:
            return []

        params = {
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": str(max_results),
        }

        if time_min:
            params["timeMin"] = time_min.isoformat() + "Z"
        if time_max:
            params["timeMax"] = time_max.isoformat() + "Z"

        result = await self._api_request(
            "GET",
            f"/calendars/{calendar_id}/events",
            params=params,
        )
        return result.get("items", [])

    async def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        calendar_id: str = "primary",
        description: str = "",
        location: str = "",
        attendees: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a new calendar event."""
        if not self.is_connected:
            return None

        event_data = {
            "summary": summary,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        }

        if description:
            event_data["description"] = description
        if location:
            event_data["location"] = location
        if attendees:
            event_data["attendees"] = [{"email": a} for a in attendees]

        return await self._api_request(
            "POST",
            f"/calendars/{calendar_id}/events",
            json=event_data,
        )

    async def update_event(
        self,
        event_id: str,
        updates: Dict[str, Any],
        calendar_id: str = "primary",
    ) -> Optional[Dict[str, Any]]:
        """Update an existing event."""
        if not self.is_connected:
            return None

        return await self._api_request(
            "PATCH",
            f"/calendars/{calendar_id}/events/{event_id}",
            json=updates,
        )

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> bool:
        """Delete an event."""
        if not self.is_connected:
            return False

        try:
            await self._api_request(
                "DELETE",
                f"/calendars/{calendar_id}/events/{event_id}",
            )
            return True
        except Exception:
            return False

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
