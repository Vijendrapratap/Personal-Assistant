"""
Integration Manager

Central manager for all integrations with OAuth redirect flow support.
Handles discovery, OAuth flow coordination, and unified access.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from alfred.integrations.base import (
    BaseIntegration,
    CalendarIntegration,
    EmailIntegration,
    TaskManagerIntegration,
    IntegrationStatus,
    IntegrationConfig,
    OAuthConfig,
    CalendarEvent,
    Email,
    FreeSlot
)


class IntegrationManager:
    """
    Central manager for all Alfred integrations.

    Features:
    - OAuth flow coordination (redirect-based auth like Manus/Claude)
    - Unified interface across providers
    - Automatic token refresh
    - Developer-managed OAuth credentials (via environment variables)
    """

    def __init__(self, storage, base_url: str = ""):
        """
        Initialize the integration manager.

        Args:
            storage: Storage adapter for credentials
            base_url: Base URL for OAuth callbacks (e.g., https://api.alfred.app)
        """
        self.storage = storage
        self.base_url = base_url
        self.integrations: Dict[str, BaseIntegration] = {}
        self._discover_integrations()

    def _discover_integrations(self):
        """Discover and register available integrations."""
        # Google integrations
        google_oauth = self._get_google_oauth_config()
        if google_oauth:
            try:
                from alfred.integrations.google.calendar import GoogleCalendarIntegration
                self.integrations["google_calendar"] = GoogleCalendarIntegration(
                    self.storage, google_oauth
                )
            except ImportError:
                pass

            try:
                from alfred.integrations.google.gmail import GmailIntegration
                self.integrations["gmail"] = GmailIntegration(
                    self.storage, google_oauth
                )
            except ImportError:
                pass

        # Microsoft integrations
        microsoft_oauth = self._get_microsoft_oauth_config()
        if microsoft_oauth:
            try:
                from alfred.integrations.outlook.calendar import OutlookCalendarIntegration
                self.integrations["outlook_calendar"] = OutlookCalendarIntegration(
                    self.storage, microsoft_oauth
                )
            except ImportError:
                pass

            try:
                from alfred.integrations.outlook.mail import OutlookMailIntegration
                self.integrations["outlook_mail"] = OutlookMailIntegration(
                    self.storage, microsoft_oauth
                )
            except ImportError:
                pass

        # Notion
        notion_oauth = self._get_notion_oauth_config()
        if notion_oauth:
            try:
                from alfred.integrations.notion.notion import NotionIntegration
                self.integrations["notion"] = NotionIntegration(
                    self.storage, notion_oauth
                )
            except ImportError:
                pass

        # Todoist
        todoist_oauth = self._get_todoist_oauth_config()
        if todoist_oauth:
            try:
                from alfred.integrations.todoist.todoist import TodoistIntegration
                self.integrations["todoist"] = TodoistIntegration(
                    self.storage, todoist_oauth
                )
            except ImportError:
                pass

    def _get_google_oauth_config(self) -> Optional[OAuthConfig]:
        """Get Google OAuth config from environment (developer-managed)."""
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        if not client_id or not client_secret:
            return None

        return OAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=[
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send"
            ],
            redirect_uri=f"{self.base_url}/api/integrations/callback/google"
        )

    def _get_microsoft_oauth_config(self) -> Optional[OAuthConfig]:
        """Get Microsoft OAuth config from environment (developer-managed)."""
        client_id = os.getenv("MICROSOFT_CLIENT_ID")
        client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")

        if not client_id or not client_secret:
            return None

        return OAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            scopes=[
                "Calendars.ReadWrite",
                "Mail.Read",
                "Mail.Send",
                "offline_access"
            ],
            redirect_uri=f"{self.base_url}/api/integrations/callback/microsoft"
        )

    def _get_notion_oauth_config(self) -> Optional[OAuthConfig]:
        """Get Notion OAuth config from environment (developer-managed)."""
        client_id = os.getenv("NOTION_CLIENT_ID")
        client_secret = os.getenv("NOTION_CLIENT_SECRET")

        if not client_id or not client_secret:
            return None

        return OAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            auth_url="https://api.notion.com/v1/oauth/authorize",
            token_url="https://api.notion.com/v1/oauth/token",
            scopes=[],
            redirect_uri=f"{self.base_url}/api/integrations/callback/notion"
        )

    def _get_todoist_oauth_config(self) -> Optional[OAuthConfig]:
        """Get Todoist OAuth config from environment (developer-managed)."""
        client_id = os.getenv("TODOIST_CLIENT_ID")
        client_secret = os.getenv("TODOIST_CLIENT_SECRET")

        if not client_id or not client_secret:
            return None

        return OAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            auth_url="https://todoist.com/oauth/authorize",
            token_url="https://todoist.com/oauth/access_token",
            scopes=["data:read_write"],
            redirect_uri=f"{self.base_url}/api/integrations/callback/todoist"
        )

    def get_integration(self, name: str) -> Optional[BaseIntegration]:
        """Get a specific integration by name."""
        return self.integrations.get(name)

    def get_available_integrations(self) -> List[Dict[str, Any]]:
        """Get list of all available integrations with their config."""
        result = []
        for name, integration in self.integrations.items():
            config = integration.config
            result.append({
                "name": config.name,
                "display_name": config.display_name,
                "description": config.description,
                "icon": config.icon,
                "capabilities": config.capabilities,
                "auth_type": config.auth_type
            })
        return result

    async def get_user_integrations(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Get status of all integrations for a user."""
        result = {}
        for name, integration in self.integrations.items():
            try:
                status = await integration.get_status(user_id)
                result[name] = {
                    "name": name,
                    "display_name": integration.config.display_name,
                    "status": status.value,
                    "connected": status == IntegrationStatus.CONNECTED,
                    "capabilities": integration.config.capabilities
                }
            except Exception as e:
                result[name] = {
                    "name": name,
                    "display_name": integration.config.display_name,
                    "status": "error",
                    "error": str(e)
                }
        return result

    def get_auth_url(
        self,
        integration_name: str,
        user_id: str,
        redirect_uri: str = None
    ) -> Optional[str]:
        """
        Get OAuth authorization URL for a user to connect an integration.

        Args:
            integration_name: Which integration to connect
            user_id: User requesting the connection
            redirect_uri: Override default redirect URI

        Returns:
            OAuth URL to redirect user to, or None if not available
        """
        integration = self.integrations.get(integration_name)
        if not integration or not integration.oauth_config:
            return None

        uri = redirect_uri or integration.oauth_config.redirect_uri
        state = f"{user_id}:{integration_name}"
        return integration.get_auth_url(user_id, uri, state)

    async def handle_oauth_callback(
        self,
        integration_name: str,
        user_id: str,
        auth_code: str,
        redirect_uri: str = None
    ) -> bool:
        """
        Handle OAuth callback after user authorizes.

        Args:
            integration_name: Which integration completed auth
            user_id: User completing the connection
            auth_code: Authorization code from provider
            redirect_uri: Redirect URI used

        Returns:
            True if connection successful
        """
        integration = self.integrations.get(integration_name)
        if not integration:
            return False

        uri = redirect_uri or (
            integration.oauth_config.redirect_uri
            if integration.oauth_config
            else ""
        )
        return await integration.handle_callback(user_id, auth_code, uri)

    async def disconnect_integration(
        self,
        user_id: str,
        integration_name: str
    ) -> bool:
        """Disconnect an integration for a user."""
        integration = self.integrations.get(integration_name)
        if not integration:
            return False
        return await integration.disconnect(user_id)

    # =========================================
    # Unified Calendar Access
    # =========================================

    def _get_calendar_integrations(self) -> List[CalendarIntegration]:
        """Get all calendar integrations."""
        return [
            i for i in self.integrations.values()
            if isinstance(i, CalendarIntegration)
        ]

    async def get_all_events(
        self,
        user_id: str,
        start: datetime,
        end: datetime
    ) -> List[CalendarEvent]:
        """Get events from all connected calendars."""
        all_events = []

        for integration in self._get_calendar_integrations():
            try:
                if await integration.ensure_connected(user_id):
                    events = await integration.get_events(user_id, start, end)
                    for event in events:
                        event.source = integration.config.name
                    all_events.extend(events)
            except Exception as e:
                print(f"Error getting events from {integration.config.name}: {e}")

        return sorted(all_events, key=lambda e: e.start)

    async def get_todays_events(self, user_id: str) -> List[CalendarEvent]:
        """Get today's events from all calendars."""
        from datetime import date
        today = date.today()
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
        return await self.get_all_events(user_id, start, end)

    async def get_free_slots(
        self,
        user_id: str,
        target_date,
        duration_minutes: int = 60
    ) -> List[FreeSlot]:
        """Get free time slots considering all calendars."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        all_events = await self.get_all_events(user_id, start, end)

        work_start = datetime.combine(
            target_date, datetime.min.time().replace(hour=9)
        )
        work_end = datetime.combine(
            target_date, datetime.min.time().replace(hour=18)
        )

        events = sorted(all_events, key=lambda e: e.start)
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

    async def create_event(
        self,
        user_id: str,
        title: str,
        start: datetime,
        end: datetime,
        integration_name: str = None,
        **kwargs
    ) -> Optional[str]:
        """Create event on specified or first connected calendar."""
        calendar = None

        if integration_name:
            calendar = self.integrations.get(integration_name)
        else:
            for integration in self._get_calendar_integrations():
                if await integration.ensure_connected(user_id):
                    calendar = integration
                    break

        if not calendar or not isinstance(calendar, CalendarIntegration):
            return None

        return await calendar.create_event(
            user_id=user_id,
            title=title,
            start=start,
            end=end,
            **kwargs
        )

    # =========================================
    # Unified Email Access
    # =========================================

    def _get_email_integrations(self) -> List[EmailIntegration]:
        """Get all email integrations."""
        return [
            i for i in self.integrations.values()
            if isinstance(i, EmailIntegration)
        ]

    async def get_all_emails(
        self,
        user_id: str,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[Email]:
        """Get emails from all connected email services."""
        all_emails = []

        for integration in self._get_email_integrations():
            try:
                if await integration.ensure_connected(user_id):
                    emails = await integration.get_inbox(
                        user_id, limit, unread_only
                    )
                    for email in emails:
                        email.source = integration.config.name
                    all_emails.extend(emails)
            except Exception as e:
                print(f"Error getting emails from {integration.config.name}: {e}")

        return sorted(all_emails, key=lambda e: e.received_at, reverse=True)

    async def get_inbox_summary(self, user_id: str) -> Dict[str, Any]:
        """Get combined inbox summary."""
        all_emails = await self.get_all_emails(user_id, limit=50)
        unread = [e for e in all_emails if not e.is_read]
        important = [e for e in all_emails if e.is_important]

        return {
            "total_recent": len(all_emails),
            "unread_count": len(unread),
            "important_count": len(important),
            "sources": list(set(e.source for e in all_emails)),
            "latest_unread": [e.to_dict() for e in unread[:5]]
        }

    async def send_email(
        self,
        user_id: str,
        to: List[str],
        subject: str,
        body: str,
        integration_name: str = None,
        **kwargs
    ) -> bool:
        """Send email using specified or first connected service."""
        email_service = None

        if integration_name:
            email_service = self.integrations.get(integration_name)
        else:
            for integration in self._get_email_integrations():
                if await integration.ensure_connected(user_id):
                    email_service = integration
                    break

        if not email_service or not isinstance(email_service, EmailIntegration):
            return False

        return await email_service.send_email(
            user_id=user_id,
            to=to,
            subject=subject,
            body=body,
            **kwargs
        )

    # =========================================
    # Health Check
    # =========================================

    async def health_check(self, user_id: str = None) -> Dict[str, Any]:
        """Check health of all integrations."""
        health = {
            "total_integrations": len(self.integrations),
            "available_integrations": list(self.integrations.keys()),
            "integration_status": {}
        }

        if user_id:
            for name, integration in self.integrations.items():
                try:
                    status = await integration.get_status(user_id)
                    health["integration_status"][name] = status.value
                except Exception as e:
                    health["integration_status"][name] = f"error: {str(e)}"

        return health
