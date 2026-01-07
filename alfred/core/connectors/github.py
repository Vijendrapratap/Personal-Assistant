"""
GitHub Connector.

Integrates with GitHub API for repository and issue management.
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
    AuthenticationError,
    MCPResource,
)
from alfred.core.connectors.registry import register_connector


logger = logging.getLogger("alfred.connectors.github")


@register_connector
class GitHubConnector(BaseConnector):
    """
    GitHub connector.

    Capabilities:
    - List repositories and issues
    - Create and manage issues/PRs
    - Access notifications
    - Subscribe to webhooks
    """

    connector_type = "github"
    display_name = "GitHub"
    description = "Connect your GitHub repositories for issue and PR management"
    category = ConnectorCategory.DEVELOPMENT
    capabilities = [
        ConnectorCapability.READ,
        ConnectorCapability.LIST,
        ConnectorCapability.CREATE,
        ConnectorCapability.UPDATE,
        ConnectorCapability.SEARCH,
        ConnectorCapability.WEBHOOK,
        ConnectorCapability.OAUTH,
    ]
    required_scopes = [
        "repo",
        "notifications",
        "read:user",
    ]
    icon = "github"

    # OAuth config
    OAUTH_AUTH_URL = "https://github.com/login/oauth/authorize"
    OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
    API_BASE_URL = "https://api.github.com"

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client_id = os.getenv("GITHUB_CLIENT_ID", "")
        self._client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")
        self._user_info: Optional[Dict] = None

    async def connect(self) -> bool:
        """Connect to GitHub API."""
        self._set_status(ConnectorStatus.CONNECTING)

        if not self.config.auth or not self.config.auth.token:
            self._set_status(ConnectorStatus.ERROR, "No authentication token")
            return False

        try:
            # Verify connection by fetching user info
            user = await self._api_request("GET", "/user")
            if user:
                self._user_info = user
                self._set_status(ConnectorStatus.CONNECTED)
                logger.info(
                    f"Connected to GitHub as {user.get('login')} "
                    f"for user {self.user_id}"
                )
                return True
        except Exception as e:
            self._set_status(ConnectorStatus.ERROR, str(e))
            logger.error(f"Failed to connect to GitHub: {e}")

        return False

    async def disconnect(self) -> bool:
        """Disconnect from GitHub."""
        self._set_status(ConnectorStatus.DISCONNECTED)
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
            rate_limit = await self._api_request("GET", "/rate_limit")
            return {
                "healthy": True,
                "status": "connected",
                "github_user": self._user_info.get("login") if self._user_info else None,
                "rate_limit": {
                    "limit": rate_limit["rate"]["limit"],
                    "remaining": rate_limit["rate"]["remaining"],
                    "reset": rate_limit["rate"]["reset"],
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
            }

    async def get_resources(self) -> List[Dict[str, Any]]:
        """List available GitHub resources (repos)."""
        if not self.is_connected:
            return []

        resources = []

        # Get user's repositories
        repos = await self._api_request(
            "GET",
            "/user/repos",
            params={"per_page": "100", "sort": "updated"},
        )

        for repo in repos:
            resources.append(
                MCPResource(
                    uri=f"github://repos/{repo['full_name']}",
                    name=repo["full_name"],
                    description=repo.get("description", ""),
                    mime_type="application/json",
                    metadata={
                        "repo_id": repo["id"],
                        "private": repo["private"],
                        "language": repo.get("language"),
                        "stars": repo["stargazers_count"],
                        "open_issues": repo["open_issues_count"],
                    },
                ).to_dict()
            )

        return resources

    async def sync(self) -> Dict[str, Any]:
        """Sync GitHub data (notifications, assigned issues)."""
        if not self.is_connected:
            return {"synced": False, "error": "Not connected"}

        try:
            # Get notifications
            notifications = await self._api_request(
                "GET",
                "/notifications",
                params={"all": "false"},
            )

            # Get assigned issues
            issues = await self._api_request(
                "GET",
                "/issues",
                params={"filter": "assigned", "state": "open"},
            )

            # Get assigned PRs
            prs = await self._api_request(
                "GET",
                "/issues",
                params={"filter": "assigned", "state": "open", "pulls": "true"},
            )

            return {
                "synced": True,
                "notifications": len(notifications),
                "assigned_issues": len(issues),
                "assigned_prs": len(prs),
            }

        except Exception as e:
            logger.error(f"GitHub sync failed: {e}")
            return {"synced": False, "error": str(e)}

    def get_oauth_url(self, redirect_uri: str, state: str) -> Optional[str]:
        """Generate OAuth authorization URL."""
        if not self._client_id:
            return None

        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.required_scopes),
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
                    headers={"Accept": "application/json"},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "access_token" in data:
                            return ConnectorAuth(
                                auth_type="oauth2",
                                token=data["access_token"],
                                scopes=data.get("scope", "").split(","),
                            )
                    logger.error(f"OAuth exchange failed: {await response.text()}")
                    return None
        except Exception as e:
            logger.error(f"OAuth exchange error: {e}")
            return None

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process GitHub webhook events."""
        event_type = payload.get("action")
        repo = payload.get("repository", {}).get("full_name")

        logger.info(f"GitHub webhook: {event_type} on {repo}")

        # Handle specific events
        if "issue" in payload:
            return await self._handle_issue_event(payload)
        elif "pull_request" in payload:
            return await self._handle_pr_event(payload)
        elif "push" in payload:
            return await self._handle_push_event(payload)

        return {"handled": True, "event": event_type}

    # GitHub-specific methods

    async def list_repos(
        self,
        visibility: str = "all",
        sort: str = "updated",
    ) -> List[Dict[str, Any]]:
        """List user's repositories."""
        if not self.is_connected:
            return []

        return await self._api_request(
            "GET",
            "/user/repos",
            params={
                "visibility": visibility,
                "sort": sort,
                "per_page": "100",
            },
        )

    async def get_repo(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get repository details."""
        if not self.is_connected:
            return None

        return await self._api_request("GET", f"/repos/{owner}/{repo}")

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """List issues for a repository."""
        if not self.is_connected:
            return []

        params = {"state": state, "per_page": "100"}
        if labels:
            params["labels"] = ",".join(labels)

        return await self._api_request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            params=params,
        )

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a new issue."""
        if not self.is_connected:
            return None

        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees

        return await self._api_request(
            "POST",
            f"/repos/{owner}/{repo}/issues",
            json=data,
        )

    async def update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update an issue."""
        if not self.is_connected:
            return None

        return await self._api_request(
            "PATCH",
            f"/repos/{owner}/{repo}/issues/{issue_number}",
            json=updates,
        )

    async def list_notifications(
        self,
        all_notifications: bool = False,
    ) -> List[Dict[str, Any]]:
        """List notifications."""
        if not self.is_connected:
            return []

        return await self._api_request(
            "GET",
            "/notifications",
            params={"all": str(all_notifications).lower()},
        )

    async def search_issues(
        self,
        query: str,
        sort: str = "updated",
    ) -> List[Dict[str, Any]]:
        """Search issues and PRs."""
        if not self.is_connected:
            return []

        result = await self._api_request(
            "GET",
            "/search/issues",
            params={"q": query, "sort": sort, "per_page": "50"},
        )
        return result.get("items", [])

    # Private helpers

    async def _api_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Any:
        """Make authenticated API request."""
        import aiohttp

        url = f"{self.API_BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {self.config.auth.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
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

                if response.status == 403:
                    # Check for rate limiting
                    remaining = response.headers.get("X-RateLimit-Remaining", "0")
                    if remaining == "0":
                        reset_time = response.headers.get("X-RateLimit-Reset", "0")
                        raise ConnectorError(
                            f"Rate limited until {reset_time}",
                            self.connector_type,
                            {"reset_at": reset_time},
                        )

                if response.status >= 400:
                    raise ConnectorError(
                        await response.text(),
                        self.connector_type,
                    )

                if response.status == 204:
                    return {}
                return await response.json()

    async def _handle_issue_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue webhook event."""
        action = payload.get("action")
        issue = payload.get("issue", {})

        # Could trigger notifications or sync here
        return {
            "handled": True,
            "event": "issue",
            "action": action,
            "issue_number": issue.get("number"),
        }

    async def _handle_pr_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request webhook event."""
        action = payload.get("action")
        pr = payload.get("pull_request", {})

        return {
            "handled": True,
            "event": "pull_request",
            "action": action,
            "pr_number": pr.get("number"),
        }

    async def _handle_push_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle push webhook event."""
        ref = payload.get("ref")
        commits = payload.get("commits", [])

        return {
            "handled": True,
            "event": "push",
            "ref": ref,
            "commit_count": len(commits),
        }
