import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import get_db, init_db
from .middleware import CacheHeaderMiddleware, LoggingMiddleware, RateLimitMiddleware, configure_logging
from .pokeapi import _cache, build_type_index
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


configure_logging()

_start_time = time.time()


_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        await build_type_index()
    except Exception:
        _logger.warning("build_type_index() failed at startup; type filtering will be unavailable", exc_info=True)
    yield


app = FastAPI(title="Pokédex", lifespan=lifespan)

# Middleware is applied in reverse registration order (last registered = outermost).
# Logging is outermost so it records every request including 429s from rate limiting.
# Rate limiting short-circuits before cache headers run on the inner response.
app.add_middleware(CacheHeaderMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_window=100, window_seconds=60)
app.add_middleware(LoggingMiddleware)

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


# --------------- Health check ---------------

@app.get("/api/health")
async def health():
    db_status = "ok"
    db = None
    try:
        db = await get_db()
        await db.execute("SELECT 1")
    except Exception:
        db_status = "error"
    finally:
        if db is not None:
            await db.close()
    return {
        "status": "ok",
        "uptime_seconds": time.time() - _start_time,
        "cache_entries": len(_cache),
        "db": db_status,
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
