"""
Reputation ripple effects system.
Creates a social network where NPC opinions of the player spread and influence each other.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
import random
import time
import logging
import math

logger = logging.getLogger(__name__)


class ReputationAspect(Enum):
    """Different aspects of reputation NPCs can have opinions about."""

    TRUSTWORTHINESS = "trustworthiness"
    GENEROSITY = "generosity"
    COMBAT_SKILL = "combat_skill"
    BUSINESS_ACUMEN = "business_acumen"
    SOCIAL_CHARM = "social_charm"
    RELIABILITY = "reliability"
    HONESTY = "honesty"
    WEALTH = "wealth"
    PROBLEM_SOLVING = "problem_solving"
    RESPECT_FOR_AUTHORITY = "respect_for_authority"


@dataclass
class ReputationOpinion:
    """An NPC's opinion about a specific aspect of the player's reputation."""

    aspect: ReputationAspect
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0 - how sure they are
    source: str  # How they formed this opinion
    last_updated: float
    experiences: List[str] = field(default_factory=list)  # Personal experiences that shaped this

    def update_from_experience(self, new_score: float, experience_description: str, confidence_boost: float = 0.2):
        """Update opinion based on direct experience."""
        # Weight new experience more heavily if they have high confidence
        weight = 0.3 + (self.confidence * 0.4)

        # Update score (moving average with weight)
        self.score = self.score * (1 - weight) + new_score * weight

        # Increase confidence from direct experience
        self.confidence = min(1.0, self.confidence + confidence_boost)

        # Add experience to history
        self.experiences.append(experience_description)
        if len(self.experiences) > 5:  # Keep only recent experiences
            self.experiences = self.experiences[-5:]

        self.last_updated = time.time()
        self.source = "personal_experience"

    def update_from_gossip(self, gossip_score: float, source_credibility: float, gossip_description: str):
        """Update opinion based on gossip from another NPC."""
        # Gossip has less impact than personal experience
        weight = 0.1 * source_credibility

        # Only update if gossip confidence is reasonable
        if source_credibility > 0.3:
            old_score = self.score
            self.score = self.score * (1 - weight) + gossip_score * weight

            # Gossip slightly reduces confidence unless it strongly aligns with existing belief
            alignment = 1.0 - abs(old_score - gossip_score)
            if alignment > 0.7:
                self.confidence = min(1.0, self.confidence + 0.05)
            else:
                self.confidence = max(0.1, self.confidence - 0.1)

            self.experiences.append(f"heard from others: {gossip_description}")
            self.last_updated = time.time()
            self.source = "gossip"


class SocialConnection:
    """Represents the relationship between two NPCs for reputation spreading."""

    def __init__(self, npc1_id: str, npc2_id: str, connection_strength: float = 0.5):
        self.npc1_id = npc1_id
        self.npc2_id = npc2_id
        self.connection_strength = connection_strength  # 0.0 to 1.0
        self.trust_level = 0.5  # How much they trust each other's opinions
        self.gossip_frequency = 0.3  # How often they share gossip
        self.last_interaction = time.time()
        self.shared_experiences: List[str] = []

    def get_other_npc(self, npc_id: str) -> Optional[str]:
        """Get the other NPC in this connection."""
        if npc_id == self.npc1_id:
            return self.npc2_id
        elif npc_id == self.npc2_id:
            return self.npc1_id
        return None

    def should_share_gossip(self) -> bool:
        """Determine if these NPCs should share gossip now."""
        time_since_last = time.time() - self.last_interaction
        hours_since = time_since_last / 3600.0

        # More likely to gossip if they haven't talked in a while
        base_chance = self.gossip_frequency
        if hours_since > 24:
            base_chance *= 1.5
        elif hours_since < 2:
            base_chance *= 0.3

        return random.random() < base_chance

    def get_trust_multiplier(self) -> float:
        """Get how much one NPC trusts the other's opinions."""
        return self.trust_level * self.connection_strength


class NPCReputation:
    """Manages reputation opinions for a single NPC."""

    def __init__(self, npc_id: str, npc_name: str):
        self.npc_id = npc_id
        self.npc_name = npc_name
        self.opinions: Dict[ReputationAspect, ReputationOpinion] = {}
        self.overall_opinion: float = 0.0  # Cached overall opinion
        self.opinion_update_time = time.time()

        # How this NPC weighs different aspects (personality-dependent)
        self.aspect_importance: Dict[ReputationAspect, float] = {
            aspect: 0.5 for aspect in ReputationAspect  # Default equal weighting
        }

    def get_or_create_opinion(self, aspect: ReputationAspect) -> ReputationOpinion:
        """Get existing opinion or create neutral one."""
        if aspect not in self.opinions:
            self.opinions[aspect] = ReputationOpinion(
                aspect=aspect, score=0.0, confidence=0.1, source="unknown", last_updated=time.time()
            )
        return self.opinions[aspect]

    def update_opinion_from_action(self, action_type: str, outcome: str, context: Dict[str, Any]):
        """Update reputation based on player action this NPC witnessed or heard about."""

        # Map actions to reputation aspects
        action_mappings = {
            "help_npc": {ReputationAspect.GENEROSITY: 0.3, ReputationAspect.TRUSTWORTHINESS: 0.2},
            "complete_quest": {ReputationAspect.RELIABILITY: 0.4, ReputationAspect.PROBLEM_SOLVING: 0.3},
            "pay_debt": {ReputationAspect.HONESTY: 0.3, ReputationAspect.TRUSTWORTHINESS: 0.2},
            "break_promise": {ReputationAspect.TRUSTWORTHINESS: -0.4, ReputationAspect.RELIABILITY: -0.3},
            "cheat_in_deal": {ReputationAspect.HONESTY: -0.5, ReputationAspect.BUSINESS_ACUMEN: -0.2},
            "win_fight": {ReputationAspect.COMBAT_SKILL: 0.4},
            "lose_fight": {ReputationAspect.COMBAT_SKILL: -0.2},
            "successful_trade": {ReputationAspect.BUSINESS_ACUMEN: 0.3, ReputationAspect.WEALTH: 0.1},
            "charity_donation": {ReputationAspect.GENEROSITY: 0.4, ReputationAspect.WEALTH: 0.2},
            "rude_behavior": {ReputationAspect.SOCIAL_CHARM: -0.3, ReputationAspect.RESPECT_FOR_AUTHORITY: -0.2},
        }

        if action_type in action_mappings:
            for aspect, score_change in action_mappings[action_type].items():
                opinion = self.get_or_create_opinion(aspect)

                # Determine if this was direct experience or hearsay
                is_direct = context.get("witnessed_directly", False)
                confidence_boost = 0.3 if is_direct else 0.1

                experience_desc = f"{action_type}: {outcome}"
                if not is_direct:
                    source_npc = context.get("source_npc", "someone")
                    experience_desc = f"heard that player did {action_type} with result {outcome} (from {source_npc})"

                opinion.update_from_experience(opinion.score + score_change, experience_desc, confidence_boost)

        # Recalculate overall opinion
        self._calculate_overall_opinion()

    def _calculate_overall_opinion(self):
        """Calculate overall opinion as weighted average of aspect opinions."""
        if not self.opinions:
            self.overall_opinion = 0.0
            return

        total_weight = 0.0
        weighted_sum = 0.0

        for aspect, opinion in self.opinions.items():
            importance = self.aspect_importance.get(aspect, 0.5)
            weight = importance * opinion.confidence

            weighted_sum += opinion.score * weight
            total_weight += weight

        if total_weight > 0:
            self.overall_opinion = weighted_sum / total_weight
        else:
            self.overall_opinion = 0.0

        self.opinion_update_time = time.time()

    def get_opinion_summary(self) -> Dict[str, Any]:
        """Get a summary of this NPC's opinions about the player."""
        summary = {
            "overall_opinion": self.overall_opinion,
            "opinion_strength": sum(op.confidence for op in self.opinions.values()) / max(1, len(self.opinions)),
            "aspects": {},
        }

        for aspect, opinion in self.opinions.items():
            if opinion.confidence > 0.2:  # Only include opinions they're somewhat confident about
                summary["aspects"][aspect.value] = {
                    "score": opinion.score,
                    "confidence": opinion.confidence,
                    "source": opinion.source,
                }

        return summary

    def get_gossip_to_share(self) -> Optional[Tuple[ReputationAspect, float, str]]:
        """Get an opinion this NPC might share as gossip."""
        # Share opinions they're confident about
        confident_opinions = [
            (aspect, opinion)
            for aspect, opinion in self.opinions.items()
            if opinion.confidence > 0.5 and abs(opinion.score) > 0.2
        ]

        if not confident_opinions:
            return None

        # Prefer strong opinions (positive or negative)
        aspect, opinion = max(confident_opinions, key=lambda x: abs(x[1].score) * x[1].confidence)

        # Create gossip description
        if opinion.score > 0.5:
            gossip_desc = f"player is quite {aspect.value}"
        elif opinion.score < -0.5:
            gossip_desc = f"player lacks {aspect.value}"
        else:
            gossip_desc = f"player has average {aspect.value}"

        return aspect, opinion.score, gossip_desc


class ReputationNetwork:
    """Manages the entire social network and reputation spreading."""

    def __init__(self):
        self.npc_reputations: Dict[str, NPCReputation] = {}
        self.social_connections: Dict[Tuple[str, str], SocialConnection] = {}
        self.global_events: List[Tuple[str, str, Dict[str, Any], float]] = []  # action, outcome, context, timestamp

    def get_or_create_reputation(self, npc_id: str, npc_name: str) -> NPCReputation:
        """Get existing reputation tracker or create new one."""
        if npc_id not in self.npc_reputations:
            self.npc_reputations[npc_id] = NPCReputation(npc_id, npc_name)
            logger.info(f"Created reputation tracker for {npc_name}")
        return self.npc_reputations[npc_id]

    def add_social_connection(self, npc1_id: str, npc2_id: str, strength: float = 0.5, trust: float = 0.5):
        """Add a social connection between two NPCs."""
        # Use sorted tuple to avoid duplicates
        connection_key = tuple(sorted([npc1_id, npc2_id]))

        if connection_key not in self.social_connections:
            self.social_connections[connection_key] = SocialConnection(npc1_id, npc2_id, strength)
            self.social_connections[connection_key].trust_level = trust
            logger.debug(f"Added social connection: {npc1_id} <-> {npc2_id} (strength: {strength})")

    def record_player_action(self, action_type: str, outcome: str, witnesses: List[str], context: Dict[str, Any]):
        """Record a player action and update relevant NPC opinions."""
        timestamp = time.time()

        # Add to global events
        self.global_events.append((action_type, outcome, context.copy(), timestamp))

        # Update opinions of direct witnesses
        for witness_id in witnesses:
            if witness_id in self.npc_reputations:
                witness_context = context.copy()
                witness_context["witnessed_directly"] = True
                self.npc_reputations[witness_id].update_opinion_from_action(action_type, outcome, witness_context)

        # Spread through gossip network (delayed effect)
        self._queue_gossip_spread(action_type, outcome, witnesses, context)

    def _queue_gossip_spread(
        self, action_type: str, outcome: str, initial_witnesses: List[str], context: Dict[str, Any]
    ):
        """Queue gossip to spread through the social network."""
        # This would be called periodically to simulate gossip spreading

        # Find NPCs connected to witnesses
        for witness_id in initial_witnesses:
            connected_npcs = self._get_connected_npcs(witness_id)

            for connected_id, connection in connected_npcs:
                if connection.should_share_gossip():
                    # Spread gossip with reduced impact
                    gossip_context = context.copy()
                    gossip_context["witnessed_directly"] = False
                    gossip_context["source_npc"] = witness_id

                    if connected_id in self.npc_reputations:
                        self.npc_reputations[connected_id].update_opinion_from_action(
                            action_type, outcome, gossip_context
                        )
                        connection.last_interaction = time.time()

    def _get_connected_npcs(self, npc_id: str) -> List[Tuple[str, SocialConnection]]:
        """Get all NPCs connected to the given NPC."""
        connected = []

        for connection_key, connection in self.social_connections.items():
            other_npc = connection.get_other_npc(npc_id)
            if other_npc:
                connected.append((other_npc, connection))

        return connected

    def simulate_gossip_round(self):
        """Simulate a round of gossip spreading between connected NPCs."""
        for connection in self.social_connections.values():
            if connection.should_share_gossip():
                # Get gossip from both NPCs
                npc1_reputation = self.npc_reputations.get(connection.npc1_id)
                npc2_reputation = self.npc_reputations.get(connection.npc2_id)

                if npc1_reputation and npc2_reputation:
                    # NPC1 shares gossip with NPC2
                    gossip1 = npc1_reputation.get_gossip_to_share()
                    if gossip1:
                        aspect, score, description = gossip1
                        npc2_opinion = npc2_reputation.get_or_create_opinion(aspect)
                        npc2_opinion.update_from_gossip(score, connection.get_trust_multiplier(), description)

                    # NPC2 shares gossip with NPC1
                    gossip2 = npc2_reputation.get_gossip_to_share()
                    if gossip2:
                        aspect, score, description = gossip2
                        npc1_opinion = npc1_reputation.get_or_create_opinion(aspect)
                        npc1_opinion.update_from_gossip(score, connection.get_trust_multiplier(), description)

                    connection.last_interaction = time.time()

    def get_overall_reputation_summary(self) -> Dict[str, Any]:
        """Get a summary of the player's reputation across all NPCs."""
        if not self.npc_reputations:
            return {"overall_score": 0.0, "reputation_level": "unknown", "npc_opinions": {}}

        # Calculate weighted average reputation
        total_weight = 0.0
        weighted_sum = 0.0
        npc_summaries = {}

        for npc_id, reputation in self.npc_reputations.items():
            opinion_strength = sum(op.confidence for op in reputation.opinions.values())
            weight = max(0.1, opinion_strength)  # Minimum weight so all NPCs have some influence

            weighted_sum += reputation.overall_opinion * weight
            total_weight += weight

            npc_summaries[npc_id] = reputation.get_opinion_summary()

        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Determine reputation level
        if overall_score > 0.6:
            rep_level = "hero"
        elif overall_score > 0.3:
            rep_level = "respected"
        elif overall_score > 0.0:
            rep_level = "trusted"
        elif overall_score > -0.3:
            rep_level = "unknown"
        elif overall_score > -0.6:
            rep_level = "suspicious"
        else:
            rep_level = "notorious"

        return {
            "overall_score": overall_score,
            "reputation_level": rep_level,
            "npc_opinions": npc_summaries,
            "social_connections": len(self.social_connections),
            "recent_events": len([e for e in self.global_events if time.time() - e[3] < 86400]),  # Last 24 hours
        }

    def create_default_social_network(self, npc_ids: List[str]):
        """Create a default social network between NPCs."""
        # Create connections based on likely relationships

        # Everyone knows each other in a small town, but with varying strength
        for i, npc1 in enumerate(npc_ids):
            for npc2 in npc_ids[i + 1 :]:
                # Random connection strength with bias towards moderate connections
                strength = random.uniform(0.2, 0.8)
                trust = random.uniform(0.3, 0.7)

                self.add_social_connection(npc1, npc2, strength, trust)

        # Add some stronger connections (friends/business partners)
        if len(npc_ids) >= 3:
            # Create a few strong friendships
            for _ in range(min(3, len(npc_ids) // 2)):
                npc1, npc2 = random.sample(npc_ids, 2)
                connection_key = tuple(sorted([npc1, npc2]))
                if connection_key in self.social_connections:
                    connection = self.social_connections[connection_key]
                    connection.connection_strength = min(1.0, connection.connection_strength + 0.3)
                    connection.trust_level = min(1.0, connection.trust_level + 0.2)
                    connection.gossip_frequency = min(1.0, connection.gossip_frequency + 0.2)


def setup_reputation_network_for_profession(
    reputation_network: ReputationNetwork, npc_id: str, npc_name: str, profession: str
):
    """Setup profession-specific reputation aspect weights."""
    reputation = reputation_network.get_or_create_reputation(npc_id, npc_name)

    if profession.lower() in ["merchant", "trader", "shopkeeper"]:
        # Merchants care more about business aspects
        reputation.aspect_importance.update(
            {
                ReputationAspect.HONESTY: 0.8,
                ReputationAspect.BUSINESS_ACUMEN: 0.7,
                ReputationAspect.WEALTH: 0.6,
                ReputationAspect.TRUSTWORTHINESS: 0.8,
                ReputationAspect.RELIABILITY: 0.7,
            }
        )

    elif profession.lower() in ["guard", "soldier"]:
        # Guards care about respect and combat prowess
        reputation.aspect_importance.update(
            {
                ReputationAspect.RESPECT_FOR_AUTHORITY: 0.9,
                ReputationAspect.COMBAT_SKILL: 0.7,
                ReputationAspect.RELIABILITY: 0.8,
                ReputationAspect.TRUSTWORTHINESS: 0.6,
            }
        )

    elif profession.lower() in ["bartender", "innkeeper"]:
        # Bartenders care about social aspects
        reputation.aspect_importance.update(
            {
                ReputationAspect.SOCIAL_CHARM: 0.8,
                ReputationAspect.GENEROSITY: 0.6,
                ReputationAspect.TRUSTWORTHINESS: 0.7,
                ReputationAspect.HONESTY: 0.6,
            }
        )

    elif profession.lower() in ["blacksmith", "craftsman"]:
        # Craftsmen value reliability and problem-solving
        reputation.aspect_importance.update(
            {
                ReputationAspect.RELIABILITY: 0.8,
                ReputationAspect.PROBLEM_SOLVING: 0.7,
                ReputationAspect.HONESTY: 0.7,
                ReputationAspect.RESPECT_FOR_AUTHORITY: 0.6,
            }
        )
