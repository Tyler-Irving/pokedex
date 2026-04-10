"""Shared PokeAPI client with in-memory caching."""

import time
from collections import OrderedDict

import httpx
from fastapi import HTTPException

POKEAPI_BASE = "https://pokeapi.co/api/v2"

CACHE_TTL = 300  # 5 minutes
CACHE_MAX_SIZE = 500


class _LRUCache:
    """TTL-aware LRU cache backed by OrderedDict."""

    def __init__(self, max_size: int, ttl: float) -> None:
        self._store: OrderedDict[str, tuple[dict, float]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl

    def get(self, key: str) -> dict | None:
        if key not in self._store:
            return None
        data, ts = self._store[key]
        if time.time() - ts >= self._ttl:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return data

    def set(self, key: str, value: dict) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = (value, time.time())
        if len(self._store) > self._max_size:
            self._store.popitem(last=False)  # evict LRU entry

    def __len__(self) -> int:
        return len(self._store)


_cache = _LRUCache(max_size=CACHE_MAX_SIZE, ttl=CACHE_TTL)


async def pokeapi_get(path: str) -> dict:
    """Fetch from PokeAPI with caching."""
    url = f"{POKEAPI_BASE}/{path}"
    cached = _cache.get(url)
    if cached is not None:
        return cached
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found on PokeAPI")
        resp.raise_for_status()
        data = resp.json()
        _cache.set(url, data)
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
