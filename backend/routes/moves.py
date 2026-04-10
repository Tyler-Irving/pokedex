from fastapi import APIRouter, Query

from ..pokeapi import pokeapi_get

router = APIRouter(prefix="/api", tags=["Moves"])


# --- Move ---

@router.get("/move")
async def list_moves(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"move?limit={limit}&offset={offset}")


@router.get("/move/{id_or_name}")
async def get_move(id_or_name: str):
    return await pokeapi_get(f"move/{id_or_name}")


# --- Move Ailment ---

@router.get("/move-ailment")
async def list_move_ailments(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"move-ailment?limit={limit}&offset={offset}")


@router.get("/move-ailment/{id_or_name}")
async def get_move_ailment(id_or_name: str):
    return await pokeapi_get(f"move-ailment/{id_or_name}")


# --- Move Battle Style ---

@router.get("/move-battle-style")
async def list_move_battle_styles(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"move-battle-style?limit={limit}&offset={offset}")


@router.get("/move-battle-style/{id_or_name}")
async def get_move_battle_style(id_or_name: str):
    return await pokeapi_get(f"move-battle-style/{id_or_name}")


# --- Move Category ---

@router.get("/move-category")
async def list_move_categories(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"move-category?limit={limit}&offset={offset}")


@router.get("/move-category/{id_or_name}")
async def get_move_category(id_or_name: str):
    return await pokeapi_get(f"move-category/{id_or_name}")


# --- Move Damage Class ---

@router.get("/move-damage-class")
async def list_move_damage_classes(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"move-damage-class?limit={limit}&offset={offset}")


@router.get("/move-damage-class/{id_or_name}")
async def get_move_damage_class(id_or_name: str):
    return await pokeapi_get(f"move-damage-class/{id_or_name}")


# --- Move Learn Method ---

@router.get("/move-learn-method")
async def list_move_learn_methods(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"move-learn-method?limit={limit}&offset={offset}")


@router.get("/move-learn-method/{id_or_name}")
async def get_move_learn_method(id_or_name: str):
    return await pokeapi_get(f"move-learn-method/{id_or_name}")


# --- Move Target ---

@router.get("/move-target")
async def list_move_targets(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"move-target?limit={limit}&offset={offset}")


@router.get("/move-target/{id_or_name}")
async def get_move_target(id_or_name: str):
    return await pokeapi_get(f"move-target/{id_or_name}")
