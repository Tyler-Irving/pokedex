"""
Structured request-logging middleware.

Emits one JSON log line per request containing:
  - timestamp  – ISO-8601 UTC
  - request_id – UUID4 (from X-Request-ID header or auto-generated)
  - method     – HTTP verb
  - path       – URL path (with query string)
  - status     – HTTP status code
  - latency_ms – wall-clock time in milliseconds
  - client_ip  – resolved client IP (honours reverse-proxy headers)

The request_id is also echoed back in the X-Request-ID response header so
callers can correlate client-side traces with server logs.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ._client_ip import get_client_ip


# ---------------------------------------------------------------------------
# JSON log formatter
# ---------------------------------------------------------------------------

class _JsonFormatter(logging.Formatter):
    """Render each LogRecord as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Merge any extra fields attached by the caller.
        for key, value in record.__dict__.items():
            if key not in {
                "args", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "message",
                "module", "msecs", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "taskName",
                "thread", "threadName",
            }:
                payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """
    Install the JSON formatter on the root logger.

    Call once at application startup (before the first request arrives).
    Subsequent calls are idempotent.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())

    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    else:
        for h in root.handlers:
            h.setFormatter(_JsonFormatter())

    root.setLevel(level)

    # Silence noisy uvicorn access log (we replace it with our middleware).
    logging.getLogger("uvicorn.access").propagate = False


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

_logger = logging.getLogger("pokedex.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Emit a structured JSON log line for every HTTP request.

    Parameters
    ----------
    app:
        The ASGI application to wrap.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        client_ip = get_client_ip(request)
        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query}"

        start = time.perf_counter()
        response: Response = await call_next(request)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        _logger.info(
            "%s %s %d",
            request.method,
            path,
            response.status_code,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "status": response.status_code,
                "latency_ms": latency_ms,
                "client_ip": client_ip,
            },
        )

        response.headers["X-Request-ID"] = request_id
        return response
