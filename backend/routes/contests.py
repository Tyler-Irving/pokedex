from fastapi import APIRouter

from ..pokeapi import register_named_api_routes

router = APIRouter(prefix="/api", tags=["Contests"])

register_named_api_routes(router, "contest-type")
register_named_api_routes(router, "contest-effect", id_only=True)
register_named_api_routes(router, "super-contest-effect", id_only=True)
