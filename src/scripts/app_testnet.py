"""
FastAPI backend for Bitcoin Testnet Heatmap
Serves pre-populated peer data and allows dynamic refresh
"""
import os
import time
import sqlite3
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "../../databases/bitcoin_testnet.db")

# CORS configuration
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001"
).split(",")

app = FastAPI(
    title="Bitcoin Testnet Peer Heatmap API",
    description="API for serving Bitcoin testnet peer geolocation data",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if "*" not in ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class Stats(BaseModel):
    """Statistics response model"""
    total_peers: int
    geolocated_peers: int
    countries: int
    last_crawl: Optional[int]
    crawl_duration: Optional[int]


def get_db_connection():
    """Get database connection"""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail=f"Database not found: {DB_PATH}")
    return sqlite3.connect(DB_PATH)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Bitcoin Testnet Peer Heatmap API",
        "version": "1.0.0",
        "description": "Serving 100K+ testnet peer locations",
        "network": "testnet",
        "data_source": "Real P2P crawl + Geolocation",
        "endpoints": {
            "/": "This endpoint (API information)",
            "/health": "Health check and database status",
            "/stats": "Statistics about crawled data",
            "/locations": "Geolocation coordinates for heatmap",
            "/locations?limit=N": "Limit number of locations returned",
            "/peers": "List of all peers with details",
            "/peers/{ip}": "Details for specific peer",
            "/countries": "Peer count by country",
            "/metadata": "Crawl metadata and information"
        },
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check database tables
        cursor.execute("SELECT COUNT(*) FROM peers")
        (peer_count,) = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM geolocations")
        (geo_count,) = cursor.fetchone()
        
        conn.close()
        
        coverage = (geo_count / peer_count * 100) if peer_count > 0 else 0
        
        return {
            "status": "healthy",
            "database": {
                "connected": True,
                "path": DB_PATH,
                "peers": peer_count,
                "geolocations": geo_count,
                "coverage": round(coverage, 2)
            },
            "network": "testnet",
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": int(time.time())
        }


@app.get("/stats", response_model=Stats)
async def get_stats():
    """Get statistics about crawled data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total peers
        cursor.execute("SELECT COUNT(*) FROM peers")
        (total_peers,) = cursor.fetchone()
        
        # Geolocated peers
        cursor.execute("SELECT COUNT(*) FROM geolocations")
        (geolocated_peers,) = cursor.fetchone()
        
        # Countries
        cursor.execute("SELECT COUNT(DISTINCT country) FROM geolocations WHERE country != ''")
        (countries,) = cursor.fetchone()
        
        # Last crawl info
        cursor.execute("""
            SELECT crawl_date, crawl_duration_seconds 
            FROM crawl_metadata 
            ORDER BY id DESC 
            LIMIT 1
        """)
        result = cursor.fetchone()
        last_crawl = result[0] if result else None
        crawl_duration = result[1] if result else None
        
        conn.close()
        
        return Stats(
            total_peers=total_peers,
            geolocated_peers=geolocated_peers,
            countries=countries or 0,
            last_crawl=last_crawl,
            crawl_duration=crawl_duration
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/locations")
async def get_locations(limit: Optional[int] = None):
    """Get geolocation data for heatmap visualization"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if limit and limit > 0:
            cursor.execute("""
                SELECT g.lat, g.lon, g.country, g.city
                FROM geolocations g
                INNER JOIN peers p ON g.ip = p.ip
                ORDER BY p.last_seen DESC
                LIMIT ?
            """, (limit,))
        else:
            cursor.execute("""
                SELECT g.lat, g.lon, g.country, g.city
                FROM geolocations g
                INNER JOIN peers p ON g.ip = p.ip
                ORDER BY p.last_seen DESC
            """)
        
        locations = [
            {
                "lat": row[0],
                "lng": row[1],
                "country": row[2] or "Unknown",
                "city": row[3] or "Unknown"
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            "count": len(locations),
            "locations": locations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/peers")
async def get_peers(limit: Optional[int] = 100):
    """Get list of peers with details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.ip, p.port, p.user_agent, p.last_seen, p.contacted, 
                   g.country, g.city, g.lat, g.lon
            FROM peers p
            LEFT JOIN geolocations g ON p.ip = g.ip
            ORDER BY p.last_seen DESC
            LIMIT ?
        """, (limit,))
        
        peers = [
            {
                "ip": row[0],
                "port": row[1],
                "user_agent": row[2],
                "last_seen": row[3],
                "contacted": bool(row[4]),
                "location": {
                    "country": row[5] or "Unknown",
                    "city": row[6] or "Unknown",
                    "lat": row[7],
                    "lon": row[8]
                } if row[7] is not None else None
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            "count": len(peers),
            "peers": peers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/peers/{ip}")
async def get_peer(ip: str):
    """Get details for a specific peer"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.ip, p.port, p.user_agent, p.protocol_version, p.services,
                   p.first_discovered, p.last_seen, p.contacted, p.successful_handshake,
                   g.country, g.city, g.region, g.lat, g.lon, g.isp
            FROM peers p
            LEFT JOIN geolocations g ON p.ip = g.ip
            WHERE p.ip = ?
        """, (ip,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Peer {ip} not found")
        
        return {
            "ip": row[0],
            "port": row[1],
            "user_agent": row[2],
            "protocol_version": row[3],
            "services": row[4],
            "first_discovered": row[5],
            "last_seen": row[6],
            "contacted": bool(row[7]),
            "successful_handshake": bool(row[8]),
            "location": {
                "country": row[9] or "Unknown",
                "city": row[10] or "Unknown",
                "region": row[11] or "Unknown",
                "lat": row[12],
                "lon": row[13],
                "isp": row[14] or "Unknown"
            } if row[12] is not None else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/countries")
async def get_countries():
    """Get peer count by country"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT country, COUNT(*) as count
            FROM geolocations
            WHERE country != ''
            GROUP BY country
            ORDER BY count DESC
        """)
        
        countries = [
            {"country": row[0], "count": row[1]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            "total_countries": len(countries),
            "countries": countries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metadata")
async def get_metadata():
    """Get crawl metadata"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT crawl_date, total_peers_discovered, total_peers_contacted,
                   total_geolocated, crawl_duration_seconds, iterations_completed, notes
            FROM crawl_metadata
            ORDER BY id DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {"message": "No crawl metadata available"}
        
        return {
            "crawl_date": row[0],
            "total_peers_discovered": row[1],
            "total_peers_contacted": row[2],
            "total_geolocated": row[3],
            "crawl_duration_seconds": row[4],
            "crawl_duration_minutes": round(row[4] / 60, 1) if row[4] else 0,
            "iterations_completed": row[5],
            "notes": row[6],
            "network": "testnet"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Bitcoin Testnet Heatmap API...")
    print(f"📊 Database: {DB_PATH}")
    print("🌐 Server: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

