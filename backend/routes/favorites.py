from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..pokeapi import pokeapi_get

router = APIRouter(prefix="/api", tags=["Favorites"])


@router.get("/favorites")
def list_favorites():
    db = get_db()
    rows = db.execute(
        "SELECT pokemon_id, name, sprite FROM favorites ORDER BY added_at DESC"
    ).fetchall()
    db.close()
    return {"favorites": [dict(r) for r in rows]}


@router.post("/favorites/{pokemon_id}")
async def add_favorite(pokemon_id: int):
    data = await pokeapi_get(f"pokemon/{pokemon_id}")
    db = get_db()
    try:
        db.execute(
            "INSERT INTO favorites (pokemon_id, name, sprite) VALUES (?, ?, ?)",
            (pokemon_id, data["name"], data["sprites"]["front_default"]),
        )
        db.commit()
    except Exception:
        db.close()
        raise HTTPException(status_code=409, detail="Already a favorite")
    db.close()
    return {"ok": True}


@router.delete("/favorites/{pokemon_id}")
def remove_favorite(pokemon_id: int):
    db = get_db()
    cur = db.execute("DELETE FROM favorites WHERE pokemon_id = ?", (pokemon_id,))
    db.commit()
    db.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not in favorites")
    return {"ok": True}
