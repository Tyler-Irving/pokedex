from fastapi import APIRouter

from ..pokeapi import register_named_api_routes

router = APIRouter(prefix="/api", tags=["Items"])

for _resource in ("item", "item-attribute", "item-category", "item-pocket"):
    register_named_api_routes(router, _resource)

register_named_api_routes(router, "item-fling-effect", id_only=True)
