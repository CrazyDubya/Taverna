#!/usr/bin/env python3
"""
Run AI player analysis to understand what LLM parser needs.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Any
from core.ai_player import AIPlayer, AIPlayerPersonality
from core.game_state import GameState

# Set up logging to capture details
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class LLMParsingAnalyzer:
    def __init__(self):
        self.command_attempts = []
        self.parsing_failures = []
        self.successful_patterns = []
        self.game_context_snapshots = []
        
    async def run_analysis(self, turns: int = 300):
        """Run AI player analysis to understand LLM parsing needs."""
        print(f"🧙 Starting AI Player Analysis for {turns} turns")
        print("🎯 Focus: Understanding what long-Gemma LLM needs for parsing")
        print("="*70)
        
        # Create game and AI player
        game = GameState()
        ai_player = AIPlayer(
            name="TestGemma",
            personality=AIPlayerPersonality.CURIOUS_EXPLORER,
            model="gemma2:2b"  # AI player uses gemma2:2b as default
        )
        
        print(f"📊 AI Player using model: {ai_player.model}")
        print(f"🔧 Game parser using model: {game.llm_parser.llm_model}")
        
        # Initialize AI player state
        ai_player.session_id = "analysis_session"
        
        try:
            for turn in range(turns):
                if turn % 50 == 0:
                    print(f"📈 Progress: {turn}/{turns} turns")
                
                # Get game context for AI
                game_context = f"""Current Location: {game.room_manager.current_room.name if game.room_manager.current_room else 'Unknown'}
