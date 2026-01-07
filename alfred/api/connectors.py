"""
Connectors API Router.

Provides endpoints for managing external service integrations.
"""

import secrets
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Query, Body
from pydantic import BaseModel


logger = logging.getLogger("alfred.api.connectors")

router = APIRouter(prefix="/connectors", tags=["Connectors"])


# =========================================
# Request/Response Models
# =========================================

class ConnectorInfo(BaseModel):
    """Connector information."""
    type: str
    display_name: str
    description: str
    category: str
    capabilities: List[str]
    icon: str
    status: Optional[str] = None


class UserConnectorInfo(BaseModel):
    """User's connector status."""
    type: str
    display_name: str
    status: str
    connected_at: Optional[str] = None
    last_sync_at: Optional[str] = None
    sync_enabled: bool = True


class OAuthUrlResponse(BaseModel):
    """OAuth URL response."""
    oauth_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request."""
    code: str
    redirect_uri: str
    state: Optional[str] = None


class ConnectorSyncResponse(BaseModel):
    """Connector sync response."""
    success: bool
    connector_type: str
    details: Dict[str, Any] = {}


class ConnectorSettingsUpdate(BaseModel):
    """Settings update for a connector."""
    sync_enabled: Optional[bool] = None
    sync_interval_minutes: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None


# =========================================
# Helper Functions
# =========================================

def get_connector_manager(request: Request):
    """Get connector manager from app state."""
    from alfred.main import connector_manager
    if not connector_manager:
        raise HTTPException(status_code=503, detail="Connector manager not initialized")
    return connector_manager


def get_current_user(request: Request) -> str:
    """Get current user ID from request state."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


# =========================================
# List Available Connectors
# =========================================

@router.get("", response_model=Dict[str, Any])
async def list_available_connectors(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """
    List all available connector types.

    Returns connector metadata including capabilities and auth requirements.
    """
    from alfred.core.connectors import get_connector_registry
    from alfred.core.connectors.registry import ConnectorCatalog

    registry = get_connector_registry()

    if category:
        # Get from catalog by category
        connectors = ConnectorCatalog.get_by_category(category)
    else:
        # Get all registered connectors
        connectors = registry.list_connectors()

    return {
        "connectors": connectors,
        "categories": [
            "productivity",
            "communication",
            "development",
            "smart_home",
            "finance",
            "health",
        ],
    }


@router.get("/catalog")
async def get_connector_catalog():
    """
    Get the full connector catalog with categories.

    Returns available integrations organized by category.
    """
    from alfred.core.connectors.registry import ConnectorCatalog

    return {
        "productivity": ConnectorCatalog.PRODUCTIVITY,
        "communication": ConnectorCatalog.COMMUNICATION,
        "development": ConnectorCatalog.DEVELOPMENT,
        "smart_home": ConnectorCatalog.SMART_HOME,
    }


# =========================================
# User's Connected Services
# =========================================

@router.get("/user", response_model=Dict[str, Any])
async def list_user_connectors(request: Request):
    """
    List all connectors configured for the current user.

    Returns connection status and sync information.
    """
    user_id = get_current_user(request)
    manager = get_connector_manager(request)

    connectors = manager.get_user_connector_info(user_id)

    return {
        "user_id": user_id,
        "connectors": connectors,
        "count": len(connectors),
    }


@router.get("/user/{connector_type}")
async def get_user_connector(
    connector_type: str,
    request: Request,
):
    """Get details of a specific user connector."""
    user_id = get_current_user(request)
    manager = get_connector_manager(request)

    connector = manager.get_connector(user_id, connector_type)
    if not connector:
        raise HTTPException(
            status_code=404,
            detail=f"Connector {connector_type} not found for user"
        )

    return connector.get_info()


# =========================================
# OAuth Flow
# =========================================

@router.get("/{connector_type}/oauth/url", response_model=OAuthUrlResponse)
async def get_oauth_url(
    connector_type: str,
    redirect_uri: str,
    request: Request,
):
    """
    Get OAuth authorization URL for a connector.

    Use this URL to redirect the user to the service's OAuth page.
    Store the returned state parameter to verify the callback.
    """
    get_current_user(request)  # Verify authenticated
    manager = get_connector_manager(request)

    state = secrets.token_urlsafe(32)
    oauth_url = manager.get_oauth_url(connector_type, redirect_uri, state)

    if not oauth_url:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth not supported for {connector_type}"
        )

    return OAuthUrlResponse(oauth_url=oauth_url, state=state)


@router.post("/{connector_type}/oauth/callback")
async def handle_oauth_callback(
    connector_type: str,
    callback: OAuthCallbackRequest,
    request: Request,
):
    """
    Complete OAuth flow and create connector.

    Call this after the user authorizes and is redirected back with a code.
    """
    user_id = get_current_user(request)
    manager = get_connector_manager(request)

    connector = await manager.complete_oauth(
        user_id=user_id,
        connector_type=connector_type,
        code=callback.code,
        redirect_uri=callback.redirect_uri,
    )

    if not connector:
        raise HTTPException(
            status_code=400,
            detail="Failed to connect service. Please try again."
        )

    return {
        "success": True,
        "message": f"Successfully connected {connector.display_name}",
        "connector": connector.get_info(),
    }


