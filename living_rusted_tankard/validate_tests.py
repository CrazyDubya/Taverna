#!/usr/bin/env python3
"""
Test Validation Script - Phase 1.1 Completion Check
Validates that the test infrastructure is comprehensive and working.
"""

import os
import sys
import importlib
from pathlib import Path
from typing import List, Dict, Set

def get_core_modules() -> Set[str]:
    """Get list of all core modules that should have tests."""
    core_dir = Path("core")
    modules = set()
    
    for file_path in core_dir.rglob("*.py"):
        if file_path.name == "__init__.py":
            continue
        
        # Convert path to module name
        relative_path = file_path.relative_to(Path("."))
        module_name = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]
        modules.add(module_name)
    
    return modules

def get_test_modules() -> Set[str]:
    """Get list of all test modules."""
    tests_dir = Path("tests")
    modules = set()
    
    for file_path in tests_dir.rglob("test_*.py"):
        # Convert path to module name
        relative_path = file_path.relative_to(Path("."))
        module_name = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]
        modules.add(module_name)
    
    return modules

def analyze_test_coverage() -> Dict[str, any]:
    """Analyze test coverage and identify gaps."""
    core_modules = get_core_modules()
    test_modules = get_test_modules()
    
    # Map core modules to expected test files
    expected_tests = {}
    for module in core_modules:
        module_name = module.split(".")[-1]  # Get just the filename
        expected_test = f"tests.test_{module_name}"
        expected_tests[module] = expected_test
    
    # Check which core modules have tests
    tested_modules = set()
    missing_tests = set()
    
    for core_module, expected_test in expected_tests.items():
        if expected_test in test_modules:
            tested_modules.add(core_module)
        else:
            missing_tests.add(core_module)
    
    # Check for extra test files (not bad, but worth noting)
    extra_tests = test_modules - set(expected_tests.values())
    
    return {
        "core_modules": core_modules,
        "test_modules": test_modules,
        "tested_modules": tested_modules,
        "missing_tests": missing_tests,
        "extra_tests": extra_tests,
        "coverage_percentage": len(tested_modules) / len(core_modules) * 100 if core_modules else 0
    }

def check_critical_systems() -> Dict[str, bool]:
    """Check if critical systems have test coverage."""
    critical_systems = [
        "core.error_recovery",
        "core.event_bus", 
        "core.clock",
        "core.fantasy_calendar",
        "core.game_state",
        "core.npc",
        "core.player",
        "core.economy",
        "core.room",
        "core.llm_game_master"
    ]
    
    test_coverage = {}
    
    for system in critical_systems:
        module_name = system.split(".")[-1]
        test_file = Path(f"tests/test_{module_name}.py")
        test_coverage[system] = test_file.exists()
    
    return test_coverage

def validate_test_structure() -> List[str]:
    """Validate test file structure and imports."""
    issues = []
    
    # Check if tests directory exists
    if not Path("tests").exists():
        issues.append("❌ tests/ directory does not exist")
        return issues
    
    # Check for conftest.py
    if not Path("tests/conftest.py").exists():
        issues.append("❌ tests/conftest.py missing")
    
    # Check for __init__.py in tests
    if not Path("tests/__init__.py").exists():
        issues.append("❌ tests/__init__.py missing")
    
    # Check for fixtures directory
    if not Path("tests/fixtures").exists():
        issues.append("❌ tests/fixtures/ directory missing")
    else:
        if not Path("tests/fixtures/__init__.py").exists():
            issues.append("❌ tests/fixtures/__init__.py missing")
    
    # Check for utils directory
    if not Path("tests/utils").exists():
        issues.append("❌ tests/utils/ directory missing")
    else:
        if not Path("tests/utils/__init__.py").exists():
            issues.append("❌ tests/utils/__init__.py missing")
    
    return issues

def validate_new_tests() -> List[str]:
    """Validate the newly created test files."""
    new_tests = [
        "tests/test_error_recovery.py",
        "tests/test_event_bus.py", 
        "tests/test_clock.py",
        "tests/test_fantasy_calendar.py"
    ]
    
    issues = []
    
    for test_file in new_tests:
        if not Path(test_file).exists():
            issues.append(f"❌ {test_file} missing")
            continue
        
        # Check file is not empty
        content = Path(test_file).read_text()
        if len(content) < 100:
            issues.append(f"❌ {test_file} appears to be empty or too small")
            continue
        
        # Check for basic test structure
        if "class Test" not in content:
            issues.append(f"❌ {test_file} missing test classes")
        
        if "def test_" not in content:
            issues.append(f"❌ {test_file} missing test methods")
        
        if "import pytest" not in content:
            issues.append(f"⚠️  {test_file} missing pytest import")
    
    return issues

