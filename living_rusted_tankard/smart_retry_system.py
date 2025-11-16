class SmartCommandRetry:
    """Intelligent command retry system that learns from failures."""

    def __init__(self, game_state):
        self.game_state = game_state
        self.retry_strategies = {
            "room": self._retry_room_movement,
            "item": self._retry_item_action,
            "gold": self._retry_with_less_gold,
            "npc": self._retry_after_wait,
            "default": self._suggest_alternative,
        }

    def process_with_retry(self, command: str, max_retries: int = 2) -> Dict[str, Any]:
        """Process command with intelligent retry on failure."""

        # First attempt
        result = self.game_state.process_command(command)

        if result["success"] or max_retries == 0:
            return result

        # Analyze failure and determine retry strategy
        error_type = self._classify_error(result["message"])
        retry_strategy = self.retry_strategies.get(
            error_type, self.retry_strategies["default"]
        )

        # Attempt retry with appropriate strategy
        retry_command = retry_strategy(command, result["message"])

        if retry_command and retry_command != command:
            # Add explanation of retry
            result["retry_attempted"] = True
            result["original_command"] = command
            result["retry_command"] = retry_command

            # Try the new command
            retry_result = self.game_state.process_command(retry_command)

            if retry_result["success"]:
                retry_result["message"] = f"[Retry succeeded] {retry_result['message']}"
                retry_result["original_failed"] = command

            return retry_result

        return result

    def _classify_error(self, error_message: str) -> str:
        """Classify error type from message."""

        error_lower = error_message.lower()

        if "room" in error_lower or "move" in error_lower:
            return "room"
        elif "item" in error_lower or "inventory" in error_lower:
            return "item"
        elif "gold" in error_lower or "afford" in error_lower:
            return "gold"
        elif "npc" in error_lower or "no one" in error_lower:
            return "npc"
        else:
            return "default"

    def _retry_room_movement(self, original_cmd: str, error_msg: str) -> Optional[str]:
        """Extract available rooms from error and suggest valid one."""

        # Extract room list from error message
        if "Available rooms:" in error_msg:
            rooms_part = error_msg.split("Available rooms:")[1].strip()
            available_rooms = [r.strip() for r in rooms_part.split(",")]

            if available_rooms:
                # Pick first available room
                return f"move {available_rooms[0]}"

        return None

    def _retry_item_action(self, original_cmd: str, error_msg: str) -> Optional[str]:
        """Suggest checking inventory or buying available item."""

        if original_cmd.startswith("use"):
            return "inventory"  # Check what we have
        elif original_cmd.startswith("buy"):
            return "buy"  # List available items

        return None

    def _retry_with_less_gold(self, original_cmd: str, error_msg: str) -> Optional[str]:
        """Extract gold amount and retry with smaller amount."""

        # Extract current gold from error
        gold_match = re.search(r"have (\d+)", error_msg)
        if gold_match:
            current_gold = int(gold_match.group(1))

            if "gamble" in original_cmd:
                # Gamble with 25% of current gold
                safe_bet = max(1, current_gold // 4)
                return f"gamble {safe_bet}"

        return None

    def _retry_after_wait(self, original_cmd: str, error_msg: str) -> Optional[str]:
        """Wait a bit and check NPCs again."""
        return "npcs"  # Check who's around

    def _suggest_alternative(self, original_cmd: str, error_msg: str) -> Optional[str]:
        """Suggest a helpful alternative command."""

        # Common alternatives
        alternatives = {
            "interact": "npcs",
            "work": "jobs",
            "accept": "bounties",
            "complete": "status",
            "move": "look",
            "buy": "status",
            "use": "inventory",
        }

        first_word = original_cmd.split()[0]
        return alternatives.get(first_word, "help")
