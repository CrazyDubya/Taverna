#!/usr/bin/env bash
# Helper script to wait for server to be ready
# Usage: wait_for_server.sh [SERVER_URL] [HEALTH_ENDPOINT] [MAX_WAIT_SECONDS]

set -e

# Configuration with defaults
SERVER_URL="${1:-http://localhost:8080}"
HEALTH_ENDPOINT="${2:-/health}"
MAX_WAIT_SECONDS="${3:-60}"

HEALTH_URL="${SERVER_URL}${HEALTH_ENDPOINT}"
ELAPSED=0
INTERVAL=2

echo "🔍 Waiting for server at ${HEALTH_URL}..."
echo "⏱️  Maximum wait time: ${MAX_WAIT_SECONDS} seconds"

while [ $ELAPSED -lt $MAX_WAIT_SECONDS ]; do
    if curl --silent --show-error --fail --max-time 5 "$HEALTH_URL" > /dev/null 2>&1; then
        echo "✅ Server is ready! (waited ${ELAPSED}s)"
        exit 0
    fi
    
    echo "⏳ Waiting for server... (${ELAPSED}/${MAX_WAIT_SECONDS}s)"
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo "❌ Server did not become ready within ${MAX_WAIT_SECONDS} seconds"
exit 1
