"""Item system for The Living Rusted Tankard."""
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


class InventoryItem:
    """Wrapper class for items in the inventory with quantity tracking."""
    def __init__(self, item: Item, quantity: int = 1):
        self.item = item
        self.quantity = quantity


class Inventory:
    """Player's inventory system with quantity tracking and stackable items."""
    def __init__(self):
        self._items: Dict[str, InventoryItem] = {}
        
    def add_item(self, item: Item, quantity: int = 1) -> tuple[bool, str]:
        """Add an item to the inventory.
        
        Args:
            item: The Item to add
            quantity: Number of items to add (must be positive)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not isinstance(quantity, int) or quantity <= 0:
            return False, "Quantity must be a positive integer"
            
        try:
            if item.id in self._items:
                # Item exists, update quantity
                self._items[item.id].quantity += quantity
            else:
                # New item
                self._items[item.id] = InventoryItem(item, quantity)
                
            return True, f"Added {quantity} x {item.name} to inventory"
        except Exception as e:
            return False, f"Failed to add item: {str(e)}"

    def remove_item(self, item_id: str, quantity: int = 1) -> tuple[bool, str]:
        """Remove items from the inventory.
        
        Args:
            item_id: ID of the item to remove
            quantity: Number of items to remove (default: 1)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not isinstance(quantity, int) or quantity <= 0:
            return False, "Quantity must be a positive integer"
            
        if item_id not in self._items:
            return False, f"Item '{item_id}' not found in inventory"
            
        try:
            if self._items[item_id].quantity > quantity:
                # Reduce quantity
                self._items[item_id].quantity -= quantity
                return True, f"Removed {quantity} x {self._items[item_id].item.name}"
            else:
                # Remove the item entirely
                item_name = self._items[item_id].item.name
                del self._items[item_id]
                return True, f"Removed all {item_name} from inventory"
        except Exception as e:
            return False, f"Failed to remove item: {str(e)}"

    def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by its ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            Optional[Item]: The item if found, None otherwise
        """
        if item_id in self._items:
            return self._items[item_id].item
        return None
    
    def get_item_quantity(self, item_id: str) -> int:
        """Get the quantity of a specific item in the inventory.
        
        Args:
            item_id: The ID of the item
            
        Returns:
            int: The quantity of the item (0 if not found)
        """
        if item_id in self._items:
            return self._items[item_id].quantity
        return 0

    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check if the inventory has at least the specified quantity of an item.
        
        Args:
            item_id: The ID of the item to check
            quantity: The minimum quantity required (default: 1)
            
        Returns:
            bool: True if the inventory has enough of the item
        """
        if quantity <= 0:
            return False
            
        if item_id not in self._items:
            return False
            
        return self._items[item_id].quantity >= quantity

    def list_items(self) -> List[dict]:
        """List all items in the inventory with their quantities.
        
        Returns:
            List[dict]: A list of dictionaries containing item info and quantity
        """
        return [
            {
                "item": item_data.item,
                "quantity": item_data.quantity,
                "name": item_data.item.name,
                "id": item_data.item.id,
                "type": item_data.item.item_type.value
            }
            for item_data in self._items.values()
        ]
        
    def get_total_items(self) -> int:
        """Get the total number of items in the inventory.
        
        Returns:
            int: Total count of all items
        """
        return sum(item.quantity for item in self._items.values())
        
    def is_empty(self) -> bool:
        """Check if the inventory is empty.
        
        Returns:
            bool: True if the inventory is empty
        """
        return len(self._items) == 0


# Common items in the tavern
TAVERN_ITEMS = {
    "ale": Item(
        id="ale",
        name="Mug of Ale",
        description="A frothy mug of the tavern's house ale.",
        item_type=ItemType.DRINK,
        base_price=2,
        effects={"tiredness": -0.1, "happiness": 0.2}
    ),
    "stew": Item(
        id="stew",
        name="Hearty Stew",
        description="A warm, filling stew with chunks of meat and vegetables.",
        item_type=ItemType.FOOD,
        base_price=3,
        effects={"hunger": -0.5, "tiredness": 0.1}
    ),
    "bread": Item(
        id="bread",
        name="Loaf of Bread",
        description="A fresh loaf of crusty bread.",
        item_type=ItemType.FOOD,
        base_price=1,
        effects={"hunger": -0.3}
    ),
}
