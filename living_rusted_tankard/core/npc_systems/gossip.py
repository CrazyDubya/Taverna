"""Rumor and gossip propagation system."""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import random
import math

from .psychology import NPCPsychology, Personality
from .relationships import RelationshipWeb, RelationshipType
from .secrets import EnhancedSecret, SecretType


class RumorType(Enum):
    """Types of rumors that can spread."""
    SECRET = "secret"          # Based on actual secrets
    EVENT = "event"            # About things that happened
    SPECULATION = "speculation" # Guesses and theories
    ACCUSATION = "accusation"  # Direct accusations
    PRAISE = "praise"          # Positive rumors
    WARNING = "warning"        # Cautionary tales
    PREDICTION = "prediction"  # Future events
    NONSENSE = "nonsense"      # False/silly rumors


class RumorReliability(Enum):
    """How reliable a rumor is."""
    FACTUAL = "factual"        # 100% true
    MOSTLY_TRUE = "mostly_true" # 80% accurate
    DISTORTED = "distorted"    # 50% accurate
    EXAGGERATED = "exaggerated" # Has truth but blown up
    FALSE = "false"            # Completely untrue
    UNKNOWN = "unknown"        # Can't verify


@dataclass
class RumorSource:
    """Information about rumor origin."""
    original_source: str  # Who started it
    current_source: str   # Who you heard it from
    source_reliability: float = 0.5  # How reliable they are
    confidence: float = 0.5  # How sure they seemed
    
    def get_trust_factor(self) -> float:
        """Calculate how much to trust this source."""
        return self.source_reliability * self.confidence


@dataclass
class Rumor:
    """A piece of gossip or rumor."""
    id: str
    type: RumorType
    content: str
    subject: Optional[str] = None  # Who/what it's about
    
    # Truth and reliability
    reliability: RumorReliability = RumorReliability.UNKNOWN
    truth_value: float = 0.5  # 0-1, actual truth
    perceived_truth: Dict[str, float] = field(default_factory=dict)  # NPC beliefs
    
    # Spread tracking
    known_by: Set[str] = field(default_factory=set)
    spread_count: int = 0
    spread_speed: float = 0.5  # How fast it spreads
    
    # Source tracking
    sources: Dict[str, RumorSource] = field(default_factory=dict)  # Who heard from whom
    
    # Content evolution
    variations: List[str] = field(default_factory=list)  # How it changes
    distortion_level: float = 0.0  # How much it's changed
    
    # Impact
    scandalousness: float = 0.5  # How shocking/interesting
    importance: float = 0.5      # How significant
    danger_level: float = 0.0    # Dangerous to spread
    
    # Lifecycle
    created: datetime = field(default_factory=datetime.now)
    last_spread: Optional[datetime] = None
    expiry: Optional[datetime] = None  # When it becomes old news
    
    def add_knower(self, npc_id: str, source: RumorSource, 
                   perceived_truth: float = 0.5) -> None:
        """Add someone who knows this rumor."""
        self.known_by.add(npc_id)
        self.sources[npc_id] = source
        self.perceived_truth[npc_id] = perceived_truth
        self.spread_count += 1
        self.last_spread = datetime.now()
    
    def get_spread_probability(self) -> float:
        """Calculate probability of spreading further."""
        # Base probability from scandalousness and importance
        base_prob = (self.scandalousness + self.importance) / 2
        
        # Modify by spread speed
        base_prob *= self.spread_speed
        
        # Reduce over time (old news)
        if self.created:
            age_days = (datetime.now() - self.created).days
            age_factor = math.exp(-age_days * 0.1)  # Exponential decay
            base_prob *= age_factor
        
        # Cap probability
        return min(0.9, max(0.1, base_prob))
    
    def evolve_content(self) -> str:
        """Get evolved version of rumor content."""
        if self.distortion_level < 0.2:
            return self.content
        
        # Pick a variation if available
        if self.variations and random.random() < self.distortion_level:
            return random.choice(self.variations)
        
        # Otherwise return original with disclaimer
        return f"{self.content} (or so I heard)"
    
    def is_fresh(self) -> bool:
        """Check if rumor is still fresh/interesting."""
        if self.expiry and datetime.now() > self.expiry:
            return False
        
        # Check age
        age_days = (datetime.now() - self.created).days
        if age_days > 7:  # Week old
            return False
        
        return True


