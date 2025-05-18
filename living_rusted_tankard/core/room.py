"""Room management for The Living Rusted Tankard."""
from typing import Dict, Optional, List, Tuple
import random
import string
from pydantic import BaseModel, Field

from core.player import PlayerState
from core.clock import GameClock

# Cost to rent a room for one night
ROOM_COST = 10


class Room(BaseModel):
    """Represents a rentable room in the tavern."""
    number: str
    price_per_night: int = ROOM_COST
    is_occupied: bool = False
    occupant_id: Optional[str] = None
    npcs: List[str] = Field(default_factory=list, description="List of NPC IDs currently in the room")
    
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


class RoomManager:
    """Manages all rooms and room-related operations in the tavern."""
    
    def __init__(self, num_rooms: int = 10):
        """Initialize the room manager with a number of rooms.
        
        Args:
            num_rooms: Number of rooms to create in the tavern
        """
        self.rooms: Dict[str, Room] = {}
        self._initialize_rooms(num_rooms)
        
        # Ensure the tavern main room exists
        if "tavern_main" not in self.rooms:
            main_room = Room(number="tavern_main", price_per_night=0)
            main_room.is_occupied = False
            main_room.occupant_id = None
            self.rooms["tavern_main"] = main_room
    
    def _generate_room_number(self) -> str:
        """Generate a random room number (e.g., '2B', '3A')."""
        floor = random.randint(1, 3)
        letter = random.choice(string.ascii_uppercase[:5])  # A-E
        return f"{floor}{letter}"
    
    def _initialize_rooms(self, count: int) -> None:
        """Initialize the tavern's rooms.
        
        Args:
            count: Number of rooms to create
        """
        # Clear any existing rooms
        self.rooms.clear()
        
        print(f"Initializing {count} rooms with ROOM_COST={ROOM_COST}")
        
        # Add the main tavern room (always free)
        self.rooms['tavern_main'] = Room(
            number='tavern_main',
            price_per_night=0,
            is_occupied=False
        )
        
        # Add guest rooms with explicit price_per_night
        for i in range(1, count + 1):
            room_number = f"{i}A"
            print(f"Creating room {room_number} with price_per_night={ROOM_COST}")
            room = Room(number=room_number, price_per_night=ROOM_COST)
            print(f"Room {room_number} created with price_per_night={room.price_per_night}")
            self.rooms[room_number] = room
            print(f"Room {room_number} added to rooms dictionary with price={self.rooms[room_number].price_per_night}")
    
    def rent_room(self, player: PlayerState) -> Tuple[bool, Optional[str]]:
        """Rent a room to the player.
        
        Args:
            player: The player renting the room
            
        Returns:
            tuple: (success: bool, room_number: Optional[str])
        """
        # Check if player already has a room
        if player.has_room:
            return False, None
            
        # Check if player has enough gold
        room_cost = ROOM_COST  # Get the current room cost
        if player.gold < room_cost:
            return False, None
            
        # Find an available room
        available_rooms = self.get_available_rooms()
        if not available_rooms:
            return False, None
            
        # Rent the first available room
        room = available_rooms[0]
        success = room.rent(player.player_id)
        
        if success:
            player.has_room = True
            player.room_number = room.number
            player.gold -= room_cost  # Use the room_cost variable
            
            # Lock the no-sleep quest when renting a room
            player.lock_no_sleep_quest()
            
            return True, room.number
            
        return False, None
    
    def get_room_status(self, room_number: str) -> Optional[dict]:
        """Get the status of a specific room.
        
        Args:
            room_number: The room number to check
            
        Returns:
            Optional[dict]: Room status or None if room doesn't exist
        """
        room = self.rooms.get(room_number)
        if not room:
            return None
            
        return {
            "number": room.number,
            "price_per_night": room.price_per_night,
            "is_occupied": room.is_occupied,
            "occupant_id": room.occupant_id
        }
    
    def get_available_rooms(self) -> List[Room]:
        """Get a list of all available (unoccupied) rooms.
        
        Returns:
            List[Room]: List of available rooms
        """
        return [room for room in self.rooms.values() if not room.is_occupied]
        
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by its ID.
        
        Args:
            room_id: The ID of the room to retrieve
            
        Returns:
            Optional[Room]: The room if found, None otherwise
        """
        return self.rooms.get(room_id)
    

    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by its ID.
        
        Args:
            room_id: The ID of the room to retrieve
            
        Returns:
            Optional[Room]: The room if found, None otherwise
        """
        return self.rooms.get(room_id)
    

    
    def get_available_rooms(self) -> List[Room]:
        """Get a list of all available (unoccupied) rooms.
        
        Returns:
            List[Room]: List of available rooms
        """
        return [room for room in self.rooms.values() 
                if not room.is_occupied and room.number != 'tavern_main']
    
    def get_available_rooms_list(self) -> List[dict]:
        """Get a list of all available rooms as dictionaries.
        
        Returns:
            List[dict]: List of available rooms as dictionaries
        """
        return [{
            'number': room.number,
            'price_per_night': room.price_per_night,
            'is_occupied': room.is_occupied,
            'occupant_id': room.occupant_id
        } for room in self.get_available_rooms()]
                
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
            "number": room.number,
            "price_per_night": room.price_per_night,
            "is_occupied": room.is_occupied,
            "occupant_id": room.occupant_id
        }
    
    def sleep(self, player: PlayerState, clock: GameClock) -> bool:
        """Handle player sleeping in their rented room.
        
        Args:
            player: The player trying to sleep
            clock: The game clock to advance time
            
        Returns:
            bool: True if sleep was successful, False otherwise
        """
        if not player.has_room or not player.room_number:
            return False
            
        room = self.rooms.get(player.room_number)
        if not room or not room.is_occupied or room.occupant_id != player.player_id:
            return False
        
        # Sleep for 6-8 hours
        sleep_hours = 6 + (random.random() * 2)  # 6-8 hours
        clock.advance_time(sleep_hours)
        
        # Fully reset tiredness when sleeping in a rented room
        player.tiredness = 0
        
        return True
