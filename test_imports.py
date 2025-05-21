#!/usr/bin/env python3
"""
Test imports for The Living Rusted Tankard.
"""

print("Testing imports...")

try:
    from pathlib import Path
    print("- pathlib.Path: OK")
    
    from datetime import datetime
    print("- datetime: OK")
    
    from typing import Dict, List, Optional, Any
    print("- typing basics: OK")
    
    from pydantic import BaseModel
    print("- pydantic.BaseModel: OK")
    
    # Check PrivateAttr
    try:
        from pydantic import PrivateAttr
        print("- pydantic.PrivateAttr: OK")
    except ImportError:
        print("- pydantic.PrivateAttr: MISSING")
        print("  Alternative: Install pydantic v2 or use Field with exclude=True for private fields")
    
    # Try importing core modules
    try:
        from living_rusted_tankard.core.clock import GameTime
        print("- living_rusted_tankard.core.clock.GameTime: OK")
    except ImportError as e:
        print(f"- living_rusted_tankard.core.clock.GameTime: ERROR - {e}")
        
        # Try direct import
        try:
            import sys
            sys.path.insert(0, "./living_rusted_tankard")
            from core.clock import GameTime
            print("- core.clock.GameTime: OK (with path fix)")
        except ImportError as e:
            print(f"- core.clock.GameTime: ERROR - {e}")
    
    # Print pydantic version
    import pydantic
    print(f"- pydantic version: {pydantic.__version__}")
    
except Exception as e:
    print(f"Error during import tests: {e}")
    
print("Import tests complete.")