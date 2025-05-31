#!/usr/bin/env python3
"""Quick test to see score improvement after NPC fix"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.game_state import GameState

def quick_score_test():
    print("🚀 QUICK SCORE TEST AFTER NPC FIX")
    print("="*50)
    
    game = GameState()
    
    # Force NPCs present
    for npc_id in ["gene_bartender", "serena_waitress"]:
        npc = game.npc_manager.get_npc(npc_id)
        if npc:
            npc.is_present = True
    
    # Test interaction-heavy commands
    test_commands = [
        "look",
        "interact gene_bartender talk", 
        "interact gene_bartender talk The old days",
        "buy ale",
        "interact serena_waitress talk",
        "buy bread", 
        "wait 1",
        "interact gene_bartender talk Rumors in town"
    ]
    
    success_count = 0
    for cmd in test_commands:
        result = game.process_command(cmd)
        if result['success']:
            success_count += 1
            print(f"✓ {cmd}")
        else:
            print(f"✗ {cmd}")
    
    # Quick score calculation
    status = game.get_narrative_status()
    
    score = 0
    score += min(20, success_count * 2.5)  # Command success
    score += min(20, status.get('player_engagement', 0) * 20)  # Engagement
    cons = status.get('consequence_engine', {})
    score += min(15, cons.get('total_actions_tracked', 0) * 1.5)  # Action tracking
    relationships = status.get('relationships', {})
    active_rels = sum(1 for r in relationships.values() if r.get('interactions', 0) > 0)
    score += min(15, active_rels * 5)  # Relationships
    
    print(f"\n📊 Quick Score Estimate: {score}/100")
    print(f"   Success rate: {success_count}/{len(test_commands)} ({success_count/len(test_commands)*100:.1f}%)")
    print(f"   Engagement: {status.get('player_engagement', 0):.2f}")
    print(f"   Actions tracked: {cons.get('total_actions_tracked', 0)}")
    print(f"   Active relationships: {active_rels}")
    
    return score

if __name__ == "__main__":
    quick_score_test()