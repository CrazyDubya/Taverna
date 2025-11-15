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
    # Ensure score is clamped for tier lookup, though update_reputation should handle clamping.
    score = max(MIN_REPUTATION, min(MAX_REPUTATION, score))

    if score == 0:
        return "Neutral"

    # Iterate upwards for positive scores
    if score > 0:
        for threshold, name in reversed(REPUTATION_TIERS):
            if name in ["Neutral", "Unfriendly", "Disliked", "Hated", "Despised"]:  # Skip negative tiers
                continue
            if score >= threshold:  # This logic is a bit off for threshold based.
                # Let's use the REPUTATION_TIER_MAP ranges.
                pass  # Placeholder, will fix below

    # Corrected logic using REPUTATION_TIER_MAP approach (conceptual)
    # For simplicity, let's use the provided REPUTATION_TIERS list properly.
    # Iterate from highest tier downwards.

    # If score is exactly 0, it's Neutral
    if score == 0:
        return "Neutral"

    # For positive scores, iterate from high to low (excluding Neutral and below)
    if score > 0:
        for i in range(len(REPUTATION_TIERS) - 1, -1, -1):
            threshold, name = REPUTATION_TIERS[i]
            if name in ["Neutral", "Unfriendly", "Disliked", "Hated", "Despised"]:
                continue
            if score >= threshold:
                return name

    # For negative scores, iterate from low to high (excluding Neutral and above)
    if score < 0:
        for threshold, name in REPUTATION_TIERS:
            if name in ["Neutral", "Friendly", "Liked", "Trusted", "Hero"]:
                continue
            # For negative tiers, the score should be less than or equal to the tier's upper bound.
            # E.g., Hated is -75. If score is -75 or -80, it's Hated.
            # The REPUTATION_TIERS list is (threshold, name), meaning score >= threshold.
            # For negative, we want the "highest" negative tier they qualify for.
            # Example: score = -60. Disliked (-50), Unfriendly (-25). It's Disliked.
            # This means we find the *last* tier in the sorted list whose threshold is <= score.
            # Or, iterate upwards:

            # Corrected logic for negative scores
            # Find the tier that this score falls into.
            # E.g. score -60. Hated is -75, Disliked is -50. It's Disliked.
            # The current REPUTATION_TIERS is threshold to be >=
            # So, for -60:
            # - Despised (-101): -60 >= -101 (True)
            # - Hated (-75): -60 >= -75 (True)
            # - Disliked (-50): -60 >= -50 (False) -> So it was Hated. This is correct.

            # Let's re-verify the iteration for negative scores.
            # We want the "worst" tier they qualify for.
            # Iterate from "Despised" upwards. The last one they meet or exceed is their tier.
            selected_tier = "Unknown"  # Should not happen
            for threshold, name in REPUTATION_TIERS:
                if name in ["Neutral", "Friendly", "Liked", "Trusted", "Hero"]:
                    continue  # Only consider negative tiers
                if score >= threshold:
                    selected_tier = name
                else:  # If score is less than this threshold, they can't be in higher negative tiers
                    break
            return selected_tier

    # Fallback, though logic above should cover clamped scores.
    return "Neutral"  # Default fallback if no tier is matched (e.g. exactly 0 if not caught)


# Example usage:
# from core.player import PlayerState
# player = PlayerState()
# update_reputation(player, "villagers", 10) -> 10
# get_reputation_tier(get_reputation(player, "villagers")) -> "Friendly"
# update_reputation(player, "guards", -30) -> -30
# get_reputation_tier(get_reputation(player, "guards")) -> "Unfriendly"
# update_reputation(player, "guards", -1000) -> -100 (clamped)
# get_reputation_tier(get_reputation(player, "guards")) -> "Hated" (or Despised depending on exact thresholds)
# update_reputation(player, "nobles", 1000) -> 100 (clamped)
# get_reputation_tier(get_reputation(player, "nobles")) -> "Hero"
# get_reputation_tier(0) -> "Neutral"
# get_reputation_tier(-5) -> "Unfriendly"
# get_reputation_tier(-55) -> "Disliked"
# get_reputation_tier(-80) -> "Hated"


# Refined get_reputation_tier for clarity
def get_reputation_tier_v2(score: int) -> str:
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
            return "Despised"  # Corrected: Hated/Despised based on typical use
        if score <= -51:
            return "Hated"  # Hated: -75 to -51
        if score <= -26:
            return "Disliked"  # Disliked: -50 to -26
        if score <= -1:
            return "Unfriendly"  # Unfriendly: -25 to -1

    return "Neutral"  # Should be caught by score == 0, but as a fallback.


# Overwrite the previous function with the refined one for use.
get_reputation_tier = get_reputation_tier_v2


class ReputationManager:
    """Manager class for handling reputation operations."""

    def __init__(self):
        pass

    def get_reputation(self, player_state: "PlayerState", entity_id: str) -> int:
        return get_reputation(player_state, entity_id)

    def update_reputation(self, player_state: "PlayerState", entity_id: str, change: int) -> int:
        return update_reputation(player_state, entity_id, change)

    def get_reputation_tier(self, score: int) -> str:
        return get_reputation_tier(score)
