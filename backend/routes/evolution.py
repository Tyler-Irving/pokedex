from fastapi import APIRouter

from ..pokeapi import register_named_api_routes

router = APIRouter(prefix="/api", tags=["Evolution"])

register_named_api_routes(router, "evolution-chain", id_only=True)
register_named_api_routes(router, "evolution-trigger")
