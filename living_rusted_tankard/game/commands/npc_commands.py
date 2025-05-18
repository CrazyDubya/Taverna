"""Command handlers for NPC interactions."""

from typing import Dict, Any, List

def handle_look_npcs(presence_manager, current_room: str = None) -> Dict[str, Any]:
    """
    Handle looking for NPCs in the current location.
    
    Args:
        presence_manager: PresenceManager instance
        current_room: ID of the current room (optional)
        
    Returns:
        Dict with result and message
    """
    # Get present NPCs, optionally filtered by room
    present_npcs = presence_manager.get_present_npcs(room=current_room)
    
    if not present_npcs:
        return {
            "success": True,
            "message": "There's no one else here right now.",
            "npcs_present": []
        }
    
    # Format the message based on number of NPCs
    if len(present_npcs) == 1:
        message = f"You see {present_npcs[0]} here."
    else:
        npc_list = ", ".join(present_npcs[:-1]) + f", and {present_npcs[-1]}"
        message = f"You see {npc_list} here."
    
    return {
        "success": True,
        "message": message,
        "npcs_present": present_npcs
    }

def handle_where_npc(npc_id: str, presence_manager) -> Dict[str, Any]:
    """
    Handle checking where an NPC is.
    
    Args:
        npc_id: ID of the NPC to locate
        presence_manager: PresenceManager instance
        
    Returns:
        Dict with result and message
    """
    # Ensure we have the latest presence data
    presence_manager.update_all()
    
    # Find the NPC in the presence manager
    npc = next((npc for npc in presence_manager.npcs.values() 
               if npc.npc_id == npc_id), None)
    
    if not npc:
        return {
            "success": False,
            "message": f"You don't know anyone named {npc_id}.",
            "found": False
        }
    
    if not npc.is_present:
        return {
            "success": True,
            "message": f"{npc_id} is not currently in the tavern.",
            "found": True,
            "present": False
        }
    
    room_msg = f"the {npc.current_room}" if npc.current_room else "the tavern"
    
    return {
        "success": True,
        "message": f"{npc_id} is in {room_msg}.",
        "found": True,
        "present": True,
        "room": npc.current_room
    }
