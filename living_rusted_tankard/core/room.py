"""Room management for The Living Rusted Tankard."""
from typing import Dict, Optional, List, Tuple
import random
import string
from pydantic import BaseModel, Field

from core.player import PlayerState
from core.clock import GameClock

from pydantic import model_validator

# Cost to rent a room for one night
ROOM_COST = 10


class Room(BaseModel):
    """Represents a rentable room in the tavern."""
    id: str # Changed 'number' to 'id' for clarity and consistency
    name: Optional[str] = None # Optional descriptive name for the room
    price_per_night: int = ROOM_COST
    is_occupied: bool = False
    occupant_id: Optional[str] = None # Player ID if rented by player
    npcs: List[str] = Field(default_factory=list, description="List of NPC IDs currently in the room")

    # If 'name' is not provided, use 'id' as name by default.
    @model_validator(mode='after')
    def set_name_if_none(cls, values):
        if values.name is None:
            values.name = values.id
        return values
    
    def rent(self, player_id: str) -> bool:
        """Attempt to rent the room to a player.
        
        Args:
            player_id: The ID of the player renting the room
            
        Returns:
            bool: True if room was successfully rented, False otherwise
        """
        if self.is_occupied:
            return False
            
        self.is_occupied = True
        self.occupant_id = player_id
        return True
        
    def add_npc(self, npc_id: str) -> None:
        """Add an NPC to this room.
        
        Args:
            npc_id: The ID of the NPC to add
        """
        if npc_id not in self.npcs:
            self.npcs.append(npc_id)
            
    def remove_npc(self, npc_id: str) -> bool:
        """Remove an NPC from this room.
        
        Args:
            npc_id: The ID of the NPC to remove
            
        Returns:
            bool: True if NPC was removed, False if not found
        """
        if npc_id in self.npcs:
            self.npcs.remove(npc_id)
            return True
        return False
        
    @property
    def occupants(self) -> List[str]:
        """Get a list of all occupant IDs in the room (players and NPCs)."""
        occupants = []
        if self.occupant_id:
            occupants.append(self.occupant_id)
        occupants.extend(self.npcs)
        return occupants
        
    def is_occupant(self, entity_id: str) -> bool:
        """Check if an entity (player or NPC) is in this room.
        
        Args:
            entity_id: The ID of the entity to check
            
        Returns:
            bool: True if the entity is in this room, False otherwise
        """
        return entity_id in self.occupants
    
    def vacate(self) -> None:
        """Mark the room as vacant."""
        self.is_occupied = False
        self.occupant_id = None


