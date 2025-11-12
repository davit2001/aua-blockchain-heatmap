import aiohttp
import asyncio
import aiosqlite
import time

API_URL = "http://ip-api.com/json/{}"

async def fetch_geolocation(session, ip):
    try:
        async with session.get(API_URL.format(ip)) as resp:
            if resp.status == 429:
                print("[!] Rate limited — sleeping for 60s")
                await asyncio.sleep(60)
                return await fetch_geolocation(session, ip)
            data = await resp.json()
            if data.get("status") == "success":
                return {
                    "ip": ip,
                    "latitude": data["lat"],
                    "longtitude": data["lon"],
                    "country": data["country"],
                    "region": data["regionName"],
                }
    except Exception as e:
        print(f"[!] Failed for {ip}: {e}")
    return None

async def main():
    async with aiosqlite.connect("nodes.db") as db:
        async with db.execute("SELECT DISTINCT ip FROM nodes") as cursor:
            ips = [row[0] for row in await cursor.fetchall()]

        print(f"[+] Found {len(ips)} IPs to geolocate")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS geolocations (
                ip TEXT PRIMARY KEY,
                country TEXT,
                region TEXT,
                latitude REAL,
                longtitude REAL
            )
        """)

        async with aiohttp.ClientSession() as session:
            for i, ip in enumerate(ips, 1):
                result = await fetch_geolocation(session, ip)
                if result:
                    await db.execute(
                        "INSERT OR REPLACE INTO geolocations VALUES (?, ?, ?, ?, ?)",
                        (result["ip"], result["country"], result["region"], result["latitude"], result["longtitude"])
                    )
                    await db.commit()
                    print(f"[{i}] {ip} → {result['country']}, {result['region']} ({result['latitude']}, {result['longtitude']})")
                await asyncio.sleep(1.5)

if __name__ == "__main__":
    asyncio.run(main())
