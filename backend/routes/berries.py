from fastapi import APIRouter

from ..pokeapi import register_named_api_routes

router = APIRouter(prefix="/api", tags=["Berries"])

for _resource in ("berry", "berry-firmness", "berry-flavor"):
    register_named_api_routes(router, _resource)
