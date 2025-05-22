"""
API routes for AI Player functionality.
"""

import asyncio
import json
import time
import random
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging

from core.ai_player import (
    AIPlayerPersonality
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-player", tags=["ai-player"])

class AIPlayerConfig(BaseModel):
    personality: str
    name: Optional[str] = None
    thinking_speed: Optional[float] = 2.0
    auto_play: Optional[bool] = False

class AIPlayerAction(BaseModel):
    command: str
    reasoning: Optional[str] = ""

# Store for AI player state and active sessions
ai_player_sessions: Dict[str, Dict[str, Any]] = {}

@router.post("/start")
async def start_ai_player(config: AIPlayerConfig):
    """Start an AI player session with specified personality."""
    logger.info(f"🚀 [TRACE] Function called with config: {config}")
    try:
        # Validate personality
        logger.info("🔍 [TRACE] Validating personality...")
        try:
            personality = AIPlayerPersonality(config.personality)
            logger.info(f"✅ [TRACE] Personality validated: {personality}")
        except ValueError:
            logger.error(f"❌ [TRACE] Invalid personality: {config.personality}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid personality. Must be one of: {[p.value for p in AIPlayerPersonality]}"
            )
        
        # Create AI player directly without any LLM calls
        logger.info("🔍 [TRACE] Importing modules...")
        import uuid
        logger.info("🔍 [TRACE] Importing GameState...")
        from core.game_state import GameState
        logger.info("🔍 [TRACE] Importing AIPlayer...")
        from core.ai_player import AIPlayer
        
        logger.info("🔍 [TRACE] Creating session ID...")
        session_id = str(uuid.uuid4())
        logger.info("🔍 [TRACE] Creating GameState...")
        game_state = GameState()
        logger.info("🔍 [TRACE] GameState created successfully")
        
        # Create AI player instance directly
        ai_player = AIPlayer(
            name=config.name or "Gemma",
            personality=personality,
            model="gemma2:2b"
        )
        
        if config.thinking_speed:
            ai_player.thinking_delay = config.thinking_speed
        
        # Set up AI player
        ai_player.session_id = session_id
        ai_player.update_game_state(game_state.get_snapshot())
        ai_player.is_active = True
        
        # Store session info including the AI player instance
        ai_player_sessions[session_id] = {
            "personality": config.personality,
            "name": ai_player.name,
            "auto_play": config.auto_play,
            "is_active": True,
            "last_action": time.time(),
            "ai_player": ai_player  # Store the actual AI player instance
        }
        
        return {
            "success": True,
            "session_id": session_id,
            "ai_player": {
                "name": ai_player.name,
                "personality": ai_player.personality.value,
                "greeting": ai_player.personality_traits[ai_player.personality]["greeting"]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to start AI player: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{session_id}")
async def get_ai_player_status(session_id: str):
    """Get the current status of an AI player session."""
    if session_id not in ai_player_sessions:
        raise HTTPException(status_code=404, detail="AI player session not found")
    
    session_info = ai_player_sessions[session_id]
    ai_player = session_info["ai_player"]
    
    return {
        "session_id": session_id,
        "ai_player": {
            "name": ai_player.name,
            "personality": ai_player.personality.value,
            "is_active": ai_player.is_active,
            "action_count": len(ai_player.action_history),
            "last_action": session_info.get("last_action", 0)
        },
        "recent_actions": [
            {
                "command": action.command,
                "reasoning": action.reasoning,
                "timestamp": action.timestamp
            }
            for action in ai_player.action_history[-5:]  # Last 5 actions
        ]
    }

@router.post("/action/{session_id}")
async def generate_ai_action(session_id: str):
    """Generate and execute the next AI player action."""
    if session_id not in ai_player_sessions:
        raise HTTPException(status_code=404, detail="AI player session not found")
    
    ai_player = ai_player_sessions[session_id]["ai_player"]
    
    try:
        # Generate action based on current game state
        game_context = ai_player.get_game_context()
        action = await ai_player.generate_action(game_context)
        
        # Execute the action directly via GameState
        from core.game_state import GameState
        
        # Get the game state from session (or create new one)
        game_state = GameState()
        result = game_state.process_command(action)
        
        # Update AI player's game state
        ai_player.update_game_state(game_state.get_snapshot())
        
        # Record the action
        ai_player.record_action(action, "AI-generated action")
        
        # Update session info
        ai_player_sessions[session_id]["last_action"] = time.time()
        
        return {
            "success": True,
            "action": action,
            "result": result.get('message', ''),
            "game_state": game_state.get_snapshot(),
            "ai_reasoning": f"As a {ai_player.personality.value}, I chose to: {action}"
        }
            
    except Exception as e:
        logger.error(f"Failed to generate AI action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/action-stream/{session_id}")
async def stream_ai_action_generation(session_id: str):
    """Stream the AI player's thought process and action generation."""
    if session_id not in ai_player_sessions:
        raise HTTPException(status_code=404, detail="AI player session not found")
    
    ai_player = ai_player_sessions[session_id]["ai_player"]
    
    async def generate():
        try:
            # Send thinking indicator
            yield f"data: {json.dumps({'type': 'thinking', 'message': f'{ai_player.name} is thinking...'})}\n\n"
            
            # Add personality-based thinking delay
            await asyncio.sleep(ai_player.thinking_delay)
            
            # Get game context
            game_context = ai_player.get_game_context()
            
            # Stream the action generation
            yield f"data: {json.dumps({'type': 'generating', 'message': f'{ai_player.name} is deciding what to do...'})}\n\n"
            
            # Generate action with streaming
            action_text = ""
            async for token in ai_player.generate_action_stream(game_context):
                action_text += token
                yield f"data: {json.dumps({'type': 'token', 'token': token, 'partial_action': action_text.strip()})}\n\n"
            
            # Clean up the final action
            final_action = action_text.strip().split('\n')[0].strip()
            if not final_action:
                final_action = "look around"
            
            yield f"data: {json.dumps({'type': 'action_ready', 'action': final_action})}\n\n"
            
            # Execute the action
            yield f"data: {json.dumps({'type': 'executing', 'message': f'{ai_player.name} performs: {final_action}'})}\n\n"
            
            # Execute directly via GameState
            from core.game_state import GameState
            
            game_state = GameState()
            result = game_state.process_command(final_action)
            
            # Update AI player state
            ai_player.update_game_state(game_state.get_snapshot())
            ai_player.record_action(final_action, "Streamed AI action")
            ai_player_sessions[session_id]["last_action"] = time.time()
            
            # Send result
            yield f"data: {json.dumps({'type': 'result', 'action': final_action, 'output': result.get('message', ''), 'game_state': game_state.get_snapshot()})}\n\n"
            
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in AI action stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@router.post("/auto-play/{session_id}")
async def toggle_auto_play(session_id: str, background_tasks: BackgroundTasks):
    """Toggle auto-play mode for the AI player."""
    if session_id not in ai_player_sessions:
        raise HTTPException(status_code=404, detail="AI player session not found")
    
    session_info = ai_player_sessions[session_id]
    session_info["auto_play"] = not session_info.get("auto_play", False)
    
    if session_info["auto_play"]:
        # Start auto-play background task
        background_tasks.add_task(auto_play_loop, session_id)
    
    return {
        "success": True,
        "auto_play": session_info["auto_play"]
    }

async def auto_play_loop(session_id: str):
    """Background task for auto-play mode."""
    if session_id not in ai_player_sessions:
        return
    ai_player = ai_player_sessions[session_id]["ai_player"]
    
    while (session_id in ai_player_sessions and 
           ai_player_sessions[session_id].get("auto_play", False)):
        
        try:
            # Wait before next action
            await asyncio.sleep(ai_player.thinking_delay + random.uniform(2, 5))
            
            # Generate and execute action
            game_context = ai_player.get_game_context()
            action = await ai_player.generate_action(game_context)
            
            from core.game_state import GameState
            
            game_state = GameState()
            result = game_state.process_command(action)
            ai_player.update_game_state(game_state.get_snapshot())
            ai_player.record_action(action, "Auto-play action")
            ai_player_sessions[session_id]["last_action"] = time.time()
            
        except Exception as e:
            logger.error(f"Error in auto-play loop: {e}")
            break
    
    # Disable auto-play if loop exits
    if session_id in ai_player_sessions:
        ai_player_sessions[session_id]["auto_play"] = False

@router.delete("/stop/{session_id}")
async def stop_ai_player(session_id: str):
    """Stop an AI player session."""
    if session_id not in ai_player_sessions:
        raise HTTPException(status_code=404, detail="AI player session not found")
    
    # Mark session as inactive
    ai_player_sessions[session_id]["is_active"] = False
    ai_player_sessions[session_id]["auto_play"] = False
    
    # Clean up
    ai_player = ai_player_sessions[session_id]["ai_player"]
    ai_player.is_active = False
    
    return {
        "success": True,
        "message": f"AI player session {session_id} stopped"
    }

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify router is working."""
    return {"status": "ok", "message": "AI Player router is working"}

@router.post("/start-simple")
async def start_ai_player_simple(config: AIPlayerConfig):
    """Simplified AI player start for testing."""
    logger.info(f"🟢 [SIMPLE] Function reached with config: {config}")
    import uuid
    session_id = str(uuid.uuid4())
    logger.info(f"🟢 [SIMPLE] Returning successful response")
    
    return {
        "success": True,
        "session_id": session_id,
        "ai_player": {
            "name": config.name or "TestAI",
            "personality": config.personality,
            "greeting": "Hello! This is a simplified AI player for testing."
        }
    }

@router.get("/personalities")
async def list_personalities():
    """Get available AI player personalities."""
    personalities = []
    
    for personality in AIPlayerPersonality:
        # Create temporary AI player to get personality traits
        from core.ai_player import AIPlayer
        temp_ai = AIPlayer(personality=personality)
        traits = temp_ai.personality_traits[personality]
        
        personalities.append({
            "id": personality.value,
            "name": personality.value.replace("_", " ").title(),
            "style": traits["interaction_style"],
            "decision_pattern": traits["decision_pattern"],
            "preferred_commands": traits["preferred_commands"]
        })
    
    return {"personalities": personalities}