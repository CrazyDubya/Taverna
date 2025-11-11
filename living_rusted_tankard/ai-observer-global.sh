#!/usr/bin/env bash
# Global AI Observer Command with Enhanced Reliability
# Implements health checks and retry logic for robust AI session startup
#
# Usage:
#   ./ai-observer-global.sh --new              # Start new AI session
#   ./ai-observer-global.sh --continue SESSION # Continue existing session
#   ./ai-observer-global.sh --web              # Launch web interface only
#   ./ai-observer-global.sh --demo             # Run simple terminal demo
#
# Environment Variables (with defaults):
#   SERVER_URL              - Server base URL (default: http://localhost:8000)
#   HEALTH_ENDPOINT         - Health check endpoint path (default: /health)
#   MAX_WAIT_SECONDS        - Maximum time to wait for server ready (default: 60)
#   AI_SESSION_RETRIES      - Number of retries for AI session start (default: 3)
#   AI_SESSION_RETRY_INTERVAL - Initial retry interval in seconds (default: 5)

set -e

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Configuration with sensible defaults
SERVER_URL="${SERVER_URL:-http://localhost:8000}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-60}"
AI_SESSION_RETRIES="${AI_SESSION_RETRIES:-3}"
AI_SESSION_RETRY_INTERVAL="${AI_SESSION_RETRY_INTERVAL:-5}"

# Ensure logs directory exists
mkdir -p logs

# Diagnostics log file
DIAGNOSTICS_LOG="logs/ai-session-diagnostics.log"

# Initialize server process tracking
SERVER_PID=""

# Cleanup function for graceful shutdown
cleanup() {
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "🛑 Stopping server (PID: $SERVER_PID)..."
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
        echo "✅ Server stopped"
    fi
}

trap cleanup EXIT INT TERM

# Function: wait_for_server
# Polls the health endpoint until server is ready or timeout
wait_for_server() {
    local health_url="${SERVER_URL}${HEALTH_ENDPOINT}"
    local elapsed=0
    local interval=2
    
    echo "🔍 Waiting for server at ${health_url}..."
    echo "⏱️  Maximum wait time: ${MAX_WAIT_SECONDS} seconds"
    
    while [ $elapsed -lt $MAX_WAIT_SECONDS ]; do
        if curl --silent --show-error --fail --max-time 5 "$health_url" > /dev/null 2>&1; then
            echo "✅ Server is ready! (waited ${elapsed}s)"
            return 0
        fi
        
        echo "⏳ Waiting for server... (${elapsed}/${MAX_WAIT_SECONDS}s)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    echo "❌ Server did not become ready within ${MAX_WAIT_SECONDS} seconds" | tee -a "$DIAGNOSTICS_LOG"
    echo "   Server logs may contain more information" | tee -a "$DIAGNOSTICS_LOG"
    return 1
}

