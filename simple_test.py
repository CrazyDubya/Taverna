#!/usr/bin/env python3
"""
Simple test script for The Living Rusted Tankard components.
"""
import sys
import os
from pathlib import Path

# Add the living_rusted_tankard directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(script_dir, "living_rusted_tankard")
sys.path.insert(0, project_dir)

try:
    print("Testing imports for The Living Rusted Tankard components...")
    
    # Try importing core modules
    from core.clock import GameClock, GameTime
    print("✓ core.clock.GameClock")
    
    from core.player import PlayerState
    print("✓ core.player.PlayerState")
    
    from core.npc import NPC, NPCManager
    print("✓ core.npc.NPC, NPCManager")
    
    from core.economy import Economy
    print("✓ core.economy.Economy")
    
    from core.items import Item, Inventory, TAVERN_ITEMS
    print("✓ core.items.Item, Inventory, TAVERN_ITEMS")
    
    from core.room import Room, RoomManager
    print("✓ core.room.Room, RoomManager")
    
    # Setup basic game elements
    print("\nSetting up basic game elements...")
    
    clock = GameClock()
    print("✓ Created GameClock")
    
    player = PlayerState(name="Player", gold=100)
    print("✓ Created PlayerState")
    
    # Try manipulating player inventory
    player_inventory = Inventory()
    player_inventory.add_item("ale", 2)
    print(f"✓ Added items to inventory: {player_inventory.list_items_for_display()}")
    
    print("\nAll components are working correctly.")
    
except ImportError as e:
    print(f"Error: Failed to import required modules. {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()