"""Shared helper for resolving the client IP from a request.

Honours reverse-proxy headers (X-Forwarded-For, X-Real-IP) and falls back
to the direct ASGI connection IP.
"""

from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """Resolve the real client IP, honouring common reverse-proxy headers.

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
