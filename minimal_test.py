#!/usr/bin/env python3
"""
Minimal test script for The Living Rusted Tankard components.
"""
import sys
import os
from pathlib import Path

# Add the living_rusted_tankard directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(script_dir, "living_rusted_tankard")
sys.path.insert(0, project_dir)

try:
    print("Testing imports for The Living Rusted Tankard basic components...")
    
    # Import only the very basic components
    from core.items import Item, ItemType
    print("✓ core.items.Item imported successfully")
    
    # Create a simple item
    item = Item(
        id="bread",
        name="Bread",
        description="A loaf of bread",
        item_type=ItemType.FOOD,
        base_price=2
    )
    print(f"✓ Created item: {item.name} (price: {item.base_price} gold)")
    
    print("\nBasic components are working correctly.")
    
except ImportError as e:
    print(f"Error: Failed to import required modules. {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()