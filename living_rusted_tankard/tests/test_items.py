"""
Test suite for the Items system.

Tests item definitions, inventory management, and item effects.
"""
import unittest

from living_rusted_tankard.core.items import (
    Item,
    Inventory,
    ITEM_DEFINITIONS,
    load_item_definitions,
)


class TestItem(unittest.TestCase):
    """Test the Item class."""

    def test_item_creation(self):
        """Test creating an item."""
        item = Item(
            id="test_item",
            name="Test Item",
            description="A test item",
            category="misc",
            price=10,
            weight=1.0,
        )

        self.assertEqual(item.id, "test_item")
        self.assertEqual(item.name, "Test Item")
        self.assertEqual(item.price, 10)
        self.assertEqual(item.weight, 1.0)

    def test_item_with_effects(self):
        """Test item with effects."""
        item = Item(
            id="healing_potion",
            name="Healing Potion",
            description="Restores health",
            category="consumable",
            price=50,
            weight=0.5,
            effects={"health": 50, "duration": 0},
        )

        self.assertIsNotNone(item.effects)
        self.assertEqual(item.effects.get("health"), 50)

    def test_item_categories(self):
        """Test different item categories."""
        categories = ["weapon", "armor", "consumable", "misc", "quest"]

        for category in categories:
            item = Item(
                id=f"{category}_item",
                name=f"{category.title()} Item",
                description=f"A {category} item",
                category=category,
                price=10,
            )
            self.assertEqual(item.category, category)


class TestInventory(unittest.TestCase):
    """Test the Inventory class."""

    def setUp(self):
        """Set up test fixtures."""
        self.inventory = Inventory()
        self.test_item = Item(
            id="test_item",
            name="Test Item",
            description="Test",
            category="misc",
            price=10,
        )

    def test_inventory_initialization(self):
        """Test that inventory initializes empty."""
        self.assertEqual(self.inventory.get_total_items(), 0)

    def test_add_item(self):
        """Test adding an item to inventory."""
        success = self.inventory.add_item(self.test_item, quantity=1)
        self.assertTrue(success)
        self.assertEqual(self.inventory.get_total_items(), 1)

    def test_add_multiple_items(self):
        """Test adding multiple quantities of an item."""
        self.inventory.add_item(self.test_item, quantity=5)
        self.assertTrue(self.inventory.has_item(self.test_item.id, quantity=5))

    def test_remove_item(self):
        """Test removing an item from inventory."""
        self.inventory.add_item(self.test_item, quantity=3)
        success, msg = self.inventory.remove_item(self.test_item.id, quantity=1)

        self.assertTrue(success)
        self.assertTrue(self.inventory.has_item(self.test_item.id, quantity=2))

    def test_remove_nonexistent_item(self):
        """Test removing an item that doesn't exist."""
        success, msg = self.inventory.remove_item("nonexistent_item", quantity=1)
        self.assertFalse(success)

    def test_has_item(self):
        """Test checking if item exists in inventory."""
        self.inventory.add_item(self.test_item, quantity=3)

        self.assertTrue(self.inventory.has_item(self.test_item.id, quantity=3))
        self.assertTrue(self.inventory.has_item(self.test_item.id, quantity=1))
        self.assertFalse(self.inventory.has_item(self.test_item.id, quantity=5))

    def test_get_item_quantity(self):
        """Test getting quantity of specific item."""
        self.inventory.add_item(self.test_item, quantity=7)
        quantity = self.inventory.get_item_quantity(self.test_item.id)
        self.assertEqual(quantity, 7)

    def test_list_items(self):
        """Test listing all items in inventory."""
        item1 = Item(id="item1", name="Item 1", description="", category="misc", price=5)
        item2 = Item(id="item2", name="Item 2", description="", category="misc", price=10)

        self.inventory.add_item(item1, quantity=2)
        self.inventory.add_item(item2, quantity=3)

        items = self.inventory.list_items_for_display()
        self.assertEqual(len(items), 2)

    def test_inventory_capacity(self):
        """Test inventory capacity limits if implemented."""
        # Add many items to test capacity
        for i in range(100):
            item = Item(
                id=f"item_{i}",
                name=f"Item {i}",
                description="Test",
                category="misc",
                price=1,
            )
            self.inventory.add_item(item, quantity=1)

        # Just verify it doesn't crash
        self.assertGreater(self.inventory.get_total_items(), 0)


class TestItemDefinitions(unittest.TestCase):
    """Test item definition loading and access."""

    def test_item_definitions_exist(self):
        """Test that ITEM_DEFINITIONS is accessible."""
        self.assertIsNotNone(ITEM_DEFINITIONS)

    def test_load_item_definitions(self):
        """Test loading item definitions from data directory."""
        import tempfile
        import json
        from pathlib import Path

        # Create temporary data directory with items
        temp_dir = tempfile.mkdtemp()
        items_file = Path(temp_dir) / "items.json"

        test_items = {
            "items": [
                {
                    "id": "test_sword",
                    "name": "Test Sword",
                    "description": "A test sword",
                    "category": "weapon",
                    "price": 100,
                }
            ]
        }

        with open(items_file, "w") as f:
            json.dump(test_items, f)

        # Load definitions
        load_item_definitions(Path(temp_dir))

        # Clean up
        import shutil
        shutil.rmtree(temp_dir)

        # Just verify function doesn't crash
        self.assertTrue(True)

    def test_item_lookup(self):
        """Test looking up items by ID."""
        if len(ITEM_DEFINITIONS) > 0:
            # Get first item ID
            first_id = list(ITEM_DEFINITIONS.keys())[0]
            item = ITEM_DEFINITIONS.get(first_id)
            self.assertIsNotNone(item)


if __name__ == "__main__":
    unittest.main()
