"""Room management for The Living Rusted Tankard."""
from typing import Dict, Optional, List, Tuple, TYPE_CHECKING
import random
import string
from pydantic import BaseModel, Field, validator

if TYPE_CHECKING:
    from core.player import PlayerState # Assuming PlayerState is in core.player

from core.clock import GameClock # Assuming GameClock is in core.clock
from core.config import CONFIG
# using validator instead of model_validator for compatibility with v1

# Constants from configuration
ROOM_COST = CONFIG.ROOM_COST
STORAGE_CHEST_COST_MODIFIER = CONFIG.STORAGE_CHEST_COST_MODIFIER


class Room(BaseModel):
    """Represents a rentable room in the tavern."""
    id: str 
    name: Optional[str] = None 
    description: Optional[str] = "A standard room." 
    price_per_night: int = ROOM_COST
    is_occupied: bool = False
    occupant_id: Optional[str] = None 
    npcs: List[str] = Field(default_factory=list, description="List of NPC IDs currently in the room")
    features: List[Dict[str, str]] = Field(default_factory=list)
    has_storage_chest: bool = False # Added
    storage_chest_cost_modifier: int = STORAGE_CHEST_COST_MODIFIER # Added

    def __init__(self, **data):
        super().__init__(**data)
        # Set name if none was provided
        if self.name is None:
            if self.id.startswith("room_"):
                parts = self.id.split("_")
                if len(parts) > 1:
                    self.name = f"Room {parts[1]}"
                else:
                    self.name = self.id
            else:
                self.name = self.id
        if self.description is None and self.name:
             self.description = f"This is {self.name}."
    
    def rent(self, player_id: str, with_storage_chest: bool = False) -> bool: # Added with_storage_chest
        if self.is_occupied and self.occupant_id != player_id : # Allow re-renting to same player if needed by logic elsewhere
            return False
            
        self.is_occupied = True
        self.occupant_id = player_id
        if with_storage_chest:
            self.has_storage_chest = True
        # If not with_storage_chest, it defaults to False or retains previous if permanent (not current design)
        return True
        
    def add_npc(self, npc_id: str) -> None:
        if npc_id not in self.npcs:
            self.npcs.append(npc_id)
            
    def remove_npc(self, npc_id: str) -> bool:
        if npc_id in self.npcs:
            self.npcs.remove(npc_id)
            return True
        return False
        
    @property
    def occupants(self) -> List[str]: 
        occupants_list = []
        if self.occupant_id:
            occupants_list.append(self.occupant_id)
        occupants_list.extend(self.npcs)
        return occupants_list
        
    def is_occupant(self, entity_id: str) -> bool:
        return entity_id in self.occupants
    
    def vacate(self) -> None:
        self.is_occupied = False
        self.occupant_id = None
        self.has_storage_chest = False # Reset storage chest status on vacate


