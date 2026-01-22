"""
Test suite for the World Area system.

Tests areas, connections, features, and navigation.
"""
import unittest

from living_rusted_tankard.core.world.area import (
    Area,
    AreaType,
    AccessLevel,
    Feature,
    Connection,
)


class TestAreaType(unittest.TestCase):
    """Test the AreaType enumeration."""

    def test_area_types_exist(self):
        """Test that all area types are defined."""
        types = [
            AreaType.COMMON,
            AreaType.PRIVATE,
            AreaType.SERVICE,
            AreaType.STORAGE,
            AreaType.SECRET,
            AreaType.OUTDOOR,
        ]
        
        for area_type in types:
            self.assertIsNotNone(area_type)


class TestAccessLevel(unittest.TestCase):
    """Test the AccessLevel enumeration."""

    def test_access_levels_exist(self):
        """Test that all access levels are defined."""
        levels = [
            AccessLevel.PUBLIC,
            AccessLevel.PATRON,
            AccessLevel.GUEST,
            AccessLevel.STAFF,
            AccessLevel.OWNER,
            AccessLevel.SECRET,
        ]
        
        for level in levels:
            self.assertIsNotNone(level)

    def test_access_level_ordering(self):
        """Test that access levels are properly ordered."""
        self.assertLess(AccessLevel.PUBLIC.value, AccessLevel.PATRON.value)
        self.assertLess(AccessLevel.PATRON.value, AccessLevel.STAFF.value)
        self.assertLess(AccessLevel.STAFF.value, AccessLevel.OWNER.value)


class TestFeature(unittest.TestCase):
    """Test the Feature class."""

    def test_feature_creation(self):
        """Test creating a feature."""
        feature = Feature(
            id="fireplace",
            name="Stone Fireplace",
            description="A warm fireplace with crackling flames",
            interaction_verb="examine",
        )
        
        self.assertEqual(feature.id, "fireplace")
        self.assertEqual(feature.name, "Stone Fireplace")

    def test_can_interact_basic(self):
        """Test basic interaction checking."""
        feature = Feature(
            id="table",
            name="Table",
            description="A wooden table",
        )
        
        self.assertTrue(feature.can_interact())

    def test_can_interact_with_required_item(self):
        """Test interaction requiring an item."""
        feature = Feature(
            id="locked_chest",
            name="Locked Chest",
            description="A chest with a lock",
            requires_item="key",
        )
        
        self.assertFalse(feature.can_interact(has_item=False))
        self.assertTrue(feature.can_interact(has_item=True))

    def test_hidden_feature(self):
        """Test hidden feature behavior."""
        feature = Feature(
            id="secret_door",
            name="Secret Door",
            description="A hidden passage",
            hidden=True,
            discovered=False,
        )
        
        self.assertFalse(feature.can_interact())
        
        feature.discovered = True
        self.assertTrue(feature.can_interact())

    def test_one_time_use_feature(self):
        """Test one-time use feature."""
        feature = Feature(
            id="lever",
            name="Lever",
            description="A rusty lever",
            one_time_use=True,
        )
        
        self.assertTrue(feature.can_interact())
        
        feature.interact()
        
        self.assertFalse(feature.can_interact())

    def test_interact_method(self):
        """Test interaction method."""
        feature = Feature(
            id="door",
            name="Door",
            description="A wooden door",
            interaction_verb="open",
        )
        
        result = feature.interact()
        self.assertIsInstance(result, str)
        self.assertIn("open", result.lower())


