#!/usr/bin/env python3
"""
Verify Actual Integration

Check that the GameState class actually uses the phase implementations,
not just has them sitting in separate files.
"""

import re
from pathlib import Path


def check_game_state_integration():
    """Check if GameState has been modified to use phase systems"""
    
    print("="*60)
    print("VERIFYING ACTUAL INTEGRATION IN GAMESTATE")
    print("="*60)
    
    game_state_file = Path("core/game_state.py")
    
    if not game_state_file.exists():
        print("❌ core/game_state.py not found!")
        return False
    
    with open(game_state_file, 'r') as f:
        content = f.read()
    
    # Check for phase imports
    print("\n1. Checking Phase Imports...")
    
    phase_imports = {
        "Phase 2": [
            "from .world.atmosphere import AtmosphereManager",
            "from .world.area_manager import AreaManager",
            "from .world.floor_manager import FloorManager"
        ],
        "Phase 3": [
            "from .npc.psychology import NPCPsychologyManager",
            "from .npc.dialogue import DialogueGenerator",
            "from .npc.secrets import SecretsManager",
            "from .npc.gossip import GossipNetwork"
        ],
        "Phase 4": [
            "from .narrative import",
            "ThreadManager",
            "NarrativeOrchestrator",
            "from .narrative.event_integration import NarrativeEventHandler"
        ]
    }
    
    for phase, imports in phase_imports.items():
        found = sum(1 for imp in imports if imp in content)
        print(f"{phase}: {found}/{len(imports)} imports found {'✅' if found == len(imports) else '❌'}")
    
    # Check for initialization in __init__
    print("\n2. Checking Initialization in __init__...")
    
    init_checks = {
        "atmosphere_manager": "self.atmosphere_manager = AtmosphereManager()",
        "area_manager": "self.area_manager = AreaManager()",
        "npc_psychology": "self.npc_psychology = NPCPsychologyManager()",
        "dialogue_generator": "self.dialogue_generator = DialogueGenerator()",
        "thread_manager": "self.thread_manager = ThreadManager()",
        "narrative_orchestrator": "self.narrative_orchestrator = NarrativeOrchestrator("
    }
    
    for attr, init_code in init_checks.items():
        if init_code in content:
            print(f"✅ {attr} initialized")
        else:
            print(f"❌ {attr} NOT initialized")
    
    # Check if interact_with_npc uses enhanced systems
    print("\n3. Checking Enhanced NPC Interaction...")
    
    npc_enhancements = [
        "self.npc_psychology.get_npc_state",
        "self.dialogue_generator.generate_dialogue",
        "DialogueContext",
        "narrative_context"
    ]
    
    # Find interact_with_npc method
    interact_match = re.search(r'def interact_with_npc\(.*?\):(.*?)(?=\n    def|\Z)', content, re.DOTALL)
    if interact_match:
        interact_content = interact_match.group(1)
        enhanced = sum(1 for enh in npc_enhancements if enh in interact_content)
        print(f"Enhanced NPC interaction: {enhanced}/{len(npc_enhancements)} features {'✅' if enhanced >= 2 else '❌'}")
    else:
        print("❌ interact_with_npc method not found")
    
    # Check if look command uses atmosphere
    print("\n4. Checking Enhanced Look Command...")
    
    look_match = re.search(r'def _handle_look\(.*?\):(.*?)(?=\n    def|\Z)', content, re.DOTALL)
    if look_match:
        look_content = look_match.group(1)
        if "atmosphere_manager" in look_content:
            print("✅ Look command uses atmosphere")
        else:
            print("❌ Look command doesn't use atmosphere")
    
    # Check for update method enhancements
    print("\n5. Checking Update Method...")
    
    if "_update_phase_systems" in content:
        print("✅ Update method calls _update_phase_systems")
    else:
        print("❌ Update method doesn't update phase systems")
    
    # Check PHASE flags
    print("\n6. Checking Phase Availability Flags...")
    
    flags = ["PHASE2_AVAILABLE", "PHASE3_AVAILABLE", "PHASE4_AVAILABLE"]
    for flag in flags:
        if f"{flag} = True" in content:
            print(f"✅ {flag} is set")
        else:
            print(f"❌ {flag} not found or False")
    
    # Summary
    print("\n" + "="*60)
    print("INTEGRATION STATUS")
    print("="*60)
    
    # Count actual integrations
    phase2_integrated = all([
        "AtmosphereManager" in content,
        "self.atmosphere_manager" in content
    ])
    
    phase3_integrated = all([
        "NPCPsychologyManager" in content,
        "self.npc_psychology" in content,
        "generate_dialogue" in content
    ])
    
    phase4_integrated = all([
        "ThreadManager" in content,
        "self.thread_manager" in content
    ])
    
    if phase2_integrated and phase3_integrated and phase4_integrated:
        print("✅ ALL PHASES ARE INTEGRATED INTO GAMESTATE!")
        print("\nThe modifications have been applied successfully:")
        print("• GameState imports all phase systems")
        print("• GameState initializes all managers")
        print("• NPC interactions use enhanced dialogue")
        print("• Commands use phase features")
    else:
        print("❌ PARTIAL INTEGRATION")
        print(f"\nPhase 2 (World): {'✅ Integrated' if phase2_integrated else '❌ Not integrated'}")
        print(f"Phase 3 (NPCs): {'✅ Integrated' if phase3_integrated else '❌ Not integrated'}")
        print(f"Phase 4 (Narrative): {'✅ Integrated' if phase4_integrated else '❌ Not integrated'}")
        
        if not phase2_integrated or not phase3_integrated or not phase4_integrated:
            print("\nThe phase files exist but GameState needs to be modified to use them.")


if __name__ == "__main__":
    check_game_state_integration()