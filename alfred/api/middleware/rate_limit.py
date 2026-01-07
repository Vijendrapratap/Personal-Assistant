"""
Rate Limiting Middleware.

Implements token bucket rate limiting for API protection.
"""

import time
import asyncio
from typing import Optional, Dict, Callable
from dataclasses import dataclass, field
from functools import wraps
from collections import defaultdict

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    # Default limits
    requests_per_minute: int = 60
    requests_per_hour: int = 1000

    # Burst allowance
    burst_size: int = 10

    # Per-endpoint limits (path -> requests per minute)
    endpoint_limits: Dict[str, int] = field(default_factory=lambda: {
        "/chat": 30,
        "/voice/transcribe": 20,
        "/auth/login": 10,
        "/auth/signup": 5,
    })

    # Paths exempt from rate limiting
    exempt_paths: set = field(default_factory=lambda: {
        "/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    })

    # Enable per-user rate limiting (vs per-IP)
    per_user: bool = True

    # Redis backend (if None, uses in-memory)
    redis_url: Optional[str] = None


class TokenBucket:
    """
    Token bucket rate limiter implementation.

    Allows bursts while maintaining average rate.
    """

    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: Tokens per second
            capacity: Maximum tokens (burst size)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Returns True if tokens were available, False if rate limited.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update

            # Add tokens based on elapsed time
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    @property
    def available_tokens(self) -> float:
        """Get currently available tokens."""
        now = time.monotonic()
        elapsed = now - self.last_update
        return min(self.capacity, self.tokens + elapsed * self.rate)


class InMemoryRateLimiter:
    """
    In-memory rate limiter using token buckets.

    For production, use Redis-backed implementation.
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._buckets: Dict[str, TokenBucket] = {}
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.monotonic()

    def _get_bucket(self, key: str, rate: float, capacity: int) -> TokenBucket:
        """Get or create a token bucket for a key."""
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(rate, capacity)

        # Periodic cleanup of stale buckets
        self._maybe_cleanup()

        return self._buckets[key]

    def _maybe_cleanup(self):
        """Clean up stale buckets periodically."""
        now = time.monotonic()
        if now - self._last_cleanup > self._cleanup_interval:
            self._last_cleanup = now
            # Remove buckets that are at full capacity (inactive)
            stale_keys = [
                k for k, v in self._buckets.items()
                if v.available_tokens >= v.capacity
            ]
            for key in stale_keys[:100]:  # Limit cleanup per cycle
                del self._buckets[key]

    async def check_rate_limit(
        self,
        identifier: str,
        path: str,
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limits.

        Returns:
            (allowed, headers) - allowed is True if request should proceed
            headers contains rate limit info
        """
        # Get limit for this path
        limit = self.config.endpoint_limits.get(
            path,
            self.config.requests_per_minute
        )

        # Convert to rate per second
        rate = limit / 60.0
        capacity = min(limit, self.config.burst_size + limit // 2)

        # Get bucket for this identifier + path combo
        bucket_key = f"{identifier}:{path}"
        bucket = self._get_bucket(bucket_key, rate, capacity)

        # Try to consume a token
        allowed = await bucket.consume()

        # Build rate limit headers
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(int(bucket.available_tokens)),
            "X-RateLimit-Reset": str(int(time.time() + 60)),
        }

        if not allowed:
            headers["Retry-After"] = str(int(60 / rate))

        return allowed, headers


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.

    Features:
    - Per-user or per-IP rate limiting
    - Per-endpoint custom limits
    - Token bucket algorithm for burst handling
    - Standard rate limit headers
    """

    def __init__(self, app, config: Optional[RateLimitConfig] = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.limiter = InMemoryRateLimiter(self.config)

    async def dispatch(self, request: Request, call_next):
        # Skip exempt paths
        if request.url.path in self.config.exempt_paths:
            return await call_next(request)

        # Determine identifier (user_id or IP)
        if self.config.per_user and hasattr(request.state, "user_id") and request.state.user_id:
            identifier = f"user:{request.state.user_id}"
        else:
            identifier = f"ip:{request.client.host if request.client else 'unknown'}"

        # Check rate limit
        allowed, headers = await self.limiter.check_rate_limit(
            identifier,
            request.url.path,
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": headers.get("Retry-After", "60"),
                },
                headers=headers,
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response


def rate_limit(
    requests_per_minute: int = 60,
    burst: int = 10,
    key_func: Optional[Callable[[Request], str]] = None,
):
    """
    Decorator for per-route rate limiting.

    Usage:
        @router.post("/expensive-operation")
        @rate_limit(requests_per_minute=10, burst=2)
        async def expensive_operation(request: Request):
            ...
    """
    limiter = InMemoryRateLimiter(RateLimitConfig(
        requests_per_minute=requests_per_minute,
        burst_size=burst,
    ))

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get identifier
            if key_func:
                identifier = key_func(request)
            elif hasattr(request.state, "user_id") and request.state.user_id:
                identifier = f"user:{request.state.user_id}"
            else:
                identifier = f"ip:{request.client.host if request.client else 'unknown'}"

            # Check rate limit
            allowed, headers = await limiter.check_rate_limit(
                identifier,
                request.url.path,
            )

            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers=headers,
                )

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


class SlidingWindowRateLimiter:
    """
    Alternative: Sliding window rate limiter.

    More accurate than token bucket for strict rate limits.
    """

    def __init__(self, window_seconds: int = 60, max_requests: int = 60):
        self.window = window_seconds
        self.max_requests = max_requests
        self._requests: Dict[str, list] = defaultdict(list)

    async def check(self, identifier: str) -> tuple[bool, int]:
        """
        Check if request is allowed.

        Returns (allowed, remaining).
        """
        now = time.time()
        window_start = now - self.window

        # Get requests in current window
        requests = self._requests[identifier]

        # Remove old requests
        requests = [t for t in requests if t > window_start]
        self._requests[identifier] = requests

        # Check limit
        remaining = self.max_requests - len(requests)

        if remaining > 0:
            requests.append(now)
            return True, remaining - 1

        return False, 0
