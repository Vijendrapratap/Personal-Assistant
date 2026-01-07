"""
Request Logging Middleware.

Logs incoming requests and outgoing responses with timing information.
"""

import time
import uuid
import logging
from typing import Optional, Set
from dataclasses import dataclass, field

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


logger = logging.getLogger("alfred.api")


@dataclass
class LoggingConfig:
    """Logging middleware configuration."""
    log_request_body: bool = False
    log_response_body: bool = False
    max_body_length: int = 1000
    exclude_paths: Set[str] = field(default_factory=lambda: {"/health", "/metrics"})
    exclude_headers: Set[str] = field(default_factory=lambda: {
        "authorization",
        "cookie",
        "x-api-key",
    })
    slow_request_threshold_ms: float = 1000.0


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all HTTP requests and responses.

    Features:
    - Assigns unique request ID for tracing
    - Logs request details (method, path, headers)
    - Logs response status and timing
    - Optionally logs request/response bodies
    - Identifies slow requests
    - Excludes sensitive headers
    """

    def __init__(self, app, config: Optional[LoggingConfig] = None):
        super().__init__(app)
        self.config = config or LoggingConfig()

    async def dispatch(self, request: Request, call_next):
        # Skip logging for excluded paths
        if request.url.path in self.config.exclude_paths:
            return await call_next(request)

        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Start timing
        start_time = time.perf_counter()

        # Log request
        await self._log_request(request, request_id)

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[{request_id}] EXCEPTION {request.method} {request.url.path} "
                f"- {type(e).__name__}: {str(e)} ({duration_ms:.2f}ms)"
            )
            raise

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log response
        self._log_response(request, response, request_id, duration_ms)

        # Add request ID to response headers for tracing
        response.headers["X-Request-ID"] = request_id

        return response

    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Get user ID if authenticated
        user_id = getattr(request.state, "user_id", None)
        user_info = f" user={user_id}" if user_id else ""

        # Build log message
        log_msg = (
            f"[{request_id}] --> {request.method} {request.url.path}"
            f"{user_info} from={client_ip}"
        )

        # Add query params if present
        if request.query_params:
            log_msg += f" params={dict(request.query_params)}"

        logger.info(log_msg)

        # Log request body if configured
        if self.config.log_request_body and request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                if body:
                    body_str = body.decode("utf-8")
                    if len(body_str) > self.config.max_body_length:
                        body_str = body_str[:self.config.max_body_length] + "..."
                    logger.debug(f"[{request_id}] Request body: {body_str}")
            except Exception:
                pass

    def _log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        duration_ms: float,
    ):
        """Log outgoing response details."""
        # Determine log level based on status and timing
        is_slow = duration_ms > self.config.slow_request_threshold_ms
        is_error = response.status_code >= 400

        # Build log message
        log_msg = (
            f"[{request_id}] <-- {request.method} {request.url.path} "
            f"{response.status_code} ({duration_ms:.2f}ms)"
        )

        if is_slow:
            log_msg += " [SLOW]"

        # Log at appropriate level
        if is_error:
            if response.status_code >= 500:
                logger.error(log_msg)
            else:
                logger.warning(log_msg)
        elif is_slow:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    def _sanitize_headers(self, headers: dict) -> dict:
        """Remove sensitive headers from logs."""
        return {
            k: v if k.lower() not in self.config.exclude_headers else "[REDACTED]"
            for k, v in headers.items()
        }


def get_request_id(request: Request) -> str:
    """Get the request ID from request state."""
    return getattr(request.state, "request_id", "unknown")


class StructuredLogger:
    """
    Structured logging helper for consistent log format.

    Usage:
        log = StructuredLogger("alfred.service")
        log.info("User action", user_id="123", action="login")
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _format_extra(self, **kwargs) -> str:
        """Format extra fields as key=value pairs."""
        if not kwargs:
            return ""
        pairs = [f"{k}={v}" for k, v in kwargs.items() if v is not None]
        return " " + " ".join(pairs) if pairs else ""

    def debug(self, message: str, **kwargs):
        self.logger.debug(f"{message}{self._format_extra(**kwargs)}")

    def info(self, message: str, **kwargs):
        self.logger.info(f"{message}{self._format_extra(**kwargs)}")

    def warning(self, message: str, **kwargs):
        self.logger.warning(f"{message}{self._format_extra(**kwargs)}")

    def error(self, message: str, **kwargs):
        self.logger.error(f"{message}{self._format_extra(**kwargs)}")

    def exception(self, message: str, **kwargs):
        self.logger.exception(f"{message}{self._format_extra(**kwargs)}")
