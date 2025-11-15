# AI Observer Scripts Documentation

This document describes the AI observer scripts and their configuration options for The Living Rusted Tankard.

## Overview

The AI observer scripts allow you to launch and monitor AI players interacting with the game. The scripts include robust health checking and retry logic to handle server startup delays and transient errors.

## Main Script: `ai-observer-global.sh`

The main observer script located at `living_rusted_tankard/ai-observer-global.sh` provides a reliable way to start the game server and AI player sessions.

### Usage

```bash
# Start a new AI session
./ai-observer-global.sh --new

# Continue an existing session
./ai-observer-global.sh --continue SESSION_ID

# Launch web interface only
./ai-observer-global.sh --web

# Run simple terminal demo
./ai-observer-global.sh --demo
```

### Environment Variables

The script behavior can be configured using the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_URL` | `http://localhost:8000` | Base URL for the game server |
| `HEALTH_ENDPOINT` | `/health` | Health check endpoint path |
| `MAX_WAIT_SECONDS` | `60` | Maximum time (in seconds) to wait for server to become ready |
| `AI_SESSION_RETRIES` | `3` | Number of retry attempts for AI session initialization on 5xx errors |
| `AI_SESSION_RETRY_INTERVAL` | `5` | Initial retry interval in seconds (doubles with exponential backoff) |

### Example with Custom Configuration

```bash
# Wait longer for server and retry more times
SERVER_URL=http://localhost:8000 \
MAX_WAIT_SECONDS=120 \
AI_SESSION_RETRIES=5 \
AI_SESSION_RETRY_INTERVAL=10 \
./ai-observer-global.sh --new
```

### Features

#### 1. Server Health Checking

The script polls the health endpoint (`/health` by default) until the server responds successfully or the timeout is reached. This ensures the server is fully initialized before attempting to start an AI session.

Progress is displayed during the wait:
```
🔍 Waiting for server at http://localhost:8000/health...
⏱️  Maximum wait time: 60 seconds
⏳ Waiting for server... (0/60s)
⏳ Waiting for server... (2/60s)
...
✅ Server is ready! (waited 8s)
```

#### 2. AI Session Retry Logic

When starting a new AI session (`--new`), the script automatically retries on transient 5xx server errors (500-599). This handles scenarios where the server is running but not yet fully ready to accept AI session requests.

**Retry behavior:**
- Retries only on 5xx errors (server errors)
- Does not retry on 4xx errors (client errors) or connection failures
- Uses exponential backoff: initial interval doubles after each retry
- Example: 5s → 10s → 20s → 40s

**Logging:**
All AI session initialization attempts are logged to `logs/ai-session-diagnostics.log` with:
- Timestamp
- HTTP status code
- Response body
- Retry attempts and intervals

#### 3. Error Handling

The script provides clear error messages and exit codes:

- **Exit code 0**: Success
- **Exit code 1**: Failure (server didn't start, session initialization failed, etc.)

On failure, the script:
- Preserves server logs at `logs/server.log`
- Saves diagnostics to `logs/ai-session-diagnostics.log`
- Provides helpful messages about where to find more information
- Gracefully stops the server before exiting

#### 4. Graceful Shutdown

The script automatically stops the server when:
- You press Ctrl+C
- An error occurs
- The script exits normally

### Diagnostics

#### Server Logs

Server output is captured in `logs/server.log`. Check this file if:
- The server fails to start
- The health check times out
- You encounter unexpected behavior

```bash
tail -f logs/server.log
```

#### AI Session Diagnostics

AI session initialization details are in `logs/ai-session-diagnostics.log`. This includes:
- Each initialization attempt
- HTTP status codes and response bodies
- Retry intervals and timing

```bash
cat logs/ai-session-diagnostics.log
```

## Helper Script: `wait_for_server.sh`

A standalone helper script in `scripts/wait_for_server.sh` for waiting on server readiness.

### Usage

```bash
./scripts/wait_for_server.sh [SERVER_URL] [HEALTH_ENDPOINT] [MAX_WAIT_SECONDS]
```

### Examples

```bash
# Use defaults (http://localhost:8080/health, 60s timeout)
./scripts/wait_for_server.sh

# Custom URL and endpoint
./scripts/wait_for_server.sh http://localhost:8000 /health 120

# Different port
./scripts/wait_for_server.sh http://localhost:3000 /api/health 90
```

## Troubleshooting

### Server Never Becomes Ready

**Symptoms:**
```
❌ Server did not become ready within 60 seconds
```

**Solutions:**
1. Increase `MAX_WAIT_SECONDS`:
   ```bash
   MAX_WAIT_SECONDS=120 ./ai-observer-global.sh --new
   ```

2. Check server logs for errors:
   ```bash
   cat logs/server.log
   ```

3. Verify dependencies are installed:
   ```bash
   cd living_rusted_tankard
   pip install -r requirements.txt
   ```

### AI Session Fails with 5xx Errors

**Symptoms:**
```
❌ Failed after 3 attempts with server error 500
```

**Solutions:**
1. Check diagnostics for error details:
   ```bash
   cat logs/ai-session-diagnostics.log
   ```

2. Increase retry attempts and initial interval:
   ```bash
   AI_SESSION_RETRIES=5 \
   AI_SESSION_RETRY_INTERVAL=10 \
   ./ai-observer-global.sh --new
   ```

3. Verify the server is fully initialized by checking health endpoint manually:
   ```bash
   curl http://localhost:8000/health
   ```

### Port Already in Use

**Symptoms:**
Server fails to start because port 8000 is already in use.

**Solutions:**
1. Find and stop the existing process:
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. Use a different port:
   ```bash
   SERVER_URL=http://localhost:8001 ./ai-observer-global.sh --new
   ```
   Note: You'll also need to modify the server startup command in the script or run the server separately.

## Best Practices

1. **Always check logs on failure**: Both `logs/server.log` and `logs/ai-session-diagnostics.log` provide valuable debugging information.

2. **Use appropriate timeouts**: For slow systems or cold starts, increase `MAX_WAIT_SECONDS` and `AI_SESSION_RETRY_INTERVAL`.

3. **Monitor resource usage**: AI sessions can be resource-intensive. Ensure adequate CPU and memory.

4. **Clean up old sessions**: Use the web interface or API to stop old AI sessions before starting new ones.

## Architecture Notes

### Why Separate Health Check and AI Session?

The two-phase approach (health check → AI session) exists because:

1. **Server initialization**: The HTTP server may start accepting connections before all services (database, LLM, etc.) are fully initialized.

2. **Service dependencies**: AI session creation depends on multiple services being ready:
   - Database connections
   - LLM service (Ollama)
   - Game state initialization
   - Memory systems

3. **Transient failures**: Initial AI session attempts may fail due to:
   - Background migrations
   - Cache warming
   - Service discovery delays

The health check confirms the server is ready, while retries handle remaining initialization edge cases.

## Related Files

- `living_rusted_tankard/ai-observer-global.sh` - Main observer script
- `living_rusted_tankard/launch_ai_observer.py` - Python implementation for advanced features
- `scripts/wait_for_server.sh` - Standalone health check helper
- `logs/server.log` - Server output log
- `logs/ai-session-diagnostics.log` - AI session initialization diagnostics
