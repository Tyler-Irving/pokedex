"""Shared PokeAPI client with in-memory caching."""

import time
from collections import OrderedDict
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query

from .schemas import NamedAPIResourceList

POKEAPI_BASE = "https://pokeapi.co/api/v2"

CACHE_TTL = 300  # 5 minutes
CACHE_MAX_SIZE = 500


class _LRUCache:
    """TTL-aware LRU cache backed by OrderedDict."""

    def __init__(self, max_size: int, ttl: float) -> None:
        self._store: OrderedDict[str, tuple[dict[str, Any], float]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl

    def get(self, key: str) -> dict[str, Any] | None:
        if key not in self._store:
            return None
        data, cached_at = self._store[key]
        if time.time() - cached_at >= self._ttl:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return data

    def set(self, key: str, value: dict[str, Any]) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = (value, time.time())
        if len(self._store) > self._max_size:
            self._store.popitem(last=False)  # evict LRU entry

    def __len__(self) -> int:
        return len(self._store)


_cache = _LRUCache(max_size=CACHE_MAX_SIZE, ttl=CACHE_TTL)


async def pokeapi_get(path: str) -> dict[str, Any]:
    """Fetch from PokeAPI with caching."""
    url = f"{POKEAPI_BASE}/{path}"
    cached = _cache.get(url)
    if cached is not None:
        return cached
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Not found on PokeAPI")
            resp.raise_for_status()
            data = resp.json()
            _cache.set(url, data)
            return data
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="PokeAPI request timed out")
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"PokeAPI unreachable: {exc}")


_type_index: dict[str, list[str]] = {}  # type_name -> [pokemon_name, ...]


async def build_type_index():
    data = await pokeapi_get("type?limit=50")
    for type_entry in data["results"]:
        type_data = await pokeapi_get(f"type/{type_entry['name']}")
        _type_index[type_entry["name"]] = [
            pokemon_entry["pokemon"]["name"] for pokemon_entry in type_data["pokemon"]
        ]


def register_named_api_routes(
    router: APIRouter,
    resource: str,
    *,
    id_only: bool = False,
) -> None:
    """Register standard list + detail proxy routes for a PokeAPI resource.

    Adds two routes to ``router``:
      - ``GET /{resource}``                     → paginated list
      - ``GET /{resource}/{id_or_name}`` (or ``{id}`` when ``id_only``)

    ``id_only=True`` is used for resources whose detail endpoint only
    accepts a numeric id (evolution-chain, machine, contest-effect, ...).
    """

    async def _list(
        offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    ):
        return await pokeapi_get(f"{resource}?limit={limit}&offset={offset}")

    router.add_api_route(
        f"/{resource}",
        _list,
        methods=["GET"],
        response_model=NamedAPIResourceList,
    )

    if id_only:
        async def _detail(id: int):
            return await pokeapi_get(f"{resource}/{id}")

        router.add_api_route(f"/{resource}/{{id}}", _detail, methods=["GET"])
    else:
        async def _detail(id_or_name: str):
            return await pokeapi_get(f"{resource}/{id_or_name}")

        router.add_api_route(f"/{resource}/{{id_or_name}}", _detail, methods=["GET"])


_type_chart: dict[str, dict[str, Any]] = {}


async def build_type_chart():
    """Cache type effectiveness data for coverage calculations."""
    data = await pokeapi_get("type?limit=50")
    for type_entry in data["results"]:
        name = type_entry["name"]
        if name in ("unknown", "shadow"):
            continue
        type_data = await pokeapi_get(f"type/{name}")
        _type_chart[name] = type_data["damage_relations"]
