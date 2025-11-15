"""
FastAPI endpoints for The Living Rusted Tankard game.

This module provides a REST API interface to interact with the game state
and serves the web interface.
"""

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
import time
import requests
from pathlib import Path
import logging

from .game_state import GameState
from .enhanced_llm_game_master import EnhancedLLMGameMaster as LLMGameMaster
from .items import ITEM_DEFINITIONS, load_item_definitions

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="The Living Rusted Tankard API",
    description="REST API for The Living Rusted Tankard text-based RPG",
    version="0.1.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up templates directory
# First, determine the templates directory path
current_dir = Path(__file__).parent
templates_dir = current_dir.parent.parent / "living_rusted_tankard" / "game" / "templates"
if not templates_dir.exists():
    # Create the templates directory if it doesn't exist
    logger.info(f"Creating templates directory: {templates_dir}")
    templates_dir.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(templates_dir))

# In-memory storage for game sessions with timestamps
sessions: Dict[str, dict] = {}
SESSION_TIMEOUT = 30 * 60  # 30 minutes in seconds

# Initialize the LLM Game Master and Async Pipeline
llm_gm = LLMGameMaster()

# Initialize async LLM pipeline for non-blocking processing
from .async_llm_pipeline import get_pipeline, initialize_pipeline, shutdown_pipeline

async_llm_pipeline = get_pipeline()

# Include AI Player routes
try:
    from api.routers.ai_player import router as ai_player_router

    app.include_router(ai_player_router)
except ImportError:
    # Try alternative import path
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from api.routers.ai_player import router as ai_player_router

    app.include_router(ai_player_router)


# Startup and shutdown handlers for async pipeline
@app.on_event("startup")
async def startup_event():
    """Initialize async systems on startup."""
    logger.info("Starting async LLM pipeline...")
    try:
        await initialize_pipeline()
        logger.info("Async LLM pipeline started successfully")
    except Exception as e:
        logger.error(f"Failed to start async LLM pipeline: {e}")

    # Ensure item definitions are loaded at startup
    logger.info("Loading item definitions...")
    if not ITEM_DEFINITIONS:
        load_item_definitions()
    logger.info(f"Loaded {len(ITEM_DEFINITIONS)} item definitions")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up async systems on shutdown."""
    logger.info("Shutting down async LLM pipeline...")
    try:
        await shutdown_pipeline()
        logger.info("Async LLM pipeline shut down successfully")
    except Exception as e:
        logger.error(f"Error shutting down async LLM pipeline: {e}")


# Clean up expired sessions periodically
def cleanup_sessions():
    """Remove expired sessions"""
    current_time = time.time()
    expired_sessions = []

    for session_id, session_data in sessions.items():
        if current_time - session_data["last_activity"] > SESSION_TIMEOUT:
            expired_sessions.append(session_id)

    for session_id in expired_sessions:
        logger.info(f"Removing expired session: {session_id}")
        del sessions[session_id]

    return len(expired_sessions)


# Models
class CommandRequest(BaseModel):
    """Request model for the /command endpoint."""

    input: str
    session_id: Optional[str] = None


class CommandResponse(BaseModel):
    """Response model for the /command endpoint."""

    output: str
    session_id: str
    game_state: Dict[str, Any]
    events: List[Dict[str, Any]] = []


class StateResponse(BaseModel):
    """Response model for the /state endpoint."""

    session_id: str
    game_state: Dict[str, Any]
    events: List[Dict[str, Any]] = []


# Helper functions
def get_or_create_session(session_id: Optional[str] = None) -> tuple[GameState, str]:
    """Get an existing session or create a new one."""
    # Clean up expired sessions
    cleanup_sessions()

    current_time = time.time()

    if session_id and session_id in sessions:
        # Update last activity time
        sessions[session_id]["last_activity"] = current_time
        return sessions[session_id]["game_state"], session_id

    # Create new session
    new_session_id = str(uuid.uuid4())
    # Ensure items are loaded before creating game state
    from .items import ITEM_DEFINITIONS, load_item_definitions

    if not ITEM_DEFINITIONS:
        load_item_definitions()
    game_state = GameState()
    sessions[new_session_id] = {"game_state": game_state, "last_activity": current_time, "created_at": current_time}
    logger.info(f"Created new game session: {new_session_id}")
    return game_state, new_session_id


# Web routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main game interface."""
    return templates.TemplateResponse("enhanced_game.html", {"request": request})