def run_validation():
    """Run complete validation of test infrastructure."""
    print("🔍 VALIDATING TEST INFRASTRUCTURE")
    print("=" * 50)
    
    # Check test structure
    print("\n📁 Checking test directory structure...")
    structure_issues = validate_test_structure()
    
    if structure_issues:
        for issue in structure_issues:
            print(f"  {issue}")
    else:
        print("  ✅ Test directory structure is correct")
    
    # Check test coverage
    print("\n📊 Analyzing test coverage...")
    coverage = analyze_test_coverage()
    
    print(f"  📈 Coverage: {coverage['coverage_percentage']:.1f}%")
    print(f"  📦 Core modules: {len(coverage['core_modules'])}")
    print(f"  🧪 Test modules: {len(coverage['test_modules'])}")
    print(f"  ✅ Tested modules: {len(coverage['tested_modules'])}")
    print(f"  ❌ Missing tests: {len(coverage['missing_tests'])}")
    
    if coverage['missing_tests']:
        print("\n  Missing test coverage for:")
        for module in sorted(coverage['missing_tests']):
            print(f"    - {module}")
    
    # Check critical systems
    print("\n🔧 Checking critical system coverage...")
    critical_coverage = check_critical_systems()
    
    for system, has_test in critical_coverage.items():
        status = "✅" if has_test else "❌"
        print(f"  {status} {system}")
    
    # Validate new tests
    print("\n🆕 Validating newly created tests...")
    new_test_issues = validate_new_tests()
    
    if new_test_issues:
        for issue in new_test_issues:
            print(f"  {issue}")
    else:
        print("  ✅ All new test files are properly structured")
    
    # Overall assessment
    print("\n" + "=" * 50)
    print("📋 PHASE 1.1 ASSESSMENT")
    
    critical_systems_covered = sum(critical_coverage.values())
    total_critical = len(critical_coverage)
    
    if critical_systems_covered == total_critical and not new_test_issues:
        print("✅ PHASE 1.1 COMPLETE: Test infrastructure is comprehensive")
        print("   Ready to proceed to Phase 1.2")
        return True
    else:
        print("🔄 PHASE 1.1 IN PROGRESS: Some issues remain")
        print(f"   Critical systems covered: {critical_systems_covered}/{total_critical}")
        if new_test_issues:
            print(f"   New test issues: {len(new_test_issues)}")
        return False

def check_importability():
    """Check if test modules can be imported without errors."""
    print("\n🔍 Checking test module importability...")
    
    test_modules = [
        "tests.test_error_recovery",
        "tests.test_event_bus",
        "tests.test_clock", 
        "tests.test_fantasy_calendar"
    ]
    
    issues = []
    
    for module_name in test_modules:
        try:
            # Add current directory to path
            sys.path.insert(0, str(Path.cwd()))
            
            importlib.import_module(module_name)
            print(f"  ✅ {module_name}")
        except ImportError as e:
            print(f"  ❌ {module_name}: {e}")
            issues.append(f"{module_name}: {e}")
        except Exception as e:
            print(f"  ⚠️  {module_name}: {e}")
            issues.append(f"{module_name}: {e}")
    
    return issues

if __name__ == "__main__":
    print("🏗️  THE LIVING RUSTED TANKARD - TEST VALIDATION")
    print("Phase 1.1: Test Infrastructure Setup")
    print()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run validation
    success = run_validation()
    
    # Check imports
    import_issues = check_importability()
    
    if import_issues:
        print(f"\n⚠️  Import issues found: {len(import_issues)}")
        for issue in import_issues:
            print(f"   - {issue}")
        success = False
    
    # Final status
    print("\n" + "=" * 50)
    if success:
        print("🎉 VALIDATION SUCCESSFUL!")
        print("✅ Test infrastructure is ready for development")
        print("➡️  Ready to proceed to next phase")
    else:
        print("⚠️  VALIDATION INCOMPLETE")
        print("🔧 Please address the issues above before proceeding")
        print("📚 Refer to DEVELOPMENT_ROADMAP.md for guidance")
    
    sys.exit(0 if success else 1)