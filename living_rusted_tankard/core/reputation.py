from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .player import PlayerState

MIN_REPUTATION = -100
MAX_REPUTATION = 100

# Reputation tiers: (threshold, tier_name)
# Ordered from lowest to highest threshold.
REPUTATION_TIERS = [
    (-101, "Despised"),  # Should not happen if clamped
    (-75, "Hated"),
    (-50, "Disliked"),
    (-25, "Unfriendly"),
    (0, "Neutral"),
    (25, "Friendly"),
    (50, "Liked"),
    (75, "Trusted"),
    (101, "Hero"),  # Should not happen if clamped
]
# A simpler way for tiers if thresholds are fixed:
REPUTATION_TIER_MAP = {
    "Despised": (-100, -76),  # Theoretical, as we clamp
    "Hated": (-75, -51),
    "Disliked": (-50, -26),
    "Unfriendly": (-25, -1),  # Score of 0 is Neutral
    "Neutral": (0, 0),  # Exact Neutral
    "Friendly": (1, 25),
    "Liked": (26, 50),
    "Trusted": (51, 75),
    "Hero": (76, 100),  # Theoretical, as we clamp
}


def get_reputation(player_state: "PlayerState", entity_id: str) -> int:
    """
    Returns the player's reputation with a given NPC or faction.
    Defaults to 0 (Neutral) if no specific reputation is recorded.
    """
    return player_state.reputation.get(entity_id, 0)


def update_reputation(player_state: "PlayerState", entity_id: str, change: int) -> int:
    """
    Modifies the player's reputation with an entity by the 'change' amount.
    Ensures scores are clamped between MIN_REPUTATION and MAX_REPUTATION.
    Returns the new reputation score.
    """
    current_score = player_state.reputation.get(entity_id, 0)
    new_score = current_score + change

    # Clamp the new score
    clamped_score = max(MIN_REPUTATION, min(MAX_REPUTATION, new_score))

    player_state.reputation[entity_id] = clamped_score
    return clamped_score


def get_reputation_tier(score: int) -> str:
    """
    Translates a numerical reputation score into a descriptive tier name.
    """
    score = max(MIN_REPUTATION, min(MAX_REPUTATION, score))

    if score == 0:
        return "Neutral"

    # Check positive tiers from highest to lowest threshold
    if score > 0:
        if score >= 76:
            return "Hero"
        if score >= 51:
            return "Trusted"
        if score >= 26:
            return "Liked"
        if score >= 1:
            return "Friendly"  # Covers 1 to 25

    # Check negative tiers from lowest (most negative) to highest threshold
    if score < 0:
        if score <= -76:
            return "Despised"
        if score <= -51:
            return "Hated"  # Hated: -75 to -51
        if score <= -26:
            return "Disliked"  # Disliked: -50 to -26
        if score <= -1:
            return "Unfriendly"  # Unfriendly: -25 to -1

    return "Neutral"  # Should be caught by score == 0, but as a fallback.


class ReputationManager:
    """Manager class for handling reputation operations."""

    def __init__(self):
        pass

    def get_reputation(self, player_state: "PlayerState", entity_id: str) -> int:
        return get_reputation(player_state, entity_id)

    def update_reputation(
        self, player_state: "PlayerState", entity_id: str, change: int
    ) -> int:
        return update_reputation(player_state, entity_id, change)

    def get_reputation_tier(self, score: int) -> str:
        return get_reputation_tier(score)
