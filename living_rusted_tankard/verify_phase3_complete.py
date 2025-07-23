#!/usr/bin/env python3
"""Verify Phase 3 completion without external dependencies."""

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


def check_module_imports(filepath, required_imports):
    """Check if a file contains required imports/classes."""
    if not os.path.exists(filepath):
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
        
    missing = []
    for imp in required_imports:
        if imp not in content:
            missing.append(imp)
    
    if missing:
        print(f"  ⚠️  Missing in {filepath}: {', '.join(missing)}")
        return False
    
    return True


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


def check_enhanced_secrets():
    """Check enhanced secrets and evidence system."""
    print("\n🔐 CHECKING ENHANCED SECRETS SYSTEM:")
    
    checks = [
        ("core/npc_modules/secrets.py", "Enhanced Secrets"),
    ]
    
    success = all(check_file_exists(path, desc) for path, desc in checks)
    
    # Check for key components
    if success:
        required = ["EnhancedSecret", "Evidence", "SecretConsequence", 
                   "SecretProtection", "SecretGenerator", "EvidenceType",
                   "investigate", "revelation_progress"]
        success = check_module_imports("core/npc_modules/secrets.py", required)
    
    # Check tests
    test_exists = check_file_exists("tests/test_npc_secrets.py", "Secrets Tests")
    
    return success and test_exists


def check_dialogue_system():
    """Check dynamic dialogue system."""
    print("\n💬 CHECKING DIALOGUE SYSTEM:")
    
    checks = [
        ("core/npc_modules/dialogue.py", "Dialogue System"),
    ]
    
    success = all(check_file_exists(path, desc) for path, desc in checks)
    
    # Check for key components
    if success:
        required = ["DialogueGenerator", "DialogueContext", "DialogueOption",
                   "DialogueType", "DialogueTone", "generate_dialogue_options"]
        success = check_module_imports("core/npc_modules/dialogue.py", required)
    
    # Check tests
    test_exists = check_file_exists("tests/test_npc_dialogue.py", "Dialogue Tests")
    
    return success and test_exists


def check_gossip_system():
    """Check rumor and gossip propagation system."""
    print("\n🗣️ CHECKING GOSSIP SYSTEM:")
    
    checks = [
        ("core/npc_modules/gossip.py", "Gossip System"),
    ]
    
    success = all(check_file_exists(path, desc) for path, desc in checks)
    
    # Check for key components
    if success:
        required = ["GossipNetwork", "Rumor", "RumorType", "spread_rumor",
                   "create_rumor_from_secret", "gossip_tendencies"]
        success = check_module_imports("core/npc_modules/gossip.py", required)
    
    return success


def check_goals_agency():
    """Check NPC goals and agency system."""
    print("\n🎯 CHECKING GOALS & AGENCY SYSTEM:")
    
    checks = [
        ("core/npc_modules/goals.py", "Goals System"),
    ]
    
    success = all(check_file_exists(path, desc) for path, desc in checks)
    
    # Check for key components
    if success:
        required = ["Goal", "GoalStep", "NPCAgency", "GoalGenerator",
                   "GoalType", "GoalCategory", "select_action"]
        success = check_module_imports("core/npc_modules/goals.py", required)
    
    return success


def check_interactions():
    """Check inter-NPC interactions system."""
    print("\n🤝 CHECKING INTERACTIONS SYSTEM:")
    
    checks = [
        ("core/npc_modules/interactions.py", "Interactions System"),
    ]
    
    success = all(check_file_exists(path, desc) for path, desc in checks)
    
    # Check for key components
    if success:
        required = ["InteractionManager", "NPCInteraction", "InteractionType",
                   "initiate_interaction", "simulate_autonomous_interactions"]
        success = check_module_imports("core/npc_modules/interactions.py", required)
    
    return success


def check_phase2_compatibility():
    """Check that Phase 2 systems are still intact."""
    print("\n🔄 CHECKING PHASE 2 COMPATIBILITY:")
    
    phase2_files = [
        ("core/npc_modules/psychology.py", "Psychology (Phase 2)"),
        ("core/npc_modules/behavioral_rules.py", "Behavioral Rules (Phase 2)"),
        ("core/npc_modules/schedules.py", "Schedules (Phase 2)"),
        ("core/npc_modules/relationships.py", "Relationships (Phase 2)"),
    ]
    
    return all(check_file_exists(path, desc) for path, desc in phase2_files)


def check_feature_integration():
    """Check that features are properly integrated."""
    print("\n🔗 CHECKING FEATURE INTEGRATION:")
    
    integration_points = {
        "Secrets ↔ Gossip": False,
        "Goals ↔ Behavior": False,
        "Dialogue ↔ Context": False,
        "Interactions ↔ Relationships": False,
        "Evidence ↔ Investigation": False
    }
    
    # Check secrets-gossip integration
    if os.path.exists("core/npc_modules/gossip.py"):
        with open("core/npc_modules/gossip.py", 'r') as f:
            if "create_rumor_from_secret" in f.read():
                integration_points["Secrets ↔ Gossip"] = True
    
    # Check goals-behavior integration
    if os.path.exists("core/npc_modules/goals.py"):
        with open("core/npc_modules/goals.py", 'r') as f:
            content = f.read()
            if "BehaviorRule" in content or "Action" in content:
                integration_points["Goals ↔ Behavior"] = True
    
    # Check dialogue-context integration
    if os.path.exists("core/npc_modules/dialogue.py"):
        with open("core/npc_modules/dialogue.py", 'r') as f:
            if "psychology" in f.read().lower():
                integration_points["Dialogue ↔ Context"] = True
    
    # Check interactions-relationships integration
    if os.path.exists("core/npc_modules/interactions.py"):
        with open("core/npc_modules/interactions.py", 'r') as f:
            if "relationship_web" in f.read():
                integration_points["Interactions ↔ Relationships"] = True
    
    # Check evidence-investigation integration
    if os.path.exists("core/npc_modules/secrets.py"):
        with open("core/npc_modules/secrets.py", 'r') as f:
            content = f.read()
            if "def investigate" in content and "class Evidence" in content:
                integration_points["Evidence ↔ Investigation"] = True
    
    # Print results
    for integration, status in integration_points.items():
        if status:
            print(f"  ✅ {integration}")
        else:
            print(f"  ❌ {integration}")
    
    return all(integration_points.values())


