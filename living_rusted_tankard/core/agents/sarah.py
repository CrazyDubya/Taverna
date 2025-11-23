"""
Sarah the Merchant - First Deep Agent Implementation.

Sarah is a struggling merchant who serves as the exemplar for
the deep agent system. She has:
- Rich personality (conscientious, independent, stressed)
- Complex motivations (survival, independence, fairness)
- Evolving emotional state (anxiety about her business)
- Theory of mind about other agents
- Memory of her experiences
- Goals that emerge from her needs and situation

This is what a truly alive NPC looks like.
"""

from typing import Dict, Any
import time

from .agent import DeepAgent
from .personality import Personality, Value, create_personality_archetype
from .needs import PhysiologicalNeeds, Drive, NeedType, create_standard_drives
from .emotions import EmotionalState, EmotionType
from .beliefs import BeliefSystem, BeliefType
from .memory import EpisodicMemory, SemanticMemory
from .goals import GoalHierarchy, GoalType


def create_sarah() -> DeepAgent:
    """
    Create Sarah the Merchant with her full psychological profile.

    Background:
    Sarah runs a small trading business but is struggling with:
    - Rising costs from suppliers
    - Debt accumulation
    - Competition from established merchants
    - Maintaining her reputation while desperate

    Her personality makes her:
    - Hardworking and responsible (high conscientiousness)
    - Values independence fiercely
    - Stressed and anxious (elevated neuroticism due to situation)
    - Somewhat introverted but can be social when needed
    - Fair-minded but willing to consider desperate measures

    This creates internal conflict:
    - Values independence vs. needing to ask for help
    - Values fairness vs. considering shady deals
    - Drive for achievement vs. fear of failure
    """

    # Start with merchant archetype and customize
    personality = create_personality_archetype("merchant")

    # Sarah is more stressed than typical merchant
    personality.neuroticism = 0.6  # Higher anxiety due to business struggles
    personality.extraversion = 0.4  # Slightly introverted
    personality.optimism = 0.4  # Pessimistic due to current situation
    personality.patience = 0.6  # Trying to be patient but it's hard

    # Her values create internal conflict
    personality.values = [
        Value("independence", 0.95, "Above all, I must stand on my own two feet"),
        Value("fairness", 0.85, "Honest dealings and fair prices matter"),
        Value("family", 0.80, "My family depends on my success"),
        Value("reputation", 0.70, "A good name in business is everything"),
        Value("survival", 0.90, "I must survive this crisis"),
    ]

    # Her needs reflect her current struggles
    needs = PhysiologicalNeeds()

    # She's working too hard
    needs.needs[NeedType.REST].level = 0.3  # Exhausted
    needs.needs[NeedType.REST].decay_rate = 0.04  # Gets tired quickly

    # Stressed about achievement
    needs.needs[NeedType.ACHIEVEMENT].level = 0.2  # Feels like she's failing
    needs.needs[NeedType.ACHIEVEMENT].urgency_threshold = 0.5  # This is critical to her

    # Isolated due to shame
    needs.needs[NeedType.BELONGING].level = 0.4  # Somewhat lonely
    needs.needs[NeedType.RESPECT].level = 0.3  # Worried people look down on her

    # Drives are intensified by situation
    drives = create_standard_drives()

    # Modify drive intensities for Sarah's situation
    for drive in drives:
        if drive.name == "survival":
            drive.intensity = 1.0  # Maxed out - she's desperate
        elif drive.name == "achievement":
            drive.intensity = 0.9  # Must succeed
        elif drive.name == "autonomy":
            drive.intensity = 0.95  # Fiercely independent
        elif drive.name == "affiliation":
            drive.intensity = 0.4  # Wants connection but feels she can't afford it

    # Initial emotional state - anxious and stressed
    emotions = EmotionalState()

    # Trigger initial emotions reflecting her situation
    emotions.trigger_emotion(
        EmotionType.ANXIETY,
        intensity=0.7,
        trigger="Business is struggling, debt mounting",
    )

    emotions.trigger_emotion(
        EmotionType.FEAR,
        intensity=0.5,
        trigger="Might lose everything I've worked for",
    )

    emotions.trigger_emotion(
        EmotionType.SADNESS,
        intensity=0.4,
        trigger="Feeling isolated and ashamed",
    )

    # Small amount of hope keeps her going
    emotions.trigger_emotion(
        EmotionType.HOPE, intensity=0.3, trigger="Maybe things will turn around"
    )

    # Her beliefs shape how she sees the world
    beliefs = BeliefSystem()

    # Core beliefs about the world
    beliefs.add_belief(
        BeliefType.FACT,
        "world",
        "Hard work pays off... eventually",
        confidence=0.6,  # Wavering faith
        evidence="My parents taught me this",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "world",
        "People are mostly out for themselves",
        confidence=0.7,
        evidence="Recent business dealings",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "suppliers",
        "Suppliers are raising prices unfairly",
        confidence=0.9,
        evidence="Seen it happen repeatedly",
    )

    # Beliefs about herself
    beliefs.add_belief(
        BeliefType.ABILITY,
        "self",
        "I am a capable merchant",
        confidence=0.7,  # Self-doubt creeping in
        evidence="Years of experience",
    )

    beliefs.add_belief(
        BeliefType.PROBABILITY,
        "business",
        "My business might fail if I don't get help",
        confidence=0.8,
        evidence="The numbers don't lie",
    )

    # Beliefs about the tavern
    beliefs.add_belief(
        BeliefType.FACT,
        "gene",
        "Gene is a fair but shrewd businessman",
        confidence=0.7,
        evidence="Observations of his dealings",
    )

    # Initial theory of mind about Gene
    gene_tom = beliefs.get_theory_of_mind("gene_bartender")
    gene_tom.update_perceived_trait("shrewd", 0.8)
    gene_tom.update_perceived_trait("fair", 0.7)
    gene_tom.update_perceived_trait("trustworthy", 0.6)
    gene_tom.model_confidence = 0.6

    # Her memories shape her current state
    episodic_memory = EpisodicMemory()

    # Traumatic memory: confrontation with supplier
    episodic_memory.add_memory(
        content="Supplier Merchant demanded 30% price increase. I couldn't afford it. He laughed.",
        location="market_square",
        participants=["supplier_merchant"],
        emotional_valence=-0.8,
        emotional_intensity=0.9,
        importance=0.95,
    )

    # Memory of better times
    episodic_memory.add_memory(
        content="Made my first major sale - 50 gold profit in one day! I felt on top of the world.",
        location="market_square",
        participants=[],
        emotional_valence=0.9,
        emotional_intensity=0.8,
        importance=0.8,
    )

    # Recent memory: counting coins late at night
    episodic_memory.add_memory(
        content="Stayed up counting gold. Still short 20 for this month's rent. Felt hopeless.",
        location="home",
        participants=[],
        emotional_valence=-0.7,
        emotional_intensity=0.7,
        importance=0.85,
    )

    # Positive memory: Gene gave her a fair price once
    episodic_memory.add_memory(
        content="Gene bought some of my goods at a fair price, even when he didn't have to.",
        location="tavern",
        participants=["gene_bartender"],
        emotional_valence=0.6,
        emotional_intensity=0.5,
        importance=0.7,
    )

    # Her semantic knowledge of the business
    semantic_memory = SemanticMemory()

    semantic_memory.add_knowledge(
        "bread_price", "Bread typically sells for 2 gold", confidence=1.0
    )

    semantic_memory.add_knowledge(
        "my_debt", "I owe approximately 50 gold in debts", confidence=0.95
    )

    semantic_memory.add_knowledge(
        "monthly_expenses",
        "My monthly expenses are around 30 gold",
        confidence=0.9,
    )

    semantic_memory.add_knowledge(
        "supplier_prices", "Supplier raised prices by 30%", confidence=1.0
    )

    semantic_memory.add_knowledge(
        "tavern_location",
        "The Living Rusted Tankard is on the corner of Market Street",
        confidence=1.0,
    )

    # Her goals reflect her desperate situation
    goal_hierarchy = GoalHierarchy()

    # Immediate survival goal - URGENT
    goal_hierarchy.add_goal(
        description="Make 30 gold this month for expenses",
        goal_type=GoalType.SURVIVAL,
        priority=1.0,
        success_condition="Have at least 30 gold",
        deadline=time.time() + (30 * 24 * 3600),  # 30 days from now
        motivated_by=["survival", "achievement"],
    )

    # Debt repayment goal - HIGH PRIORITY
    goal_hierarchy.add_goal(
        description="Pay back 50 gold in debt",
        goal_type=GoalType.ACHIEVEMENT,
        priority=0.9,
        success_condition="Debt reduced to 0",
        deadline=time.time() + (60 * 24 * 3600),  # 60 days
        motivated_by=["survival", "autonomy"],
    )

    # Maintain reputation - IMPORTANT but in conflict with survival
    goal_hierarchy.add_goal(
        description="Maintain good reputation in merchant community",
        goal_type=GoalType.SOCIAL,
        priority=0.7,
        success_condition="Merchants respect me",
        motivated_by=["affiliation", "purpose"],
    )

    # Long-term aspiration - BACKGROUND
    goal_hierarchy.add_goal(
        description="Expand business to be truly independent",
        goal_type=GoalType.ACHIEVEMENT,
        priority=0.6,
        success_condition="Thriving, profitable business",
        motivated_by=["achievement", "autonomy", "purpose"],
    )

    # Social need - CONFLICTING with her shame
    goal_hierarchy.add_goal(
        description="Find someone I can trust and open up to",
        goal_type=GoalType.SOCIAL,
        priority=0.5,
        success_condition="Have at least one confidant",
        motivated_by=["affiliation"],
    )

    # Create the agent
    sarah = DeepAgent(
        name="Sarah",
        agent_id="sarah_merchant",
        personality=personality,
        needs=needs,
        drives=drives,
        emotions=emotions,
        beliefs=beliefs,
        episodic_memory=episodic_memory,
        semantic_memory=semantic_memory,
        goals=goal_hierarchy,
        current_location="tavern_main_hall",
        current_activity="looking_for_opportunities",
    )

    return sarah


