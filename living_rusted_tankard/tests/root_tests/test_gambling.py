"""Simple test script for gambling logic."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import random
from living_rusted_tankard.game.mechanics.economy import EconomyMechanics, EconomyState

# Mock clock for testing
class MockClock:
    def __init__(self, current_time=0.0, days_elapsed=0):
        self.current_time = current_time
        self.days_elapsed = days_elapsed

def test_gambling():
    # Set up test environment
    clock = MockClock()
    economy = EconomyMechanics(clock)
    
    # Test 1: Winning scenario
    print("\n--- Testing Win Scenario ---")
    economy.state.gold = 50
    random.seed(42)
    roll = random.random()
    print(f"Random roll: {roll}")
    print(f"Win threshold: {economy.WIN_CHANCE}")
    
    print(f"Starting gold: {economy.state.gold}")
    wager = 20
    print(f"Wagering: {wager}")
    
    result = economy.gamble(wager, {"name": "Test Dealer"})
    print(f"Result: {result}")
    print(f"Gold after win: {economy.state.gold}")
    print(f"Expected gold: 90")
    
    # Test 2: Losing scenario
    print("\n--- Testing Loss Scenario ---")
    economy.state.gold = 50
    random.seed(1)
    roll = random.random()
    print(f"Random roll: {roll}")
    print(f"Win threshold: {economy.WIN_CHANCE}")
    
    print(f"Starting gold: {economy.state.gold}")
    wager = 30
    print(f"Wagering: {wager}")
    
    result = economy.gamble(wager, {"name": "Test Dealer"})
    print(f"Result: {result}")
    print(f"Gold after loss: {economy.state.gold}")
    print(f"Expected gold: 20")

if __name__ == "__main__":
    test_gambling()
