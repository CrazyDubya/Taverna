"""
Consequence Propagation Engine.
Tracks player actions and creates meaningful, interconnected consequences across the world.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
import random
import logging

logger = logging.getLogger(__name__)


class ConsequenceType(Enum):
    """Types of consequences that can occur."""
    IMMEDIATE = "immediate"         # Happens right away
    SHORT_TERM = "short_term"      # Within hours
    MEDIUM_TERM = "medium_term"    # Within days
    LONG_TERM = "long_term"        # Within weeks
    PERMANENT = "permanent"        # Lasting change


class ConsequenceScope(Enum):
    """Scope of consequence impact."""
    PERSONAL = "personal"          # Affects only the player
    INDIVIDUAL = "individual"      # Affects one NPC
    LOCAL = "local"               # Affects multiple NPCs in area
    COMMUNITY = "community"       # Affects entire community
    REGIONAL = "regional"         # Affects broader region
    WORLD = "world"              # World-changing event


class ActionCategory(Enum):
    """Categories of player actions that can have consequences."""
    SOCIAL = "social"             # Talking, helping, relationships
    ECONOMIC = "economic"         # Trading, money, business
    VIOLENT = "violent"           # Fighting, threatening
    MORAL = "moral"              # Ethical choices
    REPUTATION = "reputation"     # Actions affecting standing
    EXPLORATION = "exploration"   # Discovery, investigation
    POLITICAL = "political"       # Authority, power dynamics
    SUPERNATURAL = "supernatural" # Magic, mysterious events


@dataclass
class ConsequenceRule:
    """Rule defining how actions lead to consequences."""
    rule_id: str
    name: str
    description: str
    
    # Trigger conditions
    action_category: ActionCategory
    action_patterns: List[str]  # Regex patterns matching action descriptions
    minimum_occurrences: int = 1  # How many times before triggering
    time_window_hours: float = 24.0  # Time window for counting occurrences
    
    # Context requirements
    required_npcs: List[str] = field(default_factory=list)
    required_locations: List[str] = field(default_factory=list)
    required_reputation_min: Optional[float] = None
    required_gold_min: Optional[int] = None
    prohibited_conditions: List[str] = field(default_factory=list)
    
    # Consequence definition
    consequence_type: ConsequenceType = ConsequenceType.SHORT_TERM
    consequence_scope: ConsequenceScope = ConsequenceScope.LOCAL
    delay_hours: float = 0.0  # How long before consequence manifests
    
    # Effects
    reputation_changes: Dict[str, float] = field(default_factory=dict)  # NPC ID -> change
    relationship_changes: Dict[str, float] = field(default_factory=dict)  # NPC ID -> change
    mood_changes: Dict[str, float] = field(default_factory=dict)  # NPC ID -> mood modifier
    world_state_changes: Dict[str, Any] = field(default_factory=dict)
    story_thread_triggers: List[str] = field(default_factory=list)  # Thread types to create
    
    # Descriptive text
    consequence_description: str = ""
    player_notification: str = ""
    npc_reactions: Dict[str, str] = field(default_factory=dict)  # NPC ID -> reaction text
    
    # Rule metadata
    weight: float = 1.0  # Likelihood multiplier
    cooldown_hours: float = 0.0  # Time before rule can trigger again
    max_triggers: Optional[int] = None  # Maximum times this rule can trigger
    
    triggered_count: int = 0
    last_triggered: Optional[float] = None


@dataclass
class TrackedAction:
    """A player action being tracked for consequence evaluation."""
    action_id: str
    timestamp: float
    category: ActionCategory
    description: str
    location: str
    involved_npcs: List[str]
    context: Dict[str, Any]
    
    # Action metadata
    success: bool = True
    magnitude: float = 1.0  # How significant this action was
    player_intent: str = ""  # Inferred intent behind action
    witnesses: List[str] = field(default_factory=list)
    
    def age_in_hours(self) -> float:
        """Get the age of this action in hours."""
        return (time.time() - self.timestamp) / 3600.0


@dataclass
class PendingConsequence:
    """A consequence that will manifest in the future."""
    consequence_id: str
    rule_id: str
    trigger_action_id: str
    scheduled_time: float
    
    # Effect details
    description: str
    affected_npcs: List[str]
    effects: Dict[str, Any]
    player_notification: str
    
    # State
    executed: bool = False
    cancelled: bool = False
    
    def is_ready_to_execute(self) -> bool:
        """Check if this consequence should be executed now."""
        return not self.executed and not self.cancelled and time.time() >= self.scheduled_time


class ConsequenceChain:
    """Represents a chain of interconnected consequences."""
    
    def __init__(self, chain_id: str, initial_action_id: str):
        self.chain_id = chain_id
        self.initial_action_id = initial_action_id
        self.consequences: List[str] = []  # Consequence IDs in order
        self.created_at = time.time()
        self.impact_score = 0.0
        
    def add_consequence(self, consequence_id: str, impact: float):
        """Add a consequence to this chain."""
        self.consequences.append(consequence_id)
        self.impact_score += impact
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of this consequence chain."""
        return {
            'chain_id': self.chain_id,
            'initial_action': self.initial_action_id,
            'consequence_count': len(self.consequences),
            'total_impact': self.impact_score,
            'age_hours': (time.time() - self.created_at) / 3600.0
        }


