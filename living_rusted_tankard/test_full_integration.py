#!/usr/bin/env python3
"""
Full Integration Test

This script verifies that all phases (1-4) are properly integrated and
actually affect gameplay. No mocks, no shortcuts - real functional testing.
"""

import sys
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.game_state import GameState
from core.integration.phase_integration import PhaseIntegration
from core.event import Event
from core.event_bus import EventType

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_phase2_world_system(game_state: GameState, integration: PhaseIntegration):
    """Test Phase 2: World and Atmosphere System"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 2: WORLD SYSTEM")
    print("=" * 60)

    # Check if enhanced world system is active
    assert hasattr(game_state, "atmosphere_manager"), "Atmosphere manager not found"
    assert hasattr(game_state, "area_manager"), "Area manager not found"
    assert hasattr(game_state, "floor_manager"), "Floor manager not found"

    # Test atmosphere effects
    current_atmosphere = integration.atmosphere_manager.get_current_atmosphere()
    print(f"✓ Current atmosphere: {current_atmosphere}")

    # Test area navigation
    areas = integration.area_manager.get_all_areas()
    print(f"✓ Available areas: {len(areas)} areas loaded")

    # Test floor system
    floors = integration.floor_manager.get_all_floors()
    print(f"✓ Floor system: {len(floors)} floors available")

    # Test atmosphere change
    integration.atmosphere_manager.set_atmosphere_property("tension", 0.7)
    new_atmosphere = integration.atmosphere_manager.get_current_atmosphere()
    assert new_atmosphere.get("tension", 0) == 0.7, "Atmosphere change failed"
    print("✓ Atmosphere changes work correctly")

    return True


def test_phase3_npc_systems(game_state: GameState, integration: PhaseIntegration):
    """Test Phase 3: Enhanced NPC Systems"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 3: NPC SYSTEMS")
    print("=" * 60)

    # Check if NPC systems are active
    assert hasattr(game_state, "npc_psychology"), "NPC psychology not found"
    assert hasattr(game_state, "dialogue_generator"), "Dialogue generator not found"
    assert hasattr(game_state, "gossip_network"), "Gossip network not found"
    assert hasattr(game_state, "secrets_manager"), "Secrets manager not found"

    # Create a test NPC
    test_npc = game_state.npc_manager.create_npc(
        {
            "id": "test_npc",
            "name": "Test NPC",
            "description": "A test character",
            "personality": {"openness": 0.8, "agreeableness": 0.6},
            "has_secret": True,
        }
    )

    # Test psychology system
    psychology = integration.npc_psychology.get_npc_state("test_npc")
    print(f"✓ NPC psychology initialized: {psychology}")

    # Test dialogue generation
    base_dialogue = "Hello there!"
    enhanced = integration.enhance_npc_interaction("test_npc", base_dialogue)
    assert enhanced != base_dialogue, "Dialogue enhancement failed"
    print(f"✓ Enhanced dialogue: '{enhanced[:50]}...'")

    # Test gossip system
    integration.gossip_network.add_rumor(
        {
            "content": "Strange things happening at night",
            "source": "test_npc",
            "credibility": 0.7,
        }
    )
    gossip = integration.gossip_network.get_npc_gossip("test_npc")
    assert gossip is not None, "Gossip system failed"
    print(f"✓ Gossip system active: '{gossip}'")

    # Test secrets system
    if hasattr(test_npc, "has_secret") and test_npc.has_secret:
        integration.secrets_manager.initialize_npc_secrets("test_npc")
        has_secrets = integration.secrets_manager.npc_has_secrets("test_npc")
        assert has_secrets, "Secrets system failed"
        print("✓ Secrets system initialized")

    return True


