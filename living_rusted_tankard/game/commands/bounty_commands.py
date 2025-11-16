from typing import TYPE_CHECKING, List, Dict, Any, Optional

if TYPE_CHECKING:
    from core.game_state import GameState
    from core.player import PlayerState


# Helper function to find a bounty by partial ID or title from a list of bounties
def find_bounty_by_term(
    term: str, bounty_list: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    term_lower = term.lower()
    # Check for exact ID match first
    for bounty_data in bounty_list:
        if bounty_data["id"].lower() == term_lower:
            return bounty_data
    # Then check for partial title match
    for bounty_data in bounty_list:
        if term_lower in bounty_data["title"].lower():
            return bounty_data
    return None


def list_bounties_command(game_state: "GameState", args: List[str]) -> Dict[str, Any]:
    """Lists all available bounties."""
    bounty_manager = game_state.bounty_manager
    available_bounties = bounty_manager.get_available_bounties_on_notice_board(
        game_state.player
    )

    if not available_bounties:
        return {"success": True, "message": "There are currently no bounties posted."}

    message_lines = ["Available Bounties:"]
    for bounty in available_bounties:
        message_lines.append(
            f"  ID: {bounty.id}\n  Title: {bounty.title}\n  Issuer: {bounty.issuer}\n  Reward: {bounty.rewards.gold or 0} gold"
        )
        if bounty.rewards.items:
            # Handle case where items might be dicts with name/id
            item_names = []
            for item in bounty.rewards.items:
                if isinstance(item, dict):
                    item_names.append(item.get("name", item.get("id", str(item))))
                else:
                    item_names.append(str(item))
            message_lines.append(f"    Other items: {', '.join(item_names)}")
        message_lines.append("-" * 20)

    return {"success": True, "message": "\n".join(message_lines)}


def view_bounty_command(game_state: "GameState", args: List[str]) -> Dict[str, Any]:
    """Views details of a specific bounty. Usage: bounty view <bounty_id_or_partial_title>"""
    if not args:
        return {
            "success": False,
            "message": "Usage: bounty view <bounty_id_or_partial_title>",
        }

    term = " ".join(args)
    bounty_manager = game_state.bounty_manager

    # Search in available bounties (definitions or managed available ones)
    all_bounties_for_viewing = []
    for b_def in bounty_manager._bounty_definitions.values():
        managed_b = bounty_manager.managed_bounties_state.get(b_def.id)
        b_to_consider = managed_b if managed_b else b_def
        all_bounties_for_viewing.append(b_to_consider)

    # Convert to dicts for find_bounty_by_term, or adapt find_bounty_by_term
    bounties_as_dicts = [b.model_dump() for b in all_bounties_for_viewing]

    found_bounty_dict = find_bounty_by_term(term, bounties_as_dicts)

    if not found_bounty_dict:
        # Also check player's active bounties if not found in general list
        active_bounty_details = []
        for b_id in game_state.player.active_bounty_ids:
            b = bounty_manager.view_bounty(b_id)  # This gets the managed state
            if b:
                active_bounty_details.append(b.model_dump())
        found_bounty_dict = find_bounty_by_term(term, active_bounty_details)

    if not found_bounty_dict:
        return {"success": False, "message": f"Bounty matching '{term}' not found."}

    # Re-fetch the actual Bounty object to get its methods and proper structure
    bounty_obj = bounty_manager.view_bounty(found_bounty_dict["id"])
    if not bounty_obj:  # Should not happen if found_bounty_dict was populated
        return {"success": False, "message": "Error retrieving bounty details."}

    message_lines = [
        f"Bounty Details for: {bounty_obj.title} (ID: {bounty_obj.id})",
        f"Issuer: {bounty_obj.issuer}",
        f"Status: {bounty_obj.status.value}",
        f"Description: {bounty_obj.description}",
        "Objectives:",
    ]
    for i, obj in enumerate(bounty_obj.objectives):
        status_marker = "[X]" if obj.is_completed else "[ ]"
        message_lines.append(
            f"  {status_marker} {obj.description} ({obj.current_progress}/{obj.required_progress})"
        )

    message_lines.append("Rewards:")
    if bounty_obj.rewards.gold:
        message_lines.append(f"  Gold: {bounty_obj.rewards.gold}")
    if bounty_obj.rewards.items:
        message_lines.append(f"  Items: {', '.join(bounty_obj.rewards.items)}")
    if bounty_obj.rewards.reputation:
        rep_str = ", ".join(
            [f"{val} with {key}" for key, val in bounty_obj.rewards.reputation.items()]
        )
        message_lines.append(f"  Reputation: {rep_str}")
    if bounty_obj.rewards.xp:
        message_lines.append(f"  XP: {bounty_obj.rewards.xp}")
    if not any(
        [
            bounty_obj.rewards.gold,
            bounty_obj.rewards.items,
            bounty_obj.rewards.reputation,
            bounty_obj.rewards.xp,
        ]
    ):
        message_lines.append("  None specified.")

    return {"success": True, "message": "\n".join(message_lines)}


def accept_bounty_command(game_state: "GameState", args: List[str]) -> Dict[str, Any]:
    """Accepts a bounty. Usage: bounty accept <bounty_id_or_partial_title>"""
    if not args:
        return {
            "success": False,
            "message": "Usage: bounty accept <bounty_id_or_partial_title>",
        }

    term = " ".join(args)
    bounty_manager = game_state.bounty_manager
    player = game_state.player

    # Find from available bounties only
    available_bounties = bounty_manager.list_available_bounties(player=player)
    bounties_as_dicts = [b.model_dump() for b in available_bounties]
    found_bounty_dict = find_bounty_by_term(term, bounties_as_dicts)

    if not found_bounty_dict:
        return {
            "success": False,
            "message": f"Available bounty matching '{term}' not found or prerequisites not met.",
        }

    bounty_id_to_accept = found_bounty_dict["id"]

    if bounty_id_to_accept in player.active_bounty_ids:
        return {"success": False, "message": "You have already accepted this bounty."}
    if bounty_id_to_accept in player.completed_bounty_ids:
        return {"success": False, "message": "You have already completed this bounty."}

    success, message = bounty_manager.accept_bounty(
        player.id, bounty_id_to_accept, game_state.clock.current_time_hours
    )

    if success:
        if bounty_id_to_accept not in player.active_bounty_ids:
            player.active_bounty_ids.append(bounty_id_to_accept)

    return {"success": success, "message": message}


def complete_bounty_command(game_state: "GameState", args: List[str]) -> Dict[str, Any]:
    """Attempts to complete an active bounty. Usage: bounty complete <bounty_id_or_partial_title>"""
    if not args:
        return {
            "success": False,
            "message": "Usage: bounty complete <bounty_id_or_partial_title>",
        }

    term = " ".join(args)
    bounty_manager = game_state.bounty_manager
    player = game_state.player

    # Find from player's active bounties
    active_bounty_details = []
    for b_id in player.active_bounty_ids:
        b = bounty_manager.view_bounty(b_id)  # This gets the managed state
        if b:
            active_bounty_details.append(b.model_dump())

    found_bounty_dict = find_bounty_by_term(term, active_bounty_details)

    if not found_bounty_dict:
        return {
            "success": False,
            "message": f"Active bounty matching '{term}' not found.",
        }

    bounty_id_to_complete = found_bounty_dict["id"]

    # Simulate objective completion for now - this would normally be driven by gameplay
    # For testing, let's assume finding the bounty in active list and calling 'complete' is enough
    # if objectives are simple or auto-completed by some other event.
    # A more robust system would check actual objective progress.

    # For demo, let's find the active bounty and manually mark objectives if needed.
    # This is a placeholder for actual objective completion logic.
    # In a real game, objectives (like killing rats) would update progress in BountyManager.
    active_bounty_instance = bounty_manager.managed_bounties_state.get(
        bounty_id_to_complete
    )
    if active_bounty_instance:
        all_objectives_complete = True
        for i, obj in enumerate(active_bounty_instance.objectives):
            if not obj.is_completed:
                # Try to auto-complete simple "find" or "deliver to sel" objectives for testing
                if (
                    "find" in obj.description.lower()
                    or "deliver" in obj.description.lower()
                ):
                    # Simulate finding/delivering for the demo
                    bounty_manager.update_objective_progress(
                        player.id, bounty_id_to_complete, i, obj.required_progress
                    )
                else:  # For other objectives, assume they need external completion
                    all_objectives_complete = False
        if (
            not active_bounty_instance.are_all_objectives_completed()
            and all_objectives_complete
        ):
            # Re-check after potential auto-completion
            if not active_bounty_instance.are_all_objectives_completed():
                return {
                    "success": False,
                    "message": f"Objectives for '{active_bounty_instance.title}' are not yet complete.",
                }

    success, message = bounty_manager.complete_bounty(
        player.id, bounty_id_to_complete, game_state
    )

    if success:
        if bounty_id_to_complete in player.active_bounty_ids:
            player.active_bounty_ids.remove(bounty_id_to_complete)
        if bounty_id_to_complete not in player.completed_bounty_ids:
            player.completed_bounty_ids.append(bounty_id_to_complete)

    return {"success": success, "message": message}


def list_active_bounties_command(
    game_state: "GameState", args: List[str]
) -> Dict[str, Any]:
    """Lists all bounties currently accepted by the player."""
    player = game_state.player
    bounty_manager = game_state.bounty_manager

    if not player.active_bounty_ids:
        return {"success": True, "message": "You have no active bounties."}

    message_lines = ["Your Active Bounties:"]
    for bounty_id in player.active_bounty_ids:
        bounty = bounty_manager.view_bounty(bounty_id)  # Gets the managed state
        if bounty:
            message_lines.append(
                f"  ID: {bounty.id} - Title: {bounty.title} (Status: {bounty.status.value})"
            )
            for i, obj in enumerate(bounty.objectives):
                status_marker = "[X]" if obj.is_completed else "[ ]"
                message_lines.append(
                    f"    {status_marker} {obj.description} ({obj.current_progress}/{obj.required_progress})"
                )
        else:
            message_lines.append(f"  ID: {bounty_id} - (Error: Details not found)")
        message_lines.append("-" * 10)

    return {"success": True, "message": "\n".join(message_lines)}


def list_completed_bounties_command(
    game_state: "GameState", args: List[str]
) -> Dict[str, Any]:
    """Lists all bounties completed by the player."""
    player = game_state.player
    bounty_manager = game_state.bounty_manager

    if not player.completed_bounty_ids:
        return {"success": True, "message": "You have not completed any bounties yet."}

    message_lines = ["Your Completed Bounties:"]
    for bounty_id in player.completed_bounty_ids:
        bounty = bounty_manager.view_bounty(
            bounty_id
        )  # Gets the managed state (should be COMPLETED)
        if bounty:
            message_lines.append(f"  ID: {bounty.id} - Title: {bounty.title}")
        else:  # Fallback to definition if managed state somehow missing (shouldn't happen for completed)
            b_def = bounty_manager._bounty_definitions.get(bounty_id)
            if b_def:
                message_lines.append(
                    f"  ID: {b_def.id} - Title: {b_def.title} (Status: From Definition - Likely Completed)"
                )
            else:
                message_lines.append(f"  ID: {bounty_id} - (Error: Details not found)")
        message_lines.append("-" * 10)

    return {"success": True, "message": "\n".join(message_lines)}


# This dictionary maps command strings to their handler functions.
# It would be used by a command parsing system.
BOUNTY_COMMAND_HANDLERS = {
    "bounties": list_bounties_command,
    "bounty list": list_bounties_command,
    "bounty view": view_bounty_command,
    "bounty accept": accept_bounty_command,
    "bounty complete": complete_bounty_command,
    "bounty active": list_active_bounties_command,
    "bounty log": list_completed_bounties_command,
    "bounty completed": list_completed_bounties_command,
}
