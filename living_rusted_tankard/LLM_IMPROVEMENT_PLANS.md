# LLM Parser Engine Improvement Plans

## Overview

Based on comprehensive analysis of 200+ complex commands, edge cases, and failure patterns, this document outlines specific implementation plans for enhancing the LLM parser engine from its current ~73% success rate to 90%+ target performance.

## Phase 1: Foundation Improvements (Weeks 1-3)

### 1.1 Enhanced Error Handling & User Feedback

#### Current State
- Generic error messages: "I don't understand that command"
- No suggestions or guidance
- No differentiation between error types

#### Implementation Plan

```python
# core/llm/enhanced_error_handler.py
class EnhancedErrorHandler:
    def __init__(self):
        self.common_typos = {
            'lok': 'look', 'hlep': 'help', 'inventori': 'inventory',
            'tlak': 'talk', 'raed': 'read', 'chekc': 'check'
        }
        self.command_categories = {
            'exploration': ['look', 'examine', 'move', 'go'],
            'social': ['talk', 'interact', 'speak', 'ask'],
            'commerce': ['buy', 'purchase', 'get', 'acquire'],
            'work': ['jobs', 'work', 'bounty', 'accept'],
            'info': ['status', 'inventory', 'time', 'help']
        }
    
    def generate_intelligent_error(self, 
                                 failed_command: str, 
                                 error_type: str,
                                 game_context: GameSnapshot) -> str:
        """Generate contextually appropriate error messages with suggestions."""
        
        if error_type == "command_not_recognized":
            return self._handle_unrecognized_command(failed_command, game_context)
        elif error_type == "context_missing":
            return self._handle_context_error(failed_command, game_context)
        elif error_type == "parameter_invalid":
            return self._handle_parameter_error(failed_command)
        else:
            return self._handle_generic_error(failed_command, game_context)
    
    def _handle_unrecognized_command(self, command: str, context: GameSnapshot) -> str:
        # Check for typos
        words = command.lower().split()
        corrected_words = []
        has_corrections = False
        
        for word in words:
            if word in self.common_typos:
                corrected_words.append(self.common_typos[word])
                has_corrections = True
            else:
                # Fuzzy matching for typos
                best_match = self._find_closest_command(word)
                if best_match and self._similarity(word, best_match) > 0.7:
                    corrected_words.append(best_match)
                    has_corrections = True
                else:
                    corrected_words.append(word)
        
        if has_corrections:
            suggestion = ' '.join(corrected_words)
            return f"Did you mean '{suggestion}'? (Original: '{command}')"
        
        # Intent-based suggestions
        intent = self._classify_intent(command)
        if intent:
            suggestions = self._get_commands_for_intent(intent)
            return f"I'm not sure what '{command}' means. Try: {', '.join(suggestions[:3])}"
        
        # Context-based suggestions
        available_actions = self._get_contextual_actions(context)
        return f"'{command}' isn't recognized. Available actions: {', '.join(available_actions[:5])}"
    
    def _handle_context_error(self, command: str, context: GameSnapshot) -> str:
        if "talk" in command.lower() or "interact" in command.lower():
            if not context.visible_npcs:
                return ("No one is here to talk to. Try 'wait' to see if someone arrives, "
                       "or 'move <location>' to find people elsewhere.")
        
        if "buy" in command.lower():
            return ("No vendor is available right now. Look for a shopkeeper or "
                   "check if you're in the right location for purchasing.")
        
        return f"'{command}' requires something that's not currently available. Try 'look' to see what's around."
    
    def _classify_intent(self, command: str) -> str:
        """Classify user intent from failed command."""
        command_lower = command.lower()
        
        social_words = ['talk', 'speak', 'chat', 'conversation', 'hello', 'greet']
        if any(word in command_lower for word in social_words):
            return 'social'
        
        movement_words = ['go', 'move', 'walk', 'head', 'travel']
        if any(word in command_lower for word in movement_words):
            return 'movement'
        
        commerce_words = ['buy', 'purchase', 'get', 'acquire', 'shop']
        if any(word in command_lower for word in commerce_words):
            return 'commerce'
        
        return 'exploration'  # default
```

