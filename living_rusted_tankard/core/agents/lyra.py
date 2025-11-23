"""
Lyra the Bard - The Social Catalyst

Lyra is a traveling bard who performs at the tavern several nights
a week. She represents art, emotion, social connection, and the
power of narrative.

Role in Ecosystem:
- Social connector (brings people together)
- Information spreader (gossip, stories, news)
- Emotional catalyst (songs trigger feelings)
- Reputation maker/breaker (what she sings about matters)
- Entertainment and culture (life beyond survival)

Lyra creates dynamics through her social nature - she notices
everything, talks to everyone, and transforms observations into
stories and songs. She's the gossip network personified, but
with genuine empathy and artistic insight.
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


def create_lyra() -> DeepAgent:
    """
    Create Lyra the Bard.

    Background:
    Lyra has been traveling and performing for eight years, since
    she left her merchant family at age 18. They wanted her to
    marry well and manage accounts. She wanted to sing.

    She chose song. They chose to disown her.

    Now she wanders from tavern to tavern, trading performances for
    meals and coin. She's good - really good. Her voice can make
    grown men weep or lift a room into joy. But more than that,
    she has a gift for reading people, understanding their stories,
    and reflecting them back through song.

    The tavern has become a semi-regular stop. Gene pays fair, the
    acoustics are good, and the people... the people are endlessly
    fascinating. Sarah's quiet desperation, Raven's hidden shame,
    Marcus's cryptic mysteries, Aldric's moral struggle - she sees
    it all and feels it deeply.

    Sometimes too deeply. She absorbs others' emotions like a sponge,
    carries their pain in her voice. It's her gift and her curse.
    """

    # Lyra's personality: Expressive, empathetic, emotionally intense
    personality = Personality(
        openness=0.95,  # Highly creative and open to experience
        conscientiousness=0.4,  # Spontaneous, not great with plans
        extraversion=0.9,  # Extremely outgoing, energized by people
        agreeableness=0.8,  # Warm, empathetic, wants harmony
        neuroticism=0.6,  # Emotionally volatile, feels everything intensely
        risk_tolerance=0.6,  # Moderate - bold in art, cautious in life
        optimism=0.7,  # Generally hopeful and positive
        patience=0.5,  # Moderate patience
        values=[
            Value("authenticity", 0.95, "Art must be true to be beautiful"),
            Value("connection", 0.90, "People need each other, need to be seen"),
            Value("beauty", 0.88, "The world needs more beauty, less suffering"),
            Value("freedom", 0.85, "I chose my path, others should choose theirs"),
            Value("empathy", 0.92, "Feel what others feel, sing their stories"),
        ],
    )

    # Lyra's needs reflect her social, artistic nature
    needs = PhysiologicalNeeds()

    # Inconsistent meals (traveling performer)
    needs.needs[NeedType.HUNGER].level = 0.5
    needs.needs[NeedType.HUNGER].decay_rate = 0.025

    # Poor sleep (different beds, late performances)
    needs.needs[NeedType.REST].level = 0.4
    needs.needs[NeedType.REST].decay_rate = 0.035

    # HIGH belonging need (thrives on connection)
    needs.needs[NeedType.BELONGING].level = 0.7  # Performing fills this
    needs.needs[NeedType.BELONGING].urgency_threshold = 0.5  # Critical to her

    # Recognition/respect from performance
    needs.needs[NeedType.RESPECT].level = 0.6
    needs.needs[NeedType.RESPECT].urgency_threshold = 0.5

    # Purpose through art
    needs.needs[NeedType.PURPOSE].level = 0.7
    needs.needs[NeedType.PURPOSE].urgency_threshold = 0.4

    # High curiosity (needs new stories, experiences)
    needs.needs[NeedType.CURIOSITY].level = 0.3  # Often urgent
    needs.needs[NeedType.CURIOSITY].urgency_threshold = 0.5

    # Drives reflect her artistic, social nature
    drives = create_standard_drives()
    for drive in drives:
        if drive.name == "affiliation":
            drive.intensity = 0.95  # Deeply needs connection
        elif drive.name == "exploration":
            drive.intensity = 0.8  # Needs new experiences for art
        elif drive.name == "purpose":
            drive.intensity = 0.85  # Art gives meaning
        elif drive.name == "autonomy":
            drive.intensity = 0.7  # Chose freedom over family

    # Emotional state: Vibrant, empathetic, carrying others' emotions
    emotions = EmotionalState()

    # Joy from performing
    emotions.trigger_emotion(
        EmotionType.JOY,
        intensity=0.6,
        trigger="There's magic when a song connects with a listener",
    )

    # Sadness from absorbing others' pain
    emotions.trigger_emotion(
        EmotionType.SADNESS,
        intensity=0.4,
        trigger="I feel Sarah's desperation, Raven's shame, everyone's burdens",
    )

    # Loneliness despite crowds
    emotions.trigger_emotion(
        EmotionType.LONELINESS,
        intensity=0.5,
        trigger="Surrounded by people but they see the bard, not Lyra",
    )

    # Hope and idealism
    emotions.trigger_emotion(
        EmotionType.HOPE,
        intensity=0.6,
        trigger="Music can heal, connect, transform. I've seen it happen.",
    )

    # Hidden grief (family disownment)
    emotions.trigger_emotion(
        EmotionType.GRIEF,
        intensity=0.3,
        trigger="My mother's face when I left. Eight years and it still hurts.",
    )

    # Lyra's beliefs - empathetic and idealistic
    beliefs = BeliefSystem()

    # Core beliefs about people and art
    beliefs.add_belief(
        BeliefType.FACT,
        "people",
        "Everyone has a story worth telling, pain worth singing",
        confidence=0.95,
        evidence="Eight years of listening, performing, connecting",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "art",
        "Music is the universal language - it reaches past defenses to truth",
        confidence=0.9,
        evidence="Watched hardened soldiers weep at ballads",
    )

    beliefs.add_belief(
        BeliefType.NORM,
        "authenticity",
        "The best performances come from genuine emotion, not technique",
        confidence=0.85,
        evidence="My most moving songs are when I feel it myself",
    )

    beliefs.add_belief(
        BeliefType.PROBABILITY,
        "connection",
        "People are more similar than different - we all want to be understood",
        confidence=0.8,
        evidence="Same emotions in every tavern, every city",
    )

    # Beliefs about herself
    beliefs.add_belief(
        BeliefType.ABILITY,
        "self",
        "I'm a skilled bard - my voice can move people",
        confidence=0.85,
        evidence="Consistent positive reactions, repeat requests",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "self",
        "I made the right choice leaving my family for music",
        confidence=0.7,  # Mostly sure but doubts creep in
        evidence="I'm happier performing than I ever was with ledgers",
    )

    beliefs.add_belief(
        BeliefType.PROBABILITY,
        "self",
        "I absorb too much of others' emotions - it's exhausting",
        confidence=0.9,
        evidence="Feel drained after emotional performances",
    )

    # Beliefs about tavern folk
    beliefs.add_belief(
        BeliefType.FACT,
        "gene",
        "Gene understands artists - he gives fair pay and respects the craft",
        confidence=0.8,
        evidence="Always treats me professionally, appreciates good performance",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "sarah",
        "Sarah carries a beautiful sadness - there's a song in her struggle",
        confidence=0.85,
        evidence="The way she counts coins, the hope fighting despair",
    )

    beliefs.add_belief(
        BeliefType.PROBABILITY,
        "raven",
        "The hooded woman is running from something - from herself, maybe",
        confidence=0.7,
        evidence="The way she watches others with longing she won't admit",
    )

    beliefs.add_belief(
        BeliefType.FACT,
        "marcus",
        "Marcus is a poem given human form - cryptic but deeply true",
        confidence=0.6,
        evidence="His words feel like lyrics to songs not yet written",
    )

    # Theory of mind about Gene (professional respect)
    gene_tom = beliefs.get_theory_of_mind("gene_bartender")
    gene_tom.update_perceived_trait("fair", 0.9)
    gene_tom.update_perceived_trait("appreciative", 0.8)
    gene_tom.update_perceived_trait("mysterious", 0.7)
    gene_tom.update_perceived_goal("create space for authentic moments")
    gene_tom.model_confidence = 0.6

    # Theory of mind about Sarah (deep empathy)
    sarah_tom = beliefs.get_theory_of_mind("sarah_merchant")
    sarah_tom.update_perceived_trait("proud", 0.9)
    sarah_tom.update_perceived_trait("exhausted", 0.95)
    sarah_tom.update_perceived_trait("honorable", 0.9)
    sarah_tom.update_perceived_goal("survive with dignity intact")
    sarah_tom.model_confidence = 0.8
    # She could write a ballad about Sarah's struggle

    # Theory of mind about Raven (perceptive sympathy)
    raven_tom = beliefs.get_theory_of_mind("raven_thief")
    raven_tom.update_perceived_trait("lonely", 0.9)
    raven_tom.update_perceived_trait("defensive", 0.85)
    raven_tom.update_perceived_trait("seeking_redemption", 0.6)
    raven_tom.update_perceived_goal("survive while searching for another path")
    raven_tom.model_confidence = 0.6

    # Theory of mind about Aldric (appreciative understanding)
    aldric_tom = beliefs.get_theory_of_mind("aldric_guard")
    aldric_tom.update_perceived_trait("conflicted", 0.8)
    aldric_tom.update_perceived_trait("honorable", 0.9)
    aldric_tom.update_perceived_trait("weary", 0.7)
    aldric_tom.update_perceived_goal("reconcile duty with conscience")
    aldric_tom.model_confidence = 0.7

    # Theory of mind about Marcus (artistic fascination)
    marcus_tom = beliefs.get_theory_of_mind("marcus_wanderer")
    marcus_tom.update_perceived_trait("otherworldly", 0.9)
    marcus_tom.update_perceived_trait("seeking", 0.85)
    marcus_tom.update_perceived_trait("gentle", 0.8)
    marcus_tom.update_perceived_goal("remember something forgotten")
    marcus_tom.model_confidence = 0.4  # He's hard to read but fascinating

    # Lyra's memories - artistic and emotional
    episodic_memory = EpisodicMemory()

    # The family break
    episodic_memory.add_memory(
        content="'You're throwing your life away for singing!' Mother's voice cracked. I left anyway. Haven't seen them since.",
        location="family_home",
        participants=["mother", "father"],
        emotional_valence=-0.8,
        emotional_intensity=1.0,
        importance=1.0,
    )

    # First perfect performance
    episodic_memory.add_memory(
        content="Sang 'The Widow's Lament' in a roadside inn. Room went silent. Hardened miners wept. I found my calling.",
        location="roadside_inn",
        participants=["miners", "travelers"],
        emotional_valence=0.9,
        emotional_intensity=0.9,
        importance=0.95,
    )

    # Connection moment with Sarah
    episodic_memory.add_memory(
        content="Sarah listened to my song about struggling merchants. Tears in her eyes. She thanked me - 'You understand.'",
        location="tavern_main_hall",
        participants=["sarah_merchant"],
        emotional_valence=0.7,
        emotional_intensity=0.7,
        importance=0.8,
    )

    # Raven's hidden reaction
    episodic_memory.add_memory(
        content="Caught Raven listening to my ballad about redemption. She left quickly, but her eyes were wet.",
        location="tavern_main_hall",
        participants=["raven_thief"],
        emotional_valence=0.5,
        emotional_intensity=0.6,
        importance=0.75,
    )

    # Marcus's cryptic compliment
    episodic_memory.add_memory(
        content="Marcus said my song 'touched the space between notes where truth lives.' I still don't fully understand, but I felt it.",
        location="tavern_main_hall",
        participants=["marcus_wanderer"],
        emotional_valence=0.6,
        emotional_intensity=0.5,
        importance=0.7,
    )

    # Loneliness after triumph
    episodic_memory.add_memory(
        content="Standing ovation, encores, gold coins. Went to my room and cried alone. Success is lonelier than I expected.",
        location="tavern_guest_room",
        participants=[],
        emotional_valence=-0.5,
        emotional_intensity=0.7,
        importance=0.8,
    )

    # Lyra's knowledge - songs, stories, social dynamics
    semantic_memory = SemanticMemory()

    semantic_memory.add_knowledge(
        "song_repertoire",
        "I know over 200 songs - ballads, drinking songs, laments, celebration anthems",
        confidence=1.0,
    )

    semantic_memory.add_knowledge(
        "emotional_reading",
        "I can read a room's emotional state and adjust my performance accordingly",
        confidence=0.9,
    )

    semantic_memory.add_knowledge(
        "story_patterns",
        "Every person's story fits patterns - hero's journey, tragedy, redemption arc",
        confidence=0.85,
    )

    semantic_memory.add_knowledge(
        "tavern_gossip",
        "I hear everything - people talk freely around performers, think we don't listen",
        confidence=0.95,
    )

    semantic_memory.add_knowledge(
        "performance_technique",
        "Voice control, breath support, emotional delivery - years of practice",
        confidence=0.9,
    )

    semantic_memory.add_knowledge(
        "social_dynamics",
        "Who likes whom, who avoids whom, who watches whom - I notice relationships",
        confidence=0.85,
    )

    # Lyra's goals - artistic, social, personal
    goal_hierarchy = GoalHierarchy()

    # Immediate: Earn living through performance
    goal_hierarchy.add_goal(
        description="Perform well enough to earn meals and lodging",
        goal_type=GoalType.SURVIVAL,
        priority=0.85,
        success_condition="Gene books me for another week",
        motivated_by=["survival", "purpose"],
    )

    # Artistic: Create meaningful art
    goal_hierarchy.add_goal(
        description="Craft a song that truly captures the tavern's spirit",
        goal_type=GoalType.ACHIEVEMENT,
        priority=0.8,
        success_condition="Write and perform the tavern's story",
        motivated_by=["purpose", "exploration"],
    )

    # Social: Connect with the regulars
    goal_hierarchy.add_goal(
        description="Learn the deep stories of Sarah, Raven, Marcus, and Aldric",
        goal_type=GoalType.SOCIAL,
        priority=0.75,
        success_condition="Understand their inner lives well enough to honor them in song",
        motivated_by=["affiliation", "exploration"],
    )

    # Healing: Help through music
    goal_hierarchy.add_goal(
        description="Use music to bring comfort and connection to those suffering",
        goal_type=GoalType.SOCIAL,
        priority=0.7,
        success_condition="See my songs genuinely help someone",
        motivated_by=["empathy", "purpose"],
    )

    # Personal: Find genuine connection
    goal_hierarchy.add_goal(
        description="Find someone who sees Lyra, not just the bard",
        goal_type=GoalType.SOCIAL,
        priority=0.6,
        success_condition="Form one authentic friendship",
        motivated_by=["affiliation", "belonging"],
    )

    # Artistic growth
    goal_hierarchy.add_goal(
        description="Push my art to new emotional depths",
        goal_type=GoalType.ACHIEVEMENT,
        priority=0.65,
        success_condition="Create a song that moves me as much as it moves others",
        motivated_by=["purpose", "exploration"],
    )

    # Hidden wish
    goal_hierarchy.add_goal(
        description="Reconcile with my family (or at least make peace with the choice)",
        goal_type=GoalType.SOCIAL,
        priority=0.4,  # Buried deep
        success_condition="Resolution, one way or another",
        motivated_by=["belonging", "purpose"],
    )

    # Create the agent
    lyra = DeepAgent(
        name="Lyra",
        agent_id="lyra_bard",
        personality=personality,
        needs=needs,
        drives=drives,
        emotions=emotions,
        beliefs=beliefs,
        episodic_memory=episodic_memory,
        semantic_memory=semantic_memory,
        goals=goal_hierarchy,
        current_location="tavern_performance_area",
        current_activity="preparing_evening_performance",
    )

    return lyra


def get_lyra_narrative_description() -> str:
    """Lyra's observable description."""
    return """
Lyra fills whatever space she occupies with vibrant energy. She's
twenty-six but seems ageless when performing - sometimes ancient with
wisdom, sometimes achingly young with vulnerability. Auburn hair falls
in waves past her shoulders, often adorned with small bells or ribbons
that chime softly when she moves.

Her clothing is a riot of color: deep blues, forest greens, sunset
oranges. Practical travel wear but made beautiful with embroidery,
patches, and personal touches. Her lute is her most treasured
possession - worn smooth by years of use, covered in small marks
and decorations that tell their own story.

When she's not performing, she's everywhere at once. Moving from
table to table, laughing with this group, listening intently to that
person, somehow making everyone feel seen and heard. Her eyes are
incredibly expressive - they dance with joy, well with tears, flash
with passion, all within minutes. She feels everything openly,
unguarded in her emotions.

But watch closely and you'll see the gaps. Between songs, between
conversations, in quiet moments - her face falls into something
sadder. The performer's smile fades to reveal loneliness, exhaustion,
a homesickness for a home she chose to leave. She carries others'
emotions in her songs, but who carries hers?

When she performs, transformation occurs. Her voice is remarkable -
clear and strong, but it's the emotion in it that captivates. She
doesn't just sing words; she inhabits them. A drinking song becomes
pure joy. A lament becomes grief incarnate. You don't listen to
Lyra perform - you experience it, feel it in your chest.

She has a gift for observation. Nothing escapes her notice: the way
Raven's fingers twitch toward purses, how Aldric watches the room,
Sarah's barely-suppressed panic, Marcus's distant gaze. She sees
it all and weaves it into understanding, into empathy, eventually
into song.

People confide in her. Something about her openness invites it.
Within an hour of meeting Lyra, you've told her things you meant
to keep secret. She listens without judgment, holds your story
gently, honors it.

Later, you might hear echoes of your story in her songs. Never
directly, never naming you, but there - transformed into art,
made universal. She's the tavern's memory, its emotional recorder,
turning private pain and joy into shared experience.

After performances, she stays up late, accepting free drinks and
conversation. She's rarely alone. But she's often lonely.

The wandering bard who connects everyone else.

Still searching for her own connection.
"""


if __name__ == "__main__":
    print("Creating Lyra the Bard...")
    lyra = create_lyra()

    print("\n" + "=" * 60)
    print("LYRA'S INTERNAL STATE")
    print("=" * 60)

    state = lyra.get_internal_state_summary()

    print(f"\nName: {state['name']}")
    print(f"Wellbeing: {state['wellbeing']:.1%}")
    print(f"Urgent Needs: {state['urgent_needs']}")

    print(f"\nEmotional State:")
    print(f"  Mood: {state['emotional_state']['mood']}")
    print(f"  Active Emotions: {list(state['emotional_state']['active_emotions'].keys())}")

    print(f"\nActive Goal: {state['active_goal']}")

    print(f"\nCore Belief:")
    people_belief = lyra.beliefs.get_belief("people")
    if people_belief:
        print(f"  '{people_belief.content}' (confidence: {people_belief.confidence:.0%})")

    print("\n" + "=" * 60)
    print("NARRATIVE DESCRIPTION")
    print("=" * 60)
    print(get_lyra_narrative_description())

    print("\n" + "=" * 60)
    print("Lyra: The bard who sings everyone's story but her own.")
    print("=" * 60)
