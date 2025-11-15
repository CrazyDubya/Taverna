"""Item system for The Living Rusted Tankard."""

import json
from pathlib import Path
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Types of items in the game."""

    DRINK = "drink"
    FOOD = "food"
    MISC = "misc"


class Item(BaseModel):
    """Base class for all items in the game."""

    id: str
    name: str
    description: str
    item_type: ItemType
    base_price: int = 0
    effects: Dict[str, float] = Field(default_factory=dict)

    def model_copy(self, *args, **kwargs):
        """For compatibility with Pydantic v2 - needed by NPC code."""
        return self.copy(*args, **kwargs)


class InventoryItem(BaseModel):
    """An item in the player's inventory."""

    item: Item
    quantity: int = 1


class Inventory(BaseModel):
    """Player inventory for storing items."""

    items: Dict[str, InventoryItem] = Field(default_factory=dict)

    def add_item(self, item_id: str, quantity: int = 1) -> bool:
        """Add items to the inventory.

        Args:
            item_id: The ID of the item to add
            quantity: The quantity to add (default: 1)

        Returns:
            bool: True if successful, False if item_id not found
        """
        # If this exact item object is already in the inventory, just increase quantity
        if item_id in self.items:
            self.items[item_id].quantity += quantity
            return True

        # Otherwise, find the item in the definitions
        if item_id in ITEM_DEFINITIONS:
            self.items[item_id] = InventoryItem(item=ITEM_DEFINITIONS[item_id], quantity=quantity)
            return True

        print(f"Warning: Item ID '{item_id}' not found in ITEM_DEFINITIONS.")
        return False

    def remove_item(self, item_id: str, quantity: int = 1) -> tuple[bool, str]:
        """Remove items from the inventory.

        Args:
            item_id: The ID of the item to remove
            quantity: The quantity to remove (default: 1)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if item_id not in self.items:
                return False, f"Item '{item_id}' not in inventory."

            if self.items[item_id].quantity > quantity:
                self.items[item_id].quantity -= quantity
                return True, f"Removed {quantity} {self.items[item_id].item.name}(s) from inventory."

            elif self.items[item_id].quantity == quantity:
                # Remove the item entirely
                item_name = self.items[item_id].item.name
                del self.items[item_id]
                return True, f"Removed all {item_name} from inventory"
            else:  # quantity to remove is greater than available
                return (
                    False,
                    f"Not enough {self.items[item_id].item.name} to remove. Only {self.items[item_id].quantity} available.",
                )

        except Exception as e:
            return False, f"Failed to remove item: {str(e)}"

    def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by its ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            Optional[Item]: The item if found, None otherwise
        """
        inventory_item_instance = self.items.get(item_id)
        if inventory_item_instance:
            return inventory_item_instance.item
        return None

    def get_item_quantity(self, item_id: str) -> int:
        """Get the quantity of a specific item in the inventory.

        Args:
            item_id: The ID of the item

        Returns:
            int: The quantity of the item (0 if not found)
        """
        inventory_item_instance = self.items.get(item_id)
        if inventory_item_instance:
            return inventory_item_instance.quantity
        return 0

    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check if the inventory has at least the specified quantity of an item.

        Args:
            item_id: The ID of the item to check
            quantity: The minimum quantity required (default: 1)

        Returns:
            bool: True if the inventory has enough of the item
        """
        if quantity <= 0:  # Cannot check for non-positive quantity
            return True  # Or False, depending on desired behavior for non-positive checks. Usually True.

        inventory_item_instance = self.items.get(item_id)
        if not inventory_item_instance:
            return False

        return inventory_item_instance.quantity >= quantity

    def list_items_for_display(self) -> List[dict]:  # Renamed for clarity
        """List all items in the inventory with their quantities for display purposes.

        Returns:
            List[dict]: A list of dictionaries containing item info and quantity
        """
        # This method is for display/external use, not direct serialization of state.
        # Pydantic will serialize the 'items' field directly.
        display_list = []
        for item_id, inv_item in self.items.items():
            display_list.append(
                {
                    "id": item_id,
                    "name": inv_item.item.name,
                    "description": inv_item.item.description,
                    "quantity": inv_item.quantity,
                    "type": inv_item.item.item_type.value,
                    "base_price": inv_item.item.base_price,
                }
            )
        return display_list

    def is_empty(self) -> bool:
        """Check if the inventory is empty.

        Returns:
            bool: True if inventory has no items, False otherwise.
        """
        return not self.items

    def get_total_items(self) -> int:
        """Get the total number of unique items in the inventory.

        Returns:
            int: The number of unique items
        """
        return len(self.items)

    def get_total_quantity(self) -> int:
        """Get the total quantity of all items in the inventory.

        Returns:
            int: The total quantity of all items
        """
        return sum(item.quantity for item in self.items.values())


# Built-in tavern items that are always available
TAVERN_ITEMS = {
    "ale": Item(
        id="ale",
        name="Mug of Ale",
        description="A frothy mug of the tavern's house ale.",
        item_type=ItemType.MISC,
        base_price=0,
        effects={"happiness": 0.1, "duration_hours": 0.5},
    ),
    "stew": Item(
        id="stew",
        name="Hearty Stew",
        description="A warm, filling stew with chunks of meat and vegetables.",
        item_type=ItemType.FOOD,
        base_price=3,
        effects={"hunger": -0.5, "tiredness": 0.1},
    ),
    "bread": Item(
        id="bread",
        name="Loaf of Bread",
        description="A fresh loaf of crusty bread.",
        item_type=ItemType.MISC,
        base_price=0,
        effects={"hunger_reduction": 0.3, "duration_hours": 0.0},
    ),
}

# Default item definitions - initially empty, populated by load_item_definitions
ITEM_DEFINITIONS = {}


def load_item_definitions(data_dir: Path = Path("data")) -> Dict[str, Item]:
    """Load item definitions from items.json and populate ITEM_DEFINITIONS."""
    global ITEM_DEFINITIONS  # noqa: F824 - modified via .update() and dict assignment

    # First, populate with built-in TAVERN_ITEMS
    ITEM_DEFINITIONS.update(TAVERN_ITEMS)

    try:
        # Then try to load from file
        items_file = data_dir / "items.json"
        if not items_file.exists():
            print(f"Warning: Item definitions file not found at {items_file}")
            return ITEM_DEFINITIONS

        with open(items_file, "r") as f:
            data = json.load(f)

        # Add additional items from file
        for item_data in data.get("items", []):
            item = Item(
                id=item_data["id"],
                name=item_data["name"],
                description=item_data.get("description", ""),
                item_type=ItemType(item_data.get("item_type", "misc")),
                base_price=item_data.get("base_price", 0),
                effects=item_data.get("effects", {}),
            )
            ITEM_DEFINITIONS[item.id] = item

        return ITEM_DEFINITIONS
    except Exception as e:
        print(f"Error loading item definitions: {e}")
        return ITEM_DEFINITIONS