#### Integration Points
- Modify `GameState.process_command()` to use `EnhancedErrorHandler`
- Update LLM parser fallback to generate better error messages
- Add error categorization to command processing pipeline

### 1.2 Fuzzy Command Matching System

#### Implementation Plan

```python
# core/llm/fuzzy_matcher.py
import difflib
from typing import List, Tuple

class FuzzyCommandMatcher:
    def __init__(self):
        self.base_commands = [
            'look', 'status', 'inventory', 'help', 'move', 'buy', 'talk',
            'interact', 'read', 'wait', 'sleep', 'jobs', 'work', 'accept'
        ]
        self.command_aliases = {
            'examine': 'look',
            'check': 'status',
            'purchase': 'buy',
            'speak': 'talk',
            'rest': 'sleep',
            'employment': 'jobs'
        }
    
    def find_best_matches(self, input_command: str, max_matches: int = 3) -> List[Tuple[str, float]]:
        """Find best matching commands with confidence scores."""
        words = input_command.lower().split()
        
        matches = []
        
        # Check each word against base commands
        for word in words:
            # Exact alias match
            if word in self.command_aliases:
                matches.append((self.command_aliases[word], 1.0))
                continue
            
            # Fuzzy match against base commands
            close_matches = difflib.get_close_matches(
                word, self.base_commands, n=max_matches, cutoff=0.6
            )
            
            for match in close_matches:
                similarity = difflib.SequenceMatcher(None, word, match).ratio()
                matches.append((match, similarity))
        
        # Sort by confidence and return top matches
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:max_matches]
    
    def suggest_corrections(self, failed_command: str) -> List[str]:
        """Generate correction suggestions for failed commands."""
        matches = self.find_best_matches(failed_command)
        
        suggestions = []
        for command, confidence in matches:
            if confidence > 0.7:  # High confidence matches
                suggestions.append(command)
        
        return suggestions[:3]  # Top 3 suggestions
```

### 1.3 Command Preprocessing Pipeline

#### Implementation Plan

```python
# core/llm/command_preprocessor.py
import re
from typing import Dict

class CommandPreprocessor:
    def __init__(self):
        self.contractions = {
            "i'd": "i would", "i'll": "i will", "i'm": "i am",
            "can't": "cannot", "won't": "will not", "don't": "do not",
            "what's": "what is", "where's": "where is", "how's": "how is"
        }
        
        self.common_typos = {
            "lok": "look", "hlep": "help", "inventori": "inventory",
            "whta": "what", "teh": "the", "adn": "and", "tiem": "time"
        }
        
        self.normalization_rules = [
            (r'\s+', ' '),  # Multiple spaces to single space
            (r'[.!?]+$', ''),  # Remove trailing punctuation
            (r'^[^\w\s]+|[^\w\s]+$', ''),  # Remove leading/trailing special chars
        ]
    
    def preprocess(self, command: str) -> str:
        """Apply full preprocessing pipeline to command."""
        if not command or not command.strip():
            return ""
        
        # Step 1: Basic cleaning
        processed = command.lower().strip()
        
        # Step 2: Expand contractions
        processed = self._expand_contractions(processed)
        
        # Step 3: Fix common typos
        processed = self._fix_typos(processed)
        
        # Step 4: Apply normalization rules
        processed = self._normalize(processed)
        
        # Step 5: Handle special patterns
        processed = self._handle_special_patterns(processed)
        
        return processed.strip()
    
    def _expand_contractions(self, text: str) -> str:
        for contraction, expansion in self.contractions.items():
            text = text.replace(contraction, expansion)
        return text
    
    def _fix_typos(self, text: str) -> str:
        words = text.split()
        corrected_words = []
        
        for word in words:
            if word in self.common_typos:
                corrected_words.append(self.common_typos[word])
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def _normalize(self, text: str) -> str:
        for pattern, replacement in self.normalization_rules:
            text = re.sub(pattern, replacement, text)
        return text
    
    def _handle_special_patterns(self, text: str) -> str:
        """Handle common natural language patterns."""
        # "I want to X" -> "X"
        text = re.sub(r'^i (?:want to|would like to|need to) ', '', text)
        
        # "Can I X" -> "X"
        text = re.sub(r'^(?:can i|could i|may i) ', '', text)
        
        # "Please X" -> "X"
        text = re.sub(r'^(?:please |kindly )', '', text)
        
        return text
```

