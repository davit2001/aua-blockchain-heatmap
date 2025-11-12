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


@app.on_event("startup")
async def init_db():
    """Create tables if they don't exist yet."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
            ip TEXT PRIMARY KEY,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS geolocations (
            ip TEXT,
            latitude REAL,
            longitude REAL,
            FOREIGN KEY (ip) REFERENCES nodes (ip)
        );
        """)
        await db.commit()
    print("✅ Database initialized")


@app.get("/nodes")
async def get_nodes(limit: int = 100):
    """Return up to `limit` Bitcoin node IPs."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT ip FROM nodes ORDER BY first_seen DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [ip for (ip,) in rows]


@app.get("/count")
async def get_count():
    """Return total number of Bitcoin nodes."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM nodes")
        (count,) = await cursor.fetchone()
        return {"count": count}


@app.get("/locations")
async def get_locations(limit: int | None = None):
    """Return up to `limit` geolocation entries."""
    query = "SELECT latitude, longitude FROM geolocations"
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

    return [{"latitude": lat, "longitude": lon} for lat, lon in rows]
