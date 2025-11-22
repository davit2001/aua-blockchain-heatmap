#!/usr/bin/env python3
"""
Geolocate all discovered testnet peers
Adds latitude/longitude coordinates for heatmap visualization
Uses ip-api.com free tier (45 requests/minute, 100 IPs per batch)
"""
import asyncio
import aiohttp
import sqlite3
import time
from typing import List, Tuple

DB_PATH = "databases/bitcoin_testnet.db"
BATCH_SIZE = 100  # ip-api.com allows 100 IPs per batch
RATE_LIMIT_DELAY = 1.5  # Seconds between batches (45 req/min = ~1.3s)


def get_ungeolocated_ips() -> List[str]:
    """Get list of peer IPs that don't have geolocation data yet"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.ip FROM peers p
        LEFT JOIN geolocations g ON p.ip = g.ip
        WHERE g.ip IS NULL
        ORDER BY p.last_seen DESC
    """)
    
    ips = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ips


def save_geolocation(ip: str, lat: float, lon: float, country: str, city: str, region: str, isp: str):
    """Save geolocation data to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_time = int(time.time())
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO geolocations
            (ip, lat, lon, country, city, region, isp, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ip, lat, lon, country, city, region, isp, current_time))
        
        conn.commit()
    except Exception as e:
        print(f"⚠️  DB error for {ip}: {e}")
    finally:
        conn.close()


async def geolocate_batch(session: aiohttp.ClientSession, ips: List[str]) -> int:
    """Geolocate a batch of IPs using ip-api.com batch endpoint"""
    if not ips:
        return 0
    
    # Prepare batch request
    queries = [
        {
            "query": ip,
            "fields": "status,message,country,city,regionName,lat,lon,isp,query"
        }
        for ip in ips
    ]
    
    try:
        async with session.post(
            "http://ip-api.com/batch",
            json=queries,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status != 200:
                print(f"❌ HTTP Error {response.status}")
                return 0
            
            results = await response.json()
            
            success_count = 0
            for result in results:
                if result.get('status') == 'success':
                    ip = result.get('query')
                    lat = result.get('lat')
                    lon = result.get('lon')
                    country = result.get('country', '')
                    city = result.get('city', '')
                    region = result.get('regionName', '')
                    isp = result.get('isp', '')
                    
                    if ip and lat is not None and lon is not None:
                        save_geolocation(ip, lat, lon, country, city, region, isp)
                        success_count += 1
                else:
                    # Failed geolocation (probably private IP or invalid)
                    pass
            
            return success_count
            
    except asyncio.TimeoutError:
        print(f"⚠️  Timeout for batch of {len(ips)} IPs")
        return 0
    except Exception as e:
        print(f"⚠️  Error: {e}")
        return 0


async def geolocate_all_peers():
    """Geolocate all peers that don't have location data"""
    print("=" * 70)
    print("🌍 GEOLOCATING TESTNET PEERS")
    print("=" * 70)
    
    # Get ungeolocated IPs
    ips = get_ungeolocated_ips()
    total_ips = len(ips)
    
    print(f"\n📊 Found {total_ips:,} peers without geolocation")
    
    if total_ips == 0:
        print("✅ All peers already geolocated!")
        return
    
    # Calculate estimates
    num_batches = (total_ips + BATCH_SIZE - 1) // BATCH_SIZE
    estimated_time = (num_batches * RATE_LIMIT_DELAY) / 60
    
    print(f"📦 Batches needed: {num_batches:,} (batch size: {BATCH_SIZE})")
    print(f"⏱️  Estimated time: {estimated_time:.1f} minutes")
    print(f"🌐 Using: ip-api.com (free tier)")
    print("\n" + "=" * 70)
    
    start_time = time.time()
    total_geolocated = 0
    
    # Create aiohttp session
    async with aiohttp.ClientSession() as session:
        for i in range(0, total_ips, BATCH_SIZE):
            batch = ips[i:i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            
            # Geolocate batch
            success_count = await geolocate_batch(session, batch)
            total_geolocated += success_count
            
            # Progress
            progress = ((i + len(batch)) / total_ips) * 100
            elapsed = time.time() - start_time
            rate = total_geolocated / (elapsed / 60) if elapsed > 0 else 0
            eta = ((total_ips - (i + len(batch))) / rate) if rate > 0 else 0
            
            print(f"📍 Batch {batch_num}/{num_batches}: "
                  f"{success_count}/{len(batch)} successful | "
                  f"Progress: {progress:.1f}% | "
                  f"Total: {total_geolocated:,}/{total_ips:,} | "
                  f"Rate: {rate:.0f}/min | "
                  f"ETA: {eta:.1f}min")
            
            # Rate limiting (respect ip-api.com limits)
            if i + BATCH_SIZE < total_ips:  # Don't sleep on last batch
                await asyncio.sleep(RATE_LIMIT_DELAY)
    
    # Final statistics
    elapsed = time.time() - start_time
    success_rate = (total_geolocated / total_ips) * 100 if total_ips > 0 else 0
    
    print("\n" + "=" * 70)
    print("🎉 GEOLOCATION COMPLETE!")
    print("=" * 70)
    print(f"✅ Successfully geolocated: {total_geolocated:,}/{total_ips:,} ({success_rate:.1f}%)")
    print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
    print(f"📈 Average rate: {total_geolocated/(elapsed/60):.0f} IPs/minute")
    print(f"💾 Database: {DB_PATH}")
    print("=" * 70)
    
    # Update crawl metadata
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE crawl_metadata 
        SET total_geolocated = ?
        WHERE id = (SELECT MAX(id) FROM crawl_metadata)
    """, (total_geolocated,))
    conn.commit()
    conn.close()
    
    print("\n🎨 Data is ready for heatmap visualization!")
    print("   Next: Start the backend API and frontend!")
    print("=" * 70)


def show_statistics():
    """Display database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM peers")
    (total_peers,) = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) FROM geolocations")
    (total_geo,) = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(DISTINCT country) FROM geolocations")
    (total_countries,) = cursor.fetchone()
    
    cursor.execute("SELECT country, COUNT(*) as count FROM geolocations GROUP BY country ORDER BY count DESC LIMIT 10")
    top_countries = cursor.fetchall()
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("📊 DATABASE STATISTICS")
    print("=" * 70)
    print(f"Total peers: {total_peers:,}")
    print(f"Geolocated peers: {total_geo:,}")
    print(f"Coverage: {(total_geo/total_peers)*100:.1f}%" if total_peers > 0 else "N/A")
    print(f"Countries: {total_countries}")
    
    if top_countries:
        print(f"\n🌍 Top 10 Countries:")
        for i, (country, count) in enumerate(top_countries, 1):
            print(f"   {i:2d}. {country:20s} - {count:,} peers")
    
    print("=" * 70)


if __name__ == "__main__":
    print("\n🌍 Starting geolocation process...")
    print("   This will add lat/lon coordinates to all discovered peers\n")
    
    # Run geolocation
    asyncio.run(geolocate_all_peers())
    
    # Show statistics
    show_statistics()

