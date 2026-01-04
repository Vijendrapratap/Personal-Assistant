"""
Google Calendar Integration

OAuth-based Google Calendar integration.
Users authenticate via Google OAuth, app operates on their behalf.
"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from alfred.integrations.base import (
    CalendarIntegration,
    IntegrationConfig,
    IntegrationStatus,
    CalendarEvent,
    OAuthConfig,
    OAuthTokens,
    IntegrationError
)


class GoogleCalendarIntegration(CalendarIntegration):
    """
    Google Calendar integration with OAuth2 flow.

    Developer setup:
    1. Create project at console.cloud.google.com
    2. Enable Google Calendar API
    3. Create OAuth2 credentials (Web application)
    4. Set environment variables:
       GOOGLE_CLIENT_ID=your_client_id
       GOOGLE_CLIENT_SECRET=your_client_secret
    """

    @property
    def config(self) -> IntegrationConfig:
        return IntegrationConfig(
            name="google_calendar",
            display_name="Google Calendar",
            description="Sync with Google Calendar for events and scheduling",
            icon="google-calendar",
            auth_type="oauth2",
            scopes=[
                "https://www.googleapis.com/auth/calendar.readonly",
                "https://www.googleapis.com/auth/calendar.events"
            ],
            capabilities=[
                "read_events",
                "create_events",
                "update_events",
                "delete_events",
                "check_availability"
            ]
        )

    async def handle_callback(
        self,
        user_id: str,
        auth_code: str,
        redirect_uri: str
    ) -> bool:
        """Exchange authorization code for tokens."""
        if not self.oauth_config:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.oauth_config.token_url,
                    data={
                        "client_id": self.oauth_config.client_id,
                        "client_secret": self.oauth_config.client_secret,
                        "code": auth_code,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri
                    }
                )

                if response.status_code != 200:
                    print(f"Token exchange failed: {response.text}")
                    return False

                data = response.json()

                expires_at = None
                if data.get("expires_in"):
                    expires_at = datetime.utcnow() + timedelta(
                        seconds=data["expires_in"]
                    )

                tokens = OAuthTokens(
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token"),
                    token_type=data.get("token_type", "Bearer"),
                    expires_at=expires_at,
                    scope=data.get("scope", "")
                )

                return self._store_tokens(user_id, tokens)

        except Exception as e:
            print(f"Google OAuth callback error: {e}")
            return False

    async def refresh_tokens(self, user_id: str) -> bool:
        """Refresh expired OAuth tokens."""
        if not self.oauth_config:
            return False

        tokens = self._get_tokens(user_id)
        if not tokens or not tokens.refresh_token:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.oauth_config.token_url,
                    data={
                        "client_id": self.oauth_config.client_id,
                        "client_secret": self.oauth_config.client_secret,
                        "refresh_token": tokens.refresh_token,
                        "grant_type": "refresh_token"
                    }
                )

                if response.status_code != 200:
                    return False

                data = response.json()

                expires_at = None
                if data.get("expires_in"):
                    expires_at = datetime.utcnow() + timedelta(
                        seconds=data["expires_in"]
                    )

                new_tokens = OAuthTokens(
                    access_token=data["access_token"],
                    refresh_token=tokens.refresh_token,
                    token_type=data.get("token_type", "Bearer"),
                    expires_at=expires_at,
                    scope=data.get("scope", tokens.scope)
                )

                return self._store_tokens(user_id, new_tokens)

        except Exception as e:
            print(f"Google token refresh error: {e}")
            return False

    async def get_events(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
        calendar_id: str = "primary"
    ) -> List[CalendarEvent]:
        """Get calendar events from Google Calendar API."""
        if not await self.ensure_connected(user_id):
            return []

        tokens = self._get_tokens(user_id)
        if not tokens:
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                    headers={
                        "Authorization": f"Bearer {tokens.access_token}"
                    },
                    params={
                        "timeMin": start.isoformat() + "Z",
                        "timeMax": end.isoformat() + "Z",
                        "singleEvents": "true",
                        "orderBy": "startTime"
                    }
                )

                if response.status_code != 200:
                    print(f"Google Calendar API error: {response.text}")
                    return []

                data = response.json()
                events = []

                for item in data.get("items", []):
                    start_data = item.get("start", {})
                    end_data = item.get("end", {})

                    is_all_day = "date" in start_data
                    if is_all_day:
                        event_start = datetime.fromisoformat(start_data["date"])
                        event_end = datetime.fromisoformat(end_data["date"])
                    else:
                        event_start = datetime.fromisoformat(
                            start_data["dateTime"].replace("Z", "+00:00")
                        )
                        event_end = datetime.fromisoformat(
                            end_data["dateTime"].replace("Z", "+00:00")
                        )

                    events.append(CalendarEvent(
                        id=item["id"],
                        title=item.get("summary", "No title"),
                        start=event_start,
                        end=event_end,
                        location=item.get("location"),
                        description=item.get("description"),
                        attendees=[
                            a["email"] for a in item.get("attendees", [])
                        ],
                        is_all_day=is_all_day,
                        calendar_id=calendar_id,
                        source="google_calendar"
                    ))

                return events

        except Exception as e:
            print(f"Error fetching Google Calendar events: {e}")
            return []

    async def create_event(
        self,
        user_id: str,
        title: str,
        start: datetime,
        end: datetime,
        description: str = "",
        location: str = "",
        attendees: List[str] = None,
        calendar_id: str = "primary"
    ) -> Optional[str]:
        """Create a calendar event."""
        if not await self.ensure_connected(user_id):
            return None

        tokens = self._get_tokens(user_id)
        if not tokens:
            return None

        event_body = {
            "summary": title,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"}
        }

        if description:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        if attendees:
            event_body["attendees"] = [{"email": a} for a in attendees]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                    headers={
                        "Authorization": f"Bearer {tokens.access_token}",
                        "Content-Type": "application/json"
                    },
                    json=event_body
                )

                if response.status_code in (200, 201):
                    return response.json().get("id")

                print(f"Error creating event: {response.text}")
                return None

        except Exception as e:
            print(f"Error creating Google Calendar event: {e}")
            return None

    async def update_event(
        self,
        user_id: str,
        event_id: str,
        updates: Dict[str, Any],
        calendar_id: str = "primary"
    ) -> bool:
        """Update a calendar event."""
        if not await self.ensure_connected(user_id):
            return False

        tokens = self._get_tokens(user_id)
        if not tokens:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
                    headers={
                        "Authorization": f"Bearer {tokens.access_token}",
                        "Content-Type": "application/json"
                    },
                    json=updates
                )

                return response.status_code == 200

        except Exception as e:
            print(f"Error updating Google Calendar event: {e}")
            return False

    async def delete_event(
        self,
        user_id: str,
        event_id: str,
        calendar_id: str = "primary"
    ) -> bool:
        """Delete a calendar event."""
        if not await self.ensure_connected(user_id):
            return False

        tokens = self._get_tokens(user_id)
        if not tokens:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
                    headers={
                        "Authorization": f"Bearer {tokens.access_token}"
                    }
                )

                return response.status_code in (200, 204)

        except Exception as e:
            print(f"Error deleting Google Calendar event: {e}")
            return False
