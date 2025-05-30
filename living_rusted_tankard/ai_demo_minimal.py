#!/usr/bin/env python3
"""
Minimal AI Player Demo - Works without external dependencies
Shows how the AI player makes decisions based on personality
"""

import random
import time
import json
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional

# Mock the personality enum
class AIPlayerPersonality(Enum):
    CURIOUS_EXPLORER = "curious_explorer"
    CAUTIOUS_MERCHANT = "cautious_merchant" 
    SOCIAL_BUTTERFLY = "social_butterfly"
    MYSTERIOUS_WANDERER = "mysterious_wanderer"

@dataclass
class AIPlayerAction:
    command: str
    reasoning: str
    personality_trait: str
    timestamp: float

class MockAIPlayer:
    """Simplified AI Player that demonstrates decision making without LLM"""
    
    def __init__(self, name: str = "Gemma", personality: AIPlayerPersonality = AIPlayerPersonality.CURIOUS_EXPLORER):
        self.name = name
        self.personality = personality
        self.action_history: List[AIPlayerAction] = []
        self.is_active = True
        
        # Personality-based behavior patterns
        self.personality_traits = {
            AIPlayerPersonality.CURIOUS_EXPLORER: {
                "preferred_commands": ["look", "read notice board", "interact", "jobs", "status", "inventory"],
                "interaction_style": "eager and inquisitive",
                "decision_pattern": "always chooses the most interesting option",
                "greeting": f"Hello! I'm {name}, a curious traveler always seeking new adventures!",
                "example_actions": [
                    ("look", "I want to see what's around me!"),
                    ("read notice board", "There might be interesting quests!"),
                    ("interact gene_bartender talk", "I'd love to hear local stories!"),
                    ("jobs", "What work is available here?"),
                    ("inventory", "Let me check what I'm carrying.")
                ]
            },
            AIPlayerPersonality.CAUTIOUS_MERCHANT: {
                "preferred_commands": ["status", "inventory", "buy", "jobs", "work"],
                "interaction_style": "careful and business-minded", 
                "decision_pattern": "evaluates cost-benefit before acting",
                "greeting": f"Greetings. I am {name}, a merchant who values careful planning.",
                "example_actions": [
                    ("status", "I should check my resources first."),
                    ("inventory", "What goods do I have to trade?"),
                    ("jobs", "I need to find profitable work."),
                    ("interact gene_bartender talk", "Perhaps they know of business opportunities."),
                    ("buy ale", "A small investment in local relations.")
                ]
            },
            AIPlayerPersonality.SOCIAL_BUTTERFLY: {
                "preferred_commands": ["interact", "read notice board", "look", "jobs"],
                "interaction_style": "friendly and talkative",
                "decision_pattern": "prioritizes social interactions",
                "greeting": f"Hi there! I'm {name}! I love meeting new people!",
                "example_actions": [
                    ("interact gene_bartender talk", "I'd love to chat with them!"),
                    ("look", "Who else is here to talk to?"),
                    ("read notice board", "Maybe there are social events!"),
                    ("interact old_sailor greet", "Hello there, friend!"),
                    ("help", "How can I help around here?")
                ]
            },
            AIPlayerPersonality.MYSTERIOUS_WANDERER: {
                "preferred_commands": ["look", "wait", "status", "read notice board"],
                "interaction_style": "cryptic and thoughtful",
                "decision_pattern": "observes before acting",
                "greeting": f"I am {name}... a wanderer seeking hidden truths.",
                "example_actions": [
                    ("look", "I observe the shadows and the light..."),
                    ("wait", "Patience reveals what haste conceals..."),
                    ("status", "Know thyself, as the ancients say..."),
                    ("read notice board", "Written words hold power..."),
                    ("look", "The room speaks to those who listen...")
                ]
            }
        }
    
    def make_decision(self, game_state: Dict) -> Dict:
        """Make a decision based on personality and game state"""
        traits = self.personality_traits[self.personality]
        
        # Simulate thinking time
        thinking_time = random.uniform(0.5, 1.5)
        time.sleep(thinking_time)
        
        # Choose an action based on personality
        action, reasoning = random.choice(traits["example_actions"])
        
        # Create action record
        ai_action = AIPlayerAction(
            command=action,
            reasoning=reasoning,
            personality_trait=traits["interaction_style"],
            timestamp=time.time()
        )
        
        self.action_history.append(ai_action)
        
        return {
            "command": action,
            "reasoning": reasoning,
            "personality": self.personality.value,
            "thinking_time": thinking_time
        }
    
    def introduce_self(self) -> str:
        """Get the AI's introduction based on personality"""
        return self.personality_traits[self.personality]["greeting"]

# Demo game state
def create_mock_game_state():
    return {
        "location": "The Rusted Tankard Tavern",
        "time": "evening",
        "npcs_present": ["gene_bartender", "old_sailor", "mysterious_hooded_figure"],
        "player_gold": 100,
        "player_health": 100,
        "available_actions": ["look", "interact", "buy", "jobs", "wait"]
    }

# Run the demo
def run_ai_demo():
    print("=" * 60)
    print("THE LIVING RUSTED TANKARD - AI PLAYER DEMO")
    print("=" * 60)
    print()
    
    # Create game state
    game_state = create_mock_game_state()
    print("📍 Location:", game_state["location"])
    print("🌙 Time:", game_state["time"])
    print("👥 NPCs Present:", ", ".join(game_state["npcs_present"]))
    print()
    
    # Demo each personality
    personalities = [
        AIPlayerPersonality.CURIOUS_EXPLORER,
        AIPlayerPersonality.CAUTIOUS_MERCHANT,
        AIPlayerPersonality.SOCIAL_BUTTERFLY,
        AIPlayerPersonality.MYSTERIOUS_WANDERER
    ]
    
    for personality in personalities:
        print("-" * 60)
        ai_player = MockAIPlayer(name=f"AI_{personality.value}", personality=personality)
        
        print(f"\n🤖 {ai_player.name} enters the tavern...")
        print(f"💭 {ai_player.introduce_self()}")
        print()
        
        # Make 3 decisions
        for i in range(3):
            print(f"Turn {i+1}:")
            decision = ai_player.make_decision(game_state)
            
            print(f"  ⏰ (Thinking for {decision['thinking_time']:.1f}s...)")
            print(f"  💡 \"{decision['reasoning']}\"")
            print(f"  ▶️  {decision['command']}")
            print()
            
            # Simulate game response
            if "look" in decision['command']:
                print("  📜 The tavern is warm and inviting, filled with the sounds of laughter.")
            elif "interact" in decision['command']:
                npc = decision['command'].split()[1] if len(decision['command'].split()) > 1 else "someone"
                print(f"  💬 {npc} nods in acknowledgment.")
            elif "jobs" in decision['command']:
                print("  📋 Available jobs: Clean tables (5g), Deliver message (10g)")
            elif "inventory" in decision['command']:
                print("  🎒 Inventory: Basic clothes, 10 gold, small dagger")
            elif "status" in decision['command']:
                print("  📊 Health: 100/100, Gold: 100, Level: 1")
            elif "wait" in decision['command']:
                print("  ⏳ Time passes quietly...")
            print()
    
    print("=" * 60)
    print("Demo complete! Each AI personality made unique decisions.")
    print("In the real game, these would connect to Ollama LLM for dynamic responses.")

if __name__ == "__main__":
    run_ai_demo()