from fastapi import APIRouter, Query

from ..pokeapi import pokeapi_get

router = APIRouter(prefix="/api", tags=["Machines"])


# --- Machine (id only) ---

@router.get("/machine")
async def list_machines(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"machine?limit={limit}&offset={offset}")


@router.get("/machine/{id}")
async def get_machine(id: int):
    return await pokeapi_get(f"machine/{id}")