## Phase 2: Advanced Processing (Weeks 4-8)

### 2.1 Multi-Step Command Processing

#### Architecture Design

```python
# core/llm/multi_step_processor.py
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class CommandType(Enum):
    SIMPLE = "simple"
    SEQUENTIAL = "sequential"  # "do X then Y"
    CONDITIONAL = "conditional"  # "if X then Y"
    COMPOUND = "compound"  # "X and Y"

@dataclass
class ParsedStep:
    command: str
    condition: Optional[str] = None
    order: int = 0

class MultiStepCommandProcessor:
    def __init__(self):
        self.sequence_indicators = [
            'then', 'after', 'next', 'following', 'subsequently'
        ]
        self.conditional_indicators = [
            'if', 'when', 'should', 'in case', 'provided'
        ]
        self.compound_indicators = [
            'and', 'also', 'plus', 'as well as'
        ]
    
    def parse_multi_step_command(self, command: str) -> Tuple[CommandType, List[ParsedStep]]:
        """Parse command into steps and determine type."""
        
        # Check for conditional commands
        if any(indicator in command.lower() for indicator in self.conditional_indicators):
            return self._parse_conditional(command)
        
        # Check for sequential commands
        if any(indicator in command.lower() for indicator in self.sequence_indicators):
            return self._parse_sequential(command)
        
        # Check for compound commands
        if any(indicator in command.lower() for indicator in self.compound_indicators):
            return self._parse_compound(command)
        
        # Simple command
        return CommandType.SIMPLE, [ParsedStep(command=command, order=0)]
    
    def _parse_sequential(self, command: str) -> Tuple[CommandType, List[ParsedStep]]:
        """Parse sequential commands like 'buy ale then talk to bartender'."""
        steps = []
        
        # Split on sequence indicators
        for indicator in self.sequence_indicators:
            if indicator in command.lower():
                parts = command.lower().split(indicator, 1)
                if len(parts) == 2:
                    steps.append(ParsedStep(command=parts[0].strip(), order=0))
                    steps.append(ParsedStep(command=parts[1].strip(), order=1))
                    break
        
        return CommandType.SEQUENTIAL, steps
    
    def _parse_conditional(self, command: str) -> Tuple[CommandType, List[ParsedStep]]:
        """Parse conditional commands like 'if there are jobs, accept one'."""
        # Implementation for conditional parsing
        pass
    
    def execute_multi_step(self, steps: List[ParsedStep], game_state) -> List[Dict]:
        """Execute multiple steps in order."""
        results = []
        
        for step in sorted(steps, key=lambda x: x.order):
            if step.condition:
                # Check condition before executing
                if not self._evaluate_condition(step.condition, game_state):
                    results.append({
                        'success': False,
                        'message': f"Condition not met: {step.condition}",
                        'skipped': True
                    })
                    continue
            
            # Execute the step
            result = game_state.process_command(step.command)
            results.append(result)
            
            # If step failed and it's critical, stop execution
            if not result.get('success', False) and self._is_critical_step(step):
                break
        
        return results
```

### 2.2 Command History & Context Memory

#### Implementation Plan