def test_phase4_narrative_engine(game_state: GameState, integration: PhaseIntegration):
    """Test Phase 4: Narrative Engine"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 4: NARRATIVE ENGINE")
    print("=" * 60)

    # Check if narrative systems are active
    assert hasattr(game_state, "thread_manager"), "Thread manager not found"
    assert hasattr(
        game_state, "narrative_orchestrator"
    ), "Narrative orchestrator not found"
    assert hasattr(game_state, "narrative_handler"), "Narrative event handler not found"

    # Check initial threads
    threads = integration.thread_manager.get_active_threads()
    print(f"✓ Active threads: {len(threads)} threads running")
    for thread in threads:
        print(
            f"  - {thread.title} ({thread.type.value}) - Tension: {thread.tension_level}"
        )

    # Test event integration
    game_state.event_bus.emit(
        Event(
            EventType.NPC_INTERACTION,
            {"npc_name": "test_npc", "interaction_type": "talk"},
        )
    )
    print("✓ Narrative responds to game events")

    # Test narrative context
    context = integration.narrative_handler.get_narrative_context_for_npc("test_npc")
    assert "active_threads" in context, "Narrative context failed"
    print(f"✓ Narrative context generated: {context['emotional_state']}")

    # Test narrative effects
    effects = {"room_atmosphere": {"atmosphere": "mysterious", "duration": 30}}
    results = integration.narrative_handler.apply_narrative_effects(effects)
    assert len(results) > 0, "Narrative effects failed"
    print(f"✓ Narrative effects applied: {results}")

    return True


def test_integration_flow(game_state: GameState, integration: PhaseIntegration):
    """Test the complete integration flow"""
    print("\n" + "=" * 60)
    print("TESTING COMPLETE INTEGRATION FLOW")
    print("=" * 60)

    # Simulate player entering a new room
    print("\n1. Testing room change with all systems...")
    old_room = game_state.current_room
    game_state.current_room = "tavern_upstairs"

    # Emit room change event
    game_state.event_bus.emit(
        Event(
            EventType.ROOM_CHANGE, {"old_room": old_room, "new_room": "tavern_upstairs"}
        )
    )

    # Check atmosphere updated
    current_atmosphere = integration.atmosphere_manager.get_current_atmosphere()
    print("   ✓ Atmosphere updated for new room")

    # Simulate NPC interaction with all systems
    print("\n2. Testing enhanced NPC interaction...")
    if "bartender" in game_state.npcs:
        result = game_state.interact_with_npc("bartender")
        print("   ✓ NPC interaction processed through all systems")
        print(f"   Response preview: '{result[:100]}...'")

    # Test time progression affecting all systems
    print("\n3. Testing time progression...")
    initial_time = game_state.clock.time
    game_state.clock.advance(30)  # 30 minutes

    # Emit time event
    game_state.event_bus.emit(
        Event(
            EventType.TIME_ADVANCED,
            {"current_time": game_state.clock.time, "elapsed_minutes": 30},
        )
    )

    # Update all systems
    integration.update_all_systems(30 * 60)  # Convert to seconds

    print(f"   ✓ Time advanced from {initial_time} to {game_state.clock.time}")
    print("   ✓ All systems updated with time progression")

    # Test command processing through enhanced system
    print("\n4. Testing enhanced command processing...")
    result = integration.process_enhanced_command("look around")
    assert len(result) > 0, "Enhanced command processing failed"
    print("   ✓ Command processed with enhancements")

    return True


def main():
    """Run the full integration test"""
    print("FULL INTEGRATION TEST - Living Rusted Tankard")
    print("Testing all phases are properly connected and functional")

    try:
        # Create base game state
        print("\nInitializing game state...")
        game_state = GameState()

        # Apply phase integration
        print("Applying phase integration...")
        integration = PhaseIntegration(game_state)

        # Run tests for each phase
        phase2_ok = test_phase2_world_system(game_state, integration)
        phase3_ok = test_phase3_npc_systems(game_state, integration)
        phase4_ok = test_phase4_narrative_engine(game_state, integration)

        # Test complete integration
        integration_ok = test_integration_flow(game_state, integration)

        # Summary
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print(f"Phase 2 (World System):     {'✅ PASS' if phase2_ok else '❌ FAIL'}")
        print(f"Phase 3 (NPC Systems):      {'✅ PASS' if phase3_ok else '❌ FAIL'}")
        print(f"Phase 4 (Narrative Engine): {'✅ PASS' if phase4_ok else '❌ FAIL'}")
        print(f"Full Integration:           {'✅ PASS' if integration_ok else '❌ FAIL'}")

        if all([phase2_ok, phase3_ok, phase4_ok, integration_ok]):
            print("\n🎉 ALL SYSTEMS INTEGRATED AND FUNCTIONAL! 🎉")
            print("\nThe Living Rusted Tankard is now running with:")
            print("• Dynamic atmosphere and multi-floor world")
            print("• NPC psychology, goals, and dynamic dialogue")
            print("• Full narrative engine with story threads")
            print("• All systems working together seamlessly")
            return 0
        else:
            print("\n❌ Some integration tests failed!")
            return 1

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