@dataclass
class GossipExchange:
    """Record of a gossip exchange between NPCs."""
    timestamp: datetime
    gossiper: str
    listener: str
    rumors_shared: List[str]  # Rumor IDs
    location: str
    success: bool = True
    
    # Context
    relationship_level: float = 0.5
    trust_level: float = 0.5
    
    # Outcomes
    belief_levels: Dict[str, float] = field(default_factory=dict)  # Rumor ID -> belief
    reactions: Dict[str, str] = field(default_factory=dict)  # Rumor ID -> reaction


class GossipNetwork:
    """Manages the spread of rumors and gossip."""
    
    def __init__(self, relationship_web: RelationshipWeb):
        self.relationship_web = relationship_web
        self.rumors: Dict[str, Rumor] = {}
        self.exchanges: List[GossipExchange] = []
        
        # Gossiper traits
        self.gossip_tendencies: Dict[str, float] = {}  # NPC -> tendency to gossip
        self.gullibility: Dict[str, float] = {}  # NPC -> tendency to believe
        self.discretion: Dict[str, float] = {}  # NPC -> tendency to keep secrets
        
        # Topics of interest
        self.interests: Dict[str, Set[RumorType]] = {}  # NPC -> interested topics
        
    def create_rumor_from_secret(self, secret: EnhancedSecret, 
                                discovered_by: str,
                                accuracy: float = 0.7) -> Rumor:
        """Create a rumor based on a discovered secret."""
        # Determine rumor type and reliability
        if accuracy > 0.9:
            rumor_type = RumorType.SECRET
            reliability = RumorReliability.FACTUAL
        elif accuracy > 0.7:
            rumor_type = RumorType.SECRET
            reliability = RumorReliability.MOSTLY_TRUE
        elif accuracy > 0.5:
            rumor_type = RumorType.SPECULATION
            reliability = RumorReliability.DISTORTED
        else:
            rumor_type = RumorType.SPECULATION
            reliability = RumorReliability.EXAGGERATED
        
        # Create content based on accuracy
        if accuracy > 0.8:
            content = f"I heard that {secret.holder_id} {secret.content}"
        elif accuracy > 0.5:
            content = f"There are whispers that {secret.holder_id} might be involved in {secret.type.value} activities"
        else:
            content = f"Something suspicious is going on with {secret.holder_id}"
        
        # Create rumor
        rumor = Rumor(
            id=f"rumor_{secret.id}_{random.randint(1000, 9999)}",
            type=rumor_type,
            content=content,
            subject=secret.holder_id,
            reliability=reliability,
            truth_value=accuracy,
            scandalousness=secret.danger_level,
            importance=secret.danger_level * 0.8,
            danger_level=secret.danger_level * 0.5  # Dangerous to spread
        )
        
        # Add variations based on secret type
        if secret.type == SecretType.ROMANTIC:
            rumor.variations = [
                f"{secret.holder_id} has been seen with someone suspicious",
                f"There's a scandal brewing around {secret.holder_id}",
                f"{secret.holder_id} isn't being faithful, if you know what I mean"
            ]
        elif secret.type == SecretType.CRIMINAL:
            rumor.variations = [
                f"{secret.holder_id} is up to no good",
                f"The guards should look into {secret.holder_id}",
                f"I wouldn't trust {secret.holder_id} if I were you"
            ]
        
        # Set initial knower
        source = RumorSource(
            original_source=discovered_by,
            current_source=discovered_by,
            source_reliability=1.0,  # They discovered it
            confidence=accuracy
        )
        rumor.add_knower(discovered_by, source, accuracy)
        
        # Add to network
        self.rumors[rumor.id] = rumor
        
        return rumor
    
    def create_rumor_from_event(self, event_type: str, 
                               participants: List[str],
                               witness: str,
                               description: str) -> Rumor:
        """Create a rumor based on a witnessed event."""
        # Determine rumor type
        if "fight" in event_type or "argument" in event_type:
            rumor_type = RumorType.EVENT
            scandalousness = 0.7
        elif "romance" in event_type:
            rumor_type = RumorType.EVENT
            scandalousness = 0.8
        elif "suspicious" in event_type:
            rumor_type = RumorType.SPECULATION
            scandalousness = 0.6
        else:
            rumor_type = RumorType.EVENT
            scandalousness = 0.4
        
        # Create content
        if len(participants) == 1:
            content = f"I saw {participants[0]} {description}"
        elif len(participants) == 2:
            content = f"{participants[0]} and {participants[1]} were {description}"
        else:
            content = f"There was quite a scene involving {', '.join(participants)}"
        
        # Create rumor
        rumor = Rumor(
            id=f"rumor_event_{event_type}_{random.randint(1000, 9999)}",
            type=rumor_type,
            content=content,
            subject=participants[0] if participants else None,
            reliability=RumorReliability.MOSTLY_TRUE,  # Witnessed
            truth_value=0.9,  # High truth since witnessed
            scandalousness=scandalousness,
            importance=0.5
        )
        
        # Set witness as initial knower
        source = RumorSource(
            original_source=witness,
            current_source=witness,
            source_reliability=1.0,
            confidence=0.9
        )
        rumor.add_knower(witness, source, 0.9)
        
        # Add to network
        self.rumors[rumor.id] = rumor
        
        return rumor
    
    def spread_rumor(self, rumor_id: str, gossiper: str, 
                    listener: str, context: Dict[str, Any]) -> bool:
        """Attempt to spread a rumor from one NPC to another."""
        rumor = self.rumors.get(rumor_id)
        if not rumor or listener in rumor.known_by:
            return False  # Unknown rumor or already knows
        
        # Check relationship
        relationship = self.relationship_web.get_relationship(gossiper, listener)
        if not relationship:
            return False
        
        # Calculate spread probability
        base_prob = rumor.get_spread_probability()
        
        # Modify by relationship
        if relationship.trust < 0.3:
            base_prob *= 0.5  # Less likely to share with untrusted
        elif relationship.trust > 0.7:
            base_prob *= 1.5  # More likely with trusted
        
        # Modify by gossiper tendency
        gossiper_tendency = self.gossip_tendencies.get(gossiper, 0.5)
        base_prob *= gossiper_tendency
        
        # Modify by danger
        if rumor.danger_level > 0.5:
            discretion = self.discretion.get(gossiper, 0.5)
            base_prob *= (1.0 - discretion * rumor.danger_level)
        
        # Check if spread succeeds
        if random.random() > base_prob:
            return False
        
        # Calculate belief level
        source_trust = relationship.trust
        gullibility = self.gullibility.get(listener, 0.5)
        
        # Get gossiper's belief
        gossiper_belief = rumor.perceived_truth.get(gossiper, 0.5)
        
        # Calculate listener's belief
        belief = (source_trust * gossiper_belief * 0.5 + 
                 gullibility * rumor.scandalousness * 0.3 +
                 rumor.importance * 0.2)
        
        # Add distortion
        if random.random() < 0.3:  # 30% chance of distortion
            rumor.distortion_level += 0.1
            
            # Maybe create variation
            if random.random() < rumor.distortion_level:
                self._create_variation(rumor, gossiper)
        
        # Record the spread
        source = RumorSource(
            original_source=rumor.sources[gossiper].original_source,
            current_source=gossiper,
            source_reliability=source_trust,
            confidence=gossiper_belief
        )
        
        rumor.add_knower(listener, source, belief)
        
        # Record exchange
        exchange = GossipExchange(
            timestamp=datetime.now(),
            gossiper=gossiper,
            listener=listener,
            rumors_shared=[rumor_id],
            location=context.get("location", "unknown"),
            relationship_level=relationship.get_overall_disposition(),
            trust_level=relationship.trust
        )
        exchange.belief_levels[rumor_id] = belief
        
        self.exchanges.append(exchange)
        
        return True
    
    def _create_variation(self, rumor: Rumor, creator: str) -> None:
        """Create a variation of a rumor."""
        variations = {
            RumorType.SECRET: [
                f"I heard even worse things about {rumor.subject}",
                f"The truth about {rumor.subject} is darker than you think",
                f"{rumor.subject} has been hiding more than we knew"
            ],
            RumorType.EVENT: [
                "It was even more dramatic than that",
                "You should have seen what really happened",
                "That's not even the half of it"
            ],
            RumorType.SPECULATION: [
                "I have my own theories about that",
                "There's definitely more to the story",
                "I think I know what's really going on"
            ]
        }
        
        base_variations = variations.get(rumor.type, [
            "The story gets worse",
            "There's more to it",
            "I heard something different"
        ])
        
        if len(rumor.variations) < 5:  # Limit variations
            new_variation = random.choice(base_variations)
            if new_variation not in rumor.variations:
                rumor.variations.append(new_variation)
    
    def find_gossip_opportunities(self, npc_id: str, 
                                 location: str,
                                 present_npcs: List[str]) -> List[Tuple[str, List[str]]]:
        """Find opportunities for gossip."""
        opportunities = []
        
        # Get NPC's known rumors
        known_rumors = [
            rumor_id for rumor_id, rumor in self.rumors.items()
            if npc_id in rumor.known_by and rumor.is_fresh()
        ]
        
        if not known_rumors:
            return opportunities
        
        # Check each present NPC
        for other_npc in present_npcs:
            if other_npc == npc_id:
                continue
            
            # Get relationship
            relationship = self.relationship_web.get_relationship(npc_id, other_npc)
            if not relationship or relationship.trust < 0.2:
                continue  # Don't gossip with untrusted
            
            # Find rumors they don't know
            shareable_rumors = [
                rumor_id for rumor_id in known_rumors
                if other_npc not in self.rumors[rumor_id].known_by
            ]
            
            if shareable_rumors:
                # Filter by interest
                other_interests = self.interests.get(other_npc, set())
                if other_interests:
                    prioritized = [
                        r_id for r_id in shareable_rumors
                        if self.rumors[r_id].type in other_interests
                    ]
                    if prioritized:
                        shareable_rumors = prioritized
                
                opportunities.append((other_npc, shareable_rumors[:3]))  # Max 3
        
        return opportunities
    
    def simulate_gossip_spread(self, hours: float = 1.0) -> Dict[str, Any]:
        """Simulate gossip spreading over time."""
        spread_events = []
        
        # For each active rumor
        for rumor_id, rumor in self.rumors.items():
            if not rumor.is_fresh():
                continue
            
            # For each knower
            for gossiper in list(rumor.known_by):  # Copy to avoid modification issues
                # Check gossip probability based on time
                gossip_chance = self.gossip_tendencies.get(gossiper, 0.5) * (hours / 24.0)
                
                if random.random() < gossip_chance:
                    # Find someone to tell
                    connections = self.relationship_web.gossip_network.get(gossiper, set())
                    
                    for potential_listener in connections:
                        if potential_listener not in rumor.known_by:
                            # Try to spread
                            context = {"location": "tavern", "time": "gossip_hour"}
                            if self.spread_rumor(rumor_id, gossiper, potential_listener, context):
                                spread_events.append({
                                    "rumor": rumor_id,
                                    "from": gossiper,
                                    "to": potential_listener,
                                    "content": rumor.evolve_content()
                                })
                                break  # One spread per gossiper per cycle
        
        return {
            "spread_count": len(spread_events),
            "events": spread_events,
            "active_rumors": len([r for r in self.rumors.values() if r.is_fresh()])
        }
    
    def get_npc_known_rumors(self, npc_id: str, 
                            include_beliefs: bool = True) -> List[Dict[str, Any]]:
        """Get all rumors known by an NPC."""
        known = []
        
        for rumor_id, rumor in self.rumors.items():
            if npc_id in rumor.known_by:
                rumor_info = {
                    "id": rumor_id,
                    "type": rumor.type.value,
                    "content": rumor.evolve_content(),
                    "subject": rumor.subject,
                    "source": rumor.sources[npc_id].current_source,
                    "freshness": rumor.is_fresh()
                }
                
                if include_beliefs:
                    rumor_info["belief"] = rumor.perceived_truth.get(npc_id, 0.5)
                    rumor_info["trust_in_source"] = rumor.sources[npc_id].get_trust_factor()
                
                known.append(rumor_info)
        
        # Sort by freshness and importance
        known.sort(key=lambda x: (x["freshness"], 
                                  self.rumors[x["id"]].importance), 
                  reverse=True)
        
        return known
    
    def create_false_rumor(self, creator: str, target: str, 
                          rumor_type: RumorType = RumorType.ACCUSATION) -> Rumor:
        """Create a deliberately false rumor."""
        templates = {
            RumorType.ACCUSATION: [
                f"{target} has been stealing from the tavern",
                f"{target} can't be trusted with secrets",
                f"{target} is plotting something sinister"
            ],
            RumorType.SPECULATION: [
                f"I wonder what {target} is really up to",
                f"{target} has been acting very suspicious lately",
                f"Something's not right about {target}"
            ]
        }
        
        content = random.choice(templates.get(rumor_type, [f"Lies about {target}"]))
        
        rumor = Rumor(
            id=f"false_rumor_{target}_{random.randint(1000, 9999)}",
            type=rumor_type,
            content=content,
            subject=target,
            reliability=RumorReliability.FALSE,
            truth_value=0.0,
            scandalousness=0.7,
            importance=0.4,
            danger_level=0.6  # Dangerous to spread lies
        )
        
        # Creator believes their own lie (sort of)
        source = RumorSource(
            original_source=creator,
            current_source=creator,
            source_reliability=0.3,  # Low reliability
            confidence=0.8  # But confident
        )
        rumor.add_knower(creator, source, 0.8)
        
        self.rumors[rumor.id] = rumor
        
        return rumor
    
    def evaluate_rumor_impact(self, rumor_id: str) -> Dict[str, Any]:
        """Evaluate the impact of a rumor on the social network."""
        rumor = self.rumors.get(rumor_id)
        if not rumor:
            return {}
        
        impact = {
            "spread_reach": len(rumor.known_by),
            "spread_percentage": len(rumor.known_by) / max(len(self.gossip_tendencies), 1),
            "average_belief": sum(rumor.perceived_truth.values()) / max(len(rumor.perceived_truth), 1),
            "distortion_level": rumor.distortion_level,
            "variations_created": len(rumor.variations)
        }
        
        # Check relationship impacts
        if rumor.subject:
            affected_relationships = []
            for knower in rumor.known_by:
                if knower != rumor.subject:
                    rel = self.relationship_web.get_relationship(knower, rumor.subject)
                    if rel:
                        # Negative rumors reduce trust
                        if rumor.type in [RumorType.ACCUSATION, RumorType.WARNING]:
                            trust_impact = -rumor.perceived_truth[knower] * 0.2
                            affected_relationships.append({
                                "from": knower,
                                "to": rumor.subject,
                                "trust_change": trust_impact
                            })
            
            impact["relationship_impacts"] = affected_relationships
        
        return impact