# =========================================
# Connector Management
# =========================================

@router.post("/{connector_type}/connect")
async def connect_connector(
    connector_type: str,
    request: Request,
):
    """
    Connect/reconnect an existing connector.

    For connectors that are configured but disconnected.
    """
    user_id = get_current_user(request)
    manager = get_connector_manager(request)

    success = await manager.connect(user_id, connector_type)

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect {connector_type}"
        )

    return {"success": True, "message": f"Connected {connector_type}"}


@router.post("/{connector_type}/disconnect")
async def disconnect_connector(
    connector_type: str,
    request: Request,
):
    """Disconnect a connector (keeps configuration)."""
    user_id = get_current_user(request)
    manager = get_connector_manager(request)

    success = await manager.disconnect(user_id, connector_type)

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to disconnect {connector_type}"
        )

    return {"success": True, "message": f"Disconnected {connector_type}"}


@router.delete("/{connector_type}")
async def remove_connector(
    connector_type: str,
    request: Request,
):
    """
    Remove a connector completely.

    This disconnects and removes the connector configuration.
    """
    user_id = get_current_user(request)
    manager = get_connector_manager(request)

    success = await manager.remove_connector(user_id, connector_type)

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to remove {connector_type}"
        )

    return {"success": True, "message": f"Removed {connector_type}"}


@router.patch("/{connector_type}/settings")
async def update_connector_settings(
    connector_type: str,
    settings: ConnectorSettingsUpdate,
    request: Request,
):
    """Update connector settings."""
    user_id = get_current_user(request)
    manager = get_connector_manager(request)

    connector = manager.get_connector(user_id, connector_type)
    if not connector:
        raise HTTPException(
            status_code=404,
            detail=f"Connector {connector_type} not found"
        )

    # Update settings
    if settings.sync_enabled is not None:
        connector.config.sync_enabled = settings.sync_enabled

    if settings.sync_interval_minutes is not None:
        connector.config.sync_interval_minutes = settings.sync_interval_minutes

    if settings.settings:
        connector.config.settings.update(settings.settings)

    return {
        "success": True,
        "message": "Settings updated",
        "settings": {
            "sync_enabled": connector.config.sync_enabled,
            "sync_interval_minutes": connector.config.sync_interval_minutes,
            "settings": connector.config.settings,
        },
    }


# =========================================
# Sync Operations
# =========================================

@router.post("/{connector_type}/sync", response_model=ConnectorSyncResponse)
async def sync_connector(
    connector_type: str,
    request: Request,
):
    """
    Manually trigger a sync for a connector.

    Fetches latest data from the connected service.
    """
    user_id = get_current_user(request)
    manager = get_connector_manager(request)

    result = await manager.sync_connector(user_id, connector_type)

    return ConnectorSyncResponse(
        success=result.get("success", False),
        connector_type=connector_type,
        details=result,
    )


@router.post("/user/sync-all")
async def sync_all_connectors(request: Request):
    """Sync all connected services for the user."""
    user_id = get_current_user(request)
    manager = get_connector_manager(request)

    results = await manager.sync_all_user_connectors(user_id)

    return {
        "success": True,
        "results": results,
    }


# =========================================
# Health & Resources
# =========================================

@router.get("/{connector_type}/health")
async def check_connector_health(
    connector_type: str,
    request: Request,
):
    """Check health status of a connector."""
    user_id = get_current_user(request)
    manager = get_connector_manager(request)

    connector = manager.get_connector(user_id, connector_type)
    if not connector:
        raise HTTPException(
            status_code=404,
            detail=f"Connector {connector_type} not found"
        )

    health = await connector.health_check()

    return {
        "connector_type": connector_type,
        "health": health,
    }


@router.get("/{connector_type}/resources")
async def list_connector_resources(
    connector_type: str,
    request: Request,
):
    """
    List resources available from a connector.

    Resources are items like calendars, repositories, channels, etc.
    """
    user_id = get_current_user(request)
    manager = get_connector_manager(request)

    connector = manager.get_connector(user_id, connector_type)
    if not connector:
        raise HTTPException(
            status_code=404,
            detail=f"Connector {connector_type} not found"
        )

    if not connector.is_connected:
        raise HTTPException(
            status_code=400,
            detail=f"Connector {connector_type} is not connected"
        )

    resources = await connector.get_resources()

    return {
        "connector_type": connector_type,
        "resources": resources,
        "count": len(resources),
    }


# =========================================
# Webhooks
# =========================================

@router.post("/{connector_type}/webhook")
async def handle_webhook(
    connector_type: str,
    request: Request,
):
    """
    Handle incoming webhook from a connected service.

    This endpoint receives events from external services.
    """
    manager = get_connector_manager(request)

    # Get raw payload
    payload = await request.json()

    # Route to connector manager
    result = await manager.handle_webhook(connector_type, payload)

    return result
