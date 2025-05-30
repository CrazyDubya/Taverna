"""Atmosphere system for dynamic area properties."""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
import random


class LightLevel(Enum):
    """Lighting conditions in an area."""
    PITCH_BLACK = 0
    VERY_DARK = 1
    DIM = 2
    MODERATE = 3
    BRIGHT = 4
    BLAZING = 5


class NoiseLevel(Enum):
    """Noise levels in an area."""
    SILENT = 0
    QUIET = 1
    MURMUR = 2
    MODERATE = 3
    LOUD = 4
    RAUCOUS = 5
    DEAFENING = 6


class CrowdDensity(Enum):
    """How crowded an area is."""
    EMPTY = 0
    SPARSE = 1
    LIGHT = 2
    MODERATE = 3
    BUSY = 4
    PACKED = 5
    OVERCROWDED = 6


@dataclass
class SensoryDetail:
    """A sensory detail that can be perceived in an area."""
    type: str  # "sight", "sound", "smell", "touch", "taste"
    description: str
    intensity: float = 0.5  # 0.0 to 1.0
    source: Optional[str] = None
    temporary: bool = False
    duration: Optional[float] = None  # hours


@dataclass
class AtmosphereState:
    """Current atmospheric conditions in an area."""
    noise_level: float = 0.3  # 0.0 (silent) to 1.0 (deafening)
    lighting: float = 0.5  # 0.0 (pitch black) to 1.0 (blazing bright)
    crowd_density: float = 0.2  # 0.0 (empty) to 1.0 (overcrowded)
    temperature: float = 0.5  # 0.0 (freezing) to 1.0 (sweltering)
    air_quality: float = 0.7  # 0.0 (suffocating) to 1.0 (fresh)
    
    # Sensory details
    sensory_details: List[SensoryDetail] = field(default_factory=list)
    
    # Environmental modifiers
    visibility_modifier: float = 1.0
    stealth_modifier: float = 1.0
    conversation_difficulty: float = 0.0
    comfort_level: float = 0.5
    
    def get_noise_level(self) -> NoiseLevel:
        """Get discrete noise level."""
        if self.noise_level < 0.1:
            return NoiseLevel.SILENT
        elif self.noise_level < 0.25:
            return NoiseLevel.QUIET
        elif self.noise_level < 0.4:
            return NoiseLevel.MURMUR
        elif self.noise_level < 0.6:
            return NoiseLevel.MODERATE
        elif self.noise_level < 0.75:
            return NoiseLevel.LOUD
        elif self.noise_level < 0.9:
            return NoiseLevel.RAUCOUS
        else:
            return NoiseLevel.DEAFENING
    
    def get_light_level(self) -> LightLevel:
        """Get discrete light level."""
        if self.lighting < 0.1:
            return LightLevel.PITCH_BLACK
        elif self.lighting < 0.25:
            return LightLevel.VERY_DARK
        elif self.lighting < 0.4:
            return LightLevel.DIM
        elif self.lighting < 0.6:
            return LightLevel.MODERATE
        elif self.lighting < 0.8:
            return LightLevel.BRIGHT
        else:
            return LightLevel.BLAZING
    
    def get_crowd_density(self) -> CrowdDensity:
        """Get discrete crowd density."""
        if self.crowd_density < 0.1:
            return CrowdDensity.EMPTY
        elif self.crowd_density < 0.25:
            return CrowdDensity.SPARSE
        elif self.crowd_density < 0.4:
            return CrowdDensity.LIGHT
        elif self.crowd_density < 0.6:
            return CrowdDensity.MODERATE
        elif self.crowd_density < 0.75:
            return CrowdDensity.BUSY
        elif self.crowd_density < 0.9:
            return CrowdDensity.PACKED
        else:
            return CrowdDensity.OVERCROWDED
    
    def affects_conversation(self) -> bool:
        """Check if atmosphere significantly affects conversation."""
        return self.noise_level > 0.6 or self.crowd_density > 0.7
    
    def affects_stealth(self) -> bool:
        """Check if atmosphere affects stealth attempts."""
        # Better stealth in darkness and noise
        return self.lighting < 0.3 or self.noise_level > 0.5
    
    def affects_eavesdropping(self) -> bool:
        """Check if atmosphere affects eavesdropping."""
        # Harder to eavesdrop in noisy/crowded areas
        return self.noise_level > 0.5 or self.crowd_density > 0.6
    
    def calculate_modifiers(self) -> None:
        """Recalculate all modifiers based on current conditions."""
        # Visibility affected by lighting and air quality
        self.visibility_modifier = self.lighting * (0.5 + self.air_quality * 0.5)
        
        # Stealth improved by darkness and noise, hindered by crowds
        darkness_bonus = 1.0 - self.lighting
        noise_cover = min(self.noise_level * 0.5, 0.3)
        crowd_penalty = self.crowd_density * 0.5
        self.stealth_modifier = darkness_bonus + noise_cover - crowd_penalty
        
        # Conversation difficulty from noise and crowds
        self.conversation_difficulty = (self.noise_level * 0.7 + 
                                      self.crowd_density * 0.3)
        
        # Comfort from temperature, air quality, and moderate conditions
        temp_comfort = 1.0 - abs(self.temperature - 0.5) * 2
        air_comfort = self.air_quality
        crowd_comfort = 1.0 - max(0, self.crowd_density - 0.7) * 3
        self.comfort_level = (temp_comfort + air_comfort + crowd_comfort) / 3
    
    def add_sensory_detail(self, detail: SensoryDetail) -> None:
        """Add a sensory detail to the atmosphere."""
        # Remove any existing detail of same type from same source
        if detail.source:
            self.sensory_details = [d for d in self.sensory_details 
                                  if not (d.type == detail.type and 
                                         d.source == detail.source)]
        self.sensory_details.append(detail)
    
    def get_sensory_details(self, sense_type: Optional[str] = None) -> List[SensoryDetail]:
        """Get sensory details, optionally filtered by type."""
        if sense_type:
            return [d for d in self.sensory_details if d.type == sense_type]
        return self.sensory_details.copy()
    
    def describe_atmosphere(self) -> str:
        """Generate a description of the current atmosphere."""
        descriptions = []
        
        # Lighting
        light_level = self.get_light_level()
        if light_level == LightLevel.PITCH_BLACK:
            descriptions.append("The area is shrouded in complete darkness")
        elif light_level == LightLevel.VERY_DARK:
            descriptions.append("Shadows dominate the dimly lit space")
        elif light_level == LightLevel.DIM:
            descriptions.append("Soft lighting creates an intimate atmosphere")
        elif light_level == LightLevel.BRIGHT:
            descriptions.append("Bright lights illuminate every corner")
        
        # Noise
        noise_level = self.get_noise_level()
        if noise_level == NoiseLevel.SILENT:
            descriptions.append("An eerie silence fills the air")
        elif noise_level == NoiseLevel.QUIET:
            descriptions.append("Quiet murmurs barely disturb the peace")
        elif noise_level == NoiseLevel.LOUD:
            descriptions.append("Loud conversations and laughter fill the space")
        elif noise_level == NoiseLevel.RAUCOUS:
            descriptions.append("The cacophony of voices creates a raucous din")
        
        # Crowd
        crowd = self.get_crowd_density()
        if crowd == CrowdDensity.EMPTY:
            descriptions.append("The area stands empty and abandoned")
        elif crowd == CrowdDensity.SPARSE:
            descriptions.append("A few scattered patrons occupy the space")
        elif crowd == CrowdDensity.BUSY:
            descriptions.append("The bustling crowd creates a lively atmosphere")
        elif crowd == CrowdDensity.PACKED:
            descriptions.append("Bodies press together in the packed space")
        
        # Temperature
        if self.temperature < 0.2:
            descriptions.append("A bone-chilling cold permeates the area")
        elif self.temperature > 0.8:
            descriptions.append("Sweltering heat makes the air thick and heavy")
        
        return ". ".join(descriptions) + "."


