"""
Economy-related test fixtures.
"""

import pytest
from unittest.mock import MagicMock
from typing import Dict, Any, List

try:
    from core.economy import Economy
    from core.items import ItemManager
    ECONOMY_AVAILABLE = True
except ImportError:
    ECONOMY_AVAILABLE = False


@pytest.fixture
def test_item_data():
    """Provide test item data for economy fixtures."""
    return {
        "bread": {
            "id": "bread",
            "name": "Bread",
            "description": "Fresh baked bread",
            "base_price": 2,
            "category": "food",
            "effects": [{"type": "reduce_hunger", "amount": 10}]
        },
        "ale": {
            "id": "ale",
            "name": "Ale",
            "description": "A mug of frothy ale",
            "base_price": 3,
            "category": "drink",
            "effects": [{"type": "reduce_thirst", "amount": 15}]
        },
        "rusty_sword": {
            "id": "rusty_sword",
            "name": "Rusty Sword",
            "description": "An old, rusty sword",
            "base_price": 25,
            "category": "weapon",
            "effects": [{"type": "increase_attack", "amount": 5}]
        },
        "gold_coin": {
            "id": "gold_coin",
            "name": "Gold Coin",
            "description": "A shiny gold coin",
            "base_price": 1,
            "category": "currency",
            "effects": []
        },
        "health_potion": {
            "id": "health_potion",
            "name": "Health Potion",
            "description": "Restores health when consumed",
            "base_price": 15,
            "category": "consumable",
            "effects": [{"type": "restore_health", "amount": 50}]
        }
    }


@pytest.fixture
def test_job_data():
    """Provide test job data for economy fixtures."""
    return {
        "clean_tables": {
            "id": "clean_tables",
            "name": "Clean Tables",
            "description": "Wipe down the tavern tables",
            "base_payment": 5,
            "energy_cost": 10,
            "tiredness_increase": 5,
            "duration_minutes": 15,
            "cooldown_seconds": 300,  # 5 minutes
            "requirements": []
        },
        "wash_dishes": {
            "id": "wash_dishes", 
            "name": "Wash Dishes",
            "description": "Clean the dirty dishes",
            "base_payment": 8,
            "energy_cost": 15,
            "tiredness_increase": 10,
            "duration_minutes": 20,
            "cooldown_seconds": 600,  # 10 minutes
            "requirements": []
        },
        "tend_bar": {
            "id": "tend_bar",
            "name": "Tend Bar",
            "description": "Help serve drinks to customers",
            "base_payment": 12,
            "energy_cost": 20,
            "tiredness_increase": 15,
            "duration_minutes": 30,
            "cooldown_seconds": 900,  # 15 minutes
            "requirements": [{"type": "energy", "amount": 25}]
        },
        "bouncer_duty": {
            "id": "bouncer_duty",
            "name": "Bouncer Duty",
            "description": "Keep order in the tavern",
            "base_payment": 25,
            "energy_cost": 30,
            "tiredness_increase": 20,
            "duration_minutes": 60,
            "cooldown_seconds": 1800,  # 30 minutes
            "requirements": [
                {"type": "energy", "amount": 40},
                {"type": "reputation", "amount": 0.2}
            ]
        }
    }


