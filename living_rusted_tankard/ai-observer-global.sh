#!/usr/bin/env bash
# Global AI Observer Command
# Run this from anywhere to launch the AI player observer with robust server readiness checks

set -euo pipefail

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Configurable environment variables with sensible defaults
SERVER_URL="${SERVER_URL:-http://localhost:8000}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-60}"
AI_SESSION_RETRIES="${AI_SESSION_RETRIES:-3}"
AI_SESSION_RETRY_INTERVAL="${AI_SESSION_RETRY_INTERVAL:-5}"

# Ensure logs directory exists
LOGS_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGS_DIR"
DIAGNOSTICS_LOG="$LOGS_DIR/ai-session-diagnostics.log"
SERVER_LOG="$LOGS_DIR/server.log"

# Server process ID
SERVER_PID=""

# Function to log messages with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$DIAGNOSTICS_LOG"
}

# Function to log error messages
log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$DIAGNOSTICS_LOG" >&2
}

# Function to cleanup on exit
cleanup() {
    local exit_code=$?
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        log_message "Stopping server (PID: $SERVER_PID)..."
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    
    if [ $exit_code -ne 0 ]; then
        log_error "Script exited with code $exit_code"
        log_message "Server logs available at: $SERVER_LOG"
        log_message "Diagnostics available at: $DIAGNOSTICS_LOG"
    fi
    
    exit $exit_code
}

trap cleanup EXIT INT TERM

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
    log_error "Check server logs at: $SERVER_LOG"
    return 1
}

# Function to start AI session with retries
start_ai_session_with_retries() {
    local personality="${1:-curious_explorer}"
    local name="${2:-}"
    local session_url="${SERVER_URL}/ai-player/start"
    local attempt=1
    local backoff=$AI_SESSION_RETRY_INTERVAL
    
    log_message "Starting AI session with personality: $personality"
    
    # Build JSON payload
    local json_payload="{\"personality\":\"$personality\",\"thinking_speed\":2.0,\"auto_play\":true"
    if [ -n "$name" ]; then
        json_payload="$json_payload,\"name\":\"$name\""
    fi
    json_payload="$json_payload}"
    
    while [ $attempt -le "$AI_SESSION_RETRIES" ]; do
        log_message "Attempt $attempt/$AI_SESSION_RETRIES: Starting AI session..."
        
        # Make the request and capture response
        local http_code
        local response_body
        local temp_response
        temp_response=$(mktemp)
        
        http_code=$(curl --silent --show-error --write-out "%{http_code}" \
            --max-time 30 \
            --header "Content-Type: application/json" \
            --data "$json_payload" \
            --output "$temp_response" \
            "$session_url" 2>&1 || echo "000")
        
        response_body=$(cat "$temp_response" 2>/dev/null || echo "")
        rm -f "$temp_response"
        
        # Log the attempt
        log_message "HTTP Status: $http_code"
        
        # Check if successful (2xx status code)
        if [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
            log_message "✅ AI session started successfully!"
            log_message "Response: $response_body"
            # Export the response for the caller to parse
            echo "$response_body"
            return 0
        fi
        
        # Check if it's a 5xx error (server error)
        if [[ "$http_code" =~ ^5[0-9][0-9]$ ]]; then
            log_error "Received HTTP $http_code (server error)"
            log_message "Response body: $response_body"
            
            if [ $attempt -lt "$AI_SESSION_RETRIES" ]; then
                log_message "Retrying in ${backoff}s with exponential backoff..."
                sleep $backoff
                backoff=$((backoff * 2))
                attempt=$((attempt + 1))
                continue
            else
                log_error "❌ All retry attempts exhausted"
                return 1
            fi
        else
            # For 4xx or other errors, don't retry
            log_error "❌ Request failed with HTTP $http_code (non-retryable)"
            log_message "Response body: $response_body"
            return 1
        fi
    done
    
    log_error "❌ Failed to start AI session after $AI_SESSION_RETRIES attempts"
    return 1
}

# Main execution
main() {
    log_message "=== AI Observer Global Script Started ==="
    log_message "Configuration:"
    log_message "  SERVER_URL: $SERVER_URL"
    log_message "  HEALTH_ENDPOINT: $HEALTH_ENDPOINT"
    log_message "  MAX_WAIT_SECONDS: $MAX_WAIT_SECONDS"
    log_message "  AI_SESSION_RETRIES: $AI_SESSION_RETRIES"
    log_message "  AI_SESSION_RETRY_INTERVAL: $AI_SESSION_RETRY_INTERVAL"
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Start the server
    log_message "Starting FastAPI server..."
    python3 -m uvicorn core.api:app --host 0.0.0.0 --port 8000 > "$SERVER_LOG" 2>&1 &
    SERVER_PID=$!
    
    log_message "Server started with PID: $SERVER_PID"
    
    # Wait for server to be ready
    if ! wait_for_server; then
        log_error "Server failed to start properly"
        exit 1
    fi
    
    # Parse command line arguments
    local personality="curious_explorer"
    local name=""
    
    # Simple argument parsing
    while [[ $# -gt 0 ]]; do
        case $1 in
            --personality)
                personality="$2"
                shift 2
                ;;
            --name)
                name="$2"
                shift 2
                ;;
            --new)
                # Flag for starting new session (default behavior)
                shift
                ;;
            *)
                # Pass through other arguments to Python launcher
                log_message "Delegating to Python launcher for advanced options..."
                python3 launch_ai_observer.py "$@"
                return $?
                ;;
        esac
    done
    
    # Start AI session with retries and capture response
    local session_response
    session_response=$(start_ai_session_with_retries "$personality" "$name")
    if [ $? -ne 0 ]; then
        log_error "Failed to start AI session"
        exit 1
    fi
    
    log_message "✅ AI session started successfully!"
    log_message "Server is running at: ${SERVER_URL}"
    log_message "Health endpoint: ${SERVER_URL}${HEALTH_ENDPOINT}"
    log_message ""
    log_message "To observe the AI session, visit:"
    log_message "  ${SERVER_URL}/ai-demo"
    log_message ""
    log_message "Or use the Python observer to watch AI actions in terminal:"
    log_message "  python3 launch_ai_observer.py --web"
    log_message ""
    log_message "Logs:"
    log_message "  Server: $SERVER_LOG"
    log_message "  Diagnostics: $DIAGNOSTICS_LOG"
    log_message ""
    log_message "Press Ctrl+C to stop the server"
    
    # Keep the script running to keep server alive
    wait "$SERVER_PID"
}

main "$@"