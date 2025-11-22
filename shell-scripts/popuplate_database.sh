#!/bin/bash
###############################################################################
# TESTNET DATABASE POPULATION SCRIPT
# This script will:
# 1. Test Bitcoin Core testnet connection
# 2. Create the database schema
# 3. Crawl 100K+ testnet peers
# 4. Geolocate all discovered peers
# 5. Display final statistics
###############################################################################

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════════════════"
echo "  🚀 BITCOIN TESTNET DATABASE POPULATION"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "This will discover 100K+ real testnet peers and geolocate them."
echo "Estimated time: 30-60 minutes"
echo ""
echo "Prerequisites:"
echo "  ✅ Bitcoin-Qt running in TESTNET mode"
echo "  ✅ RPC server enabled (port 18334)"
echo "  ✅ Internet connection for geolocation"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Step 1: Test Bitcoin Core connection
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Testing Bitcoin Core Testnet Connection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 test_testnet_connection.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Bitcoin Core connection test failed!"
    echo "   Please make sure Bitcoin-Qt is running in testnet mode with RPC enabled."
    echo "   Then restart Bitcoin-Qt and run this script again."
    exit 1
fi

echo ""
echo "✅ Bitcoin Core connection successful!"
echo ""
read -p "Press ENTER to continue with database creation..."

# Step 3: Crawl testnet peers
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Crawling Testnet P2P Network (Target: 100K peers)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  This will take 20-40 minutes depending on network conditions."
echo "   You can press Ctrl+C to stop if needed (progress is saved)."
echo ""

python3 src/scripts/crawler.py
if [ $? -ne 0 ]; then
    echo "⚠️  Crawl encountered errors, but may have discovered some peers."
    echo "   Continuing with geolocation..."
fi

# Step 4: Geolocate peers
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4: Geolocating Discovered Peers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 src/scripts/geolocate_nodes.py
if [ $? -ne 0 ]; then
    echo "⚠️  Geolocation encountered errors."
fi

# Final summary
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "🎉 TESTNET DATABASE POPULATION COMPLETE!"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "Database location: databases/bitcoin_testnet.db"
echo ""
echo "Next steps:"
echo "  1. Verify database contents"
echo "  2. Commit database to Git"
echo "  3. Build backend API to serve data"
echo "  4. Update frontend to display heatmap"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"