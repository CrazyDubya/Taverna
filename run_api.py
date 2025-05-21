#!/usr/bin/env python3
"""
Run the FastAPI server for The Living Rusted Tankard.

This script launches a web server that provides both the API and web interface
for the game.
"""
import uvicorn
import sys
import os
import logging
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add the living_rusted_tankard directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(script_dir, "living_rusted_tankard")
sys.path.insert(0, project_dir)

def parse_args():
    parser = argparse.ArgumentParser(description="Run the web server for The Living Rusted Tankard.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8001, help="Port to run the server on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    parser.add_argument("--log-level", type=str, default="info", choices=["debug", "info", "warning", "error", "critical"], help="Logging level")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    logger.info("Starting The Living Rusted Tankard web server...")
    logger.info(f"Web interface will be available at: http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}")
    logger.info(f"API docs will be available at: http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/docs")
    logger.info("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "core.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )
