#!/usr/bin/env python3
"""
Test how our current system handles narrative-focused gameplay.
Based on the three narratives understanding.
"""

import logging
import time
from typing import List, Dict, Any

logging.basicConfig(level=logging.ERROR)

from core.game_state import GameState


class NarrativeRealityTest:
    """Test current system against narrative expectations."""

    def __init__(self):
        self.game = GameState()
        self.narrative_log = []
        self.relationship_tracking = {}
        self.story_threads = {}

    def run_narrative_test(self) -> Dict[str, Any]:
        """Run a focused narrative test based on Elena's journey."""
        print("🎭 NARRATIVE REALITY TEST")
        print("Testing current system against story-driven gameplay expectations")
        print("=" * 70)

        # Simulate Elena's journey focusing on narrative moments
        narrative_commands = [
            # Arrival and first impressions
            ("I step into the tavern and look around", "arrival", "Setting the scene"),
            (
                "I approach the bar and greet the bartender",
                "social",
                "First NPC contact",
            ),
            ("I ask about this establishment", "information", "World building"),
            # Exploration and discovery
            (
                "I'm curious about the woman in the corner",
                "observation",
                "NPC interest",
            ),
            (
                "I walk over and ask if I can sit with her",
                "social",
                "Relationship building",
            ),
            (
                "I ask her about what she's working on",
                "social",
                "Story thread discovery",
            ),
            # Building relationships
            (
                "I tell her I've traveled many trade routes",
                "personal",
                "Sharing expertise",
            ),
            (
                "I offer to help with her business problems",
                "helpful",
                "Active assistance",
            ),
            ("I share my knowledge of northern routes", "expertise", "Providing value"),
            # Deepening connections
            (
                "I return the next day and greet Sarah",
                "continuity",
                "Relationship persistence",
            ),
            ("I ask Gene about the tavern's history", "lore", "World depth"),
            (
                "I check on how Sarah's business is doing",
                "follow_up",
                "Consequence tracking",
            ),
            # Mystery and complexity
            (
                "I notice the man in the corner and his strange coins",
                "mystery",
                "Observation skills",
            ),
            (
                "I carefully approach Marcus and ask to join him",
                "social_risk",
                "Trust building",
            ),
            ("I ask Marcus about his travels", "personal", "Character development"),
            # Difficult choices
            (
                "I discuss Marcus's offer with Gene privately",
                "complex",
                "Moral complexity",
            ),
            (
                "I try to help Marcus while protecting Gene's neutrality",
                "values",
                "Character consistency",
            ),
            # Legacy and impact
            ("I reflect on how this place has changed me", "growth", "Self-awareness"),
            ("I make plans to return regularly", "commitment", "Ongoing relationship"),
            (
                "I leave something valuable for future travelers",
                "legacy",
                "Lasting impact",
            ),
        ]

        results = {
            "narrative_moments": [],
            "relationship_tracking": {},
            "story_continuity": {},
            "emotional_resonance": {},
            "success_metrics": {},
        }

        print(f"Running {len(narrative_commands)} narrative-focused commands:\n")

        for i, (command, category, intent) in enumerate(narrative_commands, 1):
            print(f'{i:2d}. [{category.upper()}] "{command}"')
            print(f"    Intent: {intent}")

            # Execute command
            start_time = time.time()
            result = self.game.process_command(command)
            response_time = time.time() - start_time

            success = result.get("success", False)
            message = result.get("message", "")

            # Analyze response quality for narrative purposes
            narrative_quality = self._analyze_narrative_quality(
                command, message, category
            )

            moment_result = {
                "command": command,
                "category": category,
                "intent": intent,
                "success": success,
                "message": message,
                "response_time": response_time,
                "narrative_quality": narrative_quality,
            }

            results["narrative_moments"].append(moment_result)

            # Show result
            if success:
                quality_indicator = "🌟" if narrative_quality["immersive"] else "✅"
                print(f"    {quality_indicator} {message[:80]}...")
            else:
                print(f"    ❌ {message[:80]}...")

            # Track narrative elements
            self._track_narrative_elements(command, result, category)

            print()

        # Analyze overall narrative performance
        results.update(self._analyze_overall_narrative_performance())

        return results

    def _analyze_narrative_quality(
        self, command: str, response: str, category: str
    ) -> Dict[str, Any]:
        """Analyze how well the response serves narrative purposes."""
        quality = {
            "immersive": False,
            "character_aware": False,
            "story_advancing": False,
            "emotionally_resonant": False,
            "world_building": False,
        }

        response_lower = response.lower()

        # Check for immersive language
        immersive_indicators = [
            "you see",
            "you notice",
            "you feel",
            "the atmosphere",
            "warmly",
            "carefully",
        ]
        quality["immersive"] = any(
            indicator in response_lower for indicator in immersive_indicators
        )

        # Check for character awareness (NPCs mentioned by name)
        character_indicators = ["gene", "sarah", "marcus", "bartender"]
        quality["character_aware"] = any(
            char in response_lower for char in character_indicators
        )

        # Check for story advancement
        story_indicators = ["tells you", "mentions", "explains", "reveals", "suggests"]
        quality["story_advancing"] = any(
            indicator in response_lower for indicator in story_indicators
        )

        # Check for emotional resonance
        emotion_indicators = [
            "grateful",
            "pleased",
            "concerned",
            "interested",
            "surprised",
        ]
        quality["emotionally_resonant"] = any(
            emotion in response_lower for emotion in emotion_indicators
        )

        # Check for world building
        world_indicators = [
            "tavern",
            "establishment",
            "history",
            "tradition",
            "community",
        ]
        quality["world_building"] = any(
            indicator in response_lower for indicator in world_indicators
        )

        return quality

    def _track_narrative_elements(self, command: str, result: Dict, category: str):
        """Track elements important for narrative continuity."""
        message = result.get("message", "").lower()

        # Track NPC mentions
        npcs = ["gene", "sarah", "marcus"]
        for npc in npcs:
            if npc in message:
                if npc not in self.relationship_tracking:
                    self.relationship_tracking[npc] = {
                        "interactions": 0,
                        "depth": "shallow",
                    }
                self.relationship_tracking[npc]["interactions"] += 1

        # Track story thread development
        if category in ["social", "helpful", "follow_up"]:
            thread_key = f"{category}_development"
            if thread_key not in self.story_threads:
                self.story_threads[thread_key] = 0
            self.story_threads[thread_key] += 1

    def _analyze_overall_narrative_performance(self) -> Dict[str, Any]:
        """Analyze how well the system supports narrative gameplay."""

        total_moments = len(self.narrative_log)

        # Calculate narrative metrics
        immersive_responses = sum(
            1
            for moment in self.narrative_log
            if moment.get("narrative_quality", {}).get("immersive", False)
        )

        character_aware_responses = sum(
            1
            for moment in self.narrative_log
            if moment.get("narrative_quality", {}).get("character_aware", False)
        )

        story_advancing_responses = sum(
            1
            for moment in self.narrative_log
            if moment.get("narrative_quality", {}).get("story_advancing", False)
        )

        success_rate = (
            sum(1 for moment in self.narrative_log if moment.get("success", False))
            / total_moments
            * 100
        )

        return {
            "success_metrics": {
                "basic_success_rate": success_rate,
                "immersion_rate": (immersive_responses / total_moments * 100)
                if total_moments > 0
                else 0,
                "character_awareness_rate": (
                    character_aware_responses / total_moments * 100
                )
                if total_moments > 0
                else 0,
                "story_advancement_rate": (
                    story_advancing_responses / total_moments * 100
                )
                if total_moments > 0
                else 0,
            },
            "relationship_tracking": self.relationship_tracking,
            "story_threads": self.story_threads,
        }

    def print_narrative_analysis(self, results: Dict[str, Any]):
        """Print analysis focused on narrative capabilities."""
        print("\n🎭 NARRATIVE ANALYSIS RESULTS")
        print("=" * 50)

        metrics = results["success_metrics"]

        print("📊 NARRATIVE PERFORMANCE METRICS:")
        print(f"   Basic Success Rate: {metrics['basic_success_rate']:.1f}%")
        print(f"   Immersion Quality: {metrics['immersion_rate']:.1f}%")
        print(f"   Character Awareness: {metrics['character_awareness_rate']:.1f}%")
        print(f"   Story Advancement: {metrics['story_advancement_rate']:.1f}%")

        print("\n👥 RELATIONSHIP TRACKING:")
        relationships = results["relationship_tracking"]
        if relationships:
            for npc, data in relationships.items():
                print(
                    f"   {npc.title()}: {data['interactions']} interactions ({data['depth']} relationship)"
                )
        else:
            print("   No meaningful NPC relationships detected")

        print("\n📖 STORY THREAD DEVELOPMENT:")
        threads = results["story_threads"]
        if threads:
            for thread, count in threads.items():
                print(f"   {thread.replace('_', ' ').title()}: {count} moments")
        else:
            print("   No story threads detected")

        # Identify biggest gaps
        print("\n🚨 NARRATIVE GAPS IDENTIFIED:")

        if metrics["character_awareness_rate"] < 30:
            print(
                "   • Low character awareness - NPCs not sufficiently present in responses"
            )

        if metrics["story_advancement_rate"] < 25:
            print("   • Limited story advancement - responses don't develop narratives")

        if metrics["immersion_rate"] < 40:
            print("   • Poor immersion - responses lack atmospheric detail")

        if not relationships:
            print(
                "   • No relationship tracking - system doesn't remember character interactions"
            )

        # Calculate narrative readiness score
        narrative_score = (
            metrics["basic_success_rate"] * 0.3
            + metrics["immersion_rate"] * 0.3
            + metrics["character_awareness_rate"] * 0.2
            + metrics["story_advancement_rate"] * 0.2
        )

        print(f"\n🎯 NARRATIVE READINESS SCORE: {narrative_score:.1f}/100")

        if narrative_score >= 75:
            print("   🌟 EXCELLENT - Ready for story-driven gameplay!")
        elif narrative_score >= 60:
            print("   ✅ GOOD - Solid foundation, needs narrative polish")
        elif narrative_score >= 45:
            print("   ⚠️ MODERATE - Basic functionality, major narrative gaps")
        else:
            print("   🚨 POOR - Significant work needed for narrative gameplay")

        return narrative_score


def main():
    """Run the narrative reality test."""
    tester = NarrativeRealityTest()
    results = tester.run_narrative_test()
    score = tester.print_narrative_analysis(results)

    print("\n🎪 REALITY CHECK:")
    print(f"Current system narrative readiness: {score:.1f}%")
    print("Target for story-driven gameplay: 75%+")
    print(f"Gap to close: {max(0, 75 - score):.1f} percentage points")


if __name__ == "__main__":
    main()
