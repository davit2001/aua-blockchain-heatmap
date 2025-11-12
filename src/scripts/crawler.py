#!/usr/bin/env python3
"""
Async Bitcoin P2P Crawler (Refactored, same logic).

- Resolves DNS seeds
- Connects to peers (TCP / 8333)
- Performs version/verack handshake
- Sends getaddr, parses addr responses
- Stores discovered IPs in SQLite (aiosqlite)
- Concurrent, rate-limited using asyncio.Semaphore
"""

import asyncio
import aiosqlite
import socket
import struct
import time
import random
import hashlib
import ipaddress
import os
from typing import List, Tuple

# -----------------------
# Configuration
# -----------------------
MAINNET_MAGIC = b'\xf9\xbe\xb4\xd9'
BITCOIN_PORT = 8333
PROTOCOL_VERSION = 70015
USER_AGENT = b"/BitcoinCrawler:0.1/"
DB_PATH = "nodes.db"

CONCURRENCY = 200
CONNECT_TIMEOUT = 8
READ_TIMEOUT = 8
CRAWL_ITERATIONS = 3

SEED_DNS = [
    "seed.bitcoin.sipa.be",
    "dnsseed.bluematt.me",
    "seed.bitcoinstats.com",
    "seed.bitcoin.jonasschnelli.ch",
    "seed.bitcoin.sprovoost.nl"
]

# -----------------------
# Utilities
# -----------------------
def sha256d(b: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()

def encode_varint(n: int) -> bytes:
    if n < 0xfd:
        return struct.pack("<B", n)
    elif n <= 0xffff:
        return b'\xfd' + struct.pack("<H", n)
    elif n <= 0xffffffff:
        return b'\xfe' + struct.pack("<I", n)
    return b'\xff' + struct.pack("<Q", n)

def decode_varint(b: bytes, offset: int = 0) -> Tuple[int, int]:
    prefix = b[offset]
    if prefix < 0xfd:
        return prefix, offset + 1
    if prefix == 0xfd:
        return struct.unpack_from("<H", b, offset + 1)[0], offset + 3
    if prefix == 0xfe:
        return struct.unpack_from("<I", b, offset + 1)[0], offset + 5
    return struct.unpack_from("<Q", b, offset + 1)[0], offset + 9

def ipv4_to_ipv6_packed(ipv4: str) -> bytes:
    parts = list(map(int, ipv4.split('.')))
    return b'\x00' * 10 + b'\xff\xff' + bytes(parts)

def make_message(command: str, payload: bytes) -> bytes:
    name = command.encode('ascii') + b'\x00' * (12 - len(command))
    length = struct.pack("<I", len(payload))
    checksum = sha256d(payload)[:4]
    return MAINNET_MAGIC + name + length + checksum + payload

def build_version_payload(peer_ip: str) -> bytes:
    version = struct.pack("<i", PROTOCOL_VERSION)
    services = struct.pack("<Q", 0)
    timestamp = struct.pack("<q", int(time.time()))

    addr_recv = struct.pack("<Q", 0) + ipv4_to_ipv6_packed(peer_ip) + struct.pack(">H", BITCOIN_PORT)
    addr_from = struct.pack("<Q", 0) + (b'\x00' * 16) + struct.pack(">H", BITCOIN_PORT)

    nonce = struct.pack("<Q", random.getrandbits(64))
    ua = encode_varint(len(USER_AGENT)) + USER_AGENT
    start_height = struct.pack("<i", 0)
    relay = b'\x00'

    return version + services + timestamp + addr_recv + addr_from + nonce + ua + start_height + relay

async def read_message(reader: asyncio.StreamReader) -> Tuple[str, bytes]:
    header = await asyncio.wait_for(reader.readexactly(24), READ_TIMEOUT)
    if header[:4] != MAINNET_MAGIC:
        raise ValueError("Bad magic")

    name = header[4:16].rstrip(b'\x00').decode('ascii')
    length = struct.unpack("<I", header[16:20])[0]
    checksum = header[20:24]

    payload = b''
    if length:
        payload = await asyncio.wait_for(reader.readexactly(length), READ_TIMEOUT)
        if sha256d(payload)[:4] != checksum:
            pass  # Ignore checksum mismatch silently
    return name, payload

def parse_addr_payload(payload: bytes) -> List[Tuple[str, int]]:
    peers = []
    try:
        offset = 0
        count, offset = decode_varint(payload, offset)
        for _ in range(count):
            if len(payload) - offset < 30:
                break
            _ = struct.unpack_from("<I", payload, offset)[0]; offset += 4
            _ = struct.unpack_from("<Q", payload, offset)[0]; offset += 8
            ip_packed = payload[offset:offset + 16]; offset += 16
            port = struct.unpack_from(">H", payload, offset)[0]; offset += 2

            if ip_packed[:12] == b'\x00'*10 + b'\xff\xff':
                ip = '.'.join(str(b) for b in ip_packed[12:])
            else:
                try:
                    ip = str(ipaddress.IPv6Address(ip_packed))
                except Exception:
                    continue
            peers.append((ip, port))
    except Exception:
        pass
    return peers

async def _safe_close(writer: asyncio.StreamWriter):
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass

def _is_public_ip(ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_global
    except Exception:
        return False

# -----------------------
# Database
# -----------------------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS nodes (ip TEXT PRIMARY KEY, first_seen INTEGER)"
        )
        await db.commit()

async def insert_nodes(nodes: List[Tuple[str, int]]):
    ts = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        for ip, _ in nodes:
            await db.execute(
                "INSERT OR IGNORE INTO nodes(ip, first_seen) VALUES (?, ?)", (ip, ts)
            )
        await db.commit()

# -----------------------
# Core Peer Crawling
# -----------------------
async def crawl_peer(ip: str, port: int = BITCOIN_PORT) -> List[Tuple[str, int]]:
    peers = []
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), CONNECT_TIMEOUT)
    except Exception:
        return peers

    try:
        writer.write(make_message("version", build_version_payload(ip)))
        await writer.drain()

        got_verack = False
        start_time = time.time()
        while time.time() - start_time < READ_TIMEOUT:
            try:
                name, payload = await read_message(reader)
            except Exception:
                break
            if name == "version":
                writer.write(make_message("verack", b""))
                await writer.drain()
            elif name == "verack":
                got_verack = True
                break

        writer.write(make_message("getaddr", b""))
        await writer.drain()

        start_time = time.time()
        while time.time() - start_time < READ_TIMEOUT:
            try:
                name, payload = await read_message(reader)
            except Exception:
                break
            if name == "addr":
                peers.extend(parse_addr_payload(payload))
            if len(peers) >= 1000:
                break

    except Exception:
        pass
    finally:
        await _safe_close(writer)

    filtered = [(ip_, port_) for ip_, port_ in peers if _is_public_ip(ip_)]
    return list(dict.fromkeys(filtered))  # deduplicate

