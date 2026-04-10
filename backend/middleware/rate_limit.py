"""
Sliding-window rate limiting middleware.

Tracks request counts per client IP using an in-memory store.  Each IP gets a
fixed-size sliding window (default: 100 requests / 60 seconds).  When the limit
is exceeded the middleware short-circuits the request and returns a 429 JSON
response before the application sees the request.

Standard rate-limit headers are injected on every response:
  - X-RateLimit-Limit     – maximum requests allowed in the window
  - X-RateLimit-Remaining – requests left in the current window
  - X-RateLimit-Reset     – Unix timestamp (UTC) when the window resets
"""

import json
import time
import asyncio
from collections import defaultdict, deque
from typing import Deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter keyed by client IP address.

    Parameters
    ----------
    app:
        The ASGI application to wrap.
    requests_per_window:
        Maximum number of requests allowed within ``window_seconds``.
        Defaults to 100.
    window_seconds:
        Length of the sliding window in seconds.  Defaults to 60.
    """

    def __init__(
        self,
        app,
        requests_per_window: int = 100,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds

        # ip -> deque of request timestamps (float, seconds since epoch)
        self._store: dict[str, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client_ip(self, request: Request) -> str:
        """
        Resolve the real client IP, honouring common reverse-proxy headers.

        Priority order:
        1. X-Forwarded-For (first address in the list)
        2. X-Real-IP
        3. Direct connection IP from the ASGI scope
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        client = request.client
        return client.host if client else "unknown"

    def _evict_old_timestamps(self, timestamps: Deque[float], now: float) -> None:
        """Remove timestamps that have fallen outside the current window."""
        cutoff = now - self.window_seconds
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

    def _build_rate_limit_headers(
        self, remaining: int, reset_at: float
    ) -> dict[str, str]:
        return {
            "X-RateLimit-Limit": str(self.requests_per_window),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(int(reset_at)),
        }

    def _too_many_requests_response(self, reset_at: float) -> Response:
        body = json.dumps(
            {
                "detail": "Too Many Requests",
                "message": (
                    f"Rate limit of {self.requests_per_window} requests per "
                    f"{self.window_seconds} seconds exceeded. "
                    f"Retry after {int(reset_at - time.time())} seconds."
                ),
            }
        )
        headers = self._build_rate_limit_headers(remaining=0, reset_at=reset_at)
        headers["Retry-After"] = str(int(reset_at - time.time()))
        headers["Content-Type"] = "application/json"
        return Response(content=body, status_code=429, headers=headers)

    # ------------------------------------------------------------------
    # Middleware dispatch
    # ------------------------------------------------------------------

    async def dispatch(self, request: Request, call_next) -> Response:
        ip = self._get_client_ip(request)
        now = time.time()

        async with self._lock:
            timestamps = self._store[ip]
            self._evict_old_timestamps(timestamps, now)

            current_count = len(timestamps)

            if current_count >= self.requests_per_window:
                # The oldest timestamp in the deque marks when a slot frees up.
                reset_at = timestamps[0] + self.window_seconds
                return self._too_many_requests_response(reset_at)

            # Admit the request and record the timestamp.
            timestamps.append(now)
            remaining = self.requests_per_window - len(timestamps)
            # Reset time is when the oldest recorded request will expire.
            reset_at = timestamps[0] + self.window_seconds

        response = await call_next(request)

        # Attach rate-limit headers to every successful response.
        rl_headers = self._build_rate_limit_headers(remaining=remaining, reset_at=reset_at)
        for header_name, header_value in rl_headers.items():
            response.headers[header_name] = header_value

        return response
