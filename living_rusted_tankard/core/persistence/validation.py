"""
Save Validation System - Validates save file integrity and structure.

This module provides:
- Save data structure validation
- Content validation and consistency checks
- Corruption detection
- Recovery suggestions for invalid saves
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in save data."""

    severity: ValidationSeverity
    message: str
    path: str  # JSON path to the problematic data
    suggested_fix: Optional[str] = None

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.path}: {self.message}"


@dataclass
class ValidationResult:
    """Result of save data validation."""

    is_valid: bool
    issues: List[ValidationIssue]
    errors: List[str]  # Quick access to error messages
    warnings: List[str]  # Quick access to warning messages

    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] for issue in self.issues)

    def has_warnings(self) -> bool:
        """Check if there are any warning-level issues."""
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)

    def get_critical_issues(self) -> List[ValidationIssue]:
        """Get all critical issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.CRITICAL]

    def summary(self) -> str:
        """Get a summary of validation results."""
        if self.is_valid:
            return "Save data is valid"

        critical = len(self.get_critical_issues())
        errors = len(self.errors)
        warnings = len(self.warnings)

        parts = []
        if critical > 0:
            parts.append(f"{critical} critical issues")
        if errors > 0:
            parts.append(f"{errors} errors")
        if warnings > 0:
            parts.append(f"{warnings} warnings")

        return f"Save validation failed: {', '.join(parts)}"


class SaveValidator:
    """
    Validates save file data for structural integrity and consistency.

    Performs checks for:
    - Required fields and structure
    - Data type validation
    - Value range validation
    - Cross-reference consistency
    - Corruption detection
    """

    def __init__(self):
        self.issues: List[ValidationIssue] = []

    def validate_save_data(self, save_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete save data structure.

        Args:
            save_data: Save data dictionary to validate

        Returns:
            ValidationResult with findings
        """
        self.issues = []

        try:
            # Validate top-level structure
            self._validate_top_level_structure(save_data)

            # Validate metadata
            if "metadata" in save_data:
                self._validate_metadata(save_data["metadata"])

            # Validate game state
            if "game_state" in save_data:
                self._validate_game_state(save_data["game_state"])

            # Cross-reference validation
            self._validate_cross_references(save_data)

        except Exception as e:
            self._add_issue(ValidationSeverity.CRITICAL, f"Validation failed with exception: {e}", "root")

        # Compile results
        errors = [
            issue.message
            for issue in self.issues
            if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
        ]
        warnings = [issue.message for issue in self.issues if issue.severity == ValidationSeverity.WARNING]

        is_valid = len(errors) == 0

        return ValidationResult(is_valid=is_valid, issues=self.issues.copy(), errors=errors, warnings=warnings)

    def _validate_top_level_structure(self, save_data: Dict[str, Any]):
        """Validate top-level save structure."""
        required_fields = ["metadata", "game_state"]

        for field in required_fields:
            if field not in save_data:
                self._add_issue(
                    ValidationSeverity.CRITICAL,
                    f"Missing required field: {field}",
                    "root",
                    f"Add empty {field} object to save data",
                )

        # Check for unexpected top-level fields
        expected_fields = {"metadata", "game_state"}
        for field in save_data:
            if field not in expected_fields:
                self._add_issue(ValidationSeverity.WARNING, f"Unexpected top-level field: {field}", "root")

    def _validate_metadata(self, metadata: Dict[str, Any]):
        """Validate save metadata."""
        required_fields = {
            "version": str,
            "created_at": str,
            "game_version": str,
            "session_id": str,
            "player_name": str,
        }

        for field, expected_type in required_fields.items():
            if field not in metadata:
                self._add_issue(ValidationSeverity.ERROR, f"Missing metadata field: {field}", f"metadata.{field}")
            elif not isinstance(metadata[field], expected_type):
                self._add_issue(
                    ValidationSeverity.ERROR,
                    f"Invalid type for {field}: expected {expected_type.__name__}, got {type(metadata[field]).__name__}",
                    f"metadata.{field}",
                )

        # Validate version format
        if "version" in metadata:
            version_str = metadata["version"]
            if not self._is_valid_version(version_str):
                self._add_issue(
                    ValidationSeverity.WARNING,
                    f"Invalid version format: {version_str}",
                    "metadata.version",
                    "Use semantic versioning (e.g., '1.0.0')",
                )

        # Validate player name
        if "player_name" in metadata:
            player_name = metadata["player_name"]
            if not player_name or len(player_name.strip()) == 0:
                self._add_issue(ValidationSeverity.WARNING, "Player name is empty", "metadata.player_name")

    def _validate_game_state(self, game_state: Dict[str, Any]):
        """Validate game state structure."""
        # Validate major subsystems
        subsystems = {
            "player": self._validate_player,
            "clock": self._validate_clock,
            "room_manager": self._validate_room_manager,
            "npc_manager": self._validate_npc_manager,
            "economy": self._validate_economy,
        }

        for subsystem, validator in subsystems.items():
            if subsystem in game_state:
                try:
                    validator(game_state[subsystem], f"game_state.{subsystem}")
                except Exception as e:
                    self._add_issue(
                        ValidationSeverity.ERROR, f"Validation error in {subsystem}: {e}", f"game_state.{subsystem}"
                    )
            else:
                self._add_issue(
                    ValidationSeverity.WARNING, f"Missing subsystem: {subsystem}", f"game_state.{subsystem}"
                )

    def _validate_player(self, player: Dict[str, Any], path: str):
        """Validate player data."""
        required_fields = {
            "name": str,
            "gold": (int, float),
            "health": (int, float),
            "max_health": (int, float),
            "level": int,
        }

        for field, expected_types in required_fields.items():
            if field not in player:
                self._add_issue(ValidationSeverity.ERROR, f"Missing player field: {field}", f"{path}.{field}")
            else:
                value = player[field]
                if not isinstance(value, expected_types):
                    self._add_issue(
                        ValidationSeverity.ERROR,
                        f"Invalid type for {field}: expected {expected_types}, got {type(value).__name__}",
                        f"{path}.{field}",
                    )

        # Validate value ranges
        if "health" in player and "max_health" in player:
            health = player["health"]
            max_health = player["max_health"]

            if isinstance(health, (int, float)) and isinstance(max_health, (int, float)):
                if health < 0:
                    self._add_issue(ValidationSeverity.ERROR, f"Health cannot be negative: {health}", f"{path}.health")

                if health > max_health:
                    self._add_issue(
                        ValidationSeverity.WARNING,
                        f"Health ({health}) exceeds max_health ({max_health})",
                        f"{path}.health",
                    )

                if max_health <= 0:
                    self._add_issue(
                        ValidationSeverity.ERROR, f"Max health must be positive: {max_health}", f"{path}.max_health"
                    )

        if "gold" in player:
            gold = player["gold"]
            if isinstance(gold, (int, float)) and gold < 0:
                self._add_issue(ValidationSeverity.WARNING, f"Gold is negative: {gold}", f"{path}.gold")

        if "level" in player:
            level = player["level"]
            if isinstance(level, int) and level < 1:
                self._add_issue(ValidationSeverity.ERROR, f"Level must be at least 1: {level}", f"{path}.level")

    def _validate_clock(self, clock: Dict[str, Any], path: str):
        """Validate clock/time data."""
        if "current_time" in clock:
            time_data = clock["current_time"]

            if isinstance(time_data, dict):
                time_fields = {"hour": (0, 23), "day": (1, 30), "month": (1, 12), "year": (1, 9999), "minute": (0, 59)}

                for field, (min_val, max_val) in time_fields.items():
                    if field in time_data:
                        value = time_data[field]
                        if not isinstance(value, int):
                            self._add_issue(
                                ValidationSeverity.ERROR,
                                f"Time field {field} must be integer: {value}",
                                f"{path}.current_time.{field}",
                            )
                        elif not (min_val <= value <= max_val):
                            self._add_issue(
                                ValidationSeverity.ERROR,
                                f"Time field {field} out of range ({min_val}-{max_val}): {value}",
                                f"{path}.current_time.{field}",
                            )

    def _validate_room_manager(self, room_manager: Dict[str, Any], path: str):
        """Validate room manager data."""
        if "rooms" in room_manager:
            rooms = room_manager["rooms"]

            if not isinstance(rooms, dict):
                self._add_issue(ValidationSeverity.ERROR, "Rooms must be a dictionary", f"{path}.rooms")
                return

            for room_id, room_data in rooms.items():
                self._validate_room(room_data, f"{path}.rooms.{room_id}")

    def _validate_room(self, room: Dict[str, Any], path: str):
        """Validate individual room data."""
        required_fields = ["id", "name", "price_per_night", "is_occupied"]

        for field in required_fields:
            if field not in room:
                self._add_issue(ValidationSeverity.WARNING, f"Missing room field: {field}", f"{path}.{field}")

        # Validate price
        if "price_per_night" in room:
            price = room["price_per_night"]
            if not isinstance(price, (int, float)) or price < 0:
                self._add_issue(ValidationSeverity.ERROR, f"Invalid room price: {price}", f"{path}.price_per_night")

    def _validate_npc_manager(self, npc_manager: Dict[str, Any], path: str):
        """Validate NPC manager data."""
        if "npcs" in npc_manager:
            npcs = npc_manager["npcs"]

            if isinstance(npcs, dict):
                for npc_id, npc_data in npcs.items():
                    self._validate_npc(npc_data, f"{path}.npcs.{npc_id}")

    def _validate_npc(self, npc: Dict[str, Any], path: str):
        """Validate individual NPC data."""
        required_fields = ["name", "id"]

        for field in required_fields:
            if field not in npc:
                self._add_issue(ValidationSeverity.WARNING, f"Missing NPC field: {field}", f"{path}.{field}")

        # Validate relationships
        if "relationships" in npc:
            relationships = npc["relationships"]
            if isinstance(relationships, dict):
                for player_id, relationship_value in relationships.items():
                    if not isinstance(relationship_value, (int, float)):
                        self._add_issue(
                            ValidationSeverity.WARNING,
                            f"Invalid relationship value: {relationship_value}",
                            f"{path}.relationships.{player_id}",
                        )

    def _validate_economy(self, economy: Dict[str, Any], path: str):
        """Validate economy data."""
        # Basic structure validation
        if "market_prices" in economy:
            prices = economy["market_prices"]
            if isinstance(prices, dict):
                for item, price in prices.items():
                    if not isinstance(price, (int, float)) or price < 0:
                        self._add_issue(
                            ValidationSeverity.WARNING,
                            f"Invalid price for {item}: {price}",
                            f"{path}.market_prices.{item}",
                        )

    def _validate_cross_references(self, save_data: Dict[str, Any]):
        """Validate cross-references between different parts of save data."""
        if "game_state" not in save_data:
            return

        game_state = save_data["game_state"]

        # Validate player room reference
        if "player" in game_state and "room_manager" in game_state:
            player = game_state["player"]
            room_manager = game_state["room_manager"]

            if player.get("has_room") and "room_id" in player:
                room_id = player["room_id"]
                rooms = room_manager.get("rooms", {})

                if room_id not in rooms:
                    self._add_issue(
                        ValidationSeverity.ERROR,
                        f"Player references non-existent room: {room_id}",
                        "game_state.player.room_id",
                    )
                else:
                    room = rooms[room_id]
                    if not room.get("is_occupied") or room.get("occupant_id") != player.get("id"):
                        self._add_issue(
                            ValidationSeverity.WARNING,
                            f"Room occupancy mismatch for room {room_id}",
                            "game_state.player.room_id",
                        )

    def _is_valid_version(self, version_str: str) -> bool:
        """Check if version string follows semantic versioning."""
        try:
            parts = version_str.split(".")
            if len(parts) != 3:
                return False

            for part in parts:
                int(part)  # Check if numeric

            return True
        except (ValueError, AttributeError):
            return False

    def _add_issue(self, severity: ValidationSeverity, message: str, path: str, suggested_fix: str = None):
        """Add a validation issue."""
        issue = ValidationIssue(severity=severity, message=message, path=path, suggested_fix=suggested_fix)
        self.issues.append(issue)

        # Log based on severity
        if severity == ValidationSeverity.CRITICAL:
            logger.critical(f"Save validation: {issue}")
        elif severity == ValidationSeverity.ERROR:
            logger.error(f"Save validation: {issue}")
        elif severity == ValidationSeverity.WARNING:
            logger.warning(f"Save validation: {issue}")
        else:
            logger.info(f"Save validation: {issue}")


def validate_save_file(save_data: Dict[str, Any]) -> ValidationResult:
    """
    Convenience function to validate save data.

    Args:
        save_data: Save data to validate

    Returns:
        ValidationResult
    """
    validator = SaveValidator()
    return validator.validate_save_data(save_data)
