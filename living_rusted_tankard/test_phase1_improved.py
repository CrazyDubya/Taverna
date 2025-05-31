#!/usr/bin/env python3
"""
IMPROVED PHASE 1 INTEGRATION TEST
Tests narrative systems with proper NPC scheduling and interaction flow.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.game_state import GameState
import time


def test_phase1_improved():
    """Test Phase 1 narrative engine with timing-aware interactions."""
    print("🎭 IMPROVED PHASE 1 NARRATIVE ENGINE TEST")
    print("="*60)
    
    # Create game with complete narrative systems
    game = GameState()
    
    # Check if all systems are available
    if not hasattr(game, 'story_orchestrator'):
        print("❌ Complete narrative systems not available")
        return 0
    
    print("✅ Complete Phase 1 narrative engine initialized")
    
    # Get current time and adjust to when NPCs are present
    current_time = game.clock.current_time_hours
    current_hour = current_time % 24
    print(f"⏰ Current time: {current_hour:.1f}:00")
    
    # Gene works 16:00-04:00, Serena 10:00-16:00 and 18:00-22:00
    # Wait until Gene's shift starts if needed
    if current_hour < 16:
        hours_to_wait = 16 - current_hour
        print(f"⏳ Waiting {hours_to_wait:.1f} hours for Gene's shift...")
        game.process_command(f"wait {hours_to_wait}")
    elif current_hour >= 4 and current_hour < 16:
        hours_to_wait = 16 - current_hour
        print(f"⏳ Waiting {hours_to_wait:.1f} hours for Gene's shift...")
        game.process_command(f"wait {hours_to_wait}")
    
    # Update NPCs to ensure they spawn
    game.npc_manager.update_all_npcs(game.clock.current_time_hours)
    
    # Check who's present
    present_npcs = game.npc_manager.get_present_npcs()
    print(f"\n👥 NPCs present: {len(present_npcs)}")
    for npc in present_npcs:
        print(f"   - {npc.name} ({npc.npc_type.name})")
    
    # Get initial narrative status
    initial_status = game.get_narrative_status()
    print(f"\n📊 Initial Narrative State:")
    print(f"   Tension Level: {initial_status.get('tension_level', 'unknown')}")
    print(f"   Player Engagement: {initial_status.get('player_engagement', 0):.2f}")
    print(f"   Active Threads: {initial_status.get('active_threads', 0)}")
    
    # Test comprehensive story emergence
    print(f"\n🎮 STORY EMERGENCE TEST")
    print("-" * 40)
    
    # Improved action sequence that works with NPC schedules
    story_actions = [
        ("look", "👀 Survey the tavern"),
        ("npcs", "👥 Check who's around"),
        ("interact gene_bartender talk", "💬 First conversation with Gene"),
        ("interact gene_bartender talk The old days", "💬 Ask about the old days"),
        ("buy ale from gene", "💰 Buy a drink"),
        ("interact gene_bartender talk", "💬 Post-purchase chat"),
        ("wait 2", "⏰ Pass some time"),
        ("interact serena_waitress talk", "💬 Talk to Serena (if present)"),
        ("buy bread from serena", "💰 Buy food from Serena"),
        ("interact gene_bartender talk Rumors in town", "💬 Ask Gene about rumors"),
        ("wait 1", "⏰ More time passes"),
        ("look", "👀 Check environment again"),
        ("interact gene_bartender talk", "💬 Build relationship with Gene"),
        ("help gene_bartender", "🤝 Offer to help Gene"),
        ("interact gene_bartender talk The mysterious locked door", "💬 Ask about the door")
    ]
    
    successful_actions = 0
    total_actions = len(story_actions)
    narrative_moments = []
    
    for i, (command, description) in enumerate(story_actions):
        print(f"\n[{i+1:2d}] {description}")
        print(f"     Command: {command}")
        
        result = game.process_command(command)
        
        if result['success']:
            successful_actions += 1
            message = result.get('message', '')
            # Truncate for readability
            if len(message) > 200:
                message = message[:200] + "..."
            print(f"     ✓ {message}")
            
            # Track narrative moments
            if any(phrase in message.lower() for phrase in 
                   ['remember', 'reputation', 'relationship', 'quest', 'story', 
                    'consequence', 'tension', 'trust', 'mood']):
                narrative_moments.append((i+1, command, message[:100]))
                print(f"     🎭 Narrative moment detected!")
        else:
            print(f"     ✗ {result.get('message', 'Failed')}")
        
        # Show narrative evolution every 5 actions
        if (i + 1) % 5 == 0:
            status = game.get_narrative_status()
            print(f"     📈 Narrative Update:")
            print(f"        Tension: {status.get('tension_level', 'unknown')}")
            print(f"        Engagement: {status.get('player_engagement', 0):.2f}")
            print(f"        Active Threads: {status.get('active_threads', 0)}")
            print(f"        Story Moments: {len(status.get('recent_story_moments', []))}")
    
    # Final analysis
    print(f"\n🎯 FINAL NARRATIVE ANALYSIS")
    print("="*60)
    
    final_status = game.get_narrative_status()
    
    print(f"📊 Story Orchestrator Status:")
    print(f"   Tension: {final_status.get('overall_tension', 0):.2f}")
    print(f"   Engagement: {final_status.get('player_engagement', 0):.2f}")
    print(f"   Active Threads: {final_status.get('active_threads', 0)}")
    print(f"   Story Moments: {len(final_status.get('recent_story_moments', []))}")
    
    print(f"\n⚡ Consequence Engine:")
    cons_stats = final_status.get('consequence_engine', {})
    print(f"   Actions Tracked: {cons_stats.get('total_actions_tracked', 0)}")
    print(f"   Consequences: {cons_stats.get('total_consequences_triggered', 0)}")
    print(f"   Active Chains: {cons_stats.get('active_chains', 0)}")
    
    print(f"\n🎯 Quest System:")
    quest_stats = final_status.get('quest_generator', {})
    print(f"   Generated: {quest_stats.get('total_generated', 0)}")
    print(f"   Active: {quest_stats.get('active_quests', 0)}")
    available_quests = game.get_available_quests()
    if available_quests:
        print(f"   Available: {len(available_quests)}")
        for q in available_quests[:3]:
            print(f"     - {q.get('title', 'Unknown')} ({q.get('type', '?')})")
    
    print(f"\n💬 Character Relationships:")
    relationships = final_status.get('relationships', {})
    for npc_id, rel_info in relationships.items():
        if rel_info.get('interactions', 0) > 0:
            print(f"   {npc_id}: {rel_info.get('interactions', 0)} interactions, "
                  f"relationship: {rel_info.get('relationship_score', 0):.2f}")
    
    print(f"\n🎭 Narrative Moments Captured: {len(narrative_moments)}")
    for idx, cmd, msg in narrative_moments[:5]:
        print(f"   [{idx}] {cmd}: {msg}...")
    
    # Calculate improved score
    score = calculate_improved_score(
        final_status, 
        successful_actions, 
        total_actions,
        narrative_moments
    )
    
    print(f"\n🏆 NARRATIVE READINESS SCORE: {score}/100")
    print(f"   Success Rate: {successful_actions}/{total_actions} ({successful_actions/total_actions*100:.1f}%)")
    print(f"   Narrative Moments: {len(narrative_moments)}")
    print(f"   {get_score_description(score)}")
    
    # Test persistence
    print(f"\n💾 Testing Narrative Persistence...")
    save_success = game.save_narrative_state()
    print(f"   Save: {'✅' if save_success else '❌'}")
    
    return score


def calculate_improved_score(status, successful_actions, total_actions, narrative_moments):
    """Calculate narrative readiness score with improved metrics."""
    score = 0
    
    # Command success rate (20 points)
    success_rate = successful_actions / max(1, total_actions)
    score += success_rate * 20
    
    # Narrative moments (20 points)
    moment_score = min(20, len(narrative_moments) * 4)
    score += moment_score
    
    # Engagement and tension (15 points)
    engagement = status.get('player_engagement', 0)
    tension = status.get('overall_tension', 0)
    score += (engagement * 10) + (tension * 5)
    
    # Consequence system activity (15 points)
    cons_stats = status.get('consequence_engine', {})
    actions = cons_stats.get('total_actions_tracked', 0)
    consequences = cons_stats.get('total_consequences_triggered', 0)
    if actions > 0:
        cons_ratio = min(1.0, consequences / (actions * 0.3))  # Expect ~30% to trigger
        score += cons_ratio * 15
    
    # Quest activity (10 points)
    quest_stats = status.get('quest_generator', {})
    quests = quest_stats.get('total_generated', 0)
    active = quest_stats.get('active_quests', 0)
    score += min(10, (quests * 3) + (active * 2))
    
    # Relationships (10 points)
    relationships = status.get('relationships', {})
    active_relationships = sum(1 for r in relationships.values() 
                              if r.get('interactions', 0) > 0)
    total_interactions = sum(r.get('interactions', 0) 
                            for r in relationships.values())
    score += min(10, (active_relationships * 3) + (total_interactions * 0.5))
    
    # Story threads (10 points)
    threads = status.get('active_threads', 0)
    moments = len(status.get('recent_story_moments', []))
    score += min(10, (threads * 3) + (moments * 1))
    
    return min(100, int(score))


def get_score_description(score):
    """Get description based on score."""
    if score >= 90:
        return "🌟 LEGENDARY - Ready to share! Rich narrative experience"
    elif score >= 80:
        return "🔥 EXCELLENT - Nearly ready, compelling storytelling"
    elif score >= 70:
        return "✨ GOOD - Strong foundation, needs polish"
    elif score >= 60:
        return "📈 PROMISING - Core systems working well"
    elif score >= 50:
        return "🔧 FUNCTIONAL - Basic narrative emerging"
    elif score >= 40:
        return "🏗️ DEVELOPING - Systems connected but limited"
    elif score >= 30:
        return "⚠️ EARLY - Narrative potential visible"
    else:
        return "🚧 FOUNDATIONAL - Core systems need work"


if __name__ == "__main__":
    score = test_phase1_improved()
    print(f"\n{'='*60}")
    print(f"🎉 TEST COMPLETE - Score: {score}/100")
    print(f"{'='*60}")