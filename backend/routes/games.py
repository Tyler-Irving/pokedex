from fastapi import APIRouter

from ..pokeapi import register_named_api_routes

router = APIRouter(prefix="/api", tags=["Games"])

for _resource in ("generation", "pokedex", "version", "version-group"):
    register_named_api_routes(router, _resource)