@pytest.fixture
def mock_economy(test_item_data, test_job_data):
    """Create a mock economy system with test data."""
    class MockEconomy:
        def __init__(self):
            self.items = test_item_data.copy()
            self.jobs = test_job_data.copy()
            self.job_cooldowns = {}
            self.economic_events = []
            self.price_modifiers = {}
        
        def get_item_price(self, item_id: str, quantity: int = 1) -> int:
            """Get the current price of an item."""
            item = self.items.get(item_id)
            if not item:
                return 0
            
            base_price = item["base_price"]
            modifier = self.price_modifiers.get(item_id, 1.0)
            return int(base_price * modifier * quantity)
        
        def can_afford(self, player_gold: int, item_id: str, quantity: int = 1) -> bool:
            """Check if player can afford an item."""
            total_price = self.get_item_price(item_id, quantity)
            return player_gold >= total_price
        
        def purchase_item(self, player_gold: int, item_id: str, quantity: int = 1) -> Dict[str, Any]:
            """Simulate purchasing an item."""
            if not self.can_afford(player_gold, item_id, quantity):
                return {
                    "success": False,
                    "message": "Not enough gold",
                    "cost": self.get_item_price(item_id, quantity)
                }
            
            cost = self.get_item_price(item_id, quantity)
            return {
                "success": True,
                "message": f"Purchased {quantity}x {self.items[item_id]['name']}",
                "cost": cost,
                "new_gold": player_gold - cost,
                "item": self.items[item_id]
            }
        
        def sell_item(self, item_id: str, quantity: int = 1) -> Dict[str, Any]:
            """Simulate selling an item."""
            if item_id not in self.items:
                return {"success": False, "message": "Unknown item"}
            
            # Sell for 70% of base price
            base_price = self.items[item_id]["base_price"]
            sell_price = int(base_price * 0.7 * quantity)
            
            return {
                "success": True,
                "message": f"Sold {quantity}x {self.items[item_id]['name']}",
                "gold_earned": sell_price,
                "item": self.items[item_id]
            }
        
        def can_perform_job(self, job_id: str, player_energy: int, player_gold: int = 0) -> bool:
            """Check if player can perform a job."""
            job = self.jobs.get(job_id)
            if not job:
                return False
            
            # Check cooldown
            if job_id in self.job_cooldowns:
                # In real implementation, would check actual time
                return False
            
            # Check energy requirement
            if player_energy < job["energy_cost"]:
                return False
            
            # Check other requirements
            for req in job.get("requirements", []):
                if req["type"] == "energy" and player_energy < req["amount"]:
                    return False
                # Add other requirement checks as needed
            
            return True
        
        def perform_job(self, job_id: str, player_energy: int) -> Dict[str, Any]:
            """Simulate performing a job."""
            if not self.can_perform_job(job_id, player_energy):
                return {"success": False, "message": "Cannot perform this job"}
            
            job = self.jobs[job_id]
            
            # Set cooldown
            self.job_cooldowns[job_id] = True  # Simplified for testing
            
            return {
                "success": True,
                "message": f"Completed {job['name']}",
                "gold_earned": job["base_payment"],
                "energy_used": job["energy_cost"],
                "tiredness_gained": job["tiredness_increase"],
                "job": job
            }
        
        def add_economic_event(self, event_type: str, effect: Dict[str, Any]):
            """Add an economic event that affects prices."""
            self.economic_events.append({
                "type": event_type,
                "effect": effect
            })
            
            # Apply price modifiers
            if event_type == "price_increase":
                for item_id in effect.get("items", []):
                    current_modifier = self.price_modifiers.get(item_id, 1.0)
                    self.price_modifiers[item_id] = current_modifier * effect.get("multiplier", 1.1)
            elif event_type == "price_decrease":
                for item_id in effect.get("items", []):
                    current_modifier = self.price_modifiers.get(item_id, 1.0)
                    self.price_modifiers[item_id] = current_modifier * effect.get("multiplier", 0.9)
        
        def clear_cooldowns(self):
            """Clear all job cooldowns (for testing)."""
            self.job_cooldowns.clear()
        
        def reset_prices(self):
            """Reset all price modifiers (for testing)."""
            self.price_modifiers.clear()
    
    return MockEconomy()


@pytest.fixture
def economy_with_events(mock_economy):
    """Create an economy with active economic events."""
    # Add some test economic events
    mock_economy.add_economic_event("price_increase", {
        "items": ["bread", "ale"],
        "multiplier": 1.2,
        "reason": "Supply shortage"
    })
    
    mock_economy.add_economic_event("price_decrease", {
        "items": ["rusty_sword"],
        "multiplier": 0.8,
        "reason": "Market oversupply"
    })
    
    return mock_economy


@pytest.fixture
def wealthy_economy_test():
    """Set up an economy test with a wealthy player."""
    def _create_test(starting_gold: int = 1000):
        return {
            "player_gold": starting_gold,
            "expensive_items": ["rusty_sword", "health_potion"],
            "cheap_items": ["bread", "ale"],
            "test_purchases": [
                {"item": "bread", "quantity": 5, "should_succeed": True},
                {"item": "health_potion", "quantity": 2, "should_succeed": True},
                {"item": "rusty_sword", "quantity": 10, "should_succeed": starting_gold >= 250}
            ]
        }
    
    return _create_test


