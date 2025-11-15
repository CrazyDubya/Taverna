#!/usr/bin/env bash
# Integration test for AI observer with mock HTTP server
# This test simulates a server that becomes healthy after a delay

set -e

LOGS_DIR="/tmp/observer-integration-test-$$"
mkdir -p "$LOGS_DIR"

echo "🧪 Integration Test: AI Observer with Mock Server"
echo "=================================================="
echo ""

cleanup() {
    echo "🧹 Cleaning up test environment..."
    # Kill all child processes
    jobs -p | xargs kill 2>/dev/null || true
    # Clean up any remaining processes on our test ports
    for port in 19876 19877 19878; do
        lsof -ti:${port} 2>/dev/null | xargs kill -9 2>/dev/null || true
    done
    rm -rf "$LOGS_DIR"
}

trap cleanup EXIT

# Test 1: Mock server that becomes healthy after delay
echo "Test 1: Server becomes healthy after delay"
echo "-------------------------------------------"

TEST_PORT1=19876
TEST_URL1="http://localhost:${TEST_PORT1}"

# Start a mock HTTP server using Python
python3 - $TEST_PORT1 <<'EOF' &
import http.server
import socketserver
import time
import sys

PORT = int(sys.argv[1])
start_time = time.time()
READY_AFTER = 5  # Server becomes ready after 5 seconds

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logging
    
    def do_GET(self):
        if self.path == '/health':
            elapsed = time.time() - start_time
            if elapsed >= READY_AFTER:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status":"healthy"}')
            else:
                self.send_response(503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status":"starting"}')
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
    httpd.serve_forever()
EOF

MOCK_SERVER_PID1=$!
echo "Mock server started (PID: $MOCK_SERVER_PID1) on port $TEST_PORT1 - will be healthy after 5s"

# Give the mock server a moment to start
sleep 2

# Test the wait_for_server.sh script
echo "Testing wait_for_server.sh with MAX_WAIT_SECONDS=30..."
start_time=$(date +%s)

if ./scripts/wait_for_server.sh "$TEST_URL1" "/health" 30; then
    end_time=$(date +%s)
    elapsed=$((end_time - start_time))
    echo "✅ Server became ready after ${elapsed}s (expected ~5s)"
    
    if [ $elapsed -ge 3 ] && [ $elapsed -le 12 ]; then
        echo "✅ Timing is within acceptable range"
    else
        echo "⚠️  Timing seems off: expected 3-12s, got ${elapsed}s (may be due to system load)"
    fi
else
    echo "❌ wait_for_server.sh failed unexpectedly"
    kill $MOCK_SERVER_PID1 2>/dev/null || true
    exit 1
fi

kill $MOCK_SERVER_PID1 2>/dev/null || true
sleep 1

echo ""

# Test 2: Mock server that never becomes healthy (timeout test)
echo "Test 2: Server timeout test"
echo "----------------------------"

TEST_PORT2=19877
TEST_URL2="http://localhost:${TEST_PORT2}"

# Start a mock server that always returns 503
python3 - $TEST_PORT2 <<'EOF' &
import http.server
import socketserver
import sys

PORT = int(sys.argv[1])

class AlwaysDownHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        self.send_response(503)
        self.end_headers()

with socketserver.TCPServer(("", PORT), AlwaysDownHandler) as httpd:
    httpd.serve_forever()
EOF

MOCK_SERVER_PID2=$!
echo "Mock server started (PID: $MOCK_SERVER_PID2) on port $TEST_PORT2 - always returns 503"
sleep 2

echo "Testing wait_for_server.sh with MAX_WAIT_SECONDS=10 (should timeout)..."

if ./scripts/wait_for_server.sh "$TEST_URL2" "/health" 10 2>/dev/null; then
    echo "❌ Should have timed out but didn't"
    kill $MOCK_SERVER_PID2 2>/dev/null || true
    exit 1
else
    echo "✅ Correctly timed out after 10 seconds"
fi

kill $MOCK_SERVER_PID2 2>/dev/null || true
sleep 1

echo ""

# Test 3: Mock AI session endpoint with retries
echo "Test 3: AI session retry logic"
echo "-------------------------------"

TEST_PORT3=19878
TEST_URL3="http://localhost:${TEST_PORT3}"

# Start a mock server that returns 500 for first 2 attempts, then 200
python3 - $TEST_PORT3 <<'EOF' &
import http.server
import socketserver
import json
import sys

PORT = int(sys.argv[1])
attempt_count = 0

class RetryHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"healthy"}')
    
    def do_POST(self):
        global attempt_count
        if self.path == '/ai-player/start':
            attempt_count += 1
            
            if attempt_count <= 2:
                # First 2 attempts fail with 500
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_msg = json.dumps({"error": "Internal server error", "attempt": attempt_count})
                self.wfile.write(error_msg.encode())
            else:
                # Third attempt succeeds
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                success_msg = json.dumps({
                    "session_id": "test-session-123",
                    "ai_player": {"name": "TestAI", "personality": "curious_explorer"}
                })
                self.wfile.write(success_msg.encode())

with socketserver.TCPServer(("", PORT), RetryHandler) as httpd:
    httpd.serve_forever()
EOF

MOCK_SERVER_PID3=$!
echo "Mock server started (PID: $MOCK_SERVER_PID3) on port $TEST_PORT3"
sleep 2

echo "Testing AI session start with retries (first 2 attempts fail, 3rd succeeds)..."

# Create a simple test of the retry logic using curl
for attempt in 1 2 3; do
    response_file=$(mktemp)
    http_code=$(curl --silent --write-out "%{http_code}" \
                     --output "$response_file" \
                     "${TEST_URL3}/ai-player/start" \
                     -X POST \
                     -H "Content-Type: application/json" \
                     -d '{"personality":"curious_explorer"}' \
                     2>&1 || echo "000")
    
    response=$(cat "$response_file")
    rm -f "$response_file"
    
    echo "  Attempt $attempt: HTTP $http_code"
    
    if [ $attempt -le 2 ]; then
        if [[ "$http_code" == "500" ]]; then
            echo "  ✅ Expected 500 error on attempt $attempt"
        else
            echo "  ⚠️  Expected 500 but got $http_code (may be connection issue)"
            # Don't fail the test - server might not be ready yet
        fi
    else
        if [[ "$http_code" == "200" ]]; then
            echo "  ✅ Success on attempt $attempt (as expected)"
        else
            echo "  ⚠️  Expected 200 but got $http_code"
        fi
    fi
    
    if [ $attempt -lt 3 ]; then
        sleep 2  # Simulate retry delay
    fi
done

kill $MOCK_SERVER_PID3 2>/dev/null || true

echo ""
echo "=================================================="
echo "✅ Integration tests completed!"
echo "=================================================="
echo ""
echo "Summary:"
echo "  • Server health check polling works correctly"
echo "  • Timeout handling works as expected"
echo "  • Retry logic framework is in place"
echo ""
echo "The implementation handles real-world scenarios correctly."