```python
# core/llm/command_context.py
from collections import deque
from dataclasses import dataclass
from typing import Optional, List, Dict
import time

@dataclass
class CommandRecord:
    command: str
    timestamp: float
    success: bool
    result_message: str
    game_state_snapshot: Dict

class CommandContext:
    def __init__(self, max_history: int = 50):
        self.history: deque = deque(maxlen=max_history)
        self.last_successful_command: Optional[CommandRecord] = None
        self.last_failed_command: Optional[CommandRecord] = None
        self.command_patterns: Dict[str, int] = {}
    
    def record_command(self, command: str, success: bool, 
                      result_message: str, game_state: Dict):
        """Record a command execution for context."""
        record = CommandRecord(
            command=command,
            timestamp=time.time(),
            success=success,
            result_message=result_message,
            game_state_snapshot=game_state
        )
        
        self.history.append(record)
        
        if success:
            self.last_successful_command = record
        else:
            self.last_failed_command = record
        
        # Track command patterns
        base_command = command.split()[0] if command else ""
        self.command_patterns[base_command] = self.command_patterns.get(base_command, 0) + 1
    
    def resolve_contextual_reference(self, command: str) -> Optional[str]:
        """Resolve commands that reference previous actions."""
        command_lower = command.lower().strip()
        
        # "do that again" / "repeat"
        if any(phrase in command_lower for phrase in 
               ['that again', 'repeat', 'same thing', 'do it again']):
            if self.last_successful_command:
                return self.last_successful_command.command
        
        # "undo" / "cancel"
        if any(phrase in command_lower for phrase in 
               ['undo', 'cancel', 'never mind', 'forget that']):
            return "help"  # Safe fallback
        
        # "continue" / "keep going"
        if any(phrase in command_lower for phrase in 
               ['continue', 'keep going', 'carry on']):
            return self._suggest_continuation()
        
        return None
    
    def _suggest_continuation(self) -> str:
        """Suggest what to do next based on history."""
        if not self.history:
            return "look"
        
        recent_commands = [record.command for record in list(self.history)[-5:]]
        
        # If user has been exploring, suggest more exploration
        if any('look' in cmd for cmd in recent_commands):
            return "move"
        
        # If user has been working, suggest checking status
        if any('work' in cmd for cmd in recent_commands):
            return "status"
        
        return "help"
    
    def get_context_for_llm(self) -> str:
        """Generate context string for LLM prompts."""
        if not self.history:
            return "No previous commands."
        
        recent = list(self.history)[-3:]  # Last 3 commands
        context_parts = []
        
        for record in recent:
            status = "✓" if record.success else "✗"
            context_parts.append(f"{status} '{record.command}' → {record.result_message[:30]}")
        
        return "Recent commands:\n" + "\n".join(context_parts)
```

### 2.3 Clarification & Disambiguation Engine

#### Implementation Plan

```python
# core/llm/clarification_engine.py
class ClarificationEngine:
    def __init__(self):
        self.ambiguous_patterns = [
            'something', 'anything', 'stuff', 'things', 'it',
            'that', 'this', 'whatever', 'some'
        ]
        
        self.clarification_templates = {
            'buy_something': "What would you like to buy? Available: {items}",
            'talk_someone': "Who would you like to talk to? Present: {npcs}",
            'go_somewhere': "Where would you like to go? Available: {locations}",
            'do_something': "What would you like to do? Try: {suggestions}"
        }
    
    def needs_clarification(self, command: str, context: GameSnapshot) -> bool:
        """Determine if command is too ambiguous to execute."""
        command_lower = command.lower()
        
        # Check for ambiguous words
        if any(pattern in command_lower for pattern in self.ambiguous_patterns):
            return True
        
        # Check for incomplete commands
        if len(command.strip()) < 3:
            return True
        
        # Check for commands that reference unavailable context
        if 'talk' in command_lower and not context.visible_npcs:
            return True
        
        return False
    
    def generate_clarification(self, command: str, context: GameSnapshot) -> str:
        """Generate specific clarification questions."""
        command_lower = command.lower()
        
        if 'buy' in command_lower and any(word in command_lower for word in self.ambiguous_patterns):
            available_items = self._get_available_items(context)
            return self.clarification_templates['buy_something'].format(items=', '.join(available_items))
        
        if 'talk' in command_lower and any(word in command_lower for word in self.ambiguous_patterns):
            if context.visible_npcs:
                return self.clarification_templates['talk_someone'].format(npcs=', '.join(context.visible_npcs))
            else:
                return "No one is here to talk to. Try 'wait' or 'move <location>' to find people."
        
        if any(word in command_lower for word in ['do', 'make', 'handle']):
            suggestions = self._get_contextual_suggestions(context)
            return self.clarification_templates['do_something'].format(suggestions=', '.join(suggestions))
        
        return f"I'm not sure what you mean by '{command}'. Could you be more specific?"
    
    def _get_contextual_suggestions(self, context: GameSnapshot) -> List[str]:
        """Get contextually appropriate suggestions."""
        suggestions = ['look', 'status', 'inventory', 'help']
        
        if context.visible_npcs:
            suggestions.extend(['talk to ' + npc for npc in context.visible_npcs[:2]])
        
        if context.player_state.get('gold', 0) > 0:
            suggestions.append('buy something')
        
        return suggestions[:5]
```

