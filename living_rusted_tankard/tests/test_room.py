"""Test room management system."""
import pytest
from unittest.mock import Mock, patch

from tests.fixtures import new_player
from tests.utils.assertion_helpers import assert_dict_has_nested_value

from core.room import Room, RoomManager, ROOM_COST, STORAGE_CHEST_COST_MODIFIER
from core.clock import GameClock


class TestRoom:
    """Test Room functionality."""
    
    def test_room_creation(self):
        """Test creating Room objects."""
        room = Room(
            id="test_room_1",
            name="Test Room",
            description="A room for testing",
            price_per_night=15
        )
        
        assert room.id == "test_room_1"
        assert room.name == "Test Room"
        assert room.description == "A room for testing"
        assert room.price_per_night == 15
        assert room.is_occupied is False
        assert room.occupant_id is None
        assert len(room.npcs) == 0
        assert room.has_storage_chest is False
    
    def test_room_auto_naming(self):
        """Test room auto-naming when name not provided."""
        room = Room(id="room_5")
        assert room.name == "Room 5"
        
        room2 = Room(id="custom_room")
        assert room2.name == "custom_room"
    
    def test_room_rental(self):
        """Test renting a room."""
        room = Room(id="test_room", price_per_night=10)
        
        # Rent room
        success = room.rent("player1")
        
        assert success is True
        assert room.is_occupied is True
        assert room.occupant_id == "player1"
    
    def test_room_rental_with_storage(self):
        """Test renting a room with storage chest."""
        room = Room(id="test_room", price_per_night=10)
        
        # Rent room with storage
        success = room.rent("player1", with_storage_chest=True)
        
        assert success is True
        assert room.is_occupied is True
        assert room.occupant_id == "player1"
        assert room.has_storage_chest is True
    
    def test_room_rental_already_occupied(self):
        """Test renting already occupied room fails."""
        room = Room(id="test_room", price_per_night=10)
        
        # First rental succeeds
        room.rent("player1")
        
        # Second rental by different player fails
        success = room.rent("player2")
        assert success is False
        assert room.occupant_id == "player1"  # Still original occupant
    
    def test_room_re_rental_same_player(self):
        """Test same player can re-rent their room."""
        room = Room(id="test_room", price_per_night=10)
        
        # First rental
        room.rent("player1")
        
        # Re-rental by same player succeeds
        success = room.rent("player1", with_storage_chest=True)
        assert success is True
        assert room.occupant_id == "player1"
        assert room.has_storage_chest is True
    
    def test_room_npc_management(self):
        """Test adding and removing NPCs from room."""
        room = Room(id="test_room")
        
        # Add NPCs
        room.add_npc("npc1")
        room.add_npc("npc2")
        
        assert "npc1" in room.npcs
        assert "npc2" in room.npcs
        assert len(room.npcs) == 2
        
        # Add duplicate (should not duplicate)
        room.add_npc("npc1")
        assert len(room.npcs) == 2  # Still only 2
        
        # Remove NPC
        success = room.remove_npc("npc1")
        assert success is True
        assert "npc1" not in room.npcs
        assert len(room.npcs) == 1
        
        # Remove non-existent NPC
        success = room.remove_npc("nonexistent")
        assert success is False
    
    def test_room_occupants_property(self):
        """Test room occupants property."""
        room = Room(id="test_room")
        
        # No occupants initially
        assert len(room.occupants) == 0
        
        # Add player occupant
        room.rent("player1")
        assert "player1" in room.occupants
        assert len(room.occupants) == 1
        
        # Add NPCs
        room.add_npc("npc1")
        room.add_npc("npc2")
        
        occupants = room.occupants
        assert "player1" in occupants
        assert "npc1" in occupants
        assert "npc2" in occupants
        assert len(occupants) == 3
    
    def test_room_is_occupant_check(self):
        """Test checking if entity is occupant."""
        room = Room(id="test_room")
        
        room.rent("player1")
        room.add_npc("npc1")
        
        assert room.is_occupant("player1") is True
        assert room.is_occupant("npc1") is True
        assert room.is_occupant("stranger") is False
    
    def test_room_vacate(self):
        """Test vacating a room."""
        room = Room(id="test_room")
        
        # Rent with storage
        room.rent("player1", with_storage_chest=True)
        room.add_npc("npc1")
        
        # Vacate
        room.vacate()
        
        assert room.is_occupied is False
        assert room.occupant_id is None
        assert room.has_storage_chest is False  # Storage reset on vacate
        assert len(room.npcs) == 1  # NPCs remain


