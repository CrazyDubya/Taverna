#!/usr/bin/env bash
# Helper script to wait for server readiness
# Can be used standalone or sourced by other scripts

set -e

# Configuration
SERVER_URL="${SERVER_URL:-http://localhost:8000}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-60}"

# Wait for server to be ready
wait_for_server() {
    local url="${SERVER_URL}${HEALTH_ENDPOINT}"
    local elapsed=0
    local interval=2
    
    echo "⏳ Waiting for server to be ready at ${url}..."
    echo "Maximum wait time: ${MAX_WAIT_SECONDS} seconds"
    
    while [ $elapsed -lt $MAX_WAIT_SECONDS ]; do
        if curl --silent --show-error --fail --max-time 5 "$url" > /dev/null 2>&1; then
            echo "✅ Server is ready!"
            return 0
        fi
        
        echo -n "."
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    echo ""
    echo "❌ Server did not become ready within ${MAX_WAIT_SECONDS} seconds"
    return 1
}

# If script is run directly (not sourced)
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    wait_for_server
    exit $?
fi
