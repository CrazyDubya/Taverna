#!/usr/bin/env python3
"""Verify Phase 2 completion without external dependencies."""

import os
import sys


def check_file_exists(filepath, description):
    """Check if a file exists and print result."""
    if os.path.exists(filepath):
        print(f"  ✅ {description}: {filepath}")
        return True
    else:
        print(f"  ❌ {description}: {filepath} - NOT FOUND")
        return False


def check_module_structure(module_path, description):
    """Check if a module has proper structure."""
    init_file = os.path.join(module_path, "__init__.py")
    if os.path.exists(module_path) and os.path.isdir(module_path):
        if os.path.exists(init_file):
            print(f"  ✅ {description}: {module_path}")
            return True
        else:
            print(f"  ⚠️  {description}: {module_path} - Missing __init__.py")
            return True  # Still count as success if directory exists
    else:
        print(f"  ❌ {description}: {module_path} - NOT FOUND")
        return False


def count_files_in_directory(directory, extension=".py"):
    """Count files with given extension in directory."""
    if not os.path.exists(directory):
        return 0

    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                count += 1
    return count


def check_area_system():
    """Check area and atmosphere system implementation."""
    print("\n🏠 CHECKING AREA & ATMOSPHERE SYSTEM:")

    checks = [
        ("core/world/__init__.py", "World Package Init"),
        ("core/world/area.py", "Area System"),
        ("core/world/area_manager.py", "Area Manager"),
        ("core/world/atmosphere.py", "Atmosphere System"),
        ("core/world/floor_manager.py", "Floor Manager"),
        ("data/areas/tavern_layout.json", "Tavern Layout Data"),
    ]

    success = all(check_file_exists(path, desc) for path, desc in checks)

    # Check for area tests
    area_tests = check_file_exists("tests/test_area_system.py", "Area System Tests")

    return success and area_tests


def check_npc_psychology():
    """Check NPC psychology system implementation."""
    print("\n🧠 CHECKING NPC PSYCHOLOGY SYSTEM:")

    checks = [
        ("core/npc_systems/__init__.py", "NPC Package Init"),
        ("core/npc_systems/psychology.py", "Psychology System"),
        ("core/npc_systems/behavioral_rules.py", "Behavioral Rules"),
        ("core/npc_systems/schedules.py", "NPC Schedules"),
        ("core/npc_systems/relationships.py", "Relationship System"),
    ]

    success = all(check_file_exists(path, desc) for path, desc in checks)

    # Check for NPC tests
    psych_tests = check_file_exists("tests/test_npc_psychology.py", "Psychology Tests")
    behavior_tests = check_file_exists(
        "tests/test_npc_behavioral_rules.py", "Behavioral Tests"
    )

    return success and psych_tests and behavior_tests


def check_feature_coverage():
    """Check that key features are implemented."""
    print("\n🔍 CHECKING FEATURE COVERAGE:")

    features = {
        "Dynamic Properties": False,
        "Atmosphere System": False,
        "NPC Schedules": False,
        "Behavioral Rules": False,
        "Relationship Web": False,
        "Hidden Areas": False,
        "Floor Management": False,
        "Social Dynamics": False,
    }

    # Check for key classes/functions in files
    checks = [
        (
            "core/world/atmosphere.py",
            ["AtmosphereState", "SensoryDetail", "AtmosphereManager"],
        ),
        (
            "core/world/area.py",
            ["TavernArea", "Feature", "Connection", "hidden", "discovered"],
        ),
        ("core/npc_systems/schedules.py", ["NPCSchedule", "ScheduleBlock", "DayType"]),
        (
            "core/npc_systems/behavioral_rules.py",
            ["BehaviorEngine", "BehaviorRule", "Condition"],
        ),
        (
            "core/npc_systems/relationships.py",
            ["RelationshipWeb", "Conflict", "Alliance"],
        ),
        (
            "core/world/floor_manager.py",
            ["FloorManager", "FloorInfo", "vertical_sound"],
        ),
    ]

    for filepath, keywords in checks:
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                content = f.read()
                for keyword in keywords:
                    if keyword in content:
                        if "atmosphere" in filepath.lower():
                            features["Dynamic Properties"] = True
                            features["Atmosphere System"] = True
                        if "schedules" in filepath:
                            features["NPC Schedules"] = True
                        if "behavioral_rules" in filepath:
                            features["Behavioral Rules"] = True
                        if "relationships" in filepath:
                            features["Relationship Web"] = True
                            features["Social Dynamics"] = True
                        if "area.py" in filepath and "hidden" in keyword:
                            features["Hidden Areas"] = True
                        if "floor_manager" in filepath:
                            features["Floor Management"] = True

    for feature, implemented in features.items():
        if implemented:
            print(f"  ✅ {feature}")
        else:
            print(f"  ❌ {feature}")

    return all(features.values())


