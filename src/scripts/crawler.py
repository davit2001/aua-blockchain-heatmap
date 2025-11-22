#!/usr/bin/env python3
"""
Bitcoin TESTNET P2P Network Crawler
Discovers 100K+ peers by crawling the testnet P2P network
Uses YOUR Bitcoin Core testnet node as starting point
"""
import asyncio
import socket
import struct
import hashlib
import time
import random
import sqlite3
from typing import Set, List, Tuple, Optional
import requests
from requests.auth import HTTPBasicAuth
import json
import os

# Bitcoin TESTNET Protocol Constants
MAGIC_BYTES = b'\x0b\x11\x09\x07'  # Testnet magic bytes
PROTOCOL_VERSION = 70015
USER_AGENT = "/BitcoinTestnetCrawler:1.0/"

# Crawl Configuration
TARGET_PEERS = 100000  # Target: 100K unique peers
MAX_QUEUE_SIZE = 10000  # Keep queue manageable
CONCURRENCY = 500  # Parallel connections (aggressive for testnet)
CONNECT_TIMEOUT = 5  # Connection timeout
READ_TIMEOUT = 5  # Read timeout
MAX_ITERATIONS = 100  # More iterations for 100K peers

# Database
DB_PATH = "db/nodes.db"
print("DB path:", DB_PATH)
# Bitcoin Core RPC Configuration (Testnet)
RPC_USER = "bitcoinrpc"
RPC_PASSWORD = "your_secure_password_here_12345"
RPC_HOST = "127.0.0.1"
RPC_PORT = 18332  # Testnet RPC port (default)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "db", "nodes.db")
DB_PATH = os.path.abspath(DB_PATH)

# Statistics
stats = {
    "total_discovered": 0,
    "total_contacted": 0,
    "successful_handshakes": 0,
    "failed_connections": 0,
    "peers_per_iteration": [],
    "start_time": 0
}


def bitcoin_rpc_call(method: str, params: List = None) -> Optional[dict]:
    """Make an RPC call to Bitcoin Core to get initial seeds"""
    if params is None:
        params = []

    url = f"http://{RPC_HOST}:{RPC_PORT}/"
    headers = {"content-type": "text/plain"}
    payload = {
        "jsonrpc": "1.0",
        "id": "crawler",
        "method": method,
        "params": params
    }

    try:
        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers,
            auth=HTTPBasicAuth(RPC_USER, RPC_PASSWORD),
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        if "error" in result and result["error"]:
            print(f"❌ RPC Error: {result['error']}")
            return None

        return result.get("result")
    except Exception as e:
        print(f"⚠️  RPC call failed: {e}")
        return None


def get_seed_peers_from_bitcoin_core() -> List[Tuple[str, int]]:
    """Fetch initial seed peers from YOUR Bitcoin Core testnet node"""
    print("🔍 Fetching seed peers from YOUR Bitcoin Core testnet node...")

    peers_info = bitcoin_rpc_call("getpeerinfo")
    if not peers_info:
        print("⚠️  Could not fetch peers from Bitcoin Core")
        print("   Using fallback testnet DNS seeds...")
        # Fallback to testnet DNS seeds
        return [
            ("testnet-seed.bitcoin.jonasschnelli.ch", 18333),
            ("seed.tbtc.petertodd.org", 18333),
            ("testnet-seed.bluematt.me", 18333),
        ]

    seed_peers = []
    for peer in peers_info:
        addr = peer.get('addr', '')
        if ':' in addr:
            try:
                ip, port = addr.rsplit(':', 1)
                port = int(port)
                # Skip IPv6 for now (focus on IPv4)
                if ':' not in ip:
                    seed_peers.append((ip, port))
            except ValueError:
                continue

    print(f"✅ Found {len(seed_peers)} seed peers from Bitcoin Core")
    for i, (ip, port) in enumerate(seed_peers[:5], 1):
        print(f"   {i}. {ip}:{port}")
    if len(seed_peers) > 5:
        print(f"   ... and {len(seed_peers) - 5} more")

    return seed_peers if seed_peers else [
        ("testnet-seed.bitcoin.jonasschnelli.ch", 18333),
    ]


def _is_public_ipv4(ip: str) -> bool:
    """Check if IP is public IPv4 (not private/local)"""
    try:
        # Skip IPv6
        if ':' in ip:
            return False

        parts = [int(p) for p in ip.split('.')]
        if len(parts) != 4:
            return False

        # Private ranges
        if parts[0] == 10:
            return False
        if parts[0] == 172 and 16 <= parts[1] <= 31:
            return False
        if parts[0] == 192 and parts[1] == 168:
            return False
        if parts[0] == 127:
            return False
        if parts[0] == 0:
            return False
        if parts[0] >= 224:  # Multicast and reserved
            return False

        return True
    except:
        return False


