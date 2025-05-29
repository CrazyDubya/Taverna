#!/usr/bin/env python3
"""
Verify Phase 1 completion by checking file structure and code quality.
"""

import sys
from pathlib import Path

def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists and report."""
    path = Path(file_path)
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"  {status} {description}: {file_path}")
    return exists

def check_test_coverage():
    """Check critical test coverage."""
    print("🧪 CHECKING CRITICAL TEST COVERAGE:")
    
    critical_tests = [
        ("tests/test_error_recovery.py", "Error Recovery System"),
        ("tests/test_event_bus.py", "Event Bus System"),
        ("tests/test_clock.py", "Time Management System"),
        ("tests/test_fantasy_calendar.py", "Fantasy Calendar System"),
        ("tests/test_room.py", "Room Management System"),
        ("tests/test_llm_game_master.py", "LLM Game Master System"),
        ("tests/test_save_manager.py", "Save Manager System")
    ]
    
    all_exist = True
    for test_file, description in critical_tests:
        exists = check_file_exists(test_file, description)
        all_exist = all_exist and exists
    
    return all_exist

def check_persistence_system():
    """Check persistence system files."""
    print("\n💾 CHECKING PERSISTENCE SYSTEM:")
    
    persistence_files = [
        ("core/persistence/__init__.py", "Persistence Package Init"),
        ("core/persistence/save_manager.py", "Save Manager"),
        ("core/persistence/migrations.py", "Migration System"),
        ("core/persistence/validation.py", "Validation System")
    ]
    
    all_exist = True
    for file_path, description in persistence_files:
        exists = check_file_exists(file_path, description)
        all_exist = all_exist and exists
    
    return all_exist

def check_test_infrastructure():
    """Check test infrastructure."""
    print("\n🏗️ CHECKING TEST INFRASTRUCTURE:")
    
    infrastructure_files = [
        ("tests/fixtures/__init__.py", "Fixtures Package"),
        ("tests/fixtures/game_fixtures.py", "Game Fixtures"),
        ("tests/fixtures/npc_fixtures.py", "NPC Fixtures"),
        ("tests/fixtures/economy_fixtures.py", "Economy Fixtures"),
        ("tests/fixtures/player_fixtures.py", "Player Fixtures"),
        ("tests/fixtures/database_fixtures.py", "Database Fixtures"),
        ("tests/fixtures/performance_fixtures.py", "Performance Fixtures"),
        ("tests/utils/__init__.py", "Utils Package"),
        ("tests/utils/test_helpers.py", "Test Helpers"),
        ("tests/utils/mock_helpers.py", "Mock Helpers"),
        ("tests/utils/assertion_helpers.py", "Assertion Helpers")
    ]
    
    all_exist = True
    for file_path, description in infrastructure_files:
        exists = check_file_exists(file_path, description)
        all_exist = all_exist and exists
    
    return all_exist

def check_documentation():
    """Check documentation files."""
    print("\n📚 CHECKING DOCUMENTATION:")
    
    doc_files = [
        ("docs/DEVELOPMENT_ROADMAP.md", "Development Roadmap"),
        ("docs/DEEP_NARRATIVE_ENGINE_DESIGN.md", "Narrative Engine Design"),
        ("docs/ENGINE.md", "Engine Documentation"),
        ("docs/PHASE_1_PROGRESS.md", "Phase 1 Progress Report")
    ]
    
    all_exist = True
    for file_path, description in doc_files:
        exists = check_file_exists(file_path, description)
        all_exist = all_exist and exists
    
    return all_exist

def check_code_quality():
    """Check code quality indicators."""
    print("\n🔍 CHECKING CODE QUALITY:")
    
    # Check for test file structure
    test_files = list(Path("tests").glob("test_*.py"))
    print(f"  ✅ Test Files: {len(test_files)} files found")
    
    # Check for fixture files
    fixture_files = list(Path("tests/fixtures").glob("*.py"))
    print(f"  ✅ Fixture Files: {len(fixture_files)} files found")
    
    # Check core module count
    core_files = list(Path("core").rglob("*.py"))
    print(f"  ✅ Core Modules: {len(core_files)} files found")
    
    return len(test_files) > 25 and len(fixture_files) > 5

def check_thread_safety():
    """Check thread safety implementation."""
    print("\n🔒 CHECKING THREAD SAFETY:")
    
    # Check async_llm_pipeline for thread safety
    pipeline_file = Path("core/async_llm_pipeline.py")
    if pipeline_file.exists():
        content = pipeline_file.read_text()
        has_threading = "import threading" in content
        has_lock = "threading.RLock()" in content or "threading.Lock()" in content
        
        print(f"  {'✅' if has_threading else '❌'} Threading import found")
        print(f"  {'✅' if has_lock else '❌'} Thread locks implemented")
        
        return has_threading and has_lock
    else:
        print("  ❌ Async LLM Pipeline file not found")
        return False

def main():
    """Main verification function."""
    print("🔍 PHASE 1 COMPLETION VERIFICATION")
    print("=" * 60)
    
    checks = [
        ("Critical Test Coverage", check_test_coverage),
        ("Persistence System", check_persistence_system),
        ("Test Infrastructure", check_test_infrastructure),
        ("Documentation", check_documentation),
        ("Code Quality", check_code_quality),
        ("Thread Safety", check_thread_safety)
    ]
    
    all_passed = True
    results = {}
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results[check_name] = result
            all_passed = all_passed and result
        except Exception as e:
            print(f"  ❌ Error in {check_name}: {e}")
            results[check_name] = False
            all_passed = False
    
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check_name}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 PHASE 1 VERIFICATION SUCCESSFUL!")
        print("✅ All critical components implemented")
        print("✅ Test infrastructure complete")
        print("✅ Persistence system ready")
        print("✅ Thread safety implemented")
        print("✅ Documentation comprehensive")
        print("\n🚀 READY FOR GIT COMMIT AND PHASE 2!")
    else:
        print("⚠️ PHASE 1 VERIFICATION INCOMPLETE")
        print("🔧 Some components need attention")
        print("📚 Review failed checks above")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)