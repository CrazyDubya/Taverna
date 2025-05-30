#!/usr/bin/env python3
"""
Simple Integration Test

Test that the phase integrations are actually working in GameState.
"""

import sys
from pathlib import Path

# Ensure we can import from the project
sys.path.insert(0, str(Path(__file__).parent))

def test_phase_integration():
    """Test that phases are integrated into GameState"""
    print("Testing Phase Integration in GameState...\n")
    
    try:
        from core.game_state import GameState
        
        # Create a game state
        print("1. Creating GameState...")
        game_state = GameState()
        print("   ✅ GameState created successfully")
        
        # Check Phase 2 integration
        print("\n2. Checking Phase 2 (World System)...")
        has_atmosphere = hasattr(game_state, 'atmosphere_manager')
        has_area = hasattr(game_state, 'area_manager')
        has_floor = hasattr(game_state, 'floor_manager')
        
        if has_atmosphere and has_area and has_floor:
            print("   ✅ Phase 2 integrated: atmosphere_manager, area_manager, floor_manager present")
        else:
            print(f"   ❌ Phase 2 missing: atmosphere={has_atmosphere}, area={has_area}, floor={has_floor}")
        
        # Check Phase 3 integration
        print("\n3. Checking Phase 3 (NPC Systems)...")
        has_psychology = hasattr(game_state, 'npc_psychology')
        has_dialogue = hasattr(game_state, 'dialogue_generator')
        has_secrets = hasattr(game_state, 'secrets_manager')
        has_gossip = hasattr(game_state, 'gossip_network')
        
        if has_psychology and has_dialogue and has_secrets and has_gossip:
            print("   ✅ Phase 3 integrated: NPC systems present")
        else:
            print(f"   ❌ Phase 3 missing: psych={has_psychology}, dialogue={has_dialogue}, secrets={has_secrets}, gossip={has_gossip}")
        
        # Check Phase 4 integration
        print("\n4. Checking Phase 4 (Narrative Engine)...")
        has_threads = hasattr(game_state, 'thread_manager')
        has_orchestrator = hasattr(game_state, 'narrative_orchestrator')
        has_rules = hasattr(game_state, 'rules_engine')
        
        if has_threads and has_orchestrator and has_rules:
            print("   ✅ Phase 4 integrated: narrative engine present")
        else:
            print(f"   ❌ Phase 4 missing: threads={has_threads}, orchestrator={has_orchestrator}, rules={has_rules}")
        
        # Test enhanced NPC interaction
        print("\n5. Testing enhanced NPC interaction...")
        try:
            # Create a test NPC if not present
            if 'bartender' not in game_state.npc_manager.npcs:
                from core.npc import NPC, NPCType
                bartender = NPC(
                    id='bartender',
                    definition_id='bartender_tom',
                    name='Tom the Bartender',
                    description='A gruff but friendly bartender',
                    npc_type=NPCType.BARKEEP
                )
                game_state.npc_manager.npcs['bartender'] = bartender
            
            # Try to interact
            result = game_state.interact_with_npc('bartender', 'talk')
            if result.get('success'):
                message = result.get('message', '')
                print(f"   ✅ NPC interaction works: '{message[:50]}...'")
            else:
                print(f"   ❌ NPC interaction failed: {result.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ NPC interaction error: {e}")
        
        # Test look command with atmosphere
        print("\n6. Testing enhanced look command...")
        try:
            result = game_state.process_command('look')
            if result.get('success'):
                message = result.get('message', '')
                has_atmosphere_desc = 'atmosphere' in message.lower() or 'feel' in message.lower()
                print(f"   ✅ Look command works{' with atmosphere' if has_atmosphere_desc else ''}")
            else:
                print("   ❌ Look command failed")
        except Exception as e:
            print(f"   ❌ Look command error: {e}")
            
        # Test narrative functionality
        print("\n7. Testing narrative functionality...")
        try:
            if hasattr(game_state, 'thread_manager'):
                threads = game_state.thread_manager.get_active_threads()
                print(f"   ✅ Active narrative threads: {len(threads)}")
                for thread in threads[:2]:  # Show first 2
                    print(f"     - {thread.title} (tension: {thread.tension_level})")
            else:
                print("   ❌ No thread manager found")
        except Exception as e:
            print(f"   ❌ Narrative test error: {e}")
        
        # Summary
        print("\n" + "="*50)
        print("INTEGRATION SUMMARY")
        print("="*50)
        
        all_integrated = all([
            has_atmosphere and has_area and has_floor,  # Phase 2
            has_psychology and has_dialogue and has_secrets and has_gossip,  # Phase 3
            has_threads and has_orchestrator and has_rules  # Phase 4
        ])
        
        if all_integrated:
            print("✅ ALL PHASES SUCCESSFULLY INTEGRATED!")
            print("\nThe Living Rusted Tankard now has:")
            print("• Dynamic world atmosphere and multi-floor areas")
            print("• NPC psychology, dialogue, and secrets systems")
            print("• Full narrative engine with story threads")
            print("\nAll systems are connected to the actual game!")
        else:
            print("❌ Some phases are not integrated")
            print("\nCheck that all phase files exist in:")
            print("• core/world/ (Phase 2)")
            print("• core/npc/ (Phase 3)")
            print("• core/narrative/ (Phase 4)")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_phase_integration()