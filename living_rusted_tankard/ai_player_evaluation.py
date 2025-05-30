#!/usr/bin/env python3
"""Comprehensive AI Player evaluation to assess integration progress."""

import subprocess
import time
import json
import re
from typing import List, Dict, Any
from pathlib import Path

class AIPlayerEvaluator:
    def __init__(self, turns: int = 250):
        self.turns = turns
        self.metrics = {
            'total_turns': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'economic_activity': {
                'initial_gold': 0,
                'final_gold': 0,
                'gambling_attempts': 0,
                'jobs_completed': 0,
                'purchases': 0
            },
            'exploration': {
                'rooms_visited': set(),
                'npcs_interacted': set(),
                'unique_commands': set()
            },
            'phase_system_usage': {
                'atmosphere_descriptions': 0,
                'npc_interactions': 0,
                'time_progression': 0,
                'fantasy_time_display': 0
            },
            'errors_encountered': [],
            'command_patterns': {},
            'progression_indicators': {
                'bounties_attempted': 0,
                'skills_used': 0,
                'story_progression': 0
            }
        }
        
    def run_ai_player_session(self) -> Dict[str, Any]:
        """Run AI player for specified turns and collect metrics."""
        print(f"🤖 Starting AI Player evaluation for {self.turns} turns...")
        
        # Start AI player process
        try:
            cmd = ["poetry", "run", "python", "core/ai_player.py", "--turns", str(self.turns), "--output-file", "ai_evaluation_log.txt"]
            
            print(f"🚀 Launching: {' '.join(cmd)}")
            
            # Run with timeout to prevent infinite loops
            result = subprocess.run(
                cmd,
                cwd="/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard",
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                print(f"❌ AI Player failed with return code {result.returncode}")
                print(f"STDERR: {result.stderr}")
                return {"success": False, "error": result.stderr}
            
            # Parse the output
            return self._analyze_ai_output(result.stdout, result.stderr)
            
        except subprocess.TimeoutExpired:
            print("⏰ AI Player session timed out after 10 minutes")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            print(f"❌ Error running AI Player: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_ai_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Analyze AI player output to extract metrics."""
        print("📊 Analyzing AI Player performance...")
        
        lines = stdout.split('\n')
        
        # Extract basic metrics
        for line in lines:
            if 'Turn' in line and ':' in line:
                self.metrics['total_turns'] += 1
                
            if 'gold' in line.lower():
                # Extract gold amounts
                gold_match = re.search(r'(\d+)\s*gold', line.lower())
                if gold_match:
                    gold_amount = int(gold_match.group(1))
                    if self.metrics['economic_activity']['initial_gold'] == 0:
                        self.metrics['economic_activity']['initial_gold'] = gold_amount
                    self.metrics['economic_activity']['final_gold'] = gold_amount
            
            # Track command patterns
            if 'Command:' in line:
                command = line.split('Command:')[-1].strip()
                self.metrics['exploration']['unique_commands'].add(command.split()[0] if command.split() else 'unknown')
                self.metrics['command_patterns'][command] = self.metrics['command_patterns'].get(command, 0) + 1
            
            # Track phase system usage
            if any(time_word in line.lower() for time_word in ['bell', 'dawn', 'morning', 'evening', 'night']):
                self.metrics['phase_system_usage']['fantasy_time_display'] += 1
                
            if 'atmosphere' in line.lower() or 'dimly lit' in line.lower() or 'crackling' in line.lower():
                self.metrics['phase_system_usage']['atmosphere_descriptions'] += 1
                
            if 'interact' in line.lower() or 'npc' in line.lower():
                self.metrics['phase_system_usage']['npc_interactions'] += 1
                
            if 'gamble' in line.lower():
                self.metrics['economic_activity']['gambling_attempts'] += 1
                
            if 'bounty' in line.lower():
                self.metrics['progression_indicators']['bounties_attempted'] += 1
                
            if 'ERROR' in line or 'error' in line.lower():
                self.metrics['errors_encountered'].append(line.strip())
        
        # Calculate success rate
        total_commands = sum(self.metrics['command_patterns'].values())
        error_commands = len([e for e in self.metrics['errors_encountered'] if 'command' in e.lower()])
        
        if total_commands > 0:
            self.metrics['successful_commands'] = total_commands - error_commands
            self.metrics['failed_commands'] = error_commands
        
        return {"success": True, "metrics": self.metrics}
    
    def evaluate_integration_quality(self) -> Dict[str, Any]:
        """Evaluate the quality of phase integration based on AI player behavior."""
        evaluation = {
            "overall_score": 0,
            "categories": {},
            "recommendations": [],
            "critical_issues": [],
            "success_indicators": []
        }
        
        # Category 1: Basic Functionality (0-25 points)
        basic_score = 0
        if self.metrics['total_turns'] >= self.turns * 0.8:  # Completed most turns
            basic_score += 10
            evaluation["success_indicators"].append("AI completed most planned turns")
        
        if self.metrics['successful_commands'] > self.metrics['failed_commands']:
            basic_score += 10
            evaluation["success_indicators"].append("More successful than failed commands")
        else:
            evaluation["critical_issues"].append("High command failure rate")
            
        if len(self.metrics['exploration']['unique_commands']) >= 5:
            basic_score += 5
            evaluation["success_indicators"].append(f"Used {len(self.metrics['exploration']['unique_commands'])} different command types")
        
        evaluation["categories"]["Basic Functionality"] = basic_score
        
        # Category 2: Phase System Integration (0-25 points)
        phase_score = 0
        
        if self.metrics['phase_system_usage']['fantasy_time_display'] > 0:
            phase_score += 8
            evaluation["success_indicators"].append("Fantasy time system actively used")
        else:
            evaluation["critical_issues"].append("Fantasy time system not being used")
            
        if self.metrics['phase_system_usage']['atmosphere_descriptions'] > 0:
            phase_score += 8
            evaluation["success_indicators"].append("Atmospheric descriptions working")
        else:
            evaluation["critical_issues"].append("Atmospheric descriptions not appearing")
            
        if self.metrics['phase_system_usage']['npc_interactions'] > 0:
            phase_score += 9
            evaluation["success_indicators"].append("NPC systems being utilized")
        else:
            evaluation["recommendations"].append("Improve NPC availability or interaction prompts")
            
        evaluation["categories"]["Phase System Integration"] = phase_score
        
        # Category 3: Economic Activity (0-25 points)
        economic_score = 0
        
        gold_change = self.metrics['economic_activity']['final_gold'] - self.metrics['economic_activity']['initial_gold']
        if abs(gold_change) > 0:
            economic_score += 10
            evaluation["success_indicators"].append(f"Economic activity: {gold_change:+d} gold change")
        
        if self.metrics['economic_activity']['gambling_attempts'] > 0:
            economic_score += 10
            evaluation["success_indicators"].append(f"Gambling system used {self.metrics['economic_activity']['gambling_attempts']} times")
        else:
            evaluation["recommendations"].append("Encourage AI to use gambling system more")
            
        if self.metrics['progression_indicators']['bounties_attempted'] > 0:
            economic_score += 5
            evaluation["success_indicators"].append("Bounty system engagement")
        
        evaluation["categories"]["Economic Activity"] = economic_score
        
        # Category 4: Error Handling & Stability (0-25 points)
        stability_score = 25  # Start with full points, deduct for issues
        
        error_rate = len(self.metrics['errors_encountered']) / max(self.metrics['total_turns'], 1)
        if error_rate > 0.2:  # More than 20% error rate
            stability_score -= 15
            evaluation["critical_issues"].append(f"High error rate: {error_rate:.1%}")
        elif error_rate > 0.1:  # More than 10% error rate
            stability_score -= 8
            evaluation["recommendations"].append(f"Moderate error rate: {error_rate:.1%}")
        else:
            evaluation["success_indicators"].append(f"Low error rate: {error_rate:.1%}")
        
        if any("timeout" in error.lower() for error in self.metrics['errors_encountered']):
            stability_score -= 5
            evaluation["critical_issues"].append("Timeout errors detected")
            
        evaluation["categories"]["Error Handling & Stability"] = max(0, stability_score)
        
        # Calculate overall score
        evaluation["overall_score"] = sum(evaluation["categories"].values())
        
        # Determine overall assessment
        if evaluation["overall_score"] >= 80:
            evaluation["assessment"] = "EXCELLENT - Integration highly successful"
        elif evaluation["overall_score"] >= 60:
            evaluation["assessment"] = "GOOD - Integration working with minor issues"
        elif evaluation["overall_score"] >= 40:
            evaluation["assessment"] = "FAIR - Integration needs improvement"
        else:
            evaluation["assessment"] = "POOR - Major integration issues need addressing"
            
        return evaluation
    
    def generate_report(self) -> str:
        """Generate comprehensive evaluation report."""
        result = self.run_ai_player_session()
        
        if not result["success"]:
            return f"""
🚨 AI PLAYER EVALUATION FAILED 🚨
Error: {result['error']}

This indicates a critical issue with the integration.
The AI player could not complete a basic session.
"""
        
        evaluation = self.evaluate_integration_quality()
        
        report = f"""
🤖 AI PLAYER INTEGRATION EVALUATION REPORT
==========================================

📊 SESSION METRICS:
- Total Turns Completed: {self.metrics['total_turns']}/{self.turns}
- Successful Commands: {self.metrics['successful_commands']}
- Failed Commands: {self.metrics['failed_commands']}
- Command Success Rate: {(self.metrics['successful_commands']/(self.metrics['successful_commands']+self.metrics['failed_commands'])*100) if (self.metrics['successful_commands']+self.metrics['failed_commands']) > 0 else 0:.1f}%

💰 ECONOMIC ACTIVITY:
- Initial Gold: {self.metrics['economic_activity']['initial_gold']}
- Final Gold: {self.metrics['economic_activity']['final_gold']}
- Net Change: {self.metrics['economic_activity']['final_gold'] - self.metrics['economic_activity']['initial_gold']:+d}
- Gambling Attempts: {self.metrics['economic_activity']['gambling_attempts']}

🔍 EXPLORATION:
- Unique Commands Used: {len(self.metrics['exploration']['unique_commands'])}
- Commands: {', '.join(sorted(self.metrics['exploration']['unique_commands']))}

🚀 PHASE SYSTEM USAGE:
- Fantasy Time Displays: {self.metrics['phase_system_usage']['fantasy_time_display']}
- Atmospheric Descriptions: {self.metrics['phase_system_usage']['atmosphere_descriptions']}
- NPC Interactions: {self.metrics['phase_system_usage']['npc_interactions']}

📈 PROGRESSION INDICATORS:
- Bounties Attempted: {self.metrics['progression_indicators']['bounties_attempted']}

🎯 INTEGRATION QUALITY ASSESSMENT:
Overall Score: {evaluation['overall_score']}/100
Assessment: {evaluation['assessment']}

CATEGORY BREAKDOWN:
"""
        
        for category, score in evaluation['categories'].items():
            report += f"- {category}: {score}/25\n"
        
        if evaluation['success_indicators']:
            report += f"\n✅ SUCCESS INDICATORS:\n"
            for indicator in evaluation['success_indicators']:
                report += f"  • {indicator}\n"
        
        if evaluation['recommendations']:
            report += f"\n💡 RECOMMENDATIONS:\n"
            for rec in evaluation['recommendations']:
                report += f"  • {rec}\n"
        
        if evaluation['critical_issues']:
            report += f"\n🚨 CRITICAL ISSUES:\n"
            for issue in evaluation['critical_issues']:
                report += f"  • {issue}\n"
        
        if self.metrics['errors_encountered']:
            report += f"\n❌ ERRORS ENCOUNTERED ({len(self.metrics['errors_encountered'])}):\n"
            for error in self.metrics['errors_encountered'][:5]:  # Show first 5 errors
                report += f"  • {error}\n"
            if len(self.metrics['errors_encountered']) > 5:
                report += f"  • ... and {len(self.metrics['errors_encountered']) - 5} more\n"
        
        report += f"\n🎯 NEXT STEPS RECOMMENDATION:\n"
        if evaluation['overall_score'] >= 70:
            report += "  ✅ Integration is successful! Focus on polish and optimization.\n"
        elif evaluation['overall_score'] >= 50:
            report += "  🔧 Integration is functional but needs refinement in identified areas.\n"
        else:
            report += "  🚨 Integration needs significant work. Address critical issues first.\n"
        
        return report

def main():
    print("🎯 Starting comprehensive AI Player integration evaluation...")
    
    evaluator = AIPlayerEvaluator(turns=250)
    report = evaluator.generate_report()
    
    print(report)
    
    # Save report to file
    with open("/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard/ai_evaluation_report.txt", "w") as f:
        f.write(report)
    
    print(f"\n📄 Full report saved to: ai_evaluation_report.txt")

if __name__ == "__main__":
    main()