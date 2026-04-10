from fastapi import APIRouter, Query

from ..pokeapi import pokeapi_get
from ..schemas import NamedAPIResourceList

router = APIRouter(prefix="/api", tags=["Locations"])


# --- Location ---

@router.get("/location", response_model=NamedAPIResourceList)
async def list_locations(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"location?limit={limit}&offset={offset}")


@router.get("/location/{id_or_name}")
async def get_location(id_or_name: str):
    return await pokeapi_get(f"location/{id_or_name}")


# --- Location Area ---

@router.get("/location-area", response_model=NamedAPIResourceList)
async def list_location_areas(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"location-area?limit={limit}&offset={offset}")


@router.get("/location-area/{id_or_name}")
async def get_location_area(id_or_name: str):
    return await pokeapi_get(f"location-area/{id_or_name}")


# --- Pal Park Area ---

@router.get("/pal-park-area", response_model=NamedAPIResourceList)
async def list_pal_park_areas(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"pal-park-area?limit={limit}&offset={offset}")


@router.get("/pal-park-area/{id_or_name}")
async def get_pal_park_area(id_or_name: str):
    return await pokeapi_get(f"pal-park-area/{id_or_name}")


# --- Region ---

@router.get("/region", response_model=NamedAPIResourceList)
async def list_regions(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"region?limit={limit}&offset={offset}")


@router.get("/region/{id_or_name}")
async def get_region(id_or_name: str):
    return await pokeapi_get(f"region/{id_or_name}")