@app.get("/ai-demo", response_class=HTMLResponse)
async def ai_demo(request: Request):
    """Serve the AI player demo interface."""
    return templates.TemplateResponse("ai_player_demo.html", {"request": request})


# API Endpoints
@app.post("/command", response_model=CommandResponse)
async def process_command(command: CommandRequest):
    """
    Process a game command and return the result.

    Args:
        command: The command request containing input text and optional session ID

    Returns:
        CommandResponse with output, session ID, and game state
    """
    try:
        logger.info(f"Processing command: '{command.input}' for session: {command.session_id}")

        # Check if this is a new session being created
        is_new_session = command.session_id is None or command.session_id not in sessions

        # Get or create game session
        game_state, session_id = get_or_create_session(command.session_id)

        # If it's a new session, we want to include the welcome message in the response
        # even if the command doesn't produce a response
        initial_events = []
        if is_new_session:
            if hasattr(game_state, "events") and game_state.events:
                # Convert GameEvent objects to dictionaries
                initial_events = [
                    {"message": event.message, "event_type": event.event_type} for event in game_state.events
                ]
                logger.info(f"New session created with {len(initial_events)} initial events")

        # Process the input through the async LLM pipeline (with sync fallback)
        try:
            narrative_response, command_to_execute, action_results = async_llm_pipeline.process_request_sync(
                command.input, game_state, session_id
            )
            logger.debug(
                f"Processed via async pipeline: command='{command_to_execute}', actions={len(action_results or [])}"
            )
        except Exception as e:
            logger.error(f"Error in async pipeline, falling back to direct LLM: {e}")
            # Fallback to direct LLM processing
            narrative_response, command_to_execute, action_results = llm_gm.process_input(
                command.input, game_state, session_id
            )

        # Check if the LLM identified a specific command to execute
        if command_to_execute:
            logger.info(f"LLM identified command: '{command_to_execute}' from input: '{command.input}'")
            # Process the identified command through the regular game logic
            result = game_state.process_command(command_to_execute)
            logger.debug(f"Command result: {result}")

            # Use the command result but enhance it with the narrative response
            if result.get("success", False):
                # Only replace the message if the command was successful
                result["message"] = narrative_response
            else:
                # If command failed, append LLM response to explain
                result["message"] = f"{result.get('message', '')} {narrative_response}"
        else:
            # We have two cases here:
            # 1. Examining an object with pre-defined facts (the LLM will generate a description)
            # 2. A completely open-ended input that doesn't map to a specific command

            # For objects with special handling, check if the input is examining something
            examining_object = None
            input_lower = command.input.lower()
            if (
                input_lower.startswith("look at ")
                or input_lower.startswith("look ")
                or input_lower.startswith("examine ")
            ):
                parts = input_lower.replace("look at ", "").replace("look ", "").replace("examine ", "").strip().split()
                if len(parts) > 0:
                    examining_object = parts[0]

            # Log what we're doing
            if examining_object:
                logger.info(
                    f"Special handling for examining object: '{examining_object}' from input: '{command.input}'"
                )
            else:
                logger.info(f"Using narrative response for input: '{command.input}'")

            # In either case, use the narrative response directly
            result = {"success": True, "message": narrative_response, "recent_events": []}

        # Get any events that were generated
        events = []
        if hasattr(game_state, "event_formatter") and hasattr(game_state.event_formatter, "get_recent_events"):
            events = game_state.event_formatter.get_recent_events()

        # Include initial events for new sessions
        if is_new_session and initial_events:
            events = initial_events + (events or [])

        # Add action results as events
        if action_results:
            for action_result in action_results:
                if action_result.get("success"):
                    events.append(
                        {
                            "type": "action_result",
                            "action_type": action_result.get("action_type", "unknown"),
                            "message": action_result.get("message", "Action completed"),
                            "data": action_result,
                        }
                    )

        # Update session last activity time
        sessions[session_id]["last_activity"] = time.time()

        # Check if any memories were created during this interaction
        memories_created = 0
        if hasattr(llm_gm, "session_memories") and session_id in llm_gm.session_memories:
            # Count memories created in the last few seconds (indicating new memories from this interaction)
            current_time = time.time()
            memories_created = sum(
                1 for memory in llm_gm.session_memories[session_id] if current_time - memory.get("timestamp", 0) < 5
            )

        return CommandResponse(
            output=result.get("message", ""),
            session_id=session_id,
            game_state=game_state.get_snapshot(),
            events=events + ([{"type": "memory", "count": memories_created}] if memories_created > 0 else []),
        )
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing command: {str(e)}"
        )


