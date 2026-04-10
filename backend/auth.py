import os

from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Security(_api_key_header)) -> None:
    expected = os.environ.get("POKEDEX_API_KEY")
    if expected is None:
        return
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
