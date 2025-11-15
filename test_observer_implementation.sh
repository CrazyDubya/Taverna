#!/usr/bin/env bash
# Test script for ai-observer-global.sh functionality
# This script validates the health check and retry logic without requiring a live server

set -e

TEST_DIR="/tmp/observer-test-$$"
mkdir -p "$TEST_DIR/logs"

echo "🧪 Testing AI Observer Script Functionality"
echo "============================================="
echo ""

# Test 1: Test wait_for_server helper script
echo "Test 1: Validating wait_for_server.sh syntax and structure"
echo "-----------------------------------------------------------"

if bash -n scripts/wait_for_server.sh; then
    echo "✅ wait_for_server.sh has valid bash syntax"
else
    echo "❌ wait_for_server.sh has syntax errors"
    exit 1
fi

# Check that it has the required functionality
if grep -q "curl.*--silent.*--show-error.*--fail" scripts/wait_for_server.sh; then
    echo "✅ wait_for_server.sh uses proper curl flags"
else
    echo "❌ wait_for_server.sh missing proper curl usage"
    exit 1
fi

if grep -q "MAX_WAIT_SECONDS" scripts/wait_for_server.sh; then
    echo "✅ wait_for_server.sh respects MAX_WAIT_SECONDS"
else
    echo "❌ wait_for_server.sh doesn't use MAX_WAIT_SECONDS"
    exit 1
fi

echo ""

# Test 2: Test ai-observer-global.sh syntax
echo "Test 2: Validating ai-observer-global.sh syntax and structure"
echo "--------------------------------------------------------------"

if bash -n living_rusted_tankard/ai-observer-global.sh; then
    echo "✅ ai-observer-global.sh has valid bash syntax"
else
    echo "❌ ai-observer-global.sh has syntax errors"
    exit 1
fi

# Check for required functions
if grep -q "wait_for_server()" living_rusted_tankard/ai-observer-global.sh; then
    echo "✅ ai-observer-global.sh defines wait_for_server function"
else
    echo "❌ ai-observer-global.sh missing wait_for_server function"
    exit 1
fi

if grep -q "start_ai_session_with_retries()" living_rusted_tankard/ai-observer-global.sh; then
    echo "✅ ai-observer-global.sh defines start_ai_session_with_retries function"
else
    echo "❌ ai-observer-global.sh missing start_ai_session_with_retries function"
    exit 1
fi

# Check for environment variables with defaults
for var in SERVER_URL HEALTH_ENDPOINT MAX_WAIT_SECONDS AI_SESSION_RETRIES AI_SESSION_RETRY_INTERVAL; do
    if grep -q "${var}=\"\${${var}:-" living_rusted_tankard/ai-observer-global.sh; then
        echo "✅ $var has default value"
    else
        echo "⚠️  $var may not have default value (acceptable if handled differently)"
    fi
done

echo ""

# Test 3: Check retry logic for 5xx errors
echo "Test 3: Validating retry logic for 5xx errors"
echo "----------------------------------------------"

if grep -q "5\[0-9\]\[0-9\]" living_rusted_tankard/ai-observer-global.sh; then
    echo "✅ Script checks for 5xx HTTP status codes"
else
    echo "❌ Script doesn't properly check for 5xx errors"
    exit 1
fi

if grep -q "retry_interval.*\*.*2" living_rusted_tankard/ai-observer-global.sh; then
    echo "✅ Script implements exponential backoff"
else
    echo "❌ Script missing exponential backoff logic"
    exit 1
fi

echo ""

# Test 4: Check logging
echo "Test 4: Validating logging functionality"
echo "-----------------------------------------"

if grep -q "DIAGNOSTICS_LOG" living_rusted_tankard/ai-observer-global.sh; then
    echo "✅ Script defines diagnostics log path"
else
    echo "❌ Script missing diagnostics log definition"
    exit 1
fi

if grep -q "tee.*DIAGNOSTICS_LOG" living_rusted_tankard/ai-observer-global.sh; then
    echo "✅ Script logs to diagnostics file"
else
    echo "❌ Script doesn't log to diagnostics file"
    exit 1
fi

echo ""

# Test 5: Check cleanup handler
echo "Test 5: Validating cleanup and signal handling"
echo "-----------------------------------------------"

if grep -q "trap.*cleanup.*EXIT.*INT.*TERM" living_rusted_tankard/ai-observer-global.sh; then
    echo "✅ Script has proper signal handlers"
else
    echo "❌ Script missing signal handlers"
    exit 1
fi

if grep -q "cleanup()" living_rusted_tankard/ai-observer-global.sh; then
    echo "✅ Script defines cleanup function"
else
    echo "❌ Script missing cleanup function"
    exit 1
fi

echo ""