class RoomManager(BaseModel):
    """Manages all rooms and room-related operations in the tavern."""
    
    rooms: Dict[str, Room] = Field(default_factory=dict)
    current_room_id: Optional[str] = None # Player's current room
    
    _default_num_rooms: int = Field(10, exclude=True) # Used if initializing fresh

    @model_validator(mode='after')
    def ensure_rooms_initialized(self):
        if not self.rooms: # If rooms dict is empty (e.g., new game)
            self._initialize_rooms(self._default_num_rooms)
        
        # Ensure the tavern main room exists if not loaded
        if "tavern_main" not in self.rooms:
            main_room = Room(id="tavern_main", name="Tavern Common Area", price_per_night=0, is_occupied=False)
            self.rooms["tavern_main"] = main_room
        
        if self.current_room_id is None and "tavern_main" in self.rooms:
            self.current_room_id = "tavern_main"
        return self
    
    def _generate_room_id(self, number: int) -> str:
        """Generate a unique room ID (e.g., 'room_1A')."""
        # Simple generation, can be made more complex if needed
        return f"room_{number}{random.choice(string.ascii_uppercase[:3])}"

    def _initialize_rooms(self, count: int) -> None:
        """Initialize the tavern's guest rooms. Called when no room data is loaded."""
        # self.rooms dictionary would be empty at this point if called from ensure_rooms_initialized
        
        # Main tavern area (already handled in ensure_rooms_initialized, but good to be defensive)
        if 'tavern_main' not in self.rooms:
            self.rooms['tavern_main'] = Room(
                id='tavern_main',
                name='Tavern Common Area',
                price_per_night=0,
                is_occupied=False 
            )
        
        # Add guest rooms
        for i in range(1, count + 1):
            room_id = self._generate_room_id(i)
            # Ensure unique ID, though _generate_room_id with random choice is unlikely to collide for small counts
            while room_id in self.rooms: 
                room_id = self._generate_room_id(i + count) # Offset to reduce collision chance

            self.rooms[room_id] = Room(id=room_id, name=f"Room {room_id}", price_per_night=ROOM_COST)

    @property
    def current_room(self) -> Optional[Room]:
        """Get the current room object where the player is."""
        if self.current_room_id:
            return self.rooms.get(self.current_room_id)
        return None

    def move_to_room(self, room_id: str) -> bool:
        """Move the player to a different room."""
        if room_id in self.rooms:
            self.current_room_id = room_id
            return True
        return False

    def rent_room(self, player: PlayerState) -> Tuple[bool, Optional[str]]:
        """Rent a room to the player.
        
        Args:
            player: The player renting the room
            
        Returns:
            tuple: (success: bool, room_number: Optional[str])
        """
        # Check if player already has a room
        # PlayerState might need a field like `rented_room_id`
        if player.has_room and player.room_id: # Assuming PlayerState has room_id if has_room is true
             # Check if the current room is already rented by this player
            current_rented_room = self.rooms.get(player.room_id)
            if current_rented_room and current_rented_room.occupant_id == player.id: # player.id assumed
                 return False, player.room_id # Already has this room

        room_to_rent: Optional[Room] = None
        for r_id, r_obj in self.rooms.items():
            if r_id != "tavern_main" and not r_obj.is_occupied:
                room_to_rent = r_obj
                break # Found an available room
        
        if not room_to_rent:
            return False, None # No rooms available

        # Check if player has enough gold
        if player.gold < room_to_rent.price_per_night:
            return False, None
            
        # If player already has a different room, vacate it first (optional logic)
        if player.has_room and player.room_id and player.room_id != room_to_rent.id:
            old_room = self.rooms.get(player.room_id)
            if old_room:
                old_room.vacate()

        success = room_to_rent.rent(player.id) # player.id assumed
        
        if success:
            player.has_room = True
            player.room_id = room_to_rent.id # player.room_id assumed
            player.gold -= room_to_rent.price_per_night 
            
            # player.lock_no_sleep_quest() # This method would be on PlayerState
            
            return True, room_to_rent.id
            
        return False, None
    
    def get_room_status(self, room_id: str) -> Optional[dict]:
        """Get the status of a specific room.
        
        Args:
            room_id: The room ID to check
            
        Returns:
            Optional[dict]: Room status or None if room doesn't exist
        """
        room_instance = self.rooms.get(room_id) # Renamed variable
        if not room_instance:
            return None
            
        return {
            "id": room_instance.id,
            "name": room_instance.name,
            "price_per_night": room_instance.price_per_night,
            "is_occupied": room_instance.is_occupied,
            "occupant_id": room_instance.occupant_id,
            "npcs": room_instance.npcs
        }
    
    def get_available_rooms(self) -> List[Room]:
        """Get a list of all available (unoccupied) rooms, excluding 'tavern_main'."""
        return [
            room_obj for room_id, room_obj in self.rooms.items() 
            if not room_obj.is_occupied and room_id != 'tavern_main'
        ]
        
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by its ID.
        
        Args:
            room_id: The ID of the room to retrieve
            
        Returns:
            Optional[Room]: The room if found, None otherwise
        """
        return self.rooms.get(room_id)

    # Duplicated get_room was removed by making the one above the single source.
    # Duplicated get_available_rooms was removed for the same reason.

    def get_available_rooms_list(self) -> List[dict]:
        """Get a list of all available rooms as dictionaries.
        
        Returns:
            List[dict]: List of available rooms as dictionaries
        """
        return [{
            'id': room.id,
            'name': room.name,
            'price_per_night': room.price_per_night,
            'is_occupied': room.is_occupied,
            'occupant_id': room.occupant_id,
            'npcs': room.npcs
        } for room in self.get_available_rooms()] # Uses the updated get_available_rooms
                
    def get_all_rooms(self) -> Dict[str, Room]:
        """Get all rooms in the tavern.
        
        Returns:
            Dict[str, Room]: Dictionary mapping room numbers to Room objects
        """
        return self.rooms
    
    def _room_to_dict(self, room: Room) -> dict:
        """Convert a Room object to a dictionary.
        
        Args:
            room: The room to convert
            
        Returns:
            dict: Room details as a dictionary
        """
        return {
            "id": room.id,
            "name": room.name,
            "price_per_night": room.price_per_night,
            "is_occupied": room.is_occupied,
            "occupant_id": room.occupant_id,
            "npcs": room.npcs
        }
    
    def sleep(self, player: PlayerState, clock: GameClock) -> bool:
        """Handle player sleeping in their rented room.
        
        Args:
            player: The player trying to sleep
            clock: The game clock to advance time
            
        Returns:
            bool: True if sleep was successful, False otherwise
        """
        # PlayerState needs room_id if has_room is True
        if not player.has_room or not player.room_id: 
            return False
            
        room = self.rooms.get(player.room_id) 
        # PlayerState needs id matching occupant_id
        if not room or not room.is_occupied or room.occupant_id != player.id: 
            return False
        
        # Sleep for 6-8 hours
        sleep_hours = 6 + (random.random() * 2) 
        clock.advance_time(sleep_hours) 
        
        # Fully reset tiredness when sleeping in a rented room
        player.tiredness = 0.0 # Explicitly float
        
        return True
