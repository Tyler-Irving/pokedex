from fastapi import APIRouter, Query

from ..pokeapi import pokeapi_get

router = APIRouter(prefix="/api", tags=["Berries"])


# --- Berry ---

@router.get("/berry")
async def list_berries(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"berry?limit={limit}&offset={offset}")


@router.get("/berry/{id_or_name}")
async def get_berry(id_or_name: str):
    return await pokeapi_get(f"berry/{id_or_name}")


# --- Berry Firmness ---

@router.get("/berry-firmness")
async def list_berry_firmness(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"berry-firmness?limit={limit}&offset={offset}")


@router.get("/berry-firmness/{id_or_name}")
async def get_berry_firmness(id_or_name: str):
    return await pokeapi_get(f"berry-firmness/{id_or_name}")


# --- Berry Flavor ---

@router.get("/berry-flavor")
async def list_berry_flavors(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"berry-flavor?limit={limit}&offset={offset}")


@router.get("/berry-flavor/{id_or_name}")
async def get_berry_flavor(id_or_name: str):
    return await pokeapi_get(f"berry-flavor/{id_or_name}")
