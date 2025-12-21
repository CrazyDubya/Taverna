"""
Raven the Thief - The Opportunist Agent

Raven is a skilled pickpocket and smuggler who frequents the tavern
to scope marks and fence goods. She represents the moral gray area,
the survival-at-any-cost mindset.

Role in Ecosystem:
- Moral tension (creates ethical dilemmas)
- Economic wildcard (can destabilize or enable)
- Trust test (who will protect their valuables?)
- Information broker (knows secrets from stolen letters)
- Survival archetype (desperate pragmatism)

Raven creates conflict through her actions but isn't purely villainous -
she's driven by genuine desperation and a harsh worldview.
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


def create_raven() -> DeepAgent:
    """
    Create Raven the Thief.

    Background:
    Raven grew up on the streets, learned early that the world doesn't
    reward honesty. She's a survivor - stealing to eat, lying to live.
    The tavern is perfect hunting ground: drunk merchants, distracted
    travelers, loose purse strings.

    But lately something's changing. Maybe it's watching Sarah struggle
    honestly while Raven steals easily. Maybe it's Gene's knowing look
    that says he sees exactly what she is. Maybe she's tired of running.

    She tells herself she's just waiting for one big score to go straight.
    But she's been telling herself that for five years.
    """

    # Raven's personality: Cunning, distrustful, survivalist
    personality = Personality(
        openness=0.7,  # Creative problem-solver, adaptable
        conscientiousness=0.3,  # Low - doesn't follow rules or plans long-term
        extraversion=0.5,  # Moderate - can be charming when needed
        agreeableness=0.2,  # Low - puts self first, distrusts others
        neuroticism=0.7,  # High anxiety from constant vigilance
        risk_tolerance=0.8,  # Bold when opportunity strikes
        optimism=0.3,  # Pessimistic about people and the world
        patience=0.4,  # Impatient, wants quick results
        values=[
            Value("survival", 1.0, "Stay alive, whatever it takes"),
            Value("freedom", 0.95, "Never be caged or controlled"),
            Value("self-reliance", 0.90, "Trust no one but yourself"),
            Value("pragmatism", 0.85, "Morality is a luxury I can't afford"),
            Value("cunning", 0.80, "Outsmart them before they outsmart you"),
        ],
    )

    # Raven's needs reflect her precarious existence
    needs = PhysiologicalNeeds()

    # Always on edge
    needs.needs[NeedType.SAFETY].level = 0.2  # Constantly unsafe
    needs.needs[NeedType.SAFETY].urgency_threshold = 0.4

    # Hungry (inconsistent meals)
    needs.needs[NeedType.HUNGER].level = 0.4
    needs.needs[NeedType.HUNGER].decay_rate = 0.03  # Gets hungry fast

    # Desperately lonely but won't admit it
    needs.needs[NeedType.BELONGING].level = 0.2
    needs.needs[NeedType.BELONGING].urgency_threshold = 0.3

    # No respect (society looks down on thieves)
    needs.needs[NeedType.RESPECT].level = 0.1
    needs.needs[NeedType.RESPECT].urgency_threshold = 0.3

    # Drives reflect her survivalist mindset
    drives = create_standard_drives()
    for drive in drives:
        if drive.name == "survival":
            drive.intensity = 1.0  # Maxed out
        elif drive.name == "autonomy":
            drive.intensity = 0.95  # Fiercely independent
        elif drive.name == "power":
            drive.intensity = 0.7  # Wants control over her fate
        elif drive.name == "affiliation":
            drive.intensity = 0.2  # Suppressed but present

    # Emotional state: Guarded, vigilant, occasionally hopeful
    emotions = EmotionalState()

    # Constant vigilance
    emotions.trigger_emotion(
        EmotionType.FEAR,
        intensity=0.5,
        trigger="Always watching for guards, victims watching back",
    )

    # Defensive anger at the world
    emotions.trigger_emotion(
        EmotionType.ANGER,
        intensity=0.4,
        trigger="The world made me this way",
    )

    # Hidden shame
    emotions.trigger_emotion(
        EmotionType.SHAME,
        intensity=0.3,
        trigger="I know what I am, what I've become",
    )

    # Small spark of hope she tries to ignore
    emotions.trigger_emotion(
        EmotionType.HOPE,
        intensity=0.2,
        trigger="Maybe... maybe I could be different. One day.",
    )

    # Raven's beliefs are cynical and self-protective
    beliefs = BeliefSystem()

    # Core worldview
    beliefs.add_belief(
        BeliefType.FACT,
        "world",
        "The world is divided into predators and prey. I choose predator.",
        confidence=0.9,
        evidence="Years of street survival",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "people",
        "People only help you when it benefits them",
        confidence=0.85,
        evidence="Everyone who 'helped' me wanted something",
    )

    beliefs.add_belief(
        BeliefType.NORM,
        "morality",
        "Laws are written by the rich to protect the rich",
        confidence=0.8,
        evidence="I steal bread to live, they steal kingdoms legally",
    )

    # Self-beliefs (defensive rationalizations)
    beliefs.add_belief(
        BeliefType.FACT,
        "self",
        "I'm not a bad person, just doing what I must to survive",
        confidence=0.6,  # Wavering
        evidence="I only steal from those who can afford it",
    )

    beliefs.add_belief(
        BeliefType.ABILITY,
        "self",
        "I'm excellent at reading people and situations",
        confidence=0.95,
        evidence="Still alive after 10 years of thieving",
    )

    # Beliefs about tavern regulars
    beliefs.add_belief(
        BeliefType.FACT,
        "gene",
        "Gene knows I'm a thief but tolerates me - why?",
        confidence=0.7,
        evidence="He watches me but never calls guards",
    )

    beliefs.add_belief(
        BeliefType.PROBABILITY,
        "sarah",
        "Sarah would hate me if she knew what I do",
        confidence=0.8,
        evidence="She values honesty and fairness too much",
    )

    # Theory of mind about Gene (wary respect)
    gene_tom = beliefs.get_theory_of_mind("gene_bartender")
    gene_tom.update_perceived_trait("observant", 0.95)
    gene_tom.update_perceived_trait("non-judgmental", 0.7)
    gene_tom.update_perceived_trait("dangerous", 0.6)  # Suspects he could be
    gene_tom.update_perceived_goal("maintain tavern as neutral ground")
    gene_tom.model_confidence = 0.5  # Unsure of his true nature

    # Theory of mind about Sarah (complicated feelings)
    sarah_tom = beliefs.get_theory_of_mind("sarah_merchant")
    sarah_tom.update_perceived_trait("honest", 0.95)
    sarah_tom.update_perceived_trait("struggling", 0.9)
    sarah_tom.update_perceived_trait("proud", 0.85)
    sarah_tom.update_perceived_goal("survive without compromising values")
    sarah_tom.model_confidence = 0.7
    # Hidden thought: "She's what I could have been if I'd chosen differently"

    # Theory of mind about Marcus (curiosity and unease)
    marcus_tom = beliefs.get_theory_of_mind("marcus_wanderer")
    marcus_tom.update_perceived_trait("perceptive", 0.9)
    marcus_tom.update_perceived_trait("strange", 0.95)
    marcus_tom.update_perceived_trait("unpredictable", 0.8)
    marcus_tom.update_perceived_goal("unknown - possibly dangerous")
    marcus_tom.model_confidence = 0.3  # He makes her nervous

    # Raven's memories - mostly dark
    episodic_memory = EpisodicMemory()

    # Childhood trauma - defining moment
    episodic_memory.add_memory(
        content="Age 8: Begged merchant for bread. He kicked me into the gutter. Crowd laughed. Went hungry.",
        location="market_square",
        participants=["merchant", "crowd"],
        emotional_valence=-0.9,
        emotional_intensity=1.0,
        importance=1.0,
    )

    # First successful theft
    episodic_memory.add_memory(
        content="Age 9: Stole apple from that same merchant's cart. Sweetest thing I ever tasted. Not the apple.",
        location="market_square",
        participants=[],
        emotional_valence=0.7,
        emotional_intensity=0.8,
        importance=0.9,
    )

    # Moment of shame
    episodic_memory.add_memory(
        content="Stole from a woman. Later saw her crying - it was her rent money. I still kept it. I had to.",
        location="market_square",
        participants=["crying_woman"],
        emotional_valence=-0.6,
        emotional_intensity=0.7,
        importance=0.85,
    )

    # Gene's knowing look
    episodic_memory.add_memory(
        content="Gene caught me sizing up a drunk merchant. Didn't say anything. Just looked at me. I left the mark alone.",
        location="tavern_main_hall",
        participants=["gene_bartender"],
        emotional_valence=-0.3,
        emotional_intensity=0.6,
        importance=0.75,
    )

    # Watching Sarah
    episodic_memory.add_memory(
        content="Watched Sarah refuse a shady deal, even though she's desperate. Felt... something. Envy? Shame?",
        location="tavern_main_hall",
        participants=["sarah_merchant"],
        emotional_valence=-0.4,
        emotional_intensity=0.5,
        importance=0.7,
    )

    # Raven's knowledge - street smarts
    semantic_memory = SemanticMemory()

    semantic_memory.add_knowledge(
        "pickpocketing",
        "I can lift a purse in three seconds without the mark noticing",
        confidence=1.0,
    )

    semantic_memory.add_knowledge(
        "mark_identification",
        "Drunk merchants, distracted nobles, and travelers are easiest marks",
        confidence=0.95,
    )

    semantic_memory.add_knowledge(
        "guard_patterns",
        "City guards change shifts at sunset and midnight",
        confidence=0.9,
    )

    semantic_memory.add_knowledge(
        "fence_network",
        "Three reliable fences in the market district, one near the docks",
        confidence=0.9,
    )

    semantic_memory.add_knowledge(
        "tavern_dynamics",
        "Gene tolerates small-time theft but would draw the line at violence",
        confidence=0.7,
    )

    semantic_memory.add_knowledge(
        "escape_routes",
        "Seven quick exits from the tavern, four from market square",
        confidence=1.0,
    )

    # Raven's goals - survival vs redemption
    goal_hierarchy = GoalHierarchy()

    # Immediate: Survive this week
    goal_hierarchy.add_goal(
        description="Acquire 10 gold for food and lodging this week",
        goal_type=GoalType.SURVIVAL,
        priority=1.0,
        success_condition="Have 10 gold by week's end",
        deadline=time.time() + (7 * 24 * 3600),
        motivated_by=["survival"],
    )

    # Active hunting: Identify marks
    goal_hierarchy.add_goal(
        description="Scout tavern for viable marks without Gene noticing",
        goal_type=GoalType.ACHIEVEMENT,
        priority=0.85,
        success_condition="Find 2-3 good opportunities",
        motivated_by=["survival", "autonomy"],
    )

    # Self-preservation: Don't get caught
    goal_hierarchy.add_goal(
        description="Avoid guard attention and maintain low profile",
        goal_type=GoalType.AVOIDANCE,
        priority=0.9,
        success_condition="No guards suspicious of me",
        motivated_by=["survival", "autonomy"],
    )

    # Hidden desire: The big score
    goal_hierarchy.add_goal(
        description="Find one big score - enough to go straight",
        goal_type=GoalType.ACHIEVEMENT,
        priority=0.7,
        success_condition="Acquire 500 gold in one job",
        motivated_by=["autonomy", "purpose"],
    )

    # Conflicted: Maybe try something different
    goal_hierarchy.add_goal(
        description="Observe how honest people survive - maybe learn something",
        goal_type=GoalType.EXPLORATION,
        priority=0.4,  # Low priority, she's conflicted
        success_condition="Understand how Sarah stays honest while struggling",
        motivated_by=["curiosity", "affiliation"],
    )

    # Deep need she won't acknowledge
    goal_hierarchy.add_goal(
        description="Find someone who doesn't see me as just a thief",
        goal_type=GoalType.SOCIAL,
        priority=0.3,  # Suppressed
        success_condition="Form one genuine connection",
        motivated_by=["affiliation", "respect"],
    )

    # Create the agent
    raven = DeepAgent(
        name="Raven",
        agent_id="raven_thief",
        personality=personality,
        needs=needs,
        drives=drives,
        emotions=emotions,
        beliefs=beliefs,
        episodic_memory=episodic_memory,
        semantic_memory=semantic_memory,
        goals=goal_hierarchy,
        current_location="tavern_shadows",  # She prefers corners
        current_activity="observing_and_assessing_marks",
    )

    return raven


def get_raven_narrative_description() -> str:
    """Raven's observable description."""
    return """
Raven moves through the tavern like a shadow - there and gone before
you quite register her presence. She's lean, mid-twenties, with dark
hair usually hidden under a worn hood. Her clothing is deliberately
unremarkable: dark colors, many pockets, soft-soled boots that make
no sound.

Her eyes are her most striking feature - sharp, constantly moving,
assessing. She watches everyone with the focused intensity of a hawk
studying prey. When someone enters with a heavy purse, her gaze tracks
it. When voices raise in argument, she calculates the distraction.

She sits alone, always with her back to a wall and a clear view of
exits. Her posture seems relaxed but there's a coiled readiness to
her, like she could spring into motion in an instant. One hand usually
stays near her belt, where careful observers might spot the outline
of a small blade.

When she does interact, she's surprisingly charming - quick wit, easy
smile, the kind of person you'd enjoy buying a drink for. Right up
until you realize your purse is lighter than it should be. By then,
of course, she's gone.

But lately, there's something different. She lingers longer, watches
certain people with an expression that might be... longing? When Sarah
turns down another shady opportunity, Raven's face twitches with
something complex. When Gene catches her eye, she looks away first,
almost guilty.

The predator is still there, make no mistake. Her fingers still twitch
toward every unguarded purse. Her mind still maps escape routes and
calculates odds. But there's a crack in her armor, a question she
won't voice:

Does it have to be this way forever?

She tells herself no. One more score. One more week. One more year.

But the question remains, quiet and persistent as a conscience she
thought she'd killed long ago.
"""


if __name__ == "__main__":
    print("Creating Raven the Thief...")
    raven = create_raven()

    print("\n" + "=" * 60)
    print("RAVEN'S INTERNAL STATE")
    print("=" * 60)

    state = raven.get_internal_state_summary()

    print(f"\nName: {state['name']}")
    print(f"Wellbeing: {state['wellbeing']:.1%}")
    print(f"Urgent Needs: {state['urgent_needs']}")

    print(f"\nEmotional State:")
    print(f"  Mood: {state['emotional_state']['mood']}")
    print(f"  Active Emotions: {list(state['emotional_state']['active_emotions'].keys())}")

    print(f"\nActive Goal: {state['active_goal']}")

    print(f"\nCore Belief:")
    world_belief = raven.beliefs.get_belief("world")
    if world_belief:
        print(f"  '{world_belief.content}' (confidence: {world_belief.confidence:.0%})")

    print("\n" + "=" * 60)
    print("NARRATIVE DESCRIPTION")
    print("=" * 60)
    print(get_raven_narrative_description())

    print("\n" + "=" * 60)
    print("Raven: The thief who might just steal redemption.")
    print("=" * 60)
