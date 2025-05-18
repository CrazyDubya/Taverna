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


class Inventory:
    """Player's inventory system."""
    def __init__(self):
        self.items: Dict[str, Item] = {}
        self.gold: int = 0

    def add_item(self, item: Item, quantity: int = 1) -> None:
        """Add an item to the inventory."""
        if item.id in self.items:
            # If item is stackable, we'd increment quantity here
            pass
        else:
            self.items[item.id] = item

    def remove_item(self, item_id: str) -> Optional[Item]:
        """Remove an item from the inventory."""
        return self.items.pop(item_id, None)

    def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by its ID."""
        return self.items.get(item_id)

    def list_items(self) -> List[Item]:
        """List all items in the inventory."""
        return list(self.items.values())


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
