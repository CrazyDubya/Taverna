#!/bin/bash

echo "🍺 Starting The Living Rusted Tankard Server (Background Mode)"
echo "=================================================="

# Kill any existing Python servers
pkill -f "standalone_game.py" 2>/dev/null
pkill -f "python.*8888" 2>/dev/null
sleep 1

# Start the server in background with nohup
cd "$(dirname "$0")"
nohup python3 standalone_game.py > server.log 2>&1 &
SERVER_PID=$!

echo "✅ Server started with PID: $SERVER_PID"
sleep 2

# Check if it's running
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ Server is running successfully!"
    echo "📍 Open your browser to: http://localhost:8888"
    echo ""
    echo "To stop the server later, run:"
    echo "  kill $SERVER_PID"
    echo ""
    echo "Server logs are in: server.log"
else
    echo "❌ Server failed to start"
    echo "Check server.log for errors"
fi