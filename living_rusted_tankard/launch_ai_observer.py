#!/usr/bin/env python3
"""
AI Player Observer Launch Script

Launch the AI player system and passively observe the AI character interact with the game.
Supports both new sessions and continuing existing ones.

Usage:
    python launch_ai_observer.py --new              # Start new AI session
    python launch_ai_observer.py --continue         # Continue existing session
    python launch_ai_observer.py --web              # Launch web interface only
    python launch_ai_observer.py --demo             # Run simple terminal demo
"""

import argparse
import asyncio
import json
import sys
import time
import subprocess
import signal
import os
from pathlib import Path
import requests
from typing import Optional

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))


class AIObserver:
    def __init__(self):
        self.server_process = None
        self.session_id = None
        self.ai_name = None

    def start_server(self):
        """Start the FastAPI server."""
        print("🚀 Starting The Living Rusted Tankard server...")
        try:
            self.server_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "core.api:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8000",
                    "--reload",
                ],
                cwd=Path(__file__).parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for server to start
            max_retries = 30
            for i in range(max_retries):
                try:
                    response = requests.get("http://localhost:8000/", timeout=2)
                    if response.status_code == 200:
                        print("✅ Server started successfully!")
                        return True
                except:
                    print(f"⏳ Waiting for server... ({i+1}/{max_retries})")
                    time.sleep(1)

            print("❌ Server failed to start within timeout")
            return False

        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False

    def stop_server(self):
        """Stop the FastAPI server."""
        if self.server_process:
            print("\n🛑 Stopping server...")
            self.server_process.terminate()
            self.server_process.wait()
            print("✅ Server stopped")

    async def start_ai_session(
        self, personality: str = "curious_explorer", name: Optional[str] = None
    ):
        """Start a new AI player session."""
        print("🤖 Starting AI player session...")

        config = {"personality": personality, "thinking_speed": 2.0, "auto_play": True}

        if name:
            config["name"] = name

        try:
            response = requests.post(
                "http://localhost:8000/ai-player/start", json=config
            )
            if response.status_code == 200:
                result = response.json()
                self.session_id = result["session_id"]
                self.ai_name = result["ai_player"]["name"]
                print(
                    f"✅ AI player '{self.ai_name}' started with session: {self.session_id[:8]}..."
                )
                print(f"🎭 Personality: {result['ai_player']['personality']}")
                print(f"💬 Greeting: {result['ai_player']['greeting']}")
                return True
            else:
                print(f"❌ Failed to start AI session: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error starting AI session: {e}")
            return False

    async def observe_ai_stream(self):
        """Observe the AI player's actions via streaming."""
        if not self.session_id:
            print("❌ No active AI session")
            return

        print(f"\n👁️  Observing {self.ai_name}...")
        print("═" * 60)
        print("Press Ctrl+C to stop observing\n")

        action_count = 0

        try:
            while True:
                # Trigger AI action and stream the response
                url = f"http://localhost:8000/ai-player/action-stream/{self.session_id}"

                try:
                    response = requests.get(url, stream=True)
                    if response.status_code != 200:
                        print(f"❌ Stream error: {response.status_code}")
                        await asyncio.sleep(5)
                        continue

                    action_count += 1
                    print(f"\n🎬 Action #{action_count} - {time.strftime('%H:%M:%S')}")
                    print("-" * 40)

                    current_command = ""

                    for line in response.iter_lines():
                        if line:
                            line = line.decode("utf-8")
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])

                                    if data["type"] == "thinking":
                                        print(f"💭 {data['message']}")

                                    elif data["type"] == "generating":
                                        print(f"⚡ {data['message']}")

                                    elif data["type"] == "token":
                                        # Show typing effect
                                        current_command = data.get("partial_action", "")
                                        if current_command:
                                            print(
                                                f"\r🔤 Typing: {current_command}",
                                                end="",
                                                flush=True,
                                            )

                                    elif data["type"] == "action_ready":
                                        final_action = data["action"]
                                        print(f"\n✨ Final action: {final_action}")

                                    elif data["type"] == "executing":
                                        print(f"⚙️  {data['message']}")

                                    elif data["type"] == "result":
                                        output = data.get("output", "")
                                        print(f"📝 Game response:\n{output}")

                                        # Show some game state info
                                        game_state = data.get("game_state", {})
                                        if "player" in game_state:
                                            player = game_state["player"]
                                            print(
                                                f"💰 Gold: {player.get('gold', 0)} | 📍 Location: {player.get('location', 'unknown')}"
                                            )

                                    elif data["type"] == "complete":
                                        print("✅ Action completed")
                                        break

                                    elif data["type"] == "error":
                                        print(f"❌ Error: {data['message']}")
                                        break

                                except json.JSONDecodeError:
                                    continue

                    # Wait before next action
                    print(f"\n⏸️  Waiting {3} seconds before next action...")
                    await asyncio.sleep(3)

                except requests.exceptions.RequestException as e:
                    print(f"❌ Connection error: {e}")
                    print("🔄 Retrying in 5 seconds...")
                    await asyncio.sleep(5)

        except KeyboardInterrupt:
            print(f"\n\n👋 Stopped observing {self.ai_name}")

    async def continue_session(self, session_id: str):
        """Continue observing an existing session."""
        self.session_id = session_id

        # Get session status
        try:
            response = requests.get(
                f"http://localhost:8000/ai-player/status/{session_id}"
            )
            if response.status_code == 200:
                result = response.json()
                self.ai_name = result["ai_player"]["name"]
                print(f"✅ Continuing session for {self.ai_name}")
                print(f"📊 Actions so far: {result['ai_player']['action_count']}")
                return True
            else:
                print(f"❌ Session not found: {session_id}")
                return False
        except Exception as e:
            print(f"❌ Error accessing session: {e}")
            return False

    def list_personalities(self):
        """List available AI personalities."""
        try:
            response = requests.get("http://localhost:8000/ai-player/personalities")
            if response.status_code == 200:
                personalities = response.json()["personalities"]
                print("\n🎭 Available AI Personalities:")
                print("=" * 40)
                for p in personalities:
                    print(f"• {p['name']}")
                    print(f"  ID: {p['id']}")
                    print(f"  Style: {p['style']}")
                    print(f"  Decisions: {p['decision_pattern']}")
                    print()
                return personalities
            else:
                print("❌ Failed to fetch personalities")
                return []
        except Exception as e:
            print(f"❌ Error fetching personalities: {e}")
            return []

    def open_web_interface(self):
        """Open the web interface in browser."""
        import webbrowser

        print("🌐 Opening web interface...")
        webbrowser.open("http://localhost:8000/ai-demo")
        print("💡 Web interface opened at: http://localhost:8000/ai-demo")


