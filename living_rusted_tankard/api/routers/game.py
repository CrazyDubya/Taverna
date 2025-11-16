"""API endpoints for the integrated game with all phase systems."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

from core.game_state import GameState

router = APIRouter()

# Store game sessions in memory (in production, use database)
game_sessions: Dict[str, GameState] = {}


class CommandRequest(BaseModel):
    command: str
    session_id: Optional[str] = None


class GameResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    game_state: Dict[str, Any]
    recent_events: list = []


@router.post("/game/new-session", response_model=GameResponse)
def create_new_game_session():
    """Create a new integrated game session with all phase systems."""
    session_id = str(uuid.uuid4())

    # Create new GameState with all integrated systems
    game_state = GameState()
    game_sessions[session_id] = game_state

    # Get initial state
    initial_look = game_state.process_command("look")

    return GameResponse(
        success=True,
        message=initial_look["message"],
        session_id=session_id,
        game_state={
            "time": game_state.clock.get_current_time().total_hours,
            "player_gold": game_state.player.gold,
            "player_energy": game_state.player.energy,
            "player_tiredness": game_state.player.tiredness,
            "location": "The Rusted Tankard",
        },
        recent_events=initial_look.get("recent_events", []),
    )


@router.post("/game/command", response_model=GameResponse)
def process_game_command(request: CommandRequest):
    """Process a command in the integrated game."""
    if not request.session_id or request.session_id not in game_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found. Please create a new session.",
        )

    game_state = game_sessions[request.session_id]

    try:
        # Process command through integrated game state
        result = game_state.process_command(request.command)

        # Get current game state for response
        current_state = {
            "time": game_state.clock.get_current_time().total_hours,
            "player_gold": game_state.player.gold,
            "player_energy": game_state.player.energy,
            "player_tiredness": game_state.player.tiredness,
            "location": "The Rusted Tankard",
            "has_room": game_state.player.has_room,
            "inventory_count": len(game_state.player.inventory.items),
        }

        return GameResponse(
            success=result["success"],
            message=result["message"],
            session_id=request.session_id,
            game_state=current_state,
            recent_events=result.get("recent_events", []),
        )

    except Exception as e:
        return GameResponse(
            success=False,
            message=f"Error processing command: {str(e)}",
            session_id=request.session_id,
            game_state={},
            recent_events=[],
        )


@router.get("/game/sessions/{session_id}/state", response_model=Dict[str, Any])
def get_game_state(session_id: str):
    """Get the current state of a game session."""
    if session_id not in game_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found"
        )

    game_state = game_sessions[session_id]

    return {
        "session_id": session_id,
        "time": game_state.clock.get_current_time().total_hours,
        "player": {
            "gold": game_state.player.gold,
            "energy": game_state.player.energy,
            "tiredness": game_state.player.tiredness,
            "has_room": game_state.player.has_room,
            "inventory": dict(game_state.player.inventory.items),
            "active_bounties": list(game_state.player.active_bounty_ids),
            "completed_bounties": list(game_state.player.completed_bounty_ids),
        },
        "world": {
            "current_room": game_state.room_manager.current_room_id,
            "present_npcs": [
                {"id": npc.id, "name": npc.name}
                for npc in game_state.npc_manager.get_present_npcs()
            ],
        },
        "systems": {
            "phase2_available": hasattr(game_state, "atmosphere_manager"),
            "phase3_available": hasattr(game_state, "npc_psychology"),
            "phase4_available": hasattr(game_state, "narrative_orchestrator"),
        },
    }


@router.delete("/game/sessions/{session_id}")
def delete_game_session(session_id: str):
    """Delete a game session."""
    if session_id not in game_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Game session not found"
        )

    del game_sessions[session_id]
    return {"message": f"Session {session_id} deleted successfully"}


@router.get("/game/sessions")
def list_active_sessions():
    """List all active game sessions."""
    return {
        "active_sessions": len(game_sessions),
        "sessions": [
            {
                "session_id": session_id,
                "player_gold": game_state.player.gold,
                "game_time": game_state.clock.get_current_time().total_hours,
            }
            for session_id, game_state in game_sessions.items()
        ],
    }
