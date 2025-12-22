"""Integration tests for core game systems working together."""
import pytest
import asyncio
from unittest.mock import Mock, patch

from tests.fixtures import (
    clean_game_state,
    populated_game_state,
    new_player,
    wealthy_player,
    isolated_db_session,
    mock_economy,
)
from tests.utils.assertion_helpers import (
    assert_game_state_valid,
    assert_player_valid,
    assert_economy_transaction_valid,
)

from core.game_state import GameState
from core.player import Player
from core.npc import NPC, NPCType
from core.economy import Economy
from core.bounties import BountySystem
from core.event_bus import EventBus


class TestGameStateManagement:
    """Test game state management across systems."""

    def test_game_state_serialization_deserialization(
        self, populated_game_state, isolated_db_session
    ):
        """Test game state can be saved and loaded correctly."""
        game_state = GameState()

        # Set initial state
        game_state.update_from_dict(populated_game_state)

        # Serialize state
        serialized = game_state.serialize()
        assert isinstance(serialized, (str, dict))

        # Create new game state and deserialize
        new_game_state = GameState()
        new_game_state.deserialize(serialized)

        # Verify state is preserved
        assert_game_state_valid(new_game_state.to_dict())
        assert new_game_state.player.name == populated_game_state["player"]["name"]
        assert new_game_state.player.gold == populated_game_state["player"]["gold"]

    def test_game_state_npc_integration(self, clean_game_state):
        """Test game state integration with NPC system."""
        game_state = GameState()
        game_state.update_from_dict(clean_game_state)

        # Create NPCs
        barkeeper = NPC(
            id="barkeeper_bob",
            name="Barkeeper Bob",
            description="A friendly barkeeper",
            npc_type=NPCType.BARKEEP,
            current_room="tavern"
        )
        guard = NPC(
            id="town_guard",
            name="Town Guard",
            description="A stern town guard",
            npc_type=NPCType.GUARD,
            current_room="entrance"
        )

        # Add NPCs to game state
        game_state.add_npc(barkeeper)
        game_state.add_npc(guard)

        # Verify NPCs are in game state
        npcs = game_state.get_npcs()
        assert len(npcs) == 2
        assert any(npc.name == "Barkeeper Bob" for npc in npcs)
        assert any(npc.name == "Town Guard" for npc in npcs)

        # Test NPC location filtering
        tavern_npcs = game_state.get_npcs_in_location("tavern")
        assert len(tavern_npcs) == 1
        assert tavern_npcs[0].name == "Barkeeper Bob"

    def test_game_state_player_progression(self, new_player):
        """Test game state updates with player progression."""
        game_state = GameState()
        game_state.player = new_player

        initial_gold = new_player.gold
        initial_level = new_player.level

        # Simulate player progression
        game_state.player.add_gold(100)
        game_state.player.add_experience(250)

        # Verify changes are reflected in game state
        assert game_state.player.gold == initial_gold + 100
        assert game_state.player.level > initial_level  # Should level up

        # Verify game state validity
        assert_game_state_valid(game_state.to_dict())

    def test_game_state_time_progression(self, clean_game_state):
        """Test game state time management."""
        game_state = GameState()
        game_state.update_from_dict(clean_game_state)

        initial_time = game_state.get_game_time()

        # Advance time
        game_state.advance_time(hours=2)

        new_time = game_state.get_game_time()
        assert new_time["hour"] == (initial_time["hour"] + 2) % 24

        # Test day advancement
        game_state.advance_time(hours=25)  # More than a day
        final_time = game_state.get_game_time()
        assert final_time["day"] > initial_time["day"]


class TestEconomyIntegration:
    """Test economy system integration with other systems."""

    def test_economy_player_transactions(self, new_player, mock_economy):
        """Test economy transactions affecting player state."""
        economy = Economy()
        player = new_player

        initial_gold = player.gold

        # Test purchase transaction
        transaction = {"type": "purchase", "item": "ale", "price": 10, "quantity": 2}

        result = economy.process_transaction(player, transaction)

        assert result is True
        assert player.gold == initial_gold - 20  # 10 * 2

        # Verify transaction validity
        assert_economy_transaction_valid(
            {"type": "purchase", "amount": 20, "participant": player.name}
        )

    def test_economy_market_price_updates(self, mock_economy):
        """Test market price updates affecting the economy."""
        economy = Economy()

        # Set initial prices
        economy.set_item_price("bread", 5)
        economy.set_item_price("ale", 8)

        # Simulate market event
        market_event = {
            "type": "supply_shortage",
            "affected_items": ["bread"],
            "price_multiplier": 1.5,
        }

        economy.apply_market_event(market_event)

        # Verify price changes
        new_bread_price = economy.get_item_price("bread")
        ale_price = economy.get_item_price("ale")

        assert new_bread_price == 7.5  # 5 * 1.5
        assert ale_price == 8  # Unchanged

    def test_economy_job_system_integration(self, new_player, mock_economy):
        """Test economy integration with job/quest system."""
        economy = Economy()
        player = new_player

        # Create a job
        job = {
            "id": "delivery_job_1",
            "type": "delivery",
            "payment": 50,
            "requirements": ["item_delivery"],
            "status": "available",
        }

        # Player accepts job
        economy.assign_job(player, job)

        # Player completes job
        completion_result = economy.complete_job(player, job["id"])

        assert completion_result is True
        assert player.gold >= 50  # Should have received payment

        # Verify transaction was recorded
        transactions = economy.get_player_transactions(player.name)
        assert len(transactions) > 0
        assert any(t["type"] == "job_payment" for t in transactions)


