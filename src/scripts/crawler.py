#!/usr/bin/env python3
"""
async Bitcoin P2P crawler (minimal, practical).

Features:
- Resolve DNS seeds for initial IPs
- Connect to peers (TCP / port 8333)
- Perform version/verack handshake
- Send getaddr and parse addr responses
- Store discovered IPs in SQLite using aiosqlite
- Concurrent and rate-limited using asyncio.Semaphore

Usage:
    python3 crawler.py

Files created:
    nodes.db  (SQLite) with table 'nodes(ip TEXT PRIMARY KEY, first_seen INTEGER)
"""

import asyncio
import aiosqlite
import socket
import struct
import time
import random
import hashlib
from typing import List, Tuple

# -----------------------
# Config
# -----------------------
MAINNET_MAGIC = b'\xf9\xbe\xb4\xd9'  # Bitcoin mainnet magic bytes
BITCOIN_PORT = 8333
PROTOCOL_VERSION = 70015
USER_AGENT = b"/BitcoinCrawler:0.1/"
DB_PATH = "nodes.db"
CONCURRENCY = 200           # number of concurrent connections
CONNECT_TIMEOUT = 8         # seconds to establish TCP connection
READ_TIMEOUT = 8            # seconds for network read operations
CRAWL_ITERATIONS = 3        # how many BFS layers (0 = seeds only)
SEED_DNS = [
    "seed.bitcoin.sipa.be",
    "dnsseed.bluematt.me",
    "seed.bitcoinstats.com",
    "seed.bitcoin.jonasschnelli.ch",
    "seed.bitcoin.jonasschnelli.ch",
    "seed.bitcoin.sprovoost.nl"
]

# -----------------------
# Util: varint encoding/decoding (Bitcoin style)
# -----------------------
def encode_varint(n: int) -> bytes:
    if n < 0xfd:
        return struct.pack("<B", n)
    elif n <= 0xffff:
        return b'\xfd' + struct.pack("<H", n)
    elif n <= 0xffffffff:
        return b'\xfe' + struct.pack("<I", n)
    else:
        return b'\xff' + struct.pack("<Q", n)