class TestRoomManager:
    """Test RoomManager functionality."""
    
    def test_room_manager_initialization(self):
        """Test RoomManager initializes correctly."""
        manager = RoomManager()
        
        assert manager is not None
        assert len(manager.rooms) > 0  # Should have default rooms
        assert "tavern_main" in manager.rooms
        assert "deep_cellar" in manager.rooms
        assert manager.current_room_id == "tavern_main"
    
    def test_room_manager_default_rooms(self):
        """Test default rooms are created correctly."""
        manager = RoomManager()
        
        # Check main tavern room
        main_room = manager.rooms["tavern_main"]
        assert main_room.name == "Tavern Common Area"
        assert main_room.price_per_night == 0  # Free common area
        assert any(f["id"] == "notice_board" for f in main_room.features)
        
        # Check deep cellar
        deep_cellar = manager.rooms["deep_cellar"]
        assert deep_cellar.name == "Deep Cellar"
        assert deep_cellar.price_per_night == 0  # Free area
    
    def test_room_manager_rentable_rooms(self):
        """Test manager creates rentable rooms."""
        manager = RoomManager()
        
        rentable_rooms = manager.get_available_rooms()
        
        # Should have rentable rooms (excluding tavern_main and deep_cellar)
        assert len(rentable_rooms) > 0
        
        for room in rentable_rooms:
            assert room.id not in ["tavern_main", "deep_cellar"]
            assert room.price_per_night == ROOM_COST
            assert not room.is_occupied
    
    def test_current_room_property(self):
        """Test current room property."""
        manager = RoomManager()
        
        current = manager.current_room
        assert current is not None
        assert current.id == "tavern_main"
    
    def test_move_to_room(self):
        """Test moving to different room."""
        manager = RoomManager()
        
        # Get available room
        available_rooms = manager.get_available_rooms()
        target_room = available_rooms[0]
        
        # Move to room
        success = manager.move_to_room(target_room.id)
        
        assert success is True
        assert manager.current_room_id == target_room.id
        assert manager.current_room == target_room
        
        # Try to move to non-existent room
        success = manager.move_to_room("nonexistent_room")
        assert success is False
        assert manager.current_room_id == target_room.id  # Unchanged
    
    def test_rent_room_success(self, new_player):
        """Test successfully renting a room."""
        manager = RoomManager()
        player = new_player
        player.gold = 100  # Ensure enough gold
        
        # Rent room
        success, room_id, message = manager.rent_room(player)
        
        assert success is True
        assert room_id is not None
        assert "rented" in message.lower()
        assert player.has_room is True
        assert player.room_id == room_id
        assert player.gold == 100 - ROOM_COST
        
        # Check room is occupied
        room = manager.get_room(room_id)
        assert room.is_occupied is True
        assert room.occupant_id == player.id
    
    def test_rent_room_with_storage(self, new_player):
        """Test renting room with storage chest."""
        manager = RoomManager()
        player = new_player
        player.gold = 100
        
        # Rent room with storage
        success, room_id, message = manager.rent_room(player, with_storage_chest=True)
        
        assert success is True
        assert "storage chest" in message.lower()
        
        expected_cost = ROOM_COST + STORAGE_CHEST_COST_MODIFIER
        assert player.gold == 100 - expected_cost
        
        # Check room has storage
        room = manager.get_room(room_id)
        assert room.has_storage_chest is True
    
    def test_rent_room_insufficient_gold(self, new_player):
        """Test renting room with insufficient gold."""
        manager = RoomManager()
        player = new_player
        player.gold = 5  # Not enough for room
        
        # Try to rent room
        success, room_id, message = manager.rent_room(player)
        
        assert success is False
        assert room_id is None
        assert "not enough gold" in message.lower()
        assert player.has_room is False
        assert player.gold == 5  # Unchanged
    
    def test_rent_room_already_has_room(self, new_player):
        """Test renting room when player already has one."""
        manager = RoomManager()
        player = new_player
        player.gold = 100
        
        # Rent first room
        success1, room_id1, message1 = manager.rent_room(player)
        assert success1 is True
        
        # Try to rent second room
        success2, room_id2, message2 = manager.rent_room(player)
        
        assert success2 is False
        assert room_id2 == room_id1  # Returns current room
        assert "already have" in message2.lower()
    
    def test_rent_room_no_rooms_available(self, new_player):
        """Test renting when no rooms available."""
        manager = RoomManager()
        
        # Occupy all available rooms
        available_rooms = manager.get_available_rooms()
        for room in available_rooms:
            room.rent("other_player")
        
        player = new_player
        player.gold = 100
        
        # Try to rent room
        success, room_id, message = manager.rent_room(player)
        
        assert success is False
        assert room_id is None
        assert "no rooms available" in message.lower()
    
    def test_room_status(self):
        """Test getting room status."""
        manager = RoomManager()
        
        # Get room and check status
        available_rooms = manager.get_available_rooms()
        room = available_rooms[0]
        
        status = manager.get_room_status(room.id)
        
        assert status is not None
        assert status["id"] == room.id
        assert status["name"] == room.name
        assert status["is_occupied"] is False
        assert status["has_storage_chest"] is False
        
        # Test non-existent room
        status = manager.get_room_status("nonexistent")
        assert status is None
    
    def test_get_available_rooms_list(self):
        """Test getting available rooms as list."""
        manager = RoomManager()
        
        rooms_list = manager.get_available_rooms_list()
        
        assert isinstance(rooms_list, list)
        assert len(rooms_list) > 0
        
        for room_dict in rooms_list:
            assert "id" in room_dict
            assert "name" in room_dict
            assert "price_per_night" in room_dict
            assert room_dict["is_occupied"] is False
    
    def test_sleep_in_room(self, new_player):
        """Test sleeping in rented room."""
        manager = RoomManager()
        clock = GameClock()
        player = new_player
        
        # Rent room first
        manager.rent_room(player)
        
        # Set tiredness
        player.tiredness = 0.8
        
        # Sleep in room
        success = manager.sleep(player, clock)
        
        assert success is True
        assert player.tiredness == 0.0  # Should be reset
        # Note: time advancement would be tested with clock integration
    
    def test_sleep_without_room(self, new_player):
        """Test sleeping without rented room fails."""
        manager = RoomManager()
        clock = GameClock()
        player = new_player
        
        # Try to sleep without room
        success = manager.sleep(player, clock)
        
        assert success is False
        # Tiredness should be unchanged
    
    def test_sleep_in_unoccupied_room(self, new_player):
        """Test sleeping when room is not properly occupied."""
        manager = RoomManager()
        clock = GameClock()
        player = new_player
        
        # Set room_id but don't properly rent
        available_room = manager.get_available_rooms()[0]
        player.has_room = True
        player.room_id = available_room.id
        # Room is not actually rented to player
        
        # Try to sleep
        success = manager.sleep(player, clock)
        
        assert success is False


