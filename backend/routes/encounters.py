from fastapi import APIRouter, Query

from ..pokeapi import pokeapi_get

router = APIRouter(prefix="/api", tags=["Encounters"])


# --- Encounter Method ---

@router.get("/encounter-method")
async def list_encounter_methods(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"encounter-method?limit={limit}&offset={offset}")


@router.get("/encounter-method/{id_or_name}")
async def get_encounter_method(id_or_name: str):
    return await pokeapi_get(f"encounter-method/{id_or_name}")


# --- Encounter Condition ---

@router.get("/encounter-condition")
async def list_encounter_conditions(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"encounter-condition?limit={limit}&offset={offset}")


@router.get("/encounter-condition/{id_or_name}")
async def get_encounter_condition(id_or_name: str):
    return await pokeapi_get(f"encounter-condition/{id_or_name}")


# --- Encounter Condition Value ---

@router.get("/encounter-condition-value")
async def list_encounter_condition_values(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"encounter-condition-value?limit={limit}&offset={offset}")


@router.get("/encounter-condition-value/{id_or_name}")
async def get_encounter_condition_value(id_or_name: str):
    return await pokeapi_get(f"encounter-condition-value/{id_or_name}")