class AtmosphereManager:
    """Manages atmosphere propagation and time-based changes."""
    
    def __init__(self):
        self.atmospheres: Dict[str, AtmosphereState] = {}
        self.connections: Dict[str, List[Tuple[str, float]]] = {}  # area_id -> [(connected_id, influence)]
    
    def set_atmosphere(self, area_id: str, atmosphere: AtmosphereState) -> None:
        """Set atmosphere for an area."""
        self.atmospheres[area_id] = atmosphere
        atmosphere.calculate_modifiers()
    
    def get_atmosphere(self, area_id: str) -> Optional[AtmosphereState]:
        """Get atmosphere for an area."""
        return self.atmospheres.get(area_id)
    
    def add_connection(self, area1: str, area2: str, influence: float = 0.3) -> None:
        """Add atmospheric connection between areas."""
        if area1 not in self.connections:
            self.connections[area1] = []
        if area2 not in self.connections:
            self.connections[area2] = []
        
        self.connections[area1].append((area2, influence))
        self.connections[area2].append((area1, influence))
    
    def propagate_atmosphere(self) -> None:
        """Propagate atmospheric effects between connected areas."""
        updates = {}
        
        for area_id, atmosphere in self.atmospheres.items():
            if area_id not in self.connections:
                continue
                
            for connected_id, influence in self.connections[area_id]:
                if connected_id not in self.atmospheres:
                    continue
                
                connected = self.atmospheres[connected_id]
                
                # Prepare updates (don't modify during iteration)
                if connected_id not in updates:
                    updates[connected_id] = {
                        'noise': 0,
                        'temperature': 0,
                        'air_quality': 0,
                        'count': 0
                    }
                
                # Sound propagates
                if atmosphere.noise_level > connected.noise_level:
                    updates[connected_id]['noise'] += (
                        atmosphere.noise_level - connected.noise_level
                    ) * influence * 0.5
                
                # Temperature equalizes
                temp_diff = atmosphere.temperature - connected.temperature
                updates[connected_id]['temperature'] += temp_diff * influence * 0.2
                
                # Air quality spreads
                air_diff = atmosphere.air_quality - connected.air_quality  
                updates[connected_id]['air_quality'] += air_diff * influence * 0.3
                
                updates[connected_id]['count'] += 1
        
        # Apply updates
        for area_id, changes in updates.items():
            if changes['count'] == 0:
                continue
                
            atmosphere = self.atmospheres[area_id]
            
            # Average the influences
            count = changes['count']
            atmosphere.noise_level = min(1.0, max(0.0, 
                atmosphere.noise_level + changes['noise'] / count))
            atmosphere.temperature = min(1.0, max(0.0,
                atmosphere.temperature + changes['temperature'] / count))
            atmosphere.air_quality = min(1.0, max(0.0,
                atmosphere.air_quality + changes['air_quality'] / count))
            
            atmosphere.calculate_modifiers()
    
    def update_time_based_changes(self, hour: int, season: str) -> None:
        """Update atmospheres based on time of day and season."""
        for area_id, atmosphere in self.atmospheres.items():
            # Natural lighting changes
            if "window" in area_id.lower() or "outside" in area_id.lower():
                if 6 <= hour <= 18:
                    # Daytime
                    atmosphere.lighting = 0.7 + random.uniform(-0.1, 0.1)
                else:
                    # Nighttime
                    atmosphere.lighting = 0.1 + random.uniform(-0.05, 0.05)
            
            # Temperature changes
            base_temp = 0.5
            if season == "winter":
                base_temp = 0.3
            elif season == "summer":
                base_temp = 0.7
            
            # Time of day temperature variation
            if 12 <= hour <= 16:
                base_temp += 0.1
            elif 2 <= hour <= 6:
                base_temp -= 0.1
                
            atmosphere.temperature = min(1.0, max(0.0, 
                base_temp + random.uniform(-0.05, 0.05)))
            
            # Update expired sensory details
            atmosphere.sensory_details = [
                d for d in atmosphere.sensory_details
                if not d.temporary or d.duration is None or d.duration > 0
            ]
            
            # Decrement durations
            for detail in atmosphere.sensory_details:
                if detail.temporary and detail.duration is not None:
                    detail.duration -= 1.0 / 60  # Assume called every minute
            
            atmosphere.calculate_modifiers()
    
    def get_current_atmosphere(self) -> Dict[str, float]:
        """Get current atmosphere properties for the active area"""
        if not self.atmospheres:
            return {
                'tension': 0.0,
                'comfort': 0.5,
                'mystery': 0.0,
                'safety': 0.8,
                'energy': 0.5
            }
        
        # Use the first atmosphere or find main area
        atmosphere_id = list(self.atmospheres.keys())[0]
        atmosphere = self.atmospheres[atmosphere_id]
        
        return {
            'tension': atmosphere.tension,
            'comfort': atmosphere.comfort,
            'mystery': atmosphere.mystery,
            'safety': atmosphere.safety,
            'energy': atmosphere.energy,
            'lighting': atmosphere.lighting,
            'noise_level': atmosphere.noise_level,
            'temperature': atmosphere.temperature
        }
    
    def apply_area_atmosphere(self, area: Any) -> None:
        """Apply atmosphere settings for a specific area"""
        area_id = getattr(area, 'id', 'unknown')
        
        if area_id not in self.atmospheres:
            # Create default atmosphere for new area
            self.atmospheres[area_id] = Atmosphere()
        
        # Apply area-specific atmosphere settings
        atmosphere = self.atmospheres[area_id]
        
        # Set atmosphere based on area type
        if 'basement' in area_id or 'cellar' in area_id:
            atmosphere.lighting = 0.2
            atmosphere.mystery = 0.7
            atmosphere.safety = 0.4
        elif 'kitchen' in area_id:
            atmosphere.temperature = 0.8
            atmosphere.energy = 0.8
            atmosphere.comfort = 0.6
        elif 'tavern' in area_id:
            atmosphere.comfort = 0.8
            atmosphere.energy = 0.7
            atmosphere.safety = 0.7
        elif 'room' in area_id:
            atmosphere.comfort = 0.9
            atmosphere.safety = 0.9
        
        atmosphere.calculate_modifiers()
    
    def set_atmosphere_property(self, property_name: str, value: float) -> None:
        """Set a specific atmosphere property"""
        if not self.atmospheres:
            self.atmospheres['default'] = Atmosphere()
        
        # Apply to all atmospheres
        for atmosphere in self.atmospheres.values():
            if hasattr(atmosphere, property_name):
                setattr(atmosphere, property_name, max(0.0, min(1.0, value)))
                atmosphere.calculate_modifiers()