from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .pokeapi import build_type_index
from .routes import (
    berries,
    contests,
    encounters,
    evolution,
    favorites,
    games,
    items,
    locations,
    machines,
    moves,
    pokemon,
    utility,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await build_type_index()
    yield


app = FastAPI(title="Pokédex", lifespan=lifespan)

# Mount all routers
for module in [
    berries,
    contests,
    encounters,
    evolution,
    favorites,
    games,
    items,
    locations,
    machines,
    moves,
    pokemon,
    utility,
]:
    app.include_router(module.router)


# --------------- API index ---------------

@app.get("/api")
async def api_index():
    """List all available resource endpoints."""
    return {
        "berries": {
            "berry": "/api/berry",
            "berry-firmness": "/api/berry-firmness",
            "berry-flavor": "/api/berry-flavor",
        },
        "contests": {
            "contest-type": "/api/contest-type",
            "contest-effect": "/api/contest-effect",
            "super-contest-effect": "/api/super-contest-effect",
        },
        "encounters": {
            "encounter-method": "/api/encounter-method",
            "encounter-condition": "/api/encounter-condition",
            "encounter-condition-value": "/api/encounter-condition-value",
        },
        "evolution": {
            "evolution-chain": "/api/evolution-chain",
            "evolution-trigger": "/api/evolution-trigger",
        },
        "games": {
            "generation": "/api/generation",
            "pokedex": "/api/pokedex",
            "version": "/api/version",
            "version-group": "/api/version-group",
        },
        "items": {
            "item": "/api/item",
            "item-attribute": "/api/item-attribute",
            "item-category": "/api/item-category",
            "item-fling-effect": "/api/item-fling-effect",
            "item-pocket": "/api/item-pocket",
        },
        "locations": {
            "location": "/api/location",
            "location-area": "/api/location-area",
            "pal-park-area": "/api/pal-park-area",
            "region": "/api/region",
        },
        "machines": {
            "machine": "/api/machine",
        },
        "moves": {
            "move": "/api/move",
            "move-ailment": "/api/move-ailment",
            "move-battle-style": "/api/move-battle-style",
            "move-category": "/api/move-category",
            "move-damage-class": "/api/move-damage-class",
            "move-learn-method": "/api/move-learn-method",
            "move-target": "/api/move-target",
        },
        "pokemon": {
            "pokemon": "/api/pokemon",
            "ability": "/api/ability",
            "characteristic": "/api/characteristic",
            "egg-group": "/api/egg-group",
            "gender": "/api/gender",
            "growth-rate": "/api/growth-rate",
            "nature": "/api/nature",
            "pokeathlon-stat": "/api/pokeathlon-stat",
            "pokemon-color": "/api/pokemon-color",
            "pokemon-form": "/api/pokemon-form",
            "pokemon-habitat": "/api/pokemon-habitat",
            "pokemon-shape": "/api/pokemon-shape",
            "pokemon-species": "/api/pokemon-species",
            "stat": "/api/stat",
            "type": "/api/type",
            "types": "/api/types",
        },
        "favorites": {
            "favorites": "/api/favorites",
        },
        "utility": {
            "language": "/api/language",
        },
    }


# --------------- Serve frontend ---------------

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file = FRONTEND_DIR / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(FRONTEND_DIR / "index.html")