class TestConnection(unittest.TestCase):
    """Test the Connection class."""

    def test_connection_creation(self):
        """Test creating a connection."""
        connection = Connection(
            from_area="main_hall",
            to_area="kitchen",
            direction="east",
            reverse_direction="west",
            description="A passage leads east to the kitchen",
        )
        
        self.assertEqual(connection.from_area, "main_hall")
        self.assertEqual(connection.to_area, "kitchen")
        self.assertEqual(connection.direction, "east")

    def test_can_traverse_public(self):
        """Test traversing a public connection."""
        connection = Connection(
            from_area="hall",
            to_area="room",
            direction="north",
            reverse_direction="south",
            access_level=AccessLevel.PUBLIC,
        )
        
        self.assertTrue(connection.can_traverse(access=AccessLevel.PUBLIC))

    def test_can_traverse_locked(self):
        """Test traversing a locked connection."""
        connection = Connection(
            from_area="hall",
            to_area="private_room",
            direction="north",
            reverse_direction="south",
            is_locked=True,
            requires_key="room_key",
        )
        
        self.assertFalse(connection.can_traverse(has_key=False))
        self.assertTrue(connection.can_traverse(has_key=True))

    def test_can_traverse_hidden(self):
        """Test traversing a hidden connection."""
        connection = Connection(
            from_area="hall",
            to_area="secret",
            direction="hidden",
            reverse_direction="out",
            is_hidden=True,
            discovered=False,
        )
        
        self.assertFalse(connection.can_traverse())
        
        connection.discovered = True
        self.assertTrue(connection.can_traverse())

    def test_can_traverse_access_level(self):
        """Test access level requirements."""
        connection = Connection(
            from_area="public",
            to_area="staff_only",
            direction="door",
            reverse_direction="door",
            access_level=AccessLevel.STAFF,
        )
        
        self.assertFalse(connection.can_traverse(access=AccessLevel.PUBLIC))
        self.assertFalse(connection.can_traverse(access=AccessLevel.PATRON))
        self.assertTrue(connection.can_traverse(access=AccessLevel.STAFF))
        self.assertTrue(connection.can_traverse(access=AccessLevel.OWNER))


class TestArea(unittest.TestCase):
    """Test the Area class."""

    def test_area_creation(self):
        """Test creating an area."""
        area = Area(
            id="main_hall",
            name="Main Hall",
            description="A grand hall with high ceilings",
            area_type=AreaType.COMMON,
        )
        
        self.assertEqual(area.id, "main_hall")
        self.assertEqual(area.name, "Main Hall")
        self.assertEqual(area.area_type, AreaType.COMMON)

    def test_add_feature(self):
        """Test adding features to an area."""
        area = Area(
            id="room",
            name="Room",
            description="A room",
            area_type=AreaType.COMMON,
        )
        
        feature = Feature(
            id="chest",
            name="Chest",
            description="A wooden chest",
        )
        
        area.add_feature(feature)
        
        self.assertIn("chest", area.features)

    def test_add_connection(self):
        """Test adding connections to an area."""
        area = Area(
            id="hall",
            name="Hall",
            description="A hallway",
            area_type=AreaType.COMMON,
        )
        
        connection = Connection(
            from_area="hall",
            to_area="room",
            direction="north",
            reverse_direction="south",
        )
        
        area.add_connection(connection)
        
        self.assertIn("north", area.connections)

    def test_get_feature(self):
        """Test retrieving a feature."""
        area = Area(
            id="room",
            name="Room",
            description="A room",
            area_type=AreaType.COMMON,
        )
        
        feature = Feature(id="table", name="Table", description="A table")
        area.add_feature(feature)
        
        retrieved = area.get_feature("table")
        self.assertEqual(retrieved.id, "table")

    def test_get_available_directions(self):
        """Test getting available movement directions."""
        area = Area(
            id="hall",
            name="Hall",
            description="A hallway",
            area_type=AreaType.COMMON,
        )
        
        conn1 = Connection(
            from_area="hall", to_area="room1",
            direction="north", reverse_direction="south"
        )
        conn2 = Connection(
            from_area="hall", to_area="room2",
            direction="east", reverse_direction="west"
        )
        
        area.add_connection(conn1)
        area.add_connection(conn2)
        
        directions = area.get_available_directions()
        self.assertIn("north", directions)
        self.assertIn("east", directions)


if __name__ == "__main__":
    unittest.main()
