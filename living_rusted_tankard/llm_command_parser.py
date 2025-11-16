#!/usr/bin/env python3
"""LLM-assisted command parser - the ACTUAL solution."""

from typing import Dict, Any, Optional
import json


class LLMCommandParser:
    """Use LLM to parse natural language into game commands."""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def parse_natural_command(
        self, user_input: str, game_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse natural language into game command using LLM."""

        # If no LLM available, fall back to basic parsing
        if not self.llm_client:
            return self._basic_parse(user_input)

        # Create prompt for LLM
        prompt = """You are parsing commands for a text adventure game set in a tavern.

Current context:
- Player has {game_context.get('gold', 0)} gold
- Location: {game_context.get('location', 'tavern')}
- Time: {game_context.get('time_display', 'unknown')}
- NPCs present: {', '.join(game_context.get('npcs', [])) or 'none'}

Valid commands include:
- look, wait [hours], status, inventory, help
- move [room], buy [item], use [item], gamble [amount]
- npcs, interact [npc] [action], bounties, jobs
- sleep [hours], quit

User said: "{user_input}"

Parse this into a valid game command. If unclear, make your best guess based on context.
If completely unparseable, respond with a narrative explanation.

Respond in JSON format:
{{
    "command": "valid game command or null",
    "confidence": 0.0-1.0,
    "narrative": "narrative response if no valid command"
}}"""

        try:
            response = await self.llm_client.complete(prompt)
            result = json.loads(response)

            if result["command"] and result["confidence"] > 0.7:
                return {
                    "success": True,
                    "parsed_command": result["command"],
                    "llm_assisted": True,
                }
            else:
                # Use narrative to cover uncertainty
                return {
                    "success": False,
                    "message": result.get(
                        "narrative",
                        "I'm not sure what you mean. Try 'help' for commands.",
                    ),
                    "llm_narrative": True,
                }

        except Exception as e:
            print(f"LLM parsing error: {e}")
            return self._basic_parse(user_input)

    def _basic_parse(self, user_input: str) -> Dict[str, Any]:
        """Fallback basic parsing without LLM."""

        # Natural language patterns to game commands
        patterns = {
            # Movement
            "go to": "move",
            "walk to": "move",
            "head to": "move",
            "enter": "move",
            # Interaction
            "talk to": "interact {} talk",
            "speak with": "interact {} talk",
            "chat with": "interact {} talk",
            "ask": "interact {} talk",
            # Actions
            "pick up": "take",
            "grab": "take",
            "get": "take",
            "look around": "look",
            "look at": "look",
            "examine": "look",
            "check inventory": "inventory",
            "check status": "status",
            "rest": "sleep",
            "take a nap": "sleep 2",
            "go to sleep": "sleep",
            # Shopping
            "purchase": "buy",
            "order": "buy",
            "get me": "buy",
            "I want": "buy",
            "I'll have": "buy",
            # Gambling
            "bet": "gamble",
            "wager": "gamble",
            "roll the dice": "gamble 5",
            "try my luck": "gamble 5",
        }

        user_lower = user_input.lower().strip()

        # Check each pattern
        for pattern, command in patterns.items():
            if pattern in user_lower:
                # Extract parameters if needed
                if "{}" in command:
                    # Extract the target (e.g., NPC name)
                    parts = user_lower.split(pattern)
                    if len(parts) > 1:
                        target = parts[1].strip().split()[0] if parts[1].strip() else ""
                        return {
                            "success": True,
                            "parsed_command": command.format(target),
                        }
                else:
                    # Simple replacement
                    remaining = user_lower.replace(pattern, "").strip()
                    if remaining:
                        return {
                            "success": True,
                            "parsed_command": f"{command} {remaining}",
                        }
                    else:
                        return {"success": True, "parsed_command": command}

        # No pattern matched
        return {
            "success": False,
            "message": "I don't understand that. Try 'help' for valid commands.",
        }


# Example of how this SHOULD be integrated into GameState
example_integration = """
# In GameState.process_command():

# First try LLM parsing for natural language
if self.llm_parser and not command.startswith(tuple(KNOWN_COMMANDS)):
    parse_result = await self.llm_parser.parse_natural_command(
        command,
        {
            'gold': self.player.gold,
            'location': self.room_manager.current_room_id,
            'time_display': self.clock.get_display_time(),
            'npcs': [npc.name for npc in self.npc_manager.get_present_npcs()]
        }
    )

    if parse_result.get('success') and parse_result.get('parsed_command'):
        # Use the parsed command
        command = parse_result['parsed_command']
        print(f"[LLM parsed '{original_command}' -> '{command}']")
    elif parse_result.get('llm_narrative'):
        # Return narrative response
        return {
            'success': True,
            'message': parse_result['message'],
            'llm_generated': True
        }
"""

if __name__ == "__main__":
    print("🤖 LLM COMMAND PARSER")
    print("====================")
    print("\nThis is what we SHOULD have built instead of:")
    print("❌ Complex retry systems")
    print("❌ Preprocessors for every edge case")
    print("❌ More validation layers")
    print("\n✅ Natural language -> game command via LLM")
    print("✅ Narrative responses for ambiguous inputs")
    print("✅ Context-aware parsing")

    # Test basic parser
    parser = LLMCommandParser()

    test_inputs = [
        "go to the cellar",
        "talk to the bartender",
        "I want to buy some ale",
        "bet 10 gold",
        "take a nap",
        "where am I?",
    ]

    print("\n🧪 Basic Parser Tests:")
    for inp in test_inputs:
        result = parser._basic_parse(inp)
        if result["success"]:
            print(f"✅ '{inp}' -> '{result['parsed_command']}'")
        else:
            print(f"❌ '{inp}' -> {result['message']}")