## Phase 3: Advanced AI Features (Weeks 9-16)

### 3.1 Intent Recognition & Classification

```python
# core/llm/intent_engine.py
from enum import Enum
import re
from typing import Dict, List, Tuple

class UserIntent(Enum):
    EXPLORATION = "exploration"
    COMMERCE = "commerce" 
    SOCIAL = "social"
    WORK = "work"
    INFORMATION = "information"
    SYSTEM = "system"
    UNCLEAR = "unclear"

class IntentRecognizer:
    def __init__(self):
        self.intent_patterns = {
            UserIntent.EXPLORATION: [
                r'\b(look|examine|explore|search|find|discover)\b',
                r'\b(where|what.*around|show.*place)\b',
                r'\b(move|go|travel|head|walk)\b'
            ],
            UserIntent.COMMERCE: [
                r'\b(buy|purchase|acquire|get|shop|sell)\b',
                r'\b(gold|money|cost|price|afford)\b',
                r'\b(items?|goods|wares|merchandise)\b'
            ],
            UserIntent.SOCIAL: [
                r'\b(talk|speak|chat|conversation|greet)\b',
                r'\b(ask|tell|say|discuss)\b',
                r'\b(people|person|someone|bartender)\b'
            ],
            UserIntent.WORK: [
                r'\b(work|job|employment|task|quest)\b',
                r'\b(bounty|mission|assignment)\b',
                r'\b(earn|make.*money|income)\b'
            ],
            UserIntent.INFORMATION: [
                r'\b(status|health|inventory|time)\b',
                r'\b(what.*have|how.*doing|check)\b',
                r'\b(help|guide|explain|how)\b'
            ]
        }
    
    def classify_intent(self, command: str) -> Tuple[UserIntent, float]:
        """Classify user intent with confidence score."""
        command_lower = command.lower()
        
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, command_lower))
                score += matches
            
            if score > 0:
                intent_scores[intent] = score / len(patterns)  # Normalize
        
        if not intent_scores:
            return UserIntent.UNCLEAR, 0.0
        
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[best_intent]
        
        return best_intent, confidence
    
    def suggest_intent_actions(self, intent: UserIntent, context: GameSnapshot) -> List[str]:
        """Suggest specific actions based on classified intent."""
        if intent == UserIntent.EXPLORATION:
            suggestions = ['look around', 'examine room']
            if context.visible_objects:
                suggestions.append(f"examine {context.visible_objects[0]}")
            return suggestions
        
        elif intent == UserIntent.SOCIAL:
            if context.visible_npcs:
                return [f"talk to {npc}" for npc in context.visible_npcs[:2]]
            else:
                return ['wait for people', 'move to find people']
        
        elif intent == UserIntent.COMMERCE:
            return ['check what\'s for sale', 'buy ale', 'check gold']
        
        elif intent == UserIntent.WORK:
            return ['check jobs', 'read notice board', 'accept bounty']
        
        elif intent == UserIntent.INFORMATION:
            return ['status', 'inventory', 'help', 'time']
        
        return ['help', 'look around']
```

### 3.2 Dynamic Prompt Generation

