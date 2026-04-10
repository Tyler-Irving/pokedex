from fastapi import APIRouter, Query

from ..pokeapi import pokeapi_get
from ..schemas import NamedAPIResourceList

router = APIRouter(prefix="/api", tags=["Games"])


# --- Generation ---

@router.get("/generation", response_model=NamedAPIResourceList)
async def list_generations(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"generation?limit={limit}&offset={offset}")


@router.get("/generation/{id_or_name}")
async def get_generation(id_or_name: str):
    return await pokeapi_get(f"generation/{id_or_name}")


# --- Pokedex ---

@router.get("/pokedex", response_model=NamedAPIResourceList)
async def list_pokedexes(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"pokedex?limit={limit}&offset={offset}")


@router.get("/pokedex/{id_or_name}")
async def get_pokedex(id_or_name: str):
    return await pokeapi_get(f"pokedex/{id_or_name}")


# --- Version ---

@router.get("/version", response_model=NamedAPIResourceList)
async def list_versions(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"version?limit={limit}&offset={offset}")


@router.get("/version/{id_or_name}")
async def get_version(id_or_name: str):
    return await pokeapi_get(f"version/{id_or_name}")


# --- Version Group ---

@router.get("/version-group", response_model=NamedAPIResourceList)
async def list_version_groups(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"version-group?limit={limit}&offset={offset}")


@router.get("/version-group/{id_or_name}")
async def get_version_group(id_or_name: str):
    return await pokeapi_get(f"version-group/{id_or_name}")
