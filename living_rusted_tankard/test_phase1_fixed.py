#!/usr/bin/env python3
"""
FIXED PHASE 1 TEST - Properly handles NPC scheduling
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.game_state import GameState
import time


def test_phase1_with_npcs():
    """Test Phase 1 with proper NPC spawning."""
    print("🎭 PHASE 1 NARRATIVE TEST - NPC SCHEDULING FIXED")
    print("="*60)
    
    # Create game
    game = GameState()
    
    if not hasattr(game, 'story_orchestrator'):
        print("❌ Narrative systems not available")
        return 0
        
    print("✅ Phase 1 narrative systems initialized")
    
    # Check initial time
    current_hour = game.clock.current_time_hours % 24
    print(f"\n⏰ Starting time: {current_hour:.1f}:00")
    
    # Debug NPC schedules
    print("\n📅 NPC Schedules:")
    for npc_id, npc in game.npc_manager.npcs.items():
        schedule_str = ", ".join([f"{s[0]}-{s[1]}" for s in npc.schedule])
        print(f"   {npc.name}: {schedule_str}")
    
    # Wait until Gene's shift (16:00-04:00)
    if 4 <= current_hour < 16:
        hours_to_wait = 16 - current_hour
        print(f"\n⏳ Waiting {hours_to_wait:.1f} hours until Gene's shift...")
        result = game.process_command(f"wait {hours_to_wait}")
        print(f"   Result: {result['success']} - {result.get('message', '')[:100]}")
        
    # Force update and check
    current_hour = game.clock.current_time_hours % 24
    print(f"\n⏰ Current time after wait: {current_hour:.1f}:00")
    
    # Check NPCs
    present_npcs = game.npc_manager.get_present_npcs()
    print(f"\n👥 NPCs present: {len(present_npcs)}")
    for npc in present_npcs:
        print(f"   - {npc.name} (present: {npc.is_present})")
        
    # If no NPCs, debug why
    if len(present_npcs) == 0:
        print("\n🔍 Debugging NPC presence:")
        for npc_id, npc in game.npc_manager.npcs.items():
            hour = game.clock.current_time_hours % 24
            day = int(game.clock.current_time_hours // 24)
            scheduled = any(
                (start <= hour < end) if start < end else (hour >= start or hour < end)
                for start, end in npc.schedule
            )
            print(f"   {npc.name}:")
            print(f"     - Current hour: {hour:.1f}, Day: {day}")
            print(f"     - Schedule: {npc.schedule}")
            print(f"     - Scheduled now: {scheduled}")
            print(f"     - Is present: {npc.is_present}")
            print(f"     - Last visit day: {npc.last_visit_day}")
            print(f"     - Visit frequency: {npc.visit_frequency}")
    
    # Try a simple narrative flow
    print("\n🎮 TESTING NARRATIVE FLOW")
    print("-" * 40)
    
    # Simple commands that should work
    test_commands = [
        ("look", "Survey the tavern"),
        ("status", "Check player status"),
        ("inventory", "Check inventory"),
        ("buy ale", "Buy a drink"),
        ("buy bread", "Buy some food"),
        ("wait 1", "Wait an hour"),
        ("look", "Look again")
    ]
    
    success_count = 0
    for cmd, desc in test_commands:
        print(f"\n[{desc}] Command: {cmd}")
        result = game.process_command(cmd)
        if result['success']:
            success_count += 1
            msg = result.get('message', '')[:150]
            print(f"✓ {msg}...")
        else:
            print(f"✗ {result.get('message', 'Failed')}")
    
    # Check narrative status
    print("\n📊 NARRATIVE STATUS CHECK")
    print("-" * 40)
    
    status = game.get_narrative_status()
    
    # Story orchestrator
    print(f"📚 Story Orchestrator:")
    print(f"   Tension: {status.get('overall_tension', 0):.2f}")
    print(f"   Engagement: {status.get('player_engagement', 0):.2f}")
    print(f"   Active Threads: {status.get('active_threads', 0)}")
    
    # Consequences
    cons = status.get('consequence_engine', {})
    print(f"\n⚡ Consequences:")
    print(f"   Actions: {cons.get('total_actions_tracked', 0)}")
    print(f"   Triggered: {cons.get('total_consequences_triggered', 0)}")
    
    # Character systems
    print(f"\n💬 Character Systems:")
    character_count = 0
    if hasattr(game, 'character_memory_manager'):
        for npc_id in game.npc_manager.npcs:
            memory = game.character_memory_manager.get_or_create_memory(npc_id, game.npc_manager.npcs[npc_id].name)
            if memory:
                character_count += 1
    print(f"   Character memories created: {character_count}")
    
    # Calculate score
    score = 0
    score += min(20, success_count * 3)  # Command success
    score += min(20, status.get('player_engagement', 0) * 20)  # Engagement
    score += min(20, cons.get('total_actions_tracked', 0) * 2)  # Action tracking
    score += min(20, character_count * 5)  # Character systems
    score += min(20, len(present_npcs) * 10)  # NPC presence
    
    print(f"\n🏆 NARRATIVE READINESS: {score}/100")
    
    return score


if __name__ == "__main__":
    score = test_phase1_with_npcs()
    print(f"\n{'='*60}")
    print(f"TEST COMPLETE - Score: {score}/100")
    if score < 50:
        print("⚠️  NPCs not spawning properly - scheduling system needs investigation")
    print(f"{'='*60}")