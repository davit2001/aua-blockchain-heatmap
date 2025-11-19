from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import aiosqlite
import os

DB_PATH = "nodes.db"

# Configure allowed origins from environment variable
# Default to localhost for development
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001"
).split(",")

app = FastAPI(
    title="Bitcoin Node API",
    description="API for Bitcoin node discovery and geolocation data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if "*" not in ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["GET"],  # Only allow GET requests for security
    allow_headers=["Content-Type"],
)


@app.on_event("startup")
async def init_db():
    """Create tables and indexes if they don't exist yet."""
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
        
        CREATE INDEX IF NOT EXISTS idx_geolocations_ip ON geolocations(ip);
        CREATE INDEX IF NOT EXISTS idx_nodes_first_seen ON nodes(first_seen DESC);
        """)
        await db.commit()
    print("✅ Database initialized with indexes")


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
