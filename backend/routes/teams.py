import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_api_key
from ..database import get_db
from ..pokeapi import _type_chart, pokeapi_get
from ..schemas import (
    CoverageResponse,
    OkResponse,
    TeamCreateRequest,
    TeamDetail,
    TeamRenameRequest,
    TeamSummary,
    TeamsListResponse,
)

router = APIRouter(prefix="/api", tags=["Teams"])

MAX_TEAMS = 5
MAX_MEMBERS = 6

ALL_TYPES = [
    "normal", "fire", "water", "electric", "grass", "ice",
    "fighting", "poison", "ground", "flying", "psychic", "bug",
    "rock", "ghost", "dragon", "dark", "steel", "fairy",
]


@router.get("/teams", response_model=TeamsListResponse)
async def list_teams(_: None = Depends(require_api_key)):
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT t.id, t.name, COUNT(tm.id) AS member_count
            FROM teams t
            LEFT JOIN team_members tm ON tm.team_id = t.id
            GROUP BY t.id, t.name
            ORDER BY t.created_at ASC
            """
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()
    return {"teams": [dict(row) for row in rows]}


@router.post("/teams", response_model=TeamSummary, status_code=201)
async def create_team(body: TeamCreateRequest, _: None = Depends(require_api_key)):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) FROM teams")
        (count,) = await cursor.fetchone()
        if count >= MAX_TEAMS:
            raise HTTPException(status_code=409, detail=f"Max {MAX_TEAMS} teams allowed")
        cursor = await db.execute(
            "INSERT INTO teams (name) VALUES (?) RETURNING id, name",
            (body.name,),
        )
        row = await cursor.fetchone()
        await db.commit()
    finally:
        await db.close()
    return {"id": row["id"], "name": row["name"], "member_count": 0}


@router.patch("/teams/{team_id}", response_model=TeamSummary)
async def rename_team(team_id: int, body: TeamRenameRequest, _: None = Depends(require_api_key)):
    db = await get_db()
    try:
        cursor = await db.execute(
            "UPDATE teams SET name = ? WHERE id = ? RETURNING id, name",
            (body.name, team_id),
        )
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Team not found")
        await db.commit()
        c = await db.execute(
            "SELECT COUNT(*) FROM team_members WHERE team_id = ?", (team_id,)
        )
        (member_count,) = await c.fetchone()
    finally:
        await db.close()
    return {"id": row["id"], "name": row["name"], "member_count": member_count}


@router.delete("/teams/{team_id}", response_model=OkResponse)
async def delete_team(team_id: int, _: None = Depends(require_api_key)):
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        await db.commit()
        rowcount = cursor.rowcount
    finally:
        await db.close()
    if rowcount == 0:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"ok": True}


@router.get("/teams/{team_id}", response_model=TeamDetail)
async def get_team(team_id: int, _: None = Depends(require_api_key)):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id, name FROM teams WHERE id = ?", (team_id,))
        team_row = await cursor.fetchone()
        if team_row is None:
            raise HTTPException(status_code=404, detail="Team not found")
        cursor = await db.execute(
            "SELECT pokemon_id, name, sprite FROM team_members WHERE team_id = ? ORDER BY added_at ASC",
            (team_id,),
        )
        member_rows = await cursor.fetchall()
    finally:
        await db.close()
    return {
        "id": team_row["id"],
        "name": team_row["name"],
        "members": [dict(row) for row in member_rows],
    }


@router.post("/teams/{team_id}/members/{pokemon_id}", response_model=OkResponse, status_code=201)
async def add_member(team_id: int, pokemon_id: int, _: None = Depends(require_api_key)):
    # Fetch from PokeAPI before touching the DB so the count check and insert
    # happen in the same connection, eliminating the TOCTOU race window.
    data = await pokeapi_get(f"pokemon/{pokemon_id}")
    name = data["name"]
    sprite = data["sprites"]["front_default"]

    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM teams WHERE id = ?", (team_id,))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Team not found")
        cursor = await db.execute(
            "SELECT COUNT(*) FROM team_members WHERE team_id = ?", (team_id,)
        )
        (count,) = await cursor.fetchone()
        if count >= MAX_MEMBERS:
            raise HTTPException(status_code=409, detail=f"Team is full ({MAX_MEMBERS} members max)")
        await db.execute(
            "INSERT INTO team_members (team_id, pokemon_id, name, sprite) VALUES (?, ?, ?, ?)",
            (team_id, pokemon_id, name, sprite),
        )
        await db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Pokémon already on this team")
    finally:
        await db.close()
    return {"ok": True}


@router.delete("/teams/{team_id}/members/{pokemon_id}", response_model=OkResponse)
async def remove_member(team_id: int, pokemon_id: int, _: None = Depends(require_api_key)):
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM team_members WHERE team_id = ? AND pokemon_id = ?",
            (team_id, pokemon_id),
        )
        await db.commit()
        rowcount = cursor.rowcount
    finally:
        await db.close()
    if rowcount == 0:
        raise HTTPException(status_code=404, detail="Pokémon not on this team")
    return {"ok": True}


@router.get("/teams/{team_id}/coverage", response_model=CoverageResponse)
async def get_coverage(team_id: int, _: None = Depends(require_api_key)):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM teams WHERE id = ?", (team_id,))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Team not found")
        cursor = await db.execute(
            "SELECT pokemon_id FROM team_members WHERE team_id = ?", (team_id,)
        )
        member_rows = await cursor.fetchall()
    finally:
        await db.close()

    if not member_rows:
        return {"strong": [], "weak": [], "no_coverage": ALL_TYPES}

    if not _type_chart:
        raise HTTPException(status_code=503, detail="Type chart not yet loaded; try again shortly")

    member_types: list[list[str]] = []
    for row in member_rows:
        data = await pokeapi_get(f"pokemon/{row['pokemon_id']}")
        types = [t["type"]["name"] for t in data["types"]]
        member_types.append(types)

    all_team_types: set[str] = {t for types in member_types for t in types}

    def type_names(relations_key: str, type_name: str) -> set[str]:
        return {r["name"] for r in _type_chart.get(type_name, {}).get(relations_key, [])}

    def is_pokemon_weak_to(def_type: str, poke_types: list[str]) -> bool:
        """True if def_type deals a net super-effective hit to this pokemon.

        A pokemon is weak to def_type when:
        - At least one of its types takes double damage from def_type, AND
        - None of its types is immune to def_type (no_damage_from).
        """
        immune = any(def_type in type_names("no_damage_from", pt) for pt in poke_types)
        if immune:
            return False
        return any(def_type in type_names("double_damage_from", pt) for pt in poke_types)

    strong = []
    weak = []
    no_coverage = []

    for def_type in ALL_TYPES:
        can_hit = any(def_type in type_names("double_damage_to", atk) for atk in all_team_types)

        if can_hit:
            strong.append(def_type)
            continue

        all_members_vulnerable = all(
            is_pokemon_weak_to(def_type, poke_types)
            for poke_types in member_types
        )

        if all_members_vulnerable:
            weak.append(def_type)
        else:
            no_coverage.append(def_type)

    return {"strong": strong, "weak": weak, "no_coverage": no_coverage}
