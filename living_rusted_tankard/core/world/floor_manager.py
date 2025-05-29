"""Floor-based management for the tavern layout."""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from .area import TavernArea, AreaType
from .atmosphere import AtmosphereState


class FloorType(Enum):
    """Types of floors in the tavern."""
    CELLAR = -1
    GROUND = 0
    FIRST = 1
    SECOND = 2
    ATTIC = 3


@dataclass
class FloorInfo:
    """Information about a floor."""
    floor_number: int
    name: str
    description: str
    base_access_level: int = 0
    vertical_sound_transmission: float = 0.3  # How much sound travels between floors
    areas: Set[str] = None
    
    def __post_init__(self):
        if self.areas is None:
            self.areas = set()


class FloorManager:
    """Manages floor-based properties and movement."""
    
    def __init__(self, area_manager):
        self.area_manager = area_manager
        self.floors: Dict[int, FloorInfo] = {}
        self._initialize_floors()
    
    def _initialize_floors(self) -> None:
        """Set up floor information."""
        # Cellar
        self.floors[-1] = FloorInfo(
            floor_number=-1,
            name="The Cellars",
            description="The damp, cool cellars beneath the tavern. Stone walls echo with dripping water and the occasional scurrying of rats.",
            base_access_level=1,  # Need to be patron
            vertical_sound_transmission=0.1  # Very little sound travels up
        )
        
        # Ground floor
        self.floors[0] = FloorInfo(
            floor_number=0,
            name="Ground Floor",
            description="The main level of the tavern, bustling with activity. The heart of The Rusted Tankard.",
            base_access_level=0,  # Public access
            vertical_sound_transmission=0.4
        )
        
        # First floor
        self.floors[1] = FloorInfo(
            floor_number=1,
            name="Guest Quarters",
            description="The first floor houses guest rooms and entertainment. Wooden floors creak under foot.",
            base_access_level=1,  # Need to be patron
            vertical_sound_transmission=0.5  # Wood transmits sound well
        )
        
        # Second floor
        self.floors[2] = FloorInfo(
            floor_number=2,
            name="Private Quarters",
            description="The uppermost floor, reserved for the owner and special guests. Luxuriously appointed.",
            base_access_level=3,  # Staff or higher
            vertical_sound_transmission=0.3
        )
        
        # Populate areas on each floor
        self._populate_floor_areas()
    
    def _populate_floor_areas(self) -> None:
        """Assign areas to their respective floors."""
        for area_id, area in self.area_manager.areas.items():
            floor = area.floor
            if floor in self.floors:
                self.floors[floor].areas.add(area_id)
    
    def get_floor_info(self, floor_number: int) -> Optional[FloorInfo]:
        """Get information about a specific floor."""
        return self.floors.get(floor_number)
    
    def get_areas_on_floor(self, floor_number: int) -> List[TavernArea]:
        """Get all areas on a specific floor."""
        floor_info = self.get_floor_info(floor_number)
        if not floor_info:
            return []
        
        areas = []
        for area_id in floor_info.areas:
            area = self.area_manager.get_area(area_id)
            if area:
                areas.append(area)
        
        return areas
    
    def get_accessible_floors(self, access_level: int) -> List[int]:
        """Get list of floors accessible at given access level."""
        accessible = []
        for floor_num, floor_info in self.floors.items():
            if access_level >= floor_info.base_access_level:
                accessible.append(floor_num)
        return sorted(accessible)
    
    def calculate_vertical_sound(self, source_floor: int, target_floor: int, 
                               source_noise: float) -> float:
        """Calculate how much sound travels between floors."""
        if source_floor == target_floor:
            return source_noise
        
        floor_distance = abs(source_floor - target_floor)
        
        # Get transmission factor for the intermediate floor
        transmission = 1.0
        for floor in range(min(source_floor, target_floor), 
                         max(source_floor, target_floor)):
            floor_info = self.get_floor_info(floor)
            if floor_info:
                transmission *= floor_info.vertical_sound_transmission
        
        # Additional reduction for distance
        distance_factor = 0.8 ** floor_distance
        
        return source_noise * transmission * distance_factor
    
    def get_floor_activity_level(self, floor_number: int) -> Tuple[float, str]:
        """Get the activity level of a floor based on occupancy."""
        floor_info = self.get_floor_info(floor_number)
        if not floor_info:
            return 0.0, "unknown"
        
        total_occupancy = 0
        total_capacity = 0
        
        for area_id in floor_info.areas:
            area = self.area_manager.get_area(area_id)
            if area:
                total_occupancy += area.current_occupancy
                total_capacity += area.max_occupancy
        
        if total_capacity == 0:
            return 0.0, "empty"
        
        activity_ratio = total_occupancy / total_capacity
        
        if activity_ratio == 0:
            description = "empty"
        elif activity_ratio < 0.2:
            description = "quiet"
        elif activity_ratio < 0.5:
            description = "moderately active"
        elif activity_ratio < 0.8:
            description = "busy"
        else:
            description = "packed"
        
        return activity_ratio, description
    
    def propagate_floor_effects(self) -> None:
        """Propagate effects between floors (sound, smells, etc.)."""
        # Propagate sound between floors
        for source_floor in self.floors:
            source_areas = self.get_areas_on_floor(source_floor)
            
            # Calculate average noise on this floor
            total_noise = 0.0
            count = 0
            
            for area in source_areas:
                atmosphere = self.area_manager.atmosphere_manager.get_atmosphere(area.id)
                if atmosphere:
                    total_noise += atmosphere.noise_level
                    count += 1
            
            if count == 0:
                continue
                
            avg_noise = total_noise / count
            
            # Propagate to other floors
            for target_floor in self.floors:
                if target_floor == source_floor:
                    continue
                
                transmitted_noise = self.calculate_vertical_sound(
                    source_floor, target_floor, avg_noise
                )
                
                # Apply to areas on target floor
                if transmitted_noise > 0.05:  # Threshold
                    target_areas = self.get_areas_on_floor(target_floor)
                    for area in target_areas:
                        atmosphere = self.area_manager.atmosphere_manager.get_atmosphere(area.id)
                        if atmosphere:
                            # Add as background noise
                            current = atmosphere.noise_level
                            atmosphere.noise_level = min(1.0, 
                                current + transmitted_noise * 0.3)
    
    def get_vertical_connections(self, area_id: str) -> List[str]:
        """Get connections that lead to different floors."""
        area = self.area_manager.get_area(area_id)
        if not area:
            return []
        
        vertical = []
        connections = self.area_manager.get_connections(area_id)
        
        for conn in connections:
            target_area = self.area_manager.get_area(conn.to_area)
            if target_area and target_area.floor != area.floor:
                vertical.append(conn.direction)
        
        return vertical
    
    def describe_floor_sounds(self, floor_number: int) -> str:
        """Describe what can be heard from other floors."""
        descriptions = []
        
        for other_floor in self.floors:
            if other_floor == floor_number:
                continue
            
            activity, desc = self.get_floor_activity_level(other_floor)
            if activity > 0.1:
                if other_floor > floor_number:
                    direction = "above"
                else:
                    direction = "below"
                
                if activity > 0.6:
                    descriptions.append(f"Loud noises drift from {direction}")
                elif activity > 0.3:
                    descriptions.append(f"Muffled sounds come from {direction}")
                elif activity > 0.1:
                    descriptions.append(f"Faint noises can be heard from {direction}")
        
        if descriptions:
            return ". ".join(descriptions) + "."
        else:
            return "The other floors are quiet."
    
    def get_floor_map(self) -> Dict[int, Dict[str, Any]]:
        """Get a map of all floors and their areas."""
        floor_map = {}
        
        for floor_num, floor_info in self.floors.items():
            areas_info = []
            for area_id in floor_info.areas:
                area = self.area_manager.get_area(area_id)
                if area:
                    areas_info.append({
                        "id": area.id,
                        "name": area.name,
                        "type": area.area_type.value,
                        "occupancy": f"{area.current_occupancy}/{area.max_occupancy}"
                    })
            
            activity, activity_desc = self.get_floor_activity_level(floor_num)
            
            floor_map[floor_num] = {
                "name": floor_info.name,
                "description": floor_info.description,
                "areas": areas_info,
                "activity": activity_desc,
                "activity_level": activity
            }
        
        return floor_map