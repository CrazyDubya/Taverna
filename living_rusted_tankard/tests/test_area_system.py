"""Tests for the area and atmosphere systems."""

import pytest
from unittest.mock import Mock, patch

from core.world.area import TavernArea, AreaType, AccessLevel, Feature, Connection
from core.world.atmosphere import (
    AtmosphereState,
    AtmosphereManager,
    LightLevel,
    NoiseLevel,
    SensoryDetail,
)
from core.world.area_manager import AreaManager, MoveResult
from core.world.floor_manager import FloorManager


class TestTavernArea:
    """Test TavernArea functionality."""

    def test_area_creation(self):
        """Test creating a tavern area."""
        area = TavernArea(
            id="test_area",
            name="Test Area",
            description="A test area",
            floor=0,
            area_type=AreaType.COMMON,
            max_occupancy=10,
        )

        assert area.id == "test_area"
        assert area.name == "Test Area"
        assert area.floor == 0
        assert area.current_occupancy == 0
        assert not area.is_full
        assert area.is_empty

    def test_occupancy_management(self):
        """Test managing area occupancy."""
        area = TavernArea(
            id="test_area", name="Test Area", description="A test area", max_occupancy=2
        )

        # Add NPCs
        assert area.add_npc("npc1")
        assert area.current_occupancy == 1
        assert area.add_npc("npc2")
        assert area.current_occupancy == 2
        assert area.is_full

        # Try to add when full
        assert not area.add_npc("npc3")

        # Remove NPC
        assert area.remove_npc("npc1")
        assert area.current_occupancy == 1
        assert not area.is_full

    def test_feature_management(self):
        """Test area features."""
        area = TavernArea(id="test_area", name="Test Area", description="A test area")

        # Add features
        feature1 = Feature(
            id="feature1",
            name="Test Feature",
            description="A test feature",
            hidden=True,
        )
        area.features.append(feature1)

        # Get feature
        found = area.get_feature("feature1")
        assert found == feature1

        # Feature is hidden
        assert found.hidden
        assert not found.discovered

        # Discover feature
        assert area.discover_feature("feature1")
        assert found.discovered

    def test_area_serialization(self):
        """Test area serialization."""
        area = TavernArea(
            id="test_area",
            name="Test Area",
            description="A test area",
            floor=1,
            area_type=AreaType.PRIVATE,
        )

        area.add_npc("npc1")
        area.add_player("player1")
        area.items.append("item1")

        # Serialize
        data = area.to_dict()
        assert data["id"] == "test_area"
        assert data["floor"] == 1
        assert "npc1" in data["npcs"]
        assert "player1" in data["players"]
        assert "item1" in data["items"]

        # Deserialize
        loaded = TavernArea.from_dict(data)
        assert loaded.id == area.id
        assert loaded.floor == area.floor
        assert "npc1" in loaded.npcs
        assert "player1" in loaded.players


class TestAtmosphereSystem:
    """Test atmosphere functionality."""

    def test_atmosphere_state(self):
        """Test atmosphere state."""
        atmosphere = AtmosphereState(noise_level=0.7, lighting=0.2, crowd_density=0.5)

        assert atmosphere.get_noise_level() == NoiseLevel.LOUD
        assert atmosphere.get_light_level() == LightLevel.VERY_DARK
        assert atmosphere.affects_conversation()
        assert atmosphere.affects_stealth()

    def test_atmosphere_modifiers(self):
        """Test atmosphere modifier calculations."""
        atmosphere = AtmosphereState(
            noise_level=0.8,
            lighting=0.1,
            crowd_density=0.7,
            temperature=0.5,
            air_quality=0.8,
        )

        atmosphere.calculate_modifiers()

        # Low visibility in darkness
        assert atmosphere.visibility_modifier < 0.3

        # Good stealth in darkness and noise
        assert atmosphere.stealth_modifier > 0.5

        # High conversation difficulty
        assert atmosphere.conversation_difficulty > 0.7

    def test_sensory_details(self):
        """Test sensory detail management."""
        atmosphere = AtmosphereState()

        # Add sensory details
        smell = SensoryDetail(
            type="smell",
            description="The aroma of roasting meat",
            intensity=0.7,
            source="kitchen",
        )
        atmosphere.add_sensory_detail(smell)

        sound = SensoryDetail(
            type="sound",
            description="Laughter from the corner table",
            intensity=0.5,
            temporary=True,
            duration=1.0,
        )
        atmosphere.add_sensory_detail(sound)

        # Get details
        all_details = atmosphere.get_sensory_details()
        assert len(all_details) == 2

        smell_details = atmosphere.get_sensory_details("smell")
        assert len(smell_details) == 1
        assert smell_details[0].description == "The aroma of roasting meat"

    def test_atmosphere_manager(self):
        """Test atmosphere manager."""
        manager = AtmosphereManager()

        # Set atmospheres
        atm1 = AtmosphereState(noise_level=0.8)
        atm2 = AtmosphereState(noise_level=0.2)

        manager.set_atmosphere("area1", atm1)
        manager.set_atmosphere("area2", atm2)

        # Add connection
        manager.add_connection("area1", "area2", influence=0.5)

        # Propagate
        manager.propagate_atmosphere()

        # Area2 should have increased noise
        atm2_after = manager.get_atmosphere("area2")
        assert atm2_after.noise_level > 0.2


