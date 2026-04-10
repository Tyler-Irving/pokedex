from fastapi import APIRouter, Query

from ..pokeapi import pokeapi_get, _type_index

router = APIRouter(prefix="/api", tags=["Pokemon"])


# --- Pokemon (enhanced with search/filter) ---

@router.get("/pokemon")
async def list_pokemon(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    type: str | None = Query(None),
):
    """List pokemon with pagination, optional search and type filter."""
    data = await pokeapi_get("pokemon?limit=1302&offset=0")
    results = data["results"]

    if search:
        q = search.lower()
        results = [r for r in results if q in r["name"]]

    if type and type in _type_index:
        type_names = set(_type_index[type])
        results = [r for r in results if r["name"] in type_names]

    total = len(results)
    page = results[offset : offset + limit]

    enriched = []
    for p in page:
        pid = int(p["url"].rstrip("/").split("/")[-1])
        enriched.append(
            {
                "id": pid,
                "name": p["name"],
                "sprite": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png",
            }
        )

    return {"total": total, "results": enriched}


@router.get("/pokemon/{pokemon_id}")
async def get_pokemon(pokemon_id: int):
    """Get detailed info for a single pokemon."""
    data = await pokeapi_get(f"pokemon/{pokemon_id}")
    species = await pokeapi_get(f"pokemon-species/{pokemon_id}")

    flavor = ""
    for entry in species.get("flavor_text_entries", []):
        if entry["language"]["name"] == "en":
            flavor = entry["flavor_text"].replace("\n", " ").replace("\f", " ")
            break

    return {
        "id": data["id"],
        "name": data["name"],
        "sprite": data["sprites"]["front_default"],
        "sprite_shiny": data["sprites"].get("front_shiny"),
        "types": [t["type"]["name"] for t in data["types"]],
        "stats": {s["stat"]["name"]: s["base_stat"] for s in data["stats"]},
        "height": data["height"],
        "weight": data["weight"],
        "abilities": [a["ability"]["name"] for a in data["abilities"]],
        "flavor_text": flavor,
    }


@router.get("/pokemon/{id_or_name}/encounters")
async def get_pokemon_encounters(id_or_name: str):
    """Get location areas where a pokemon can be found."""
    return await pokeapi_get(f"pokemon/{id_or_name}/encounters")


# --- Types (enhanced with pre-built index) ---

@router.get("/types")
async def list_types():
    """List all pokemon types."""
    return {"types": sorted(_type_index.keys())}


@router.get("/type")
async def list_types_full(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"type?limit={limit}&offset={offset}")


@router.get("/type/{id_or_name}")
async def get_type(id_or_name: str):
    return await pokeapi_get(f"type/{id_or_name}")


# --- Ability ---

@router.get("/ability")
async def list_abilities(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"ability?limit={limit}&offset={offset}")


@router.get("/ability/{id_or_name}")
async def get_ability(id_or_name: str):
    return await pokeapi_get(f"ability/{id_or_name}")


# --- Characteristic (id only) ---

@router.get("/characteristic")
async def list_characteristics(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"characteristic?limit={limit}&offset={offset}")


@router.get("/characteristic/{id}")
async def get_characteristic(id: int):
    return await pokeapi_get(f"characteristic/{id}")


# --- Egg Group ---

@router.get("/egg-group")
async def list_egg_groups(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"egg-group?limit={limit}&offset={offset}")


@router.get("/egg-group/{id_or_name}")
async def get_egg_group(id_or_name: str):
    return await pokeapi_get(f"egg-group/{id_or_name}")


# --- Gender ---

@router.get("/gender")
async def list_genders(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"gender?limit={limit}&offset={offset}")


@router.get("/gender/{id_or_name}")
async def get_gender(id_or_name: str):
    return await pokeapi_get(f"gender/{id_or_name}")


# --- Growth Rate ---

@router.get("/growth-rate")
async def list_growth_rates(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"growth-rate?limit={limit}&offset={offset}")


@router.get("/growth-rate/{id_or_name}")
async def get_growth_rate(id_or_name: str):
    return await pokeapi_get(f"growth-rate/{id_or_name}")


# --- Nature ---

@router.get("/nature")
async def list_natures(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"nature?limit={limit}&offset={offset}")


@router.get("/nature/{id_or_name}")
async def get_nature(id_or_name: str):
    return await pokeapi_get(f"nature/{id_or_name}")


# --- Pokeathlon Stat ---

@router.get("/pokeathlon-stat")
async def list_pokeathlon_stats(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"pokeathlon-stat?limit={limit}&offset={offset}")


@router.get("/pokeathlon-stat/{id_or_name}")
async def get_pokeathlon_stat(id_or_name: str):
    return await pokeapi_get(f"pokeathlon-stat/{id_or_name}")


# --- Pokemon Color ---

@router.get("/pokemon-color")
async def list_pokemon_colors(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"pokemon-color?limit={limit}&offset={offset}")


@router.get("/pokemon-color/{id_or_name}")
async def get_pokemon_color(id_or_name: str):
    return await pokeapi_get(f"pokemon-color/{id_or_name}")


# --- Pokemon Form ---

@router.get("/pokemon-form")
async def list_pokemon_forms(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"pokemon-form?limit={limit}&offset={offset}")


@router.get("/pokemon-form/{id_or_name}")
async def get_pokemon_form(id_or_name: str):
    return await pokeapi_get(f"pokemon-form/{id_or_name}")


# --- Pokemon Habitat ---

@router.get("/pokemon-habitat")
async def list_pokemon_habitats(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"pokemon-habitat?limit={limit}&offset={offset}")


@router.get("/pokemon-habitat/{id_or_name}")
async def get_pokemon_habitat(id_or_name: str):
    return await pokeapi_get(f"pokemon-habitat/{id_or_name}")


# --- Pokemon Shape ---

@router.get("/pokemon-shape")
async def list_pokemon_shapes(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"pokemon-shape?limit={limit}&offset={offset}")


@router.get("/pokemon-shape/{id_or_name}")
async def get_pokemon_shape(id_or_name: str):
    return await pokeapi_get(f"pokemon-shape/{id_or_name}")


# --- Pokemon Species ---

@router.get("/pokemon-species")
async def list_pokemon_species(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"pokemon-species?limit={limit}&offset={offset}")


@router.get("/pokemon-species/{id_or_name}")
async def get_pokemon_species(id_or_name: str):
    return await pokeapi_get(f"pokemon-species/{id_or_name}")


# --- Stat ---

@router.get("/stat")
async def list_stats(
    offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
):
    return await pokeapi_get(f"stat?limit={limit}&offset={offset}")


@router.get("/stat/{id_or_name}")
async def get_stat(id_or_name: str):
    return await pokeapi_get(f"stat/{id_or_name}")
