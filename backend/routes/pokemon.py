import asyncio
import re

from fastapi import APIRouter, HTTPException, Query

from ..pokeapi import pokeapi_get, register_named_api_routes, _type_index
from ..schemas import (
    CompareResponse,
    PokemonDetail,
    PokemonListResponse,
    TypesListResponse,
)

_POKEMON_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$|^\d+$")

router = APIRouter(prefix="/api", tags=["Pokemon"])


@router.get("/pokemon", response_model=PokemonListResponse)
async def list_pokemon(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    type: str | None = Query(None),
):
    """List pokemon with pagination, optional search and type filter."""
    data = await pokeapi_get("pokemon?limit=1302&offset=0")
    results = [
        entry for entry in data["results"]
        if int(entry["url"].rstrip("/").split("/")[-1]) < 10000
    ]

    if search:
        query = search.lower()
        results = [entry for entry in results if query in entry["name"]]

    if type and type in _type_index:
        type_names = set(_type_index[type])
        results = [entry for entry in results if entry["name"] in type_names]

    total = len(results)
    page = results[offset : offset + limit]

    enriched = []
    for entry in page:
        pid = int(entry["url"].rstrip("/").split("/")[-1])
        enriched.append(
            {
                "id": pid,
                "name": entry["name"],
                "sprite": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png",
            }
        )

    return {"total": total, "results": enriched}


@router.get("/pokemon/{pokemon_id}", response_model=PokemonDetail)
async def get_pokemon(pokemon_id: int):
    """Get detailed info for a single pokemon."""
    data = await pokeapi_get(f"pokemon/{pokemon_id}")
    species_path = data["species"]["url"].split("/api/v2/")[1]
    species = await pokeapi_get(species_path)

    flavor = ""
    for entry in species.get("flavor_text_entries", []):
        if entry["language"]["name"] == "en":
            flavor = entry["flavor_text"].replace("\n", " ").replace("\f", " ")
            break

    return {
        "id": data["id"],
        "name": data["name"],
        "sprite": data["sprites"].get("front_default"),
        "sprite_shiny": data["sprites"].get("front_shiny"),
        "types": [type_slot["type"]["name"] for type_slot in data["types"]],
        "stats": {stat_entry["stat"]["name"]: stat_entry["base_stat"] for stat_entry in data["stats"]},
        "height": data["height"],
        "weight": data["weight"],
        "abilities": [ability_slot["ability"]["name"] for ability_slot in data["abilities"]],
        "flavor_text": flavor,
    }


@router.get("/pokemon/{id_or_name}/encounters")
async def get_pokemon_encounters(id_or_name: str):
    """Get location areas where a pokemon can be found."""
    if not _POKEMON_ID_RE.match(id_or_name):
        raise HTTPException(status_code=400, detail="Invalid pokemon ID or name")
    return await pokeapi_get(f"pokemon/{id_or_name}/encounters")


@router.get("/compare", response_model=CompareResponse)
async def compare_pokemon(ids: str = Query(..., description="Comma-separated list of 2–6 pokemon IDs")):
    """Compare stats for 2 to 6 pokemon."""
    id_list = [raw_id.strip() for raw_id in ids.split(",") if raw_id.strip()]
    if len(id_list) < 2 or len(id_list) > 6:
        raise HTTPException(status_code=400, detail="Provide between 2 and 6 pokemon IDs.")
    invalid_format = [pid for pid in id_list if not _POKEMON_ID_RE.match(pid)]
    if invalid_format:
        raise HTTPException(status_code=400, detail=f"Invalid pokemon ID format: {', '.join(invalid_format)}")

    results = await asyncio.gather(
        *[pokeapi_get(f"pokemon/{pid}") for pid in id_list],
        return_exceptions=True,
    )

    invalid_ids = [id_list[index] for index, result in enumerate(results) if isinstance(result, Exception)]
    if invalid_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Invalid or unknown pokemon ID(s): {', '.join(invalid_ids)}",
        )

    pokemon = [
        {
            "id": data["id"],
            "name": data["name"],
            "sprite": data["sprites"].get("front_default"),
            "types": [type_slot["type"]["name"] for type_slot in data["types"]],
            "stats": {stat_entry["stat"]["name"]: stat_entry["base_stat"] for stat_entry in data["stats"]},
        }
        for data in results
    ]

    stat_names = ["hp", "attack", "defense", "special-attack", "special-defense", "speed"]
    best_in_stat = {
        stat: max(pokemon, key=lambda poke: poke["stats"].get(stat, 0))["name"]
        for stat in stat_names
    }

    return {"pokemon": pokemon, "best_in_stat": best_in_stat}


@router.get("/types", response_model=TypesListResponse)
async def list_types():
    """List all pokemon types."""
    return {"types": sorted(_type_index.keys())}


for _resource in (
    "type",
    "ability",
    "egg-group",
    "gender",
    "growth-rate",
    "nature",
    "pokeathlon-stat",
    "pokemon-color",
    "pokemon-form",
    "pokemon-habitat",
    "pokemon-shape",
    "pokemon-species",
    "stat",
):
    register_named_api_routes(router, _resource)

register_named_api_routes(router, "characteristic", id_only=True)
