#!/usr/bin/env bash
# Helper script to wait for server to be ready
# Can be used independently or sourced by other scripts

set -euo pipefail

# Configurable environment variables with sensible defaults
SERVER_URL="${SERVER_URL:-http://localhost:8000}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-60}"

# Function to log messages with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Function to log error messages
log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

# Function to wait for server to be ready
wait_for_server() {
    local health_url="${SERVER_URL}${HEALTH_ENDPOINT}"
    local elapsed=0
    local interval=2
    
    log_message "Waiting for server to be ready at $health_url (max ${MAX_WAIT_SECONDS}s)..."
    
    while [ $elapsed -lt "$MAX_WAIT_SECONDS" ]; do
        # Use curl to check health endpoint
        # --silent: no progress bar
        # --show-error: show errors
        # --fail: fail on HTTP errors
        # --max-time: timeout for the request
        if curl --silent --show-error --fail --max-time 5 "$health_url" >/dev/null 2>&1; then
            log_message "✅ Server is ready!"
            return 0
        fi
        
        # Show progress and sleep
        log_message "⏳ Server not ready yet... (${elapsed}/${MAX_WAIT_SECONDS}s)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    log_error "❌ Server did not become healthy within ${MAX_WAIT_SECONDS} seconds"
    return 1
}

# Main execution when run as script (not sourced)
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --url)
                SERVER_URL="$2"
                shift 2
                ;;
            --health-endpoint)
                HEALTH_ENDPOINT="$2"
                shift 2
                ;;
            --max-wait)
                MAX_WAIT_SECONDS="$2"
                shift 2
                ;;
            --help)
                cat <<EOF
Usage: wait_for_server.sh [OPTIONS]

Wait for a server to become healthy by polling its health endpoint.

Options:
  --url URL                Server URL (default: http://localhost:8000)
  --health-endpoint PATH   Health endpoint path (default: /health)
  --max-wait SECONDS      Maximum time to wait in seconds (default: 60)
  --help                  Show this help message

Environment Variables:
  SERVER_URL              Same as --url
  HEALTH_ENDPOINT         Same as --health-endpoint
  MAX_WAIT_SECONDS        Same as --max-wait

Examples:
  # Wait for default server
  ./wait_for_server.sh

  # Wait for custom server
  ./wait_for_server.sh --url http://localhost:3000 --health-endpoint /api/health

  # Use environment variables
  SERVER_URL=http://localhost:3000 MAX_WAIT_SECONDS=120 ./wait_for_server.sh

Exit Codes:
  0 - Server is healthy
  1 - Server did not become healthy within timeout
EOF
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                log_error "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Call the function
    if wait_for_server; then
        exit 0
    else
        exit 1
    fi
fi
