"""
API Middleware Module.

Provides cross-cutting concerns for all API routes:
- Authentication & Authorization
- Request logging
- Rate limiting
- Error handling
- CORS
"""

from alfred.api.middleware.auth import (
    JWTAuthMiddleware,
    get_current_user,
    get_current_user_optional,
    require_auth,
    AuthConfig,
)
from alfred.api.middleware.logging import (
    RequestLoggingMiddleware,
    LoggingConfig,
)
from alfred.api.middleware.rate_limit import (
    RateLimitMiddleware,
    RateLimitConfig,
    rate_limit,
)
from alfred.api.middleware.error_handler import (
    ErrorHandlerMiddleware,
    AlfredAPIError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
)

__all__ = [
    # Auth
    "JWTAuthMiddleware",
    "get_current_user",
    "get_current_user_optional",
    "require_auth",
    "AuthConfig",
    # Logging
    "RequestLoggingMiddleware",
    "LoggingConfig",
    # Rate Limiting
    "RateLimitMiddleware",
    "RateLimitConfig",
    "rate_limit",
    # Error Handling
    "ErrorHandlerMiddleware",
    "AlfredAPIError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "RateLimitError",
]