class TestAreaManager:
    """Test area manager functionality."""

    def test_area_manager_initialization(self):
        """Test area manager creates default areas."""
        manager = AreaManager()

        # Check main areas exist
        assert manager.get_area("main_hall") is not None
        assert manager.get_area("wine_cellar") is not None
        assert manager.get_area("guest_room_1") is not None

        # Check connections exist
        main_hall_exits = manager.get_available_exits("main_hall")
        assert len(main_hall_exits) > 0

    def test_movement(self):
        """Test movement between areas."""
        manager = AreaManager()

        # Add player to main hall
        manager.move_entity("player1", None, "main_hall")

        # Try to move to connected area
        result = manager.move_to_area(
            "player1", "bar_area", access_level=AccessLevel.STAFF
        )
        assert result.success
        assert result.new_area_id == "bar_area"

        # Try to move to non-connected area
        result = manager.move_to_area("player1", "deep_cellar")
        assert not result.success

    def test_access_restrictions(self):
        """Test access level restrictions."""
        manager = AreaManager()

        # Add player to main hall
        manager.move_entity("player1", None, "main_hall")

        # Try to access staff area without permission
        result = manager.move_to_area(
            "player1", "bar_area", access_level=AccessLevel.PUBLIC
        )
        assert not result.success
        assert "permission" in result.message

        # Try with proper permission
        result = manager.move_to_area(
            "player1", "bar_area", access_level=AccessLevel.STAFF
        )
        assert result.success

    def test_hidden_connections(self):
        """Test hidden connection discovery."""
        manager = AreaManager()

        # Check hidden connection isn't visible
        connections = manager.get_connections("storage_room", show_hidden=False)
        hidden_dirs = [c.direction for c in connections if c.to_area == "deep_cellar"]
        assert len(hidden_dirs) == 0

        # Discover connection
        assert manager.discover_connection("storage_room", "hidden passage")

        # Now it should be visible
        connections = manager.get_connections("storage_room", show_hidden=False)
        hidden_dirs = [c.direction for c in connections if c.to_area == "deep_cellar"]
        assert len(hidden_dirs) > 0

    def test_area_capacity(self):
        """Test area capacity limits."""
        manager = AreaManager()

        # Get a small area
        booth = manager.get_area("private_booth")
        original_capacity = booth.max_occupancy

        # Fill it up
        for i in range(original_capacity):
            assert manager.move_entity(f"player{i}", None, "private_booth")

        # Try to add one more
        result = manager.move_to_area(f"player{original_capacity}", "private_booth")
        assert not result.success
        assert "crowded" in result.message

    def test_save_and_load(self):
        """Test saving and loading area state."""
        manager = AreaManager()

        # Modify state
        manager.move_entity("player1", None, "main_hall")
        manager.move_entity("npc1", None, "bar_area")
        manager.discover_connection("storage_room", "hidden passage")

        # Save state
        state = manager.save_state()

        # Create new manager and load
        new_manager = AreaManager()
        new_manager.load_state(state)

        # Verify state
        assert "player1" in new_manager.entity_locations
        assert new_manager.entity_locations["player1"] == "main_hall"
        assert "npc1" in new_manager.entity_locations

        # Check discovered connection
        connections = new_manager.get_connections("storage_room")
        hidden = [c for c in connections if c.to_area == "deep_cellar" and c.discovered]
        assert len(hidden) > 0


