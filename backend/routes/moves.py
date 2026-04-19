from fastapi import APIRouter

from ..pokeapi import register_named_api_routes

router = APIRouter(prefix="/api", tags=["Moves"])

for _resource in (
    "move",
    "move-ailment",
    "move-battle-style",
    "move-category",
    "move-damage-class",
    "move-learn-method",
    "move-target",
):
    register_named_api_routes(router, _resource)
