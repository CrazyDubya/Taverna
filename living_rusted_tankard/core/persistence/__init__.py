"""
Persistence Package - Advanced save/load system with versioning and migration.

This package provides:
- SaveManager: Main interface for save/load operations
- SaveMigrator: Handles version upgrades and migrations
- SaveValidator: Validates save file integrity
- Versioned save format with backward compatibility
- Automatic migration system
- Corruption detection and recovery
"""

from .save_manager import SaveManager, SaveFormat, SaveMetadata
from .migrations import SaveMigrator, Migration, DEFAULT_MIGRATIONS
from .validation import (
    SaveValidator,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
)

__all__ = [
    # Main classes
    "SaveManager",
    "SaveMigrator",
    "SaveValidator",
    # Data structures
    "SaveFormat",
    "SaveMetadata",
    "Migration",
    "ValidationResult",
    "ValidationIssue",
    "ValidationSeverity",
    # Utilities
    "DEFAULT_MIGRATIONS",
]
