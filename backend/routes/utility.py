from fastapi import APIRouter, Query

from ..pokeapi import pokeapi_get
from ..schemas import NamedAPIResourceList

router = APIRouter(prefix="/api", tags=["Utility"])


# --- Language ---

@router.get("/language", response_model=NamedAPIResourceList)
async def list_languages(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"language?limit={limit}&offset={offset}")


@router.get("/language/{id_or_name}")
async def get_language(id_or_name: str):
    return await pokeapi_get(f"language/{id_or_name}")
