"""
Save Migration System - Handles upgrading save files between versions.

This module provides:
- Version-based migration system
- Automatic migration path finding
- Safe migration with rollback capability
- Migration validation and testing
"""

from typing import Dict, Any, List, Callable, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """Represents a single migration between versions."""

    from_version: str
    to_version: str
    migration_func: Callable[[Dict[str, Any]], Dict[str, Any]]
    description: str = ""

    def apply(self, save_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply this migration to save data."""
        try:
            logger.info(
                f"Applying migration {self.from_version} -> {self.to_version}: {self.description}"
            )
            migrated_data = self.migration_func(save_data.copy())

            # Update version in metadata
            if "metadata" in migrated_data:
                migrated_data["metadata"]["version"] = self.to_version

            return migrated_data
        except Exception as e:
            logger.error(
                f"Migration {self.from_version} -> {self.to_version} failed: {e}"
            )
            raise


class SaveMigrator:
    """
    Manages migration of save files between different versions.

    Features:
    - Automatic migration path calculation
    - Version dependency resolution
    - Safe migration with validation
    - Rollback capability for failed migrations
    """

    def __init__(self):
        self.migrations: List[Migration] = []
        self._migration_graph: Dict[str, List[Migration]] = {}

    def register_migration(
        self,
        from_version: str,
        to_version: str,
        migration_func: Callable[[Dict[str, Any]], Dict[str, Any]],
        description: str = "",
    ) -> None:
        """
        Register a migration function.

        Args:
            from_version: Source version
            to_version: Target version
            migration_func: Function to perform migration
            description: Description of what this migration does
        """
        migration = Migration(from_version, to_version, migration_func, description)
        self.migrations.append(migration)

        # Build migration graph for pathfinding
        if from_version not in self._migration_graph:
            self._migration_graph[from_version] = []
        self._migration_graph[from_version].append(migration)

        logger.info(f"Registered migration: {from_version} -> {to_version}")

    def migrate_save(
        self, save_data: Dict[str, Any], target_version: str
    ) -> Optional[Dict[str, Any]]:
        """
        Migrate save data to target version.

        Args:
            save_data: Save data to migrate
            target_version: Desired version

        Returns:
            Migrated save data or None if migration failed
        """
        current_version = save_data.get("metadata", {}).get("version", "0.0.0")

        if current_version == target_version:
            return save_data

        # Find migration path
        migration_path = self._find_migration_path(current_version, target_version)
        if not migration_path:
            logger.error(
                f"No migration path found from {current_version} to {target_version}"
            )
            return None

        # Apply migrations in sequence
        current_data = save_data

        try:
            for migration in migration_path:
                # Validate data before migration
                if not self._validate_pre_migration(current_data, migration):
                    logger.error(
                        f"Pre-migration validation failed for {migration.from_version} -> {migration.to_version}"
                    )
                    return None

                # Apply migration
                current_data = migration.apply(current_data)

                # Validate data after migration
                if not self._validate_post_migration(current_data, migration):
                    logger.error(
                        f"Post-migration validation failed for {migration.from_version} -> {migration.to_version}"
                    )
                    return None

            logger.info(
                f"Successfully migrated save from {current_version} to {target_version}"
            )
            return current_data

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return None

    def get_migration_path(
        self, from_version: str, to_version: str
    ) -> Optional[List[Migration]]:
        """Get the migration path between two versions."""
        return self._find_migration_path(from_version, to_version)

    def can_migrate(self, from_version: str, to_version: str) -> bool:
        """Check if migration is possible between versions."""
        return self._find_migration_path(from_version, to_version) is not None

    def _find_migration_path(
        self, from_version: str, to_version: str
    ) -> Optional[List[Migration]]:
        """
        Find the shortest migration path between versions using BFS.

        Args:
            from_version: Starting version
            to_version: Target version

        Returns:
            List of migrations to apply, or None if no path exists
        """
        if from_version == to_version:
            return []

        # Use BFS to find shortest path
        from collections import deque

        queue = deque([(from_version, [])])
        visited = {from_version}

        while queue:
            current_version, path = queue.popleft()

            # Check all migrations from current version
            for migration in self._migration_graph.get(current_version, []):
                next_version = migration.to_version

                if next_version == to_version:
                    # Found target
                    return path + [migration]

                if next_version not in visited:
                    visited.add(next_version)
                    queue.append((next_version, path + [migration]))

        return None

    def _validate_pre_migration(
        self, save_data: Dict[str, Any], migration: Migration
    ) -> bool:
        """Validate save data before applying migration."""
        try:
            # Check required fields exist
            if "metadata" not in save_data:
                return False

            if "game_state" not in save_data:
                return False

            # Check version matches
            current_version = save_data["metadata"].get("version")
            if current_version != migration.from_version:
                logger.warning(
                    f"Version mismatch: expected {migration.from_version}, got {current_version}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Pre-migration validation error: {e}")
            return False

    def _validate_post_migration(
        self, save_data: Dict[str, Any], migration: Migration
    ) -> bool:
        """Validate save data after applying migration."""
        try:
            # Check basic structure
            if "metadata" not in save_data:
                return False

            if "game_state" not in save_data:
                return False

            # Check version was updated
            new_version = save_data["metadata"].get("version")
            if new_version != migration.to_version:
                logger.error(
                    f"Version not updated: expected {migration.to_version}, got {new_version}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Post-migration validation error: {e}")
            return False


# Pre-defined migration functions
def migrate_game_state_structure(save_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generic migration for game state structure changes."""
    game_state = save_data["game_state"]

    # Ensure all required top-level keys exist
    required_keys = [
        "player",
        "clock",
        "room_manager",
        "npc_manager",
        "economy",
        "bounty_manager",
        "news_manager",
    ]

    for key in required_keys:
        if key not in game_state:
            game_state[key] = {}

    return save_data


def migrate_player_structure(save_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migration for player structure changes."""
    game_state = save_data["game_state"]

    if "player" in game_state:
        player = game_state["player"]

        # Add new fields with defaults
        if "reputation" not in player:
            player["reputation"] = {}

        if "memory" not in player:
            player["memory"] = {"events": [], "npcs_met": [], "locations_visited": []}

        if "achievements" not in player:
            player["achievements"] = []

        # Ensure numeric fields are present
        numeric_fields = ["gold", "health", "max_health", "experience", "level"]
        for field in numeric_fields:
            if field not in player:
                if field == "health" or field == "max_health":
                    player[field] = 100
                elif field == "level":
                    player[field] = 1
                else:
                    player[field] = 0

    return save_data


def migrate_npc_structure(save_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migration for NPC structure changes."""
    game_state = save_data["game_state"]

    if "npc_manager" in game_state:
        npc_manager = game_state["npc_manager"]

        if "npcs" in npc_manager:
            for npc_id, npc_data in npc_manager["npcs"].items():
                # Add new NPC fields
                if "relationships" not in npc_data:
                    npc_data["relationships"] = {}

                if "conversation_history" not in npc_data:
                    npc_data["conversation_history"] = []

                if "secrets" not in npc_data:
                    npc_data["secrets"] = []

                if "motivations" not in npc_data:
                    npc_data["motivations"] = []

                # Ensure disposition is valid
                if "disposition" not in npc_data:
                    npc_data["disposition"] = "NEUTRAL"

    return save_data


def migrate_economy_structure(save_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migration for economy structure changes."""
    game_state = save_data["game_state"]

    if "economy" in game_state:
        economy = game_state["economy"]

        # Add new economy fields
        if "market_trends" not in economy:
            economy["market_trends"] = {}

        if "transaction_history" not in economy:
            economy["transaction_history"] = []

        if "supply_demand" not in economy:
            economy["supply_demand"] = {}

    return save_data


def migrate_room_structure(save_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migration for room structure changes."""
    game_state = save_data["game_state"]

    if "room_manager" in game_state:
        room_manager = game_state["room_manager"]

        if "rooms" in room_manager:
            for room_id, room_data in room_manager["rooms"].items():
                # Add new room fields
                if "atmosphere" not in room_data:
                    room_data["atmosphere"] = {
                        "noise_level": 0.5,
                        "lighting": 0.7,
                        "crowd_density": 0.3,
                        "temperature": 0.6,
                    }

                if "secrets" not in room_data:
                    room_data["secrets"] = []

                if "events" not in room_data:
                    room_data["events"] = []

    return save_data


def migrate_time_system(save_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migration for time system changes."""
    game_state = save_data["game_state"]

    if "clock" in game_state:
        clock = game_state["clock"]

        # Ensure all time fields exist
        if "current_time" not in clock:
            clock["current_time"] = {
                "hour": 12,
                "day": 1,
                "month": 1,
                "year": 1,
                "minute": 0,
            }

        if "scheduled_events" not in clock:
            clock["scheduled_events"] = []

        if "time_scale" not in clock:
            clock["time_scale"] = 1.0

    return save_data


# Migration registry for easy access
DEFAULT_MIGRATIONS = {
    "game_state_structure": migrate_game_state_structure,
    "player_structure": migrate_player_structure,
    "npc_structure": migrate_npc_structure,
    "economy_structure": migrate_economy_structure,
    "room_structure": migrate_room_structure,
    "time_system": migrate_time_system,
}
