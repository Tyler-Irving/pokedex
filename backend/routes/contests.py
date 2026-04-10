from fastapi import APIRouter, Query

from ..pokeapi import pokeapi_get
from ..schemas import NamedAPIResourceList

router = APIRouter(prefix="/api", tags=["Contests"])


# --- Contest Type ---

@router.get("/contest-type", response_model=NamedAPIResourceList)
async def list_contest_types(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"contest-type?limit={limit}&offset={offset}")


@router.get("/contest-type/{id_or_name}")
async def get_contest_type(id_or_name: str):
    return await pokeapi_get(f"contest-type/{id_or_name}")


# --- Contest Effect (id only) ---

@router.get("/contest-effect", response_model=NamedAPIResourceList)
async def list_contest_effects(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"contest-effect?limit={limit}&offset={offset}")


@router.get("/contest-effect/{id}")
async def get_contest_effect(id: int):
    return await pokeapi_get(f"contest-effect/{id}")


# --- Super Contest Effect (id only) ---

@router.get("/super-contest-effect", response_model=NamedAPIResourceList)
async def list_super_contest_effects(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"super-contest-effect?limit={limit}&offset={offset}")


@router.get("/super-contest-effect/{id}")
async def get_super_contest_effect(id: int):
    return await pokeapi_get(f"super-contest-effect/{id}")