class ConsequenceEngine:
    """Engine that tracks actions and generates appropriate consequences."""
    
    def __init__(self):
        self.rules: Dict[str, ConsequenceRule] = {}
        self.tracked_actions: Dict[str, TrackedAction] = {}
        self.pending_consequences: Dict[str, PendingConsequence] = {}
        self.consequence_chains: Dict[str, ConsequenceChain] = {}
        
        # Pattern tracking for complex consequences
        self.action_patterns: Dict[str, List[str]] = {}  # Pattern name -> action IDs
        self.pattern_cooldowns: Dict[str, float] = {}
        
        # Performance tracking
        self.total_actions_tracked = 0
        self.total_consequences_triggered = 0
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default consequence rules."""
        
        # Rule: Frequent generous actions improve overall reputation
        self.add_rule(ConsequenceRule(
            rule_id="generous_behavior",
            name="Generous Behavior Pattern",
            description="Consistent helpful and generous actions improve reputation",
            action_category=ActionCategory.SOCIAL,
            action_patterns=[
                r"help.*npc",
                r"give.*gold",
                r"assist.*",
                r"volunteer.*"
            ],
            minimum_occurrences=3,
            time_window_hours=48.0,
            consequence_type=ConsequenceType.MEDIUM_TERM,
            consequence_scope=ConsequenceScope.COMMUNITY,
            delay_hours=6.0,
            reputation_changes={"all": 0.2},  # Special "all" key for everyone
            consequence_description="Your generous nature has become well-known in the community",
            player_notification="People around town speak favorably of your helpfulness",
            weight=1.5
        ))
        
        # Rule: Aggressive behavior creates tension
        self.add_rule(ConsequenceRule(
            rule_id="aggressive_behavior",
            name="Aggressive Behavior Pattern",
            description="Threatening or violent actions create fear and hostility",
            action_category=ActionCategory.VIOLENT,
            action_patterns=[
                r"threaten.*",
                r"attack.*",
                r"intimidate.*",
                r"fight.*"
            ],
            minimum_occurrences=2,
            time_window_hours=24.0,
            consequence_type=ConsequenceType.SHORT_TERM,
            consequence_scope=ConsequenceScope.LOCAL,
            delay_hours=1.0,
            reputation_changes={"all": -0.3},
            mood_changes={"all": -0.4},
            consequence_description="Your aggressive behavior has made people nervous",
            player_notification="You notice people seem more wary around you",
            story_thread_triggers=["conflict"],
            weight=2.0
        ))
        
        # Rule: Successful business dealings
        self.add_rule(ConsequenceRule(
            rule_id="business_success",
            name="Successful Merchant",
            description="Consistent profitable trading establishes business reputation",
            action_category=ActionCategory.ECONOMIC,
            action_patterns=[
                r"sell.*profit",
                r"negotiate.*success",
                r"trade.*advantage"
            ],
            minimum_occurrences=5,
            time_window_hours=72.0,
            consequence_type=ConsequenceType.MEDIUM_TERM,
            consequence_scope=ConsequenceScope.LOCAL,
            delay_hours=12.0,
            story_thread_triggers=["business_venture"],
            consequence_description="Merchants recognize your trading acumen",
            player_notification="Local merchants are eager to do business with you",
            weight=1.2
        ))
        
        # Rule: Broken promises damage trust
        self.add_rule(ConsequenceRule(
            rule_id="broken_promises",
            name="Unreliable Behavior",
            description="Breaking promises or failing commitments damages relationships",
            action_category=ActionCategory.MORAL,
            action_patterns=[
                r"break.*promise",
                r"fail.*commitment",
                r"abandon.*quest",
                r"ignore.*request"
            ],
            minimum_occurrences=1,
            consequence_type=ConsequenceType.IMMEDIATE,
            consequence_scope=ConsequenceScope.INDIVIDUAL,
            delay_hours=0.0,
            relationship_changes={"target": -0.3},  # "target" means the affected NPC
            reputation_changes={"target": -0.2},
            consequence_description="Your unreliability has damaged trust",
            player_notification="You sense that your reputation has suffered",
            weight=1.8
        ))
        
        # Rule: Mysterious investigation leads to discoveries
        self.add_rule(ConsequenceRule(
            rule_id="mystery_investigation",
            name="Curious Investigator",
            description="Investigating mysteries and asking questions uncovers secrets",
            action_category=ActionCategory.EXPLORATION,
            action_patterns=[
                r"investigate.*",
                r"search.*clues",
                r"ask.*about.*mystery",
                r"examine.*suspicious"
            ],
            minimum_occurrences=2,
            time_window_hours=24.0,
            consequence_type=ConsequenceType.SHORT_TERM,
            consequence_scope=ConsequenceScope.LOCAL,
            delay_hours=2.0,
            story_thread_triggers=["mystery"],
            consequence_description="Your investigations have uncovered something interesting",
            player_notification="You feel like you're on the verge of discovering something important",
            weight=1.3
        ))
        
        # Rule: Consistent spending attracts merchant attention
        self.add_rule(ConsequenceRule(
            rule_id="big_spender",
            name="Wealthy Customer",
            description="Spending lots of money attracts special offers and attention",
            action_category=ActionCategory.ECONOMIC,
            action_patterns=[
                r"buy.*expensive",
                r"purchase.*multiple",
                r"spend.*gold"
            ],
            minimum_occurrences=4,
            time_window_hours=48.0,
            required_gold_min=200,
            consequence_type=ConsequenceType.MEDIUM_TERM,
            consequence_scope=ConsequenceScope.LOCAL,
            delay_hours=8.0,
            world_state_changes={"merchant_special_offers": True},
            consequence_description="Merchants see you as a valued customer",
            player_notification="Merchants offer you special deals and rare items",
            weight=1.1
        ))
    
    def add_rule(self, rule: ConsequenceRule) -> None:
        """Add a consequence rule to the engine."""
        self.rules[rule.rule_id] = rule
        logger.debug(f"Added consequence rule: {rule.name}")
    
    def track_action(self, action: TrackedAction) -> None:
        """Track a player action for consequence evaluation."""
        self.tracked_actions[action.action_id] = action
        self.total_actions_tracked += 1
        
        # Clean up old actions to prevent memory bloat
        self._cleanup_old_actions()
        
        # Immediately evaluate consequences for this action
        self._evaluate_consequences_for_action(action)
        
        logger.debug(f"Tracked action: {action.description}")
    
    def _cleanup_old_actions(self, max_age_hours: float = 168.0) -> None:
        """Remove actions older than max_age_hours."""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        old_action_ids = [
            action_id for action_id, action in self.tracked_actions.items()
            if action.timestamp < cutoff_time
        ]
        
        for action_id in old_action_ids:
            del self.tracked_actions[action_id]
    
    def _evaluate_consequences_for_action(self, action: TrackedAction) -> None:
        """Evaluate if this action should trigger any consequences."""
        for rule in self.rules.values():
            if self._action_matches_rule(action, rule):
                if self._should_trigger_rule(rule, action):
                    self._trigger_consequence(rule, action)
    
    def _action_matches_rule(self, action: TrackedAction, rule: ConsequenceRule) -> bool:
        """Check if an action matches a rule's criteria."""
        # Category match
        if action.category != rule.action_category:
            return False
        
        # Pattern match
        import re
        if rule.action_patterns:
            pattern_match = any(
                re.search(pattern, action.description, re.IGNORECASE)
                for pattern in rule.action_patterns
            )
            if not pattern_match:
                return False
        
        # Location requirements
        if rule.required_locations and action.location not in rule.required_locations:
            return False
        
        # NPC requirements
        if rule.required_npcs:
            if not any(npc in action.involved_npcs for npc in rule.required_npcs):
                return False
        
        return True
    
    def _should_trigger_rule(self, rule: ConsequenceRule, current_action: TrackedAction) -> bool:
        """Determine if a rule should trigger based on occurrence patterns."""
        # Check cooldown
        if rule.last_triggered and rule.cooldown_hours > 0:
            hours_since_trigger = (time.time() - rule.last_triggered) / 3600.0
            if hours_since_trigger < rule.cooldown_hours:
                return False
        
        # Check max triggers
        if rule.max_triggers and rule.triggered_count >= rule.max_triggers:
            return False
        
        # Count matching actions in time window
        current_time = time.time()
        window_start = current_time - (rule.time_window_hours * 3600)
        
        matching_actions = [
            action for action in self.tracked_actions.values()
            if (action.timestamp >= window_start and 
                self._action_matches_rule(action, rule))
        ]
        
        return len(matching_actions) >= rule.minimum_occurrences
    
    def _trigger_consequence(self, rule: ConsequenceRule, trigger_action: TrackedAction) -> None:
        """Trigger a consequence based on a rule."""
        consequence_id = f"consequence_{rule.rule_id}_{int(time.time())}"
        
        # Calculate when consequence should manifest
        manifest_time = time.time() + (rule.delay_hours * 3600)
        
        # Determine affected NPCs
        affected_npcs = trigger_action.involved_npcs.copy()
        if rule.consequence_scope == ConsequenceScope.COMMUNITY:
            # Add all known NPCs
            affected_npcs.extend(["grim_bartender", "mira_merchant", "jonas_blacksmith", "elara_healer"])
            affected_npcs = list(set(affected_npcs))  # Remove duplicates
        
        # Create pending consequence
        consequence = PendingConsequence(
            consequence_id=consequence_id,
            rule_id=rule.rule_id,
            trigger_action_id=trigger_action.action_id,
            scheduled_time=manifest_time,
            description=rule.consequence_description,
            affected_npcs=affected_npcs,
            effects={
                'reputation_changes': rule.reputation_changes,
                'relationship_changes': rule.relationship_changes,
                'mood_changes': rule.mood_changes,
                'world_state_changes': rule.world_state_changes,
                'story_thread_triggers': rule.story_thread_triggers,
                'npc_reactions': rule.npc_reactions
            },
            player_notification=rule.player_notification
        )
        
        self.pending_consequences[consequence_id] = consequence
        
        # Update rule state
        rule.triggered_count += 1
        rule.last_triggered = time.time()
        
        # Create or extend consequence chain
        chain_id = f"chain_{trigger_action.action_id}"
        if chain_id not in self.consequence_chains:
            self.consequence_chains[chain_id] = ConsequenceChain(chain_id, trigger_action.action_id)
        
        self.consequence_chains[chain_id].add_consequence(consequence_id, rule.weight)
        
        self.total_consequences_triggered += 1
        
        logger.info(f"Triggered consequence: {rule.name} -> {rule.consequence_description}")
    
    def update(self, game_state: Any) -> List[str]:
        """Update the consequence engine and execute ready consequences."""
        executed_notifications = []
        
        # Execute ready consequences
        ready_consequences = [
            consequence for consequence in self.pending_consequences.values()
            if consequence.is_ready_to_execute()
        ]
        
        for consequence in ready_consequences:
            notification = self._execute_consequence(consequence, game_state)
            if notification:
                executed_notifications.append(notification)
        
        return executed_notifications
    
    def _execute_consequence(self, consequence: PendingConsequence, game_state: Any) -> Optional[str]:
        """Execute a pending consequence."""
        try:
            effects = consequence.effects
            
            # Apply reputation changes
            if 'reputation_changes' in effects and hasattr(game_state, 'reputation_network'):
                for npc_or_all, change in effects['reputation_changes'].items():
                    if npc_or_all == "all":
                        # Apply to all affected NPCs
                        for npc_id in consequence.affected_npcs:
                            game_state.reputation_network.record_player_action(
                                "consequence_effect", "reputation_change", [npc_id],
                                {"change": change, "witnessed_directly": True}
                            )
                    elif npc_or_all == "target" and consequence.affected_npcs:
                        # Apply to primary target
                        npc_id = consequence.affected_npcs[0]
                        game_state.reputation_network.record_player_action(
                            "consequence_effect", "reputation_change", [npc_id],
                            {"change": change, "witnessed_directly": True}
                        )
                    else:
                        # Apply to specific NPC
                        game_state.reputation_network.record_player_action(
                            "consequence_effect", "reputation_change", [npc_or_all],
                            {"change": change, "witnessed_directly": True}
                        )
            
            # Apply relationship changes
            if 'relationship_changes' in effects and hasattr(game_state, 'character_memory_manager'):
                for npc_or_target, change in effects['relationship_changes'].items():
                    if npc_or_target == "target" and consequence.affected_npcs:
                        npc_id = consequence.affected_npcs[0]
                    else:
                        npc_id = npc_or_target
                    
                    memory = game_state.character_memory_manager.get_memory(npc_id)
                    if memory:
                        if change > 0:
                            memory.improve_relationship(abs(change))
                        else:
                            memory.damage_relationship(abs(change))
            
            # Apply mood changes
            if 'mood_changes' in effects and hasattr(game_state, 'character_state_manager'):
                for npc_or_all, mood_modifier in effects['mood_changes'].items():
                    npcs_to_affect = []
                    if npc_or_all == "all":
                        npcs_to_affect = consequence.affected_npcs
                    else:
                        npcs_to_affect = [npc_or_all]
                    
                    for npc_id in npcs_to_affect:
                        state = game_state.character_state_manager.character_states.get(npc_id)
                        if state:
                            state.mood_modifiers[f"consequence_{consequence.consequence_id}"] = (
                                mood_modifier,
                                datetime.now() + timedelta(hours=24)
                            )
            
            # Apply world state changes
            if 'world_state_changes' in effects:
                for change_key, change_value in effects['world_state_changes'].items():
                    # This would need to be implemented based on specific world state structure
                    logger.info(f"World state change: {change_key} = {change_value}")
            
            # Trigger story threads
            if 'story_thread_triggers' in effects and hasattr(game_state, 'story_thread_manager'):
                for thread_type in effects['story_thread_triggers']:
                    # This would integrate with the story thread system
                    logger.info(f"Would trigger story thread: {thread_type}")
            
            # Mark as executed
            consequence.executed = True
            
            logger.info(f"Executed consequence: {consequence.description}")
            return consequence.player_notification
            
        except Exception as e:
            logger.error(f"Error executing consequence {consequence.consequence_id}: {e}")
            consequence.cancelled = True
            return None
    
    def get_active_consequence_chains(self) -> List[Dict[str, Any]]:
        """Get summaries of active consequence chains."""
        return [
            chain.get_summary() 
            for chain in self.consequence_chains.values()
            if chain.consequences  # Only include chains with consequences
        ]
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get statistics about the consequence engine."""
        return {
            'total_actions_tracked': self.total_actions_tracked,
            'total_consequences_triggered': self.total_consequences_triggered,
            'active_rules': len(self.rules),
            'pending_consequences': len([c for c in self.pending_consequences.values() if not c.executed]),
            'active_chains': len(self.consequence_chains),
            'most_triggered_rule': max(
                self.rules.values(), 
                key=lambda r: r.triggered_count, 
                default=None
            ).name if self.rules else None
        }
    
    def create_action_from_command(self, command: str, result: Dict[str, Any], 
                                 game_state: Any) -> Optional[TrackedAction]:
        """Create a TrackedAction from a game command and result."""
        if not result.get('success', False):
            return None
        
        action_id = f"action_{int(time.time() * 1000)}"  # Millisecond precision
        
        # Determine action category and description
        category = ActionCategory.SOCIAL  # Default
        description = command
        involved_npcs = []
        
        if command.startswith('interact'):
            category = ActionCategory.SOCIAL
            parts = command.split()
            if len(parts) >= 2:
                npc_id = parts[1]
                involved_npcs = [npc_id]
                description = f"talked with {npc_id}"
        
        elif command.startswith('buy'):
            category = ActionCategory.ECONOMIC
            description = f"purchased items ({result.get('message', 'unknown item')})"
            # Try to identify NPC from the transaction
            if 'from' in command:
                parts = command.split('from')
                if len(parts) > 1:
                    npc_id = parts[1].strip()
                    involved_npcs = [npc_id]
        
        elif command.startswith('sell'):
            category = ActionCategory.ECONOMIC
            description = f"sold items ({result.get('message', 'unknown item')})"
        
        elif command.startswith('help'):
            category = ActionCategory.SOCIAL
            description = "helped someone"
        
        elif command.startswith('attack') or command.startswith('fight'):
            category = ActionCategory.VIOLENT
            description = "engaged in combat"
        
        # Get current location
        location = ""
        if hasattr(game_state, 'room_manager') and game_state.room_manager.current_room:
            location = game_state.room_manager.current_room.id
        
        # Create the tracked action
        return TrackedAction(
            action_id=action_id,
            timestamp=time.time(),
            category=category,
            description=description,
            location=location,
            involved_npcs=involved_npcs,
            context={
                'command': command,
                'result': result,
                'player_gold': getattr(game_state.player, 'gold', 0) if hasattr(game_state, 'player') else 0
            },
            success=result.get('success', False),
            magnitude=1.0
        )