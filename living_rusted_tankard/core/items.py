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


class InventoryItem(BaseModel):
    """Wrapper class for items in the inventory with quantity tracking."""
    item: Item
    quantity: int = 1

    class Config:
        # For Pydantic v2, default is 'protected', which is fine.
        # If compatibility with v1 was needed for private attributes,
        # you might set underscore_attrs_are_private = True,
        # but 'item' and 'quantity' are public.
        pass

class Inventory(BaseModel):
    """Player's inventory system with quantity tracking and stackable items."""
    # Using alias "items" for the serialized output, while keeping _items for internal use.
    # Pydantic will handle mapping this during serialization/deserialization.
    # Or, more simply, just name it 'items' directly if no underscore is desired.
    # For this refactor, let's stick to a public 'items' field for simplicity with Pydantic.
    items: Dict[str, InventoryItem] = Field(default_factory=dict)
        
    def add_item(self, item_to_add: Item, quantity: int = 1) -> tuple[bool, str]: # Renamed 'item' to 'item_to_add'
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
            if item_to_add.id in self.items:
                # Item exists, update quantity
                self.items[item_to_add.id].quantity += quantity
            else:
                # New item
                self.items[item_to_add.id] = InventoryItem(item=item_to_add, quantity=quantity)
                
            return True, f"Added {quantity} x {item_to_add.name} to inventory"
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
            
        if item_id not in self.items:
            return False, f"Item '{item_id}' not found in inventory"
            
        try:
            if self.items[item_id].quantity > quantity:
                # Reduce quantity
                self.items[item_id].quantity -= quantity
                return True, f"Removed {quantity} x {self.items[item_id].item.name}"
            elif self.items[item_id].quantity == quantity:
                # Remove the item entirely
                item_name = self.items[item_id].item.name
                del self.items[item_id]
                return True, f"Removed all {item_name} from inventory"
            else: # quantity to remove is greater than available
                return False, f"Not enough {self.items[item_id].item.name} to remove. Only {self.items[item_id].quantity} available."

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
        if quantity <= 0: # Cannot check for non-positive quantity
            return True # Or False, depending on desired behavior for non-positive checks. Usually True.

        inventory_item_instance = self.items.get(item_id)
        if not inventory_item_instance:
            return False
            
        return inventory_item_instance.quantity >= quantity

    def list_items_for_display(self) -> List[dict]: # Renamed for clarity
        """List all items in the inventory with their quantities for display purposes.
        
        Returns:
            List[dict]: A list of dictionaries containing item info and quantity
        """
        # This method is for display/external use, not direct serialization of state.
        # Pydantic will serialize the 'items' field directly.
        display_list = []
        for item_id, inv_item in self.items.items():
            display_list.append({
                "id": inv_item.item.id,
                "name": inv_item.item.name,
                "description": inv_item.item.description,
                "item_type": inv_item.item.item_type.value,
                "base_price": inv_item.item.base_price,
                "effects": inv_item.item.effects,
                "quantity": inv_item.quantity,
            })
        return display_list
        
    def get_total_items(self) -> int:
        """Get the total number of distinct item types in the inventory."""
        return len(self.items)

    def get_total_quantity(self) -> int:
        """Get the total quantity of all items in the inventory."""
        return sum(inv_item.quantity for inv_item in self.items.values())
        
    def is_empty(self) -> bool:
        """Check if the inventory is empty.
        
        Returns:
            bool: True if the inventory is empty
        """
        return not self.items


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
    "elixir_luck": Item(
        id="elixir_luck",
        name="Elixir of Minor Luck",
        description="A shimmering, faintly glowing potion. Might bring a touch of good fortune.",
        item_type=ItemType.MISC, # Or a new "POTION" type if desired
        base_price=75,
        effects={"luck_modifier": 0.1} # Assuming a temporary luck effect
    ),
    "map_fragment_grove": Item(
        id="map_fragment_grove",
        name="Map Fragment to a Hidden Grove",
        description="A tattered piece of parchment showing a path to a secluded grove, rumored to have rare herbs.",
        item_type=ItemType.MISC,
        base_price=120
    ),
    "exotic_spices": Item(
        id="exotic_spices",
        name="Bag of Exotic Spices",
        description="A small, fragrant bag of spices from a faraway land. Highly valued by cooks.",
        item_type=ItemType.MISC, # Could also be a new "INGREDIENT" type
        base_price=50
    ),
}