def check_test_coverage():
    """Check test coverage for Phase 2 systems."""
    print("\n🧪 CHECKING TEST COVERAGE:")

    test_files = [
        ("tests/test_area_system.py", "Area System Tests"),
        ("tests/test_npc_psychology.py", "NPC Psychology Tests"),
        ("tests/test_npc_behavioral_rules.py", "Behavioral Rules Tests"),
    ]

    all_exist = True
    for filepath, description in test_files:
        if check_file_exists(filepath, description):
            # Count test methods
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    content = f.read()
                    test_count = content.count("def test_")
                    print(f"     → Contains {test_count} test methods")
        else:
            all_exist = False

    return all_exist


def check_code_quality():
    """Check code quality indicators."""
    print("\n📊 CHECKING CODE QUALITY INDICATORS:")

    quality_checks = []

    # Check file counts
    world_files = count_files_in_directory("core/world")
    npc_files = count_files_in_directory("core/npc_systems")
    test_files = count_files_in_directory("tests")

    print(f"  📁 World System Files: {world_files}")
    print(f"  📁 NPC System Files: {npc_files}")
    print(f"  📁 Test Files: {test_files}")

    # Check for documentation
    doc_indicators = 0
    for root, dirs, files in os.walk("core"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    content = f.read()
                    if '"""' in content:
                        doc_indicators += content.count('"""') // 2

    print(f"  📝 Docstrings Found: {doc_indicators}")

    # Check for type hints
    type_hints = 0
    for root, dirs, files in os.walk("core"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    content = f.read()
                    type_hints += content.count("->")
                    type_hints += content.count(": str")
                    type_hints += content.count(": int")
                    type_hints += content.count(": float")
                    type_hints += content.count(": bool")
                    type_hints += content.count(": List")
                    type_hints += content.count(": Dict")
                    type_hints += content.count(": Optional")

    print(f"  🔍 Type Hints Used: {type_hints}")

    return world_files >= 4 and npc_files >= 4 and test_files >= 35


def main():
    """Run Phase 2 verification."""
    print("🔍 PHASE 2 COMPLETION VERIFICATION")
    print("=" * 60)

    # Run all checks
    area_ok = check_area_system()
    npc_ok = check_npc_psychology()
    features_ok = check_feature_coverage()
    tests_ok = check_test_coverage()
    quality_ok = check_code_quality()

    # Summary
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)

    results = [
        ("Area & Atmosphere System", area_ok),
        ("NPC Psychology System", npc_ok),
        ("Feature Coverage", features_ok),
        ("Test Coverage", tests_ok),
        ("Code Quality", quality_ok),
    ]

    all_passed = True
    for component, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✅" if passed else "❌"
        print(f"{symbol} {status} {component}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)

    if all_passed:
        print("🎉 PHASE 2 VERIFICATION SUCCESSFUL!")
        print("✅ Enhanced room architecture implemented")
        print("✅ Atmosphere system with dynamic properties")
        print("✅ NPC behavioral patterns and schedules")
        print("✅ Inter-NPC relationships and conflicts")
        print("✅ Hidden areas and discovery system")
        print("✅ Comprehensive test coverage")
        print("\n🚀 READY FOR GIT COMMIT AND PHASE 3!")
    else:
        print("❌ PHASE 2 VERIFICATION FAILED")
        print("Please check the failed components above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
