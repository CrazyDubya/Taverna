#!/usr/bin/env python3
"""Direct AI Player evaluation using the integrated game state."""

import time
import random
from typing import Dict, Any, List
from core.game_state import GameState

class DirectAIEvaluator:
    """Evaluate integration by running a simulated AI player directly."""
    
    def __init__(self, turns: int = 250):
        self.turns = turns
        self.game = GameState()
        self.metrics = {
            'total_turns': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'economic_activity': {
                'initial_gold': self.game.player.gold,
                'final_gold': 0,
                'gambling_attempts': 0,
                'purchases': 0,
                'net_change': 0
            },
            'exploration': {
                'unique_commands': set(),
                'command_frequency': {},
                'time_progression': 0
            },
            'phase_system_usage': {
                'atmosphere_mentions': 0,
                'fantasy_time_displays': 0,
                'npc_interactions': 0,
                'system_features_used': set()
            },
            'errors_encountered': [],
            'sample_outputs': []
        }
        
        # Realistic AI-like command patterns
        self.command_pool = [
            "look", "wait", "wait 1", "wait 2", 
            "gamble 5", "gamble 3", "gamble 10",
            "npcs", "games", "status", "inventory",
            "jobs", "bounties", "help",
            "buy ale", "use ale", 
            "read notice board",
            "move upstairs", "move kitchen",
            "gambling stats"
        ]
        
        # Weight commands realistically (look and wait should be common)
        self.command_weights = {
            "look": 15, "wait": 10, "wait 1": 8, "wait 2": 6,
            "gamble 5": 8, "gamble 3": 5, "gamble 10": 3,
            "npcs": 7, "games": 4, "status": 6, "inventory": 5,
            "jobs": 4, "bounties": 4, "help": 2,
            "buy ale": 3, "use ale": 2,
            "read notice board": 3,
            "move upstairs": 2, "move kitchen": 2,
            "gambling stats": 2
        }
    
    def select_command(self) -> str:
        """Select a command based on realistic AI behavior."""
        # Weighted random selection
        commands = list(self.command_weights.keys())
        weights = list(self.command_weights.values())
        
        # Add some context-aware logic
        current_gold = self.game.player.gold
        
        # If low on gold, avoid expensive gambling
        if current_gold < 10:
            # Remove high-stakes gambling
            filtered_commands = []
            filtered_weights = []
            for cmd, weight in zip(commands, weights):
                if "gamble 10" not in cmd:
                    filtered_commands.append(cmd)
                    filtered_weights.append(weight)
            commands, weights = filtered_commands, filtered_weights
        
        # If haven't checked status in a while, increase its weight
        if self.metrics['total_turns'] % 20 == 0:
            try:
                status_idx = commands.index("status")
                weights[status_idx] *= 2
            except ValueError:
                pass
        
        return random.choices(commands, weights=weights)[0]
    
    def analyze_response(self, command: str, response: Dict[str, Any]) -> None:
        """Analyze the game response and update metrics."""
        
        # Track success/failure
        if response.get('success', False):
            self.metrics['successful_commands'] += 1
        else:
            self.metrics['failed_commands'] += 1
            
        message = response.get('message', '')
        
        # Track command usage
        base_command = command.split()[0]
        self.metrics['exploration']['unique_commands'].add(base_command)
        self.metrics['exploration']['command_frequency'][command] = \
            self.metrics['exploration']['command_frequency'].get(command, 0) + 1
        
        # Analyze response content for phase system features
        if any(word in message.lower() for word in ['bell', 'dawn', 'morning', 'evening', 'night']):
            self.metrics['phase_system_usage']['fantasy_time_displays'] += 1
            self.metrics['phase_system_usage']['system_features_used'].add('fantasy_time')
            
        if any(word in message.lower() for word in ['dimly lit', 'crackling', 'atmosphere', 'warm', 'cozy']):
            self.metrics['phase_system_usage']['atmosphere_mentions'] += 1
            self.metrics['phase_system_usage']['system_features_used'].add('atmosphere')
            
        if 'npc' in message.lower() or 'interact' in message.lower():
            self.metrics['phase_system_usage']['npc_interactions'] += 1
            self.metrics['phase_system_usage']['system_features_used'].add('npc_systems')
        
        # Track economic activity
        if 'gamble' in command:
            self.metrics['economic_activity']['gambling_attempts'] += 1
            
        if 'buy' in command:
            self.metrics['economic_activity']['purchases'] += 1
            
        # Track time progression
        if 'wait' in command:
            self.metrics['exploration']['time_progression'] += 1
            
        # Collect sample outputs for analysis
        if len(self.metrics['sample_outputs']) < 10:
            self.metrics['sample_outputs'].append({
                'turn': self.metrics['total_turns'],
                'command': command,
                'response': message[:100] + '...' if len(message) > 100 else message,
                'success': response.get('success', False)
            })
            
        # Track errors
        if not response.get('success', False):
            self.metrics['errors_encountered'].append({
                'turn': self.metrics['total_turns'],
                'command': command,
                'error': message
            })
    
    def run_evaluation(self) -> Dict[str, Any]:
        """Run the comprehensive evaluation."""
        print(f"🤖 Starting direct AI evaluation for {self.turns} turns...")
        print(f"📊 Initial state: {self.game.player.gold} gold, time {self.game.clock.get_current_time().total_hours:.1f}h")
        
        start_time = time.time()
        
        for turn in range(self.turns):
            self.metrics['total_turns'] = turn + 1
            
            # Select and execute command
            command = self.select_command()
            
            try:
                response = self.game.process_command(command)
                self.analyze_response(command, response)
                
                # Progress indicator
                if (turn + 1) % 50 == 0:
                    current_gold = self.game.player.gold
                    current_time = self.game.clock.get_current_time().total_hours
                    print(f"  Turn {turn + 1}/{self.turns}: {current_gold} gold, {current_time:.1f}h")
                    
            except Exception as e:
                self.metrics['errors_encountered'].append({
                    'turn': turn + 1,
                    'command': command,
                    'error': f"Exception: {str(e)}"
                })
                self.metrics['failed_commands'] += 1
        
        # Final metrics
        self.metrics['economic_activity']['final_gold'] = self.game.player.gold
        self.metrics['economic_activity']['net_change'] = (
            self.metrics['economic_activity']['final_gold'] - 
            self.metrics['economic_activity']['initial_gold']
        )
        
        elapsed_time = time.time() - start_time
        print(f"✅ Evaluation completed in {elapsed_time:.1f} seconds")
        
        return self.generate_evaluation_report()
    
    def generate_evaluation_report(self) -> Dict[str, Any]:
        """Generate comprehensive evaluation report."""
        
        # Calculate scores
        total_commands = self.metrics['successful_commands'] + self.metrics['failed_commands']
        success_rate = (self.metrics['successful_commands'] / total_commands * 100) if total_commands > 0 else 0
        
        # Assess integration quality
        scores = {}
        
        # Basic Functionality (0-25)
        basic_score = 0
        if success_rate >= 90:
            basic_score = 25
        elif success_rate >= 80:
            basic_score = 20
        elif success_rate >= 70:
            basic_score = 15
        elif success_rate >= 60:
            basic_score = 10
        else:
            basic_score = 5
        scores['Basic Functionality'] = basic_score
        
        # Phase System Integration (0-25)
        phase_score = 0
        features_used = len(self.metrics['phase_system_usage']['system_features_used'])
        
        if self.metrics['phase_system_usage']['fantasy_time_displays'] > 0:
            phase_score += 8
        if self.metrics['phase_system_usage']['atmosphere_mentions'] > 0:
            phase_score += 8
        if features_used >= 2:
            phase_score += 9
        scores['Phase System Integration'] = phase_score
        
        # Economic System (0-25)
        economic_score = 0
        if self.metrics['economic_activity']['gambling_attempts'] > 0:
            economic_score += 15
        if abs(self.metrics['economic_activity']['net_change']) > 0:
            economic_score += 10
        scores['Economic System'] = economic_score
        
        # Exploration & Variety (0-25)
        exploration_score = 0
        unique_commands = len(self.metrics['exploration']['unique_commands'])
        if unique_commands >= 10:
            exploration_score = 25
        elif unique_commands >= 8:
            exploration_score = 20
        elif unique_commands >= 6:
            exploration_score = 15
        elif unique_commands >= 4:
            exploration_score = 10
        else:
            exploration_score = 5
        scores['Exploration & Variety'] = exploration_score
        
        overall_score = sum(scores.values())
        
        # Generate assessment
        if overall_score >= 80:
            assessment = "EXCELLENT - Integration highly successful"
        elif overall_score >= 65:
            assessment = "GOOD - Integration working well"
        elif overall_score >= 50:
            assessment = "FAIR - Integration functional with issues"
        else:
            assessment = "POOR - Integration needs significant work"
        
        return {
            'overall_score': overall_score,
            'assessment': assessment,
            'category_scores': scores,
            'metrics': self.metrics,
            'success_rate': success_rate,
            'final_game_state': {
                'gold': self.game.player.gold,
                'time': self.game.clock.get_current_time().total_hours,
                'energy': self.game.player.energy,
                'tiredness': self.game.player.tiredness
            }
        }

