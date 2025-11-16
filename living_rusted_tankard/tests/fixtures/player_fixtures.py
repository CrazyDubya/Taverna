"""Player-related test fixtures."""
import pytest
from unittest.mock import Mock
from typing import Dict, Any

from core.player import Player
from core.items import Item


@pytest.fixture
def new_player():
    """Create a fresh player with default starting state."""
    player = Player(name="TestPlayer")
    player.gold = 100
    player.health = 100
    player.max_health = 100
    player.experience = 0
    player.level = 1
    return player


@pytest.fixture
def experienced_player():
    """Create a player with some progression."""
    player = Player(name="ExperiencedPlayer")
    player.gold = 500
    player.health = 150
    player.max_health = 150
    player.experience = 250
    player.level = 3
    return player


@pytest.fixture
def wealthy_player():
    """Create a player with significant wealth."""
    player = Player(name="WealthyPlayer")
    player.gold = 5000
    player.health = 100
    player.max_health = 100
    player.experience = 100
    player.level = 2
    return player


@pytest.fixture
def injured_player():
    """Create a player with reduced health."""
    player = Player(name="InjuredPlayer")
    player.gold = 200
    player.health = 30
    player.max_health = 100
    player.experience = 50
    player.level = 1
    return player


@pytest.fixture
def player_with_inventory():
    """Create a player with a populated inventory."""
    player = Player(name="InventoryPlayer")
    player.gold = 300

    # Mock some items in inventory
    sword = Mock(spec=Item)
    sword.name = "Iron Sword"
    sword.value = 50
    sword.item_type = "weapon"

    potion = Mock(spec=Item)
    potion.name = "Health Potion"
    potion.value = 25
    potion.item_type = "consumable"

    if hasattr(player, "inventory"):
        player.inventory.extend([sword, potion])
    else:
        player.inventory = [sword, potion]

    return player


@pytest.fixture
def mock_player_states():
    """Provide various player state configurations for testing."""
    return {
        "default": {
            "name": "DefaultPlayer",
            "gold": 100,
            "health": 100,
            "max_health": 100,
            "experience": 0,
            "level": 1,
        },
        "advanced": {
            "name": "AdvancedPlayer",
            "gold": 1000,
            "health": 200,
            "max_health": 200,
            "experience": 500,
            "level": 5,
        },
        "broke": {
            "name": "BrokePlayer",
            "gold": 0,
            "health": 100,
            "max_health": 100,
            "experience": 0,
            "level": 1,
        },
        "nearly_dead": {
            "name": "NearDeathPlayer",
            "gold": 50,
            "health": 5,
            "max_health": 100,
            "experience": 25,
            "level": 1,
        },
    }


@pytest.fixture
def player_progression_tracker():
    """Track player progression changes during tests."""

    class ProgressionTracker:
        def __init__(self):
            self.initial_state = {}
            self.changes = []

        def record_initial_state(self, player: Player):
            self.initial_state = {
                "gold": getattr(player, "gold", 0),
                "health": getattr(player, "health", 100),
                "experience": getattr(player, "experience", 0),
                "level": getattr(player, "level", 1),
            }

        def record_change(self, attribute: str, old_value: Any, new_value: Any):
            self.changes.append(
                {"attribute": attribute, "old_value": old_value, "new_value": new_value}
            )

        def get_progression_summary(self):
            return {"initial": self.initial_state, "changes": self.changes}

    return ProgressionTracker()


@pytest.fixture
def inventory_manager():
    """Utility for managing test inventories."""

    class InventoryManager:
        def __init__(self):
            self.test_items = {}

        def create_test_item(self, name: str, value: int, item_type: str = "misc"):
            item = Mock(spec=Item)
            item.name = name
            item.value = value
            item.item_type = item_type
            self.test_items[name] = item
            return item

        def populate_inventory(self, player: Player, items: list):
            if not hasattr(player, "inventory"):
                player.inventory = []

            for item_spec in items:
                if isinstance(item_spec, str):
                    # Use existing test item
                    if item_spec in self.test_items:
                        player.inventory.append(self.test_items[item_spec])
                elif isinstance(item_spec, dict):
                    # Create new item from spec
                    item = self.create_test_item(**item_spec)
                    player.inventory.append(item)

        def clear_inventory(self, player: Player):
            if hasattr(player, "inventory"):
                player.inventory.clear()

    return InventoryManager()
