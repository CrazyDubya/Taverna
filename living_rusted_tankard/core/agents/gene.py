"""
Gene the Bartender - The Anchor Agent

Gene is the owner and bartender of The Living Rusted Tankard.
He is the social hub - everyone passes through his tavern, and he
observes, remembers, and influences all.

Role in Ecosystem:
- Information broker (knows everyone's business)
- Economic anchor (sets prices, offers jobs)
- Moral authority (respected elder figure)
- Conflict mediator (intervenes in disputes)
- Secret keeper (knows things he'll never tell)

Gene creates stability in the social ecosystem while hiding
his own deeper motivations and past.
"""

from typing import Dict, Any
import time

from .agent import DeepAgent
from .personality import Personality, Value
from .needs import PhysiologicalNeeds, Drive, NeedType, create_standard_drives
from .emotions import EmotionalState, EmotionType
from .beliefs import BeliefSystem, BeliefType
from .memory import EpisodicMemory, SemanticMemory
from .goals import GoalHierarchy, GoalType


def create_gene() -> DeepAgent:
    """
    Create Gene the Bartender.

    Background:
    Gene has owned the tavern for 20 years, but his past before that
    is mysterious. He's shrewd but fair, observant but discrete.
    He knows everyone's secrets but reveals nothing of his own.

    His position gives him:
    - Social power (information, mediation)
    - Economic power (controls jobs, prices)
    - Moral authority (respected figure)

    But he carries:
    - Loneliness (knows everyone, trusted by few)
    - Secrets (his past is deliberately obscured)
    - Responsibility (the tavern is his life's work)
    - Weariness (20 years of other people's problems)
    """

    # Gene's personality: Shrewd observer with carefully cultivated persona
    personality = Personality(
        openness=0.7,  # Curious about people, though he hides it
        conscientiousness=0.9,  # Extremely reliable and organized
        extraversion=0.6,  # Socially skilled but not naturally outgoing
        agreeableness=0.6,  # Fair but not a pushover
        neuroticism=0.3,  # Very emotionally stable (or appears to be)
        risk_tolerance=0.4,  # Cautious, calculated
        optimism=0.5,  # Realistic, has seen it all
        patience=0.9,  # Extremely patient from years of bartending
        values=[
            Value("stability", 0.95, "The tavern must endure"),
            Value("discretion", 0.90, "Secrets are sacred"),
            Value("fairness", 0.80, "Treat customers fairly, within reason"),
            Value("independence", 0.75, "Beholden to no one"),
            Value("knowledge", 0.85, "Information is power"),
        ],
    )

    # Gene's needs are well-balanced - he's found equilibrium
    needs = PhysiologicalNeeds()

    # Well-rested (unlike Sarah)
    needs.needs[NeedType.REST].level = 0.7

    # Achievement need is satisfied - successful business
    needs.needs[NeedType.ACHIEVEMENT].level = 0.8

    # But loneliness lurks beneath
    needs.needs[NeedType.BELONGING].level = 0.4  # Knows many, close to few
    needs.needs[NeedType.INTIMACY] = needs.needs[NeedType.BELONGING]  # No close confidants

    # High need for respect (and gets it)
    needs.needs[NeedType.RESPECT].level = 0.8

    # Drives reflect his role
    drives = create_standard_drives()
    for drive in drives:
        if drive.name == "autonomy":
            drive.intensity = 0.9  # Values independence highly
        elif drive.name == "achievement":
            drive.intensity = 0.7  # Already achieved his main goal
        elif drive.name == "affiliation":
            drive.intensity = 0.5  # Wants connection but wary
        elif drive.name == "purpose":
            drive.intensity = 0.8  # The tavern IS his purpose

    # Emotional state: Calm, watchful, slightly melancholic
    emotions = EmotionalState()

    # Gene maintains calm almost always
    emotions.trigger_emotion(
        EmotionType.TRUST,
        intensity=0.5,
        trigger="Years of reliable relationships with regulars",
    )

    # Underlying sadness from loneliness
    emotions.trigger_emotion(
        EmotionType.SADNESS, intensity=0.2, trigger="Isolated by his role and secrets"
    )

    # Mild anticipation - always watching for what comes next
    emotions.trigger_emotion(
        EmotionType.ANTICIPATION, intensity=0.4, trigger="Observing the ebb and flow of tavern life"
    )

    # Gene's beliefs are extensive - he knows everyone
    beliefs = BeliefSystem()

    # Core beliefs about the world
    beliefs.add_belief(
        BeliefType.FACT,
        "world",
        "Everyone has secrets, including me",
        confidence=1.0,
        evidence="Twenty years of observation",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "world",
        "The tavern is a sanctuary - people need a place to belong",
        confidence=0.95,
        evidence="Seen desperate people find community here",
    )

    beliefs.add_belief(
        BeliefType.NORM,
        "business",
        "Fair prices build loyalty, loyalty builds success",
        confidence=0.9,
        evidence="Twenty years of business",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "self",
        "I am a good judge of character",
        confidence=0.85,
        evidence="Rarely surprised by people anymore",
    )

    # Beliefs about specific people (will be updated through observation)
    # Sarah
    sarah_tom = beliefs.get_theory_of_mind("sarah_merchant")
    sarah_tom.update_perceived_trait("hardworking", 0.9)
    sarah_tom.update_perceived_trait("prideful", 0.8)
    sarah_tom.update_perceived_trait("trustworthy", 0.8)
    sarah_tom.update_perceived_goal("survive business crisis")
    sarah_tom.model_confidence = 0.8  # Knows her well

    # Gene's memories span 20 years
    episodic_memory = EpisodicMemory()

    # Formative memory: Opening the tavern
    episodic_memory.add_memory(
        content="The day I bought this place. A new beginning, a chance to be someone else.",
        location="tavern",
        participants=[],
        emotional_valence=0.8,
        emotional_intensity=0.9,
        importance=1.0,
    )

    # Memory: First time Sarah came in, years ago
    episodic_memory.add_memory(
        content="Young Sarah came in, full of hope and ambition. Reminded me of myself once.",
        location="tavern_main_hall",
        participants=["sarah_merchant"],
        emotional_valence=0.5,
        emotional_intensity=0.6,
        importance=0.7,
    )

    # Memory: Recent - Sarah's struggle
    episodic_memory.add_memory(
        content="Sarah's hands shook when she counted her coin. She's in trouble. Pride won't let her ask.",
        location="tavern_main_hall",
        participants=["sarah_merchant"],
        emotional_valence=-0.4,
        emotional_intensity=0.6,
        importance=0.8,
    )

    # Memory: His mysterious past (deliberately vague)
    episodic_memory.add_memory(
        content="Before the tavern, before this life. That person is dead now. Let him stay dead.",
        location="unknown",
        participants=[],
        emotional_valence=-0.6,
        emotional_intensity=0.8,
        importance=0.95,
    )

    # Memory: A quiet moment of satisfaction
    episodic_memory.add_memory(
        content="Full tavern, everyone laughing and drinking. This is why I do it.",
        location="tavern_main_hall",
        participants=["regulars"],
        emotional_valence=0.7,
        emotional_intensity=0.7,
        importance=0.7,
    )

    # Gene's semantic knowledge is vast
    semantic_memory = SemanticMemory()

    semantic_memory.add_knowledge(
        "ale_price", "Ale sells for 3 gold, costs me 1 gold", confidence=1.0
    )

    semantic_memory.add_knowledge(
        "sarah_situation",
        "Sarah owes approximately 50 gold and is too proud to ask for help",
        confidence=0.9,
    )

    semantic_memory.add_knowledge(
        "tavern_regulars",
        "About 20 regular customers, another 30 occasional visitors",
        confidence=0.95,
    )

    semantic_memory.add_knowledge(
        "tavern_profit", "Tavern makes ~100 gold profit per month", confidence=1.0
    )

    semantic_memory.add_knowledge(
        "my_past",
        "My past is my business. The less people know, the better.",
        confidence=1.0,
    )

    # Gene's goals reflect his role as anchor
    goal_hierarchy = GoalHierarchy()

    # Primary goal: Maintain the tavern
    goal_hierarchy.add_goal(
        description="Keep the tavern profitable and stable",
        goal_type=GoalType.MAINTENANCE,
        priority=0.95,
        success_condition="Monthly profit > 80 gold, no major incidents",
        motivated_by=["survival", "achievement", "purpose"],
    )

    # Observation goal: Understand everyone
    goal_hierarchy.add_goal(
        description="Observe and understand the tavern's social dynamics",
        goal_type=GoalType.EXPLORATION,
        priority=0.7,
        success_condition="Know what's happening with regulars",
        motivated_by=["exploration", "autonomy"],  # Knowledge = power
    )

    # Helper goal: Discrete assistance
    goal_hierarchy.add_goal(
        description="Help struggling patrons without them losing face",
        goal_type=GoalType.SOCIAL,
        priority=0.6,
        success_condition="People succeed with subtle help",
        motivated_by=["affiliation", "purpose"],
    )

    # Personal goal: Protect his secrets
    goal_hierarchy.add_goal(
        description="Keep my past hidden",
        goal_type=GoalType.AVOIDANCE,
        priority=0.9,
        success_condition="No one learns about my previous life",
        motivated_by=["survival", "autonomy"],
    )

    # Suppressed goal: Find genuine connection
    goal_hierarchy.add_goal(
        description="Find someone I can truly trust and open up to",
        goal_type=GoalType.SOCIAL,
        priority=0.4,  # Low priority, high fear
        success_condition="Have at least one real friend who knows the truth",
        motivated_by=["affiliation"],
    )

    # Create the agent
    gene = DeepAgent(
        name="Gene",
        agent_id="gene_bartender",
        personality=personality,
        needs=needs,
        drives=drives,
        emotions=emotions,
        beliefs=beliefs,
        episodic_memory=episodic_memory,
        semantic_memory=semantic_memory,
        goals=goal_hierarchy,
        current_location="behind_bar",
        current_activity="observing_patrons",
    )

    return gene


