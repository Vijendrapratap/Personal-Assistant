"""
Authentication Middleware.

Handles JWT token validation and user authentication.
"""

import os
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps

import jwt
from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass
class AuthConfig:
    """Authentication configuration."""
    secret_key: str = os.getenv("SECRET_KEY", "supersecretkey")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    public_paths: tuple = (
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/auth/login",
        "/auth/signup",
        "/auth/refresh",
    )


# Security scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates JWT tokens and adds user context to requests.

    This middleware:
    1. Extracts JWT token from Authorization header
    2. Validates token signature and expiration
    3. Adds user_id to request state for downstream handlers
    4. Allows public paths to bypass authentication
    """

    def __init__(self, app, config: Optional[AuthConfig] = None):
        super().__init__(app)
        self.config = config or AuthConfig()

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Extract token
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # Let the route decide if auth is required
            request.state.user_id = None
            return await call_next(request)

        try:
            # Parse Bearer token
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                request.state.user_id = None
                return await call_next(request)

            # Validate token
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm]
            )

            # Add user context to request
            request.state.user_id = payload.get("user_id")
            request.state.email = payload.get("sub")
            request.state.token_exp = payload.get("exp")

        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token has expired"}
            )
        except jwt.InvalidTokenError:
            request.state.user_id = None
        except ValueError:
            request.state.user_id = None

        return await call_next(request)

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required)."""
        return any(path.startswith(p) for p in self.config.public_paths)


def create_access_token(
    data: dict,
    config: Optional[AuthConfig] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a new JWT access token."""
    config = config or AuthConfig()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.access_token_expire_minutes)

    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)


def create_refresh_token(
    data: dict,
    config: Optional[AuthConfig] = None,
) -> str:
    """Create a new JWT refresh token."""
    config = config or AuthConfig()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=config.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)


def decode_token(token: str, config: Optional[AuthConfig] = None) -> dict:
    """Decode and validate a JWT token."""
    config = config or AuthConfig()
    return jwt.decode(token, config.secret_key, algorithms=[config.algorithm])


async def get_current_user(request: Request) -> str:
    """
    Dependency to get the current authenticated user ID.

    Raises HTTPException if not authenticated.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def get_current_user_optional(request: Request) -> Optional[str]:
    """
    Dependency to get the current user ID if authenticated.

    Returns None if not authenticated (doesn't raise).
    """
    return getattr(request.state, "user_id", None)


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication on a route.

    Usage:
        @router.get("/protected")
        @require_auth
        async def protected_route(request: Request):
            user_id = request.state.user_id
            ...
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await func(request, *args, **kwargs)
    return wrapper


class TokenPayload:
    """Typed token payload."""

    def __init__(self, payload: dict):
        self.user_id: str = payload.get("user_id", "")
        self.email: str = payload.get("sub", "")
        self.exp: int = payload.get("exp", 0)
        self.token_type: str = payload.get("type", "access")

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow().timestamp() > self.exp
