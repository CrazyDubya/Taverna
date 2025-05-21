#!/usr/bin/env python3
"""
Web server entry point for The Living Rusted Tankard.

This script initializes and starts the FastAPI web server.
"""
import sys
import os
import uvicorn

def main():
    """Run the web server."""
    print("Starting The Living Rusted Tankard Web Server...")
    
    try:
        # Add the project root to the Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Start the FastAPI server using uvicorn
        uvicorn.run(
            "living_rusted_tankard.core.api:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"Error: Failed to import required modules. {e}")
        print("Make sure you have installed all dependencies with 'poetry install'")
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())