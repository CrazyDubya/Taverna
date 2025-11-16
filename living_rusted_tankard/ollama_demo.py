#!/usr/bin/env python3
"""
Dynamic Ollama Demo - Shows AI Player and Game Narrator using local LLMs
This demo works with minimal dependencies (just requests)
"""

import json
import time
import random
from typing import Dict, Any, Optional, List
from enum import Enum

# We'll use urllib instead of requests to avoid dependency
import urllib.request
import urllib.error


class AIPlayerPersonality(Enum):
    CURIOUS_EXPLORER = "curious_explorer"
    CAUTIOUS_MERCHANT = "cautious_merchant"
    SOCIAL_BUTTERFLY = "social_butterfly"
    MYSTERIOUS_WANDERER = "mysterious_wanderer"


class OllamaClient:
    """Simple Ollama client using urllib (no external dependencies)"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def generate(
        self, prompt: str, model: str = "llama3.2:latest", temperature: float = 0.7
    ) -> str:
        """Generate text using Ollama"""
        url = f"{self.base_url}/api/generate"

        data = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False,
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "").strip()

        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return None


class GameNarrator:
    """Uses Ollama to generate dynamic game narration"""

    def __init__(self, ollama_client: OllamaClient, model: str = "llama3.2:latest"):
        self.ollama = ollama_client
        self.model = model

    def describe_scene(self, location: str, time_of_day: str, npcs: List[str]) -> str:
        """Generate a scene description"""
        prompt = """You are a narrator for a fantasy tavern game. Describe this scene vividly in 2-3 sentences:
Location: {location}
Time: {time_of_day}
NPCs present: {', '.join(npcs)}

Keep it atmospheric and immersive. Focus on sights, sounds, and smells."""

        response = self.ollama.generate(prompt, self.model, temperature=0.8)
        return (
            response
            or f"You find yourself in {location}. It's {time_of_day} and you see {', '.join(npcs)}."
        )

    def narrate_action(
        self, action: str, actor: str, target: Optional[str] = None
    ) -> str:
        """Narrate an action dynamically"""
        prompt = """You are a game narrator. Describe this action in 1-2 sentences:
Actor: {actor}
Action: {action}
{'Target: ' + target if target else ''}

Make it engaging and descriptive, as if from a fantasy novel."""

        response = self.ollama.generate(prompt, self.model, temperature=0.7)
        return response or f"{actor} performs {action}."


class DynamicAIPlayer:
    """AI Player that uses Ollama for decision making"""

    def __init__(
        self,
        name: str,
        personality: AIPlayerPersonality,
        ollama_client: OllamaClient,
        model: str = "llama3.2:latest",
    ):
        self.name = name
        self.personality = personality
        self.ollama = ollama_client
        self.model = model
        self.action_history = []

        self.personality_descriptions = {
            AIPlayerPersonality.CURIOUS_EXPLORER: "You are curious and adventurous, always eager to explore and learn new things.",
            AIPlayerPersonality.CAUTIOUS_MERCHANT: "You are careful and business-minded, always evaluating risks and opportunities.",
            AIPlayerPersonality.SOCIAL_BUTTERFLY: "You are friendly and outgoing, loving to meet people and hear their stories.",
            AIPlayerPersonality.MYSTERIOUS_WANDERER: "You are cryptic and philosophical, speaking in riddles and observing deeply.",
        }

    def decide_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Use Ollama to decide what action to take"""
        personality_desc = self.personality_descriptions[self.personality]

        # Build context from game state
        context = """You are {self.name}, an AI character in a fantasy tavern game.
Personality: {personality_desc}
Current location: {game_state.get('location', 'tavern')}
NPCs nearby: {', '.join(game_state.get('npcs_present', []))}
Your gold: {game_state.get('player_gold', 100)}
Your health: {game_state.get('player_health', 100)}

Available commands:
- look (observe your surroundings)
- interact [npc] talk (talk to an NPC)
- buy [item] (purchase something)
- jobs (check available work)
- status (check your status)
- inventory (check your items)
- wait (pass time)

Based on your personality and the situation, what ONE command would you like to execute?
Respond with a JSON object containing:
- "command": the exact command to execute
- "reasoning": why you chose this action (in character)

Example: {{"command": "look", "reasoning": "I want to see what mysteries this place holds."}}"""

        response = self.ollama.generate(context, self.model, temperature=0.9)

        # Try to parse JSON response
        try:
            # Extract JSON from response (Ollama might include extra text)
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                decision = json.loads(json_str)
                self.action_history.append(decision)
                return decision
        except:
            pass

        # Fallback if parsing fails
        fallback_actions = {
            AIPlayerPersonality.CURIOUS_EXPLORER: (
                "look",
                "I need to explore this place!",
            ),
            AIPlayerPersonality.CAUTIOUS_MERCHANT: (
                "status",
                "Let me check my resources first.",
            ),
            AIPlayerPersonality.SOCIAL_BUTTERFLY: ("look", "Who can I talk to here?"),
            AIPlayerPersonality.MYSTERIOUS_WANDERER: (
                "wait",
                "I shall observe in silence...",
            ),
        }

        command, reasoning = fallback_actions[self.personality]
        decision = {"command": command, "reasoning": reasoning}
        self.action_history.append(decision)
        return decision

    def speak(self, context: str) -> str:
        """Generate speech based on personality"""
        personality_desc = self.personality_descriptions[self.personality]

        prompt = """You are {self.name}, a character with this personality: {personality_desc}
Context: {context}

Respond with a single sentence that reflects your personality. Be creative and stay in character."""

        response = self.ollama.generate(prompt, self.model, temperature=0.9)
        return response or f"*{self.name} remains thoughtful*"


