from fastapi import APIRouter, Query

from ..pokeapi import pokeapi_get
from ..schemas import NamedAPIResourceList

router = APIRouter(prefix="/api", tags=["Evolution"])


# --- Evolution Chain (id only) ---

@router.get("/evolution-chain", response_model=NamedAPIResourceList)
async def list_evolution_chains(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"evolution-chain?limit={limit}&offset={offset}")


@router.get("/evolution-chain/{id}")
async def get_evolution_chain(id: int):
    return await pokeapi_get(f"evolution-chain/{id}")


# --- Evolution Trigger ---

@router.get("/evolution-trigger", response_model=NamedAPIResourceList)
async def list_evolution_triggers(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"evolution-trigger?limit={limit}&offset={offset}")


@router.get("/evolution-trigger/{id_or_name}")
async def get_evolution_trigger(id_or_name: str):
    return await pokeapi_get(f"evolution-trigger/{id_or_name}")
