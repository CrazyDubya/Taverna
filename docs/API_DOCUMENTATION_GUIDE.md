# API Documentation Guide

## Overview

This document provides guidelines for documenting The Living Rusted Tankard API.

## Documentation Standards

### Module Documentation

Every module should have a module-level docstring explaining:
- Purpose of the module
- Key classes and functions
- Usage examples
- Dependencies

```python
"""
Module for managing player inventory and items.

This module provides the Inventory class for tracking player items,
as well as Item definitions and item-related operations.

Example:
    ```python
    from living_rusted_tankard.core.items import Inventory
    
    inventory = Inventory()
    inventory.add_item("ale", quantity=3)
    ```

Dependencies:
    - pydantic for data validation
    - pathlib for file operations
"""
```

### Class Documentation

Use Google-style docstrings for all classes:

```python
class Inventory:
    """Manages player inventory items.
    
    The Inventory class tracks items owned by the player, including
    quantities and metadata. It provides methods for adding, removing,
    and querying items.
    
    Attributes:
        items: Dictionary mapping item IDs to InventoryItem objects.
        max_capacity: Maximum number of unique items (default: unlimited).
    
    Example:
        ```python
        inventory = Inventory()
        inventory.add_item("sword_001", quantity=1)
        has_sword = inventory.has_item("sword_001")
        ```
    """
```

### Function Documentation

Document all public functions with:
- Brief description
- Args with types
- Returns with type
- Raises (if applicable)
- Example usage

```python
def add_item(self, item_id: str, quantity: int = 1) -> bool:
    """Add items to the inventory.
    
    Args:
        item_id: Unique identifier for the item to add.
        quantity: Number of items to add (default: 1).
    
    Returns:
        True if item was added successfully, False if item not found.
    
    Raises:
        ValueError: If quantity is negative.
    
    Example:
        ```python
        success = inventory.add_item("potion_health", quantity=5)
        if success:
            print("Added 5 health potions")
        ```
    """
```

### Type Hints

Always use type hints for:
- Function parameters
- Return values
- Class attributes

```python
from typing import Dict, List, Optional

def get_items_by_type(self, item_type: str) -> List[Item]:
    """Get all items of a specific type."""
    pass

def get_item(self, item_id: str) -> Optional[Item]:
    """Get a single item by ID, or None if not found."""
    pass
```

## Documentation Tools

### Generating Documentation

Use Sphinx to generate HTML documentation:

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Initialize Sphinx (one-time setup)
cd docs/
sphinx-quickstart

# Generate documentation
sphinx-build -b html docs/ docs/_build/
```

### Configuration

Add to `docs/conf.py`:

```python
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
```

## API Endpoints

For FastAPI endpoints, document using OpenAPI:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Taverna API",
    description="API for The Living Rusted Tankard game",
    version="1.0.0",
)

class PlayerAction(BaseModel):
    """Player action request.
    
    Attributes:
        action: Type of action (e.g., 'move', 'interact').
        target: Optional target for the action.
    """
    action: str
    target: Optional[str] = None

@app.post("/player/action")
async def player_action(action: PlayerAction):
    """Execute a player action.
    
    This endpoint processes player actions and returns the result.
    
    Args:
        action: PlayerAction object with action details.
    
    Returns:
        ActionResult with success status and message.
    
    Raises:
        HTTPException: If action is invalid or cannot be executed.
    """
    pass
```

## Documentation Checklist

- [ ] All public classes have docstrings
- [ ] All public methods have docstrings
- [ ] All parameters have type hints
- [ ] All return values have type hints
- [ ] Examples are provided for complex functions
- [ ] Module-level docstrings explain purpose
- [ ] README.md is up to date
- [ ] API endpoints are documented with OpenAPI
- [ ] Sphinx documentation builds without errors

## Maintenance

Documentation should be updated whenever:
- New classes or functions are added
- Function signatures change
- New features are implemented
- Bug fixes affect behavior

## Resources

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)
