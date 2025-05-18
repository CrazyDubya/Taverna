from typing import Dict, Optional, Callable, Any, List, TYPE_CHECKING
from core.player import PlayerState
from .clock import GameClock, GameTime
from .room import RoomManager
from .npc import NPCManager, NPC
from games.gambling_manager import GamblingManager
from .events import (
    NPCSpawnEvent,
    NPCDepartEvent,
    NPCInteractionEvent,
    NPCRelationshipChangeEvent
)
from .event_formatter import EventFormatter

if TYPE_CHECKING:
    from .snapshot import SnapshotManager

class GameState:
    """Main game state manager that ties all systems together."""
    def __init__(self, data_dir: str = "data"):
        """Initialize the game state.
        
        Args:
            data_dir: Directory containing game data files
        """
        # Initialize core components
        self.clock = GameClock()
        self.player = PlayerState()
        self.room_manager = RoomManager()  # Initialize room manager
        self.npc_manager = NPCManager(data_dir, self)  # Initialize NPC manager
        self.gambling_manager = GamblingManager()
        
        # Initialize event handling system
        self._observers: Dict[str, Callable[[Any], None]] = {}
        self._setup_event_handlers()
        
        # Track which NPCs are currently present
        self._present_npcs: Dict[str, NPC] = {}
        
        # Setup NPC event handlers
        self._setup_npc_event_handlers()
        
        # Initialize snapshot manager (will be set up on first access via property)
        self._snapshot_manager = None
        
        # Initialize event formatter
        self.event_formatter = EventFormatter()
    
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
        """Notify all observers of an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type in self._observers:
            self._observers[event_type](data)
    
    def dispatch(self, event):
        """Dispatch an event to the event bus if available.
        
        Args:
            event: The event to dispatch
        """
        if hasattr(self.clock, 'event_bus') and hasattr(self.clock.event_bus, 'publish'):
            self.clock.event_bus.publish(event)
        elif hasattr(self, '_notify_observers'):
            # Fall back to notifying observers if event bus is not available
            self._notify_observers(event.__class__.__name__.lower(), event)
                
        # Also forward to the event bus if it's an NPC event
        if hasattr(self, 'clock') and hasattr(self.clock, 'event_bus'):
            self.clock.event_bus.dispatch(event)
    
    def update(self) -> None:
        """Update game state. Should be called every frame."""
        # Update game clock
        self.clock.update()
        
        # Update NPC states based on current time
        current_time = self.clock.get_current_time()
        self.npc_manager.update_all_npcs(current_time.total_hours)
        
        # Update present NPCs list
        self._update_present_npcs()
    
    def _update_present_npcs(self) -> None:
        """Update the list of currently present NPCs."""
        present_npcs = {}
        for npc in self.npc_manager.get_present_npcs():
            present_npcs[npc.id] = npc
            # If this NPC is newly present, ensure they're in the current room
            if npc.id not in self._present_npcs:
                self._add_npc_to_room(npc)
        
        # Handle NPCs that have left
        for npc_id in set(self._present_npcs) - set(present_npcs):
            self._remove_npc_from_room(npc_id)
            
        self._present_npcs = present_npcs
    
    def _add_npc_to_room(self, npc: NPC) -> None:
        """Add an NPC to their current room."""
        # By default, NPCs are added to the tavern main room
        room = self.room_manager.get_room("tavern_main")
        if room:
            if not room.is_occupied:
                # If room is unoccupied, set as main occupant
                room.occupant_id = npc.id
                room.is_occupied = True
            elif npc.id not in room.npcs:
                # Otherwise add to NPCs list
                room.npcs.append(npc.id)
    
    def _remove_npc_from_room(self, npc_id: str) -> None:
        """Remove an NPC from their current room."""
        for room in self.room_manager.get_all_rooms().values():
            if room.is_occupant(npc_id):
                if npc_id == room.occupant_id:
                    room.occupant_id = None
                    room.is_occupied = False
                elif npc_id in room.npcs:
                    room.npcs.remove(npc_id)
                break
    
    @property
    def snapshot_manager(self):
        """Lazy-load the snapshot manager to avoid circular imports."""
        if self._snapshot_manager is None:
            from .snapshot import SnapshotManager  # Import here to avoid circular import
            self._snapshot_manager = SnapshotManager(self)
        return self._snapshot_manager
    
    def _setup_npc_event_handlers(self):
        """Set up event handlers for NPC-related events."""
        def handle_npc_spawn(event: NPCSpawnEvent):
            npc = self.npc_manager.get_npc(event.npc_id)
            if npc:
                self._present_npcs[npc.id] = npc
                self._add_npc_to_room(npc)
                # Add to recent events
                self.event_formatter.add_event(
                    'npc_spawn',
                    npc_name=npc.name,
                    npc_id=npc.id,
                    location=event.data.get('location', 'tavern')
                )
                # Also notify observers
                self._notify_observers('npc_spawn', {
                    'npc_id': npc.id,
                    'room_id': npc.current_room,
                    'npc_name': npc.name
                })
        
        def handle_npc_depart(event: NPCDepartEvent):
            npc = self._present_npcs.pop(event.npc_id, None)
            if npc:
                reason = event.data.get('reason', 'unknown')
                self._remove_npc_from_room(npc.id)
                # Add to recent events
                self.event_formatter.add_event(
                    'npc_depart',
                    npc_name=npc.name,
                    npc_id=npc.id,
                    reason=reason
                )
                # Also notify observers
                self._notify_observers('npc_depart', {
                    'npc_id': npc.id,
                    'room_id': npc.current_room,
                    'npc_name': npc.name,
                    'reason': reason
                })
        
        def handle_npc_interaction(event: NPCInteractionEvent):
            # Forward interaction events to observers
            self._notify_observers('npc_interaction', {
                'npc_id': event.npc_id,
                'player_id': event.player_id,
                'interaction_type': event.interaction_type,
                'data': event.data
            })
        
        def handle_relationship_change(event: NPCRelationshipChangeEvent):
            # Forward relationship change events to observers
            self._notify_observers('npc_relationship_change', {
                'npc_id': event.npc_id,
                'player_id': event.player_id,
                'change': event.change,
                'new_value': event.new_value
            })
        
        # Subscribe all handlers to the event bus if available
        if hasattr(self.clock, 'event_bus') and hasattr(self.clock.event_bus, 'subscribe'):
            self.clock.event_bus.subscribe('npc_spawn', handle_npc_spawn)
            self.clock.event_bus.subscribe('npc_depart', handle_npc_depart)
            self.clock.event_bus.subscribe('npc_interaction', handle_npc_interaction)
            self.clock.event_bus.subscribe('npc_relationship_change', handle_relationship_change)
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of the current game state."""
        # Get basic NPC info for the current room
        current_room = self.room_manager.current_room
        room_occupants = []
        
        if current_room:
            for occupant_id, occupant_type in current_room.occupants.items():
                if occupant_type == 'player' and occupant_id == self.player.id:
                    # Player
                    room_occupants.append({
                        'id': occupant_id,
                        'type': 'player',
                        'name': self.player.name,
                        'is_player': True
                    })
                elif occupant_type == 'npc':
                    # NPC
                    npc = self.npc_manager.get_npc(occupant_id)
                    if npc:
                        room_occupants.append({
                            'id': npc.id,
                            'type': 'npc',
                            'name': npc.name,
                            'description': npc.description,
                            'is_player': False,
                            'disposition': npc.disposition.name.lower(),
                            'relationship': npc.relationships.get(self.player.id, 0)
                        })
        
        return {
            'time': self.clock.get_current_time().to_dict(),
            'player': self.player.to_dict(),
            'current_room': current_room.id if current_room else None,
            'room_occupants': room_occupants,
            'present_npcs': [
                {
                    'id': npc.id,
                    'name': npc.name,
                    'description': npc.description,
                    'type': npc.npc_type.name.lower(),
                    'disposition': npc.disposition.name.lower(),
                    'relationship': npc.relationships.get(self.player.id, 0)
                }
                for npc in self.npc_manager.get_present_npcs()
            ]
        }
    
    def interact_with_npc(self, npc_id: str, interaction_type: str = "talk", **kwargs) -> Dict[str, Any]:
        """Interact with an NPC.
        
        Args:
            npc_id: ID of the NPC to interact with
            interaction_type: Type of interaction (talk, trade, etc.)
            **kwargs: Additional interaction data
            
        Returns:
            Dict with interaction results
        """
        return self.npc_manager.interact_with_npc(
            npc_id, self.player, interaction_type, **kwargs)
    
    def get_interactive_npcs(self) -> List[Dict[str, Any]]:
        """Get a list of interactive NPCs in the current room.
        
        Returns:
            List of NPCs with their available interactions
        """
        if not self.room_manager.current_room:
            return []
            
        # Only return NPCs that are in the current room
        current_room_npcs = [
            occupant_id for occupant_id, occupant_type 
            in self.room_manager.current_room.occupants.items()
            if occupant_type == 'npc' and self.npc_manager.get_npc(occupant_id)
        ]
        
        # Get interactive info for NPCs in the current room
        return [
            npc for npc in self.npc_manager.get_interactive_npcs(self.player)
            if npc['id'] in current_room_npcs
        ]
        
    def get_available_games(self) -> List[Dict[str, Any]]:
        """Get a list of available gambling games.
        
        Returns:
            List of game descriptions with rules and bet limits
        """
        return self.gambling_manager.get_available_games()
        
    def play_gambling_game(self, game_type: str, bet: int, **kwargs) -> Dict[str, Any]:
        """Play a gambling game.
        
        Args:
            game_type: Type of game to play
            bet: Amount of gold to bet
            **kwargs: Game-specific arguments
            
        Returns:
            Dict with game results and updated player state
        """
        # Check if player is in the tavern (where gambling is allowed)
        if not self.room_manager.current_room or 'tavern' not in self.room_manager.current_room.id.lower():
            return {
                'success': False,
                'message': "You can only gamble in the tavern!"
            }
            
        # Play the game and get results
        result = self.gambling_manager.play_game(self.player, game_type, bet, **kwargs)
        
        # Notify observers of the gambling result
        self._notify_observers('gambling_result', {
            'game_type': game_type,
            'bet': bet,
            'result': result,
            'player_id': self.player.id,
            'new_balance': self.player.gold
        })
        
        return result
        
    def get_gambling_stats(self) -> Dict[str, Any]:
        """Get gambling statistics for the current player.
        
        Returns:
            Dict with gambling statistics
        """
        return self.gambling_manager.get_player_stats(self.player.id)
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """Process a player command and return the result.
        
        Returns:
            Dict containing:
            - success: Whether the command was successful
            - message: The main response message
            - recent_events: List of formatted event strings that occurred during this command
            - time_advanced: Optional float of hours advanced (for time-based commands)
        """
        command = command.lower().strip()
        result = {
            'success': False, 
            'message': "I don't understand that command.",
            'recent_events': []
        }
        
        # Clear previous events at the start of each command
        self.event_formatter.clear_events()
        
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
        elif command == 'sleep':
            result = self._handle_sleep()
        elif command.startswith('sleep ') and command[6:].strip().isdigit():
            try:
                hours = float(command.split()[1])
                result = self._handle_sleep(hours)
            except (ValueError, IndexError):
                result = {'success': False, 'message': "Please specify a valid number of hours to sleep."}
        elif command in ('quit', 'exit'):
            result = {'success': True, 'message': "Goodbye!", 'should_quit': True}
        elif command == 'ask about sleep':
            result = {'success': True, 'message': self.player.ask_about_sleep()}
        elif command in ('rent room', 'rent a room'):
            if self.room_manager.rent_room(self.player):
                result = {'success': True, 'message': "You rent a room for the night."}
            else:
                result = {'success': False, 'message': "You don't have enough gold to rent a room."}
        elif command == 'games':
            games = self.get_available_games()
            if games:
                game_list = '\n'.join([
                    f"{i+1}. {game['name']}: {game['description']} (Bet: {game['min_bet']}-{game['max_bet']} gold, Payout: {game['payout']})"
                    for i, game in enumerate(games)
                ])
                result = {'success': True, 'message': f"Available games:\n{game_list}"}
            else:
                result = {'success': False, 'message': "No games available right now."}
        elif command.startswith(('play dice', 'play coin', 'play high')):
            # Parse game type and bet
            parts = command.split()
            game_type = parts[1]
            
            try:
                bet = int(parts[2]) if len(parts) > 2 else 0
                if bet <= 0:
                    raise ValueError("Bet must be a positive number!")
                
                # Handle game-specific arguments
                kwargs = {}
                if game_type == 'dice':
                    if len(parts) > 3:
                        guess = parts[3].lower()
                        if guess in ('low', '1'):
                            kwargs['guess'] = 1
                        elif guess in ('high', '2'):
                            kwargs['guess'] = 2
                        else:
                            raise ValueError("For dice, specify 'low' or 'high' after the bet.")
                    else:
                        raise ValueError("For dice, specify 'low' or 'high' after the bet.")
                elif game_type == 'coin':
                    if len(parts) > 3:
                        guess = parts[3].lower()
                        if guess in ('heads', 'tails'):
                            kwargs['guess'] = guess
                        else:
                            raise ValueError("For coin flip, specify 'heads' or 'tails' after the bet.")
                    else:
                        raise ValueError("For coin flip, specify 'heads' or 'tails' after the bet.")
                
                # Map command to game type
                game_type_map = {
                    'dice': 'dice',
                    'coin': 'coin_flip',
                    'high': 'high_card'
                }
                
                result = self.play_gambling_game(game_type_map[game_type], bet, **kwargs)
                
            except (ValueError, IndexError) as e:
                result = {'success': False, 'message': f"Invalid command. {e}"}
        elif command == 'gambling stats':
            stats = self.get_gambling_stats()
            if stats['total_games_played'] > 0:
                stats_msg = [
                    f"Games Played: {stats['total_games_played']}",
                    f"Total Won: {stats['total_won']} gold",
                    f"Total Lost: {stats['total_lost']} gold",
                    f"Net Profit: {stats['net_profit']} gold"
                ]
                
                for game_type, game_stats in stats['games'].items():
                    stats_msg.extend([
                        f"\n{game_type.title()}:",
                        f"  Games: {game_stats['games_played']}",
                        f"  Biggest Win: {game_stats['biggest_win']} gold",
                        f"  Biggest Loss: {game_stats['biggest_loss']} gold"
                    ])
                
                result = {'success': True, 'message': '\n'.join(stats_msg)}
            else:
                result = {'success': False, 'message': "You haven't played any gambling games yet!"}
        
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
        
    def _handle_sleep(self, hours: float = 8.0) -> Dict[str, Any]:
        """Handle the 'sleep' command."""
        if hours <= 0:
            return {'success': False, 'message': "You can't sleep for negative time!"}
            
        if not self.player.has_room:
            self.event_formatter.add_event('sleep_failure')
            return {'success': False, 'message': "You need to rent a room before you can sleep."}
            
        # Cap sleep at 24 hours
        sleep_hours = min(hours, 24.0)
        
        # Use the room manager to handle sleeping
        success = self.room_manager.sleep(self.player, self.clock)
        
        if success:
            self.event_formatter.add_event(
                'sleep_success',
                hours=sleep_hours,
                room_id=self.player.room_id
            )
            return {
                'success': True,
                'message': f"You sleep for {sleep_hours:.1f} hours. You feel refreshed! {self.clock.time.format_time()}",
                'time_advanced': sleep_hours
            }
        else:
            return {'success': False, 'message': "You can't sleep right now."}
            
    def _handle_rent(self, room_id: str) -> Dict[str, Any]:
        """Handle the 'rent' command."""
        if not room_id.isdigit():
            return {'success': False, 'message': 'Please specify a valid room number.'}
            
        room = self.room_manager.get_room(room_id)
        if not room:
            return {'success': False, 'message': f'Room {room_id} does not exist.'}
            
        if room.is_occupied and room.occupant_id != self.player.id:
            return {'success': False, 'message': f'Room {room_id} is already occupied.'}
            
        if self.player.gold < room.price_per_night:
            short_amount = room.price_per_night - self.player.gold
            self.event_formatter.add_event(
                'rent_failure',
                amount=room.price_per_night,
                short_amount=short_amount,
                room_id=room_id
            )
            return {
                'success': False, 
                'message': f'You need {room.price_per_night} gold to rent this room.'
            }
            
        # If player already has a room, vacate it first
        if self.player.has_room:
            old_room = self.room_manager.get_room(self.player.room_id)
            if old_room:
                old_room.vacate()
        
        # Rent the new room
        success = room.rent(self.player)
        if success:
            self.player.gold -= room.price_per_night
            self.player.has_room = True
            self.player.room_id = room_id
            
            # Add rent success event
            self.event_formatter.add_event(
                'rent_success',
                amount=room.price_per_night,
                room_id=room_id
            )
            
            # Add recent events to the result
            result = {
                'success': True,
                'message': f'You have rented room {room_id} for {room.price_per_night} gold.'
            }
        return {'success': False, 'message': 'Failed to rent the room.'}
    
    def get_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of the current game state for the parser.
        
        Returns:
            Dict containing the minimal structured data needed by the parser.
        """
        return self.snapshot_manager.create_snapshot()
