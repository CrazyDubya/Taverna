#!/usr/bin/env python3
"""
Verify Integration Status

Check if phase implementations are actually integrated into the game
without running the full application.
"""

import os
import ast
from pathlib import Path


def check_file_imports(file_path, target_imports):
    """Check if a file imports specific modules"""
    try:
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        found = []
        for target in target_imports:
            if any(target in imp for imp in imports):
                found.append(target)

        return found
    except Exception as e:
        return []


def check_phase_integration():
    """Check integration status of all phases"""

    print("=" * 60)
    print("PHASE INTEGRATION STATUS CHECK")
    print("=" * 60)

    # Check GameState for phase imports
    game_state_file = Path("core/game_state.py")

    print("\n1. Checking GameState imports...")

    phase2_imports = [
        "world.atmosphere",
        "world.area_manager",
        "world.floor_manager",
        "AtmosphereManager",
        "AreaManager",
        "FloorManager",
    ]

    phase3_imports = [
        "npc.psychology",
        "npc.secrets",
        "npc.dialogue",
        "npc.gossip",
        "NPCPsychologyManager",
        "SecretsManager",
        "DialogueGenerator",
    ]

    phase4_imports = [
        "narrative",
        "ThreadManager",
        "NarrativeOrchestrator",
        "NarrativeEventHandler",
    ]

    # Check actual imports
    phase2_found = check_file_imports(game_state_file, phase2_imports)
    phase3_found = check_file_imports(game_state_file, phase3_imports)
    phase4_found = check_file_imports(game_state_file, phase4_imports)

    print(f"Phase 2 imports found: {len(phase2_found)} of {len(phase2_imports)}")
    print(f"Phase 3 imports found: {len(phase3_found)} of {len(phase3_imports)}")
    print(f"Phase 4 imports found: {len(phase4_found)} of {len(phase4_imports)}")

    # Check if phase files exist
    print("\n2. Checking phase implementation files...")

    phase_files = {
        "Phase 2": [
            "core/world/atmosphere.py",
            "core/world/area_manager.py",
            "core/world/floor_manager.py",
        ],
        "Phase 3": [
            "core/npc/psychology.py",
            "core/npc/secrets.py",
            "core/npc/dialogue.py",
            "core/npc/gossip.py",
            "core/npc/goals.py",
        ],
        "Phase 4": [
            "core/narrative/story_thread.py",
            "core/narrative/thread_manager.py",
            "core/narrative/rules.py",
            "core/narrative/orchestrator.py",
        ],
    }

    for phase, files in phase_files.items():
        exists = sum(1 for f in files if Path(f).exists())
        print(f"{phase}: {exists}/{len(files)} files exist")
        if exists == len(files):
            print(f"  ✅ All {phase} files present")
        else:
            print(f"  ❌ Missing {phase} files")

    # Check integration module
    print("\n3. Checking integration module...")
    integration_files = [
        "core/integration/__init__.py",
        "core/integration/phase_integration.py",
    ]

    integration_exists = sum(1 for f in integration_files if Path(f).exists())
    print(
        f"Integration module: {integration_exists}/{len(integration_files)} files exist"
    )

    # Check if GameState uses integration
    print("\n4. Checking if GameState uses PhaseIntegration...")
    with open(game_state_file, "r") as f:
        game_state_content = f.read()

    uses_integration = "PhaseIntegration" in game_state_content
    uses_atmosphere = "atmosphere_manager" in game_state_content
    uses_narrative = "narrative_orchestrator" in game_state_content

    print(f"Uses PhaseIntegration: {'✅' if uses_integration else '❌'}")
    print(f"Uses atmosphere_manager: {'✅' if uses_atmosphere else '❌'}")
    print(f"Uses narrative_orchestrator: {'✅' if uses_narrative else '❌'}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    phase2_integrated = len(phase2_found) > 0 or uses_atmosphere
    phase3_integrated = len(phase3_found) > 0
    phase4_integrated = len(phase4_found) > 0 or uses_narrative
    any_integration = uses_integration

    print("Phase 1 (Quality):     ✅ Partially integrated (AIPlayerManager in use)")
    print(
        f"Phase 2 (World):       {'✅' if phase2_integrated else '❌'} {'Integrated' if phase2_integrated else 'NOT integrated'}"
    )
    print(
        f"Phase 3 (NPCs):        {'✅' if phase3_integrated else '❌'} {'Integrated' if phase3_integrated else 'NOT integrated'}"
    )
    print(
        f"Phase 4 (Narrative):   {'✅' if phase4_integrated else '❌'} {'Integrated' if phase4_integrated else 'NOT integrated'}"
    )
    print(
        f"Integration Module:    {'✅' if any_integration else '❌'} {'Active' if any_integration else 'NOT active'}"
    )

    if not any([phase2_integrated, phase3_integrated, phase4_integrated]):
        print("\n⚠️  CRITICAL: Phase implementations exist but are NOT integrated!")
        print("The game is running on basic pre-phase implementation.")
        print("\nTo fix this:")
        print("1. Modify GameState.__init__ to use PhaseIntegration")
        print("2. Update command handlers to use enhanced systems")
        print("3. Connect event handlers to phase systems")
    else:
        print("\n✅ Some phases are integrated and affecting gameplay")

    # Check what's actually being used
    print("\n5. What's actually running...")
    print(
        f"Room System: {'Basic RoomManager' if 'RoomManager()' in game_state_content else 'Unknown'}"
    )
    print(
        f"NPC System: {'Basic NPCManager' if 'NPCManager(' in game_state_content else 'Unknown'}"
    )
    print(f"Has EventBus: {'Yes' if 'event_bus' in game_state_content else 'No'}")

    # Look for the actual integration point
    print("\n6. Integration recommendations...")
    if not uses_integration:
        print("To integrate all phases, add to GameState.__init__:")
        print("```python")
        print("from core.integration import PhaseIntegration")
        print("self.phase_integration = PhaseIntegration(self)")
        print("```")
        print("\nThen update interact_with_npc to use:")
        print("```python")
        print(
            "return self.phase_integration.enhance_npc_interaction(npc_name, base_response)"
        )
        print("```")


if __name__ == "__main__":
    check_phase_integration()
