"""
Test suite for the Items system.

Tests item definitions, inventory management, and item effects.
"""
import unittest

from living_rusted_tankard.core.items import (
    Item,
    ItemType,
    Inventory,
    ITEM_DEFINITIONS,
)


class TestItem(unittest.TestCase):
    """Test the Item class."""

    def test_item_creation(self):
        """Test creating an item."""
        item = Item(
            id="test_item",
            name="Test Item",
            description="A test item",
            item_type=ItemType.MISC,
            base_price=10,
        )

        self.assertEqual(item.id, "test_item")
        self.assertEqual(item.name, "Test Item")
        self.assertEqual(item.base_price, 10)
        self.assertEqual(item.item_type, ItemType.MISC)

    def test_item_with_effects(self):
        """Test item with effects."""
        item = Item(
            id="healing_potion",
            name="Healing Potion",
            description="Restores health",
            item_type=ItemType.DRINK,
            base_price=50,
            effects={"health": 50.0, "duration": 0.0},
        )

        self.assertIsNotNone(item.effects)
        self.assertEqual(item.effects.get("health"), 50.0)

    def test_item_types(self):
        """Test different item types."""
        item_types = [ItemType.DRINK, ItemType.FOOD, ItemType.MISC]

        for item_type in item_types:
            item = Item(
                id=f"{item_type.value}_item",
                name=f"{item_type.value.title()} Item",
                description=f"A {item_type.value} item",
                item_type=item_type,
                base_price=10,
            )
            self.assertEqual(item.item_type, item_type)


class TestInventory(unittest.TestCase):
    """Test the Inventory class."""

    def setUp(self):
        """Set up test fixtures."""
        self.inventory = Inventory()
        self.test_item_id = "test_item"
        # Add test item to global definitions
        ITEM_DEFINITIONS[self.test_item_id] = Item(
            id="test_item",
            name="Test Item",
            description="Test",
            item_type=ItemType.MISC,
            base_price=10,
        )

    def test_inventory_initialization(self):
        """Test that inventory initializes empty."""
        self.assertEqual(self.inventory.get_total_items(), 0)

    def test_add_item(self):
        """Test adding an item to inventory."""
        success = self.inventory.add_item(self.test_item_id, quantity=1)
        self.assertTrue(success)
        self.assertEqual(self.inventory.get_total_items(), 1)

    def test_add_multiple_items(self):
        """Test adding multiple quantities of an item."""
        self.inventory.add_item(self.test_item_id, quantity=5)
        self.assertTrue(self.inventory.has_item(self.test_item_id, quantity=5))

    def test_remove_item(self):
        """Test removing an item from inventory."""
        self.inventory.add_item(self.test_item_id, quantity=3)
        success, msg = self.inventory.remove_item(self.test_item_id, quantity=1)

        self.assertTrue(success)
        self.assertTrue(self.inventory.has_item(self.test_item_id, quantity=2))

    def test_remove_nonexistent_item(self):
        """Test removing an item that doesn't exist."""
        success, msg = self.inventory.remove_item("nonexistent_item", quantity=1)
        self.assertFalse(success)

    def test_has_item(self):
        """Test checking if item exists in inventory."""
        self.inventory.add_item(self.test_item_id, quantity=3)

        self.assertTrue(self.inventory.has_item(self.test_item_id, quantity=3))
        self.assertTrue(self.inventory.has_item(self.test_item_id, quantity=1))
        self.assertFalse(self.inventory.has_item(self.test_item_id, quantity=5))

    def test_get_item_quantity(self):
        """Test getting quantity of specific item."""
        self.inventory.add_item(self.test_item_id, quantity=7)
        quantity = self.inventory.get_item_quantity(self.test_item_id)
        self.assertEqual(quantity, 7)

    def test_list_items(self):
        """Test listing all items in inventory."""
        # Add items to global definitions
        ITEM_DEFINITIONS["item1"] = Item(
            id="item1", name="Item 1", description="", item_type=ItemType.MISC, base_price=5
        )
        ITEM_DEFINITIONS["item2"] = Item(
            id="item2", name="Item 2", description="", item_type=ItemType.MISC, base_price=10
        )

        self.inventory.add_item("item1", quantity=2)
        self.inventory.add_item("item2", quantity=3)

        items = self.inventory.list_items_for_display()
        self.assertEqual(len(items), 2)

    def test_inventory_capacity(self):
        """Test inventory capacity limits if implemented."""
        # Add many items to test capacity
        for i in range(100):
            item_id = f"item_{i}"
            ITEM_DEFINITIONS[item_id] = Item(
                id=item_id,
                name=f"Item {i}",
                description="Test",
                item_type=ItemType.MISC,
                base_price=1,
            )
            self.inventory.add_item(item_id, quantity=1)

        # Just verify it doesn't crash
        self.assertGreater(self.inventory.get_total_items(), 0)


class TestItemDefinitions(unittest.TestCase):
    """Test item definition loading and access."""

    def test_item_definitions_exist(self):
        """Test that ITEM_DEFINITIONS is accessible."""
        self.assertIsNotNone(ITEM_DEFINITIONS)

    def test_item_definitions_format(self):
        """Test item definitions have correct format."""
        # Test that we can create items matching expected format
        test_item = Item(
            id="test_sword",
            name="Test Sword",
            description="A test sword",
            item_type=ItemType.MISC,
            base_price=100,
        )

        self.assertEqual(test_item.id, "test_sword")
        self.assertEqual(test_item.item_type, ItemType.MISC)
        self.assertEqual(test_item.base_price, 100)

    def test_item_lookup(self):
        """Test looking up items by ID."""
        if len(ITEM_DEFINITIONS) > 0:
            # Get first item ID
            first_id = list(ITEM_DEFINITIONS.keys())[0]
            item = ITEM_DEFINITIONS.get(first_id)
            self.assertIsNotNone(item)


if __name__ == "__main__":
    unittest.main()