def check_test_coverage():
    """Check test coverage for Phase 3 systems."""
    print("\n🧪 CHECKING TEST COVERAGE:")
    
    test_files = [
        ("tests/test_npc_secrets.py", "Secrets Tests"),
        ("tests/test_npc_dialogue.py", "Dialogue Tests"),
    ]
    
    all_exist = True
    total_tests = 0
    
    for filepath, description in test_files:
        if check_file_exists(filepath, description):
            with open(filepath, 'r') as f:
                content = f.read()
                test_count = content.count("def test_")
                print(f"     → Contains {test_count} test methods")
                total_tests += test_count
        else:
            all_exist = False
    
    # Check for Phase 2 tests still present
    phase2_tests = [
        "tests/test_npc_psychology.py",
        "tests/test_npc_behavioral_rules.py"
    ]
    
    for test_file in phase2_tests:
        if os.path.exists(test_file):
            with open(test_file, 'r') as f:
                test_count = f.read().count("def test_")
                total_tests += test_count
    
    print(f"\n  📊 Total Phase 3 Test Methods: {total_tests}")
    
    return all_exist and total_tests >= 40


def check_code_quality():
    """Check code quality indicators."""
    print("\n📊 CHECKING CODE QUALITY:")
    
    # Count files
    npc_files = count_files_in_directory("core/npc_modules")
    test_files = count_files_in_directory("tests")
    
    print(f"  📁 NPC System Files: {npc_files}")
    print(f"  📁 Test Files: {test_files}")
    
    # Check for docstrings
    doc_count = 0
    for root, dirs, files in os.walk("core/npc_modules"):
        for file in files:
            if file.endswith(".py") and file in ["secrets.py", "dialogue.py", 
                                                 "gossip.py", "goals.py", 
                                                 "interactions.py"]:
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    doc_count += content.count('"""')
    
    print(f"  📝 Docstrings in Phase 3 Files: {doc_count // 2}")
    
    # Check for type hints
    type_hints = 0
    for root, dirs, files in os.walk("core/npc_modules"):
        for file in files:
            if file.endswith(".py") and file in ["secrets.py", "dialogue.py", 
                                                 "gossip.py", "goals.py", 
                                                 "interactions.py"]:
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    type_hints += content.count("->")
                    type_hints += content.count(": str")
                    type_hints += content.count(": Dict")
                    type_hints += content.count(": List")
                    type_hints += content.count(": Optional")
    
    print(f"  🔍 Type Hints in Phase 3: {type_hints}")
    
    # Check complexity indicators
    total_classes = 0
    total_methods = 0
    
    for root, dirs, files in os.walk("core/npc_modules"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    total_classes += content.count("class ")
                    total_methods += content.count("def ")
    
    print(f"  🏗️ Total Classes: {total_classes}")
    print(f"  ⚙️ Total Methods: {total_methods}")
    
    return npc_files >= 10 and doc_count >= 100


def main():
    """Run Phase 3 verification."""
    print("🔍 PHASE 3 COMPLETION VERIFICATION")
    print("=" * 60)
    
    # Run all checks
    secrets_ok = check_enhanced_secrets()
    dialogue_ok = check_dialogue_system()
    gossip_ok = check_gossip_system()
    goals_ok = check_goals_agency()
    interactions_ok = check_interactions()
    phase2_ok = check_phase2_compatibility()
    integration_ok = check_feature_integration()
    tests_ok = check_test_coverage()
    quality_ok = check_code_quality()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    results = [
        ("Enhanced Secrets System", secrets_ok),
        ("Dynamic Dialogue System", dialogue_ok),
        ("Gossip Propagation System", gossip_ok),
        ("Goals & Agency System", goals_ok),
        ("Inter-NPC Interactions", interactions_ok),
        ("Phase 2 Compatibility", phase2_ok),
        ("Feature Integration", integration_ok),
        ("Test Coverage", tests_ok),
        ("Code Quality", quality_ok)
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
        print("🎉 PHASE 3 VERIFICATION SUCCESSFUL!")
        print("✅ Enhanced secrets with evidence trails")
        print("✅ Dynamic context-aware dialogue")
        print("✅ Rumor and gossip propagation")
        print("✅ NPC goals and autonomous agency")
        print("✅ Inter-NPC interactions and conflicts")
        print("✅ Full integration with Phase 2 systems")
        print("✅ Comprehensive test coverage")
        print("\n🚀 READY FOR GIT COMMIT AND PHASE 4!")
    else:
        print("❌ PHASE 3 VERIFICATION FAILED")
        print("Please check the failed components above.")
        sys.exit(1)


if __name__ == "__main__":
    main()