@pytest.fixture
def job_progression_test():
    """Set up a test scenario for job progression."""
    def _create_progression_test():
        progression = [
            {"job": "clean_tables", "energy_required": 10, "expected_payment": 5},
            {"job": "wash_dishes", "energy_required": 15, "expected_payment": 8},
            {"job": "tend_bar", "energy_required": 20, "expected_payment": 12},
            {"job": "bouncer_duty", "energy_required": 30, "expected_payment": 25}
        ]
        
        return {
            "starting_energy": 100,
            "progression": progression,
            "total_expected_earnings": sum(p["expected_payment"] for p in progression)
        }
    
    return _create_progression_test


@pytest.fixture
def gambling_test_setup():
    """Set up gambling mechanics for testing."""
    class MockGambling:
        def __init__(self):
            self.games = {
                "dice": {"min_bet": 1, "max_bet": 50, "house_edge": 0.1},
                "coin_flip": {"min_bet": 1, "max_bet": 100, "house_edge": 0.05},
                "high_card": {"min_bet": 5, "max_bet": 200, "house_edge": 0.15}
            }
            self.results_log = []
        
        def can_place_bet(self, game: str, bet_amount: int, player_gold: int) -> bool:
            """Check if a bet can be placed."""
            if game not in self.games:
                return False
            
            game_config = self.games[game]
            return (game_config["min_bet"] <= bet_amount <= game_config["max_bet"] and
                    player_gold >= bet_amount)
        
        def play_game(self, game: str, bet_amount: int, force_result: str = None) -> Dict[str, Any]:
            """Play a gambling game with optional forced result for testing."""
            if game not in self.games:
                return {"success": False, "message": "Unknown game"}
            
            # For testing, allow forcing win/loss
            if force_result:
                won = force_result == "win"
            else:
                # Simulate with house edge
                import random
                house_edge = self.games[game]["house_edge"]
                won = random.random() > house_edge
            
            result = {
                "success": True,
                "game": game,
                "bet_amount": bet_amount,
                "won": won,
                "payout": bet_amount * 2 if won else 0,
                "net_change": bet_amount if won else -bet_amount
            }
            
            self.results_log.append(result)
            return result
        
        def get_game_stats(self, game: str) -> Dict[str, Any]:
            """Get statistics for a specific game."""
            game_results = [r for r in self.results_log if r["game"] == game]
            if not game_results:
                return {"games_played": 0, "total_bet": 0, "total_won": 0, "win_rate": 0.0}
            
            total_bet = sum(r["bet_amount"] for r in game_results)
            total_won = sum(r["payout"] for r in game_results)
            wins = sum(1 for r in game_results if r["won"])
            
            return {
                "games_played": len(game_results),
                "total_bet": total_bet,
                "total_won": total_won,
                "net_change": total_won - total_bet,
                "win_rate": wins / len(game_results) if game_results else 0.0
            }
    
    return MockGambling()


@pytest.fixture
def economic_scenario_builder():
    """Builder for creating complex economic test scenarios."""
    class EconomicScenarioBuilder:
        def __init__(self):
            self.scenario = {
                "player_gold": 20,
                "player_energy": 100,
                "player_tiredness": 0,
                "inventory": {},
                "job_cooldowns": {},
                "economic_events": [],
                "expected_outcomes": {}
            }
        
        def with_player_gold(self, amount: int):
            self.scenario["player_gold"] = amount
            return self
        
        def with_player_energy(self, amount: int):
            self.scenario["player_energy"] = amount
            return self
        
        def with_inventory_item(self, item_id: str, quantity: int):
            self.scenario["inventory"][item_id] = quantity
            return self
        
        def with_job_cooldown(self, job_id: str):
            self.scenario["job_cooldowns"][job_id] = True
            return self
        
        def with_economic_event(self, event_type: str, effect: Dict[str, Any]):
            self.scenario["economic_events"].append({"type": event_type, "effect": effect})
            return self
        
        def expect_outcome(self, key: str, value: Any):
            self.scenario["expected_outcomes"][key] = value
            return self
        
        def build(self):
            return self.scenario.copy()
    
    return EconomicScenarioBuilder()