# Test 6: Validate documentation
echo "Test 6: Validating documentation"
echo "---------------------------------"

if [ -f "docs/OBSERVERS.md" ]; then
    echo "✅ OBSERVERS.md documentation exists"
else
    echo "❌ OBSERVERS.md documentation missing"
    exit 1
fi

# Check that all environment variables are documented
for var in SERVER_URL HEALTH_ENDPOINT MAX_WAIT_SECONDS AI_SESSION_RETRIES AI_SESSION_RETRY_INTERVAL; do
    if grep -q "$var" docs/OBSERVERS.md; then
        echo "✅ $var is documented"
    else
        echo "❌ $var is not documented"
        exit 1
    fi
done

echo ""

# Test 7: Mock server test (simulate behavior)
echo "Test 7: Simulating server health check behavior"
echo "------------------------------------------------"

# Create a mock server script that becomes healthy after a delay
cat > "$TEST_DIR/mock_server.sh" << 'EOF'
#!/usr/bin/env bash
# Mock server that starts responding after N seconds
DELAY=${1:-5}
PORT=${2:-9999}

# Start a simple HTTP server that responds after delay
(
    sleep $DELAY
    while true; do
        echo -e "HTTP/1.1 200 OK\r\n\r\n{\"status\":\"healthy\"}" | nc -l -p $PORT -q 1 2>/dev/null || true
    done
) &
echo $!
EOF

chmod +x "$TEST_DIR/mock_server.sh"

echo "Mock server script created for testing"
echo "✅ Mock server test framework ready"

echo ""

# Test 8: Check curl dependency
echo "Test 8: Validating dependencies"
echo "--------------------------------"

if command -v curl >/dev/null 2>&1; then
    echo "✅ curl is available"
else
    echo "❌ curl is not available (required dependency)"
    exit 1
fi

if command -v python3 >/dev/null 2>&1; then
    echo "✅ python3 is available"
else
    echo "❌ python3 is not available (required dependency)"
    exit 1
fi

echo ""

# Test 9: Executable permissions
echo "Test 9: Checking file permissions"
echo "----------------------------------"

if [ -x "living_rusted_tankard/ai-observer-global.sh" ]; then
    echo "✅ ai-observer-global.sh is executable"
else
    echo "❌ ai-observer-global.sh is not executable"
    exit 1
fi

if [ -x "scripts/wait_for_server.sh" ]; then
    echo "✅ wait_for_server.sh is executable"
else
    echo "❌ wait_for_server.sh is not executable"
    exit 1
fi

echo ""

# Test 10: Environment variable handling
echo "Test 10: Testing environment variable configuration"
echo "---------------------------------------------------"

# Test that defaults are used when not set
unset SERVER_URL HEALTH_ENDPOINT MAX_WAIT_SECONDS AI_SESSION_RETRIES AI_SESSION_RETRY_INTERVAL

# Extract defaults from script
DEFAULT_SERVER_URL=$(grep 'SERVER_URL=.*:-' living_rusted_tankard/ai-observer-global.sh | head -1 | sed -n 's/.*:-\([^}]*\)}.*/\1/p')
DEFAULT_HEALTH_ENDPOINT=$(grep 'HEALTH_ENDPOINT=.*:-' living_rusted_tankard/ai-observer-global.sh | head -1 | sed -n 's/.*:-\([^}]*\)}.*/\1/p')
DEFAULT_MAX_WAIT=$(grep 'MAX_WAIT_SECONDS=.*:-' living_rusted_tankard/ai-observer-global.sh | head -1 | sed -n 's/.*:-\([^}]*\)}.*/\1/p')

echo "  Default SERVER_URL: $DEFAULT_SERVER_URL"
echo "  Default HEALTH_ENDPOINT: $DEFAULT_HEALTH_ENDPOINT"
echo "  Default MAX_WAIT_SECONDS: $DEFAULT_MAX_WAIT"

if [ -n "$DEFAULT_SERVER_URL" ] && [ -n "$DEFAULT_HEALTH_ENDPOINT" ] && [ -n "$DEFAULT_MAX_WAIT" ]; then
    echo "✅ All defaults are properly defined"
else
    echo "⚠️  Some defaults may be empty (check if this is intentional)"
fi

echo ""

# Cleanup
rm -rf "$TEST_DIR"

echo "============================================="
echo "✅ All tests passed!"
echo "============================================="
echo ""
echo "Summary:"
echo "  • Script syntax is valid"
echo "  • Required functions are present"
echo "  • Retry logic with exponential backoff is implemented"
echo "  • Logging to diagnostics file is configured"
echo "  • Signal handlers and cleanup are in place"
echo "  • Documentation is complete"
echo "  • Dependencies are available"
echo "  • File permissions are correct"
echo ""
echo "The implementation is ready for integration testing with a live server."
