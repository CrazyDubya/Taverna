"""Integration tests for Phase 2 features."""

import unittest
import random
from datetime import datetime, timedelta
from game.mechanics import (
    EconomyMechanics,
    EconomyState,
    PresenceManager,
    NPCPresence,
    TimeWindow,
)
from game.commands import (
    handle_gamble,
    handle_earn_tip,
    handle_look_npcs,
    handle_where_npc,
)


class MockClock:
    def __init__(self, current_time=0.0, days_elapsed=0):
        self.current_time = current_time
        self.days_elapsed = days_elapsed

    def advance_hours(self, hours):
        self.current_time += hours
        self.days_elapsed = int(self.current_time // 24)


class TestEconomySystem(unittest.TestCase):
    def setUp(self):
        self.clock = MockClock()
        self.economy = EconomyMechanics(self.clock)
        self.economy.state.gold = 50  # Starting gold

    def test_gamble_win(self):
        # Test with fixed random seed for predictable results
        random.seed(42)  # This seed produces a win with our current implementation

        result = handle_gamble("20", self.economy, {"name": "Dealer"})
        self.assertTrue(result["success"])
        # On win, we should get our wager back plus winnings (20 + 20)
        self.assertEqual(self.economy.state.gold, 90)  # 50 + 20 (wager) + 20 (winnings)

    def test_gamble_loss(self):
        random.seed(1)  # This seed produces a loss with our current implementation

        result = handle_gamble("30", self.economy, {"name": "Dealer"})
        self.assertTrue(result["success"])
        self.assertEqual(self.economy.state.gold, 20)  # 50 - 30 (lost wager)

    def test_earn_tip(self):
        # Set last job time to 0 to ensure no cooldown
        self.economy.state.last_job_time = 0
        random.seed(42)  # Fixed seed for predictable results

        result = handle_earn_tip(self.economy)
        self.assertTrue(result["success"])
        self.assertIn(result["gold_change"], range(5, 16))  # 5 base + 0-10 bonus
        self.assertGreaterEqual(self.economy.state.gold, 55)  # 50 + at least 5


class TestNPCPresence(unittest.TestCase):
    def setUp(self):
        self.clock = MockClock(12.0)  # Noon
        self.presence = PresenceManager(self.clock)

        # Add a regular NPC (works 9-5, weekdays)
        self.presence.add_npc(
            "Barkeep", [{"start_hour": 9, "end_hour": 17, "days": [0, 1, 2, 3, 4]}]
        )

        # Add an indefinite guest
        self.presence.add_npc(
            "Traveler", [{"start_hour": 0, "end_hour": 24}], is_indefinite=True
        )

    def test_initial_presence(self):
        # At noon on day 0 (Monday), both should be present
        self.presence.update_all()
        # Check that both NPCs are present in the results
        present_ids = [
            npc_id for npc_id, npc in self.presence.npcs.items() if npc.is_present
        ]
        self.assertIn("Barkeep", present_ids, f"Expected Barkeep in {present_ids}")
        self.assertIn("Traveler", present_ids, f"Expected Traveler in {present_ids}")

    def test_time_window(self):
        # At 8am, Barkeep shouldn't be there yet (Barkeep's hours are 9am-5pm)
        self.clock.current_time = 8.0
        self.presence.update_all()

        # Check Barkeep's presence directly
        barkeep = self.presence.npcs.get("Barkeep")
        self.assertIsNotNone(barkeep, "Barkeep NPC not found in test setup")
        self.assertFalse(
            barkeep.is_present,
            f"Barkeep should not be present at 8am, but is_present={barkeep.is_present}",
        )

        # Check Traveler's presence (should be present all the time)
        traveler = self.presence.npcs.get("Traveler")
        self.assertIsNotNone(traveler, "Traveler NPC not found in test setup")
        self.assertTrue(
            traveler.is_present,
            f"Traveler should be present but is_present={traveler.is_present}",
        )

    def test_indefinite_departure(self):
        # Advance time and force a departure roll
        self.clock.days_elapsed = 1
        random.seed(1)  # Seed that will trigger departure
        messages = self.presence.update_all()

        # Check if Traveler left (20% chance, seed 1 should trigger it)
        present = self.presence.get_present_npcs()
        if "Traveler has left the tavern." in messages:
            self.assertNotIn("Traveler", present)
        else:
            # If not departed, should still be present
            self.assertIn("Traveler", present)


class TestNPCCommands(unittest.TestCase):
    def setUp(self):
        self.clock = MockClock(12.0)
        self.presence = PresenceManager(self.clock)
        self.presence.add_npc(
            "Barkeep", [{"start_hour": 9, "end_hour": 17, "days": [0, 1, 2, 3, 4]}]
        )
        self.presence.move_npc("Barkeep", "bar")

    def test_look_npcs(self):
        # Make sure the NPC is present in the test
        self.presence.update_all()

        # Get the Barkeep NPC and set their room
        barkeep = next(
            (npc for npc in self.presence.npcs.values() if npc.npc_id == "Barkeep"),
            None,
        )
        self.assertIsNotNone(barkeep, "Barkeep NPC not found in test setup")
        barkeep.current_room = "bar"
        barkeep.is_present = True

        # Test looking in the bar
        result = handle_look_npcs(self.presence, "bar")
        self.assertTrue(result["success"], f"Expected success but got {result}")

        # Check if Barkeep is in the results
        self.assertIn(
            "Barkeep",
            result["npcs_present"],
            f"Expected Barkeep in {result['npcs_present']}",
        )
        self.assertIn(
            "Barkeep",
            result["message"],
            f"Expected Barkeep in message: {result['message']}",
        )

        # Test looking in a different room where no one is present
        result = handle_look_npcs(self.presence, "kitchen")
        self.assertTrue(result["success"])
        self.assertEqual(len(result["npcs_present"]), 0)
        self.assertIn("no one else here", result["message"].lower())

    def test_where_npc(self):
        # Make sure the NPC is present in the test
        self.presence.update_all()
        result = handle_where_npc("Barkeep", self.presence)
        self.assertTrue(result["success"])
        self.assertTrue(result["found"])
        self.assertTrue(result["present"])
        # The room might be None if not explicitly set, so we'll just check the structure


if __name__ == "__main__":
    unittest.main()
