"""Pydantic models for LLM parser output validation in The Living Rusted Tankard."""
from enum import Enum
from typing import Dict, Any, Optional, List, Union, Literal

from pydantic import BaseModel, Field, validator, HttpUrl


class ActionType(str, Enum):
    """Valid action types for player commands."""
    LOOK = "look"
    TALK = "talk"
    ASK = "ask"
    GAMBLE = "gamble"
    WORK = "work"
    RENT = "rent"
    SLEEP = "sleep"
    INVENTORY = "inventory"
    HELP = "help"
    EXIT = "exit"


class CommandSchema(BaseModel):
    """Schema for parsed command from LLM."""
    action: Union[ActionType, str] = Field(..., description="The action to perform")
    target: Optional[str] = Field(None, description="The target of the action")
    subject: Optional[str] = Field(None, description="Additional context or subject")
    amount: Optional[int] = Field(None, description="Numeric value (e.g., for gambling)")
    error: Optional[str] = Field(None, description="Error message if parsing failed")
    
    @validator('action', pre=True)
    def validate_action(cls, v):
        """Convert string action to ActionType if possible."""
        if isinstance(v, ActionType):
            return v
        try:
            return ActionType(v.lower())
        except ValueError:
            # If it's not a valid ActionType, return as is
            return v


class CommandOutput(BaseModel):
    """Output from the parser, containing either a valid command or an error."""
    success: bool = Field(..., description="Whether parsing was successful")
    command: Optional[CommandSchema] = Field(None, description="Parsed command if successful")
    error: Optional[str] = Field(None, description="Error message if parsing failed")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Raw response from the LLM")


def format_command_output(command_dict: Dict[str, Any]) -> str:
    """Format a command dictionary into a user-friendly string.
    
    Args:
        command_dict: Dictionary containing command data
        
    Returns:
        Formatted string representation of the command
    """
    if not command_dict:
        return "No command"
        
    action = command_dict.get("action", "").upper()
    target = command_dict.get("target")
    subject = command_dict.get("subject")
    amount = command_dict.get("amount")
    
    parts = [f"Action: {action}"]
    
    if target:
        parts.append(f"Target: {target}")
    if subject:
        parts.append(f"Subject: {subject}")
    if amount is not None:
        parts.append(f"Amount: {amount}")
        
    return " | ".join(parts)