# -----------------------
# BFS Crawler Loop
# -----------------------
async def crawl(seed_ips: List[Tuple[str, int]], iterations: int = CRAWL_ITERATIONS):
    await init_db()
    seen = set()
    queue = seed_ips
    sem = asyncio.Semaphore(CONCURRENCY)

    for i in range(iterations):
        print(f"[INFO] Iteration {i+1}/{iterations} | Queue size: {len(queue)}")
        if not queue:
            break

        next_queue = []
        tasks = []

        async def sem_task(ip, port):
            async with sem:
                peers = await crawl_peer(ip, port)
                if peers:
                    await insert_nodes(peers)
                return peers

        for ip, port in queue:
            if ip not in seen:
                seen.add(ip)
                tasks.append(asyncio.create_task(sem_task(ip, port)))

        results = await asyncio.gather(*tasks)
        for peers in results:
            for p_ip, p_port in peers:
                if p_ip not in seen:
                    next_queue.append((p_ip, p_port))

        random.shuffle(next_queue)
        queue = next_queue[:2000]
        await asyncio.sleep(1)

    print("[INFO] Crawl finished.")

# -----------------------
# DNS Seed Resolution
# -----------------------
def resolve_dns_seeds(seeds: List[str]) -> List[Tuple[str, int]]:
    ips = []
    for domain in seeds:
        try:
            for info in socket.getaddrinfo(domain, BITCOIN_PORT, proto=socket.IPPROTO_TCP):
                ips.append((info[4][0], BITCOIN_PORT))
        except Exception:
            continue
    return list(dict.fromkeys(ips))

# -----------------------
# CLI
# -----------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Async Bitcoin P2P crawler (refactored).")
    parser.add_argument("--seeds", nargs="*", help="Seed IPs or hostnames.")
    parser.add_argument("--iterations", type=int, default=CRAWL_ITERATIONS)
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY)
    args = parser.parse_args()

    seedlist = []
    if args.seeds:
        for s in args.seeds:
            try:
                host, port = s.split(":")
                seedlist.append((host, int(port)))
            except ValueError:
                for info in socket.getaddrinfo(s, BITCOIN_PORT, proto=socket.IPPROTO_TCP):
                    seedlist.append((info[4][0], BITCOIN_PORT))
    else:
        seedlist = resolve_dns_seeds(SEED_DNS)

    if not seedlist:
        print("[WARN] No seeds resolved. Using fallback.")
        seedlist = [("93.184.216.34", BITCOIN_PORT)]

    CONCURRENCY = args.concurrency
    asyncio.run(crawl(seedlist, iterations=args.iterations))