def get_sarah_narrative_description() -> str:
    """
    Get a narrative description of Sarah's current state.

    This is what a player might perceive through observation.
    """
    return """
Sarah the Merchant stands near the bar, her shoulders slightly hunched
from exhaustion. Dark circles under her eyes betray many sleepless nights.
She clutches a small ledger book, occasionally glancing at it with a
worried expression.

Her clothes, while clean, show signs of wear. She was once proud of her
appearance, but lately, practical concerns have taken precedence.

When someone approaches, she quickly composes herself, forcing a
professional smile. But her eyes reveal the stress beneath - a woman
trying desperately to maintain appearances while her world crumbles.

She seems to be weighing every word before speaking, calculating,
assessing. There's a guardedness about her, as if letting anyone
too close might expose her vulnerabilities.

Yet occasionally, when she thinks no one is watching, her expression
softens into something almost hopeful. As if she still believes,
against all evidence, that things might turn around.

She is a merchant fighting for survival, pride wrestling with desperation,
independence colliding with the need for help she can't bring herself to ask for.
"""


# Example usage and observation
if __name__ == "__main__":
    print("Creating Sarah the Merchant...")
    sarah = create_sarah()

    print("\n" + "=" * 60)
    print("SARAH'S INTERNAL STATE")
    print("=" * 60)

    state = sarah.get_internal_state_summary()

    print(f"\nName: {state['name']}")
    print(f"Location: {state['location']}")
    print(f"Overall Wellbeing: {state['wellbeing']:.1%}")

    print(f"\nUrgent Needs:")
    for need in state['urgent_needs']:
        print(f"  - {need}")

    print(f"\nEmotional State:")
    print(f"  Mood: {state['emotional_state']['mood']}")
    print(f"  Dominant Emotion: {state['emotional_state']['dominant_emotion']}")
    print(f"  Active Emotions:")
    for emotion, intensity in state['emotional_state']['active_emotions'].items():
        print(f"    - {emotion}: {intensity:.0%}")

    print(f"\nBeliefs:")
    print(f"  Total Beliefs: {state['beliefs_summary']['total_beliefs']}")
    print(f"  Strong Beliefs: {state['beliefs_summary']['strong_beliefs']}")
    print(f"  Agents Modeled: {state['beliefs_summary']['agents_modeled']}")

    print(f"\nMemory:")
    memory_summary = state['memory_summary']
    print(f"  Total Memories: {memory_summary['total']}")
    print(f"  Emotionally Significant: {memory_summary['emotional']}")
    print(f"  Average Importance: {memory_summary['avg_importance']:.0%}")

    print(f"\nGoals:")
    goals_summary = state['goals_summary']
    print(f"  Total Goals: {goals_summary['total_goals']}")
    print(f"  By Status: {goals_summary['by_status']}")
    print(f"  Currently Pursuing: {state['active_goal']}")

    print("\n" + "=" * 60)
    print("NARRATIVE DESCRIPTION")
    print("=" * 60)
    print(get_sarah_narrative_description())

    print("\n" + "=" * 60)
    print("COGNITIVE CYCLE SIMULATION")
    print("=" * 60)

    # Simulate a few cognitive cycles
    game_state = {
        "location": "tavern_main_hall",
        "agents_present": ["gene_bartender", "player"],
        "recent_events": ["Player entered the tavern"],
    }

    for i in range(3):
        print(f"\n--- Cycle {i+1} ---")
        action = sarah.cognitive_cycle(game_state)

        if action:
            print(f"Sarah decides to: {action.description}")
            print(f"Command: {action.command}")
            print(f"Reasoning: Based on goal '{sarah.goals.get_active_goal().description if sarah.goals.get_active_goal() else 'idle'}'")

            # Simulate successful action
            sarah.process_outcome(
                action=action,
                outcome={"description": "Action completed successfully"},
                success=True,
            )
        else:
            print("Sarah is thinking...")

        # Show emotional state after action
        current_emotion = sarah.emotions.get_dominant_emotion()
        if current_emotion:
            intensity = sarah.emotions.emotions[current_emotion].intensity
            print(f"Current Emotion: {current_emotion.value} (intensity: {intensity:.0%})")

    print("\n" + "=" * 60)
    print("This is what a truly alive NPC looks like.")
    print("=" * 60)