def encode_varint(n: int) -> bytes:
    """Encode variable-length integer"""
    if n < 0xfd:
        return bytes([n])
    elif n <= 0xffff:
        return b'\xfd' + struct.pack('<H', n)
    elif n <= 0xffffffff:
        return b'\xfe' + struct.pack('<I', n)
    else:
        return b'\xff' + struct.pack('<Q', n)


def decode_varint(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decode variable-length integer, return (value, new_offset)"""
    if offset >= len(data):
        return 0, offset

    first = data[offset]
    if first < 0xfd:
        return first, offset + 1
    elif first == 0xfd:
        if offset + 3 > len(data):
            return 0, offset
        return struct.unpack('<H', data[offset+1:offset+3])[0], offset + 3
    elif first == 0xfe:
        if offset + 5 > len(data):
            return 0, offset
        return struct.unpack('<I', data[offset+1:offset+5])[0], offset + 5
    else:
        if offset + 9 > len(data):
            return 0, offset
        return struct.unpack('<Q', data[offset+1:offset+9])[0], offset + 9


def sha256d(data: bytes) -> bytes:
    """Double SHA256 hash"""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def create_version_message(dest_ip: str, dest_port: int) -> bytes:
    """Create Bitcoin VERSION message for testnet"""
    payload = struct.pack('<i', PROTOCOL_VERSION)  # version
    payload += struct.pack('<Q', 0)  # services
    payload += struct.pack('<q', int(time.time()))  # timestamp

    # addr_recv (destination)
    payload += struct.pack('<Q', 0)  # services
    try:
        payload += b'\x00' * 10 + b'\xff\xff' + socket.inet_aton(dest_ip)
    except:
        payload += b'\x00' * 16
    payload += struct.pack('>H', dest_port)

    # addr_from (us)
    payload += struct.pack('<Q', 0)  # services
    payload += b'\x00' * 16  # IPv6 (zeros)
    payload += struct.pack('>H', 0)  # port

    payload += struct.pack('<Q', random.getrandbits(64))  # nonce
    payload += encode_varint(len(USER_AGENT)) + USER_AGENT.encode()
    payload += struct.pack('<i', 0)  # start_height
    payload += bytes([1])  # relay

    # Header
    header = MAGIC_BYTES
    header += b'version\x00\x00\x00\x00\x00'
    header += struct.pack('<I', len(payload))
    header += sha256d(payload)[:4]

    return header + payload


def create_verack_message() -> bytes:
    """Create Bitcoin VERACK message"""
    return MAGIC_BYTES + b'verack\x00\x00\x00\x00\x00\x00' + b'\x00\x00\x00\x00' + sha256d(b'')[:4]


def create_getaddr_message() -> bytes:
    """Create Bitcoin GETADDR message to request peer list"""
    return MAGIC_BYTES + b'getaddr\x00\x00\x00\x00\x00' + b'\x00\x00\x00\x00' + sha256d(b'')[:4]


def parse_addr_payload(payload: bytes) -> List[Tuple[str, int]]:
    """Parse ADDR message payload to extract peer addresses"""
    try:
        count, offset = decode_varint(payload, 0)
        peers = []

        for _ in range(min(count, 1000)):  # Limit to 1000 addresses per message
            if offset + 30 > len(payload):
                break

            # Skip timestamp (4 bytes) and services (8 bytes)
            offset += 12

            # IP address (16 bytes)
            ip_bytes = payload[offset:offset+16]
            offset += 16

            # Port (2 bytes, big-endian)
            if offset + 2 > len(payload):
                break
            port = struct.unpack('>H', payload[offset:offset+2])[0]
            offset += 2

            # Check if IPv4-mapped IPv6
            if ip_bytes[:12] == b'\x00' * 10 + b'\xff\xff':
                ip = socket.inet_ntoa(ip_bytes[12:16])
                if _is_public_ipv4(ip):
                    peers.append((ip, port))

        return peers
    except Exception:
        return []


async def handshake_and_get_peers(ip: str, port: int) -> Tuple[bool, List[Tuple[str, int]], Optional[str]]:
    """Connect to a peer, handshake, and request their peer list"""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=CONNECT_TIMEOUT
        )

        # Send VERSION
        writer.write(create_version_message(ip, port))
        await writer.drain()

        # Wait for VERSION and VERACK
        received_version = False
        received_verack = False
        user_agent = None

        for _ in range(10):  # Max 10 messages
            try:
                header = await asyncio.wait_for(reader.readexactly(24), timeout=READ_TIMEOUT)

                # Verify magic bytes
                if header[:4] != MAGIC_BYTES:
                    break

                payload_len = struct.unpack('<I', header[16:20])[0]

                if payload_len > 5_000_000:  # Sanity check
                    break

                if payload_len > 0:
                    payload = await asyncio.wait_for(reader.readexactly(payload_len), timeout=READ_TIMEOUT)
                else:
                    payload = b''

                command = header[4:16].rstrip(b'\x00').decode('ascii', errors='ignore')

                if command == 'version':
                    received_version = True
                    # Extract user agent from version message
                    try:
                        if len(payload) > 80:
                            ua_len, offset = decode_varint(payload, 80)
                            if ua_len > 0 and ua_len < 256:
                                user_agent = payload[offset:offset+ua_len].decode('utf-8', errors='ignore')
                    except:
                        pass
                    writer.write(create_verack_message())
                    await writer.drain()
                elif command == 'verack':
                    received_verack = True

                if received_version and received_verack:
                    break
            except:
                break

        if not (received_version and received_verack):
            writer.close()
            await writer.wait_closed()
            return False, [], None

        # Send GETADDR
        writer.write(create_getaddr_message())
        await writer.drain()

        # Wait for ADDR response
        peers = []
        for _ in range(5):  # Max 5 messages
            try:
                header = await asyncio.wait_for(reader.readexactly(24), timeout=READ_TIMEOUT)

                if header[:4] != MAGIC_BYTES:
                    break

                payload_len = struct.unpack('<I', header[16:20])[0]

                if payload_len > 5_000_000:
                    break

                if payload_len > 0:
                    payload = await asyncio.wait_for(reader.readexactly(payload_len), timeout=READ_TIMEOUT)
                    command = header[4:16].rstrip(b'\x00').decode('ascii', errors='ignore')

                    if command == 'addr':
                        new_peers = parse_addr_payload(payload)
                        peers.extend(new_peers)
                        if new_peers:  # Got addresses, we're done
                            break
            except:
                break

        writer.close()
        await writer.wait_closed()
        return True, peers, user_agent

    except Exception:
        return False, [], None


def save_peer_to_db(ip: str, port: int, user_agent: Optional[str], contacted: bool, successful: bool):
    """Save a single peer to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    current_time = int(time.time())

    try:
        cursor.execute("""
            INSERT OR REPLACE INTO peers
            (ip, port, user_agent, first_discovered, last_seen, contacted, successful_handshake, network)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'testnet')
        """, (ip, port, user_agent or 'unknown', current_time, current_time, 1 if contacted else 0, 1 if successful else 0))

        conn.commit()
    except Exception as e:
        print(f"⚠️  DB error: {e}")
    finally:
        conn.close()


def get_peer_count() -> Tuple[int, int]:
    """Get count of total and contacted peers"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM peers")
    (total,) = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM peers WHERE contacted = 1")
    (contacted,) = cursor.fetchone()

    conn.close()
    return total, contacted


def get_uncontacted_peers(limit: int = 1000) -> List[Tuple[str, int]]:
    """Get uncontacted peers from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ip, port FROM peers
        WHERE contacted = 0
        ORDER BY first_discovered ASC
        LIMIT ?
    """, (limit,))

    peers = [(row[0], row[1]) for row in cursor.fetchall()]
    conn.close()
    return peers

def init_db():
    """Initialize the SQLite database with required tables for peers and crawl metadata."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create peers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS peers (
            ip TEXT PRIMARY KEY,
            port INTEGER NOT NULL,
            user_agent TEXT,
            first_discovered INTEGER,
            last_seen INTEGER,
            contacted INTEGER,
            successful_handshake INTEGER,
            network TEXT
        );
    """)

    # Create crawl_metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawl_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crawl_date INTEGER,
            total_peers_discovered INTEGER,
            total_peers_contacted INTEGER,
            network TEXT,
            crawl_duration_seconds INTEGER,
            iterations_completed INTEGER
        );
    """)

    conn.commit()
    conn.close()
    print(f"📚 Database initialized at {DB_PATH}")

