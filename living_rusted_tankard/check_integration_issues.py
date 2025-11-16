#!/usr/bin/env python3
"""
Check for Integration Issues

Identify specific problems that would prevent the integrated systems from working.
"""

import ast
import sys
from pathlib import Path


def check_method_calls():
    """Check if GameState calls methods that exist in phase systems"""
    print("=" * 60)
    print("CHECKING FOR INTEGRATION ISSUES")
    print("=" * 60)

    issues = []

    # Read GameState
    game_state_file = Path("core/game_state.py")
    with open(game_state_file, "r") as f:
        game_state_content = f.read()

    print("\n1. Checking method calls vs implementations...")

    # Check if called methods exist in phase files
    method_checks = [
        (
            "self.npc_psychology.initialize_npc",
            "core/npc/psychology.py",
            "initialize_npc",
        ),
        (
            "self.npc_psychology.get_npc_state",
            "core/npc/psychology.py",
            "get_npc_state",
        ),
        (
            "self.dialogue_generator.generate_dialogue",
            "core/npc/dialogue.py",
            "generate_dialogue",
        ),
        (
            "self.atmosphere_manager.get_current_atmosphere",
            "core/world/atmosphere.py",
            "get_current_atmosphere",
        ),
        (
            "self.thread_manager.add_thread",
            "core/narrative/thread_manager.py",
            "add_thread",
        ),
        (
            "self.thread_manager.get_active_threads",
            "core/narrative/thread_manager.py",
            "get_active_threads",
        ),
        (
            "self.area_manager.get_area_for_room",
            "core/world/area_manager.py",
            "get_area_for_room",
        ),
    ]

    for call, file_path, method_name in method_checks:
        if call in game_state_content:
            file_obj = Path(file_path)
            if file_obj.exists():
                with open(file_obj, "r") as f:
                    content = f.read()
                if f"def {method_name}" in content:
                    print(f"✅ {call} -> method exists")
                else:
                    print(f"❌ {call} -> method MISSING")
                    issues.append(f"Method {method_name} missing in {file_path}")
            else:
                print(f"❌ {call} -> file MISSING: {file_path}")
                issues.append(f"File missing: {file_path}")
        else:
            print(f"ℹ️  {call} -> not called in GameState")

    print("\n2. Checking import paths...")

    # Check if import paths are correct
    import_checks = [
        ("from .world.atmosphere import AtmosphereManager", "core/world/atmosphere.py"),
        ("from .npc.psychology import NPCPsychologyManager", "core/npc/psychology.py"),
        ("from .narrative import ThreadManager", "core/narrative/thread_manager.py"),
    ]

    for import_line, file_path in import_checks:
        if import_line in game_state_content:
            if Path(file_path).exists():
                print(f"✅ {import_line} -> file exists")
            else:
                print(f"❌ {import_line} -> file MISSING")
                issues.append(f"Import file missing: {file_path}")

    print("\n3. Checking for circular imports...")

    # Simple check for potential circular imports
    if (
        "from core.game_state import"
        in Path("core/narrative/event_integration.py").read_text()
    ):
        issues.append("Potential circular import: event_integration imports game_state")
        print("❌ Potential circular import detected")
    else:
        print("✅ No obvious circular imports")

    print("\n4. Checking DialogueContext usage...")

    # Check if DialogueContext is used correctly
    if "DialogueContext(" in game_state_content:
        # Check if all required parameters are provided
        dialogue_context_pattern = r"DialogueContext\((.*?)\)"
        import re

        matches = re.findall(dialogue_context_pattern, game_state_content, re.DOTALL)
        if matches:
            context_args = matches[0]
            required_args = ["npc_name", "player_name", "location"]
            missing_args = [arg for arg in required_args if arg not in context_args]
            if missing_args:
                print(f"❌ DialogueContext missing args: {missing_args}")
                issues.append(
                    f"DialogueContext missing required arguments: {missing_args}"
                )
            else:
                print("✅ DialogueContext properly constructed")
        else:
            print("❌ DialogueContext pattern not found")

    print("\n5. Checking EventBus integration...")

    # Check if EventBus is properly set up
    if "self.event_bus = EventBus()" in game_state_content:
        print("✅ EventBus initialized")
    else:
        print("❌ EventBus not initialized")
        issues.append("EventBus not properly initialized")

    if "NarrativeEventHandler(self, self.narrative_orchestrator)" in game_state_content:
        print("✅ NarrativeEventHandler created")
    else:
        print("❌ NarrativeEventHandler not created")
        issues.append("NarrativeEventHandler not properly created")

    print("\n6. Checking for missing __init__.py files...")

    # Check for missing __init__.py files
    required_inits = [
        "core/world/__init__.py",
        "core/npc/__init__.py",
        "core/narrative/__init__.py",
    ]

    for init_file in required_inits:
        if Path(init_file).exists():
            print(f"✅ {init_file} exists")
        else:
            print(f"❌ {init_file} MISSING")
            issues.append(f"Missing {init_file}")

    print("\n" + "=" * 60)
    print("ISSUES SUMMARY")
    print("=" * 60)

    if issues:
        print("❌ INTEGRATION ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")

        print("\nThese issues need to be fixed for the integration to work properly.")
        return False
    else:
        print("✅ NO CRITICAL INTEGRATION ISSUES FOUND!")
        print("\nAll method calls appear to match implementations.")
        print("All import paths appear correct.")
        print("Integration should work properly.")
        return True


def check_phase_file_completeness():
    """Check if all phase files have the necessary methods"""
    print("\n" + "=" * 60)
    print("CHECKING PHASE FILE COMPLETENESS")
    print("=" * 60)

    # Check key files exist with required methods
    file_method_requirements = {
        "core/world/atmosphere.py": [
            "get_current_atmosphere",
            "update",
            "apply_area_atmosphere",
        ],
        "core/npc/psychology.py": [
            "initialize_npc",
            "get_npc_state",
            "update_npc_state",
        ],
        "core/npc/dialogue.py": ["generate_dialogue"],
        "core/narrative/thread_manager.py": ["add_thread", "get_active_threads"],
        "core/narrative/event_integration.py": ["get_narrative_context_for_npc"],
    }

    missing_files = []
    missing_methods = []

    for file_path, required_methods in file_method_requirements.items():
        file_obj = Path(file_path)
        if not file_obj.exists():
            missing_files.append(file_path)
            print(f"❌ {file_path} - FILE MISSING")
        else:
            with open(file_obj, "r") as f:
                content = f.read()

            file_missing_methods = []
            for method in required_methods:
                if f"def {method}" not in content:
                    file_missing_methods.append(method)

            if file_missing_methods:
                missing_methods.extend(
                    [(file_path, method) for method in file_missing_methods]
                )
                print(f"❌ {file_path} - MISSING: {', '.join(file_missing_methods)}")
            else:
                print(f"✅ {file_path} - all methods present")

    if missing_files or missing_methods:
        print(
            f"\n❌ Found {len(missing_files)} missing files and {len(missing_methods)} missing methods"
        )
        return False
    else:
        print("\n✅ All required phase files and methods are present")
        return True


if __name__ == "__main__":
    integration_ok = check_method_calls()
    files_ok = check_phase_file_completeness()

    if integration_ok and files_ok:
        print("\n🎉 INTEGRATION IS READY TO RUN! 🎉")
        print("\nAll systems should work together properly.")
        print("Only remaining issue is installing dependencies (pydantic, etc.)")
    else:
        print("\n⚠️  INTEGRATION ISSUES NEED TO BE FIXED")
        print("\nSome code problems were found that would prevent proper operation.")