def decode_varint(b: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decode varint from bytes starting at offset.
    Returns (value, new_offset)."""
    prefix = b[offset]
    if prefix < 0xfd:
        return prefix, offset + 1
    if prefix == 0xfd:
        return struct.unpack_from("<H", b, offset + 1)[0], offset + 3
    if prefix == 0xfe:
        return struct.unpack_from("<I", b, offset + 1)[0], offset + 5
    return struct.unpack_from("<Q", b, offset + 1)[0], offset + 9

# -----------------------
# Build / parse Bitcoin P2P messages
# -----------------------
def sha256d(b: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()

def make_message(command: str, payload: bytes) -> bytes:
    # command -> ascii, padded to 12 bytes with \x00
    name = command.encode('ascii')
    name = name + b'\x00' * (12 - len(name))
    length = struct.pack("<I", len(payload))
    checksum = sha256d(payload)[:4]
    return MAINNET_MAGIC + name + length + checksum + payload

def ipv4_to_ipv6_packed(ipv4: str) -> bytes:
    # IPv4 mapped into IPv6: ::ffff:ipv4
    parts = list(map(int, ipv4.split('.')))
    return b'\x00' * 10 + b'\xff\xff' + bytes(parts)

def build_version_payload(peer_ip: str) -> bytes:
    # Construct a version payload using protocol spec:
    # version: int32, services: uint64, timestamp: int64,
    # addr_recv: services(8) + ipv6(16) + port(2 big-endian)
    # addr_from: same (we send zeros)
    # nonce: uint64, user_agent: var_str, start_height: int32, relay: bool (opt)
    version = struct.pack("<i", PROTOCOL_VERSION)
    services = struct.pack("<Q", 0)
    timestamp = struct.pack("<q", int(time.time()))
    # addr_recv
    addr_recv_services = struct.pack("<Q", 0)
    addr_recv_ip = ipv4_to_ipv6_packed(peer_ip)
    addr_recv_port = struct.pack(">H", BITCOIN_PORT)  # big-endian
    addr_recv = addr_recv_services + addr_recv_ip + addr_recv_port
    # addr_from: zeros
    addr_from = struct.pack("<Q", 0) + (b'\x00' * 16) + struct.pack(">H", BITCOIN_PORT)
    nonce = struct.pack("<Q", random.getrandbits(64))
    # user_agent as var_str
    ua = encode_varint(len(USER_AGENT)) + USER_AGENT
    start_height = struct.pack("<i", 0)
    # relay flag (1 byte) - include as 0 or 1 for nodes >=70001; we'll send 0
    relay = b'\x00'
    payload = version + services + timestamp + addr_recv + addr_from + nonce + ua + start_height + relay
    return payload

# -----------------------
# Parse incoming header/payload
# -----------------------
async def read_exact(reader: asyncio.StreamReader, n: int, timeout: int) -> bytes:
    """Read exactly n bytes or raise asyncio.TimeoutError / asyncio.IncompleteReadError"""
    data = await asyncio.wait_for(reader.readexactly(n), timeout)
    return data

async def read_message(reader: asyncio.StreamReader) -> Tuple[str, bytes]:
    # Read 24-byte header: magic(4) name(12) length(4) checksum(4)
    header = await asyncio.wait_for(reader.readexactly(24), READ_TIMEOUT)
    magic = header[:4]
    if magic != MAINNET_MAGIC:
        raise ValueError("Bad magic")
    name = header[4:16].rstrip(b'\x00').decode('ascii')
    length = struct.unpack("<I", header[16:20])[0]
    checksum = header[20:24]
    payload = b''
    if length:
        payload = await asyncio.wait_for(reader.readexactly(length), READ_TIMEOUT)
        if sha256d(payload)[:4] != checksum:
            # checksum mismatch but continue gracefully
            # raise ValueError("Checksum mismatch")
            pass
    return name, payload

# -----------------------
# Parse addr message payload
# -----------------------
def parse_addr_payload(payload: bytes) -> List[Tuple[str,int]]:
    """
    Parses addr payload and returns list of (ip, port).
    addr format: var_int count, then for each:
      - if timestamp included (>=70001): uint32 timestamp
      - uint64 services
      - 16 bytes IP (IPv6 or IPv4-mapped)
      - uint16 port (big-endian)
    """
    ip_list = []
    try:
        offset = 0
        count, offset = decode_varint(payload, offset)
        for _ in range(count):
            # If nodes are announced with timestamp (common), read it
            if len(payload) - offset >= 4:
                # read timestamp but we don't use it here
                _ts = struct.unpack_from("<I", payload, offset)[0]
                offset += 4
            # services
            _services = struct.unpack_from("<Q", payload, offset)[0]
            offset += 8
            ip_packed = payload[offset:offset+16]
            offset += 16
            port = struct.unpack_from(">H", payload, offset)[0]  # big-endian
            offset += 2
            # decode ip
            # if IPv4-mapped IPv6 (::ffff:xxxx)
            if ip_packed[:12] == b'\x00'*10 + b'\xff\xff':
                ipv4 = '.'.join(str(b) for b in ip_packed[12:16])
                ip_list.append((ipv4, port))
            else:
                # IPv6 literal - convert to a standard textual form (compact)
                try:
                    import ipaddress
                    ipv6 = str(ipaddress.IPv6Address(ip_packed))
                    ip_list.append((ipv6, port))
                except Exception:
                    continue
    except Exception:
        # parsing error -> return whatever collected
        return ip_list
    return ip_list

# -----------------------
# DB helpers
# -----------------------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS nodes(ip TEXT PRIMARY KEY, first_seen INTEGER)")
        await db.commit()

async def insert_nodes(nodes: List[Tuple[str,int]]):
    ts = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        for ip, _port in nodes:
            try:
                await db.execute("INSERT OR IGNORE INTO nodes(ip, first_seen) VALUES(?,?)", (ip, ts))
            except Exception:
                pass
        await db.commit()

# -----------------------
# Core: connect -> handshake -> getaddr -> parse -> return peers
# -----------------------
async def crawl_peer(ip: str, port: int = BITCOIN_PORT) -> List[Tuple[str,int]]:
    """Connect to a peer, handshake, send getaddr, collect peers."""
    peers_found = []
    try:
        # open connection
        fut = asyncio.open_connection(ip, port)
        reader, writer = await asyncio.wait_for(fut, timeout=CONNECT_TIMEOUT)
    except Exception:
        return peers_found

    try:
        # Send version
        payload = build_version_payload(ip)
        writer.write(make_message("version", payload))
        await writer.drain()

        # Wait for messages until we get verack (or timeout)
        got_verack = False
        start = time.time()
        # Loop reading until verack seen or timeout
        while time.time() - start < READ_TIMEOUT:
            try:
                name, payload = await read_message(reader)
            except Exception:
                break
            if name == "verack":
                got_verack = True
                break
            # Some peers reply with "version" first; respond by waiting for verack next
            # If we get "version", respond with verack by sending verack.
            if name == "version":
                # send verack
                writer.write(make_message("verack", b""))
                await writer.drain()
                # continue reading
                continue

        if not got_verack:
            # try to send verack anyway in case peer expects it
            try:
                writer.write(make_message("verack", b""))
                await writer.drain()
            except Exception:
                pass

        # Send getaddr
        writer.write(make_message("getaddr", b""))
        await writer.drain()

        # Read replies for a short window, collect addr messages
        start = time.time()
        while time.time() - start < READ_TIMEOUT:
            try:
                name, payload = await read_message(reader)
            except Exception:
                break
            if name == "addr":
                # parse and collect
                found = parse_addr_payload(payload)
                peers_found.extend(found)
            # optionally break early if many peers found
            if len(peers_found) >= 1000:
                break

    except Exception:
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    # filters: keep IPv4 only for now (or include IPv6 as desired)
    filtered = []
    for ipaddr, port in peers_found:
        # skip private/reserved IP ranges
        try:
            # quick filter on IPv4 dotted form
            if ipaddr.count('.') == 3:
                a,b,c,d = map(int, ipaddr.split('.'))
                # private ranges
                if a == 10 or (a == 172 and 16 <= b <= 31) or (a == 192 and b == 168) or a == 127:
                    continue
                filtered.append((ipaddr, port))
            else:
                # optionally include IPv6
                filtered.append((ipaddr, port))
        except Exception:
            continue
    # deduplicate
    uniq = list(dict.fromkeys(filtered))
    return uniq

# -----------------------
# High-level BFS crawler loop
# -----------------------
async def crawl(seed_ips: List[Tuple[str,int]], max_iterations: int = CRAWL_ITERATIONS):
    seen = set()
    queue = []
    # initialize queue
    for ip, port in seed_ips:
        queue.append((ip, port))
    sem = asyncio.Semaphore(CONCURRENCY)

    await init_db()

    for iteration in range(max_iterations):
        print(f"[+] Crawl iteration {iteration+1}/{max_iterations} - queue size: {len(queue)}")
        tasks = []
        next_queue = []
        async def sem_task(ip, port):
            async with sem:
                try:
                    peers = await crawl_peer(ip, port)
                    if peers:
                        await insert_nodes(peers)
                    return (ip, port, peers)
                except Exception as e:
                    return (ip, port, [])
        for ip, port in queue:
            if ip in seen:
                continue
            seen.add(ip)
            tasks.append(asyncio.create_task(sem_task(ip, port)))
        if not tasks:
            break
        results = await asyncio.gather(*tasks)
        for ip, port, peers in results:
            for p_ip, p_port in peers:
                if p_ip not in seen:
                    next_queue.append((p_ip, p_port))
        # make next queue unique and a manageable size
        # shuffle to avoid bias
        random.shuffle(next_queue)
        # limit how many new peers to pursue next iteration (politeness)
        queue = next_queue[:2000]
        # short pause between iterations
        await asyncio.sleep(1)
    print("[+] Crawl finished")

# -----------------------
# Resolve seeds to IPs
# -----------------------
def resolve_dns_seeds(seed_domains: List[str]) -> List[Tuple[str,int]]:
    ips = []
    for dom in seed_domains:
        try:
            infos = socket.getaddrinfo(dom, BITCOIN_PORT, proto=socket.IPPROTO_TCP)
            for info in infos:
                sockaddr = info[4]
                ip = sockaddr[0]
                ips.append((ip, BITCOIN_PORT))
        except Exception:
            continue
    # unique
    uniq = list(dict.fromkeys(ips))
    return uniq

# -----------------------
# CLI
# -----------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Async Bitcoin P2P crawler (getaddr-based).")
    parser.add_argument("--seeds", nargs="*", help="Seed IPs or hostnames (overrides default DNS seeds). Example: seed.bitcoin.sipa.be")
    parser.add_argument("--iterations", type=int, default=CRAWL_ITERATIONS, help="Number of BFS iterations (layers)")
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY, help="Concurrent TCP connections")
    args = parser.parse_args()

    if args.seeds:
        # parse seeds: allow ip:port or hostname
        seedlist = []
        for s in args.seeds:
            if ":" in s:
                host, port = s.split(":",1)
                seedlist.append((host, int(port)))
            else:
                # resolve hostname
                try:
                    infos = socket.getaddrinfo(s, BITCOIN_PORT, proto=socket.IPPROTO_TCP)
                    for info in infos:
                        seedlist.append((info[4][0], BITCOIN_PORT))
                except Exception:
                    pass
    else:
        seedlist = resolve_dns_seeds(SEED_DNS)
    # if no seeds resolved, fallback to a public seed IPs (some common DNS seeds resolve to many)
    if not seedlist:
        print("No seeds resolved via DNS seeds; using fallback hardcoded peers.")
        # some known nodes might be used as fallback (placeholders)
        seedlist = [("93.184.216.34", BITCOIN_PORT)]  # example only

    # set concurrency global
    CONCURRENCY = args.concurrency
    # run crawler
    asyncio.run(crawl(seedlist, max_iterations=args.iterations))

