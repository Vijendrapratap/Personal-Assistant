"""
Error Handler Middleware.

Provides consistent error responses and exception handling.
"""

import logging
import traceback
from typing import Optional, Dict, Any

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError as PydanticValidationError


logger = logging.getLogger("alfred.api.errors")


class AlfredAPIError(Exception):
    """Base class for Alfred API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self._default_error_code()
        self.details = details or {}
        super().__init__(message)

    def _default_error_code(self) -> str:
        """Generate default error code from class name."""
        name = self.__class__.__name__
        # Convert CamelCase to UPPER_SNAKE_CASE
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).upper().replace("_ERROR", "")

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            }
        }


class ValidationError(AlfredAPIError):
    """Validation error for invalid input."""

    def __init__(
        self,
        message: str = "Validation error",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class AuthenticationError(AlfredAPIError):
    """Authentication failure."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_REQUIRED",
        )


class AuthorizationError(AlfredAPIError):
    """Authorization failure (authenticated but not permitted)."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="PERMISSION_DENIED",
        )


class NotFoundError(AlfredAPIError):
    """Resource not found."""

    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[str] = None,
    ):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} '{resource_id}' not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id} if resource_id else {},
        )


class RateLimitError(AlfredAPIError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
        )


class ConflictError(AlfredAPIError):
    """Resource conflict (e.g., duplicate)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
        )


class ServiceUnavailableError(AlfredAPIError):
    """External service unavailable."""

    def __init__(self, service: str = "Service"):
        super().__init__(
            message=f"{service} is temporarily unavailable",
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service},
        )


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware.

    Catches all exceptions and returns consistent JSON error responses.

    Features:
    - Consistent error response format
    - Detailed logging for debugging
    - No sensitive info leak in production
    - Request ID in error responses
    """

    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.debug = debug

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except AlfredAPIError as e:
            # Custom API errors
            return self._create_error_response(request, e)

        except HTTPException as e:
            # FastAPI HTTP exceptions
            return self._create_http_error_response(request, e)

        except PydanticValidationError as e:
            # Pydantic validation errors
            return self._create_validation_error_response(request, e)

        except Exception as e:
            # Unexpected errors
            return self._create_internal_error_response(request, e)

    def _create_error_response(
        self,
        request: Request,
        error: AlfredAPIError,
    ) -> JSONResponse:
        """Create response for AlfredAPIError."""
        request_id = getattr(request.state, "request_id", None)

        response_data = error.to_dict()
        if request_id:
            response_data["request_id"] = request_id

        logger.warning(
            f"API Error: {error.error_code} - {error.message}",
            extra={
                "request_id": request_id,
                "status_code": error.status_code,
                "path": request.url.path,
            }
        )

        return JSONResponse(
            status_code=error.status_code,
            content=response_data,
        )

    def _create_http_error_response(
        self,
        request: Request,
        error: HTTPException,
    ) -> JSONResponse:
        """Create response for FastAPI HTTPException."""
        request_id = getattr(request.state, "request_id", None)

        response_data = {
            "error": {
                "code": f"HTTP_{error.status_code}",
                "message": error.detail,
            }
        }
        if request_id:
            response_data["request_id"] = request_id

        return JSONResponse(
            status_code=error.status_code,
            content=response_data,
            headers=getattr(error, "headers", None),
        )

    def _create_validation_error_response(
        self,
        request: Request,
        error: PydanticValidationError,
    ) -> JSONResponse:
        """Create response for Pydantic ValidationError."""
        request_id = getattr(request.state, "request_id", None)

        # Extract validation errors
        errors = []
        for err in error.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"],
            })

        response_data = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": errors},
            }
        }
        if request_id:
            response_data["request_id"] = request_id

        return JSONResponse(
            status_code=422,
            content=response_data,
        )

    def _create_internal_error_response(
        self,
        request: Request,
        error: Exception,
    ) -> JSONResponse:
        """Create response for unexpected errors."""
        request_id = getattr(request.state, "request_id", None)

        # Log full error with traceback
        logger.error(
            f"Unhandled exception: {type(error).__name__}: {str(error)}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
            },
            exc_info=True,
        )

        # Build response
        response_data = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        }

        if request_id:
            response_data["request_id"] = request_id

        # Include debug info only in debug mode
        if self.debug:
            response_data["error"]["debug"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc().split("\n"),
            }

        return JSONResponse(
            status_code=500,
            content=response_data,
        )


def handle_exceptions(func):
    """
    Decorator to handle exceptions in route handlers.

    Provides consistent error handling at the route level.
    """
    from functools import wraps

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AlfredAPIError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Unhandled error in {func.__name__}")
            raise AlfredAPIError(
                message="An unexpected error occurred",
                status_code=500,
                details={"original_error": str(e)},
            )
    return wrapper
