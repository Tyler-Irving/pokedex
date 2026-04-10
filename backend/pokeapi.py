"""Shared PokeAPI client with in-memory caching."""

import time

import httpx
from fastapi import HTTPException

POKEAPI_BASE = "https://pokeapi.co/api/v2"

# In-memory cache: url -> (data, timestamp)
_cache: dict[str, tuple[dict, float]] = {}
CACHE_TTL = 300  # 5 minutes


async def pokeapi_get(path: str) -> dict:
    """Fetch from PokeAPI with caching."""
    url = f"{POKEAPI_BASE}/{path}"
    now = time.time()
    if url in _cache:
        data, ts = _cache[url]
        if now - ts < CACHE_TTL:
            return data
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found on PokeAPI")
        resp.raise_for_status()
        data = resp.json()
        _cache[url] = (data, now)
        return data


# Pre-fetch type index for filtering
_type_index: dict[str, list[str]] = {}  # type_name -> [pokemon_name, ...]


async def build_type_index():
    data = await pokeapi_get("type?limit=50")
    for t in data["results"]:
        type_data = await pokeapi_get(f"type/{t['name']}")
        _type_index[t["name"]] = [
            p["pokemon"]["name"] for p in type_data["pokemon"]
        ]