class TestNPCSystemIntegration:
    """Test NPC system integration with other game systems."""

    def test_npc_schedule_integration(self, clean_game_state):
        """Test NPC schedule system with game time."""
        game_state = GameState()
        game_state.update_from_dict(clean_game_state)

        # Create NPC with schedule
        npc = NPC(
            id="shopkeeper",
            name="Shopkeeper",
            description="A businesslike shopkeeper",
            npc_type=NPCType.MERCHANT,
            current_room="shop"
        )
        npc.set_schedule(
            {
                "morning": {"location": "shop", "activity": "open_shop"},
                "afternoon": {"location": "shop", "activity": "serve_customers"},
                "evening": {"location": "home", "activity": "rest"},
            }
        )

        # Test different times of day
        game_state.set_game_time(hour=9)  # Morning
        npc.update_for_time(game_state.get_game_time())
        assert npc.current_activity == "open_shop"
        assert npc.location == "shop"

        game_state.set_game_time(hour=20)  # Evening
        npc.update_for_time(game_state.get_game_time())
        assert npc.current_activity == "rest"
        assert npc.location == "home"

    def test_npc_relationship_system(self, new_player):
        """Test NPC relationship system with player interactions."""
        npc = NPC(
            id="village_elder",
            name="Village Elder",
            description="A wise village elder",
            npc_type=NPCType.PATRON,
            current_room="village_center"
        )
        player = new_player

        # Initial relationship
        initial_relationship = npc.get_relationship(player.name)
        assert initial_relationship >= 0  # Neutral or positive

        # Positive interaction
        npc.update_relationship(player.name, 10)
        new_relationship = npc.get_relationship(player.name)
        assert new_relationship > initial_relationship

        # Negative interaction
        npc.update_relationship(player.name, -5)
        final_relationship = npc.get_relationship(player.name)
        assert final_relationship < new_relationship

    @pytest.mark.asyncio
    async def test_npc_conversation_system(self, clean_game_state):
        """Test NPC conversation system integration."""
        npc = NPC(
            name="Mysterious Stranger", personality="cryptic", location="corner_table"
        )

        # Mock conversation history
        conversation_history = [
            {"speaker": "player", "message": "Who are you?"},
            {"speaker": "npc", "message": "I am but a shadow in the night."},
        ]

        npc.conversation_history = conversation_history

        # Test conversation context
        context = npc.get_conversation_context()
        assert len(context) == 2
        assert context[0]["speaker"] == "player"
        assert context[1]["speaker"] == "npc"

        # Add new message
        npc.add_conversation_message("player", "What do you want?")

        updated_context = npc.get_conversation_context()
        assert len(updated_context) == 3


class TestBountySystemIntegration:
    """Test bounty/quest system integration."""

    def test_bounty_system_player_integration(self, new_player):
        """Test bounty system with player progression."""
        bounty_system = BountySystem()
        player = new_player

        # Create a bounty
        bounty = {
            "id": "goblin_hunt",
            "title": "Goblin Problem",
            "description": "Clear out the goblin cave.",
            "difficulty": "easy",
            "reward": 75,
            "requirements": ["combat"],
        }

        # Player accepts bounty
        result = bounty_system.assign_bounty(player, bounty)
        assert result is True

        # Check player has active bounty
        active_bounties = bounty_system.get_player_bounties(player.name)
        assert len(active_bounties) == 1
        assert active_bounties[0]["id"] == "goblin_hunt"

        # Player completes bounty
        completion_result = bounty_system.complete_bounty(player, "goblin_hunt")
        assert completion_result is True

        # Verify rewards
        assert player.gold >= 75  # Should have received reward
        assert player.experience > 0  # Should have gained experience

    def test_bounty_system_difficulty_scaling(self, new_player, wealthy_player):
        """Test bounty difficulty scaling based on player level."""
        bounty_system = BountySystem()

        # Generate bounties for different player levels
        low_level_bounties = bounty_system.get_available_bounties(new_player)
        high_level_bounties = bounty_system.get_available_bounties(wealthy_player)

        # Higher level player should get harder bounties
        if low_level_bounties and high_level_bounties:
            avg_low_reward = sum(b.get("reward", 0) for b in low_level_bounties) / len(
                low_level_bounties
            )
            avg_high_reward = sum(
                b.get("reward", 0) for b in high_level_bounties
            ) / len(high_level_bounties)

            # High level bounties should generally offer higher rewards
            assert avg_high_reward >= avg_low_reward


