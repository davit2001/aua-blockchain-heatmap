#!/usr/bin/env python3
"""
Create unified database schema for Bitcoin testnet peer discovery
This will store 100K+ crawled peers with geolocation data
"""
import sqlite3
import sys
import os

DB_PATH = "databases/bitcoin_testnet.db"

def create_database():
    """Create database with optimized schema for 100K+ peers"""
    
    # Create databases directory if it doesn't exist
    os.makedirs("databases", exist_ok=True)
    
    # Remove old database if it exists
    if os.path.exists(DB_PATH):
        print(f"⚠️  Removing existing database: {DB_PATH}")
        os.remove(DB_PATH)
    
    print(f"📊 Creating new database: {DB_PATH}")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table 1: Discovered Peers
    print("\n1️⃣  Creating 'peers' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS peers (
            ip TEXT PRIMARY KEY,
            port INTEGER NOT NULL,
            version TEXT,
            user_agent TEXT,
            services INTEGER DEFAULT 0,
            protocol_version INTEGER DEFAULT 0,
            first_discovered INTEGER NOT NULL,
            last_seen INTEGER NOT NULL,
            connection_type TEXT DEFAULT 'crawled',
            network TEXT DEFAULT 'testnet',
            contacted INTEGER DEFAULT 0,
            successful_handshake INTEGER DEFAULT 0
        )
    """)
    print("   ✅ Created 'peers' table")
    print("      - Stores IP, port, version info")
    print("      - Tracks discovery and contact status")
    print("      - Optimized for 100K+ entries")
    
    # Table 2: Geolocation Data
    print("\n2️⃣  Creating 'geolocations' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS geolocations (
            ip TEXT PRIMARY KEY,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            country TEXT,
            city TEXT,
            region TEXT,
            isp TEXT,
            last_updated INTEGER NOT NULL,
            FOREIGN KEY(ip) REFERENCES peers(ip) ON DELETE CASCADE
        )
    """)
    print("   ✅ Created 'geolocations' table")
    print("      - Stores latitude/longitude for heatmap")
    print("      - Links to peers via IP")
    print("      - Includes country, city, ISP info")
    
    # Table 3: Crawl Metadata
    print("\n3️⃣  Creating 'crawl_metadata' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawl_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crawl_date INTEGER NOT NULL,
            total_peers_discovered INTEGER DEFAULT 0,
            total_peers_contacted INTEGER DEFAULT 0,
            total_geolocated INTEGER DEFAULT 0,
            network TEXT DEFAULT 'testnet',
            crawl_duration_seconds INTEGER DEFAULT 0,
            seed_peers_count INTEGER DEFAULT 0,
            iterations_completed INTEGER DEFAULT 0,
            notes TEXT
        )
    """)
    print("   ✅ Created 'crawl_metadata' table")
    print("      - Tracks crawl statistics")
    print("      - Useful for research/analysis")
    
    # Create indexes for performance
    print("\n4️⃣  Creating indexes for fast queries...")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_peers_last_seen ON peers(last_seen DESC)")
    print("   ✅ Index on peers.last_seen")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_peers_contacted ON peers(contacted)")
    print("   ✅ Index on peers.contacted")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_peers_network ON peers(network)")
    print("   ✅ Index on peers.network")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_geolocations_ip ON geolocations(ip)")
    print("   ✅ Index on geolocations.ip")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_geolocations_country ON geolocations(country)")
    print("   ✅ Index on geolocations.country")
    
    # Commit and verify
    conn.commit()
    
    # Verify tables exist
    print("\n5️⃣  Verifying database structure...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ['peers', 'geolocations', 'crawl_metadata']
    for table in expected_tables:
        if table in tables:
            print(f"   ✅ Table '{table}' created successfully")
        else:
            print(f"   ❌ Table '{table}' missing!")
            return False
    
    # Get database size
    db_size = os.path.getsize(DB_PATH)
    print(f"\n📦 Database size: {db_size:,} bytes ({db_size / 1024:.2f} KB)")
    
    # Display schema
    print("\n" + "=" * 70)
    print("✅ DATABASE CREATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\n📁 Location: {os.path.abspath(DB_PATH)}")
    print("\n📊 Schema Summary:")
    print("   - peers: Stores 100K+ discovered peer nodes")
    print("   - geolocations: Lat/lon coordinates for heatmap")
    print("   - crawl_metadata: Statistics and tracking")
    print("\n🚀 Next Step: Run the crawler to populate with real testnet data!")
    print("=" * 70)
    
    conn.close()
    return True

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)