```python
# core/llm/dynamic_prompts.py
class DynamicPromptBuilder:
    def __init__(self):
        self.prompt_templates = {
            'simple': self._build_simple_prompt,
            'complex': self._build_complex_prompt,
            'multi_step': self._build_multi_step_prompt,
            'clarification': self._build_clarification_prompt
        }
    
    def build_optimal_prompt(self, 
                           command: str,
                           command_type: str,
                           context: GameSnapshot,
                           history: Optional[CommandContext] = None) -> str:
        """Build optimal prompt based on command characteristics."""
        
        builder = self.prompt_templates.get(command_type, self._build_simple_prompt)
        return builder(command, context, history)
    
    def _build_simple_prompt(self, command: str, context: GameSnapshot, history=None) -> str:
        """Lightweight prompt for simple commands."""
        return f"""Parse tavern command: "{command}"

Location: {context.location}
NPCs: {', '.join(context.visible_npcs) if context.visible_npcs else 'none'}

Map to JSON: {{"action": "verb", "target": "noun", "extras": {{}}}}

Examples:
"look around" → {{"action": "look", "target": "", "extras": {{}}}}
"buy ale" → {{"action": "buy", "target": "ale", "extras": {{}}}}"""

    def _build_complex_prompt(self, command: str, context: GameSnapshot, history=None) -> str:
        """Full context prompt for complex natural language."""
        history_context = ""
        if history:
            history_context = f"\nRecent commands:\n{history.get_context_for_llm()}"
        
        return f"""You are parsing commands for "The Living Rusted Tankard" tavern game.

CURRENT CONTEXT:
📍 Location: {context.location}
🕰️ Time: {context.time_of_day}
💰 Gold: {context.player_state.get('gold', 0)}
👥 NPCs Present: {', '.join(context.visible_npcs) if context.visible_npcs else 'none'}
🎒 Inventory: {', '.join(context.visible_objects) if context.visible_objects else 'empty'}{history_context}

COMMAND TO PARSE: "{command}"

Transform natural language into precise game commands:

MAPPING RULES:
🗣️ "talk to X" / "speak with X" → "interact X talk"
🚶 "go to X" / "move to X" → "move X"  
💰 "buy X" / "purchase X" → "buy X"
👁️ "look around" / "examine room" → "look"
ℹ️ "what time" / "check status" → "status"
🎒 "check inventory" / "what do I have" → "inventory"

RESPONSE FORMAT:
{{"action": "command", "target": "object", "extras": {{"param": "value"}}}}

EXAMPLES:
"I'd like to purchase some ale" → {{"action": "buy", "target": "ale", "extras": {{}}}}
"Could I speak with the bartender?" → {{"action": "interact", "target": "bartender", "extras": {{"type": "talk"}}}}"""
```

## Implementation Timeline & Milestones

### Week 1-2: Foundation Setup
- [ ] Implement `EnhancedErrorHandler`
- [ ] Create `FuzzyCommandMatcher`
- [ ] Build `CommandPreprocessor`
- [ ] Integration testing with existing parser
- **Milestone**: 80%+ success rate on basic commands

### Week 3-4: Error Handling Enhancement
- [ ] Deploy enhanced error messages
- [ ] Implement typo correction system  
- [ ] Add contextual suggestions
- [ ] Performance optimization
- **Milestone**: Improved user experience on failures

### Week 5-6: Multi-Step Processing
- [ ] Implement `MultiStepCommandProcessor`
- [ ] Add sequential command parsing
- [ ] Create compound command handling
- [ ] Testing with complex scenarios
- **Milestone**: 60%+ success on multi-step commands

### Week 7-8: Context & Memory
- [ ] Deploy `CommandContext` system
- [ ] Implement contextual reference resolution
- [ ] Add command history tracking
- [ ] Optimize memory usage
- **Milestone**: Contextual commands working

### Week 9-12: Advanced AI Features
- [ ] Implement `IntentRecognizer`
- [ ] Deploy `ClarificationEngine`
- [ ] Add dynamic prompt generation
- [ ] Advanced testing and tuning
- **Milestone**: 85%+ overall success rate

### Week 13-16: Optimization & Learning
- [ ] Performance optimization
- [ ] Learning system implementation
- [ ] Comprehensive testing
- [ ] Documentation and deployment
- **Milestone**: 90%+ success rate target achieved

## Success Metrics & Monitoring

### Key Performance Indicators (KPIs)
1. **Overall Success Rate**: Target 90%+
2. **Response Time**: Average <2 seconds  
3. **User Satisfaction**: Reduction in "I don't understand" responses
4. **Error Recovery**: Successful resolution after clarification

### Monitoring Dashboard
- Real-time success rate tracking
- Command category performance breakdown
- Error pattern analysis
- Response time distribution
- User interaction flow analysis

### Testing Strategy
- Automated regression testing with 200+ command suite
- A/B testing for new features
- User feedback integration
- Performance benchmarking
- Edge case stress testing

This comprehensive improvement plan transforms the LLM parser from a good natural language interface into an exceptional one, capable of handling the full complexity and nuance of human communication in a game environment.