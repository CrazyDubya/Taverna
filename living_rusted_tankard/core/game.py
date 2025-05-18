"""Main game module that ties all components together."""
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime
from pydantic import BaseModel
from .clock import GameClock, GameTime
from .player import PlayerState
from .npc import NPC, NPCManager
from .economy import Economy, TransactionResult
from .items import Item, TAVERN_ITEMS, Inventory


class GameEvent(BaseModel):
    """Represents a game event or notification."""
    timestamp: float
    message: str
    event_type: str = "info"  # info, warning, success, error
    data: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True

class GameState:
    """Main game state manager that holds all game components."""
    
    def __init__(self):
        self.clock = GameClock()
        self.player = PlayerState()
        self.npc_manager = NPCManager()
        self.economy = Economy()
        self.running = False
        self.events: List[GameEvent] = []
        self._last_update_time = 0.0
        self._setup_event_handlers()
        self._initialize_game()
    
    def _initialize_game(self) -> None:
        """Initialize the game with starting state."""
        # Add some starting items to player's inventory
        starting_items = ["bread", "ale"]
        for item_id in starting_items:
            if item_id in TAVERN_ITEMS:
                self.player.inventory.add_item(TAVERN_ITEMS[item_id])
        
        # Log game start
        self._add_event("Welcome to The Rusted Tankard!", "info")
    
    def _add_event(self, message: str, event_type: str = "info", data: Optional[Dict] = None) -> None:
        """Add a new game event."""
        # Get the current time in hours as a float
        current_time = getattr(self.clock, 'current_time', None)
        if hasattr(current_time, 'hours'):
            timestamp = float(current_time.hours)
        else:
            timestamp = float(current_time) if current_time is not None else 0.0
            
        self.events.append(GameEvent(
            timestamp=timestamp,
            message=message,
            event_type=event_type,
            data=data or {}
        ))
        # Keep only the last 100 events
        if len(self.events) > 100:
            self.events = self.events[-100:]
    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers for the game loop."""
        def on_time_advanced(old_time: float, new_time: float, delta: float) -> None:
            # Update NPC presence based on the new time
            self.npc_manager.update_all_npcs(new_time)
            
            # Update player state
            self.player.update_tiredness(delta)
            
            # Update economic events
            event_update = self.economy.update_economic_events(delta)
            if event_update:
                self._add_event(event_update["message"], "info")
            
            # Update day/night cycle and other time-based events
            self._handle_time_based_events(old_time, new_time, delta)
        
        # Register the time update handler
        self.clock.on_time_advanced = on_time_advanced
    
    def _handle_time_based_events(self, old_time: float, new_time: float, delta: float) -> None:
        """Handle events that should occur at specific times."""
        # Example: Check for day/night transitions
        old_hour = int(old_time % 24)
        new_hour = int(new_time % 24)
        
        if old_hour != new_hour:
            # Hour changed
            if new_hour == 6:
                self._add_event("Dawn breaks over the tavern.", "info")
            elif new_hour == 18:
                self._add_event("The sun begins to set outside.", "info")
            
            # Check for rest opportunities
            if new_hour in [22, 23, 0, 1, 2, 3, 4, 5]:
                if not self.player.has_room and not self.player.rest_immune:
                    self._add_event(
                        "The common room is getting uncomfortable. Consider renting a room for the night.",
                        "warning"
                    )
    
    def update(self, delta: float = 1.0) -> None:
        """Update game state.
        
        Args:
            delta: Time in hours since last update.
        """
        # Update the game clock
        self.clock.advance_time(delta)
        current_time = self.clock.current_time
        delta = current_time - self._last_update_time
        self._last_update_time = current_time
        
        # Update game clock
        self.clock.update()
        
        # Update player status effects
        self._update_player_status()
    
    def _update_player_status(self) -> None:
        """Update player's status effects and conditions."""
        # Check for exhaustion
        if self.player.tiredness >= 0.9 and not self.player.rest_immune:
            self._add_event("You're feeling extremely tired. Find a place to rest soon!", "warning")
        
        # Check for hunger/thirst
        if self.player.energy < 0.3:
            self._add_event("You're feeling weak from hunger or thirst.", "warning")
    
    def run(self) -> None:
        """Run the main game loop."""
        self.running = True
        self._last_update_time = self.clock.current_time
        
        try:
            while self.running:
                self.update()
                # In a real implementation, this would have frame limiting
                # and input handling
                import time
                time.sleep(0.1)  # Prevent CPU overuse
                
        except KeyboardInterrupt:
            self.running = False
            self._add_event("Game saved. Come back soon!", "info")
    
    def handle_command(self, command: str, *args) -> Dict[str, Any]:
        """
        Handle a player command.
        
        Args:
            command: The command string (e.g., 'buy', 'sell', 'use')
            *args: Arguments for the command
            
        Returns:
            Dict containing the result of the command
        """
        command = command.lower()
        
        # Simple command routing
        if command == "status":
            return self._handle_status()
        elif command == "inventory":
            return self._handle_inventory()
        elif command == "buy" and args:
            return self._handle_buy(args[0])
        elif command == "use" and args:
            return self._handle_use(args[0])
        elif command == "jobs":
            return self._handle_available_jobs()
        elif command == "work" and args:
            return self._handle_work(args[0])
        elif command == "gamble" and args:
            try:
                amount = int(args[0])
                npc_id = args[1] if len(args) > 1 else None
                return self._handle_gamble(amount, npc_id)
            except ValueError:
                return {"status": "error", "message": "Please specify a valid amount to gamble."}
        else:
            return {"status": "error", "message": f"Unknown command: {command}"}
    
    def _handle_status(self) -> Dict[str, Any]:
        """Handle status command."""
        status = {
            "time": self.clock.get_formatted_time(),
            "gold": self.player.gold,
            "has_room": self.player.has_room,
            "tiredness": f"{self.player.tiredness*100:.0f}%",
            "energy": f"{self.player.energy*100:.0f}%",
            "status_effects": ", ".join(self.player.get_status_effects()),
        }
        
        # Add current event info if any
        if self.economy.current_event:
            status["current_event"] = self.economy.current_event["name"]
            status["event_description"] = self.economy.current_event["description"]
        
        return {"status": "success", "data": status}
    
    def _handle_inventory(self) -> Dict[str, Any]:
        """Handle inventory command."""
        items = [{"name": item.name, "description": item.description} 
                for item in self.player.inventory.list_items()]
        return {
            "status": "success",
            "data": {
                "items": items,
                "count": len(items),
                "gold": self.player.gold
            }
        }
    
    def _handle_buy(self, item_id: str) -> Dict[str, Any]:
        """Handle buy command."""
        item = TAVERN_ITEMS.get(item_id.lower())
        if not item:
            return {"status": "error", "message": f"No such item: {item_id}"}
        
        price = self.economy.get_item_price(item_id)
        if not price:
            return {"status": "error", "message": f"Cannot determine price for {item.name}"}
        
        if not self.player.spend_gold(price):
            return {
                "status": "error",
                "message": f"Not enough gold. You need {price} gold for {item.name}."
            }
        
        # Add to inventory
        self.player.inventory.add_item(item)
        self._add_event(f"Bought {item.name} for {price} gold.", "success")
        
        return {
            "status": "success",
            "message": f"You bought {item.name} for {price} gold.",
            "gold": self.player.gold
        }
    
    def _handle_use(self, item_id: str) -> Dict[str, Any]:
        """Handle use item command."""
        if not self.player.inventory.get_item(item_id):
            return {"status": "error", "message": f"You don't have {item_id} in your inventory."}
        
        # Try to consume the item
        if self.player.consume_item(item_id):
            return {"status": "success", "message": f"Used {item_id}."}
        else:
            return {"status": "error", "message": f"Could not use {item_id}."}
    
    def _handle_available_jobs(self) -> Dict[str, Any]:
        """Handle jobs command."""
        jobs = self.economy.get_available_jobs(self.player.energy)
        return {
            "status": "success",
            "data": [{
                "id": job_id,
                "name": job["name"],
                "description": job["description"],
                "reward": f"{job['base_reward']} gold",
                "tiredness": f"+{job['tiredness_cost']*100:.0f}%"
            } for job_id, job in jobs.items()]
        }
    
    def _handle_work(self, job_id: str) -> Dict[str, Any]:
        """Handle work command."""
        result = self.economy.perform_job(job_id, self.player.energy)
        if not result["success"]:
            return {"status": "error", "message": result["message"]}
        
        # Update player state
        self.player.add_gold(result["reward"])
        self.player.tiredness = min(1.0, self.player.tiredness + result["tiredness"])
        
        # Add any items to inventory
        for item in result.get("items", []):
            self.player.inventory.add_item(item)
        
        # Format response
        response = {
            "status": "success",
            "message": result["message"],
            "reward": result["reward"],
            "tiredness": result["tiredness"]
        }
        
        if "items" in result and result["items"]:
            response["items"] = [item.name for item in result["items"]]
        
        return response
    
    def _handle_gamble(self, amount: int, npc_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle gamble command."""
        npc_skill = 0.0
        if npc_id:
            npc = self.npc_manager.get_npc(npc_id)
            if npc:
                npc_skill = npc.get("gambling_skill", 0.0)
        
        result = self.economy.gamble(self.player.gold, amount, npc_skill)
        
        if not result.success:
            return {"status": "error", "message": result.message}
        
        # Update player's gold
        self.player.gold = result.new_balance
        
        # Add event log
        if result.amount > 0:
            self._add_event(f"You won {result.amount} gold gambling!", "success")
        else:
            self._add_event(f"You lost {abs(result.amount)} gold gambling.", "warning")
        
        return {
            "status": "success" if result.amount >= 0 else "warning",
            "message": result.message,
            "amount": result.amount,
            "new_balance": result.new_balance
        }
    
    def save_game(self, filename: str) -> bool:
        """Save the current game state to a file."""
        # TODO: Implement save game functionality with proper serialization
        try:
            import json
            from datetime import datetime
            
            save_data = {
                "timestamp": datetime.now().isoformat(),
                "game_time": self.clock.current_time,
                "player": {
                    "gold": self.player.gold,
                    "has_room": self.player.has_room,
                    "tiredness": self.player.tiredness,
                    "energy": self.player.energy,
                    "inventory": [item.id for item in self.player.inventory.list_items()],
                    "flags": self.player.flags
                },
                "current_event": self.economy.current_event["name"] if self.economy.current_event else None,
                "event_duration": self.economy.event_duration
            }
            
            with open(filename, 'w') as f:
                json.dump(save_data, f, indent=2)
                
            self._add_event(f"Game saved to {filename}", "success")
            return True
            
        except Exception as e:
            self._add_event(f"Failed to save game: {str(e)}", "error")
            return False
    
    def load_game(self, filename: str) -> bool:
        """Load a game state from a file."""
        # TODO: Implement load game functionality with proper validation
        try:
            import json
            
            with open(filename, 'r') as f:
                save_data = json.load(f)
            
            # Basic validation
            if "player" not in save_data or "game_time" not in save_data:
                raise ValueError("Invalid save file format")
            
            # Restore game state
            self.clock.current_time = save_data["game_time"]
            
            # Restore player state
            player_data = save_data["player"]
            self.player.gold = player_data.get("gold", 40)
            self.player.has_room = player_data.get("has_room", False)
            self.player.tiredness = player_data.get("tiredness", 0.0)
            self.player.energy = player_data.get("energy", 1.0)
            self.player.flags = player_data.get("flags", {})
            
            # Restore inventory
            self.player.inventory = Inventory()
            for item_id in player_data.get("inventory", []):
                if item_id in TAVERN_ITEMS:
                    self.player.inventory.add_item(TAVERN_ITEMS[item_id])
            
            # Restore economic event if any
            if save_data.get("current_event") and save_data["current_event"] in self.economy.economic_events:
                self.economy.current_event = self.economy.economic_events[save_data["current_event"]]
                self.economy.event_duration = save_data.get("event_duration", 0)
            
            self._add_event("Game loaded successfully!", "success")
            return True
            
        except Exception as e:
            self._add_event(f"Failed to load game: {str(e)}", "error")
            return False
