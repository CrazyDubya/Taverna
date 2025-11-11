# AI Observer Configuration and Usage

This document describes the configuration options and behavior for the AI Observer system, particularly focusing on startup reliability improvements added to address [Issue #3](https://github.com/CrazyDubya/Taverna/issues/3).

## Problem Statement

The AI observer script previously started the game server and immediately attempted to start an AI player session. In some environments, the server needed additional time for initialization (database migrations, background tasks, etc.), which caused the AI session initialization to fail with HTTP 500 errors.

## Solution Overview

The updated `ai-observer-global.sh` script now implements:

1. **Health check polling**: Waits for the server to report healthy status before attempting AI session creation
2. **Retry logic**: Automatically retries AI session creation on transient 5xx errors with exponential backoff
3. **Comprehensive logging**: Records all startup attempts and failures to aid debugging
4. **Configurable behavior**: All timeouts and retry parameters can be customized via environment variables

## Environment Variables

All configuration is done through environment variables with sensible defaults:

### `SERVER_URL`
- **Default**: `http://localhost:8000`
- **Description**: The base URL of the game server
- **Example**: `export SERVER_URL=http://localhost:8080`

### `HEALTH_ENDPOINT`
- **Default**: `/health`
- **Description**: The health check endpoint path (relative to SERVER_URL)
- **Example**: `export HEALTH_ENDPOINT=/api/health`

### `MAX_WAIT_SECONDS`
- **Default**: `60`
- **Description**: Maximum time (in seconds) to wait for the server to become healthy
- **Example**: `export MAX_WAIT_SECONDS=120`
- **Notes**: If server doesn't become healthy within this time, the script exits with error

### `AI_SESSION_RETRIES`
- **Default**: `3`
- **Description**: Number of times to retry AI session creation on 5xx errors
- **Example**: `export AI_SESSION_RETRIES=5`
- **Notes**: 4xx errors are not retried (assumed to be configuration issues)

### `AI_SESSION_RETRY_INTERVAL`
- **Default**: `5`
- **Description**: Initial retry interval (in seconds) between AI session attempts
- **Example**: `export AI_SESSION_RETRY_INTERVAL=10`
- **Notes**: Uses exponential backoff (doubles on each retry: 5s, 10s, 20s, etc.)

## Usage Examples

### Basic usage (default settings)
```bash
./ai-observer-global.sh --new
```

### Custom server URL
```bash
export SERVER_URL=http://localhost:8080
./ai-observer-global.sh --new
```

### Extended timeout for slow systems
```bash
export MAX_WAIT_SECONDS=180
export AI_SESSION_RETRIES=5
./ai-observer-global.sh --new
```

### All options combined
```bash
export SERVER_URL=http://localhost:8080
export HEALTH_ENDPOINT=/health
export MAX_WAIT_SECONDS=120
export AI_SESSION_RETRIES=5
export AI_SESSION_RETRY_INTERVAL=10
./ai-observer-global.sh --new --personality curious_explorer --name Gemma
```

### Using the helper script standalone
```bash
# Check if server is ready
./scripts/wait_for_server.sh

# Or with custom settings
export MAX_WAIT_SECONDS=30
./scripts/wait_for_server.sh
```

## Behavior Details

### Server Startup Sequence

1. **Server Detection**: Checks if server is already running at `${SERVER_URL}${HEALTH_ENDPOINT}`
2. **Server Launch** (if needed): Starts uvicorn in background
3. **Health Polling**: Polls health endpoint every 2 seconds until:
   - Server responds with HTTP 200 (success), or
   - `MAX_WAIT_SECONDS` timeout is reached (failure)
4. **Session Creation**: Attempts to create AI session with retry logic

### AI Session Retry Logic

When starting an AI session:

1. **Initial Attempt**: Tries to POST to `/ai-player/start`
2. **Success (HTTP 200)**: Proceeds to observation mode
3. **5xx Error**: Retries with exponential backoff:
   - Retry 1: waits `AI_SESSION_RETRY_INTERVAL` seconds
   - Retry 2: waits `AI_SESSION_RETRY_INTERVAL * 2` seconds
   - Retry 3: waits `AI_SESSION_RETRY_INTERVAL * 4` seconds
   - And so on...
4. **4xx Error**: Does not retry (indicates configuration issue)
5. **Max Retries Exceeded**: Exits with error code and diagnostic logs

### Logging

All operations are logged to `logs/ai-session-diagnostics.log` including:

- Configuration values
- Server startup status
- Health check progress
- HTTP status codes and response bodies for failed requests
- Retry attempts and backoff intervals
- Final success or failure status

**Example log output:**
```
[2024-01-15 14:30:00] ==========================================
[2024-01-15 14:30:00] 🍺 The Living Rusted Tankard AI Observer
[2024-01-15 14:30:00] ==========================================
[2024-01-15 14:30:00] Configuration:
[2024-01-15 14:30:00]   SERVER_URL: http://localhost:8000
[2024-01-15 14:30:00]   HEALTH_ENDPOINT: /health
[2024-01-15 14:30:00]   MAX_WAIT_SECONDS: 60
[2024-01-15 14:30:00]   AI_SESSION_RETRIES: 3
[2024-01-15 14:30:00]   AI_SESSION_RETRY_INTERVAL: 5
[2024-01-15 14:30:00] 
[2024-01-15 14:30:00] Starting server...
[2024-01-15 14:30:00] Server started with PID: 12345
[2024-01-15 14:30:00] ⏳ Waiting for server to be ready at http://localhost:8000/health...
[2024-01-15 14:30:00] Maximum wait time: 60 seconds
[2024-01-15 14:30:15] ✅ Server is ready!
[2024-01-15 14:30:15] 🤖 Starting AI player session with personality: curious_explorer
[2024-01-15 14:30:16] HTTP Status: 200
[2024-01-15 14:30:16] ✅ AI session started successfully!
```

## Error Scenarios

### Server Never Becomes Healthy

If the server doesn't respond to health checks within `MAX_WAIT_SECONDS`:

```
❌ Server did not become ready within 60 seconds
Please check server logs for details
Server logs (last 20 lines):
[server log output...]
```

**Resolution**:
- Check `logs/server.log` for startup errors
- Increase `MAX_WAIT_SECONDS` if system is slow
- Verify port 8000 is not already in use
- Check database connectivity and migrations

### Persistent 5xx Errors

If AI session creation fails with 5xx errors after all retries:

```
❌ Failed to start AI session after 3 attempts
Check diagnostics log: logs/ai-session-diagnostics.log
Server is still running at http://localhost:8000 for debugging
```

**Resolution**:
- Review `logs/ai-session-diagnostics.log` for error details
- Server remains running for manual debugging
- Check Ollama service status if using AI features
- Verify database schema and migrations are current

### 4xx Client Errors

If AI session creation fails with 4xx errors (not retried):

```
❌ Client error or unexpected status (HTTP 400) - not retrying
```

**Resolution**:
- Check request parameters (personality, name, etc.)
- Review API documentation for correct usage
- Verify authentication if required
- Check `logs/ai-session-diagnostics.log` for response body

## Troubleshooting

### Check server health manually
```bash
curl http://localhost:8000/health
```

### View diagnostic logs
```bash
tail -f logs/ai-session-diagnostics.log
```

### View server logs
```bash
tail -f logs/server.log
```

### Test with verbose curl
```bash
curl -v -X POST http://localhost:8000/ai-player/start \
  -H "Content-Type: application/json" \
  -d '{"personality":"curious_explorer","thinking_speed":2.0,"auto_play":true}'
```

## Integration with Other Scripts

The `scripts/wait_for_server.sh` helper can be sourced by other scripts:

```bash
#!/bin/bash
source scripts/wait_for_server.sh

# Configure
export SERVER_URL=http://localhost:8080
export MAX_WAIT_SECONDS=30

# Wait for server
if wait_for_server; then
    echo "Server is ready, proceeding..."
    # Your logic here
else
    echo "Server is not ready, exiting..."
    exit 1
fi
```

## Compatibility Notes

- **Bash Version**: Requires bash 3.0+ (uses arrays and modern syntax)
- **Dependencies**: Only requires `curl` (no jq or other tools needed)
- **Portability**: Uses `#!/usr/bin/env bash` for maximum compatibility
- **Exit Codes**: 
  - `0`: Success
  - `1`: Failure (timeout, max retries exceeded, etc.)

## Special Modes

Some command-line flags bypass the startup reliability features and run Python directly:

- `--demo`: Runs terminal demo without server
- `--web`: Opens web interface only
- `--list-personalities`: Lists available AI personalities

These modes are passed directly to the Python script without server health checks or retry logic.

## Testing

To test the startup reliability features:

1. **Simulate slow server**: Add delay to server startup
2. **Simulate 5xx errors**: Use network proxy to inject errors
3. **Test timeout**: Set low `MAX_WAIT_SECONDS` and verify error handling
4. **Test retry logic**: Monitor `logs/ai-session-diagnostics.log` during retries
5. **Test backoff**: Verify exponential backoff intervals in logs

## Related Documentation

- [README_AI_OBSERVER.md](../README_AI_OBSERVER.md) - AI Observer system overview
- [Issue #3](https://github.com/CrazyDubya/Taverna/issues/3) - Original issue report
- [API Documentation](core/api.py) - Server API endpoints
