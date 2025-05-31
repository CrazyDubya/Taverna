#!/usr/bin/env python3
"""
Comprehensive 200-command test suite for LLM parser analysis.
Tests complex natural language, edge cases, and challenging scenarios.
"""

import json
import time
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')

from core.game_state import GameState

@dataclass
class CommandResult:
    """Detailed result of a command test."""
    command: str
    category: str
    complexity: str
    success: bool
    message: str
    response_time: float
    parsing_method: str  # LLM, regex, or unknown
    expected_behavior: str
    actual_behavior: str
    error_type: str = ""

@dataclass 
class TestAnalysis:
    """Comprehensive analysis of test results."""
    total_commands: int = 0
    successful_commands: int = 0
    failed_commands: int = 0
    llm_parsed: int = 0
    regex_fallback: int = 0
    results_by_category: Dict[str, List[CommandResult]] = field(default_factory=dict)
    results_by_complexity: Dict[str, List[CommandResult]] = field(default_factory=dict)
    failure_patterns: Dict[str, int] = field(default_factory=dict)
    edge_case_failures: List[CommandResult] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

class Comprehensive200CommandTest:
    """Test suite for 200 complex natural language commands."""
    
    def __init__(self):
        self.game = GameState()
        self.results: List[CommandResult] = []
        self.analysis = TestAnalysis()
        
    def get_200_complex_commands(self) -> List[Tuple[str, str, str, str]]:
        """Generate 200 complex test commands with metadata.
        
        Returns: List of (command, category, complexity, expected_behavior)
        """
        commands = []
        
        # BASIC VARIATIONS (20 commands)
        basic_commands = [
            ("look", "observation", "simple", "show room description"),
            ("glance around", "observation", "simple", "show room description"),
            ("take a look", "observation", "simple", "show room description"),
            ("examine surroundings", "observation", "simple", "show room description"),
            ("survey the area", "observation", "simple", "show room description"),
            ("check status", "info", "simple", "show player status"),
            ("how am I doing", "info", "simple", "show player status"),
            ("what's my condition", "info", "simple", "show player status"),
            ("am I okay", "info", "simple", "show player status"),
            ("show me my stats", "info", "simple", "show player status"),
            ("inventory", "info", "simple", "show inventory"),
            ("what do I have", "info", "simple", "show inventory"),
            ("check my stuff", "info", "simple", "show inventory"),
            ("what am I carrying", "info", "simple", "show inventory"),
            ("show my items", "info", "simple", "show inventory"),
            ("help", "system", "simple", "show help"),
            ("what can I do", "system", "simple", "show help or commands"),
            ("how do I play", "system", "simple", "show help"),
            ("show commands", "system", "simple", "show commands"),
            ("what are my options", "system", "simple", "show help or commands")
        ]
        commands.extend(basic_commands)
        
        # COMPLEX NATURAL LANGUAGE (40 commands)
        complex_natural = [
            ("I'd like to purchase some refreshments", "commerce", "complex", "buy items"),
            ("Could you help me find something to eat", "commerce", "complex", "buy food or show items"),
            ("I'm feeling quite parched and need a beverage", "commerce", "complex", "buy drink"),
            ("What sort of victuals do you have available", "commerce", "complex", "show available items"),
            ("I require sustenance after my long journey", "commerce", "complex", "buy food"),
            ("Might I inquire about your finest ales", "commerce", "complex", "show drinks or buy ale"),
            ("I seek conversation with the proprietor", "social", "complex", "interact with bartender"),
            ("Would it be possible to speak with someone", "social", "complex", "interact with NPC"),
            ("I wish to engage in discourse", "social", "complex", "talk to someone"),
            ("Pray tell, who runs this establishment", "social", "complex", "talk to bartender or look"),
            ("I'm curious about local happenings", "info", "complex", "talk to NPCs or read board"),
            ("What news from the surrounding lands", "info", "complex", "talk to NPCs"),
            ("Are there any matters requiring attention", "work", "complex", "check jobs or bounties"),
            ("I seek employment or tasks to complete", "work", "complex", "show jobs"),
            ("What opportunities for coin exist here", "work", "complex", "show jobs or bounties"),
            ("I require shelter for the evening", "lodging", "complex", "rent room or ask about rooms"),
            ("Where might a weary traveler rest", "lodging", "complex", "rent room"),
            ("I need somewhere to store my belongings", "storage", "complex", "ask about storage"),
            ("My pack grows heavy with treasures", "storage", "complex", "store items or rent room"),
            ("I must secure my valuables", "storage", "complex", "store items"),
            ("The hour grows late, what time is it", "time", "complex", "check time or status"),
            ("How long until dawn breaks", "time", "complex", "check time"),
            ("Has much time passed since my arrival", "time", "complex", "check time"),
            ("What tales do the walls of this place hold", "exploration", "complex", "look around"),
            ("Tell me of this tavern's history", "exploration", "complex", "look or talk to NPCs"),
            ("What secrets might this place harbor", "exploration", "complex", "explore or look"),
            ("I sense there's more here than meets the eye", "exploration", "complex", "look or explore"),
            ("Something about this place intrigues me", "exploration", "complex", "look around"),
            ("I feel the weight of destiny upon me", "narrative", "complex", "look or check status"),
            ("Perhaps fate has brought me to this place", "narrative", "complex", "philosophical response"),
            ("The threads of my story seem to converge here", "narrative", "complex", "philosophical response"),
            ("What role am I meant to play in this tale", "narrative", "complex", "check status or talk"),
            ("I sense great adventures await", "narrative", "complex", "check bounties or jobs"),
            ("My heart yearns for purpose and meaning", "work", "complex", "check jobs or bounties"),
            ("I must prove my worth through noble deeds", "work", "complex", "accept bounty or work"),
            ("Honor and glory call to me", "work", "complex", "check bounties"),
            ("I seek to forge my legend in this realm", "work", "complex", "accept challenging work"),
            ("What challenges might test my mettle", "work", "complex", "check bounties"),
            ("I hunger for trials that will shape me", "work", "complex", "check difficult jobs"),
            ("Show me tasks worthy of a true hero", "work", "complex", "check bounties")
        ]
        commands.extend(complex_natural)
        
        # AMBIGUOUS/UNCLEAR COMMANDS (30 commands)
        ambiguous = [
            ("do something", "ambiguous", "edge", "unclear intent - ask for clarification"),
            ("make it happen", "ambiguous", "edge", "unclear intent"),
            ("you know what I mean", "ambiguous", "edge", "unclear intent"),
            ("the usual", "ambiguous", "edge", "unclear - no established pattern"),
            ("same as before", "ambiguous", "edge", "unclear - no previous command"),
            ("handle it", "ambiguous", "edge", "unclear intent"),
            ("fix this", "ambiguous", "edge", "unclear what to fix"),
            ("sort me out", "ambiguous", "edge", "unclear intent"),
            ("hook me up", "ambiguous", "edge", "unclear with what"),
            ("I need stuff", "ambiguous", "edge", "unclear what stuff"),
            ("get me things", "ambiguous", "edge", "unclear what things"),
            ("do the thing", "ambiguous", "edge", "unclear what thing"),
            ("make magic happen", "ambiguous", "edge", "unclear intent"),
            ("work your magic", "ambiguous", "edge", "unclear intent"),
            ("surprise me", "ambiguous", "edge", "unclear what kind of surprise"),
            ("whatever works", "ambiguous", "edge", "unclear intent"),
            ("just... anything", "ambiguous", "edge", "unclear intent"),
            ("I don't know, something", "ambiguous", "edge", "unclear intent"),
            ("figure it out", "ambiguous", "edge", "unclear what to figure out"),
            ("deal with this situation", "ambiguous", "edge", "unclear what situation"),
            ("resolve my predicament", "ambiguous", "edge", "unclear predicament"),
            ("address my concerns", "ambiguous", "edge", "unclear concerns"),
            ("attend to my needs", "ambiguous", "edge", "unclear needs"),
            ("see to my requirements", "ambiguous", "edge", "unclear requirements"),
            ("handle my business", "ambiguous", "edge", "unclear business"),
            ("take care of everything", "ambiguous", "edge", "unclear what everything"),
            ("make everything better", "ambiguous", "edge", "unclear what's wrong"),
            ("fix whatever's broken", "ambiguous", "edge", "unclear what's broken"),
            ("improve my situation", "ambiguous", "edge", "unclear situation"),
            ("optimize my experience", "ambiguous", "edge", "unclear experience")
        ]
        commands.extend(ambiguous)
        
        # MULTI-PART COMPLEX COMMANDS (25 commands)
        multipart = [
            ("I want to buy some ale and then talk to the bartender about rumors", "multipart", "complex", "buy ale then interact"),
            ("Show me the jobs available and also check what time it is", "multipart", "complex", "show jobs and time"),
            ("Let me examine my inventory and then purchase some food", "multipart", "complex", "inventory then buy food"),
            ("I'd like to rent a room but first tell me how much gold I have", "multipart", "complex", "check gold then rent room"),
            ("Check the notice board and if there's anything interesting, accept it", "multipart", "complex", "read board then maybe accept"),
            ("Look around the room and then examine anything that seems valuable", "multipart", "complex", "look then examine objects"),
            ("Talk to whoever's here and ask them about work opportunities", "multipart", "complex", "interact with NPCs about jobs"),
            ("I need to rest but first make sure I have enough money for a room", "multipart", "complex", "check gold then rent room"),
            ("Buy the cheapest food available and then eat it immediately", "multipart", "complex", "buy food then use it"),
            ("Find out what time it is and then decide if I should sleep", "multipart", "complex", "check time then maybe sleep"),
            ("Check if anyone's here to talk to, and if not, wait a while", "multipart", "complex", "check NPCs then wait"),
            ("Examine my current status and buy healing items if I need them", "multipart", "complex", "check status then buy items"),
            ("Look for work that pays well and doesn't require special skills", "multipart", "complex", "check jobs with criteria"),
            ("I want to socialize but first need to buy a drink to be polite", "multipart", "complex", "buy drink then socialize"),
            ("Check what's available to buy and purchase anything useful", "multipart", "complex", "check items then buy useful ones"),
            ("Talk to people about current events and local news", "multipart", "complex", "interact about topics"),
            ("I need to manage my finances, show me my gold and expenses", "multipart", "complex", "financial management"),
            ("Help me plan my next adventure based on available bounties", "multipart", "complex", "check bounties and plan"),
            ("I want to become stronger, what training is available", "multipart", "complex", "check improvement options"),
            ("Show me everything I can do to earn money here", "multipart", "complex", "comprehensive money-making info"),
            ("I'm new here, give me a complete overview of this place", "multipart", "complex", "comprehensive introduction"),
            ("Help me understand the rules and customs of this establishment", "multipart", "complex", "explain game mechanics"),
            ("What's the most efficient way to spend my time here", "multipart", "complex", "optimization advice"),
            ("I want to maximize my profits while minimizing risks", "multipart", "complex", "strategic advice"),
            ("Guide me through the best sequence of actions for a newcomer", "multipart", "complex", "step-by-step guidance")
        ]
        commands.extend(multipart)
        
        # EMOTIONAL/ROLEPLAY COMMANDS (25 commands)
        emotional = [
            ("I'm feeling overwhelmed by all these choices", "emotional", "complex", "provide guidance or help"),
            ("This place makes me nervous, I don't know what to do", "emotional", "complex", "provide comfort or help"),
            ("I'm excited to be here, what should I try first", "emotional", "complex", "suggest activities"),
            ("I feel lost and confused, can someone help me", "emotional", "complex", "provide help or guidance"),
            ("I'm angry about something that happened earlier", "emotional", "complex", "provide sympathy or diversion"),
            ("I'm sad and need cheering up", "emotional", "complex", "provide cheer or diversion"),
            ("I'm bored out of my mind, entertain me", "emotional", "complex", "suggest entertainment"),
            ("I feel lonely, is anyone here to talk to", "emotional", "complex", "check for NPCs or provide interaction"),
            ("I'm homesick and miss my family", "emotional", "complex", "provide sympathy"),
            ("I'm terrified of what might happen next", "emotional", "complex", "provide reassurance"),
            ("I feel like I don't belong here", "emotional", "complex", "provide welcome or inclusion"),
            ("I'm suspicious of everyone in this place", "emotional", "complex", "provide reassurance or info"),
            ("I trust you completely, what do you recommend", "emotional", "complex", "provide recommendations"),
            ("I'm proud of my accomplishments so far", "emotional", "complex", "acknowledge achievements"),
            ("I feel guilty about something I did", "emotional", "complex", "provide absolution or advice"),
            ("I'm curious about everyone's stories here", "emotional", "complex", "facilitate social interaction"),
            ("I want to make friends with the locals", "emotional", "complex", "facilitate social connections"),
            ("I'm homesick for adventure and excitement", "emotional", "complex", "suggest exciting activities"),
            ("I feel protective of this place and its people", "emotional", "complex", "acknowledge sentiment"),
            ("I'm grateful for the hospitality shown here", "emotional", "complex", "acknowledge gratitude"),
            ("I feel inspired to do great things", "emotional", "complex", "suggest heroic activities"),
            ("I'm determined to prove myself worthy", "emotional", "complex", "suggest challenging tasks"),
            ("I feel a deep connection to this place", "emotional", "complex", "acknowledge connection"),
            ("I'm nostalgic for simpler times", "emotional", "complex", "provide comfort"),
            ("I feel like destiny brought me here", "emotional", "complex", "acknowledge fate/destiny")
        ]
        commands.extend(emotional)
        
        # TECHNICAL/EDGE CASES (25 commands)
        technical = [
            ("", "technical", "edge", "handle empty input"),
            ("   ", "technical", "edge", "handle whitespace only"),
            ("!@#$%^&*()", "technical", "edge", "handle special characters"),
            ("buy buy buy buy buy", "technical", "edge", "handle repetitive commands"),
            ("look look look look look look look", "technical", "edge", "handle command repetition"),
            ("a", "technical", "edge", "handle single character"),
            ("aa", "technical", "edge", "handle two characters"),
            ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "technical", "edge", "handle very short repetitive"),
            ("This is a very long command that goes on and on and on and contains many words that might confuse the parser because it's so verbose and complex", "technical", "edge", "handle very long input"),
            ("BUY ALE NOW IMMEDIATELY RIGHT NOW", "technical", "edge", "handle all caps"),
            ("buy ale buy ale buy ale", "technical", "edge", "handle command repetition"),
            ("look; buy ale; talk to bartender", "technical", "edge", "handle semicolon separation"),
            ("look && buy ale && inventory", "technical", "edge", "handle && operators"),
            ("look | buy ale | status", "technical", "edge", "handle pipe operators"),
            ("look > inventory", "technical", "edge", "handle redirection operators"),
            ("buy ale --help", "technical", "edge", "handle command line flags"),
            ("buy ale -v", "technical", "edge", "handle command line options"),
            ("SELECT * FROM inventory", "technical", "edge", "handle SQL injection attempt"),
            ("DROP TABLE players", "technical", "edge", "handle SQL injection attempt"),
            ("<script>alert('xss')</script>", "technical", "edge", "handle XSS attempt"),
            ("../../../etc/passwd", "technical", "edge", "handle path traversal attempt"),
            ("rm -rf /", "technical", "edge", "handle dangerous system command"),
            ("sudo buy ale", "technical", "edge", "handle sudo command"),
            ("buy ale 2>&1", "technical", "edge", "handle shell redirection"),
            ("$(buy ale)", "technical", "edge", "handle shell command substitution")
        ]
        commands.extend(technical)
        
        # MISSPELLINGS/TYPOS (20 commands)
        typos = [
            ("lok around", "typos", "edge", "handle misspelling of look"),
            ("inventori", "typos", "edge", "handle misspelling of inventory"),
            ("hlep me", "typos", "edge", "handle misspelling of help"),
            ("buy alr", "typos", "edge", "handle misspelling of ale"),
            ("satus check", "typos", "edge", "handle misspelling of status"),
            ("bauy some food", "typos", "edge", "handle misspelling of buy"),
            ("tlak to bartender", "typos", "edge", "handle misspelling of talk"),
            ("chekc my gold", "typos", "edge", "handle misspelling of check"),
            ("whta time is it", "typos", "edge", "handle misspelling of what"),
            ("raed notice board", "typos", "edge", "handle misspelling of read"),
            ("intercat with bartender", "typos", "edge", "handle misspelling of interact"),
            ("moe to cellar", "typos", "edge", "handle misspelling of move"),
            ("waht jobs are available", "typos", "edge", "handle misspelling of what"),
            ("purcase bread", "typos", "edge", "handle misspelling of purchase"),
            ("examnie the room", "typos", "edge", "handle misspelling of examine"),
            ("hwere am I", "typos", "edge", "handle misspelling of where"),
            ("giev me help", "typos", "edge", "handle misspelling of give"),
            ("shwo inventory", "typos", "edge", "handle misspelling of show"),
            ("tiem check please", "typos", "edge", "handle misspelling of time"),
            ("fidn work for me", "typos", "edge", "handle misspelling of find")
        ]
        commands.extend(typos)
        
        # CONTEXTUAL REFERENCES (15 commands)
        contextual = [
            ("do that again", "contextual", "complex", "repeat last action"),
            ("same thing as last time", "contextual", "complex", "repeat previous command"),
            ("go back to what I was doing", "contextual", "complex", "return to previous activity"),
            ("continue what I started", "contextual", "complex", "continue previous action"),
            ("finish what I began", "contextual", "complex", "complete previous task"),
            ("undo that", "contextual", "complex", "reverse last action"),
            ("cancel what I just did", "contextual", "complex", "cancel last command"),
            ("never mind", "contextual", "complex", "cancel current action"),
            ("forget I said that", "contextual", "complex", "ignore previous command"),
            ("that wasn't what I meant", "contextual", "complex", "clarify intent"),
            ("I changed my mind", "contextual", "complex", "change decision"),
            ("actually, do something else", "contextual", "complex", "change action"),
            ("on second thought", "contextual", "complex", "reconsider action"),
            ("wait, I meant something different", "contextual", "complex", "clarify intent"),
            ("let me rephrase that", "contextual", "complex", "clarify previous command")
        ]
        commands.extend(contextual)
        
        assert len(commands) == 200, f"Expected 200 commands, got {len(commands)}"
        return commands
    
    def run_comprehensive_test(self) -> TestAnalysis:
        """Run all 200 commands and analyze results."""
        print("🧪 RUNNING COMPREHENSIVE 200-COMMAND TEST SUITE")
        print("=" * 60)
        print("Testing complex natural language, edge cases, and challenging scenarios...")
        print()
        
        commands = self.get_200_complex_commands()
        
        # Initialize categories
        categories = set(cmd[1] for cmd in commands)
        complexities = set(cmd[2] for cmd in commands)
        
        for cat in categories:
            self.analysis.results_by_category[cat] = []
        for comp in complexities:
            self.analysis.results_by_complexity[comp] = []
        
        start_time = time.time()
        
        for i, (command, category, complexity, expected) in enumerate(commands, 1):
            if i % 20 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = (200 - i) / rate if rate > 0 else 0
                print(f"Progress: {i}/200 ({i/2:.0f}%) - {rate:.1f} cmd/sec - ETA: {remaining:.0f}s")
            
            # Execute command and measure time
            cmd_start = time.time()
            result = self.game.process_command(command)
            cmd_time = time.time() - cmd_start
            
            # Analyze result
            success = result.get('success', False)
            message = result.get('message', '')
            
            # Determine parsing method (simplified detection)
            parsing_method = "unknown"
            if "Unknown command" in message or "don't understand" in message:
                parsing_method = "regex_failed"
            elif success or "Invalid" not in message:
                parsing_method = "llm_or_regex_success"
            
            # Categorize error type
            error_type = ""
            if not success:
                if "Unknown command" in message:
                    error_type = "command_not_recognized"
                elif "don't understand" in message:
                    error_type = "parsing_failed"
                elif "not present" in message or "not available" in message:
                    error_type = "context_missing"
                elif "Invalid" in message:
                    error_type = "parameter_invalid"
                else:
                    error_type = "other_failure"
            
            # Create result record
            cmd_result = CommandResult(
                command=command,
                category=category,
                complexity=complexity,
                success=success,
                message=message,
                response_time=cmd_time,
                parsing_method=parsing_method,
                expected_behavior=expected,
                actual_behavior=message[:100],
                error_type=error_type
            )
            
            # Store result
            self.results.append(cmd_result)
            self.analysis.results_by_category[category].append(cmd_result)
            self.analysis.results_by_complexity[complexity].append(cmd_result)
            
            # Update counters
            if success:
                self.analysis.successful_commands += 1
            else:
                self.analysis.failed_commands += 1
                if complexity == "edge":
                    self.analysis.edge_case_failures.append(cmd_result)
            
            # Track failure patterns
            if not success and error_type:
                self.analysis.failure_patterns[error_type] = self.analysis.failure_patterns.get(error_type, 0) + 1
            
            # Track parsing methods
            if "llm" in parsing_method.lower():
                self.analysis.llm_parsed += 1
            elif "regex" in parsing_method.lower():
                self.analysis.regex_fallback += 1
        
        # Final calculations
        self.analysis.total_commands = len(self.results)
        total_time = time.time() - start_time
        self.analysis.performance_metrics = {
            'total_test_time': total_time,
            'average_command_time': total_time / 200,
            'commands_per_second': 200 / total_time,
            'success_rate': (self.analysis.successful_commands / 200) * 100
        }
        
        print(f"\n✅ Completed 200-command test in {total_time:.1f} seconds")
        print(f"📊 Overall Success Rate: {self.analysis.performance_metrics['success_rate']:.1f}%")
        
        return self.analysis
    
    def print_detailed_analysis(self):
        """Print comprehensive analysis of test results."""
        print(f"\n🔬 DETAILED ANALYSIS OF 200-COMMAND TEST")
        print("=" * 60)
        
        # Overall stats
        success_rate = self.analysis.performance_metrics['success_rate']
        print(f"📊 OVERALL PERFORMANCE:")
        print(f"   Total Commands: {self.analysis.total_commands}")
        print(f"   Successful: {self.analysis.successful_commands} ({success_rate:.1f}%)")
        print(f"   Failed: {self.analysis.failed_commands} ({100-success_rate:.1f}%)")
        print(f"   Average Response Time: {self.analysis.performance_metrics['average_command_time']:.3f}s")
        
        # Category breakdown
        print(f"\n📈 PERFORMANCE BY CATEGORY:")
        for category, results in self.analysis.results_by_category.items():
            if results:
                successes = sum(1 for r in results if r.success)
                total = len(results)
                rate = (successes / total) * 100
                print(f"   {category.title()}: {successes}/{total} ({rate:.1f}%)")
        
        # Complexity breakdown
        print(f"\n🎯 PERFORMANCE BY COMPLEXITY:")
        for complexity, results in self.analysis.results_by_complexity.items():
            if results:
                successes = sum(1 for r in results if r.success)
                total = len(results)
                rate = (successes / total) * 100
                print(f"   {complexity.title()}: {successes}/{total} ({rate:.1f}%)")
        
        # Failure patterns
        print(f"\n🚨 FAILURE PATTERN ANALYSIS:")
        total_failures = sum(self.analysis.failure_patterns.values())
        for error_type, count in sorted(self.analysis.failure_patterns.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_failures) * 100 if total_failures > 0 else 0
            print(f"   {error_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        # Edge case analysis
        print(f"\n🔍 EDGE CASE ANALYSIS:")
        edge_failures = self.analysis.edge_case_failures
        print(f"   Edge Case Failures: {len(edge_failures)}")
        if edge_failures:
            print("   Most Problematic Edge Cases:")
            for i, failure in enumerate(edge_failures[:5], 1):
                print(f"   {i}. '{failure.command}' → {failure.error_type}")
        
        # Best and worst categories
        print(f"\n🏆 BEST PERFORMING CATEGORIES:")
        cat_rates = []
        for cat, results in self.analysis.results_by_category.items():
            if results and len(results) >= 5:  # Only categories with enough samples
                rate = (sum(1 for r in results if r.success) / len(results)) * 100
                cat_rates.append((cat, rate, len(results)))
        
        best_cats = sorted(cat_rates, key=lambda x: x[1], reverse=True)[:3]
        for cat, rate, count in best_cats:
            print(f"   {cat.title()}: {rate:.1f}% ({count} commands)")
        
        print(f"\n🚨 WORST PERFORMING CATEGORIES:")
        worst_cats = sorted(cat_rates, key=lambda x: x[1])[:3]
        for cat, rate, count in worst_cats:
            print(f"   {cat.title()}: {rate:.1f}% ({count} commands)")
    
    def save_detailed_report(self):
        """Save comprehensive analysis to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw results
        results_file = f"test_results_200cmd_{timestamp}.json"
        with open(results_file, 'w') as f:
            results_data = []
            for result in self.results:
                results_data.append({
                    'command': result.command,
                    'category': result.category,
                    'complexity': result.complexity,
                    'success': result.success,
                    'message': result.message,
                    'response_time': result.response_time,
                    'parsing_method': result.parsing_method,
                    'expected_behavior': result.expected_behavior,
                    'actual_behavior': result.actual_behavior,
                    'error_type': result.error_type
                })
            json.dump(results_data, f, indent=2)
        
        # Save analysis summary
        analysis_file = f"analysis_summary_200cmd_{timestamp}.json"
        with open(analysis_file, 'w') as f:
            analysis_data = {
                'metadata': {
                    'test_date': timestamp,
                    'total_commands': self.analysis.total_commands,
                    'test_duration': self.analysis.performance_metrics.get('total_test_time', 0)
                },
                'performance_metrics': self.analysis.performance_metrics,
                'category_breakdown': {},
                'complexity_breakdown': {},
                'failure_patterns': self.analysis.failure_patterns,
                'edge_case_count': len(self.analysis.edge_case_failures)
            }
            
            # Category breakdown
            for cat, results in self.analysis.results_by_category.items():
                if results:
                    successes = sum(1 for r in results if r.success)
                    analysis_data['category_breakdown'][cat] = {
                        'total': len(results),
                        'successful': successes,
                        'success_rate': (successes / len(results)) * 100
                    }
            
            # Complexity breakdown
            for comp, results in self.analysis.results_by_complexity.items():
                if results:
                    successes = sum(1 for r in results if r.success)
                    analysis_data['complexity_breakdown'][comp] = {
                        'total': len(results),
                        'successful': successes,
                        'success_rate': (successes / len(results)) * 100
                    }
            
            json.dump(analysis_data, f, indent=2)
        
        print(f"\n💾 REPORTS SAVED:")
        print(f"   Raw Results: {results_file}")
        print(f"   Analysis Summary: {analysis_file}")
        
        return results_file, analysis_file

def main():
    """Run the comprehensive 200-command test suite."""
    tester = Comprehensive200CommandTest()
    
    # Run test
    analysis = tester.run_comprehensive_test()
    
    # Print analysis
    tester.print_detailed_analysis()
    
    # Save reports
    tester.save_detailed_report()
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    success_rate = analysis.performance_metrics['success_rate']
    if success_rate >= 80:
        print("   🚀 EXCELLENT - Ready for production!")
    elif success_rate >= 70:
        print("   🎉 GREAT - Minor improvements needed!")
    elif success_rate >= 60:
        print("   ✅ GOOD - Some refinement required!")
    elif success_rate >= 50:
        print("   ⚠️ MODERATE - Significant work needed!")
    else:
        print("   🚨 POOR - Major overhaul required!")

if __name__ == "__main__":
    main()