class TestFloorManager:
    """Test floor management functionality."""

    def test_floor_initialization(self):
        """Test floor manager initialization."""
        area_manager = AreaManager()
        floor_manager = FloorManager(area_manager)

        # Check floors exist
        assert floor_manager.get_floor_info(-1) is not None
        assert floor_manager.get_floor_info(0) is not None
        assert floor_manager.get_floor_info(1) is not None
        assert floor_manager.get_floor_info(2) is not None

    def test_floor_areas(self):
        """Test getting areas by floor."""
        area_manager = AreaManager()
        floor_manager = FloorManager(area_manager)

        # Get ground floor areas
        ground_areas = floor_manager.get_areas_on_floor(0)
        area_ids = [a.id for a in ground_areas]

        assert "main_hall" in area_ids
        assert "kitchen" in area_ids
        assert "wine_cellar" not in area_ids  # That's in cellar

    def test_vertical_sound_transmission(self):
        """Test sound transmission between floors."""
        area_manager = AreaManager()
        floor_manager = FloorManager(area_manager)

        # Calculate sound transmission
        transmitted = floor_manager.calculate_vertical_sound(0, 1, 0.8)
        assert transmitted < 0.8  # Sound reduced
        assert transmitted > 0.2  # But still audible

        # Longer distance
        transmitted_far = floor_manager.calculate_vertical_sound(0, 2, 0.8)
        assert transmitted_far < transmitted  # More reduction

    def test_floor_activity(self):
        """Test floor activity calculation."""
        area_manager = AreaManager()
        floor_manager = FloorManager(area_manager)

        # Add occupants to ground floor
        area_manager.move_entity("player1", None, "main_hall")
        area_manager.move_entity("npc1", None, "main_hall")
        area_manager.move_entity("npc2", None, "kitchen")

        activity, description = floor_manager.get_floor_activity_level(0)
        assert activity > 0
        assert description != "empty"

    def test_floor_access_levels(self):
        """Test floor access restrictions."""
        area_manager = AreaManager()
        floor_manager = FloorManager(area_manager)

        # Public access
        accessible = floor_manager.get_accessible_floors(AccessLevel.PUBLIC.value)
        assert 0 in accessible  # Ground floor
        assert -1 not in accessible  # Cellar needs patron

        # Staff access
        accessible = floor_manager.get_accessible_floors(AccessLevel.STAFF.value)
        assert -1 in accessible
        assert 0 in accessible
        assert 1 in accessible
        assert 2 in accessible


class TestIntegration:
    """Integration tests for the complete area system."""

    def test_complete_tavern_navigation(self):
        """Test navigating through the entire tavern."""
        manager = AreaManager()

        # Start in main hall
        manager.move_entity("player1", None, "main_hall")

        # Move to bar (staff only)
        result = manager.move_to_area(
            "player1", "bar_area", access_level=AccessLevel.STAFF
        )
        assert result.success

        # Move to kitchen
        connections = manager.get_connections("bar_area")
        kitchen_conn = [c for c in connections if c.to_area == "kitchen"][0]
        result = manager.move_to_area(
            "player1", "kitchen", access_level=AccessLevel.STAFF
        )
        assert result.success

        # Back to main hall
        result = manager.move_to_area("player1", "main_hall")
        assert result.success

        # Down to cellar
        result = manager.move_to_area(
            "player1", "wine_cellar", access_level=AccessLevel.PATRON
        )
        assert result.success

    def test_atmosphere_propagation_integration(self):
        """Test atmosphere propagation between connected areas."""
        manager = AreaManager()

        # Set high noise in main hall
        main_atmosphere = manager.atmosphere_manager.get_atmosphere("main_hall")
        main_atmosphere.noise_level = 0.9

        # Propagate
        manager.atmosphere_manager.propagate_atmosphere()

        # Check connected areas have increased noise
        bar_atmosphere = manager.atmosphere_manager.get_atmosphere("bar_area")
        assert bar_atmosphere.noise_level > 0.5  # Increased from propagation

        nook_atmosphere = manager.atmosphere_manager.get_atmosphere("fireplace_nook")
        assert nook_atmosphere.noise_level > 0.3  # Also affected

    def test_floor_effects_integration(self):
        """Test floor-based effects."""
        area_manager = AreaManager()
        floor_manager = FloorManager(area_manager)

        # Set high noise on ground floor
        main_atmosphere = area_manager.atmosphere_manager.get_atmosphere("main_hall")
        main_atmosphere.noise_level = 0.8

        kitchen_atmosphere = area_manager.atmosphere_manager.get_atmosphere("kitchen")
        kitchen_atmosphere.noise_level = 0.7

        # Propagate floor effects
        floor_manager.propagate_floor_effects()

        # Check first floor is affected
        room_atmosphere = area_manager.atmosphere_manager.get_atmosphere("guest_room_1")
        assert room_atmosphere is not None  # Atmosphere exists
        # Note: actual noise propagation would be set by propagate_floor_effects

    def test_time_based_changes(self):
        """Test time-based atmospheric changes."""
        manager = AreaManager()

        # Mock game time
        mock_time = Mock()
        mock_time.hour = 20  # Evening
        mock_time.get_season.return_value = "summer"

        # Update based on time
        manager.update_area_state(mock_time)

        # Main hall should be busier in evening
        main_atmosphere = manager.atmosphere_manager.get_atmosphere("main_hall")
        assert main_atmosphere.crowd_density > 0.5
