#!/bin/bash
# Global AI Observer Command
# Run this from anywhere to launch the AI player observer

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the game directory and run the observer
cd "$SCRIPT_DIR"
python3 launch_ai_observer.py "$@"