from typing import Dict, Optional, Callable, Any
from models.player import PlayerState
from .clock import GameClock, GameTime

class GameState:
    """Main game state manager that ties all systems together."""
    def __init__(self):
        self.clock = GameClock()
        self.player = PlayerState()
        self._observers: Dict[str, Callable[[Any], None]] = {}
        self._setup_event_handlers()
    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers for time-based events."""
        # Update player tiredness as time passes
        def on_time_advanced(old_time: float, new_time: float, delta: float) -> None:
            self.player.update_tiredness(delta, self.clock)
            self._notify_observers('time_advanced', {
                'old_time': old_time,
                'new_time': new_time,
                'delta': delta
            })
        
        # Schedule the first time update
        self.clock.on_time_advanced = on_time_advanced
    
    def add_observer(self, event_type: str, callback: Callable[[Any], None]) -> Callable[[], None]:
        """Add an observer for game events. Returns a function to remove the observer."""
        observer_id = str(id(callback))
        self._observers[observer_id] = callback
        
        def remove():
            self._observers.pop(observer_id, None)
            
        return remove
    
    def _notify_observers(self, event_type: str, data: Any = None) -> None:
        """Notify all observers of an event."""
        for callback in list(self._observers.values()):
            try:
                callback({'type': event_type, 'data': data})
            except Exception as e:
                print(f"Error in observer callback: {e}")
    
    def update(self) -> None:
        """Update game state. Should be called every frame."""
        self.clock.update()
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get a serializable snapshot of the game state."""
        return {
            'time': self.clock.time.hours,
            'formatted_time': self.clock.time.format_time(),
            'player': self.player.to_dict()
        }
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """Process a player command and return the result."""
        command = command.lower().strip()
        result = {'success': False, 'message': "I don't understand that command."}
        
        # Basic commands for Phase 0
        if command == 'look':
            result = self._handle_look()
        elif command == 'wait':
            result = self._handle_wait()
        elif command.startswith('wait '):
            try:
                hours = float(command.split()[1])
                result = self._handle_wait(hours)
            except (ValueError, IndexError):
                result = {'success': False, 'message': "Please specify a valid number of hours to wait."}
        elif command in ('quit', 'exit'):
            result = {'success': True, 'message': "Goodbye!", 'should_quit': True}
        
        # Update the game state
        self.update()
        return result
    
    def _handle_look(self) -> Dict[str, Any]:
        """Handle the 'look' command."""
        time_desc = self.clock.time.format_time()
        room_desc = "a small, dimly lit room" if self.player.has_room else "the common area of the tavern"
        
        return {
            'success': True,
            'message': f"It is {time_desc}. You are in {room_desc}.\n"
                     f"Your gold: {self.player.gold} | Tiredness: {int(self.player.tiredness)}%"
        }
    
    def _handle_wait(self, hours: float = 1.0) -> Dict[str, Any]:
        """Handle the 'wait' command."""
        if hours <= 0:
            return {'success': False, 'message': "Time only moves forward in The Rusted Tankard."}
            
        self.clock.advance_time(hours)
        return {
            'success': True,
            'message': f"You wait for {hours:.1f} hours. {self.clock.time.format_time()}",
            'time_advanced': hours
        }
