#!/usr/bin/env bash
# Global AI Observer Command
# Run this from anywhere to launch the AI player observer with reliable startup

set -e  # Exit on error (disabled for retry logic where needed)

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Configuration: Environment variables with sensible defaults
SERVER_URL="${SERVER_URL:-http://localhost:8000}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-60}"
AI_SESSION_RETRIES="${AI_SESSION_RETRIES:-3}"
AI_SESSION_RETRY_INTERVAL="${AI_SESSION_RETRY_INTERVAL:-5}"

# Ensure logs directory exists
mkdir -p logs

# Diagnostics log file
DIAGNOSTICS_LOG="logs/ai-session-diagnostics.log"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$DIAGNOSTICS_LOG"
}

# Wait for server to be ready
wait_for_server() {
    local url="${SERVER_URL}${HEALTH_ENDPOINT}"
    local elapsed=0
    local interval=2
    
    log "⏳ Waiting for server to be ready at ${url}..."
    log "Maximum wait time: ${MAX_WAIT_SECONDS} seconds"
    
    while [ $elapsed -lt $MAX_WAIT_SECONDS ]; do
        if curl --silent --show-error --fail --max-time 5 "$url" > /dev/null 2>&1; then
            log "✅ Server is ready!"
            return 0
        fi
        
        echo -n "."
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    log "❌ Server did not become ready within ${MAX_WAIT_SECONDS} seconds"
    log "Please check server logs for details"
    return 1
}

# Start AI session with retries and exponential backoff
start_ai_session_with_retries() {
    local personality="${1:-curious_explorer}"
    local name="${2:-}"
    local retries=$AI_SESSION_RETRIES
    local retry_count=0
    local backoff=$AI_SESSION_RETRY_INTERVAL
    
    # Build the config JSON
    local config="{\"personality\":\"${personality}\",\"thinking_speed\":2.0,\"auto_play\":true"
    if [ -n "$name" ]; then
        config="${config},\"name\":\"${name}\""
    fi
    config="${config}}"
    
    log "🤖 Starting AI player session with personality: ${personality}"
    
    while [ $retry_count -lt $retries ]; do
        if [ $retry_count -gt 0 ]; then
            log "Retry attempt $((retry_count + 1))/${retries} after ${backoff}s backoff..."
            sleep $backoff
        fi
        
        # Attempt to start AI session
        local http_code
        local response
        
        response=$(curl --silent --show-error --write-out "\nHTTP_CODE:%{http_code}" \
            --max-time 30 \
            -H "Content-Type: application/json" \
            -d "$config" \
            "${SERVER_URL}/ai-player/start" 2>&1) || true
        
        http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
        response=$(echo "$response" | sed '/HTTP_CODE:/d')
        
        if [ -z "$http_code" ]; then
            log "❌ No response from server (connection failed)"
            log "Response: $response" >> "$DIAGNOSTICS_LOG"
            retry_count=$((retry_count + 1))
            backoff=$((backoff * 2))  # Exponential backoff
            continue
        fi
        
        log "HTTP Status: $http_code"
        
        if [ "$http_code" = "200" ]; then
            log "✅ AI session started successfully!"
            echo "$response"
            return 0
        elif [ "$http_code" -ge 500 ] && [ "$http_code" -lt 600 ]; then
            # 5xx error - retry
            log "⚠️  Server error (HTTP ${http_code}) - will retry"
            log "Response body:" >> "$DIAGNOSTICS_LOG"
            echo "$response" >> "$DIAGNOSTICS_LOG"
            retry_count=$((retry_count + 1))
            backoff=$((backoff * 2))  # Exponential backoff
        else
            # 4xx or other error - don't retry
            log "❌ Client error or unexpected status (HTTP ${http_code}) - not retrying"
            log "Response body:" >> "$DIAGNOSTICS_LOG"
            echo "$response" >> "$DIAGNOSTICS_LOG"
            return 1
        fi
    done
    
    log "❌ Failed to start AI session after ${retries} attempts"
    return 1
}

# Main execution
main() {
    log "=========================================="
    log "🍺 The Living Rusted Tankard AI Observer"
    log "=========================================="
    log "Configuration:"
    log "  SERVER_URL: ${SERVER_URL}"
    log "  HEALTH_ENDPOINT: ${HEALTH_ENDPOINT}"
    log "  MAX_WAIT_SECONDS: ${MAX_WAIT_SECONDS}"
    log "  AI_SESSION_RETRIES: ${AI_SESSION_RETRIES}"
    log "  AI_SESSION_RETRY_INTERVAL: ${AI_SESSION_RETRY_INTERVAL}"
    log ""
    
    # Check if we should use Python directly for certain flags
    if [[ "$*" == *"--demo"* ]] || [[ "$*" == *"--web"* ]] || [[ "$*" == *"--list-personalities"* ]]; then
        log "Running Python script directly for special mode..."
        exec python3 launch_ai_observer.py "$@"
    fi
    
    # Start the server in background if not already running
    if ! curl --silent --fail --max-time 2 "${SERVER_URL}${HEALTH_ENDPOINT}" > /dev/null 2>&1; then
        log "Starting server..."
        python3 -m uvicorn core.api:app --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &
        SERVER_PID=$!
        log "Server started with PID: ${SERVER_PID}"
        
        # Wait for server to be ready
        if ! wait_for_server; then
            log "❌ Server failed to start properly"
            log "Server logs (last 20 lines):"
            tail -20 logs/server.log | tee -a "$DIAGNOSTICS_LOG"
            
            # Clean up
            if [ -n "$SERVER_PID" ]; then
                kill $SERVER_PID 2>/dev/null || true
            fi
            exit 1
        fi
    else
        log "✅ Server is already running"
    fi
    
    # Extract personality and name from arguments if provided
    personality="curious_explorer"
    name=""
    
    while [ $# -gt 0 ]; do
        case "$1" in
            --personality)
                personality="$2"
                shift 2
                ;;
            --name)
                name="$2"
                shift 2
                ;;
            --new|--continue-session)
                # These are handled by Python script
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # Start AI session with retries
    if ! start_ai_session_with_retries "$personality" "$name"; then
        log "❌ Could not start AI session"
        log "Check diagnostics log: ${DIAGNOSTICS_LOG}"
        
        # Keep server running for debugging
        log "Server is still running at ${SERVER_URL} for debugging"
        log "Press Ctrl+C to stop"
        wait
        exit 1
    fi
    
    # Hand off to Python for observation
    log "Handing off to Python observer for streaming..."
    python3 launch_ai_observer.py --continue-session "$(echo "$response" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)" || {
        log "Python observer exited with error"
        exit 1
    }
}

# Trap Ctrl+C to clean up
trap 'log "Shutting down..."; exit 0' INT TERM

# Run main
main "$@"