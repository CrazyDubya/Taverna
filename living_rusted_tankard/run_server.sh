#!/bin/bash
# Comprehensive server launcher for The Living Rusted Tankard

echo "🍺 The Living Rusted Tankard Server Launcher"
echo "==========================================="

# Kill any existing processes on our ports
echo "🔍 Checking for existing processes..."
for port in 8000 8001 8080 8888; do
    lsof -ti:$port | xargs kill -9 2>/dev/null && echo "Killed process on port $port"
done

# Change to script directory
cd "$(dirname "$0")"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to test server connectivity
test_server() {
    local port=$1
    sleep 3
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/health" | grep -q "200\|404"; then
        echo "✅ Server is responding on port $port!"
        echo "🌐 Open http://localhost:$port in your browser"
        return 0
    else
        echo "❌ Server not responding on port $port"
        return 1
    fi
}

# Try different methods to run the server
echo -e "\n🚀 Attempting to start server..."

# Method 1: Try with poetry
if command_exists poetry; then
    echo "📦 Trying with Poetry..."
    
    # First try the simple server
    echo "Starting simple server on port 8888..."
    poetry run python simple_server.py --port 8888 &
    SERVER_PID=$!
    
    if test_server 8888; then
        echo -e "\n✅ SUCCESS! Server running at http://localhost:8888"
        echo "Press Ctrl+C to stop"
        wait $SERVER_PID
        exit 0
    else
        kill $SERVER_PID 2>/dev/null
    fi
fi

# Method 2: Try with python3
if command_exists python3; then
    echo "🐍 Trying with python3..."
    
    # Check if we have required packages
    if python3 -c "import fastapi, uvicorn" 2>/dev/null; then
        echo "Starting with python3..."
        python3 simple_server.py &
        SERVER_PID=$!
        
        if test_server 8080; then
            echo -e "\n✅ SUCCESS! Server running at http://localhost:8080"
            echo "Press Ctrl+C to stop"
            wait $SERVER_PID
            exit 0
        else
            kill $SERVER_PID 2>/dev/null
        fi
    else
        echo "❌ Missing dependencies for python3"
    fi
fi

# Method 3: Try with python3.10
if command_exists python3.10; then
    echo "🐍 Trying with python3.10..."
    python3.10 simple_server.py &
    SERVER_PID=$!
    
    if test_server 8080; then
        echo -e "\n✅ SUCCESS! Server running at http://localhost:8080"
        echo "Press Ctrl+C to stop"
        wait $SERVER_PID
        exit 0
    else
        kill $SERVER_PID 2>/dev/null
    fi
fi

# If we get here, nothing worked
echo -e "\n❌ Could not start server!"
echo "Please install dependencies:"
echo "  1. Install Poetry: curl -sSL https://install.python-poetry.org | python3 -"
echo "  2. Run: poetry install"
echo "  3. Try again: ./run_server.sh"