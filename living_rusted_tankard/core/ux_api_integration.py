"""
API integration for UX enhancements.

This module provides endpoints and integration for:
- Enhanced web interface
- Audio system management
- Economy balancing
- Mobile responsiveness features
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, List, Any, Optional
import logging
import json
from pathlib import Path

from .audio_system import (
    audio_manager,
    game_audio,
    get_audio_config,
    process_game_audio,
)
from .economy_balancing import economy_balancer, get_economic_status, get_balanced_price
from .game_state import GameState as OptimizedGameState

logger = logging.getLogger(__name__)

# Create router for UX enhancement endpoints
ux_router = APIRouter(prefix="/ux", tags=["user-experience"])


@ux_router.get("/audio/config")
async def get_audio_configuration() -> Dict[str, Any]:
    """Get audio system configuration for client."""
    try:
        return {
            "status": "success",
            "config": get_audio_config(),
            "features": [
                "Ambient tavern sounds",
                "Dynamic sound effects",
                "Event-triggered audio",
                "Volume controls",
                "Audio asset management",
            ],
        }
    except Exception as e:
        logger.error(f"Error getting audio config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audio configuration")


@ux_router.post("/audio/trigger")
async def trigger_audio_event(request: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger an audio event."""
    try:
        event_type = request.get("event_type")
        session_id = request.get("session_id")
        context = request.get("context", {})

        if not event_type:
            raise HTTPException(status_code=400, detail="event_type is required")

        commands = audio_manager.trigger_event(event_type, context)

        return {
            "status": "success",
            "audio_commands": commands,
            "event_type": event_type,
        }
    except Exception as e:
        logger.error(f"Error triggering audio event: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger audio event")


@ux_router.get("/audio/assets")
async def get_audio_assets() -> Dict[str, Any]:
    """Get list of available audio assets."""
    try:
        assets = []
        for asset_id, asset in audio_manager.assets.items():
            assets.append(
                {
                    "id": asset.id,
                    "name": asset.name,
                    "type": asset.audio_type.value,
                    "file_path": f"/static/audio/{asset.file_path}",
                    "volume": asset.volume,
                    "loop": asset.loop,
                    "tags": asset.tags,
                }
            )

        return {"status": "success", "assets": assets, "total_assets": len(assets)}
    except Exception as e:
        logger.error(f"Error getting audio assets: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audio assets")


@ux_router.post("/audio/settings")
async def update_audio_settings(request: Dict[str, Any]) -> Dict[str, Any]:
    """Update audio settings."""
    try:
        master_volume = request.get("master_volume")
        if master_volume is not None:
            audio_manager.set_master_volume(float(master_volume))

        enabled = request.get("enabled")
        if enabled is not None:
            audio_manager.enable_audio(bool(enabled))

        volume_settings = request.get("volume_settings", {})
        for audio_type_str, volume in volume_settings.items():
            try:
                from .audio_system import AudioType

                audio_type = AudioType(audio_type_str)
                audio_manager.set_volume(audio_type, float(volume))
            except ValueError:
                logger.warning(f"Invalid audio type: {audio_type_str}")

        return {
            "status": "success",
            "message": "Audio settings updated",
            "current_config": get_audio_config(),
        }
    except Exception as e:
        logger.error(f"Error updating audio settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update audio settings")


@ux_router.get("/economy/status/{player_id}")
async def get_player_economy_status(player_id: str) -> Dict[str, Any]:
    """Get player's economy status and progression."""
    try:
        status = get_economic_status(player_id)
        return {"status": "success", "player_id": player_id, "economy": status}
    except Exception as e:
        logger.error(f"Error getting economy status for {player_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get economy status")


@ux_router.get("/economy/pricing/{player_id}")
async def get_dynamic_pricing(
    player_id: str, items: Optional[str] = None
) -> Dict[str, Any]:
    """Get dynamic pricing information for items."""
    try:
        if items:
            item_list = [item.strip() for item in items.split(",")]
        else:
            # Default items to show pricing for
            item_list = [
                "ale",
                "bread",
                "healing_potion",
                "room_basic",
                "old_toms_surprise",
            ]

        pricing = economy_balancer.get_pricing_preview(player_id, item_list)

        return {
            "status": "success",
            "player_id": player_id,
            "pricing": pricing,
            "items_checked": len(item_list),
        }
    except Exception as e:
        logger.error(f"Error getting pricing for {player_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pricing information")


@ux_router.get("/economy/events")
async def get_active_economic_events() -> Dict[str, Any]:
    """Get currently active economic events."""
    try:
        active_events = []
        for event in economy_balancer.active_events:
            active_events.append(
                {
                    "id": event.id,
                    "name": event.name,
                    "description": event.description,
                    "duration_hours": event.duration_hours,
                    "price_modifiers": event.price_modifiers,
                    "active_until": event.active_until.isoformat()
                    if event.active_until
                    else None,
                }
            )

        return {
            "status": "success",
            "active_events": active_events,
            "total_events": len(active_events),
        }
    except Exception as e:
        logger.error(f"Error getting economic events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get economic events")


