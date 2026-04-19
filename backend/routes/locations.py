from fastapi import APIRouter

from ..pokeapi import register_named_api_routes

router = APIRouter(prefix="/api", tags=["Locations"])

for _resource in ("location", "location-area", "pal-park-area", "region"):
    register_named_api_routes(router, _resource)
