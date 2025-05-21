"""
FastAPI endpoints for The Living Rusted Tankard game.

This module provides a REST API interface to interact with the game state
and serves the web interface.
"""
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
import os
import time
from pathlib import Path
import logging

from .game_state import GameState
from .event_formatter import EventFormatter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="The Living Rusted Tankard API",
    description="REST API for The Living Rusted Tankard text-based RPG",
    version="0.1.0"
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

# Clean up expired sessions periodically
def cleanup_sessions():
    """Remove expired sessions"""
    current_time = time.time()
    expired_sessions = []
    
    for session_id, session_data in sessions.items():
        if current_time - session_data['last_activity'] > SESSION_TIMEOUT:
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
        sessions[session_id]['last_activity'] = current_time
        return sessions[session_id]['game_state'], session_id
    
    # Create new session
    new_session_id = str(uuid.uuid4())
    game_state = GameState()
    sessions[new_session_id] = {
        'game_state': game_state,
        'last_activity': current_time,
        'created_at': current_time
    }
    logger.info(f"Created new game session: {new_session_id}")
    return game_state, new_session_id

# Web routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main game interface."""
    return templates.TemplateResponse(
        "game.html", 
        {"request": request}
    )

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
        
        # Get or create game session
        game_state, session_id = get_or_create_session(command.session_id)
        
        # Process the command
        result = game_state.process_command(command.input)
        logger.debug(f"Command result: {result}")
        
        # Get any events that were generated
        events = []
        if hasattr(game_state, 'event_formatter') and hasattr(game_state.event_formatter, 'get_recent_events'):
            events = game_state.event_formatter.get_recent_events()
        
        # Update session last activity time
        sessions[session_id]['last_activity'] = time.time()
        
        return CommandResponse(
            output=result.get('message', ''),
            session_id=session_id,
            game_state=game_state.get_snapshot(),
            events=events
        )
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing command: {str(e)}"
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Update session last activity time
    sessions[session_id]['last_activity'] = time.time()
    game_state = sessions[session_id]['game_state']
    
    # Get any events that were generated
    events = []
    if hasattr(game_state, 'event_formatter') and hasattr(game_state.event_formatter, 'get_recent_events'):
        events = game_state.event_formatter.get_recent_events()
    
    return StateResponse(
        session_id=session_id,
        game_state=game_state.get_snapshot(),
        events=events
    )

# Session management endpoints
@app.get("/sessions")
async def list_sessions():
    """List all active game sessions."""
    session_info = []
    for session_id, session_data in sessions.items():
        session_info.append({
            "session_id": session_id,
            "created_at": session_data['created_at'],
            "last_activity": session_data['last_activity'],
            "age_seconds": time.time() - session_data['created_at']
        })
    
    return {
        "total_sessions": len(sessions),
        "sessions": session_info
    }

@app.post("/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset a game session to its initial state."""
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    current_time = time.time()
    game_state = GameState()
    sessions[session_id] = {
        'game_state': game_state,
        'last_activity': current_time,
        'created_at': current_time
    }
    
    return {
        "success": True,
        "message": "Session reset successfully",
        "session_id": session_id
    }

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a game session."""
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    del sessions[session_id]
    
    return {
        "success": True,
        "message": "Session deleted successfully"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Run cleanup to remove expired sessions
    expired_count = cleanup_sessions()
    
    return {
        "status": "healthy",
        "active_sessions": len(sessions),
        "expired_sessions_removed": expired_count
    }