async def run_simple_demo():
    """Run a simple terminal-based AI demo."""
    print("🎮 Running Simple AI Demo")
    print("=" * 40)

    try:
        from core.ai_player import AIPlayer, AIPlayerPersonality
        from core.game_state import GameState

        # Create AI player
        ai_player = AIPlayer(
            name="DemoGemma",
            personality=AIPlayerPersonality.CURIOUS_EXPLORER,
            model="gemma2:2b",
        )

        print(f"🤖 Created AI: {ai_player.name}")
        print(f"🎭 Personality: {ai_player.personality.value}")

        # Create game state
        game_state = GameState()
        ai_player.update_game_state(game_state.get_snapshot())

        print("\n👁️  Watching AI play...")
        print("Press Ctrl+C to stop\n")

        action_count = 0

        while action_count < 10:  # Limit to 10 actions for demo
            action_count += 1
            print(f"\n🎬 Action #{action_count}")
            print("-" * 30)

            # Generate action
            context = ai_player.get_game_context()
            print("💭 Thinking...")
            await asyncio.sleep(1)

            action = await ai_player.generate_action(context)
            print(f"✨ Action: {action}")

            # Execute action
            result = game_state.process_command(action)
            print(f"📝 Result: {result.get('message', 'No response')}")

            # Update AI state
            ai_player.update_game_state(game_state.get_snapshot())
            ai_player.record_action(action, "Demo action")

            await asyncio.sleep(3)

        print("\n✅ Demo completed!")

    except KeyboardInterrupt:
        print("\n👋 Demo stopped")
    except Exception as e:
        print(f"❌ Demo error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="AI Player Observer for The Living Rusted Tankard"
    )
    parser.add_argument("--new", action="store_true", help="Start new AI session")
    parser.add_argument(
        "--continue-session",
        type=str,
        metavar="SESSION_ID",
        help="Continue existing session",
    )
    parser.add_argument("--web", action="store_true", help="Launch web interface only")
    parser.add_argument("--demo", action="store_true", help="Run simple terminal demo")
    parser.add_argument(
        "--personality",
        default="curious_explorer",
        help="AI personality (default: curious_explorer)",
    )
    parser.add_argument("--name", help="AI character name")
    parser.add_argument(
        "--list-personalities", action="store_true", help="List available personalities"
    )

    args = parser.parse_args()

    observer = AIObserver()

    # Handle simple demo
    if args.demo:
        asyncio.run(run_simple_demo())
        return

    # Start server
    if not observer.start_server():
        print("❌ Cannot start without server")
        return

    try:
        # Handle personality listing
        if args.list_personalities:
            observer.list_personalities()
            return

        # Handle web interface only
        if args.web:
            print("🌐 Web interface available at:")
            print("• Main game: http://localhost:8000/")
            print("• AI Demo: http://localhost:8000/ai-demo")
            observer.open_web_interface()
            print("\nPress Ctrl+C to stop server...")
            while True:
                time.sleep(1)

        # Handle continue session
        elif args.continue_session:

            async def continue_and_observe():
                if await observer.continue_session(args.continue_session):
                    await observer.observe_ai_stream()

            asyncio.run(continue_and_observe())

        # Handle new session (default)
        else:

            async def start_and_observe():
                if await observer.start_ai_session(args.personality, args.name):
                    await observer.observe_ai_stream()

            asyncio.run(start_and_observe())

    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

    finally:
        observer.stop_server()


if __name__ == "__main__":
    main()