Time: {game.clock.get_display_time() if hasattr(game.clock, 'get_display_time') else str(game.clock.get_current_time())}
Gold: {game.player.gold}
Energy: {game.player.energy}
NPCs Present: {[npc.name for npc in game.npc_manager.get_present_npcs()]}
"""
                
                # Get AI decision
                command_text = await ai_player.generate_action(game_context)
                if not command_text or not command_text.strip():
                    print(f"⚠️ Turn {turn}: AI provided no action")
                    continue
                
                # Clean up command text
                command_text = command_text.strip()
                
                # Capture pre-command context
                context_snapshot = {
                    'turn': turn,
                    'command': command_text,
                    'ai_reasoning': f"AI generated: {command_text}",
                    'game_state': {
                        'location': game.room_manager.current_room.name if game.room_manager.current_room else "Unknown",
                        'time': str(game.clock.get_current_time()),
                        'npcs_present': [npc.name for npc in game.npc_manager.get_present_npcs()],
                        'player_gold': game.player.gold,
                        'player_energy': game.player.energy
                    }
                }
                
                # Execute command and capture result
                result = game.process_command(command_text)
                
                # Record command attempt
                command_analysis = {
                    'turn': turn,
                    'original_command': command_text,
                    'success': result.get('success', False),
                    'message': result.get('message', ''),
                    'ai_reasoning': f"AI generated: {command_text}",
                    'context': context_snapshot['game_state']
                }
                
                self.command_attempts.append(command_analysis)
                
                if result.get('success'):
                    self.successful_patterns.append(command_analysis)
                else:
                    self.parsing_failures.append(command_analysis)
                
                # Update AI with result (record action)
                ai_player.record_action(command_text, f"Result: {result.get('success', False)}")
                
                # Update game state for AI
                ai_player.update_game_state({
                    'last_command': command_text,
                    'last_result': result.get('message', ''),
                    'success': result.get('success', False)
                })
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"🚨 Analysis stopped at turn {turn}: {e}")
        
        finally:
            await ai_player.close()
        
        # Analyze results
        self._analyze_results()
    
    def _analyze_results(self):
        """Analyze the collected data to understand LLM parsing needs."""
        print(f"\n🔍 ANALYSIS RESULTS")
        print("="*50)
        
        total_attempts = len(self.command_attempts)
        successful = len(self.successful_patterns)
        failed = len(self.parsing_failures)
        
        print(f"📊 Command Statistics:")
        print(f"   Total Commands: {total_attempts}")
        print(f"   Successful: {successful} ({successful/total_attempts*100:.1f}%)")
        print(f"   Failed: {failed} ({failed/total_attempts*100:.1f}%)")
        
        # Analyze failure patterns
        failure_reasons = {}
        for failure in self.parsing_failures:
            msg = failure['message']
            if 'Unknown command' in msg:
                reason = 'Unknown command'
            elif 'not present' in msg or 'not available' in msg:
                reason = 'Context/availability issue'
            elif 'Invalid' in msg or 'format' in msg:
                reason = 'Format/parameter issue'
            else:
                reason = 'Other'
            
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        print(f"\n🚨 Failure Analysis:")
        for reason, count in failure_reasons.items():
            print(f"   {reason}: {count} ({count/failed*100:.1f}%)")
        
        # Analyze successful patterns
        successful_commands = {}
        for success in self.successful_patterns:
            cmd = success['original_command'].split()[0]
            successful_commands[cmd] = successful_commands.get(cmd, 0) + 1
        
        print(f"\n✅ Successful Command Patterns:")
        for cmd, count in sorted(successful_commands.items(), key=lambda x: x[1], reverse=True):
            print(f"   {cmd}: {count} times")
        
        # Context analysis
        self._analyze_context_needs()
        
        # Generate LLM prompt recommendations
        self._generate_llm_recommendations()
    
    def _analyze_context_needs(self):
        """Analyze what context information is most important for parsing."""
        print(f"\n🎯 CONTEXT ANALYSIS:")
        
        # Look at when commands fail due to context
        context_issues = []
        for failure in self.parsing_failures:
            if any(phrase in failure['message'].lower() for phrase in 
                   ['not present', 'not available', 'no npcs', 'no such']):
                context_issues.append(failure)
        
        print(f"   Context-related failures: {len(context_issues)}")
        
        # Analyze what context was missing
        missing_context = {
            'npcs': 0,
            'items': 0, 
            'rooms': 0,
            'time': 0
        }
        
        for issue in context_issues:
            msg = issue['message'].lower()
            if 'npc' in msg or 'not present' in msg:
                missing_context['npcs'] += 1
            elif 'room' in msg or 'move' in msg:
                missing_context['rooms'] += 1
            elif 'item' in msg or 'buy' in msg:
                missing_context['items'] += 1
        
        print(f"   Missing context breakdown:")
        for ctx_type, count in missing_context.items():
            if count > 0:
                print(f"     {ctx_type}: {count} times")
    
    def _generate_llm_recommendations(self):
        """Generate recommendations for LLM prompt improvements."""
        print(f"\n💡 LLM PROMPT RECOMMENDATIONS:")
        print("="*40)
        
        print("📝 The long-Gemma LLM parser needs to know:")
        print()
        
        print("1. 🏢 CURRENT GAME STATE:")
        print("   - Current room/location name")
        print("   - Time of day (fantasy time format)")
        print("   - Available exits/rooms")
        print("   - Weather/atmosphere if relevant")
        print()
        
        print("2. 👥 NPC INFORMATION:")
        print("   - List of NPCs currently present")
        print("   - NPC names and basic roles (bartender, guard, etc.)")
        print("   - Whether NPCs are interactable")
        print("   - Previous interactions with NPCs")
        print()
        
        print("3. 🎒 PLAYER STATE:")
        print("   - Current inventory items")
        print("   - Player's gold amount")
        print("   - Player's energy/tiredness")
        print("   - Active quests/bounties")
        print("   - Player's current capabilities")
        print()
        
        print("4. 🌍 WORLD STATE:")
        print("   - Available items for purchase")
        print("   - Notice board content")
        print("   - Available jobs/work")
        print("   - Game mechanics (gambling, etc.)")
        print()
        
        print("5. 📚 COMMAND CONTEXT:")
        print("   - Valid command formats")
        print("   - Recently successful commands")
        print("   - Command aliases and variations")
        print("   - Context-specific commands")
        print()
        
        print("6. 🧠 MEMORY/HISTORY:")
        print("   - Recent command history")
        print("   - Previous successful interactions")
        print("   - Failed attempts and why they failed")
        print("   - Player's goals and intentions")
        
        # Save detailed analysis
        self._save_analysis_report()
    
    def _save_analysis_report(self):
        """Save detailed analysis to file."""
        report = {
            'metadata': {
                'total_commands': len(self.command_attempts),
                'successful_commands': len(self.successful_patterns),
                'failed_commands': len(self.parsing_failures),
                'analysis_timestamp': time.time()
            },
            'command_attempts': self.command_attempts,
            'successful_patterns': self.successful_patterns,
            'parsing_failures': self.parsing_failures,
            'recommendations': {
                'context_needs': [
                    'current_location',
                    'npcs_present', 
                    'player_inventory',
                    'available_actions',
                    'game_time',
                    'recent_history'
                ],
                'prompt_improvements': [
                    'Add current game state summary',
                    'Include NPC availability',
                    'Show valid command formats',
                    'Provide context about player capabilities',
                    'Include memory of recent actions'
                ]
            }
        }
        
        with open('llm_parsing_analysis.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed analysis saved to: llm_parsing_analysis.json")

async def main():
    analyzer = LLMParsingAnalyzer()
    await analyzer.run_analysis(turns=300)

if __name__ == "__main__":
    asyncio.run(main())