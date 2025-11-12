from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import aiosqlite

DB_PATH = "nodes.db"

app = FastAPI(title="Bitcoin Node API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/nodes")
async def get_nodes(limit: int = 100):
    """
    Return up to `limit` Bitcoin node IPs, ordered by most recently seen.
    Example: /nodes?limit=500
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT ip FROM nodes ORDER BY first_seen DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [ip for (ip,) in rows]


@app.get("/count")
async def get_count():
    """
    Return total number of Bitcoin nodes stored in the database.
    Example: /count
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM nodes")
        (count,) = await cursor.fetchone()
        return {"count": count}


@app.get("/locations")
async def get_locations(limit: int | None = None):
    """
    Return up to `limit` geolocation entries in the format {latitude, longitude}.
    If no limit is given, return all available rows.
    """
    query = "SELECT latitude, longtitude FROM geolocations"
    params = ()

    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

    return [{lat, lon} for lat, lon in rows]