def main():
    """Run the evaluation and print results."""
    evaluator = DirectAIEvaluator(turns=250)
    results = evaluator.run_evaluation()
    
    print(f"""
🎯 AI PLAYER INTEGRATION EVALUATION REPORT
==========================================

📊 OVERALL ASSESSMENT:
Score: {results['overall_score']}/100
Assessment: {results['assessment']}

📈 CATEGORY BREAKDOWN:
""")
    
    for category, score in results['category_scores'].items():
        print(f"  {category}: {score}/25")
    
    print(f"""
🎮 SESSION METRICS:
- Total Turns: {results['metrics']['total_turns']}
- Success Rate: {results['success_rate']:.1f}%
- Successful Commands: {results['metrics']['successful_commands']}
- Failed Commands: {results['metrics']['failed_commands']}

💰 ECONOMIC ACTIVITY:
- Initial Gold: {results['metrics']['economic_activity']['initial_gold']}
- Final Gold: {results['metrics']['economic_activity']['final_gold']}
- Net Change: {results['metrics']['economic_activity']['net_change']:+d}
- Gambling Attempts: {results['metrics']['economic_activity']['gambling_attempts']}

🔍 EXPLORATION:
- Unique Commands: {len(results['metrics']['exploration']['unique_commands'])}
- Commands Used: {', '.join(sorted(results['metrics']['exploration']['unique_commands']))}
- Time Progression Events: {results['metrics']['exploration']['time_progression']}

🚀 PHASE SYSTEM USAGE:
- Fantasy Time Displays: {results['metrics']['phase_system_usage']['fantasy_time_displays']}
- Atmosphere Mentions: {results['metrics']['phase_system_usage']['atmosphere_mentions']}
- NPC Interactions: {results['metrics']['phase_system_usage']['npc_interactions']}
- System Features Used: {', '.join(results['metrics']['phase_system_usage']['system_features_used'])}

🏁 FINAL GAME STATE:
- Gold: {results['final_game_state']['gold']}
- Time: {results['final_game_state']['time']:.1f} hours
- Energy: {results['final_game_state']['energy']:.1f}
- Tiredness: {results['final_game_state']['tiredness']:.1f}
""")
    
    if results['metrics']['sample_outputs']:
        print("📝 SAMPLE INTERACTIONS:")
        for sample in results['metrics']['sample_outputs'][:5]:
            status = "✅" if sample['success'] else "❌"
            print(f"  Turn {sample['turn']}: {status} {sample['command']} -> {sample['response']}")
    
    if results['metrics']['errors_encountered']:
        print(f"\n❌ ERRORS ENCOUNTERED ({len(results['metrics']['errors_encountered'])}):")
        for error in results['metrics']['errors_encountered'][:3]:
            print(f"  Turn {error['turn']}: {error['command']} -> {error['error'][:80]}...")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if results['overall_score'] >= 75:
        print("  ✅ Integration is highly successful! Consider adding more complex features.")
    elif results['overall_score'] >= 60:
        print("  🔧 Integration is working well. Focus on polishing the identified weak areas.")
    elif results['overall_score'] >= 45:
        print("  ⚠️  Integration is functional but needs improvement in several areas.")
    else:
        print("  🚨 Integration has significant issues that need to be addressed.")
    
    if results['category_scores']['Phase System Integration'] < 20:
        print("  🎯 Priority: Improve phase system integration and visibility.")
    if results['category_scores']['Economic System'] < 15:
        print("  💰 Priority: Enhance economic system functionality.")
    if results['success_rate'] < 80:
        print("  🔧 Priority: Reduce command failure rate.")

if __name__ == "__main__":
    main()