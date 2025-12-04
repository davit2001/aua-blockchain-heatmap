from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel
from contextlib import asynccontextmanager
import aiosqlite
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db", "nodes.db")


app = FastAPI(title="Bitcoin Node API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")
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
    yield
    print("👋 Shutting down...")

app = FastAPI(lifespan=lifespan)

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


@app.get("/stats")
async def get_stats():
    """Return basic statistics about crawled nodes"""
    async with aiosqlite.connect(DB_PATH) as db:

        # Total peers discovered
        cursor = await db.execute("SELECT COUNT(*) FROM peers")
        (total_peers,) = await cursor.fetchone()

        # Geolocated peers
        cursor = await db.execute("SELECT COUNT(*) FROM geolocations")
        (geolocated_peers,) = await cursor.fetchone()

        # Latest crawl metadata
        cursor = await db.execute("""
            SELECT crawl_date, crawl_duration_seconds
            FROM crawl_metadata
            ORDER BY id DESC
            LIMIT 1
        """)
        row = await cursor.fetchone()

        last_crawl = row[0] if row else None
        crawl_duration = row[1] if row else None

    return {
        "total_peers": total_peers,
        "geolocated_peers": geolocated_peers,
        "last_crawl": last_crawl,
        "crawl_duration": crawl_duration
    }