async def crawl():
    """Main crawl function - discover 100K testnet peers"""
    print("=" * 70)
    print("🕷️  BITCOIN TESTNET P2P NETWORK CRAWLER")
    print("=" * 70)
    print(f"🎯 Target: {TARGET_PEERS:,} unique testnet peers")
    print(f"⚡ Concurrency: {CONCURRENCY} parallel connections")
    print(f"🔄 Max iterations: {MAX_ITERATIONS}")
    print(f"💾 Database: {DB_PATH}")
    print("=" * 70)

    stats["start_time"] = time.time()

    # Get seed peers from Bitcoin Core
    seed_peers = get_seed_peers_from_bitcoin_core()

    # Save seed peers to database
    print(f"\n💾 Saving {len(seed_peers)} seed peers to database...")
    for ip, port in seed_peers:
        save_peer_to_db(ip, port, None, False, False)

    visited: Set[str] = set()

    for iteration in range(MAX_ITERATIONS):
        total_count, contacted_count = get_peer_count()

        print(f"\n{'='*70}")
        print(f"🔄 ITERATION {iteration + 1}/{MAX_ITERATIONS}")
        print(f"{'='*70}")
        print(f"📊 Total discovered: {total_count:,} peers")
        print(f"✅ Contacted: {contacted_count:,} peers")
        print(f"🎯 Progress: {(total_count/TARGET_PEERS)*100:.1f}% of target")

        if total_count >= TARGET_PEERS:
            print(f"\n🎉 TARGET REACHED! Discovered {total_count:,} peers!")
            break

        # Get uncontacted peers
        queue = get_uncontacted_peers(CONCURRENCY)

        if not queue:
            print("⚠️  No more uncontacted peers in queue")
            break

        print(f"📋 Processing {len(queue)} peers this iteration...")

        # Process peers in parallel
        tasks = []
        for ip, port in queue:
            if ip not in visited:
                visited.add(ip)
                tasks.append(handshake_and_get_peers(ip, port))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        new_peers_count = 0
        successful_count = 0

        for i, result in enumerate(results):
            if i >= len(queue):
                break

            ip, port = queue[i]

            if isinstance(result, tuple) and len(result) == 3:
                success, new_peers, user_agent = result

                # Update contacted peer
                save_peer_to_db(ip, port, user_agent, True, success)
                stats["total_contacted"] += 1

                if success:
                    stats["successful_handshakes"] += 1
                    successful_count += 1

                    # Save newly discovered peers
                    for peer_ip, peer_port in new_peers:
                        if peer_ip not in visited:
                            save_peer_to_db(peer_ip, peer_port, None, False, False)
                            new_peers_count += 1
                            stats["total_discovered"] += 1
                else:
                    stats["failed_connections"] += 1
            else:
                # Failed connection
                save_peer_to_db(ip, port, None, True, False)
                stats["total_contacted"] += 1
                stats["failed_connections"] += 1

        stats["peers_per_iteration"].append(new_peers_count)

        elapsed = time.time() - stats["start_time"]
        print(f"✨ Discovered {new_peers_count:,} new peers")
        print(f"✅ Successful handshakes: {successful_count}/{len(queue)}")
        print(f"⏱️  Elapsed time: {elapsed/60:.1f} minutes")
        print(f"📈 Discovery rate: {total_count/(elapsed/60):.0f} peers/minute")

        # Small delay between iterations
        await asyncio.sleep(0.5)

    # Final statistics
    total_count, contacted_count = get_peer_count()
    elapsed = time.time() - stats["start_time"]

    print("\n" + "=" * 70)
    print("🎉 CRAWL COMPLETE!")
    print("=" * 70)
    print(f"✅ Total discovered peers: {total_count:,}")
    print(f"📞 Total contacted peers: {contacted_count:,}")
    print(f"🤝 Successful handshakes: {stats['successful_handshakes']:,}")
    print(f"❌ Failed connections: {stats['failed_connections']:,}")
    print(f"⏱️  Total time: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
    print(f"📈 Average rate: {total_count/(elapsed/60):.0f} peers/minute")
    print(f"💾 Database: {DB_PATH}")
    print("=" * 70)

    # Save crawl metadata
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO crawl_metadata
        (crawl_date, total_peers_discovered, total_peers_contacted, network, crawl_duration_seconds, iterations_completed)
        VALUES (?, ?, ?, 'testnet', ?, ?)
    """, (int(time.time()), total_count, contacted_count, int(elapsed), iteration + 1))
    conn.commit()
    conn.close()

    print("\n🚀 Next step: Run geolocation script to map all peers!")
    print("=" * 70)


if __name__ == "__main__":
    init_db()
    print("\n⚠️  IMPORTANT: Make sure Bitcoin-Qt is running in TESTNET mode!")
    print("   Press Ctrl+C to cancel, or wait 3 seconds to start...\n")
    time.sleep(3)

    asyncio.run(crawl())

