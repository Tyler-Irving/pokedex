"""Middleware that adds Cache-Control and ETag headers to GET responses."""

import hashlib

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..pokeapi import CACHE_TTL


class CacheHeaderMiddleware(BaseHTTPMiddleware):
    """Attach Cache-Control and ETag headers to successful GET responses.

    Also handles conditional requests: if the client sends If-None-Match
    and the ETag matches, respond with 304 Not Modified.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        if request.method != "GET" or response.status_code != 200:
            return response

        # Mutable resources must not be browser-cached
        if request.url.path.startswith("/api/teams") or request.url.path.startswith("/api/favorites"):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        etag = f'"{hashlib.sha256(body).hexdigest()[:32]}"'

        if request.headers.get("if-none-match") == etag:
            return Response(
                status_code=304,
                headers={"ETag": etag, "Cache-Control": f"public, max-age={CACHE_TTL}"},
            )

        headers = dict(response.headers)
        headers["Cache-Control"] = f"public, max-age={CACHE_TTL}"
        headers["ETag"] = etag

        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )
