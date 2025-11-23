"""
Multi-Agent Social Dynamics System

Implements:
- Agent-to-agent observation and theory of mind updates
- Relationship formation and evolution
- Social reputation and gossip networks
- Agent-to-agent conversations
- Emergent group dynamics (alliances, factions, conflicts)
- Cultural evolution and shared narratives

This is where individual agents become a society.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time
import random

from .agent import DeepAgent
from .emotions import EmotionType


class RelationshipType(Enum):
    """Types of relationships between agents."""
    STRANGER = "stranger"  # No relationship yet
    ACQUAINTANCE = "acquaintance"  # Know each other
    FRIEND = "friend"  # Positive relationship
    ALLY = "ally"  # Strong positive, cooperative
    RIVAL = "rival"  # Competitive but not hostile
    ENEMY = "enemy"  # Hostile relationship
    ROMANTIC = "romantic"  # Romantic interest
    FAMILY = "family"  # Family bonds
    MENTOR_STUDENT = "mentor_student"  # Teaching relationship


@dataclass
class Relationship:
    """
    Represents relationship between two agents.

    Tracks:
    - Affinity (how much they like/dislike each other)
    - Trust (how much they trust each other)
    - Respect (how much they respect each other)
    - Familiarity (how well they know each other)
    - Shared history (memorable interactions)
    """

    agent_a_id: str
    agent_b_id: str

    # Core dimensions (-1.0 to 1.0)
    affinity: float = 0.0  # Like/dislike
    trust: float = 0.0  # Trustworthy/untrustworthy
    respect: float = 0.0  # Respect/disrespect
    familiarity: float = 0.0  # 0.0-1.0, how well they know each other

    # Relationship classification
    relationship_type: RelationshipType = RelationshipType.STRANGER

    # History
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    last_interaction_time: float = 0.0

    # Shared secrets and information
    shared_secrets: List[str] = field(default_factory=list)
    gossip_shared: List[str] = field(default_factory=list)

    def record_interaction(
        self,
        interaction_type: str,
        description: str,
        affinity_change: float = 0.0,
        trust_change: float = 0.0,
        respect_change: float = 0.0,
    ) -> None:
        """Record an interaction and update relationship values."""
        self.interactions.append({
            "timestamp": time.time(),
            "type": interaction_type,
            "description": description,
            "affinity_change": affinity_change,
            "trust_change": trust_change,
            "respect_change": respect_change,
        })

        # Update values (clamped to -1.0 to 1.0)
        self.affinity = max(-1.0, min(1.0, self.affinity + affinity_change))
        self.trust = max(-1.0, min(1.0, self.trust + trust_change))
        self.respect = max(-1.0, min(1.0, self.respect + respect_change))

        # Increase familiarity with each interaction
        familiarity_gain = 0.05 * (1.0 - self.familiarity)  # Diminishing returns
        self.familiarity = min(1.0, self.familiarity + familiarity_gain)

        self.last_interaction_time = time.time()

        # Update relationship type based on values
        self._update_relationship_type()

    def _update_relationship_type(self) -> None:
        """Classify relationship based on affinity, trust, and respect."""
        if self.familiarity < 0.2:
            self.relationship_type = RelationshipType.STRANGER
        elif self.affinity < -0.5:
            self.relationship_type = RelationshipType.ENEMY
        elif self.affinity > 0.7 and self.trust > 0.6:
            self.relationship_type = RelationshipType.ALLY
        elif self.affinity > 0.5:
            self.relationship_type = RelationshipType.FRIEND
        elif self.respect > 0.6 and abs(self.affinity) < 0.3:
            self.relationship_type = RelationshipType.RIVAL
        else:
            self.relationship_type = RelationshipType.ACQUAINTANCE

    def get_summary(self) -> str:
        """Human-readable relationship summary."""
        return (
            f"{self.relationship_type.value.title()}: "
            f"affinity={self.affinity:+.2f}, "
            f"trust={self.trust:+.2f}, "
            f"respect={self.respect:+.2f}, "
            f"familiarity={self.familiarity:.2f}"
        )

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "agent_a_id": self.agent_a_id,
            "agent_b_id": self.agent_b_id,
            "affinity": self.affinity,
            "trust": self.trust,
            "respect": self.respect,
            "familiarity": self.familiarity,
            "relationship_type": self.relationship_type.value,
            "interactions": self.interactions,
            "last_interaction_time": self.last_interaction_time,
            "shared_secrets": self.shared_secrets,
            "gossip_shared": self.gossip_shared,
        }


@dataclass
class SocialNetwork:
    """
    Manages all relationships in the agent society.

    This is the social graph - who knows whom, who trusts whom,
    who's allied with whom. Social dynamics emerge from this.
    """

    # All relationships (key: "agent_a_id:agent_b_id")
    relationships: Dict[str, Relationship] = field(default_factory=dict)

    # Reputation tracking (how others perceive each agent)
    reputation: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Format: {agent_id: {trait_name: score}}

    # Gossip network (what's being said about whom)
    gossip: List[Dict[str, Any]] = field(default_factory=list)

    def get_relationship_key(self, agent_a_id: str, agent_b_id: str) -> str:
        """Generate consistent key for relationship."""
        # Sort to ensure A:B and B:A map to same key
        ids = sorted([agent_a_id, agent_b_id])
        return f"{ids[0]}:{ids[1]}"

    def get_relationship(
        self, agent_a_id: str, agent_b_id: str
    ) -> Optional[Relationship]:
        """Get relationship between two agents."""
        key = self.get_relationship_key(agent_a_id, agent_b_id)
        return self.relationships.get(key)

    def create_relationship(
        self, agent_a_id: str, agent_b_id: str
    ) -> Relationship:
        """Create a new relationship (or return existing)."""
        key = self.get_relationship_key(agent_a_id, agent_b_id)

        if key in self.relationships:
            return self.relationships[key]

        relationship = Relationship(agent_a_id=agent_a_id, agent_b_id=agent_b_id)
        self.relationships[key] = relationship
        return relationship

    def record_observation(
        self,
        observer: DeepAgent,
        observed: DeepAgent,
        action_taken: str,
        context: Dict[str, Any],
    ) -> None:
        """
        Agent observes another agent's action.

        Updates:
        - Observer's theory of mind about observed
        - Relationship between them
        - Observer's beliefs
        """
        # Get or create relationship
        relationship = self.create_relationship(observer.agent_id, observed.agent_id)

        # Update theory of mind in observer's beliefs
        tom = observer.beliefs.get_theory_of_mind(observed.agent_id)

        # Infer traits from action (simplified inference)
        if "help" in action_taken.lower():
            tom.update_perceived_trait("helpful", min(1.0, tom.perceived_traits.get("helpful", 0.5) + 0.1))
            relationship.record_interaction(
                "observation",
                f"{observed.name} helped someone",
                affinity_change=0.1,
                respect_change=0.05,
            )

        elif "steal" in action_taken.lower() or "theft" in action_taken.lower():
            tom.update_perceived_trait("dishonest", min(1.0, tom.perceived_traits.get("dishonest", 0.5) + 0.2))
            relationship.record_interaction(
                "observation",
                f"{observed.name} engaged in theft",
                affinity_change=-0.15 if observer.personality.values and any(v.name == "fairness" for v in observer.personality.values) else -0.05,
                trust_change=-0.2,
            )

        elif "share" in action_taken.lower() or "give" in action_taken.lower():
            tom.update_perceived_trait("generous", min(1.0, tom.perceived_traits.get("generous", 0.5) + 0.1))
            relationship.record_interaction(
                "observation",
                f"{observed.name} shared something",
                affinity_change=0.1,
                trust_change=0.05,
            )

        # Update familiarity
        relationship.familiarity = min(1.0, relationship.familiarity + 0.02)

    def record_conversation(
        self,
        agent_a: DeepAgent,
        agent_b: DeepAgent,
        topic: str,
        quality: str,  # "positive", "neutral", "negative"
        depth: float,  # 0.0-1.0, how deep/meaningful
    ) -> None:
        """Record a conversation between two agents."""
        relationship = self.create_relationship(agent_a.agent_id, agent_b.agent_id)

        # Conversation quality affects relationship
        affinity_change = 0.0
        trust_change = 0.0

        if quality == "positive":
            affinity_change = 0.1 * depth
            trust_change = 0.05 * depth
        elif quality == "negative":
            affinity_change = -0.1 * depth
            trust_change = -0.05 * depth

        relationship.record_interaction(
            "conversation",
            f"Discussed {topic} ({quality})",
            affinity_change=affinity_change,
            trust_change=trust_change,
        )

        # Deep conversations create shared understanding
        if depth > 0.7:
            # Update theory of mind for both agents
            tom_a = agent_a.beliefs.get_theory_of_mind(agent_b.agent_id)
            tom_b = agent_b.beliefs.get_theory_of_mind(agent_a.agent_id)

            tom_a.model_confidence = min(1.0, tom_a.model_confidence + 0.1)
            tom_b.model_confidence = min(1.0, tom_b.model_confidence + 0.1)

    def add_gossip(
        self,
        spreader_id: str,
        subject_id: str,
        content: str,
        truthfulness: float,  # 0.0-1.0
    ) -> None:
        """Add gossip to the network."""
        self.gossip.append({
            "timestamp": time.time(),
            "spreader_id": spreader_id,
            "subject_id": subject_id,
            "content": content,
            "truthfulness": truthfulness,
            "spread_count": 1,
        })

        # Update reputation based on gossip
        if subject_id not in self.reputation:
            self.reputation[subject_id] = {}

        # Negative gossip affects reputation
        if "thief" in content.lower() or "steal" in content.lower():
            self.reputation[subject_id]["trustworthy"] = self.reputation[subject_id].get("trustworthy", 0.5) - 0.1 * truthfulness

        if "kind" in content.lower() or "help" in content.lower():
            self.reputation[subject_id]["kind"] = self.reputation[subject_id].get("kind", 0.5) + 0.1 * truthfulness

    def spread_gossip(
        self, listener_id: str, spreader_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Spread gossip from one agent to another.

        Returns the gossip item if one is shared.
        """
        relationship = self.get_relationship(listener_id, spreader_id)

        # Only share gossip if relationship has some trust
        if not relationship or relationship.trust < 0.2:
            return None

        # Find gossip the listener hasn't heard
        recent_gossip = [g for g in self.gossip[-20:] if g["spreader_id"] == spreader_id]

        if recent_gossip:
            gossip = random.choice(recent_gossip)
            gossip["spread_count"] += 1

            # Add to relationship's shared gossip
            if relationship:
                gossip_summary = f"{gossip['content']} (about {gossip['subject_id']})"
                if gossip_summary not in relationship.gossip_shared:
                    relationship.gossip_shared.append(gossip_summary)

            return gossip

        return None

    def get_agent_reputation(self, agent_id: str) -> Dict[str, float]:
        """Get an agent's reputation scores."""
        return self.reputation.get(agent_id, {})

    def get_agent_relationships(self, agent_id: str) -> List[Relationship]:
        """Get all relationships involving an agent."""
        return [
            rel
            for rel in self.relationships.values()
            if agent_id in [rel.agent_a_id, rel.agent_b_id]
        ]

    def get_social_clusters(self) -> List[List[str]]:
        """
        Identify social clusters (groups of closely connected agents).

        Uses simple clustering based on positive relationships.
        """
        # Build adjacency for positive relationships
        positive_connections: Dict[str, set] = {}

        for rel in self.relationships.values():
            if rel.affinity > 0.3:  # Positive relationship threshold
                if rel.agent_a_id not in positive_connections:
                    positive_connections[rel.agent_a_id] = set()
                if rel.agent_b_id not in positive_connections:
                    positive_connections[rel.agent_b_id] = set()

                positive_connections[rel.agent_a_id].add(rel.agent_b_id)
                positive_connections[rel.agent_b_id].add(rel.agent_a_id)

        # Simple clustering: find connected components
        clusters = []
        visited = set()

        def dfs(agent_id: str, cluster: set):
            if agent_id in visited:
                return
            visited.add(agent_id)
            cluster.add(agent_id)

            for connected in positive_connections.get(agent_id, []):
                dfs(connected, cluster)

        for agent_id in positive_connections:
            if agent_id not in visited:
                cluster = set()
                dfs(agent_id, cluster)
                clusters.append(list(cluster))

        return clusters

    def analyze_social_dynamics(self) -> Dict[str, Any]:
        """
        Analyze the current state of social dynamics.

        Returns insights about relationships, clusters, conflicts.
        """
        total_relationships = len(self.relationships)

        # Count by type
        by_type = {}
        for rel in self.relationships.values():
            rel_type = rel.relationship_type.value
            by_type[rel_type] = by_type.get(rel_type, 0) + 1

        # Find strong bonds (friends/allies)
        strong_bonds = [
            rel for rel in self.relationships.values()
            if rel.relationship_type in [RelationshipType.FRIEND, RelationshipType.ALLY]
        ]

        # Find conflicts (rivals/enemies)
        conflicts = [
            rel for rel in self.relationships.values()
            if rel.relationship_type in [RelationshipType.RIVAL, RelationshipType.ENEMY]
        ]

        # Identify social clusters
        clusters = self.get_social_clusters()

        # Most gossiped about
        gossip_subjects = {}
        for g in self.gossip:
            subject = g["subject_id"]
            gossip_subjects[subject] = gossip_subjects.get(subject, 0) + g["spread_count"]

        most_gossiped = sorted(gossip_subjects.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            "total_relationships": total_relationships,
            "by_type": by_type,
            "strong_bonds": len(strong_bonds),
            "conflicts": len(conflicts),
            "social_clusters": len(clusters),
            "largest_cluster": max([len(c) for c in clusters]) if clusters else 0,
            "most_gossiped_about": most_gossiped,
            "total_gossip_items": len(self.gossip),
        }

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "relationships": {k: v.to_dict() for k, v in self.relationships.items()},
            "reputation": self.reputation,
            "gossip": self.gossip,
        }


@dataclass
class ConversationExchange:
    """A single exchange in a conversation."""
    speaker_id: str
    content: str
    emotional_tone: str  # From speaker's dominant emotion
    timestamp: float = field(default_factory=time.time)


@dataclass
class Conversation:
    """
    Multi-turn conversation between agents.

    Manages:
    - Turn-taking
    - Topic tracking
    - Emotional flow
    - Relationship impacts
    """

    participants: List[str]  # Agent IDs
    topic: str
    exchanges: List[ConversationExchange] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    is_active: bool = True

    # Conversation quality metrics
    depth: float = 0.0  # 0.0-1.0, how meaningful
    tension: float = 0.0  # 0.0-1.0, how much conflict
    intimacy: float = 0.0  # 0.0-1.0, how personal

    def add_exchange(
        self, speaker_id: str, content: str, emotional_tone: str
    ) -> None:
        """Add an exchange to the conversation."""
        exchange = ConversationExchange(
            speaker_id=speaker_id, content=content, emotional_tone=emotional_tone
        )
        self.exchanges.append(exchange)

        # Update conversation metrics based on content
        if any(word in content.lower() for word in ["secret", "truth", "feel", "fear", "hope"]):
            self.depth = min(1.0, self.depth + 0.1)
            self.intimacy = min(1.0, self.intimacy + 0.1)

        if any(word in content.lower() for word in ["angry", "disagree", "wrong", "lie"]):
            self.tension = min(1.0, self.tension + 0.15)

    def end_conversation(self) -> None:
        """Mark conversation as ended."""
        self.is_active = False
        self.ended_at = time.time()

    def get_duration(self) -> float:
        """Get conversation duration in seconds."""
        end = self.ended_at if self.ended_at else time.time()
        return end - self.started_at

    def get_summary(self) -> str:
        """Human-readable summary."""
        duration = self.get_duration()
        return (
            f"Conversation between {', '.join(self.participants)} about '{self.topic}'\n"
            f"Duration: {duration:.0f}s, Exchanges: {len(self.exchanges)}\n"
            f"Depth: {self.depth:.1f}, Tension: {self.tension:.1f}, Intimacy: {self.intimacy:.1f}"
        )


class SocialDynamicsEngine:
    """
    Main engine for managing multi-agent social dynamics.

    Orchestrates:
    - Agent observations of each other
    - Relationship evolution
    - Conversation management
    - Gossip propagation
    - Emergent social patterns
    """

    def __init__(self):
        self.social_network = SocialNetwork()
        self.active_conversations: List[Conversation] = []
        self.conversation_history: List[Conversation] = []

    def agent_observes_action(
        self,
        observer: DeepAgent,
        observed: DeepAgent,
        action: str,
        context: Dict[str, Any],
    ) -> None:
        """Observer watches Observed perform an action."""
        self.social_network.record_observation(observer, observed, action, context)

        # Observer might form memory of this
        significance = 0.5  # Base significance
        relationship = self.social_network.get_relationship(
            observer.agent_id, observed.agent_id
        )

        if relationship and relationship.familiarity > 0.5:
            significance += 0.3  # More significant if they know each other

        if significance > 0.6:
            observer.episodic_memory.add_memory(
                content=f"Saw {observed.name} {action}",
                location=context.get("location", "unknown"),
                participants=[observed.agent_id],
                emotional_valence=relationship.affinity if relationship else 0.0,
                emotional_intensity=0.4,
                importance=significance,
            )

    def start_conversation(
        self, participants: List[DeepAgent], topic: str
    ) -> Conversation:
        """Start a conversation between agents."""
        conversation = Conversation(
            participants=[agent.agent_id for agent in participants], topic=topic
        )
        self.active_conversations.append(conversation)
        return conversation

    def conversation_exchange(
        self,
        conversation: Conversation,
        speaker: DeepAgent,
        content: str,
    ) -> None:
        """Add an exchange to an active conversation."""
        # Get speaker's emotional tone
        dominant_emotion = speaker.emotions.get_dominant_emotion()
        emotional_tone = dominant_emotion.value if dominant_emotion else "neutral"

        conversation.add_exchange(speaker.agent_id, content, emotional_tone)

        # All other participants observe this
        for participant_id in conversation.participants:
            if participant_id != speaker.agent_id:
                # This could trigger theory of mind updates
                pass  # Future: more sophisticated conversation processing

    def end_conversation(
        self, conversation: Conversation, agents: List[DeepAgent]
    ) -> None:
        """End a conversation and update relationships."""
        conversation.end_conversation()
        self.active_conversations.remove(conversation)
        self.conversation_history.append(conversation)

        # Update relationships between all participants
        participants = conversation.participants
        for i, agent_a_id in enumerate(participants):
            agent_a = next((a for a in agents if a.agent_id == agent_a_id), None)
            if not agent_a:
                continue

            for agent_b_id in participants[i + 1 :]:
                agent_b = next((a for a in agents if a.agent_id == agent_b_id), None)
                if not agent_b:
                    continue

                # Determine conversation quality based on personality compatibility
                quality = "neutral"
                if conversation.tension < 0.3 and conversation.depth > 0.5:
                    quality = "positive"
                elif conversation.tension > 0.6:
                    quality = "negative"

                self.social_network.record_conversation(
                    agent_a, agent_b, conversation.topic, quality, conversation.depth
                )

    def propagate_gossip(self, agents: List[DeepAgent]) -> List[str]:
        """
        Gossip spreads through social network.

        Returns list of gossip spread events.
        """
        events = []

        for agent in agents:
            # Check if agent is social enough to gossip
            if agent.personality.extraversion < 0.4:
                continue  # Introverts don't gossip much

            # Find agents they might gossip with
            relationships = self.social_network.get_agent_relationships(agent.agent_id)
            potential_listeners = [
                rel for rel in relationships
                if rel.familiarity > 0.3 and rel.affinity > 0.2
            ]

            if not potential_listeners:
                continue

            # Pick a listener
            relationship = random.choice(potential_listeners)
            listener_id = (
                relationship.agent_b_id
                if relationship.agent_a_id == agent.agent_id
                else relationship.agent_a_id
            )

            # Try to spread gossip
            gossip = self.social_network.spread_gossip(listener_id, agent.agent_id)
            if gossip:
                events.append(
                    f"{agent.name} gossiped to {listener_id} about {gossip['subject_id']}"
                )

        return events

    def analyze_emergence(self) -> Dict[str, Any]:
        """
        Analyze emergent social patterns.

        Returns insights about:
        - Alliance formations
        - Conflict escalations
        - Social hierarchy
        - Cultural narratives
        """
        analysis = self.social_network.analyze_social_dynamics()

        # Add conversation analysis
        analysis["total_conversations"] = len(self.conversation_history)
        analysis["active_conversations"] = len(self.active_conversations)

        if self.conversation_history:
            avg_depth = sum(c.depth for c in self.conversation_history) / len(
                self.conversation_history
            )
            avg_tension = sum(c.tension for c in self.conversation_history) / len(
                self.conversation_history
            )

            analysis["avg_conversation_depth"] = avg_depth
            analysis["avg_conversation_tension"] = avg_tension

        return analysis


# Convenience function for creating tavern society
def create_tavern_society(agents: List[DeepAgent]) -> SocialDynamicsEngine:
    """
    Initialize social dynamics engine with initial relationships.

    Sets up baseline familiarity and relationships between tavern regulars.
    """
    engine = SocialDynamicsEngine()

    # Create initial relationships based on time spent in tavern
    # Gene knows everyone (bartender)
    gene = next((a for a in agents if a.agent_id == "gene_bartender"), None)
    if gene:
        for agent in agents:
            if agent.agent_id == gene.agent_id:
                continue

            rel = engine.social_network.create_relationship(gene.agent_id, agent.agent_id)
            rel.familiarity = 0.7  # Gene knows regulars well
            rel.affinity = 0.3  # Gene likes most people
            rel.respect = 0.4  # Professional respect
            rel._update_relationship_type()

    # Sarah and Raven might have crossed paths
    sarah = next((a for a in agents if a.agent_id == "sarah_merchant"), None)
    raven = next((a for a in agents if a.agent_id == "raven_thief"), None)
    if sarah and raven:
        rel = engine.social_network.create_relationship(sarah.agent_id, raven.agent_id)
        rel.familiarity = 0.3  # Seen each other around
        rel.affinity = 0.0  # Neutral (Sarah doesn't know Raven steals)
        rel._update_relationship_type()

    # Aldric knows of Raven (suspicious)
    aldric = next((a for a in agents if a.agent_id == "aldric_guard"), None)
    if aldric and raven:
        rel = engine.social_network.create_relationship(aldric.agent_id, raven.agent_id)
        rel.familiarity = 0.4
        rel.affinity = -0.3  # Suspicious
        rel.trust = -0.4  # Doesn't trust her
        rel.respect = 0.2  # Grudging respect for her skill
        rel._update_relationship_type()

    # Lyra knows everyone (social butterfly)
    lyra = next((a for a in agents if a.agent_id == "lyra_bard"), None)
    if lyra:
        for agent in agents:
            if agent.agent_id == lyra.agent_id:
                continue

            rel = engine.social_network.create_relationship(lyra.agent_id, agent.agent_id)
            rel.familiarity = 0.6  # She talks to everyone
            rel.affinity = 0.4  # Likes most people
            rel._update_relationship_type()

    return engine