def get_gene_narrative_description() -> str:
    """Gene's observable description from player perspective."""
    return """
Gene the Bartender stands behind the bar with the ease of someone
who has occupied that exact spot for decades. His movements are
economical, practiced - every motion serving a purpose, nothing wasted.

He's in his late forties, with greying hair kept short and practical.
His face is weathered but not unkind, lined with the patience of someone
who has heard every story, twice. His eyes are his most striking feature -
sharp, observant, missing nothing. They track every entrance, every
conversation, every subtle shift in the room's atmosphere.

He speaks sparingly, but when he does, people listen. There's an
authority to him that comes not from volume but from certainty. He
knows his domain completely.

With customers, he's professional and fair. He remembers everyone's
name, their usual drink, sometimes even their troubles - though he
never mentions them unless invited. Some mistake his discretion for
indifference, but those who've been coming long enough know better.

There's a loneliness about him, visible in quiet moments when he
thinks no one is watching. He's surrounded by people yet somehow
apart, separated by an invisible wall of his own making.

Occasionally, when someone mentions the time before he owned the
tavern, his expression becomes carefully neutral. He deflects,
changes the subject with practiced ease. Whatever Gene was before
he became Gene the Bartender, that man is dead and buried.

Or perhaps just very well hidden.
"""


if __name__ == "__main__":
    print("Creating Gene the Bartender...")
    gene = create_gene()

    print("\n" + "=" * 60)
    print("GENE'S INTERNAL STATE")
    print("=" * 60)

    state = gene.get_internal_state_summary()

    print(f"\nName: {state['name']}")
    print(f"Location: {state['location']}")
    print(f"Overall Wellbeing: {state['wellbeing']:.1%}")

    print(f"\nEmotional State:")
    print(f"  Mood: {state['emotional_state']['mood']}")
    print(f"  Dominant Emotion: {state['emotional_state']['dominant_emotion']}")

    print(f"\nActive Goal: {state['active_goal']}")

    print(f"\nTheory of Mind (Sarah):")
    sarah_tom = gene.beliefs.get_theory_of_mind("sarah_merchant")
    print(f"  Perceived Traits: {sarah_tom.perceived_traits}")
    print(f"  Perceived Goals: {sarah_tom.perceived_goals}")
    print(f"  Trust Estimate: {sarah_tom.get_trust_estimate():.0%}")

    print("\n" + "=" * 60)
    print("NARRATIVE DESCRIPTION")
    print("=" * 60)
    print(get_gene_narrative_description())

    print("\n" + "=" * 60)
    print("Gene the Bartender: The anchor who sees all, reveals nothing.")
    print("=" * 60)
