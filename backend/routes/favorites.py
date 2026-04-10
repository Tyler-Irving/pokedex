import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_api_key
from ..database import get_db
from ..pokeapi import pokeapi_get
from ..schemas import FavoritesListResponse, OkResponse

router = APIRouter(prefix="/api", tags=["Favorites"])


@router.get("/favorites", response_model=FavoritesListResponse)
async def list_favorites(_: None = Depends(require_api_key)):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT pokemon_id, name, sprite FROM favorites ORDER BY added_at DESC"
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()
    return {"favorites": [dict(r) for r in rows]}


@router.post("/favorites/{pokemon_id}", response_model=OkResponse)
async def add_favorite(pokemon_id: int, _: None = Depends(require_api_key)):
    data = await pokeapi_get(f"pokemon/{pokemon_id}")
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO favorites (pokemon_id, name, sprite) VALUES (?, ?, ?)",
            (pokemon_id, data["name"], data["sprites"]["front_default"]),
        )
        await db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Already a favorite")
    finally:
        await db.close()
    return {"ok": True}


@router.delete("/favorites/{pokemon_id}", response_model=OkResponse)
async def remove_favorite(pokemon_id: int, _: None = Depends(require_api_key)):
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM favorites WHERE pokemon_id = ?", (pokemon_id,)
        )
        await db.commit()
    finally:
        await db.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not in favorites")
    return {"ok": True}
