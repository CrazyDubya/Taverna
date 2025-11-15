"""NPC loader for The Living Rusted Tankard."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

from .npc import NPC, NPCType, NPCDisposition, NPCInteraction
from .items import Item, TAVERN_ITEMS


class NPCLoader:
    """Handles loading NPCs from JSON definitions."""

    def __init__(self, data_dir: str = "data"):
        """Initialize the NPC loader.

        Args:
            data_dir: Directory containing NPC data files
        """
        self.data_dir = Path(data_dir)
        self._validate_data_dir()

    def _validate_data_dir(self) -> None:
        """Ensure the data directory exists and is valid."""
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        if not self.data_dir.is_dir():
            raise NotADirectoryError(f"Data path is not a directory: {self.data_dir}")

    def load_npcs(self, filename: str = "npcs.json") -> Dict[str, NPC]:
        """Load NPCs from a JSON file.

        Args:
            filename: Name of the JSON file containing NPC definitions

        Returns:
            Dictionary mapping NPC IDs to NPC objects
        """
        file_path = self.data_dir / filename

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"NPC data file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")

        npcs = {}
        for npc_data in data.get("npc_definitions", []):
            try:
                npc = self._create_npc_from_data(npc_data)
                npcs[npc.id] = npc
            except (KeyError, ValueError) as e:
                print(f"Error loading NPC from {npc_data.get('id', 'unknown')}: {e}")
                continue

        return npcs

    def _create_npc_from_data(self, npc_data: Dict[str, Any]) -> NPC:
        """Create an NPC object from raw data.

        Args:
            npc_data: Raw NPC data from JSON

        Returns:
            Initialized NPC object
        """
        # Parse schedule
        schedule = [tuple(hours) for hours in npc_data.get("schedule", [])]

        # Parse inventory
        inventory = []
        for item_data in npc_data.get("inventory", []):
            item_id = item_data["id"]
            if item_id not in TAVERN_ITEMS:
                print(f"Warning: Unknown item {item_id} in NPC {npc_data['id']} inventory")
                continue

            # Get the full item definition from TAVERN_ITEMS
            item = TAVERN_ITEMS[item_id].copy()
            # Update quantity if specified
            if "quantity" in item_data:
                item.quantity = item_data["quantity"]
            inventory.append(item)

        # Create NPC
        npc = NPC(
            id=npc_data["id"],
            name=npc_data["name"],
            description=npc_data["description"],
            npc_type=NPCType[npc_data["npc_type"]],
            disposition=NPCDisposition[npc_data["disposition"]],
            schedule=schedule,
            departure_chance=npc_data.get("departure_chance", 0.1),
            visit_frequency=npc_data.get("visit_frequency", 0.8),
            gold=npc_data.get("gold", 0),
            inventory=inventory,
            relationships=npc_data.get("relationships", {}),
            conversation_topics=npc_data.get("conversation_topics", []),
        )

        return npc


def load_npcs() -> Dict[str, NPC]:
    """Convenience function to load all NPCs."""
    loader = NPCLoader()
    return loader.load_npcs()
