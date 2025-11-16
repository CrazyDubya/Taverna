"""Tests for the inventory and gold management system."""

import pytest
from core.items import Item, ItemType, Inventory, InventoryItem
from core.player import PlayerState

# Test items for use in tests
TEST_ITEMS = {
    "gold_coin": Item(
        id="gold_coin",
        name="Gold Coin",
        description="Shiny gold coin",
        item_type=ItemType.MISC,
        base_price=1,
    ),
    "health_potion": Item(
        id="health_potion",
        name="Health Potion",
        description="Restores health when consumed",
        item_type=ItemType.DRINK,
        base_price=10,
    ),
    "bread": Item(
        id="bread",
        name="Loaf of Bread",
        description="Freshly baked bread",
        item_type=ItemType.FOOD,
        base_price=2,
    ),
}


class TestInventorySystem:
    """Tests for the inventory management system."""

    @pytest.fixture
    def inventory(self):
        """Create a fresh inventory for each test."""
        return Inventory()

    def test_add_item(self, inventory):
        """Test adding items to the inventory."""
        item = TEST_ITEMS["gold_coin"]

        # Add single item
        success, msg = inventory.add_item(item, 1)
        assert success is True
        assert "Added 1 x Gold Coin to inventory" in msg
        assert inventory.get_item_quantity("gold_coin") == 1

        # Add more of the same item
        success, msg = inventory.add_item(item, 2)
        assert success is True
        assert "Added 2 x Gold Coin to inventory" in msg
        assert inventory.get_item_quantity("gold_coin") == 3

    def test_remove_item(self, inventory):
        """Test removing items from the inventory."""
        item = TEST_ITEMS["health_potion"]

        # Add some items first
        inventory.add_item(item, 3)

        # Remove one item
        success, msg = inventory.remove_item("health_potion", 1)
        assert success is True
        assert "Removed 1 x Health Potion" in msg
        assert inventory.get_item_quantity("health_potion") == 2

        # Remove remaining items
        success, msg = inventory.remove_item("health_potion", 2)
        assert success is True
        assert "Removed all Health Potion from inventory" in msg
        assert inventory.get_item_quantity("health_potion") == 0

    def test_remove_nonexistent_item(self, inventory):
        """Test removing items that don't exist."""
        success, msg = inventory.remove_item("nonexistent_item")
        assert success is False
        assert "not found in inventory" in msg

    def test_has_item(self, inventory):
        """Test checking if inventory has items."""
        item = TEST_ITEMS["bread"]

        # Add some items
        inventory.add_item(item, 2)

        # Check quantities
        assert inventory.has_item("bread") is True
        assert inventory.has_item("bread", 1) is True
        assert inventory.has_item("bread", 2) is True
        assert inventory.has_item("bread", 3) is False
        assert inventory.has_item("nonexistent") is False

    def test_list_items(self, inventory):
        """Test listing items in the inventory."""
        # Add multiple items
        inventory.add_item(TEST_ITEMS["gold_coin"], 5)
        inventory.add_item(TEST_ITEMS["health_potion"], 2)

        # Get item list
        items = inventory.list_items()

        # Should have 2 unique items
        assert len(items) == 2

        # Check item details
        item_dict = {item["id"]: item for item in items}
        assert "gold_coin" in item_dict
        assert item_dict["gold_coin"]["quantity"] == 5
        assert item_dict["health_potion"]["quantity"] == 2


class TestGoldManagement:
    """Tests for the player's gold management system."""

    @pytest.fixture
    def player(self):
        """Create a fresh player for each test."""
        return PlayerState()

    def test_add_gold(self, player):
        """Test adding gold to the player."""
        # Initial gold is 40 from PlayerState defaults
        assert player.gold == 40

        # Add gold
        success, msg = player.add_gold(10)
        assert success is True
        assert "Added 10 gold. New total: 50" in msg
        assert player.gold == 50

        # Add more gold
        success, msg = player.add_gold(25)
        assert success is True
        assert "Added 25 gold. New total: 75" in msg
        assert player.gold == 75

    def test_add_invalid_gold(self, player):
        """Test adding invalid amounts of gold."""
        # Add negative amount
        success, msg = player.add_gold(-10)
        assert success is False
        assert "Amount must be a positive number" in msg
        assert player.gold == 40  # Unchanged

        # Add zero
        success, msg = player.add_gold(0)
        assert success is False
        assert "Amount must be a positive number" in msg
        assert player.gold == 40  # Unchanged

    def test_spend_gold(self, player):
        """Test spending gold."""
        # Start with 40 gold

        # Spend some gold
        success, msg = player.spend_gold(15)
        assert success is True
        assert "Spent 15 gold. Remaining: 25" in msg
        assert player.gold == 25

        # Spend more gold
        success, msg = player.spend_gold(10)
        assert success is True
        assert "Spent 10 gold. Remaining: 15" in msg
        assert player.gold == 15

    def test_spend_too_much_gold(self, player):
        """Test spending more gold than available."""
        # Try to spend more than available
        success, msg = player.spend_gold(50)
        assert success is False
        assert "Not enough gold. Needed: 50, Have: 40" in msg
        assert player.gold == 40  # Unchanged

    def test_can_afford(self, player):
        """Test the can_afford check."""
        # Start with 40 gold
        assert player.can_afford(30) is True
        assert player.can_afford(40) is True
        assert player.can_afford(41) is False
        assert player.can_afford(0) is False  # Edge case: zero
        assert player.can_afford(-10) is False  # Edge case: negative


class TestIntegration:
    """Integration tests for inventory and gold systems together."""

    def test_buying_items(self):
        """Test the complete flow of buying items with gold."""
        player = PlayerState()

        # Player starts with 40 gold
        assert player.gold == 40

        # Buy a health potion (costs 10)
        success, msg = player.spend_gold(10)
        assert success is True
        assert player.gold == 30

        # Add potion to inventory
        success, msg = player.inventory.add_item(TEST_ITEMS["health_potion"])
        assert success is True
        assert player.inventory.has_item("health_potion") is True

        # Buy some bread (costs 2)
        success, msg = player.spend_gold(2)
        assert success is True
        assert player.gold == 28

        # Add bread to inventory
        success, msg = player.inventory.add_item(TEST_ITEMS["bread"], 2)
        assert success is True
        assert player.inventory.has_item("bread", 2) is True

        # Verify inventory contents
        items = player.inventory.list_items()
        assert len(items) == 2

        # Check remaining gold
        assert player.gold == 28
