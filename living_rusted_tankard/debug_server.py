#!/usr/bin/env python3
"""
Minimal debug server to isolate web interface issues.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Debug AI Player Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AIPlayerConfig(BaseModel):
    personality: str
    name: str = "DebugAI"
    thinking_speed: float = 1.0
    auto_play: bool = False

@app.get("/debug/health")
async def health_check():
    """Simple health check."""
    return {"status": "ok", "timestamp": time.time()}

@app.post("/debug/ai-start-simple")
async def debug_ai_start_simple(config: AIPlayerConfig):
    """Ultra-simple AI start without any dependencies."""
    logger.info(f"Debug: Starting AI with config: {config}")
    
    import uuid
    session_id = str(uuid.uuid4())
    
    result = {
        "success": True,
        "session_id": session_id,
        "ai_player": {
            "name": config.name,
            "personality": config.personality,
            "greeting": f"Hello! I'm {config.name}, a debug AI player."
        },
        "debug_info": {
            "server": "debug_server.py",
            "timestamp": time.time()
        }
    }
    
    logger.info(f"Debug: Returning result: {result}")
    return result

@app.post("/debug/ai-start-with-imports")
async def debug_ai_start_with_imports(config: AIPlayerConfig):
    """Test AI start with actual imports to find the problematic one."""
    logger.info(f"Debug: Testing imports for AI start...")
    
    try:
        # Test each import individually
        logger.info("Debug: Importing uuid...")
        import uuid
        
        logger.info("Debug: Importing GameState...")
        from core.game_state import GameState
        
        logger.info("Debug: Importing AIPlayer...")
        from core.ai_player import AIPlayer, AIPlayerPersonality
        
        logger.info("Debug: Creating GameState...")
        game_state = GameState()
        
        logger.info("Debug: Creating AI Player...")
        personality = AIPlayerPersonality(config.personality)
        ai_player = AIPlayer(name=config.name, personality=personality)
        
        logger.info("Debug: Getting snapshot...")
        snapshot = game_state.get_snapshot()
        
        logger.info("Debug: Updating AI state...")
        ai_player.update_game_state(snapshot)
        
        session_id = str(uuid.uuid4())
        
        result = {
            "success": True,
            "session_id": session_id,
            "ai_player": {
                "name": ai_player.name,
                "personality": ai_player.personality.value,
                "greeting": "Debug AI with full imports created successfully!"
            }
        }
        
        logger.info(f"Debug: All imports successful, returning result")
        return result
        
    except Exception as e:
        logger.error(f"Debug: Import failed at step: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")