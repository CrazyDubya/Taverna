#!/usr/bin/env python3
"""
Simple server startup script for The Living Rusted Tankard
"""
import subprocess
import sys
import time
import os

def main():
    print("🚀 Starting The Living Rusted Tankard Server...")
    
    # Change to the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Try different Python commands
    python_cmds = ['poetry run python', 'python3.10', 'python3', 'python']
    
    for python_cmd in python_cmds:
        try:
            print(f"Trying with: {python_cmd}")
            
            # First, try to start the server directly
            server_cmd = f"{python_cmd} -m uvicorn core.api:app --host 0.0.0.0 --port 8080"
            print(f"Running: {server_cmd}")
            
            process = subprocess.Popen(server_cmd, shell=True)
            
            # Wait a bit to see if it starts
            time.sleep(3)
            
            if process.poll() is None:
                print(f"✅ Server started successfully with {python_cmd}!")
                print("📍 Access the game at: http://localhost:8080")
                print("🤖 AI Demo at: http://localhost:8080/ai-demo")
                print("\nPress Ctrl+C to stop the server")
                
                try:
                    process.wait()
                except KeyboardInterrupt:
                    print("\n🛑 Stopping server...")
                    process.terminate()
                    
                return
            else:
                print(f"❌ Failed with {python_cmd}")
                
        except Exception as e:
            print(f"Error with {python_cmd}: {e}")
            continue
    
    print("\n❌ Could not start server. Please ensure dependencies are installed:")
    print("   poetry install")
    print("   OR")
    print("   pip install fastapi uvicorn pydantic jinja2")

if __name__ == "__main__":
    main()