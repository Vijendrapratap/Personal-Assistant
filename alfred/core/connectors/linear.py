"""
Linear Connector.

Integrates with Linear for issue and project tracking.
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


logger = logging.getLogger("alfred.connectors.linear")


@register_connector
class LinearConnector(BaseConnector):
    """
    Linear connector for issue tracking.

    Capabilities:
    - List issues, projects, and cycles
    - Create and update issues
    - Search issues
    - Receive webhooks for updates
    """

    connector_type = "linear"
    display_name = "Linear"
    description = "Connect your Linear workspace for issue tracking"
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
        "read",
        "write",
        "issues:create",
    ]
    icon = "target"

    # OAuth config
    OAUTH_AUTH_URL = "https://linear.app/oauth/authorize"
    OAUTH_TOKEN_URL = "https://api.linear.app/oauth/token"
    API_BASE_URL = "https://api.linear.app/graphql"

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client_id = os.getenv("LINEAR_CLIENT_ID", "")
        self._client_secret = os.getenv("LINEAR_CLIENT_SECRET", "")
        self._user_info: Optional[Dict] = None
        self._organization: Optional[Dict] = None

    async def connect(self) -> bool:
        """Connect to Linear API."""
        self._set_status(ConnectorStatus.CONNECTING)

        if not self.config.auth or not self.config.auth.token:
            self._set_status(ConnectorStatus.ERROR, "No authentication token")
            return False

        try:
            # Verify connection by getting viewer info
            query = """
                query {
                    viewer {
                        id
                        name
                        email
                    }
                    organization {
                        id
                        name
                        urlKey
                    }
                }
            """
            result = await self._graphql(query)

            if result and "viewer" in result:
                self._user_info = result["viewer"]
                self._organization = result.get("organization")
                self._set_status(ConnectorStatus.CONNECTED)
                logger.info(
                    f"Connected to Linear org {self._organization.get('name')} "
                    f"for user {self.user_id}"
                )
                return True
            else:
                self._set_status(ConnectorStatus.ERROR, "Failed to get user info")
                return False

        except Exception as e:
            self._set_status(ConnectorStatus.ERROR, str(e))
            logger.error(f"Failed to connect to Linear: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Linear."""
        self._set_status(ConnectorStatus.DISCONNECTED)
        self._user_info = None
        self._organization = None
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
            query = "query { viewer { id } }"
            result = await self._graphql(query)
            return {
                "healthy": "viewer" in result,
                "status": "connected",
                "user": self._user_info,
                "organization": self._organization,
            }
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
            }

    async def get_resources(self) -> List[Dict[str, Any]]:
        """List available Linear resources (teams, projects)."""
        if not self.is_connected:
            return []

        resources = []

        # Get teams
        teams = await self.list_teams()
        for team in teams:
            resources.append(
                MCPResource(
                    uri=f"linear://teams/{team['id']}",
                    name=team.get("name", "Unknown Team"),
                    description=team.get("description", ""),
                    mime_type="application/json",
                    metadata={
                        "team_id": team["id"],
                        "key": team.get("key"),
                        "type": "team",
                    },
                ).to_dict()
            )

        # Get projects
        projects = await self.list_projects()
        for project in projects:
            resources.append(
                MCPResource(
                    uri=f"linear://projects/{project['id']}",
                    name=project.get("name", "Unknown Project"),
                    description=project.get("description", ""),
                    mime_type="application/json",
                    metadata={
                        "project_id": project["id"],
                        "state": project.get("state"),
                        "type": "project",
                    },
                ).to_dict()
            )

        return resources

    async def sync(self) -> Dict[str, Any]:
        """Sync Linear data (assigned issues, updates)."""
        if not self.is_connected:
            return {"synced": False, "error": "Not connected"}

        try:
            # Get assigned issues
            issues = await self.get_my_issues()

            # Get recent activity
            # (Linear doesn't have a direct activity endpoint, use issues)

            return {
                "synced": True,
                "assigned_issues": len(issues),
            }

        except Exception as e:
            logger.error(f"Linear sync failed: {e}")
            return {"synced": False, "error": str(e)}

    def get_oauth_url(self, redirect_uri: str, state: str) -> Optional[str]:
        """Generate OAuth authorization URL."""
        if not self._client_id:
            return None

        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
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
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                ) as response:
                    data = await response.json()
                    if "access_token" in data:
                        return ConnectorAuth(
                            auth_type="oauth2",
                            token=data["access_token"],
                            scopes=data.get("scope", "").split(","),
                        )
                    logger.error(f"OAuth exchange failed: {data}")
                    return None
        except Exception as e:
            logger.error(f"OAuth exchange error: {e}")
            return None

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Linear webhook events."""
        action = payload.get("action")
        event_type = payload.get("type")
        data = payload.get("data", {})

        logger.info(f"Linear webhook: {event_type} - {action}")

        if event_type == "Issue":
            return await self._handle_issue_webhook(action, data)
        elif event_type == "Comment":
            return await self._handle_comment_webhook(action, data)

        return {"handled": True, "event": event_type, "action": action}

    # Linear-specific methods

    async def list_teams(self) -> List[Dict[str, Any]]:
        """List all teams."""
        if not self.is_connected:
            return []

        query = """
            query {
                teams {
                    nodes {
                        id
                        name
                        key
                        description
                    }
                }
            }
        """
        result = await self._graphql(query)
        return result.get("teams", {}).get("nodes", [])

    async def list_projects(
        self, team_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List projects, optionally filtered by team."""
        if not self.is_connected:
            return []

        if team_id:
            query = """
                query($teamId: String!) {
                    team(id: $teamId) {
                        projects {
                            nodes {
                                id
                                name
                                description
                                state
                                progress
                            }
                        }
                    }
                }
            """
            result = await self._graphql(query, {"teamId": team_id})
            return result.get("team", {}).get("projects", {}).get("nodes", [])
        else:
            query = """
                query {
                    projects {
                        nodes {
                            id
                            name
                            description
                            state
                            progress
                        }
                    }
                }
            """
            result = await self._graphql(query)
            return result.get("projects", {}).get("nodes", [])

    async def get_my_issues(
        self,
        include_completed: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get issues assigned to the current user."""
        if not self.is_connected:
            return []

        filter_clause = ""
        if not include_completed:
            filter_clause = ', filter: { state: { type: { nin: ["completed", "canceled"] } } }'

        query = f"""
            query {{
                viewer {{
                    assignedIssues(first: 50{filter_clause}) {{
                        nodes {{
                            id
                            identifier
                            title
                            description
                            priority
                            state {{
                                name
                                type
                            }}
                            dueDate
                            project {{
                                id
                                name
                            }}
                            labels {{
                                nodes {{
                                    name
                                    color
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        """
        result = await self._graphql(query)
        return result.get("viewer", {}).get("assignedIssues", {}).get("nodes", [])

    async def get_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Get an issue by ID."""
        if not self.is_connected:
            return None

        query = """
            query($id: String!) {
                issue(id: $id) {
                    id
                    identifier
                    title
                    description
                    priority
                    state {
                        name
                        type
                    }
                    dueDate
                    assignee {
                        id
                        name
                    }
                    project {
                        id
                        name
                    }
                    labels {
                        nodes {
                            name
                            color
                        }
                    }
                    comments {
                        nodes {
                            body
                            createdAt
                            user {
                                name
                            }
                        }
                    }
                }
            }
        """
        result = await self._graphql(query, {"id": issue_id})
        return result.get("issue")

    async def create_issue(
        self,
        team_id: str,
        title: str,
        description: str = "",
        priority: int = 0,  # 0 = No priority, 1 = Urgent, 2 = High, 3 = Normal, 4 = Low
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a new issue."""
        if not self.is_connected:
            return None

        mutation = """
            mutation($input: IssueCreateInput!) {
                issueCreate(input: $input) {
                    success
                    issue {
                        id
                        identifier
                        title
                        url
                    }
                }
            }
        """

        input_data = {
            "teamId": team_id,
            "title": title,
            "description": description,
            "priority": priority,
        }

        if project_id:
            input_data["projectId"] = project_id
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if label_ids:
            input_data["labelIds"] = label_ids

        result = await self._graphql(mutation, {"input": input_data})
        create_result = result.get("issueCreate", {})

        if create_result.get("success"):
            return create_result.get("issue")
        return None

    async def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        state_id: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an issue."""
        if not self.is_connected:
            return None

        mutation = """
            mutation($id: String!, $input: IssueUpdateInput!) {
                issueUpdate(id: $id, input: $input) {
                    success
                    issue {
                        id
                        identifier
                        title
                    }
                }
            }
        """

        input_data = {}
        if title:
            input_data["title"] = title
        if description is not None:
            input_data["description"] = description
        if state_id:
            input_data["stateId"] = state_id
        if priority is not None:
            input_data["priority"] = priority

        if not input_data:
            return None

        result = await self._graphql(mutation, {"id": issue_id, "input": input_data})
        update_result = result.get("issueUpdate", {})

        if update_result.get("success"):
            return update_result.get("issue")
        return None

    async def search_issues(
        self,
        query: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search for issues."""
        if not self.is_connected:
            return []

        gql_query = """
            query($query: String!, $first: Int!) {
                issueSearch(query: $query, first: $first) {
                    nodes {
                        id
                        identifier
                        title
                        description
                        state {
                            name
                        }
                        priority
                    }
                }
            }
        """
        result = await self._graphql(gql_query, {"query": query, "first": limit})
        return result.get("issueSearch", {}).get("nodes", [])

    async def add_comment(
        self,
        issue_id: str,
        body: str,
    ) -> Optional[Dict[str, Any]]:
        """Add a comment to an issue."""
        if not self.is_connected:
            return None

        mutation = """
            mutation($input: CommentCreateInput!) {
                commentCreate(input: $input) {
                    success
                    comment {
                        id
                        body
                    }
                }
            }
        """

        result = await self._graphql(
            mutation,
            {"input": {"issueId": issue_id, "body": body}},
        )
        create_result = result.get("commentCreate", {})

        if create_result.get("success"):
            return create_result.get("comment")
        return None

    # Private helpers

    async def _graphql(
        self,
        query: str,
        variables: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL query."""
        import aiohttp

        headers = {
            "Authorization": self.config.auth.token,
            "Content-Type": "application/json",
        }

        body = {"query": query}
        if variables:
            body["variables"] = variables

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.API_BASE_URL,
                headers=headers,
                json=body,
            ) as response:
                if response.status == 401:
                    raise AuthenticationError(
                        "Authentication failed",
                        self.connector_type,
                    )

                result = await response.json()

                if "errors" in result:
                    errors = result["errors"]
                    raise ConnectorError(
                        errors[0].get("message", "GraphQL error"),
                        self.connector_type,
                        {"errors": errors},
                    )

                return result.get("data", {})

    async def _handle_issue_webhook(
        self,
        action: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle issue webhook event."""
        return {
            "handled": True,
            "event": "issue",
            "action": action,
            "issue_id": data.get("id"),
            "title": data.get("title"),
        }

    async def _handle_comment_webhook(
        self,
        action: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle comment webhook event."""
        return {
            "handled": True,
            "event": "comment",
            "action": action,
            "comment_id": data.get("id"),
        }
