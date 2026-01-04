"""
Integration Base Classes

OAuth-based integration system similar to Manus/Claude App.
Users authenticate via redirect → app stores tokens → operates on their behalf.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from enum import Enum


class IntegrationStatus(Enum):
    """Status of an integration connection."""
    NOT_CONNECTED = "not_connected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    EXPIRED = "expired"
    ERROR = "error"


class IntegrationError(Exception):
    """Base exception for integration errors."""
    pass


class AuthenticationError(IntegrationError):
    """Raised when authentication fails."""
    pass


class TokenExpiredError(IntegrationError):
    """Raised when OAuth token has expired."""
    pass


@dataclass
class OAuthConfig:
    """OAuth configuration for an integration (developer-managed)."""
    client_id: str
    client_secret: str
    auth_url: str
    token_url: str
    scopes: List[str]
    redirect_uri: str = ""


@dataclass
class IntegrationConfig:
    """Configuration for an integration."""
    name: str
    display_name: str
    description: str
    icon: str
    auth_type: str = "oauth2"  # oauth2, api_key
    scopes: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)


@dataclass
class OAuthTokens:
    """OAuth tokens stored per user per integration."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    scope: str = ""

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at


@dataclass
class CalendarEvent:
    """Represents a calendar event."""
    id: str
    title: str
    start: datetime
    end: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    attendees: List[str] = field(default_factory=list)
    is_all_day: bool = False
    calendar_id: str = "primary"
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "location": self.location,
            "description": self.description,
            "attendees": self.attendees,
            "is_all_day": self.is_all_day,
            "source": self.source
        }


@dataclass
class Email:
    """Represents an email message."""
    id: str
    subject: str
    sender: str
    recipients: List[str]
    body_preview: str
    received_at: datetime
    is_read: bool = False
    is_important: bool = False
    has_attachments: bool = False
    thread_id: Optional[str] = None
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "subject": self.subject,
            "sender": self.sender,
            "recipients": self.recipients,
            "body_preview": self.body_preview,
            "received_at": self.received_at.isoformat(),
            "is_read": self.is_read,
            "is_important": self.is_important,
            "has_attachments": self.has_attachments,
            "source": self.source
        }


@dataclass
class FreeSlot:
    """Represents a free time slot."""
    start: datetime
    end: datetime
    duration_minutes: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "duration_minutes": self.duration_minutes
        }


class BaseIntegration(ABC):
    """
    Base class for OAuth-based integrations.

    Flow:
    1. User clicks "Connect" → get_auth_url() returns OAuth URL
    2. User authenticates with provider → redirected to callback
    3. Callback exchanges code for tokens → handle_callback()
    4. Tokens stored in database → integration ready
    5. Tokens auto-refresh when expired
    """

    def __init__(self, storage, oauth_config: Optional[OAuthConfig] = None):
        self.storage = storage
        self._oauth_config = oauth_config

    @property
    @abstractmethod
    def config(self) -> IntegrationConfig:
        """Return integration configuration."""
        pass

    @property
    def oauth_config(self) -> Optional[OAuthConfig]:
        """Return OAuth configuration (developer-managed)."""
        return self._oauth_config

    def get_auth_url(self, user_id: str, redirect_uri: str, state: str = "") -> str:
        """
        Generate OAuth authorization URL for user to authenticate.

        Args:
            user_id: User requesting connection
            redirect_uri: Where to redirect after auth
            state: CSRF protection state

        Returns:
            Full OAuth URL to redirect user to
        """
        if not self.oauth_config:
            raise IntegrationError(f"{self.config.name} OAuth not configured")

        params = {
            "client_id": self.oauth_config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.oauth_config.scopes),
            "access_type": "offline",
            "prompt": "consent",
            "state": state or f"{user_id}:{self.config.name}"
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.oauth_config.auth_url}?{query}"

    @abstractmethod
    async def handle_callback(
        self,
        user_id: str,
        auth_code: str,
        redirect_uri: str
    ) -> bool:
        """
        Handle OAuth callback - exchange code for tokens and store.

        Args:
            user_id: User completing the connection
            auth_code: Authorization code from OAuth provider
            redirect_uri: Redirect URI used in auth request

        Returns:
            True if tokens obtained and stored successfully
        """
        pass

    @abstractmethod
    async def refresh_tokens(self, user_id: str) -> bool:
        """
        Refresh expired OAuth tokens.

        Args:
            user_id: User whose tokens to refresh

        Returns:
            True if refresh successful
        """
        pass

    async def disconnect(self, user_id: str) -> bool:
        """Remove integration for user."""
        if self.storage:
            return self.storage.delete_integration_credentials(
                user_id,
                self.config.name
            )
        return False

    async def get_status(self, user_id: str) -> IntegrationStatus:
        """Check connection status."""
        tokens = self._get_tokens(user_id)

        if not tokens:
            return IntegrationStatus.NOT_CONNECTED

        if tokens.is_expired:
            if await self.refresh_tokens(user_id):
                return IntegrationStatus.CONNECTED
            return IntegrationStatus.EXPIRED

        return IntegrationStatus.CONNECTED

    async def ensure_connected(self, user_id: str) -> bool:
        """Ensure integration is connected, refreshing if needed."""
        status = await self.get_status(user_id)
        return status == IntegrationStatus.CONNECTED

    def _get_tokens(self, user_id: str) -> Optional[OAuthTokens]:
        """Get stored OAuth tokens."""
        if not self.storage:
            return None

        data = self.storage.get_integration_credentials(
            user_id,
            self.config.name
        )

        if not data:
            return None

        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])

        return OAuthTokens(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=data.get("scope", "")
        )

    def _store_tokens(self, user_id: str, tokens: OAuthTokens) -> bool:
        """Store OAuth tokens."""
        if not self.storage:
            return False

        data = {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "scope": tokens.scope,
            "connected_at": datetime.utcnow().isoformat()
        }

        if tokens.expires_at:
            data["expires_at"] = tokens.expires_at.isoformat()

        return self.storage.save_integration_credentials(
            user_id,
            self.config.name,
            data
        )