@ux_router.get("/interface/config")
async def get_interface_config() -> Dict[str, Any]:
    """Get enhanced interface configuration."""
    try:
        return {
            "status": "success",
            "features": {
                "mobile_responsive": True,
                "command_history": True,
                "audio_support": True,
                "performance_optimized": True,
                "dynamic_pricing": True,
                "progressive_economy": True,
            },
            "ui_enhancements": {
                "enhanced_typography": True,
                "animated_feedback": True,
                "contextual_help": True,
                "quick_actions": True,
                "conversation_options": True,
                "visual_feedback": True,
            },
            "mobile_features": {
                "responsive_layout": True,
                "touch_optimized": True,
                "swipe_gestures": False,  # Future enhancement
                "voice_input": False,  # Future enhancement
            },
        }
    except Exception as e:
        logger.error(f"Error getting interface config: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get interface configuration"
        )


@ux_router.post("/feedback")
async def submit_user_feedback(request: Dict[str, Any]) -> Dict[str, Any]:
    """Submit user feedback about UX improvements."""
    try:
        feedback_type = request.get("type", "general")
        rating = request.get("rating", 0)
        comments = request.get("comments", "")
        session_id = request.get("session_id")
        features_used = request.get("features_used", [])

        # Log feedback for analysis
        logger.info(
            f"User feedback: {feedback_type} - Rating: {rating}/5 - Features: {features_used}"
        )

        # In a real implementation, this would be stored in a database
        feedback_data = {
            "type": feedback_type,
            "rating": rating,
            "comments": comments,
            "session_id": session_id,
            "features_used": features_used,
            "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
        }

        return {
            "status": "success",
            "message": "Thank you for your feedback!",
            "feedback_id": f"feedback_{session_id}_{len(comments)}",
        }
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@ux_router.get("/analytics/usage")
async def get_usage_analytics() -> Dict[str, Any]:
    """Get UX feature usage analytics."""
    try:
        # In a real implementation, this would query actual usage data
        return {
            "status": "success",
            "analytics": {
                "total_sessions": 150,
                "mobile_sessions": 45,
                "desktop_sessions": 105,
                "audio_enabled_sessions": 89,
                "command_history_usage": 78,
                "quick_actions_usage": 134,
                "average_session_duration": 28.5,
                "user_satisfaction": 4.2,
            },
            "feature_adoption": {
                "enhanced_ui": 95.3,
                "audio_system": 59.3,
                "command_history": 52.0,
                "quick_actions": 89.3,
                "mobile_interface": 30.0,
            },
            "performance_metrics": {
                "average_load_time": 1.2,
                "cache_hit_rate": 87.5,
                "error_rate": 0.8,
                "user_retention": 73.2,
            },
        }
    except Exception as e:
        logger.error(f"Error getting usage analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get usage analytics")


# Enhanced command processing with UX integration
async def process_command_with_ux(command_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process command with UX enhancements integrated."""
    try:
        session_id = command_data.get("session_id")
        user_input = command_data.get("input", "")

        # Process the command normally first
        # This would integrate with the main command processing system

        # Add UX enhancements
        response = {
            "output": "Command processed with UX enhancements",
            "session_id": session_id,
            "events": [],
            "audio_commands": [],
            "ui_updates": {},
        }

        # Add audio triggers based on command
        if "gold" in user_input.lower():
            audio_commands = process_game_audio(
                [{"type": "success", "message": "gold gained"}], session_id
            )
            response["audio_commands"] = audio_commands

        # Add UI updates for enhanced feedback
        response["ui_updates"] = {
            "animate_elements": ["gold-amount"] if "gold" in user_input.lower() else [],
            "highlight_sidebar": (
                True
                if any(
                    word in user_input.lower()
                    for word in ["status", "inventory", "quest"]
                )
                else False
            ),
            "show_quick_actions": True,
        }

        return response

    except Exception as e:
        logger.error(f"Error processing command with UX: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to process command with UX enhancements"
        )


# Utility functions for integration
def get_enhanced_game_response(
    base_response: Dict[str, Any], session_id: str
) -> Dict[str, Any]:
    """Enhance standard game response with UX improvements."""
    enhanced_response = base_response.copy()

    # Add audio commands if events present
    if "events" in enhanced_response:
        audio_commands = process_game_audio(enhanced_response["events"], session_id)
        enhanced_response["audio_commands"] = audio_commands

    # Add UI enhancement hints
    enhanced_response["ui_enhancements"] = {
        "auto_scroll": True,
        "animate_new_content": True,
        "update_sidebar": True,
    }

    # Add mobile-specific optimizations
    enhanced_response["mobile_optimizations"] = {
        "compact_layout": True,
        "touch_friendly": True,
    }

    return enhanced_response


def initialize_ux_session(session_id: str) -> Dict[str, Any]:
    """Initialize UX enhancements for a new session."""
    # Initialize audio
    audio_commands = game_audio.initialize_session_audio(session_id)

    # Get initial economic status
    economic_status = get_economic_status(session_id)

    return {
        "audio_commands": audio_commands,
        "economic_status": economic_status,
        "ui_config": {
            "command_history_enabled": True,
            "quick_actions_enabled": True,
            "audio_enabled": True,
            "mobile_optimized": True,
        },
    }
