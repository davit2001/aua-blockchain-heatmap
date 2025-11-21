#!/bin/bash
# Start the testnet backend API server

cd "$(dirname "$0")"

echo "🚀 Starting Bitcoin Testnet Heatmap Backend..."
echo "📊 Database: databases/bitcoin_testnet.db"
echo "🌐 Server: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""

python3 src/scripts/app_testnet.py

