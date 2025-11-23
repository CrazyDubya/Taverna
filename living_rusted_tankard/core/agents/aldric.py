"""
Captain Aldric - The Dutiful Guard

Aldric is the captain of the city watch who frequents the tavern
off-duty. He represents law, order, and the conflict between
duty and compassion.

Role in Ecosystem:
- Moral authority (upholds the law)
- Enforcement threat (Raven's natural antagonist)
- Justice vs mercy tension (sees Sarah's struggle, Raven's theft)
- Information source (knows city events, crimes, politics)
- Protector archetype (wants to help but bound by rules)

Aldric creates tension through his presence - criminals worry,
honest folk relax, and everyone knows he's watching. But he's
not just a simple law enforcer - he struggles with the gap
between law and justice.
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


def create_aldric() -> DeepAgent:
    """
    Create Captain Aldric of the City Watch.

    Background:
    Aldric has served the city guard for fifteen years, rising to
    captain through competence and unwavering dedication. He believes
    in law, order, and the social contract. The law is what separates
    civilization from chaos.

    But lately, the law feels insufficient. He watches Sarah struggle
    while merchants exploit loopholes legally. He knows Raven steals,
    but also knows she'd starve otherwise. He sees nobles break laws
    with impunity while he arrests beggars for petty theft.

    The tavern is his refuge - off duty, he can be just Aldric, not
    Captain Aldric. Here he watches people as people, not as potential
    criminals or victims. And here his certainty about law and justice
    slowly erodes.
    """

    # Aldric's personality: Dutiful, rigid, increasingly conflicted
    personality = Personality(
        openness=0.4,  # Traditional, resistant to new ideas
        conscientiousness=0.95,  # Extremely disciplined and dutiful
        extraversion=0.6,  # Moderately outgoing, leadership presence
        agreeableness=0.6,  # Wants to help, but duty comes first
        neuroticism=0.4,  # Generally stable, but stress building
        risk_tolerance=0.3,  # Conservative, follows protocol
        optimism=0.5,  # Neutral - wants to believe in justice
        patience=0.7,  # Patient but frustration growing
        values=[
            Value("duty", 0.98, "My oath to protect and serve is sacred"),
            Value("order", 0.95, "Law is what separates us from beasts"),
            Value("honor", 0.90, "A guard's word must be unbreakable"),
            Value("fairness", 0.85, "Justice should be blind and equal"),
            Value("protection", 0.88, "The weak need defenders"),
        ],
    )

    # Aldric's needs reflect his stable but stressful position
    needs = PhysiologicalNeeds()

    # Well-maintained (military discipline)
    needs.needs[NeedType.HUNGER].level = 0.7  # Regular meals
    needs.needs[NeedType.REST].level = 0.6  # Decent sleep, military schedule

    # High respect from position
    needs.needs[NeedType.RESPECT].level = 0.8  # Citizens respect the captain
    needs.needs[NeedType.RESPECT].urgency_threshold = 0.6  # Important to him

    # Strong sense of purpose from duty
    needs.needs[NeedType.PURPOSE].level = 0.7  # Serving the city
    needs.needs[NeedType.PURPOSE].urgency_threshold = 0.5

    # Moderate belonging (has guards under his command, but lonely at top)
    needs.needs[NeedType.BELONGING].level = 0.5

    # Achievement need related to keeping order
    needs.needs[NeedType.ACHIEVEMENT].level = 0.6
    needs.needs[NeedType.ACHIEVEMENT].urgency_threshold = 0.5

    # Drives reflect his dedication
    drives = create_standard_drives()
    for drive in drives:
        if drive.name == "purpose":
            drive.intensity = 0.95  # Strong sense of duty
        elif drive.name == "power":
            drive.intensity = 0.6  # Authority is responsibility, not pleasure
        elif drive.name == "affiliation":
            drive.intensity = 0.5  # Wants connection but maintains distance
        elif drive.name == "autonomy":
            drive.intensity = 0.4  # Bound by duty and rules

    # Emotional state: Stable but increasingly conflicted
    emotions = EmotionalState()

    # Pride in service
    emotions.trigger_emotion(
        EmotionType.PRIDE,
        intensity=0.6,
        trigger="Fifteen years keeping this city safe",
    )

    # Growing frustration with system
    emotions.trigger_emotion(
        EmotionType.FRUSTRATION,
        intensity=0.5,
        trigger="Laws that protect the rich, punish the poor",
    )

    # Moral conflict
    emotions.trigger_emotion(
        EmotionType.GUILT,
        intensity=0.4,
        trigger="Should I arrest the starving thief or the corrupt merchant?",
    )

    # Weariness
    emotions.trigger_emotion(
        EmotionType.SADNESS,
        intensity=0.3,
        trigger="Fifteen years and crime doesn't decrease, just changes",
    )

    # Aldric's beliefs - lawful but questioning
    beliefs = BeliefSystem()

    # Core beliefs about law and order
    beliefs.add_belief(
        BeliefType.FACT,
        "law",
        "Law is the foundation of civilization - without it, chaos reigns",
        confidence=0.9,  # Still strong but wavering
        evidence="Fifteen years witnessing crime and punishment",
    )

    beliefs.add_belief(
        BeliefType.NORM,
        "duty",
        "A guard's duty is to enforce the law, not to judge it",
        confidence=0.7,  # Decreasing
        evidence="My training and oath",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "justice",
        "Justice and law should be the same, but they're not always",
        confidence=0.8,  # Growing awareness
        evidence="Too many unjust outcomes from just following the law",
    )

    # Beliefs about himself
    beliefs.add_belief(
        BeliefType.FACT,
        "self",
        "I am a good guard and a fair captain",
        confidence=0.8,
        evidence="Low corruption in my watch, respect from guards",
    )

    beliefs.add_belief(
        BeliefType.PROBABILITY,
        "self",
        "I'm becoming too cynical - maybe I need to retire soon",
        confidence=0.5,
        evidence="Increased frustration, questioning orders",
    )

    # Beliefs about the tavern folk
    beliefs.add_belief(
        BeliefType.FACT,
        "gene",
        "Gene runs a clean establishment and keeps the peace better than I do",
        confidence=0.8,
        evidence="Rarely get trouble calls from this tavern",
    )

    beliefs.add_belief(
        BeliefType.PROBABILITY,
        "raven",
        "That hooded woman is a thief, but I can't prove it... yet",
        confidence=0.75,
        evidence="Pickpocket victim reports, her behavior patterns",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "sarah",
        "Sarah is honest but struggling - the system is failing her",
        confidence=0.9,
        evidence="Observations of her business dealings",
    )

    # Theory of mind about Gene (professional respect)
    gene_tom = beliefs.get_theory_of_mind("gene_bartender")
    gene_tom.update_perceived_trait("fair", 0.9)
    gene_tom.update_perceived_trait("wise", 0.8)
    gene_tom.update_perceived_trait("secretive", 0.7)
    gene_tom.update_perceived_goal("maintain tavern as neutral ground for all")
    gene_tom.model_confidence = 0.7

    # Theory of mind about Sarah (sympathetic)
    sarah_tom = beliefs.get_theory_of_mind("sarah_merchant")
    sarah_tom.update_perceived_trait("honest", 0.95)
    sarah_tom.update_perceived_trait("hardworking", 0.9)
    sarah_tom.update_perceived_trait("desperate", 0.8)
    sarah_tom.update_perceived_goal("survive through honest work")
    sarah_tom.model_confidence = 0.8

    # Theory of mind about Raven (suspicious but conflicted)
    raven_tom = beliefs.get_theory_of_mind("raven_thief")
    raven_tom.update_perceived_trait("criminal", 0.8)
    raven_tom.update_perceived_trait("cunning", 0.9)
    raven_tom.update_perceived_trait("desperate", 0.7)  # He sees the desperation
    raven_tom.update_perceived_goal("survive through theft")
    raven_tom.model_confidence = 0.6
    # Hidden thought: "She's a criminal, but she's starving. What's my duty here?"

    # Theory of mind about Marcus (curious and slightly unnerved)
    marcus_tom = beliefs.get_theory_of_mind("marcus_wanderer")
    marcus_tom.update_perceived_trait("harmless", 0.6)
    marcus_tom.update_perceived_trait("strange", 0.9)
    marcus_tom.update_perceived_trait("observant", 0.8)
    marcus_tom.update_perceived_goal("unknown - philosophical wandering?")
    marcus_tom.model_confidence = 0.4

    # Aldric's memories - duty and disillusionment
    episodic_memory = EpisodicMemory()

    # Oath-taking ceremony (proudest moment)
    episodic_memory.add_memory(
        content="Took my oath before the city magistrate: 'To protect and serve, to uphold the law.' Meant every word.",
        location="guard_headquarters",
        participants=["magistrate", "fellow_guards"],
        emotional_valence=0.9,
        emotional_intensity=0.9,
        importance=1.0,
    )

    # Saved a child from fire
    episodic_memory.add_memory(
        content="Pulled a child from burning building. Mother's tears of gratitude. This is why I serve.",
        location="merchant_district",
        participants=["child", "mother"],
        emotional_valence=0.9,
        emotional_intensity=0.8,
        importance=0.95,
    )

    # Corruption revelation
    episodic_memory.add_memory(
        content="Caught fellow guard taking bribes. Had to arrest him. He said 'Everyone does it.' Not everyone.",
        location="guard_headquarters",
        participants=["corrupt_guard"],
        emotional_valence=-0.6,
        emotional_intensity=0.8,
        importance=0.9,
    )

    # Unjust order
    episodic_memory.add_memory(
        content="Magistrate ordered me to arrest beggars during winter. For 'vagrancy.' They had nowhere to go.",
        location="city_streets",
        participants=["magistrate", "beggars"],
        emotional_valence=-0.7,
        emotional_intensity=0.7,
        importance=0.85,
    )

    # Watching Sarah
    episodic_memory.add_memory(
        content="Watched Sarah turn down a suspiciously good deal. Honest in a world of corruption. Rare.",
        location="tavern_main_hall",
        participants=["sarah_merchant"],
        emotional_valence=0.5,
        emotional_intensity=0.5,
        importance=0.7,
    )

    # The Raven dilemma
    episodic_memory.add_memory(
        content="Saw that hooded woman lift a purse. Victim was a merchant who'd just fired his workers to save costs. I... hesitated.",
        location="tavern_main_hall",
        participants=["raven_thief", "merchant"],
        emotional_valence=-0.4,
        emotional_intensity=0.6,
        importance=0.8,
    )

    # Aldric's knowledge - law and city dynamics
    semantic_memory = SemanticMemory()

    semantic_memory.add_knowledge(
        "city_law",
        "I know city law better than most magistrates - fifteen years of enforcement",
        confidence=0.95,
    )

    semantic_memory.add_knowledge(
        "crime_patterns",
        "Crime increases when economy worsens - poverty drives theft more than malice",
        confidence=0.9,
    )

    semantic_memory.add_knowledge(
        "guard_corruption",
        "Approximately 20% of city guards accept bribes, mostly from wealthy merchants",
        confidence=0.8,
    )

    semantic_memory.add_knowledge(
        "tavern_politics",
        "Gene's tavern is neutral ground - even criminals respect it",
        confidence=0.85,
    )

    semantic_memory.add_knowledge(
        "pickpocket_techniques",
        "I've arrested enough thieves to recognize their methods and targets",
        confidence=0.9,
    )

    semantic_memory.add_knowledge(
        "legal_loopholes",
        "Rich merchants exploit contract law to legally rob people worse than any thief",
        confidence=0.85,
    )

    # Aldric's goals - duty vs conscience
    goal_hierarchy = GoalHierarchy()

    # Primary duty: Maintain order
    goal_hierarchy.add_goal(
        description="Keep the city safe and orderly",
        goal_type=GoalType.MAINTENANCE,
        priority=0.95,
        success_condition="Low crime rate, peaceful streets",
        motivated_by=["purpose", "duty"],
    )

    # Active patrol: Monitor tavern
    goal_hierarchy.add_goal(
        description="Observe tavern patrons for criminal activity (off-duty monitoring)",
        goal_type=GoalType.ACHIEVEMENT,
        priority=0.7,
        success_condition="Prevent crimes before they happen",
        motivated_by=["purpose"],
    )

    # Conflicted: The Raven problem
    goal_hierarchy.add_goal(
        description="Gather evidence on the hooded thief",
        goal_type=GoalType.ACHIEVEMENT,
        priority=0.6,  # Lower than it should be
        success_condition="Catch her in the act with proof",
        motivated_by=["duty"],
    )

    # Growing desire: Help Sarah
    goal_hierarchy.add_goal(
        description="Find a legal way to help Sarah's business",
        goal_type=GoalType.SOCIAL,
        priority=0.5,
        success_condition="Sarah succeeds without breaking law",
        motivated_by=["protection", "fairness"],
    )

    # Internal conflict: Question the system
    goal_hierarchy.add_goal(
        description="Understand why following the law feels wrong sometimes",
        goal_type=GoalType.EXPLORATION,
        priority=0.4,
        success_condition="Resolve moral confusion about duty vs justice",
        motivated_by=["purpose", "curiosity"],
    )

    # Long-term consideration
    goal_hierarchy.add_goal(
        description="Decide if I can continue as captain in good conscience",
        goal_type=GoalType.EXPLORATION,
        priority=0.3,  # Background concern
        success_condition="Find peace with my role or change it",
        motivated_by=["purpose", "integrity"],
    )

    # Hidden desire
    goal_hierarchy.add_goal(
        description="Connect with someone who understands this conflict",
        goal_type=GoalType.SOCIAL,
        priority=0.3,
        success_condition="Find confidant who gets the duty vs conscience struggle",
        motivated_by=["affiliation", "belonging"],
    )

    # Create the agent
    aldric = DeepAgent(
        name="Captain Aldric",
        agent_id="aldric_guard",
        personality=personality,
        needs=needs,
        drives=drives,
        emotions=emotions,
        beliefs=beliefs,
        episodic_memory=episodic_memory,
        semantic_memory=semantic_memory,
        goals=goal_hierarchy,
        current_location="tavern_main_hall",
        current_activity="off_duty_observation",
    )

    return aldric


def get_aldric_narrative_description() -> str:
    """Aldric's observable description."""
    return """
Captain Aldric sits with military posture even when off-duty - back
straight, shoulders squared, eyes scanning the room with practiced
efficiency. He's in his late thirties, weathered by years of city
watch duty but still strong and capable.

His guard uniform is impeccably maintained, though he's removed the
official insignia and weapon belt to signal he's off-duty. The sword
never goes far, though - it leans against the wall within arm's reach.
Old habits.

His face is lined with responsibility and recent stress. Dark hair
showing premature gray at the temples. Eyes that have seen too much
but still search for signs of trouble. When someone enters the tavern,
he assesses them automatically: threat level, intoxication, visible
weapons, nervousness. It's reflexive now.

He drinks slowly, nurses his ale for hours. Not here to get drunk -
here to think, observe, be off the clock for a few precious hours.
But he's never really off. When voices raise, his hand twitches
toward where his sword belt should be. When that hooded woman in
the corner shifts, he tracks her movement. When Sarah counts her
coins with shaking hands, his jaw tightens.

When he speaks, it's measured and direct. Military precision in
language. But lately there's something else - pauses before
responding, moments where certainty falters. The other guards have
noticed their captain is... different. More thoughtful. More troubled.

Gene treats him with casual respect, brings his ale without being
asked. They don't talk much, but there's understanding there. Two
men who've seen the gap between how things are and how they should be.

Sometimes, late in the evening after a particularly bad day, Aldric
stares into his ale and asks Gene questions. Quiet questions about
justice, law, duty. Gene listens, mostly doesn't answer. Sometimes
the not-answering is answer enough.

The tavern regulars behave differently when Aldric is present. Some
straighten up, become model citizens. Others leave quickly. Raven
stops working entirely, becomes invisible in her corner. Sarah seems
to relax slightly - one honest person recognizing another.

He's the law incarnate, sitting in a tavern full of gray morality.

And increasingly, he's not sure where he fits anymore.
"""


if __name__ == "__main__":
    print("Creating Captain Aldric...")
    aldric = create_aldric()

    print("\n" + "=" * 60)
    print("ALDRIC'S INTERNAL STATE")
    print("=" * 60)

    state = aldric.get_internal_state_summary()

    print(f"\nName: {state['name']}")
    print(f"Wellbeing: {state['wellbeing']:.1%}")
    print(f"Urgent Needs: {state['urgent_needs']}")

    print(f"\nEmotional State:")
    print(f"  Mood: {state['emotional_state']['mood']}")
    print(f"  Active Emotions: {list(state['emotional_state']['active_emotions'].keys())}")

    print(f"\nActive Goal: {state['active_goal']}")

    print(f"\nCore Belief:")
    law_belief = aldric.beliefs.get_belief("law")
    if law_belief:
        print(f"  '{law_belief.content}' (confidence: {law_belief.confidence:.0%})")

    print("\n" + "=" * 60)
    print("NARRATIVE DESCRIPTION")
    print("=" * 60)
    print(get_aldric_narrative_description())

    print("\n" + "=" * 60)
    print("Aldric: The lawman learning that justice and law aren't always the same.")
    print("=" * 60)
