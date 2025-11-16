"""
Save Manager - Versioned save format with migration support.

This module provides:
- Versioned save format for backward compatibility
- Migration system for save file upgrades
- Backup and restore functionality
- Save validation and corruption detection
"""

import json
import gzip
import hashlib
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from .migrations import SaveMigrator
from .validation import SaveValidator


class SaveFormat(Enum):
    """Supported save formats."""

    JSON = "json"
    COMPRESSED_JSON = "json.gz"
    BINARY = "binary"


@dataclass
class SaveMetadata:
    """Metadata for save files."""

    version: str
    created_at: str
    game_version: str
    format: SaveFormat
    checksum: str
    size_bytes: int
    session_id: str
    player_name: str
    compressed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SaveMetadata":
        """Create from dictionary."""
        # Handle enum conversion
        if isinstance(data.get("format"), str):
            data["format"] = SaveFormat(data["format"])
        return cls(**data)


class SaveManager:
    """
    Manages game save files with versioning and migration support.

    Features:
    - Versioned save format
    - Automatic migration of old saves
    - Backup creation before migrations
    - Save validation and corruption detection
    - Multiple save formats (JSON, compressed, binary)
    """

    CURRENT_SAVE_VERSION = "1.0.0"
    CURRENT_GAME_VERSION = "0.1.0"  # Should match game version

    def __init__(self, save_directory: str = "saves"):
        self.save_dir = Path(save_directory)
        self.save_dir.mkdir(exist_ok=True)

        self.backup_dir = self.save_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        self.migrator = SaveMigrator()
        self.validator = SaveValidator()

        # Register built-in migrations
        self._register_default_migrations()

    def _register_default_migrations(self):
        """Register default migration functions."""

        # Example migration from 0.9.x to 1.0.0
        def migrate_0_9_to_1_0(save_data: Dict[str, Any]) -> Dict[str, Any]:
            """Migrate save from 0.9.x to 1.0.0."""
            # Add new fields that were introduced in 1.0.0
            if "ai_player_sessions" not in save_data:
                save_data["ai_player_sessions"] = {}

            if "narrative_threads" not in save_data:
                save_data["narrative_threads"] = []

            # Update player structure if needed
            if "player" in save_data:
                player = save_data["player"]
                if "reputation" not in player:
                    player["reputation"] = {}

                if "memory" not in player:
                    player["memory"] = {"events": [], "npcs_met": []}

            return save_data

        self.migrator.register_migration("0.9.0", "1.0.0", migrate_0_9_to_1_0)

    def save_game(
        self,
        game_state: Dict[str, Any],
        save_name: str,
        session_id: str,
        player_name: str,
        format: SaveFormat = SaveFormat.COMPRESSED_JSON,
    ) -> bool:
        """
        Save game state with versioning and metadata.

        Args:
            game_state: Complete game state dictionary
            save_name: Name for the save file
            session_id: Current session identifier
            player_name: Player name for metadata
            format: Save file format

        Returns:
            True if save successful, False otherwise
        """
        try:
            # Prepare save data with metadata
            save_data = {
                "metadata": {
                    "version": self.CURRENT_SAVE_VERSION,
                    "created_at": datetime.utcnow().isoformat(),
                    "game_version": self.CURRENT_GAME_VERSION,
                    "format": format.value,
                    "session_id": session_id,
                    "player_name": player_name,
                    "compressed": format == SaveFormat.COMPRESSED_JSON,
                },
                "game_state": game_state,
            }

            # Validate save data before writing
            validation_result = self.validator.validate_save_data(save_data)
            if not validation_result.is_valid:
                raise ValueError(f"Save validation failed: {validation_result.errors}")

            # Determine save file path
            file_extension = (
                ".save.json.gz"
                if format == SaveFormat.COMPRESSED_JSON
                else ".save.json"
            )
            save_path = self.save_dir / f"{save_name}{file_extension}"

            # Create backup if file exists
            if save_path.exists():
                self._create_backup(save_path)

            # Write save file
            if format == SaveFormat.COMPRESSED_JSON:
                self._write_compressed_save(save_data, save_path)
            elif format == SaveFormat.JSON:
                self._write_json_save(save_data, save_path)
            else:
                raise ValueError(f"Unsupported save format: {format}")

            # Update metadata with file information
            file_size = save_path.stat().st_size
            checksum = self._calculate_checksum(save_path)

            save_data["metadata"]["size_bytes"] = file_size
            save_data["metadata"]["checksum"] = checksum

            # Write metadata file
            metadata_path = save_path.with_suffix(save_path.suffix + ".meta")
            self._write_metadata(save_data["metadata"], metadata_path)

            return True

        except Exception as e:
            print(f"Failed to save game: {e}")
            return False

    def load_game(self, save_name: str) -> Optional[Dict[str, Any]]:
        """
        Load game state with automatic migration if needed.

        Args:
            save_name: Name of the save file to load

        Returns:
            Game state dictionary if successful, None if failed
        """
        try:
            # Find save file
            save_path = self._find_save_file(save_name)
            if not save_path:
                return None

            # Load metadata
            metadata_path = save_path.with_suffix(save_path.suffix + ".meta")
            metadata = self._load_metadata(metadata_path)

            if metadata:
                # Verify file integrity
                current_checksum = self._calculate_checksum(save_path)
                if metadata.checksum != current_checksum:
                    print(f"Warning: Save file checksum mismatch for {save_name}")
                    # Could implement corruption recovery here

            # Load save data
            if save_path.suffix.endswith(".gz"):
                save_data = self._load_compressed_save(save_path)
            else:
                save_data = self._load_json_save(save_path)

            if not save_data:
                return None

            # Check if migration is needed
            save_version = save_data.get("metadata", {}).get("version", "0.0.0")
            if save_version != self.CURRENT_SAVE_VERSION:
                print(
                    f"Migrating save from version {save_version} to {self.CURRENT_SAVE_VERSION}"
                )

                # Create backup before migration
                self._create_backup(save_path, f"pre_migration_{save_version}")

                # Migrate save data
                migrated_data = self.migrator.migrate_save(
                    save_data, self.CURRENT_SAVE_VERSION
                )
                if not migrated_data:
                    print(f"Failed to migrate save from version {save_version}")
                    return None

                # Save migrated version
                self.save_game(
                    migrated_data["game_state"],
                    save_name,
                    migrated_data["metadata"]["session_id"],
                    migrated_data["metadata"]["player_name"],
                )

                save_data = migrated_data

            # Validate loaded save
            validation_result = self.validator.validate_save_data(save_data)
            if not validation_result.is_valid:
                print(f"Loaded save validation failed: {validation_result.errors}")
                # Could attempt recovery or return None

            return save_data["game_state"]

        except Exception as e:
            print(f"Failed to load game {save_name}: {e}")
            return None

    def list_saves(self) -> List[Dict[str, Any]]:
        """
        List all available save files with metadata.

        Returns:
            List of save file information dictionaries
        """
        saves = []

        for save_path in self.save_dir.glob("*.save.json*"):
            if save_path.suffix == ".meta":
                continue

            # Load metadata
            metadata_path = save_path.with_suffix(save_path.suffix + ".meta")
            metadata = self._load_metadata(metadata_path)

            save_info = {
                "name": save_path.stem.replace(".save", ""),
                "path": str(save_path),
                "size_bytes": save_path.stat().st_size,
                "modified_at": datetime.fromtimestamp(
                    save_path.stat().st_mtime
                ).isoformat(),
                "metadata": metadata.to_dict() if metadata else None,
            }

            saves.append(save_info)

        # Sort by modification time (newest first)
        saves.sort(key=lambda x: x["modified_at"], reverse=True)

        return saves

    def delete_save(self, save_name: str, create_backup: bool = True) -> bool:
        """
        Delete a save file.

        Args:
            save_name: Name of save to delete
            create_backup: Whether to create backup before deletion

        Returns:
            True if deletion successful
        """
        try:
            save_path = self._find_save_file(save_name)
            if not save_path:
                return False

            metadata_path = save_path.with_suffix(save_path.suffix + ".meta")

            if create_backup:
                self._create_backup(save_path, "deleted")
                if metadata_path.exists():
                    self._create_backup(metadata_path, "deleted")

            # Delete files
            if save_path.exists():
                save_path.unlink()

            if metadata_path.exists():
                metadata_path.unlink()

            return True

        except Exception as e:
            print(f"Failed to delete save {save_name}: {e}")
            return False

    def create_backup(self, save_name: str, backup_suffix: str = None) -> bool:
        """
        Create a backup of a save file.

        Args:
            save_name: Name of save to backup
            backup_suffix: Optional suffix for backup name

        Returns:
            True if backup created successfully
        """
        try:
            save_path = self._find_save_file(save_name)
            if not save_path:
                return False

            return self._create_backup(save_path, backup_suffix)

        except Exception as e:
            print(f"Failed to create backup for {save_name}: {e}")
            return False

    def restore_backup(self, backup_name: str, restore_as: str = None) -> bool:
        """
        Restore a save from backup.

        Args:
            backup_name: Name of backup to restore
            restore_as: Name for restored save (defaults to original)

        Returns:
            True if restore successful
        """
        try:
            # Find backup file
            backup_path = None
            for backup_file in self.backup_dir.glob(f"*{backup_name}*"):
                if backup_file.suffix.endswith(".json") or backup_file.suffix.endswith(
                    ".gz"
                ):
                    backup_path = backup_file
                    break

            if not backup_path:
                return False

            # Determine restore name
            if not restore_as:
                # Extract original name from backup
                restore_as = backup_path.stem.split("_")[0]

            # Copy backup to save directory
            if backup_path.suffix.endswith(".gz"):
                restore_path = self.save_dir / f"{restore_as}.save.json.gz"
            else:
                restore_path = self.save_dir / f"{restore_as}.save.json"

            shutil.copy2(backup_path, restore_path)

            # Restore metadata if available
            backup_meta = backup_path.with_suffix(backup_path.suffix + ".meta")
            if backup_meta.exists():
                restore_meta = restore_path.with_suffix(restore_path.suffix + ".meta")
                shutil.copy2(backup_meta, restore_meta)

            return True

        except Exception as e:
            print(f"Failed to restore backup {backup_name}: {e}")
            return False

    def _find_save_file(self, save_name: str) -> Optional[Path]:
        """Find save file by name, checking different extensions."""
        candidates = [
            self.save_dir / f"{save_name}.save.json.gz",
            self.save_dir / f"{save_name}.save.json",
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return None

    def _write_json_save(self, save_data: Dict[str, Any], save_path: Path):
        """Write save data as JSON."""
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

    def _write_compressed_save(self, save_data: Dict[str, Any], save_path: Path):
        """Write save data as compressed JSON."""
        json_data = json.dumps(save_data, ensure_ascii=False).encode("utf-8")
        with gzip.open(save_path, "wb") as f:
            f.write(json_data)

    def _load_json_save(self, save_path: Path) -> Optional[Dict[str, Any]]:
        """Load save data from JSON file."""
        try:
            with open(save_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load JSON save {save_path}: {e}")
            return None

    def _load_compressed_save(self, save_path: Path) -> Optional[Dict[str, Any]]:
        """Load save data from compressed JSON file."""
        try:
            with gzip.open(save_path, "rb") as f:
                json_data = f.read().decode("utf-8")
                return json.loads(json_data)
        except Exception as e:
            print(f"Failed to load compressed save {save_path}: {e}")
            return None

    def _write_metadata(self, metadata: Dict[str, Any], metadata_path: Path):
        """Write metadata to file."""
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def _load_metadata(self, metadata_path: Path) -> Optional[SaveMetadata]:
        """Load metadata from file."""
        try:
            if not metadata_path.exists():
                return None

            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_dict = json.load(f)
                return SaveMetadata.from_dict(metadata_dict)
        except Exception as e:
            print(f"Failed to load metadata {metadata_path}: {e}")
            return None

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _create_backup(self, save_path: Path, suffix: str = None) -> bool:
        """Create backup of save file."""
        try:
            timestamp = int(time.time())
            suffix_str = f"_{suffix}" if suffix else ""
            backup_name = f"{save_path.stem}_{timestamp}{suffix_str}{save_path.suffix}"
            backup_path = self.backup_dir / backup_name

            shutil.copy2(save_path, backup_path)

            # Backup metadata if exists
            metadata_path = save_path.with_suffix(save_path.suffix + ".meta")
            if metadata_path.exists():
                backup_meta = backup_path.with_suffix(backup_path.suffix + ".meta")
                shutil.copy2(metadata_path, backup_meta)

            return True

        except Exception as e:
            print(f"Failed to create backup: {e}")
            return False
