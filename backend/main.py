from contextlib import asynccontextmanager
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import get_db, init_db

POKEAPI_BASE = "https://pokeapi.co/api/v2"

# In-memory cache: url -> (data, timestamp)
_cache: dict[str, tuple[dict, float]] = {}
CACHE_TTL = 300  # 5 minutes


async def pokeapi_get(path: str) -> dict:
    url = f"{POKEAPI_BASE}/{path}"
    now = time.time()
    if url in _cache:
        data, ts = _cache[url]
        if now - ts < CACHE_TTL:
            return data
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found on PokéAPI")
        resp.raise_for_status()
        data = resp.json()
        _cache[url] = (data, now)
        return data


# Pre-fetch type index for filtering
_type_index: dict[str, list[str]] = {}  # type_name -> [pokemon_name, ...]


async def build_type_index():
    data = await pokeapi_get("type?limit=50")
    for t in data["results"]:
        type_data = await pokeapi_get(f"type/{t['name']}")
        _type_index[t["name"]] = [
            p["pokemon"]["name"] for p in type_data["pokemon"]
        ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await build_type_index()
    yield


app = FastAPI(title="PokéAPI Proxy", lifespan=lifespan)

# --------------- Pokemon endpoints ---------------


@app.get("/api/pokemon")
async def list_pokemon(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    type: str | None = Query(None),
):
    """List pokemon with pagination, optional search and type filter."""
    # Fetch a large batch from PokéAPI for filtering/searching
    data = await pokeapi_get(f"pokemon?limit=1302&offset=0")
    results = data["results"]

    if search:
        q = search.lower()
        results = [r for r in results if q in r["name"]]

    if type and type in _type_index:
        type_names = set(_type_index[type])
        results = [r for r in results if r["name"] in type_names]

    total = len(results)
    page = results[offset : offset + limit]

    # Enrich with IDs and sprites
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


@app.get("/api/pokemon/{pokemon_id}")
async def get_pokemon(pokemon_id: int):
    """Get detailed info for a single pokemon."""
    data = await pokeapi_get(f"pokemon/{pokemon_id}")
    species = await pokeapi_get(f"pokemon-species/{pokemon_id}")

    # Find English flavor text
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


@app.get("/api/types")
async def list_types():
    """List all pokemon types."""
    return {"types": sorted(_type_index.keys())}


# --------------- Favorites endpoints ---------------


@app.get("/api/favorites")
def list_favorites():
    db = get_db()
    rows = db.execute(
        "SELECT pokemon_id, name, sprite FROM favorites ORDER BY added_at DESC"
    ).fetchall()
    db.close()
    return {"favorites": [dict(r) for r in rows]}


@app.post("/api/favorites/{pokemon_id}")
async def add_favorite(pokemon_id: int):
    # Fetch pokemon info to store
    data = await pokeapi_get(f"pokemon/{pokemon_id}")
    db = get_db()
    try:
        db.execute(
            "INSERT INTO favorites (pokemon_id, name, sprite) VALUES (?, ?, ?)",
            (
                pokemon_id,
                data["name"],
                data["sprites"]["front_default"],
            ),
        )
        db.commit()
    except Exception:
        db.close()
        raise HTTPException(status_code=409, detail="Already a favorite")
    db.close()
    return {"ok": True}


@app.delete("/api/favorites/{pokemon_id}")
def remove_favorite(pokemon_id: int):
    db = get_db()
    cur = db.execute("DELETE FROM favorites WHERE pokemon_id = ?", (pokemon_id,))
    db.commit()
    db.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not in favorites")
    return {"ok": True}


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