class CalendarIntegration(BaseIntegration):
    """Interface for calendar integrations."""

    @abstractmethod
    async def get_events(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
        calendar_id: str = "primary"
    ) -> List[CalendarEvent]:
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def update_event(
        self,
        user_id: str,
        event_id: str,
        updates: Dict[str, Any],
        calendar_id: str = "primary"
    ) -> bool:
        pass

    @abstractmethod
    async def delete_event(
        self,
        user_id: str,
        event_id: str,
        calendar_id: str = "primary"
    ) -> bool:
        pass

    async def get_free_slots(
        self,
        user_id: str,
        target_date: date,
        duration_minutes: int = 60,
        work_hours: tuple = (9, 18)
    ) -> List[FreeSlot]:
        """Find free time slots on a given day."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        events = await self.get_events(user_id, start, end)

        events = sorted(events, key=lambda e: e.start)

        work_start = datetime.combine(
            target_date,
            datetime.min.time().replace(hour=work_hours[0])
        )
        work_end = datetime.combine(
            target_date,
            datetime.min.time().replace(hour=work_hours[1])
        )

        free_slots = []
        current = work_start

        for event in events:
            if event.is_all_day:
                continue
            if event.start > current:
                gap = int((event.start - current).total_seconds() / 60)
                if gap >= duration_minutes:
                    free_slots.append(FreeSlot(
                        start=current,
                        end=event.start,
                        duration_minutes=gap
                    ))
            current = max(current, event.end)

        if current < work_end:
            gap = int((work_end - current).total_seconds() / 60)
            if gap >= duration_minutes:
                free_slots.append(FreeSlot(
                    start=current,
                    end=work_end,
                    duration_minutes=gap
                ))

        return free_slots

    async def get_todays_events(self, user_id: str) -> List[CalendarEvent]:
        """Get today's events."""
        today = date.today()
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
        return await self.get_events(user_id, start, end)


class EmailIntegration(BaseIntegration):
    """Interface for email integrations."""

    @abstractmethod
    async def get_inbox(
        self,
        user_id: str,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[Email]:
        pass

    @abstractmethod
    async def get_email(self, user_id: str, email_id: str) -> Optional[Email]:
        pass

    @abstractmethod
    async def send_email(
        self,
        user_id: str,
        to: List[str],
        subject: str,
        body: str,
        cc: List[str] = None,
        bcc: List[str] = None,
        html_body: str = None,
        reply_to: str = None
    ) -> bool:
        pass

    @abstractmethod
    async def mark_as_read(self, user_id: str, email_id: str) -> bool:
        pass

    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread emails."""
        emails = await self.get_inbox(user_id, limit=100, unread_only=True)
        return len(emails)

    async def get_inbox_summary(self, user_id: str) -> Dict[str, Any]:
        """Get inbox summary."""
        emails = await self.get_inbox(user_id, limit=50)
        unread = [e for e in emails if not e.is_read]
        important = [e for e in emails if e.is_important]

        return {
            "total_recent": len(emails),
            "unread_count": len(unread),
            "important_count": len(important),
            "latest_unread": [e.to_dict() for e in unread[:5]]
        }


class TaskManagerIntegration(BaseIntegration):
    """Interface for task manager integrations."""

    @abstractmethod
    async def get_tasks(
        self,
        user_id: str,
        project_id: str = None,
        include_completed: bool = False
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def create_task(
        self,
        user_id: str,
        title: str,
        description: str = "",
        due_date: datetime = None,
        priority: int = None,
        project_id: str = None
    ) -> Optional[str]:
        pass

    @abstractmethod
    async def complete_task(self, user_id: str, task_id: str) -> bool:
        pass

    @abstractmethod
    async def get_projects(self, user_id: str) -> List[Dict[str, Any]]:
        pass
