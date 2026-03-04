import os
import aiosqlite
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "licenses.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                key TEXT PRIMARY KEY,
                hwid TEXT,
                bound_at TIMESTAMP
            )
        """)
        await db.commit()

async def get_license(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT hwid FROM licenses WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def insert_license(key: str, hwid: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO licenses (key, hwid, bound_at) VALUES (?, ?, ?)",
            (key, hwid, datetime.utcnow().isoformat())
        )
        await db.commit()

async def update_license_hwid(key: str, hwid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE licenses SET hwid = ?, bound_at = ? WHERE key = ?",
            (hwid, datetime.utcnow().isoformat(), key)
        )
        await db.commit()