class TestEventBusIntegration:
    """Test event bus integration across systems."""

    def test_event_bus_player_actions(self, new_player):
        """Test event bus with player action events."""
        event_bus = EventBus()
        player = new_player

        events_received = []

        def event_handler(event_data):
            events_received.append(event_data)

        # Subscribe to player events
        event_bus.subscribe("player_action", event_handler)

        # Trigger player action
        event_bus.publish(
            "player_action",
            {"player": player.name, "action": "buy_item", "item": "sword", "cost": 50},
        )

        # Verify event was received
        assert len(events_received) == 1
        assert events_received[0]["player"] == player.name
        assert events_received[0]["action"] == "buy_item"

    def test_event_bus_cross_system_communication(self, clean_game_state):
        """Test event bus facilitating cross-system communication."""
        event_bus = EventBus()

        economy_events = []
        npc_events = []

        def economy_handler(event_data):
            economy_events.append(event_data)

        def npc_handler(event_data):
            npc_events.append(event_data)

        # Subscribe different systems to relevant events
        event_bus.subscribe("economy_change", economy_handler)
        event_bus.subscribe("npc_interaction", npc_handler)

        # Trigger cross-system event
        event_bus.publish(
            "economy_change",
            {
                "type": "market_crash",
                "affected_items": ["luxury_goods"],
                "price_multiplier": 0.5,
            },
        )

        # This should trigger NPC reactions
        event_bus.publish(
            "npc_interaction",
            {
                "npc": "Merchant",
                "type": "concern",
                "message": "The market crash affects my business!",
            },
        )

        # Verify both systems received relevant events
        assert len(economy_events) == 1
        assert len(npc_events) == 1
        assert economy_events[0]["type"] == "market_crash"
        assert npc_events[0]["npc"] == "Merchant"


class TestFullGameSessionIntegration:
    """Test complete game session scenarios."""

    @pytest.mark.asyncio
    async def test_complete_game_session_flow(self, isolated_db_session):
        """Test a complete game session from start to finish."""
        # Initialize game systems
        game_state = GameState()
        economy = Economy()
        bounty_system = BountySystem()
        event_bus = EventBus()

        # Create player
        player = Player(name="IntegrationTestPlayer")
        game_state.player = player

        # Create initial game world
        barkeeper = NPC(
            id="barkeeper",
            name="Barkeeper",
            description="A friendly barkeeper",
            npc_type=NPCType.BARKEEP,
            current_room="tavern"
        )
        game_state.add_npc(barkeeper)

        # Session start - player enters tavern
        game_state.player.location = "tavern"
        event_bus.publish(
            "player_enter_location", {"player": player.name, "location": "tavern"}
        )

        # Player interacts with barkeeper
        interaction_result = await barkeeper.interact(player, "Hello!")
        assert interaction_result is not None

        # Player buys drink
        drink_transaction = {
            "type": "purchase",
            "item": "ale",
            "price": 5,
            "quantity": 1,
        }

        initial_gold = player.gold
        economy.process_transaction(player, drink_transaction)
        assert player.gold == initial_gold - 5

        # Player checks available bounties
        available_bounties = bounty_system.get_available_bounties(player)
        if available_bounties:
            # Accept a bounty
            bounty = available_bounties[0]
            bounty_system.assign_bounty(player, bounty)

            # Complete bounty (simplified)
            bounty_system.complete_bounty(player, bounty["id"])

            # Verify player gained experience and gold
            assert player.experience > 0
            assert player.gold > initial_gold - 5  # Should have earned more than spent

        # Save game state
        serialized_state = game_state.serialize()

        # Load game state (simulate session restore)
        new_game_state = GameState()
        new_game_state.deserialize(serialized_state)

        # Verify session integrity
        assert_game_state_valid(new_game_state.to_dict())
        assert new_game_state.player.name == player.name
        assert len(new_game_state.get_npcs()) == 1

    def test_concurrent_player_sessions(self, isolated_db_session):
        """Test multiple concurrent player sessions."""
        # Create multiple game states for different players
        sessions = {}

        for i in range(3):
            game_state = GameState()
            player = Player(name=f"Player_{i}")
            player.gold = 100 + (i * 50)  # Different starting gold

            game_state.player = player
            sessions[f"session_{i}"] = game_state

        # Verify sessions are isolated
        for session_id, game_state in sessions.items():
            assert game_state.player.name.endswith(session_id.split("_")[1])

            # Modify one session
            if session_id == "session_0":
                game_state.player.add_gold(200)

        # Verify other sessions are unaffected
        assert sessions["session_0"].player.gold == 300  # 100 + 200
        assert sessions["session_1"].player.gold == 150  # Original
        assert sessions["session_2"].player.gold == 200  # Original

        # Verify all sessions maintain validity
        for game_state in sessions.values():
            assert_game_state_valid(game_state.to_dict())
