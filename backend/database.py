import os

import aiosqlite

DB_PATH = os.environ.get("FAVORITES_DB_PATH", os.path.join(os.path.dirname(__file__), "favorites.db"))


async def get_db() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    return conn


async def init_db():
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pokemon_id INTEGER NOT NULL UNIQUE,
                name TEXT NOT NULL,
                sprite TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await conn.commit()
