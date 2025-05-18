"""
FastAPI endpoints for The Living Rusted Tankard game.

This module provides a REST API interface to interact with the game state.
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
import os
from pathlib import Path

from .game_state import GameState
from .event_formatter import EventFormatter

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

# In-memory storage for game sessions
sessions: Dict[str, GameState] = {}

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
    if session_id and session_id in sessions:
        return sessions[session_id], session_id
    
    # Create new session
    new_session_id = str(uuid.uuid4())
    game_state = GameState()
    sessions[new_session_id] = game_state
    return game_state, new_session_id

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
        # Get or create game session
        game_state, session_id = get_or_create_session(command.session_id)
        
        # Process the command
        result = game_state.process_command(command.input)
        
        # Get any events that were generated
        events = []
        if hasattr(game_state, 'event_formatter') and hasattr(game_state.event_formatter, 'get_recent_events'):
            events = game_state.event_formatter.get_recent_events()
        
        return CommandResponse(
            output=result.get('message', ''),
            session_id=session_id,
            game_state=game_state.get_snapshot(),
            events=events
        )
    except Exception as e:
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    game_state = sessions[session_id]
    
    # Get any events that were generated
    events = []
    if hasattr(game_state, 'event_formatter') and hasattr(game_state.event_formatter, 'get_recent_events'):
        events = game_state.event_formatter.get_recent_events()
    
    return StateResponse(
        session_id=session_id,
        game_state=game_state.get_snapshot(),
        events=events
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