def run_ollama_demo():
    """Run the dynamic Ollama-powered demo"""
    print("=" * 70)
    print("🏰 THE LIVING RUSTED TANKARD - DYNAMIC OLLAMA DEMO 🏰")
    print("=" * 70)
    print()

    # Check Ollama connection
    print("🔌 Connecting to Ollama...")
    ollama = OllamaClient()

    # Test connection with a simple prompt
    test_response = ollama.generate(
        "Say 'Hello Tavern' if you can hear me", temperature=0.1
    )
    if not test_response:
        print(
            "❌ Could not connect to Ollama. Make sure it's running on localhost:11434"
        )
        print("   Run: ollama serve")
        return

    print("✅ Ollama connected successfully!")
    print()

    # Create game components
    narrator = GameNarrator(ollama)

    # Game state
    game_state = {
        "location": "The Rusted Tankard Tavern",
        "time_of_day": "evening",
        "npcs_present": [
            "Gene the Bartender",
            "Old Sailor Jim",
            "Mysterious Hooded Figure",
        ],
        "player_gold": 100,
        "player_health": 100,
    }

    # Generate initial scene description
    print("📖 NARRATOR:")
    print("-" * 70)
    scene_description = narrator.describe_scene(
        game_state["location"], game_state["time_of_day"], game_state["npcs_present"]
    )
    print(f"🌟 {scene_description}")
    print()

    # Create AI players with different personalities
    ai_players = [
        DynamicAIPlayer("Lyra", AIPlayerPersonality.CURIOUS_EXPLORER, ollama),
        DynamicAIPlayer("Marcus", AIPlayerPersonality.CAUTIOUS_MERCHANT, ollama),
        DynamicAIPlayer("Bella", AIPlayerPersonality.SOCIAL_BUTTERFLY, ollama),
        DynamicAIPlayer("Shadow", AIPlayerPersonality.MYSTERIOUS_WANDERER, ollama),
    ]

    # Demo each AI player
    for ai_player in ai_players:
        print("=" * 70)
        print(
            f"\n🎭 {ai_player.name} ({ai_player.personality.value}) enters the tavern..."
        )

        # AI introduces themselves
        intro = ai_player.speak("You just entered the tavern. Introduce yourself.")
        print(f'💬 {ai_player.name}: "{intro}"')
        print()

        # Make 2 decisions
        for turn in range(2):
            print(f"🎲 Turn {turn + 1}:")

            # AI decides action
            print("   🤔 Thinking...")
            decision = ai_player.decide_action(game_state)

            print(
                "   💭 Reasoning: \"{decision.get('reasoning', 'I act on instinct')}\""
            )
            print(f"   ▶️  Command: {decision.get('command', 'wait')}")

            # Narrator describes the action
            action_narration = narrator.narrate_action(
                decision.get("command", "wait"),
                ai_player.name,
                decision.get("command", "").split()[1]
                if len(decision.get("command", "").split()) > 1
                else None,
            )
            print(f"   📜 {action_narration}")

            # Brief pause between actions
            time.sleep(1)
            print()

    print("=" * 70)
    print("🎮 Demo Complete!")
    print()
    print("This demo showcases:")
    print("✅ Dynamic scene narration using Ollama")
    print("✅ AI players making decisions based on personality using LLM")
    print("✅ Natural language generation for character speech")
    print("✅ Context-aware action narration")
    print()
    print("In the full game, this would integrate with:")
    print("- Complete game state management")
    print("- Persistent NPC memories and relationships")
    print("- Complex quest and economy systems")
    print("- Multi-threaded async processing for smooth gameplay")


if __name__ == "__main__":
    run_ollama_demo()
