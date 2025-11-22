#!/bin/bash
# Start the testnet backend API server

# Get absolute directory of this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Move to project root
cd "$SCRIPT_DIR/.." || exit

echo "🚀 Starting Bitcoin Testnet Heatmap Backend..."
echo "📊 Database: src/db/nodes.db"
echo "🌐 Server: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""


# Move into backend scripts folder
cd src/scripts || exit

# Activate venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "Run: python3 -m venv venv && source venv/bin/activate"
    exit 1
fi

# Start FastAPI with auto-reload
uvicorn app:app --reload
