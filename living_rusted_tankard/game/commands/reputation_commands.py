from typing import TYPE_CHECKING, List, Dict, Any, Optional

if TYPE_CHECKING:
    from core.game_state import GameState
    from core.player import PlayerState

# Assuming reputation utilities are in core.reputation
from core.reputation import get_reputation, get_reputation_tier

def show_reputation_command(game_state: 'GameState', args: List[str]) -> Dict[str, Any]:
    """Displays the player's reputation with various entities."""
    player = game_state.player
    
    if not player.reputation:
        return {"success": True, "message": "You have not yet established a reputation with anyone of note."}
        
    message_lines = ["Your Reputation:"]
    for entity_id, score in player.reputation.items():
        tier = get_reputation_tier(score)
        # Attempt to get a more descriptive name for the entity_id
        # This might involve looking up NPC names from NPCManager or a predefined faction list
        entity_name = entity_id # Default to ID
        
        npc = game_state.npc_manager.get_npc(entity_id)
        if npc:
            entity_name = f"{npc.name} (NPC)"
        elif entity_id == "TavernStaff": # Example faction
             entity_name = "Tavern Staff (Faction)"
        # Add more known factions or entity types here if needed
             
        message_lines.append(f"  - {entity_name}: {score} ({tier})")
        
    return {"success": True, "message": "\n".join(message_lines)}

REPUTATION_COMMAND_HANDLERS = {
    "reputation": show_reputation_command,
    "rep": show_reputation_command,
    "rep status": show_reputation_command,
}
