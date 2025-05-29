"""Economy fixtures for testing."""

import pytest
from typing import Dict, Any, List
from core.economy import Economy
from core.items import Item


@pytest.fixture
def basic_economy():
    """Create a basic economy for testing."""
    return Economy()


@pytest.fixture
def economy_with_items():
    """Create an economy with predefined items."""
    economy = Economy()
    
    # Add basic tavern items
    economy.add_item("ale", 5, 10)
    economy.add_item("bread", 2, 20)
    economy.add_item("cheese", 3, 15)
    economy.add_item("wine", 10, 5)
    
    return economy


@pytest.fixture
def premium_economy():
    """Create an economy with premium items."""
    economy = Economy()
    
    # Add premium items
    economy.add_item("fine_wine", 25, 3)
    economy.add_item("roasted_chicken", 15, 8)
    economy.add_item("imported_cheese", 12, 5)
    economy.add_item("exotic_ale", 18, 4)
    
    return economy


@pytest.fixture
def sample_items_catalog():
    """Create a catalog of sample items."""
    return [
        Item("ale", "A frothy mug of ale", 5),
        Item("bread", "Fresh baked bread", 2),
        Item("cheese", "Aged tavern cheese", 3),
        Item("wine", "Fine vintage wine", 10),
        Item("stew", "Hearty beef stew", 8),
        Item("pie", "Apple pie slice", 4)
    ]


@pytest.fixture
def price_history():
    """Create sample price history data."""
    return {
        "ale": [
            {"date": "2024-01-01", "price": 5, "demand": 10},
            {"date": "2024-01-02", "price": 6, "demand": 8},
            {"date": "2024-01-03", "price": 5, "demand": 12}
        ],
        "wine": [
            {"date": "2024-01-01", "price": 10, "demand": 3},
            {"date": "2024-01-02", "price": 12, "demand": 2},
            {"date": "2024-01-03", "price": 10, "demand": 5}
        ]
    }


@pytest.fixture
def transaction_history():
    """Create sample transaction history."""
    return [
        {
            "id": "txn_001",
            "player": "TestPlayer",
            "item": "ale",
            "quantity": 2,
            "total_cost": 10,
            "timestamp": "2024-01-01T12:00:00"
        },
        {
            "id": "txn_002",
            "player": "TestPlayer",
            "item": "bread",
            "quantity": 1,
            "total_cost": 2,
            "timestamp": "2024-01-01T12:15:00"
        }
    ]


@pytest.fixture
def market_conditions():
    """Create sample market conditions."""
    return {
        "demand_multiplier": 1.2,
        "supply_level": "normal",
        "season_modifier": 0.9,
        "special_events": [],
        "inflation_rate": 0.02
    }


@pytest.fixture
def vendor_inventory():
    """Create sample vendor inventory."""
    return {
        "bartender": [
            {"item": "ale", "quantity": 50, "base_price": 5},
            {"item": "wine", "quantity": 20, "base_price": 10},
            {"item": "spirits", "quantity": 10, "base_price": 15}
        ],
        "cook": [
            {"item": "bread", "quantity": 30, "base_price": 2},
            {"item": "stew", "quantity": 15, "base_price": 8},
            {"item": "pie", "quantity": 10, "base_price": 4}
        ]
    }


@pytest.fixture
def economy_config():
    """Create economy configuration for testing."""
    return {
        "base_prices": {
            "ale": 5,
            "bread": 2,
            "cheese": 3,
            "wine": 10
        },
        "demand_factors": {
            "time_of_day": 1.0,
            "season": 1.0,
            "events": 1.0
        },
        "supply_limits": {
            "ale": 100,
            "bread": 50,
            "cheese": 30,
            "wine": 25
        }
    }