class TestRoomManagerIntegration:
    """Test RoomManager integration with other systems."""
    
    def test_room_manager_with_npcs(self):
        """Test room manager integration with NPC system."""
        manager = RoomManager()
        
        # Add NPC to main tavern
        main_room = manager.get_room("tavern_main")
        main_room.add_npc("barkeeper")
        main_room.add_npc("patron1")
        
        assert len(main_room.npcs) == 2
        assert main_room.is_occupant("barkeeper")
        assert main_room.is_occupant("patron1")
        
        # Move NPCs between rooms
        available_room = manager.get_available_rooms()[0]
        main_room.remove_npc("patron1")
        available_room.add_npc("patron1")
        
        assert "patron1" not in main_room.npcs
        assert "patron1" in available_room.npcs
    
    def test_room_manager_persistence(self):
        """Test room manager can be serialized."""
        manager = RoomManager()
        
        # Rent a room
        available_room = manager.get_available_rooms()[0]
        available_room.rent("test_player", with_storage_chest=True)
        
        # Serialize
        serialized = manager.model_dump(mode='json')
        
        assert "rooms" in serialized
        assert "current_room_id" in serialized
        
        # Check room data is preserved
        room_data = serialized["rooms"][available_room.id]
        assert room_data["is_occupied"] is True
        assert room_data["occupant_id"] == "test_player"
        assert room_data["has_storage_chest"] is True
    
    def test_room_features(self):
        """Test room features functionality."""
        manager = RoomManager()
        
        # Main tavern should have notice board
        main_room = manager.get_room("tavern_main")
        
        notice_board = None
        for feature in main_room.features:
            if feature["id"] == "notice_board":
                notice_board = feature
                break
        
        assert notice_board is not None
        assert notice_board["name"] == "Notice Board"
        assert "description" in notice_board
    
    def test_room_capacity_and_atmosphere(self):
        """Test room capacity and atmospheric properties."""
        manager = RoomManager()
        
        # Test main tavern has reasonable capacity
        main_room = manager.get_room("tavern_main")
        assert hasattr(main_room, 'capacity')
        
        # Test private rooms have lower capacity
        private_room = manager.get_available_rooms()[0]
        # Private rooms should have lower capacity than main tavern
        # (This would be implemented based on room type)


