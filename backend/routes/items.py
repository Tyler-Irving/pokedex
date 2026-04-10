from fastapi import APIRouter, Query

from ..pokeapi import pokeapi_get

router = APIRouter(prefix="/api", tags=["Items"])


# --- Item ---

@router.get("/item")
async def list_items(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"item?limit={limit}&offset={offset}")


@router.get("/item/{id_or_name}")
async def get_item(id_or_name: str):
    return await pokeapi_get(f"item/{id_or_name}")


# --- Item Attribute ---

@router.get("/item-attribute")
async def list_item_attributes(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"item-attribute?limit={limit}&offset={offset}")


@router.get("/item-attribute/{id_or_name}")
async def get_item_attribute(id_or_name: str):
    return await pokeapi_get(f"item-attribute/{id_or_name}")


# --- Item Category ---

@router.get("/item-category")
async def list_item_categories(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"item-category?limit={limit}&offset={offset}")


@router.get("/item-category/{id_or_name}")
async def get_item_category(id_or_name: str):
    return await pokeapi_get(f"item-category/{id_or_name}")


# --- Item Fling Effect ---

@router.get("/item-fling-effect")
async def list_item_fling_effects(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"item-fling-effect?limit={limit}&offset={offset}")


@router.get("/item-fling-effect/{id}")
async def get_item_fling_effect(id: int):
    return await pokeapi_get(f"item-fling-effect/{id}")


# --- Item Pocket ---

@router.get("/item-pocket")
async def list_item_pockets(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"item-pocket?limit={limit}&offset={offset}")


@router.get("/item-pocket/{id_or_name}")
async def get_item_pocket(id_or_name: str):
    return await pokeapi_get(f"item-pocket/{id_or_name}")
