"""
Pydantic models for command parsing in The Living Rusted Tankard.
"""
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CommandType(str, Enum):
    """Valid command types for the game."""

    LOOK = "look"
    WAIT = "wait"
    SLEEP = "sleep"
    RENT = "rent"
    GAMBLE = "gamble"
    TALK = "talk"
    HELP = "help"
    EXIT = "exit"
    UNKNOWN = "unknown"


class Command(BaseModel):
    """Structured representation of a player's command."""

    action: CommandType = Field(..., description="The type of action to perform")
    target: Optional[str] = Field(None, description="The target of the action")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Additional arguments for the command"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the parsed command",
    )


class CommandSchema(BaseModel):
    """Schema for validating command output from the parser."""

    command: CommandType
    target: Optional[str] = None
    arguments: Dict[str, Any] = {}

    class Config:
        schema_extra = {
            "example": {
                "command": "talk",
                "target": "barkeep",
                "arguments": {"topic": "rumors"},
            }
        }