class RoomManager(BaseModel):
    rooms: Dict[str, Room] = Field(default_factory=dict)
    current_room_id: Optional[str] = None 
    _default_num_rooms: int = 10  # Regular class attribute, not a Field

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize rooms if needed
        if not self.rooms: 
            self._initialize_rooms(self._default_num_rooms)
        
        if "tavern_main" not in self.rooms:
            main_room = Room(
                id="tavern_main", 
                name="Tavern Common Area", 
                description="The bustling heart of The Rusted Tankard, filled with tables, a long bar, and a large fireplace.",
                price_per_night=0, 
                is_occupied=False, 
                features=[{
                    "id": "notice_board", 
                    "name": "Notice Board", 
                    "description": "A weathered board with various parchments pinned to it."
                }]
            )
            self.rooms["tavern_main"] = main_room
        elif "tavern_main" in self.rooms and not any(f["id"] == "notice_board" for f in self.rooms["tavern_main"].features):
            self.rooms["tavern_main"].features.append({
                "id": "notice_board",
                "name": "Notice Board",
                "description": "A weathered board with various parchments pinned to it."
            })
        
        if 'deep_cellar' not in self.rooms:
            self.rooms['deep_cellar'] = Room(
                id='deep_cellar',
                name='Deep Cellar',
                description='A dark, damp extension of the tavern cellar. It smells of rats and something else... unsettling.',
                price_per_night=0, 
                is_occupied=False 
            )

        if self.current_room_id is None and "tavern_main" in self.rooms:
            self.current_room_id = "tavern_main"
    
    def _generate_room_id(self, number: int) -> str:
        return f"room_{number}{random.choice(string.ascii_uppercase[:3])}"

    def _initialize_rooms(self, count: int) -> None:
        if 'tavern_main' not in self.rooms: 
            self.rooms['tavern_main'] = Room(
                id='tavern_main', name='Tavern Common Area', 
                description="The bustling heart of The Rusted Tankard.",
                price_per_night=0, is_occupied=False,
                features=[{"id": "notice_board", "name": "Notice Board", "description": "A weathered board with various parchments pinned to it."}]
            )
        
        if 'deep_cellar' not in self.rooms: 
            self.rooms['deep_cellar'] = Room(
                id='deep_cellar', name='Deep Cellar',
                description='A dark, damp extension of the tavern cellar. It smells of rats and something else... unsettling.',
                price_per_night=0, is_occupied=False
            )

        for i in range(1, count + 1):
            room_id = self._generate_room_id(i)
            while room_id in self.rooms: 
                room_id = self._generate_room_id(i + count) 
            self.rooms[room_id] = Room(id=room_id, name=f"Room {room_id.split('_')[-1]}", description=f"A simple rentable room: {room_id.split('_')[-1]}.", price_per_night=ROOM_COST)

    @property
    def current_room(self) -> Optional[Room]:
        if self.current_room_id:
            return self.rooms.get(self.current_room_id)
        return None

    def move_to_room(self, room_id: str) -> bool:
        if room_id in self.rooms:
            self.current_room_id = room_id
            return True
        return False

    def rent_room(self, player: 'PlayerState', for_how_long: int = 1, with_storage_chest: bool = False) -> Tuple[bool, Optional[str], str]:
        if player.has_room and player.room_id:
            current_rented_room = self.rooms.get(player.room_id)
            if current_rented_room and current_rented_room.occupant_id == player.id:
                 return False, player.room_id, f"You already have room {current_rented_room.name} rented."

        room_to_rent: Optional[Room] = None
        for r_id, r_obj in self.rooms.items():
            if r_id != "tavern_main" and r_id != "deep_cellar" and not r_obj.is_occupied:
                room_to_rent = r_obj
                break 
        
        if not room_to_rent:
            return False, None, "No rooms available to rent."

        current_room_cost = room_to_rent.price_per_night
        if with_storage_chest:
            current_room_cost += room_to_rent.storage_chest_cost_modifier

        if player.gold < current_room_cost:
            return False, None, f"Not enough gold. You need {current_room_cost} gold."
            
        if player.has_room and player.room_id and player.room_id != room_to_rent.id:
            old_room = self.rooms.get(player.room_id)
            if old_room:
                old_room.vacate() # Vacate also resets has_storage_chest

        success_rent = room_to_rent.rent(player.id, with_storage_chest) # Pass with_storage_chest to Room.rent
        
        if success_rent:
            player.has_room = True
            player.room_id = room_to_rent.id 
            player.gold -= current_room_cost
            
            message = f"You rented {room_to_rent.name} for {current_room_cost} gold."
            if with_storage_chest:
                message += " It comes with a sturdy storage chest."
            return True, room_to_rent.id, message
            
        return False, None, "Failed to rent the room for an unknown reason."
    
    def get_room_status(self, room_id: str) -> Optional[dict]:
        room_instance = self.rooms.get(room_id) 
        if not room_instance: return None
        return {
            "id": room_instance.id, "name": room_instance.name, "description": room_instance.description,
            "price_per_night": room_instance.price_per_night, "is_occupied": room_instance.is_occupied,
            "occupant_id": room_instance.occupant_id, "npcs": room_instance.npcs,
            "features": room_instance.features,
            "has_storage_chest": room_instance.has_storage_chest # Added for status
        }
    
    def get_available_rooms(self) -> List[Room]:
        return [room for r_id, room in self.rooms.items() 
                if not room.is_occupied and r_id != 'tavern_main' and r_id != 'deep_cellar'] 
        
    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    def get_available_rooms_list(self) -> List[dict]:
        return [self._room_to_dict(room) for room in self.get_available_rooms()]
                
    def get_all_rooms(self) -> Dict[str, Room]:
        return self.rooms
    
    def _room_to_dict(self, room: Room) -> dict:
        return {
            "id": room.id, "name": room.name, "description": room.description,
            "price_per_night": room.price_per_night, "is_occupied": room.is_occupied,
            "occupant_id": room.occupant_id, "npcs": room.npcs, "features": room.features,
            "has_storage_chest": room.has_storage_chest
        }
    
    def sleep(self, player: 'PlayerState', clock: GameClock) -> bool:
        if not player.has_room or not player.room_id: return False
        room = self.rooms.get(player.room_id) 
        if not room or not room.is_occupied or room.occupant_id != player.id: return False
        sleep_hours = 6 + (random.random() * 2) 
        clock.advance_time(sleep_hours) 
        player.tiredness = 0.0 
        return True
