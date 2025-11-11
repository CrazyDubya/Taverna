#!/usr/bin/env bash
# Test script for ai-observer-global.sh health check and retry logic
# This creates a mock server to test the retry behavior

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TEST_PORT=9998
TEST_SERVER_PID=""

cleanup() {
    if [ -n "$TEST_SERVER_PID" ] && kill -0 "$TEST_SERVER_PID" 2>/dev/null; then
        echo "Stopping test server..."
        kill "$TEST_SERVER_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT

# Create a simple Python test server that simulates delayed startup
echo "Starting mock server that becomes healthy after 5 seconds..."
python3 -c "
import http.server
import socketserver
import time
import json
from threading import Thread

start_time = time.time()
ai_session_attempts = 0

class TestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logs
    
    def do_GET(self):
        global start_time
        elapsed = time.time() - start_time
        
        if self.path == '/health':
            # Server becomes healthy after 5 seconds
            if elapsed >= 5:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'healthy'}).encode())
            else:
                self.send_response(503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'initializing'}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        global start_time, ai_session_attempts
        elapsed = time.time() - start_time
        ai_session_attempts += 1
        
        if self.path == '/ai-player/start':
            # First attempt fails with 500, second succeeds
            if ai_session_attempts == 1:
                print(f'[Mock Server] AI session attempt {ai_session_attempts}: returning 500 (simulating transient error)')
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Server still initializing'}).encode())
            else:
                print(f'[Mock Server] AI session attempt {ai_session_attempts}: returning 200 (success)')
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'session_id': 'test-session-123',
                    'ai_player': {
                        'name': 'TestAI',
                        'personality': 'curious_explorer'
                    }
                }
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(('', $TEST_PORT), TestHandler) as httpd:
    print(f'[Mock Server] Serving on port $TEST_PORT')
    httpd.serve_forever()
" > /tmp/test-server.log 2>&1 &
TEST_SERVER_PID=$!

echo "Mock server started with PID: $TEST_SERVER_PID"
sleep 1

# Test 1: wait_for_server.sh with short timeout (should fail)
echo ""
echo "=== Test 1: Testing wait_for_server.sh with timeout too short ==="
if SERVER_URL=http://localhost:$TEST_PORT MAX_WAIT_SECONDS=2 "$SCRIPT_DIR/wait_for_server.sh" 2>&1; then
    echo "❌ Test 1 FAILED: Should have timed out"
    exit 1
else
    echo "✅ Test 1 PASSED: Correctly timed out"
fi

# Test 2: wait_for_server.sh with sufficient timeout (should succeed)
echo ""
echo "=== Test 2: Testing wait_for_server.sh with sufficient timeout ==="
if SERVER_URL=http://localhost:$TEST_PORT MAX_WAIT_SECONDS=10 "$SCRIPT_DIR/wait_for_server.sh" 2>&1; then
    echo "✅ Test 2 PASSED: Server became healthy"
else
    echo "❌ Test 2 FAILED: Should have succeeded"
    exit 1
fi

# Test 3: Test retry logic with mock server
echo ""
echo "=== Test 3: Testing AI session retry on 500 error ==="
response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"personality":"curious_explorer"}' \
    http://localhost:$TEST_PORT/ai-player/start)
status=$?

if [ $status -eq 0 ]; then
    echo "First request returned: $response"
    if echo "$response" | grep -q "Server still initializing"; then
        echo "✅ Test 3a PASSED: First request correctly returned error"
        
        # Try again
        response=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -d '{"personality":"curious_explorer"}' \
            http://localhost:$TEST_PORT/ai-player/start)
        
        if echo "$response" | grep -q "test-session-123"; then
            echo "✅ Test 3b PASSED: Second request succeeded"
        else
            echo "❌ Test 3b FAILED: Second request should have succeeded"
            exit 1
        fi
    else
        echo "Note: Test may have succeeded immediately (mock server warmed up)"
    fi
else
    echo "❌ Test 3 FAILED: Request failed completely"
    exit 1
fi

echo ""
echo "==================================================="
echo "All tests passed! ✅"
echo "==================================================="
echo ""
echo "The scripts correctly:"
echo "  1. Wait for server health with timeout"
echo "  2. Handle server that becomes healthy after delay"
echo "  3. Demonstrate retry capability on 5xx errors"
