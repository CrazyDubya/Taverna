"""Area management system for the tavern world."""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
import json
import os

from .area import TavernArea, Connection, AreaType, AccessLevel, Feature
from .atmosphere import AtmosphereState, AtmosphereManager


@dataclass
class MoveResult:
    """Result of attempting to move between areas."""
    success: bool
    message: str
    new_area_id: Optional[str] = None
    time_cost: float = 0.0  # in game minutes


class AreaManager:
    """Manages all areas and movement between them."""
    
    def __init__(self):
        self.areas: Dict[str, TavernArea] = {}
        self.connections: Dict[str, List[Connection]] = {}
        self.atmosphere_manager = AtmosphereManager()
        self.current_area_id: Optional[str] = "main_hall"
        
        # Track entity locations
        self.entity_locations: Dict[str, str] = {}  # entity_id -> area_id
        
        # Initialize default areas
        self._initialize_default_areas()
    
    def _initialize_default_areas(self) -> None:
        """Create the default tavern layout."""
        # Ground floor
        self._create_main_hall()
        self._create_bar_area()
        self._create_kitchen()
        self._create_private_booth()
        self._create_fireplace_nook()
        
        # Cellar
        self._create_wine_cellar()
        self._create_storage_room()
        self._create_deep_cellar()
        
        # First floor
        self._create_guest_rooms()
        self._create_gambling_den()
        
        # Second floor
        self._create_owners_quarters()
        
        # Create connections
        self._create_default_connections()
        
        # Initialize atmospheres
        self._initialize_atmospheres()
    
    def _create_main_hall(self) -> None:
        """Create the main tavern hall."""
        main_hall = TavernArea(
            id="main_hall",
            name="The Main Hall",
            description="The heart of The Rusted Tankard, filled with sturdy wooden tables and benches. A long bar dominates one wall, while a massive stone fireplace crackles on the opposite side. The air is thick with the smell of ale, roasted meat, and pipe smoke.",
            floor=0,
            area_type=AreaType.COMMON,
            size="large",
            max_occupancy=40,
            features=[
                Feature(
                    id="notice_board",
                    name="Notice Board",
                    description="A weathered wooden board covered in parchments, wanted posters, and job offerings.",
                    interaction_verb="read"
                ),
                Feature(
                    id="bar_counter",
                    name="Bar Counter",
                    description="A well-worn oak counter, its surface marked by countless mugs and years of use.",
                    interaction_verb="approach"
                ),
                Feature(
                    id="main_fireplace",
                    name="Stone Fireplace",
                    description="A massive fireplace that provides warmth to the entire hall. The stones are blackened with age.",
                    interaction_verb="warm yourself by"
                )
            ]
        )
        self.add_area(main_hall)
    
    def _create_bar_area(self) -> None:
        """Create the bar area."""
        bar = TavernArea(
            id="bar_area",
            name="Behind the Bar",
            description="The working area behind the bar counter. Shelves lined with bottles, casks of ale, and a well-used washing basin. Only staff are usually allowed here.",
            floor=0,
            area_type=AreaType.SERVICE,
            access_level=AccessLevel.STAFF,
            size="small",
            max_occupancy=3,
            features=[
                Feature(
                    id="ale_casks",
                    name="Ale Casks",
                    description="Several large casks of the tavern's house ale, tapped and ready to serve.",
                    interaction_verb="tap"
                ),
                Feature(
                    id="bottle_shelf",
                    name="Bottle Shelf",
                    description="Rows of bottles containing various spirits, some covered in dust.",
                    interaction_verb="examine"
                ),
                Feature(
                    id="hidden_shelf",
                    name="Hidden Compartment",
                    description="A cleverly concealed compartment behind a false bottle.",
                    interaction_verb="open",
                    hidden=True
                )
            ]
        )
        self.add_area(bar)
    
    def _create_kitchen(self) -> None:
        """Create the kitchen area."""
        kitchen = TavernArea(
            id="kitchen",
            name="The Kitchen",
            description="A bustling kitchen filled with the sounds of sizzling meat and clanging pots. A large hearth dominates one wall, while preparation tables and storage fill the rest of the space.",
            floor=0,
            area_type=AreaType.SERVICE,
            access_level=AccessLevel.STAFF,
            size="medium",
            max_occupancy=6,
            features=[
                Feature(
                    id="cooking_hearth",
                    name="Cooking Hearth",
                    description="A large hearth with multiple spits and hanging pots.",
                    interaction_verb="cook at"
                ),
                Feature(
                    id="pantry",
                    name="Pantry",
                    description="Shelves stocked with ingredients, preserves, and dry goods.",
                    interaction_verb="search"
                )
            ]
        )
        self.add_area(kitchen)
    
    def _create_private_booth(self) -> None:
        """Create a private booth area."""
        booth = TavernArea(
            id="private_booth",
            name="Private Booth",
            description="A secluded booth tucked into an alcove, offering privacy for discrete conversations. Heavy curtains can be drawn for additional seclusion.",
            floor=0,
            area_type=AreaType.PRIVATE,
            access_level=AccessLevel.PATRON,
            size="tiny",
            max_occupancy=4,
            features=[
                Feature(
                    id="curtains",
                    name="Heavy Curtains",
                    description="Thick velvet curtains that can be drawn for privacy.",
                    interaction_verb="draw"
                ),
                Feature(
                    id="listening_hole",
                    name="Small Hole in the Wall",
                    description="A tiny hole that seems to lead to the adjacent room.",
                    interaction_verb="listen through",
                    hidden=True
                )
            ],
            visibility=0.3  # Dimly lit
        )
        self.add_area(booth)
    
    def _create_fireplace_nook(self) -> None:
        """Create the fireplace nook area."""
        nook = TavernArea(
            id="fireplace_nook",
            name="Fireplace Nook",
            description="A cozy area near the main fireplace with comfortable chairs and small tables. The warmth of the fire makes this a favorite spot for intimate conversations and quiet contemplation.",
            floor=0,
            area_type=AreaType.COMMON,
            size="small",
            max_occupancy=8,
            features=[
                Feature(
                    id="comfortable_chairs",
                    name="Worn Leather Chairs",
                    description="Well-used but comfortable chairs arranged around the fire.",
                    interaction_verb="sit in"
                ),
                Feature(
                    id="pipe_rack",
                    name="Pipe Rack",
                    description="A small rack holding communal pipes and tobacco.",
                    interaction_verb="take from"
                )
            ]
        )
        self.add_area(nook)
    
    def _create_wine_cellar(self) -> None:
        """Create the wine cellar."""
        cellar = TavernArea(
            id="wine_cellar",
            name="Wine Cellar",
            description="A cool, damp cellar lined with wine racks. Dust motes dance in the dim light filtering through the floorboards above. The finest vintages are kept here.",
            floor=-1,
            area_type=AreaType.STORAGE,
            access_level=AccessLevel.STAFF,
            size="medium",
            max_occupancy=6,
            features=[
                Feature(
                    id="wine_racks",
                    name="Wine Racks",
                    description="Floor-to-ceiling racks holding bottles of various vintages.",
                    interaction_verb="browse"
                ),
                Feature(
                    id="vintage_collection",
                    name="Vintage Collection",
                    description="A locked cage containing the most valuable wines.",
                    interaction_verb="examine",
                    requires_item="cellar_key"
                ),
                Feature(
                    id="loose_stone",
                    name="Loose Stone",
                    description="One of the floor stones seems slightly loose.",
                    interaction_verb="pry up",
                    hidden=True
                )
            ],
            visibility=0.4,
            allows_combat=False
        )
        self.add_area(cellar)
    
    def _create_storage_room(self) -> None:
        """Create the storage room."""
        storage = TavernArea(
            id="storage_room",
            name="Storage Room",
            description="A cluttered storage room filled with crates, barrels, and supplies. Cobwebs hang from the rafters, and the musty smell of old wood permeates the air.",
            floor=-1,
            area_type=AreaType.STORAGE,
            access_level=AccessLevel.STAFF,
            size="medium",
            max_occupancy=4,
            features=[
                Feature(
                    id="supply_crates",
                    name="Supply Crates",
                    description="Stacks of crates containing various tavern supplies.",
                    interaction_verb="search through"
                ),
                Feature(
                    id="old_barrel",
                    name="Old Barrel",
                    description="An ancient barrel pushed into the corner, covered in dust.",
                    interaction_verb="investigate",
                    one_time_use=True
                )
            ],
            visibility=0.3
        )
        self.add_area(storage)
    
    def _create_deep_cellar(self) -> None:
        """Create the deep cellar - a secret area."""
        deep = TavernArea(
            id="deep_cellar",
            name="Deep Cellar",
            description="A hidden section of the cellar, older than the rest of the tavern. Strange symbols are carved into the stone walls, and an unnatural chill permeates the air. You feel like you shouldn't be here.",
            floor=-1,
            area_type=AreaType.SECRET,
            access_level=AccessLevel.SECRET,
            size="small",
            max_occupancy=3,
            features=[
                Feature(
                    id="strange_symbols",
                    name="Strange Symbols",
                    description="Ancient symbols carved deep into the stone, their meaning lost to time.",
                    interaction_verb="study"
                ),
                Feature(
                    id="sealed_door",
                    name="Sealed Stone Door",
                    description="A massive stone door sealed with old iron bands. It hasn't been opened in ages.",
                    interaction_verb="examine",
                    requires_item="ancient_key"
                ),
                Feature(
                    id="whispering_corner",
                    name="Dark Corner",
                    description="A particularly dark corner where the air seems to whisper forgotten secrets.",
                    interaction_verb="listen to",
                    hidden=True
                )
            ],
            visibility=0.1,
            is_safe_zone=False
        )
        self.add_area(deep)
    
    def _create_guest_rooms(self) -> None:
        """Create guest room areas."""
        for i in range(1, 5):
            room = TavernArea(
                id=f"guest_room_{i}",
                name=f"Guest Room {i}",
                description=f"A modest but clean room with a comfortable bed, a small desk, and a washbasin. A window overlooks the {'street' if i <= 2 else 'courtyard'}.",
                floor=1,
                area_type=AreaType.PRIVATE,
                access_level=AccessLevel.GUEST,
                size="small",
                max_occupancy=2,
                features=[
                    Feature(
                        id=f"bed_{i}",
                        name="Comfortable Bed",
                        description="A well-maintained bed with clean linens.",
                        interaction_verb="rest in"
                    ),
                    Feature(
                        id=f"desk_{i}",
                        name="Writing Desk",
                        description="A small desk with writing materials.",
                        interaction_verb="sit at"
                    )
                ],
                allows_rest=True
            )
            
            # Room 3 has a secret
            if i == 3:
                room.features.append(Feature(
                    id="loose_floorboard",
                    name="Loose Floorboard",
                    description="A floorboard that creaks differently from the others.",
                    interaction_verb="pry up",
                    hidden=True,
                    one_time_use=True
                ))
            
            self.add_area(room)
    
    def _create_gambling_den(self) -> None:
        """Create the gambling den."""
        den = TavernArea(
            id="gambling_den",
            name="The Lucky Coin",
            description="A smoky room filled with card tables and dice games. The atmosphere is tense with excitement and desperation. Guards watch carefully from the corners.",
            floor=1,
            area_type=AreaType.PRIVATE,
            access_level=AccessLevel.PATRON,
            size="medium",
            max_occupancy=15,
            features=[
                Feature(
                    id="card_tables",
                    name="Card Tables",
                    description="Several tables where various card games are in progress.",
                    interaction_verb="join"
                ),
                Feature(
                    id="dice_corner",
                    name="Dice Corner",
                    description="A corner where patrons gather to play dice games.",
                    interaction_verb="approach"
                ),
                Feature(
                    id="lucky_coin",
                    name="Lucky Coin Display",
                    description="A glass case displaying an ancient coin said to bring luck.",
                    interaction_verb="admire"
                )
            ],
            visibility=0.6,
            allows_combat=False  # Guards prevent fights
        )
        self.add_area(den)
    
    def _create_owners_quarters(self) -> None:
        """Create the owner's quarters."""
        quarters = TavernArea(
            id="owners_quarters",
            name="Owner's Quarters",
            description="Luxurious quarters befitting the tavern's owner. Rich tapestries cover the walls, and expensive furniture fills the space. A large window provides a commanding view of the common room below.",
            floor=2,
            area_type=AreaType.PRIVATE,
            access_level=AccessLevel.OWNER,
            size="large",
            max_occupancy=4,
            features=[
                Feature(
                    id="owners_desk",
                    name="Ornate Desk",
                    description="An expensive desk covered in ledgers and correspondence.",
                    interaction_verb="examine",
                    requires_item="owner_permission"
                ),
                Feature(
                    id="secret_safe",
                    name="Hidden Safe",
                    description="A cleverly concealed safe behind a painting.",
                    interaction_verb="open",
                    hidden=True,
                    requires_item="safe_combination"
                ),
                Feature(
                    id="viewing_window",
                    name="One-Way Window",
                    description="A special window that allows observation of the main hall below without being seen.",
                    interaction_verb="peer through"
                )
            ],
            allows_rest=True
        )
        self.add_area(quarters)
    
    def _create_default_connections(self) -> None:
        """Create connections between areas."""
        # Main hall connections
        self.add_connection("main_hall", "bar_area", "behind bar", "main hall")
        self.add_connection("main_hall", "kitchen", "west", "east")
        self.add_connection("main_hall", "private_booth", "alcove", "main hall")
        self.add_connection("main_hall", "fireplace_nook", "fireside", "main hall")
        self.add_connection("main_hall", "wine_cellar", "down", "up")
        self.add_connection("main_hall", "guest_room_1", "upstairs", "downstairs")
        
        # Cellar connections
        self.add_connection("wine_cellar", "storage_room", "north", "south")
        self.add_connection("storage_room", "deep_cellar", "hidden passage", "back",
                          is_hidden=True, access_level=AccessLevel.SECRET)
        
        # Upper floor connections
        for i in range(1, 4):
            self.add_connection(f"guest_room_{i}", f"guest_room_{i+1}", "next room", "previous room")
        
        self.add_connection("guest_room_2", "gambling_den", "end of hall", "hallway")
        self.add_connection("gambling_den", "owners_quarters", "private stairs", "down",
                          access_level=AccessLevel.OWNER)
    
    def _initialize_atmospheres(self) -> None:
        """Set initial atmospheres for all areas."""
        # Main hall - busy and lively
        main_atmosphere = AtmosphereState(
            noise_level=0.6,
            lighting=0.7,
            crowd_density=0.5,
            temperature=0.6,
            air_quality=0.5
        )
        self.atmosphere_manager.set_atmosphere("main_hall", main_atmosphere)
        
        # Bar area - busy but more controlled
        bar_atmosphere = AtmosphereState(
            noise_level=0.5,
            lighting=0.6,
            crowd_density=0.3,
            temperature=0.7,
            air_quality=0.4
        )
        self.atmosphere_manager.set_atmosphere("bar_area", bar_atmosphere)
        
        # Kitchen - hot and busy
        kitchen_atmosphere = AtmosphereState(
            noise_level=0.5,
            lighting=0.8,
            crowd_density=0.4,
            temperature=0.85,
            air_quality=0.3
        )
        self.atmosphere_manager.set_atmosphere("kitchen", kitchen_atmosphere)
        
        # Private booth - quiet and dim
        booth_atmosphere = AtmosphereState(
            noise_level=0.2,
            lighting=0.3,
            crowd_density=0.1,
            temperature=0.5,
            air_quality=0.6
        )
        self.atmosphere_manager.set_atmosphere("private_booth", booth_atmosphere)
        
        # Fireplace nook - warm and cozy
        nook_atmosphere = AtmosphereState(
            noise_level=0.3,
            lighting=0.6,
            crowd_density=0.3,
            temperature=0.75,
            air_quality=0.5
        )
        self.atmosphere_manager.set_atmosphere("fireplace_nook", nook_atmosphere)
        
        # Wine cellar - cool and quiet
        cellar_atmosphere = AtmosphereState(
            noise_level=0.1,
            lighting=0.4,
            crowd_density=0.0,
            temperature=0.3,
            air_quality=0.7
        )
        self.atmosphere_manager.set_atmosphere("wine_cellar", cellar_atmosphere)
        
        # Deep cellar - cold and eerie
        deep_atmosphere = AtmosphereState(
            noise_level=0.05,
            lighting=0.1,
            crowd_density=0.0,
            temperature=0.2,
            air_quality=0.6
        )
        self.atmosphere_manager.set_atmosphere("deep_cellar", deep_atmosphere)
        
        # Set up atmosphere connections
        self.atmosphere_manager.add_connection("main_hall", "bar_area", 0.5)
        self.atmosphere_manager.add_connection("main_hall", "kitchen", 0.3)
        self.atmosphere_manager.add_connection("main_hall", "fireplace_nook", 0.7)
        self.atmosphere_manager.add_connection("main_hall", "private_booth", 0.2)
        self.atmosphere_manager.add_connection("wine_cellar", "storage_room", 0.4)
    
    def add_area(self, area: TavernArea) -> None:
        """Add an area to the manager."""
        self.areas[area.id] = area
        if area.id not in self.connections:
            self.connections[area.id] = []
    
    def get_area(self, area_id: str) -> Optional[TavernArea]:
        """Get an area by ID."""
        return self.areas.get(area_id)
    
    def get_current_area(self) -> Optional[TavernArea]:
        """Get the current area."""
        if self.current_area_id:
            return self.areas.get(self.current_area_id)
        return None
    
    def add_connection(self, from_area: str, to_area: str, direction: str, 
                      reverse_direction: str, description: Optional[str] = None,
                      requires_key: Optional[str] = None, is_locked: bool = False,
                      is_hidden: bool = False, access_level: AccessLevel = AccessLevel.PUBLIC) -> None:
        """Add a bidirectional connection between areas."""
        if from_area not in self.areas or to_area not in self.areas:
            return
        
        # Forward connection
        forward = Connection(
            from_area=from_area,
            to_area=to_area,
            direction=direction,
            reverse_direction=reverse_direction,
            description=description or f"A passage leads {direction}",
            requires_key=requires_key,
            is_locked=is_locked,
            is_hidden=is_hidden,
            access_level=access_level
        )
        
        # Reverse connection
        reverse = Connection(
            from_area=to_area,
            to_area=from_area,
            direction=reverse_direction,
            reverse_direction=direction,
            description=description or f"A passage leads {reverse_direction}",
            requires_key=requires_key,
            is_locked=is_locked,
            is_hidden=is_hidden,
            access_level=access_level
        )
        
        if from_area not in self.connections:
            self.connections[from_area] = []
        if to_area not in self.connections:
            self.connections[to_area] = []
            
        self.connections[from_area].append(forward)
        self.connections[to_area].append(reverse)
    
    def get_connections(self, area_id: str, show_hidden: bool = False) -> List[Connection]:
        """Get available connections from an area."""
        if area_id not in self.connections:
            return []
        
        connections = self.connections[area_id]
        if not show_hidden:
            connections = [c for c in connections if not c.is_hidden or c.discovered]
        
        return connections
    
    def get_available_exits(self, area_id: Optional[str] = None) -> List[str]:
        """Get list of available exit directions."""
        area_id = area_id or self.current_area_id
        if not area_id:
            return []
        
        connections = self.get_connections(area_id)
        return [c.direction for c in connections if c.can_traverse()]
    
    def move_entity(self, entity_id: str, from_area: str, to_area: str) -> bool:
        """Move an entity between areas."""
        # Remove from old area
        old_area = self.get_area(from_area)
        if old_area:
            if entity_id in old_area.players:
                old_area.remove_player(entity_id)
            elif entity_id in old_area.npcs:
                old_area.remove_npc(entity_id)
        
        # Add to new area
        new_area = self.get_area(to_area)
        if new_area:
            if entity_id.startswith("player_"):
                if not new_area.add_player(entity_id):
                    return False
            else:
                if not new_area.add_npc(entity_id):
                    return False
            
            self.entity_locations[entity_id] = to_area
            return True
        
        return False
    
    def move_to_area(self, player_id: str, target_area_id: str, 
                    has_key: bool = False, access_level: AccessLevel = AccessLevel.PUBLIC) -> MoveResult:
        """Attempt to move a player to a target area."""
        current_area_id = self.entity_locations.get(player_id, self.current_area_id)
        if not current_area_id:
            return MoveResult(False, "You are nowhere!")
        
        # Check if areas exist
        current_area = self.get_area(current_area_id)
        target_area = self.get_area(target_area_id)
        
        if not current_area or not target_area:
            return MoveResult(False, "That area doesn't exist.")
        
        # Find connection
        connection = None
        for conn in self.connections.get(current_area_id, []):
            if conn.to_area == target_area_id:
                connection = conn
                break
        
        if not connection:
            return MoveResult(False, "You can't go there from here.")
        
        # Check if movement is allowed
        if not connection.can_traverse(has_key, access_level):
            if connection.is_hidden and not connection.discovered:
                return MoveResult(False, "You don't see any way to go there.")
            elif connection.is_locked:
                return MoveResult(False, f"The way {connection.direction} is locked.")
            elif access_level.value < connection.access_level.value:
                return MoveResult(False, "You don't have permission to go there.")
        
        # Check if target area has space
        if target_area.is_full:
            return MoveResult(False, f"{target_area.name} is too crowded to enter.")
        
        # Perform the move
        if self.move_entity(player_id, current_area_id, target_area_id):
            # Calculate time cost based on movement
            time_cost = 0.5  # Base 30 seconds
            if abs(current_area.floor - target_area.floor) > 0:
                time_cost += 0.5 * abs(current_area.floor - target_area.floor)
            
            return MoveResult(
                True, 
                f"You go {connection.direction} to {target_area.name}.",
                target_area_id,
                time_cost
            )
        
        return MoveResult(False, "Something went wrong during movement.")
    
    def discover_connection(self, area_id: str, direction: str) -> bool:
        """Discover a hidden connection."""
        connections = self.connections.get(area_id, [])
        for conn in connections:
            if conn.direction == direction and conn.is_hidden and not conn.discovered:
                conn.discovered = True
                # Also discover the reverse connection
                reverse_conns = self.connections.get(conn.to_area, [])
                for rev_conn in reverse_conns:
                    if rev_conn.to_area == area_id:
                        rev_conn.discovered = True
                return True
        return False
    
    def update_area_state(self, game_time: Any) -> None:
        """Update area states based on time and events."""
        # Update atmospheres based on time
        self.atmosphere_manager.update_time_based_changes(
            game_time.hour, 
            game_time.get_season()
        )
        
        # Propagate atmospheric effects
        self.atmosphere_manager.propagate_atmosphere()
        
        # Update crowd density based on time of day
        for area_id, area in self.areas.items():
            atmosphere = self.atmosphere_manager.get_atmosphere(area_id)
            if atmosphere:
                # Main hall gets busier in evening
                if area_id == "main_hall":
                    if 18 <= game_time.hour <= 23:
                        atmosphere.crowd_density = min(0.8, area.current_occupancy / area.max_occupancy)
                    elif 6 <= game_time.hour <= 10:
                        atmosphere.crowd_density = min(0.3, area.current_occupancy / area.max_occupancy)
                    else:
                        atmosphere.crowd_density = min(0.5, area.current_occupancy / area.max_occupancy)
                
                # Gambling den is busiest at night
                elif area_id == "gambling_den":
                    if 20 <= game_time.hour or game_time.hour <= 2:
                        atmosphere.crowd_density = min(0.7, area.current_occupancy / area.max_occupancy)
                    else:
                        atmosphere.crowd_density = min(0.2, area.current_occupancy / area.max_occupancy)
                
                atmosphere.calculate_modifiers()
    
    def get_area_info(self, area_id: str) -> Dict[str, Any]:
        """Get comprehensive information about an area."""
        area = self.get_area(area_id)
        if not area:
            return {}
        
        atmosphere = self.atmosphere_manager.get_atmosphere(area_id)
        connections = self.get_connections(area_id)
        
        return {
            "area": area.to_dict(),
            "atmosphere": {
                "description": atmosphere.describe_atmosphere() if atmosphere else "",
                "noise_level": atmosphere.get_noise_level().name if atmosphere else "UNKNOWN",
                "light_level": atmosphere.get_light_level().name if atmosphere else "UNKNOWN",
                "crowd_density": atmosphere.get_crowd_density().name if atmosphere else "UNKNOWN",
                "affects_conversation": atmosphere.affects_conversation() if atmosphere else False,
                "affects_stealth": atmosphere.affects_stealth() if atmosphere else False
            } if atmosphere else {},
            "exits": [
                {
                    "direction": c.direction,
                    "description": c.get_description(),
                    "accessible": c.can_traverse()
                } for c in connections
            ]
        }
    
    def save_state(self) -> Dict[str, Any]:
        """Save the current state of all areas."""
        return {
            "areas": {area_id: area.to_dict() for area_id, area in self.areas.items()},
            "current_area_id": self.current_area_id,
            "entity_locations": self.entity_locations.copy(),
            "connections": {
                area_id: [
                    {
                        "to_area": c.to_area,
                        "direction": c.direction,
                        "reverse_direction": c.reverse_direction,
                        "description": c.description,
                        "requires_key": c.requires_key,
                        "is_locked": c.is_locked,
                        "is_hidden": c.is_hidden,
                        "discovered": c.discovered,
                        "access_level": c.access_level.value
                    } for c in conns
                ] for area_id, conns in self.connections.items()
            }
        }
    
    def load_state(self, state: Dict[str, Any]) -> None:
        """Load a saved state."""
        # Clear current state
        self.areas.clear()
        self.connections.clear()
        self.entity_locations.clear()
        
        # Load areas
        for area_id, area_data in state.get("areas", {}).items():
            area = TavernArea.from_dict(area_data)
            self.add_area(area)
        
        # Load other state
        self.current_area_id = state.get("current_area_id")
        self.entity_locations = state.get("entity_locations", {}).copy()
        
        # Load connections
        for area_id, conns_data in state.get("connections", {}).items():
            if area_id not in self.connections:
                self.connections[area_id] = []
            
            for conn_data in conns_data:
                connection = Connection(
                    from_area=area_id,
                    to_area=conn_data["to_area"],
                    direction=conn_data["direction"],
                    reverse_direction=conn_data["reverse_direction"],
                    description=conn_data.get("description", ""),
                    requires_key=conn_data.get("requires_key"),
                    is_locked=conn_data.get("is_locked", False),
                    is_hidden=conn_data.get("is_hidden", False),
                    discovered=conn_data.get("discovered", False),
                    access_level=AccessLevel(conn_data.get("access_level", 0))
                )
                self.connections[area_id].append(connection)