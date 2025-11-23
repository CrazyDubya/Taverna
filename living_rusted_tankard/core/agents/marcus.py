"""
Marcus the Wanderer - The Mystery Agent

Marcus is the enigmatic regular who sits in the corner, pays in
unusual coins, and speaks in cryptic half-truths. He represents
the unknown, the larger world beyond the tavern.

Role in Ecosystem:
- Plot catalyst (his presence raises questions)
- Information source (knows things about the outside world)
- Trust test (who will he open up to?)
- Wildcard (unpredictable loyalties)
- Observer (watches and judges)

Marcus creates tension through mystery and possibility.
His true motivations remain unclear even to him sometimes.
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


def create_marcus() -> DeepAgent:
    """
    Create Marcus the Wanderer.

    Background:
    Marcus arrived at the tavern six months ago and has been a quiet
    regular ever since. He pays in foreign coins, occasionally mentions
    distant places, and deflects personal questions with poetic evasions.

    Is he:
    - A spy? (observing for someone)
    - A fugitive? (hiding from something)
    - A scholar? (studying the tavern)
    - Something else entirely? (even he's not sure anymore)

    His mysteriousness is partly cultivated, partly genuine confusion
    about his own purpose. He's lost something and searching for it,
    but has forgotten what exactly.
    """

    # Marcus's personality: Introspective, guarded, philosophical
    personality = Personality(
        openness=0.95,  # Extremely curious and imaginative
        conscientiousness=0.5,  # Somewhat disorganized, flows with circumstances
        extraversion=0.3,  # Introverted, prefers observation
        agreeableness=0.5,  # Neutral - neither hostile nor warm
        neuroticism=0.6,  # Prone to existential anxiety
        risk_tolerance=0.7,  # Surprisingly bold when it matters
        optimism=0.4,  # Mildly pessimistic, world-weary
        patience=0.9,  # Extremely patient, can wait indefinitely
        values=[
            Value("truth", 0.95, "The truth, whatever it costs"),
            Value("freedom", 0.90, "Unchained by expectations or obligations"),
            Value("mystery", 0.85, "Some things should remain unknown"),
            Value("authenticity", 0.80, "Be genuine, even if cryptic"),
            Value("wisdom", 0.75, "Understanding over mere knowledge"),
        ],
    )

    # Marcus's needs reflect his rootless existence
    needs = PhysiologicalNeeds()

    # Well-rested (sleeps a lot, actually)
    needs.needs[NeedType.REST].level = 0.7

    # Low belonging (doesn't feel he fits anywhere)
    needs.needs[NeedType.BELONGING].level = 0.3

    # High curiosity (always seeking)
    needs.needs[NeedType.CURIOSITY].level = 0.2  # Urgent
    needs.needs[NeedType.CURIOSITY].urgency_threshold = 0.4

    # Moderate achievement (wants to figure things out)
    needs.needs[NeedType.ACHIEVEMENT].level = 0.4

    # Purpose is critically low (lost his direction)
    needs.needs[NeedType.PURPOSE].level = 0.2
    needs.needs[NeedType.PURPOSE].urgency_threshold = 0.5

    # Drives reflect his quest
    drives = create_standard_drives()
    for drive in drives:
        if drive.name == "exploration":
            drive.intensity = 0.95  # Compelled to seek
        elif drive.name == "autonomy":
            drive.intensity = 0.9  # Fiercely independent
        elif drive.name == "purpose":
            drive.intensity = 0.8  # Desperately needs meaning
        elif drive.name == "affiliation":
            drive.intensity = 0.3  # Wants but fears connection

    # Emotional state: Melancholic, contemplative, occasionally hopeful
    emotions = EmotionalState()

    # Underlying sadness from loss (what did he lose? he can't quite remember)
    emotions.trigger_emotion(
        EmotionType.SADNESS,
        intensity=0.4,
        trigger="A sense of something lost, just out of reach",
    )

    # Curiosity drives him
    emotions.trigger_emotion(
        EmotionType.ANTICIPATION,
        intensity=0.6,
        trigger="The mystery calls, answers hide in shadows",
    )

    # Occasional hope
    emotions.trigger_emotion(
        EmotionType.HOPE,
        intensity=0.3,
        trigger="Perhaps here, in this strange tavern, I'll find what I seek",
    )

    # Fear underneath
    emotions.trigger_emotion(
        EmotionType.FEAR,
        intensity=0.3,
        trigger="What if the truth is worse than not knowing?",
    )

    # Marcus's beliefs are philosophical and uncertain
    beliefs = BeliefSystem()

    # Core beliefs
    beliefs.add_belief(
        BeliefType.FACT,
        "world",
        "Reality is layered - what you see is rarely all there is",
        confidence=0.9,
        evidence="Personal experience beyond the veil",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "tavern",
        "This tavern is not what it seems - it exists at a crossroads",
        confidence=0.7,
        evidence="The front door never opens, yet people arrive. Temporal inconsistencies.",
    )

    beliefs.add_belief(
        BeliefType.PROBABILITY,
        "self",
        "I was sent here for a purpose, but I've forgotten what",
        confidence=0.6,
        evidence="Gaps in memory, unusual knowledge, foreign coins",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "gene",
        "Gene knows more than he reveals - he's hiding something significant",
        confidence=0.8,
        evidence="His careful evasions, the way he watches everyone",
    )

    beliefs.add_belief(
        BeliefType.NORM,
        "truth",
        "People fear the truth more than they fear lies",
        confidence=0.85,
        evidence="Observed countless times",
    )

    # Theory of mind about Gene (studying him)
    gene_tom = beliefs.get_theory_of_mind("gene_bartender")
    gene_tom.update_perceived_trait("secretive", 0.9)
    gene_tom.update_perceived_trait("observant", 0.95)
    gene_tom.update_perceived_trait("wise", 0.7)
    gene_tom.update_perceived_goal("protect the tavern and its secrets")
    gene_tom.model_confidence = 0.6  # Unsure, Gene is hard to read

    # Theory of mind about Sarah (sympathetic observer)
    sarah_tom = beliefs.get_theory_of_mind("sarah_merchant")
    sarah_tom.update_perceived_trait("proud", 0.8)
    sarah_tom.update_perceived_trait("struggling", 0.9)
    sarah_tom.update_perceived_trait("honest", 0.8)
    sarah_tom.update_perceived_goal("survive without compromising independence")
    sarah_tom.model_confidence = 0.7

    # Marcus's memories are fragmented
    episodic_memory = EpisodicMemory()

    # Earliest tavern memory
    episodic_memory.add_memory(
        content="I walked through... something. And then I was here. How long ago? Six months? Six years?",
        location="tavern_entrance",
        participants=[],
        emotional_valence=-0.3,
        emotional_intensity=0.8,
        importance=0.95,
    )

    # Memory: First conversation with Gene
    episodic_memory.add_memory(
        content="Gene asked no questions about where I came from. He simply poured a drink. Knowing eyes.",
        location="tavern_bar",
        participants=["gene_bartender"],
        emotional_valence=0.4,
        emotional_intensity=0.7,
        importance=0.8,
    )

    # Memory: Observation of Sarah
    episodic_memory.add_memory(
        content="The merchant woman counts coins with shaking hands. I know that fear. I've felt it.",
        location="tavern_main_hall",
        participants=["sarah_merchant"],
        emotional_valence=-0.4,
        emotional_intensity=0.6,
        importance=0.6,
    )

    # Fragment: Before the tavern
    episodic_memory.add_memory(
        content="A tower? A library? Books and stars and... someone's voice calling my name. Lost now.",
        location="unknown",
        participants=["unknown"],
        emotional_valence=-0.7,
        emotional_intensity=0.9,
        importance=1.0,
    )

    # Recent: A moment of clarity
    episodic_memory.add_memory(
        content="Rain on the windows. Gene polishing a glass. Suddenly felt: I'm exactly where I need to be.",
        location="tavern_main_hall",
        participants=["gene_bartender"],
        emotional_valence=0.6,
        emotional_intensity=0.7,
        importance=0.7,
    )

    # Marcus's knowledge is eclectic and strange
    semantic_memory = SemanticMemory()

    semantic_memory.add_knowledge(
        "tavern_anomaly",
        "The tavern exists outside normal time and space - the front door has never opened",
        confidence=0.9,
    )

    semantic_memory.add_knowledge(
        "languages",
        "I can speak seven languages but don't remember learning them",
        confidence=1.0,
    )

    semantic_memory.add_knowledge(
        "astronomical_knowledge",
        "The stars here are wrong - or perhaps I'm from somewhere else",
        confidence=0.7,
    )

    semantic_memory.add_knowledge(
        "my_coins",
        "My coins bear symbols I don't recognize, from places I can't name",
        confidence=1.0,
    )

    semantic_memory.add_knowledge(
        "gene_past",
        "Gene was someone else before. A warrior? A nobleman? The hands remember violence.",
        confidence=0.5,
    )

    # Marcus's goals are existential
    goal_hierarchy = GoalHierarchy()

    # Primary: Understand his purpose
    goal_hierarchy.add_goal(
        description="Discover why I was brought to this tavern",
        goal_type=GoalType.EXPLORATION,
        priority=0.95,
        success_condition="Remember my purpose and origins",
        motivated_by=["exploration", "purpose"],
    )

    # Observation: Study the tavern's mystery
    goal_hierarchy.add_goal(
        description="Uncover the truth about the tavern's nature",
        goal_type=GoalType.EXPLORATION,
        priority=0.85,
        success_condition="Understand why the front door never opens",
        motivated_by=["exploration"],
    )

    # Social: Connect with Gene (kindred secret-keeper)
    goal_hierarchy.add_goal(
        description="Earn Gene's trust and learn his story",
        goal_type=GoalType.SOCIAL,
        priority=0.7,
        success_condition="Gene shares his past with me",
        motivated_by=["affiliation", "exploration"],
    )

    # Helper: Guide others subtly
    goal_hierarchy.add_goal(
        description="Help those who are lost, as I am lost",
        goal_type=GoalType.SOCIAL,
        priority=0.6,
        success_condition="Offer cryptic wisdom when needed",
        motivated_by=["affiliation", "purpose"],
    )

    # Avoidance: Don't remember too quickly
    goal_hierarchy.add_goal(
        description="Let the truth reveal itself in its own time",
        goal_type=GoalType.AVOIDANCE,
        priority=0.5,
        success_condition="Don't force remembering - some doors open from the other side",
        motivated_by=["autonomy", "wisdom"],
    )

    # Create the agent
    marcus = DeepAgent(
        name="Marcus",
        agent_id="marcus_wanderer",
        personality=personality,
        needs=needs,
        drives=drives,
        emotions=emotions,
        beliefs=beliefs,
        episodic_memory=episodic_memory,
        semantic_memory=semantic_memory,
        goals=goal_hierarchy,
        current_location="corner_table",
        current_activity="observing_and_contemplating",
    )

    return marcus


def get_marcus_narrative_description() -> str:
    """Marcus's observable description."""
    return """
Marcus sits in his usual corner, a figure of stillness in the tavern's
bustle. He's perhaps thirty-five, though something about him suggests
he could be younger or far older. His clothes are well-made but worn,
practical yet bearing subtle embroidery in patterns that don't quite
match any local style.

His eyes are his most notable feature - grey, distant, as though looking
at something just beyond the visible world. When he watches the room
(which is often), his gaze is intense but not threatening. More like
a scholar observing an experiment, or an artist studying a scene.

He speaks rarely, and when he does, his voice is soft but clear. His
words tend toward the poetic, the cryptic. He answers questions with
questions, shares observations that feel profound or utterly obscure,
depending on the listener. Some think him mad. Others, wise. Most
simply find him unsettling.

When he pays for his drinks, he places unusual coins on the bar -
silver pieces bearing unfamiliar symbols, sometimes with a strange
weight to them. Gene accepts them without comment.

Occasionally, Marcus will mutter to himself in languages no one
recognizes. Or he'll trace patterns in spilled wine, geometric shapes
that somehow feel significant. Or he'll freeze mid-movement, as though
suddenly remembering something, then shake his head and continue.

Despite his strangeness, there's a gentleness to him. When Sarah
dropped her ledger once, scattering papers everywhere, Marcus helped
gather them without a word, his touch careful, respectful. When a
drunk patron became aggressive, Marcus simply looked at him, and the
man deflated, apologized, left quietly.

He seems to carry a weight of knowledge he can't quite access, like
a book written in a language he's forgotten how to read.

Those who've sat with him longest swear that sometimes, in certain
lights, they can almost see... something else. A shadow that doesn't
quite match. A shimmer in the air around him.

But that's probably just the ale talking.

Probably.
"""


if __name__ == "__main__":
    print("Creating Marcus the Wanderer...")
    marcus = create_marcus()

    print("\n" + "=" * 60)
    print("MARCUS'S INTERNAL STATE")
    print("=" * 60)

    state = marcus.get_internal_state_summary()

    print(f"\nName: {state['name']}")
    print(f"Wellbeing: {state['wellbeing']:.1%}")
    print(f"Urgent Needs: {state['urgent_needs']}")

    print(f"\nEmotional State:")
    print(f"  Mood: {state['emotional_state']['mood']}")
    print(f"  Active Emotions: {list(state['emotional_state']['active_emotions'].keys())}")

    print(f"\nActive Goal: {state['active_goal']}")

    print(f"\nBelief about the tavern:")
    tavern_belief = marcus.beliefs.get_belief("tavern")
    if tavern_belief:
        print(f"  '{tavern_belief.content}' (confidence: {tavern_belief.confidence:.0%})")

    print("\n" + "=" * 60)
    print("NARRATIVE DESCRIPTION")
    print("=" * 60)
    print(get_marcus_narrative_description())

    print("\n" + "=" * 60)
    print("Marcus: The mystery who seeks mysteries.")
    print("=" * 60)
