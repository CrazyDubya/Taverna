#!/usr/bin/env python3
"""
ULTIMATE GAME LAUNCHER - This WILL work!
"""
import subprocess
import sys
import time
import os
import socket
import webbrowser
from pathlib import Path


def check_port(port):
    """Check if a port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("localhost", port))
    sock.close()
    return result != 0  # True if port is available


def find_free_port():
    """Find a free port to use"""
    for port in [8888, 8080, 8000, 8001, 9000, 9001, 5000, 5001, 3000]:
        if check_port(port):
            return port
    # If all common ports are taken, find a random one
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def kill_process_on_port(port):
    """Kill any process using a port"""
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(
                f"lsof -ti:{port} | xargs kill -9",
                shell=True,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.run(
                f"fuser -k {port}/tcp", shell=True, stderr=subprocess.DEVNULL
            )
    except:
        pass


def launch_server():
    """Try multiple methods to launch the server"""
    os.chdir(Path(__file__).parent)

    # Find available port
    port = find_free_port()
    print(f"🔍 Found available port: {port}")

    # Try different server files and methods
    attempts = [
        # Try minimal server first (no dependencies)
        {
            "name": "Minimal Server (No Dependencies)",
            "commands": [
                f"{sys.executable} minimal_server.py",
                "python3 minimal_server.py",
                "python minimal_server.py",
            ],
            "file": "minimal_server.py",
            "port": 8888,
        },
        # Try simple server with poetry
        {
            "name": "Simple Server with Poetry",
            "commands": [
                "poetry run python simple_server.py",
            ],
            "file": "simple_server.py",
            "port": 8080,
        },
        # Try simple server directly
        {
            "name": "Simple Server Direct",
            "commands": [
                f"{sys.executable} simple_server.py",
                "python3 simple_server.py",
                "python3.10 simple_server.py",
            ],
            "file": "simple_server.py",
            "port": 8080,
        },
    ]

    for attempt in attempts:
        if not Path(attempt["file"]).exists():
            continue

        print(f"\n🚀 Trying: {attempt['name']}")

        # Make sure port is free
        kill_process_on_port(attempt["port"])
        time.sleep(1)

        for cmd in attempt["commands"]:
            try:
                print(f"   Running: {cmd}")
                process = subprocess.Popen(
                    cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )

                # Give it time to start
                time.sleep(3)

                # Check if it's running
                if process.poll() is None:
                    # Process is still running, check if port is listening
                    if not check_port(attempt["port"]):
                        print(f"✅ SUCCESS! Server is running on port {attempt['port']}")
                        url = f"http://localhost:{attempt['port']}"
                        print(f"🌐 Opening {url} in your browser...")

                        # Open browser
                        webbrowser.open(url)

                        print("\n" + "=" * 50)
                        print("🍺 THE LIVING RUSTED TANKARD IS NOW RUNNING!")
                        print(f"📍 URL: {url}")
                        print("🛑 Press Ctrl+C to stop the server")
                        print("=" * 50 + "\n")

                        # Keep running
                        try:
                            process.wait()
                        except KeyboardInterrupt:
                            print("\n🛑 Shutting down server...")
                            process.terminate()

                        return True
                else:
                    # Process died, try next command
                    continue

            except Exception as e:
                print(f"   Error: {e}")
                continue

    return False


def main():
    print("🍺 THE LIVING RUSTED TANKARD - ULTIMATE LAUNCHER")
    print("=" * 50)

    if launch_server():
        print("\n✅ Game shut down successfully!")
    else:
        print("\n❌ Could not start the server!")
        print("\nTroubleshooting steps:")
        print("1. Make sure Python 3 is installed: python3 --version")
        print("2. Try installing minimal dependencies:")
        print("   pip install --user fastapi uvicorn")
        print("3. Or use the minimal server which needs no dependencies")
        print("\nManual start commands:")
        print("   python3 minimal_server.py")
        print("   python3 simple_server.py")


if __name__ == "__main__":
    main()
