import aiohttp
import asyncio
import aiosqlite
import time

BATCH_URL = "http://ip-api.com/batch"
BATCH_SIZE = 100       # Max 100 IPs per batch
BATCHS_PER_MIN = 15    # Free-tier rate limit (15 requests/min)

async def post_batch(session, ips_batch):
    payload = [{"query": ip} for ip in ips_batch]
    try:
        async with session.post(BATCH_URL, json=payload) as resp:
            if resp.status == 429:
                ttl = resp.headers.get("X-Ttl")
                wait_time = int(ttl) + 1 if ttl else 60
                print(f"[!] Rate limited — waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await post_batch(session, ips_batch)

            data = await resp.json()
            return data, resp.headers
    except Exception as e:
        print(f"[!] Error during batch post: {e}")
        return [], {}

async def run_batch(db_path="nodes.db"):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT DISTINCT ip FROM nodes_copy") as cursor:
            ips = [row[0] for row in await cursor.fetchall()]

        if not ips:
            print("[!] No IPs found in table 'nodes_copy'")
            return

        print(f"[+] Found {len(ips)} IPs to geolocate")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS geolocations (
                ip TEXT PRIMARY KEY,
                country TEXT,
                region TEXT,
                latitude REAL,
                longitude REAL
            )
        """)
        await db.commit()

        chunks = [ips[i:i+BATCH_SIZE] for i in range(0, len(ips), BATCH_SIZE)]
        pause_between = 60.0 / BATCHS_PER_MIN

        async with aiohttp.ClientSession() as session:
            for i, chunk in enumerate(chunks, 1):
                print(f"[>] Sending batch {i}/{len(chunks)} ({len(chunk)} IPs)...")

                results, headers = await post_batch(session, chunk)

                xrl = headers.get("X-Rl")
                xttl = headers.get("X-Ttl")
                if xrl is not None and int(xrl) == 0 and xttl is not None:
                    wait = int(xttl) + 1
                    print(f"[!] Hit batch limit. Waiting {wait}s...")
                    await asyncio.sleep(wait)

                rows = []
                for item in results:
                    if item.get("status") == "success":
                        rows.append((
                            item.get("query"),
                            item.get("country"),
                            item.get("regionName"),
                            item.get("lat"),
                            item.get("lon")
                        ))

                if rows:
                    await db.executemany(
                        "INSERT OR REPLACE INTO geolocations VALUES (?, ?, ?, ?, ?)",
                        rows
                    )
                    await db.commit()
                    print(f"[{i}/{len(chunks)}] Inserted {len(rows)} geolocations.")
                else:
                    print(f"[{i}/{len(chunks)}] No valid geolocations in this batch.")

                if i < len(chunks):
                    await asyncio.sleep(pause_between)

        print("[✓] All batches processed successfully.")

if __name__ == "__main__":
    asyncio.run(run_batch())