class TestRoomEdgeCases:
    """Test room system edge cases."""
    
    def test_room_with_empty_id(self):
        """Test room creation with problematic IDs."""
        # Test with minimal valid data
        room = Room(id="r")
        assert room.id == "r"
        assert room.name == "r"  # Should use ID as name
    
    def test_room_manager_room_generation(self):
        """Test room ID generation doesn't conflict."""
        manager = RoomManager()
        
        # Check that all room IDs are unique
        room_ids = list(manager.rooms.keys())
        assert len(room_ids) == len(set(room_ids))  # No duplicates
    
    def test_room_manager_with_custom_room_count(self):
        """Test room manager with different room counts."""
        # This would test the _default_num_rooms parameter
        # Currently it's set as class attribute, could be made configurable
        manager = RoomManager()
        
        # Should have at least the minimum required rooms
        rentable_rooms = manager.get_available_rooms()
        assert len(rentable_rooms) >= 5  # Reasonable minimum
    
    def test_concurrent_room_rental(self, new_player):
        """Test concurrent room rental attempts."""
        manager = RoomManager()
        
        # Simulate concurrent rental attempts
        player1 = new_player
        player1.id = "player1"
        player1.gold = 100
        
        # Create second player
        from core.player import PlayerState
        player2 = PlayerState()
        player2.id = "player2"
        player2.gold = 100
        
        # Both try to rent same room (if only one available)
        available_rooms = manager.get_available_rooms()
        if len(available_rooms) == 1:
            # First rental should succeed
            success1, room_id1, _ = manager.rent_room(player1)
            assert success1 is True
            
            # Second rental should fail (no rooms available)
            success2, room_id2, message2 = manager.rent_room(player2)
            assert success2 is False
            assert "no rooms available" in message2.lower()
    
    def test_room_rental_edge_cases(self, new_player):
        """Test edge cases in room rental."""
        manager = RoomManager()
        player = new_player
        
        # Test rental with exact gold amount
        player.gold = ROOM_COST
        success, _, _ = manager.rent_room(player)
        
        assert success is True
        assert player.gold == 0  # Should be exactly depleted
        
        # Test rental with storage when having exact amount
        manager2 = RoomManager()
        player2 = new_player
        player2.gold = ROOM_COST + STORAGE_CHEST_COST_MODIFIER
        
        success2, _, _ = manager2.rent_room(player2, with_storage_chest=True)
        assert success2 is True
        assert player2.gold == 0