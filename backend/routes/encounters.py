from fastapi import APIRouter

from ..pokeapi import register_named_api_routes

router = APIRouter(prefix="/api", tags=["Encounters"])

for _resource in ("encounter-method", "encounter-condition", "encounter-condition-value"):
    register_named_api_routes(router, _resource)