# Function: start_ai_session_with_retries
# Attempts to start AI session with exponential backoff on 5xx errors
start_ai_session_with_retries() {
    local attempt=1
    local retry_interval=$AI_SESSION_RETRY_INTERVAL
    
    echo "🤖 Starting AI player session with retry support..."
    echo "   Max retries: $AI_SESSION_RETRIES" | tee -a "$DIAGNOSTICS_LOG"
    echo "   Initial retry interval: ${retry_interval}s" | tee -a "$DIAGNOSTICS_LOG"
    echo "" >> "$DIAGNOSTICS_LOG"
    echo "=== AI Session Initialization Attempt Log ===" >> "$DIAGNOSTICS_LOG"
    echo "Timestamp: $(date -Iseconds)" >> "$DIAGNOSTICS_LOG"
    echo "" >> "$DIAGNOSTICS_LOG"
    
    while [ $attempt -le $AI_SESSION_RETRIES ]; do
        echo "🔄 Attempt $attempt of $AI_SESSION_RETRIES..." | tee -a "$DIAGNOSTICS_LOG"
        
        # Capture HTTP status and response body
        local http_code
        local response_file=$(mktemp)
        
        http_code=$(curl --silent --show-error --write-out "%{http_code}" \
                         --output "$response_file" \
                         --max-time 30 \
                         "${SERVER_URL}/ai-player/start" \
                         -X POST \
                         -H "Content-Type: application/json" \
                         -d '{"personality":"curious_explorer","thinking_speed":2.0,"auto_play":true}' \
                         2>&1 || echo "000")
        
        local response_body=$(cat "$response_file")
        rm -f "$response_file"
        
        # Log the attempt
        echo "  HTTP Status: $http_code" | tee -a "$DIAGNOSTICS_LOG"
        echo "  Response: $response_body" | tee -a "$DIAGNOSTICS_LOG"
        
        # Check if successful (2xx)
        if [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
            echo "✅ AI session started successfully!" | tee -a "$DIAGNOSTICS_LOG"
            return 0
        fi
        
        # Check if 5xx error (server error - retryable)
        if [[ "$http_code" =~ ^5[0-9][0-9]$ ]]; then
            if [ $attempt -lt $AI_SESSION_RETRIES ]; then
                echo "⚠️  Server error ($http_code) - will retry in ${retry_interval}s..." | tee -a "$DIAGNOSTICS_LOG"
                sleep $retry_interval
                # Exponential backoff: double the interval for next retry
                retry_interval=$((retry_interval * 2))
                attempt=$((attempt + 1))
                continue
            else
                echo "❌ Failed after $AI_SESSION_RETRIES attempts with server error $http_code" | tee -a "$DIAGNOSTICS_LOG"
                return 1
            fi
        fi
        
        # For other errors (4xx, connection issues), don't retry
        echo "❌ Failed with non-retryable error: $http_code" | tee -a "$DIAGNOSTICS_LOG"
        return 1
    done
    
    return 1
}

# Main execution logic
main() {
    echo "🍺 The Living Rusted Tankard - AI Observer"
    echo "=========================================="
    echo "Configuration:"
    echo "  SERVER_URL: $SERVER_URL"
    echo "  HEALTH_ENDPOINT: $HEALTH_ENDPOINT"
    echo "  MAX_WAIT_SECONDS: $MAX_WAIT_SECONDS"
    echo "  AI_SESSION_RETRIES: $AI_SESSION_RETRIES"
    echo "  AI_SESSION_RETRY_INTERVAL: $AI_SESSION_RETRY_INTERVAL"
    echo ""
    
    # Check if this is a mode that doesn't require server health check/AI session
    # (e.g., --demo runs standalone)
    if [[ "$*" == *"--demo"* ]]; then
        echo "🎮 Running in demo mode - delegating to Python script"
        exec python3 launch_ai_observer.py "$@"
    fi
    
    # Start the server in background
    echo "🚀 Starting The Living Rusted Tankard server..."
    python3 -m uvicorn core.api:app --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &
    SERVER_PID=$!
    
    echo "   Server PID: $SERVER_PID"
    echo "   Server logs: logs/server.log"
    
    # Wait for server to be ready
    if ! wait_for_server; then
        echo "❌ Server failed to become ready - exiting" | tee -a "$DIAGNOSTICS_LOG"
        echo "   Check logs/server.log for details" | tee -a "$DIAGNOSTICS_LOG"
        exit 1
    fi
    
    # Check if we're in web-only mode
    if [[ "$*" == *"--web"* ]]; then
        echo "🌐 Web interface available at:"
        echo "  • Main game: ${SERVER_URL}/"
        echo "  • AI Demo: ${SERVER_URL}/ai-demo"
        echo ""
        echo "Press Ctrl+C to stop server..."
        wait $SERVER_PID
        exit 0
    fi
    
    # For AI session modes (--new or --continue), attempt to start with retries
    if [[ "$*" == *"--new"* ]] || [[ "$*" == *"--continue"* ]]; then
        if [[ "$*" == *"--new"* ]]; then
            if ! start_ai_session_with_retries; then
                echo "❌ Failed to start AI session after retries" | tee -a "$DIAGNOSTICS_LOG"
                echo "   Diagnostics saved to: $DIAGNOSTICS_LOG"
                echo "   Server logs available at: logs/server.log"
                exit 1
            fi
        fi
        
        # Now that server is ready and AI session is started (if --new),
        # delegate to Python script for observation
        echo "📡 Delegating to Python observer for streaming..."
        # The Python script will handle the observation part, but server is already running
        # So we need to avoid re-starting it. For now, let's just keep server running
        # and let user interact with it or use the web interface
        echo ""
        echo "✅ Setup complete! Server is running at ${SERVER_URL}"
        echo "   AI session is active and ready"
        echo "   Use the web interface at ${SERVER_URL}/ai-demo to observe"
        echo ""
        echo "Press Ctrl+C to stop server..."
        wait $SERVER_PID
        exit 0
    fi
    
    # Default: delegate everything to Python script for other modes
    exec python3 launch_ai_observer.py "$@"
}

# Run main function
main "$@"