@app.get("/state/{session_id}", response_model=StateResponse)
async def get_game_state(session_id: str):
    """
    Get the current game state for a session.

    Args:
        session_id: The session ID to get state for

    Returns:
        StateResponse with the current game state and events
    """
    if session_id not in sessions:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Update session last activity time
    sessions[session_id]["last_activity"] = time.time()
    game_state = sessions[session_id]["game_state"]

    # Get any events that were generated
    events = []
    if hasattr(game_state, "event_formatter") and hasattr(game_state.event_formatter, "get_recent_events"):
        events = game_state.event_formatter.get_recent_events()

    return StateResponse(session_id=session_id, game_state=game_state.get_snapshot(), events=events)


# Session management endpoints
@app.get("/sessions")
async def list_sessions():
    """List all active game sessions."""
    session_info = []
    for session_id, session_data in sessions.items():
        session_info.append(
            {
                "session_id": session_id,
                "created_at": session_data["created_at"],
                "last_activity": session_data["last_activity"],
                "age_seconds": time.time() - session_data["created_at"],
            }
        )

    return {"total_sessions": len(sessions), "sessions": session_info}


@app.post("/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset a game session to its initial state."""
    if session_id not in sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    current_time = time.time()
    game_state = GameState()
    sessions[session_id] = {"game_state": game_state, "last_activity": current_time, "created_at": current_time}

    return {"success": True, "message": "Session reset successfully", "session_id": session_id}


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a game session."""
    if session_id not in sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    del sessions[session_id]

    return {"success": True, "message": "Session deleted successfully"}


# LLM configuration endpoint
@app.post("/llm-config")
async def update_llm_config(request: Request):
    """Update LLM Game Master configuration."""
    data = await request.json()

    # Update Ollama URL if provided
    if "ollama_url" in data:
        llm_gm.ollama_url = data["ollama_url"]
        logger.info(f"Updated Ollama URL to: {data['ollama_url']}")

    # Update model if provided
    if "model" in data:
        llm_gm.model = data["model"]
        logger.info(f"Updated LLM model to: {data['model']}")

    # Update system prompt if provided
    if "system_prompt" in data:
        llm_gm.system_prompt = data["system_prompt"]
        logger.info("Updated LLM system prompt")

    # Test connection to Ollama
    try:
        test_url = f"{llm_gm.ollama_url}/api/version"
        logger.info(f"Testing Ollama connection at {test_url}")
        response = requests.get(test_url, timeout=5)
        response.raise_for_status()

        # Check if the model is available
        models_url = f"{llm_gm.ollama_url}/api/tags"
        models_response = requests.get(models_url, timeout=5)
        models_response.raise_for_status()
        models_data = models_response.json()

        # Get model names from response
        available_models = [model.get("name") for model in models_data.get("models", [])]

        # Check if our model is available
        model_available = llm_gm.model in available_models

        return {
            "success": True,
            "message": "LLM configuration updated successfully",
            "current_model": llm_gm.model,
            "ollama_connected": True,
            "model_available": model_available,
            "available_models": available_models,
        }
    except Exception as e:
        logger.error(f"Error connecting to Ollama: {str(e)}")
        return {
            "success": False,
            "message": f"Error connecting to Ollama: {str(e)}",
            "current_model": llm_gm.model,
            "ollama_connected": False,
        }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Enhanced health check endpoint with LLM service monitoring."""
    # Run cleanup to remove expired sessions
    expired_count = cleanup_sessions()

    # Get LLM service status
    llm_status = llm_gm.get_service_status()

    # Determine overall health
    overall_status = "healthy" if llm_status["is_healthy"] else "degraded"

    return {
        "status": overall_status,
        "active_sessions": len(sessions),
        "expired_sessions_removed": expired_count,
        "llm_service": {
            "status": "healthy" if llm_status["is_healthy"] else "unhealthy",
            "model": llm_status["model"],
            "ollama_url": llm_status["ollama_url"],
            "consecutive_failures": llm_status["consecutive_failures"],
            "last_check": llm_status["last_check"],
        },
        "fallback_available": True,
    }


# LLM service status endpoint
@app.get("/llm-status")
async def llm_status():
    """Get detailed LLM service status."""
    status = llm_gm.get_service_status()

    # Test connection if requested
    try:
        is_available = llm_gm.is_service_available()
        connection_test = {"available": is_available, "test_timestamp": time.time()}
    except Exception as e:
        connection_test = {"available": False, "error": str(e), "test_timestamp": time.time()}

    return {
        "service_status": status,
        "connection_test": connection_test,
        "configuration": {"model": llm_gm.model, "ollama_url": llm_gm.ollama_url, "max_retries": 3, "timeout": 30},
    }


# Async LLM Pipeline status endpoint
@app.get("/async-llm-status")
async def async_llm_status():
    """Get async LLM pipeline status and statistics."""
    try:
        stats = async_llm_pipeline.get_stats()
        is_healthy = async_llm_pipeline.is_healthy()

        return {
            "is_healthy": is_healthy,
            "statistics": stats,
            "pipeline_running": async_llm_pipeline.is_running,
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Error getting async LLM status: {e}")
        return {"is_healthy": False, "error": str(e), "timestamp": time.time()}


# Memory system status endpoint
@app.get("/memory-status")
async def memory_status():
    """Get memory system status and statistics."""
    try:
        from .memory import get_memory_manager

        manager = get_memory_manager()

        stats = manager.get_stats()

        return {
            "is_healthy": stats["total_memories"] < 10000,  # Arbitrary health threshold
            "statistics": stats,
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Error getting memory status: {e}")
        return {"is_healthy": False, "error": str(e), "timestamp": time.time()}


# Memory cleanup endpoint
@app.post("/memory-cleanup")
async def memory_cleanup():
    """Trigger memory cleanup and summarization."""
    try:
        from .memory import cleanup_old_memories

        summarized_count = cleanup_old_memories(age_threshold_hours=24.0)

        return {
            "success": True,
            "summarized_memories": summarized_count,
            "message": f"Cleaned up and summarized {summarized_count} old memories",
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Error during memory cleanup: {e}")
        return {"success": False, "error": str(e), "timestamp": time.time()}


# Error recovery system status endpoint
@app.get("/error-recovery-status")
async def error_recovery_status():
    """Get error recovery system status and health metrics."""
    try:
        from .error_recovery import get_error_recovery_system

        recovery_system = get_error_recovery_system()
        health = recovery_system.get_system_health()

        return {
            "is_healthy": health["is_healthy"],
            "health_score": health["health_score"],
            "system_health": health,
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Error getting error recovery status: {e}")
        return {"is_healthy": False, "error": str(e), "timestamp": time.time()}
