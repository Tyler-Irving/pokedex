from fastapi import APIRouter

from ..pokeapi import register_named_api_routes

router = APIRouter(prefix="/api", tags=["Machines"])

register_named_api_routes(router, "machine", id_only=True)
