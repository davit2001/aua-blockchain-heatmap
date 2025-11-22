#!/bin/bash
# Start the frontend

cd "$(dirname "$0")/.."

echo "Installing frontend dependencies..."
yarn

echo "🚀 Starting Bitcoin Testnet Heatmap Frontend..."
echo "🌐 Open http://localhost:3000 in your browser"
yarn dev