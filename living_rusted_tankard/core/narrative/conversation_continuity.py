"""
Persistent NPC conversations system.
Makes conversations feel natural and continuous rather than repetitive interactions.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
import time
import random
import logging

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """States a conversation can be in."""
    GREETING = "greeting"
    SMALL_TALK = "small_talk"
    BUSINESS = "business"
    PERSONAL = "personal"
    STORYTELLING = "storytelling"
    GOSSIP = "gossip"
    FAREWELL = "farewell"
    INTERRUPTED = "interrupted"
    WAITING_FOR_RESPONSE = "waiting_for_response"


class ConversationTopic(Enum):
    """Topics NPCs can discuss."""
    WEATHER = "weather"
    BUSINESS = "business"
    LOCAL_NEWS = "local_news"
    PERSONAL_LIFE = "personal_life"
    PAST_ADVENTURES = "past_adventures"
    CURRENT_EVENTS = "current_events"
    GOSSIP = "gossip"
    PHILOSOPHY = "philosophy"
    TRADE = "trade"
    FAMILY = "family"
    DREAMS = "dreams"
    FEARS = "fears"
    HOBBIES = "hobbies"
    WORK = "work"
    POLITICS = "politics"


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""
    speaker: str  # "player" or npc_id
    message: str
    topic: ConversationTopic
    timestamp: float
    emotional_tone: str  # "happy", "sad", "angry", "neutral", etc.
    reveals_information: bool = False
    asks_question: bool = False
    references_past: bool = False


@dataclass
class OngoingConversation:
    """An ongoing conversation between player and NPC."""
    npc_id: str
    npc_name: str
    start_time: float
    last_interaction: float
    current_state: ConversationState
    current_topic: Optional[ConversationTopic]
    
    turns: List[ConversationTurn] = field(default_factory=list)
    topics_discussed: Set[ConversationTopic] = field(default_factory=set)
    interruption_count: int = 0
    relationship_changes: List[Tuple[str, float]] = field(default_factory=list)  # What changed and by how much
    
    # Context for continuing conversations
    last_question_asked: Optional[str] = None
    waiting_for_response_about: Optional[str] = None
    promised_to_discuss: Optional[str] = None
    
    def add_turn(self, speaker: str, message: str, topic: ConversationTopic, 
                emotional_tone: str = "neutral", reveals_info: bool = False, 
                asks_question: bool = False, references_past: bool = False):
        """Add a turn to the conversation."""
        turn = ConversationTurn(
            speaker=speaker,
            message=message,
            topic=topic,
            timestamp=time.time(),
            emotional_tone=emotional_tone,
            reveals_information=reveals_info,
            asks_question=asks_question,
            references_past=references_past
        )
        
        self.turns.append(turn)
        self.topics_discussed.add(topic)
        self.current_topic = topic
        self.last_interaction = time.time()
        
        if asks_question and speaker != "player":
            self.last_question_asked = message
            self.current_state = ConversationState.WAITING_FOR_RESPONSE
    
    def get_conversation_length(self) -> int:
        """Get number of turns in conversation."""
        return len(self.turns)
    
    def get_time_since_last_turn(self) -> float:
        """Get hours since last conversation turn."""
        return (time.time() - self.last_interaction) / 3600.0
    
    def should_continue_previous_topic(self) -> bool:
        """Check if conversation should continue previous topic."""
        time_since = self.get_time_since_last_turn()
        
        # Very recent conversations should continue
        if time_since < 0.1:  # 6 minutes
            return True
        
        # If waiting for response, should continue up to a reasonable time
        if self.current_state == ConversationState.WAITING_FOR_RESPONSE and time_since < 24:
            return True
        
        # If conversation was interrupted, might continue
        if self.current_state == ConversationState.INTERRUPTED and time_since < 12:
            return True
        
        return False
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation so far."""
        if not self.turns:
            return "No conversation yet."
        
        total_time = (self.last_interaction - self.start_time) / 60.0  # minutes
        
        summary = f"Conversation with {self.npc_name} ({len(self.turns)} turns over {total_time:.1f} minutes). "
        
        if self.topics_discussed:
            topics = ", ".join(topic.value for topic in self.topics_discussed)
            summary += f"Discussed: {topics}. "
        
        if self.current_state == ConversationState.WAITING_FOR_RESPONSE:
            summary += f"NPC asked: '{self.last_question_asked}'"
        elif self.promised_to_discuss:
            summary += f"Promised to discuss: {self.promised_to_discuss}"
        
        return summary


class ConversationMemory:
    """Remembers conversations across multiple interactions."""
    
    def __init__(self, npc_id: str, npc_name: str):
        self.npc_id = npc_id
        self.npc_name = npc_name
        self.conversations: List[OngoingConversation] = []
        self.current_conversation: Optional[OngoingConversation] = None
        
        # What this NPC tends to talk about
        self.favorite_topics: Set[ConversationTopic] = set()
        self.avoided_topics: Set[ConversationTopic] = set()
        
        # Conversation patterns
        self.typical_greeting_style: str = "polite"
        self.chattiness_level: float = 0.5  # 0.0 = laconic, 1.0 = very chatty
        self.question_frequency: float = 0.3  # How often they ask questions
        self.story_telling_tendency: float = 0.4  # How likely to tell stories
        
        # Information revealed over time
        self.revealed_secrets: Set[str] = set()
        self.personal_info_shared: Dict[str, str] = {}
        self.trust_threshold_for_secrets: float = 0.7
    
    def start_new_conversation(self) -> OngoingConversation:
        """Start a new conversation."""
        # End current conversation if exists
        if self.current_conversation:
            self.end_current_conversation()
        
        self.current_conversation = OngoingConversation(
            npc_id=self.npc_id,
            npc_name=self.npc_name,
            start_time=time.time(),
            last_interaction=time.time(),
            current_state=ConversationState.GREETING
        )
        
        return self.current_conversation
    
    def continue_conversation(self) -> Optional[OngoingConversation]:
        """Continue existing conversation if appropriate."""
        if not self.current_conversation:
            return None
        
        if self.current_conversation.should_continue_previous_topic():
            self.current_conversation.last_interaction = time.time()
            return self.current_conversation
        else:
            # Too much time has passed, start fresh
            return self.start_new_conversation()
    
    def end_current_conversation(self):
        """End the current conversation and archive it."""
        if self.current_conversation:
            # Add to conversation history
            self.conversations.append(self.current_conversation)
            
            # Keep only recent conversations to avoid memory bloat
            if len(self.conversations) > 10:
                self.conversations = self.conversations[-10:]
            
            self.current_conversation = None
    
    def get_conversation_context(self) -> Dict[str, Any]:
        """Get context for generating appropriate responses."""
        context = {
            "conversation_exists": self.current_conversation is not None,
            "conversation_length": 0,
            "recent_topics": [],
            "waiting_for_response": False,
            "question_asked": None,
            "promised_topic": None,
            "previous_conversations": len(self.conversations),
            "favorite_topics": list(self.favorite_topics),
            "chattiness": self.chattiness_level,
            "revealed_secrets": list(self.revealed_secrets)
        }
        
        if self.current_conversation:
            conv = self.current_conversation
            context.update({
                "conversation_length": conv.get_conversation_length(),
                "recent_topics": [topic.value for topic in list(conv.topics_discussed)[-3:]],
                "waiting_for_response": conv.current_state == ConversationState.WAITING_FOR_RESPONSE,
                "question_asked": conv.last_question_asked,
                "promised_topic": conv.promised_to_discuss,
                "current_state": conv.current_state.value,
                "time_since_last_turn": conv.get_time_since_last_turn()
            })
        
        return context
    
    def should_reveal_secret(self, trust_level: float, relationship_length: int) -> bool:
        """Determine if NPC should reveal a secret based on relationship."""
        base_threshold = self.trust_threshold_for_secrets
        
        # Lower threshold for longer relationships
        adjusted_threshold = base_threshold - (relationship_length * 0.05)
        
        # Some random factor
        random_factor = random.uniform(-0.1, 0.1)
        
        return trust_level > (adjusted_threshold + random_factor)
    
    def get_appropriate_topics(self, relationship_level: str, current_mood: str) -> List[ConversationTopic]:
        """Get topics appropriate for current relationship and mood."""
        topics = []
        
        # Always available topics
        basic_topics = [ConversationTopic.WEATHER, ConversationTopic.BUSINESS, ConversationTopic.WORK]
        topics.extend(basic_topics)
        
        # Relationship-gated topics
        if relationship_level in ["acquaintance", "friendly", "friend", "trusted"]:
            topics.extend([ConversationTopic.LOCAL_NEWS, ConversationTopic.CURRENT_EVENTS, ConversationTopic.TRADE])
        
        if relationship_level in ["friendly", "friend", "trusted"]:
            topics.extend([ConversationTopic.HOBBIES, ConversationTopic.PAST_ADVENTURES, ConversationTopic.PERSONAL_LIFE])
        
        if relationship_level in ["friend", "trusted"]:
            topics.extend([ConversationTopic.FAMILY, ConversationTopic.DREAMS, ConversationTopic.PHILOSOPHY])
        
        if relationship_level == "trusted":
            topics.extend([ConversationTopic.FEARS, ConversationTopic.GOSSIP, ConversationTopic.POLITICS])
        
        # Mood affects topic selection
        if current_mood in ["happy", "cheerful", "excited"]:
            topics.extend([ConversationTopic.DREAMS, ConversationTopic.HOBBIES])
        elif current_mood in ["sad", "worried", "anxious"]:
            topics.extend([ConversationTopic.FEARS, ConversationTopic.PERSONAL_LIFE])
        elif current_mood == "angry":
            topics.extend([ConversationTopic.POLITICS, ConversationTopic.CURRENT_EVENTS])
        
        # Remove avoided topics
        topics = [t for t in topics if t not in self.avoided_topics]
        
        # Prioritize favorite topics
        favorite_topics_available = [t for t in self.favorite_topics if t in topics]
        if favorite_topics_available:
            # Put favorite topics first, then others
            other_topics = [t for t in topics if t not in self.favorite_topics]
            topics = favorite_topics_available + other_topics
        
        return topics


class ConversationGenerator:
    """Generates contextual dialogue based on conversation state."""
    
    def __init__(self):
        self.topic_starters = {
            ConversationTopic.WEATHER: [
                "Lovely weather we're having, isn't it?",
                "Quite the storm last night, wasn't it?",
                "I hope this rain lets up soon.",
                "Perfect day for traveling, this is."
            ],
            ConversationTopic.BUSINESS: [
                "Business has been good lately.",
                "Things have been quiet around the shop.",
                "I've got some new items in stock.",
                "The market's been unpredictable recently."
            ],
            ConversationTopic.LOCAL_NEWS: [
                "Did you hear about what happened at the market?",
                "There's been some interesting developments in town.",
                "The townspeople have been talking about...",
                "Have you noticed anything unusual lately?"
            ],
            ConversationTopic.PERSONAL_LIFE: [
                "I've been thinking about my future lately.",
                "My family has been on my mind.",
                "Life has been treating me well.",
                "I've been having the strangest dreams."
            ]
        }
        
        self.continuation_phrases = [
            "Speaking of which,",
            "That reminds me,",
            "On a related note,",
            "While we're on the subject,",
            "Actually,",
            "You know what,",
            "I just remembered,"
        ]
        
        self.question_starters = [
            "What do you think about",
            "Have you ever wondered",
            "I'm curious about",
            "What's your opinion on",
            "Do you happen to know",
            "Have you heard anything about"
        ]
    
    def generate_greeting(self, conversation_memory: ConversationMemory, 
                         relationship_level: str, time_since_last: float) -> str:
        """Generate an appropriate greeting."""
        
        # Check if continuing a conversation
        if conversation_memory.current_conversation and conversation_memory.current_conversation.should_continue_previous_topic():
            if conversation_memory.current_conversation.current_state == ConversationState.WAITING_FOR_RESPONSE:
                return f"So, about what I asked earlier... {conversation_memory.current_conversation.last_question_asked}"
            elif conversation_memory.current_conversation.promised_to_discuss:
                return f"Ah, I promised to tell you about {conversation_memory.current_conversation.promised_to_discuss}."
            else:
                return f"Where were we? Ah yes, we were talking about {conversation_memory.current_conversation.current_topic.value if conversation_memory.current_conversation.current_topic else 'various things'}."
        
        # Fresh greeting based on relationship and time
        if relationship_level == "stranger":
            greetings = ["Hello there.", "Good day.", "Greetings, traveler."]
        elif relationship_level == "acquaintance":
            if time_since_last < 24:
                greetings = ["Back again, I see.", "Hello again.", "Good to see you."]
            else:
                greetings = ["Well, hello there.", "Good to see you again.", "It's been a while."]
        elif relationship_level in ["friendly", "friend"]:
            if time_since_last < 12:
                greetings = ["Back so soon?", "Couldn't stay away, eh?", "Always a pleasure to see you."]
            else:
                greetings = ["My friend! Good to see you.", "Well, look who's back!", "Always good to see a friendly face."]
        else:  # trusted
            greetings = ["My dear friend, welcome.", "There you are! I was hoping you'd come by.", "Always a joy to see you."]
        
        return random.choice(greetings)
    
    def generate_topic_transition(self, current_topic: Optional[ConversationTopic], 
                                new_topic: ConversationTopic, chattiness: float) -> str:
        """Generate a natural transition between topics."""
        if not current_topic or random.random() < 0.3:
            # Direct topic starter
            return random.choice(self.topic_starters.get(new_topic, ["Let me tell you something interesting."]))
        
        # Use continuation phrase for chattier NPCs
        if chattiness > 0.6:
            continuation = random.choice(self.continuation_phrases)
            starter = random.choice(self.topic_starters.get(new_topic, ["something interesting happened"]))
            return f"{continuation} {starter.lower()}"
        else:
            return random.choice(self.topic_starters.get(new_topic, ["Anyway,"]))
    
    def should_ask_question(self, conversation_length: int, question_frequency: float) -> bool:
        """Determine if NPC should ask a question."""
        # More likely to ask questions in longer conversations
        base_chance = question_frequency
        if conversation_length > 5:
            base_chance += 0.2
        
        return random.random() < base_chance


class ConversationManager:
    """Manages conversation continuity for all NPCs."""
    
    def __init__(self):
        self.conversation_memories: Dict[str, ConversationMemory] = {}
        self.conversation_generator = ConversationGenerator()
    
    def get_or_create_memory(self, npc_id: str, npc_name: str) -> ConversationMemory:
        """Get existing conversation memory or create new one."""
        if npc_id not in self.conversation_memories:
            self.conversation_memories[npc_id] = ConversationMemory(npc_id, npc_name)
            logger.info(f"Created conversation memory for {npc_name}")
        return self.conversation_memories[npc_id]
    
    def start_conversation(self, npc_id: str, npc_name: str, relationship_level: str, 
                         time_since_last_interaction: float) -> Tuple[str, Dict[str, Any]]:
        """Start or continue a conversation with an NPC."""
        memory = self.get_or_create_memory(npc_id, npc_name)
        
        # Try to continue existing conversation or start new one
        conversation = memory.continue_conversation()
        if not conversation:
            conversation = memory.start_new_conversation()
        
        # Generate greeting
        greeting = self.conversation_generator.generate_greeting(
            memory, relationship_level, time_since_last_interaction
        )
        
        # Add greeting turn
        conversation.add_turn(
            speaker=npc_id,
            message=greeting,
            topic=ConversationTopic.WEATHER,  # Default topic for greetings
            emotional_tone="neutral"
        )
        
        # Return context for dialogue system
        context = memory.get_conversation_context()
        
        return greeting, context
    
    def continue_conversation(self, npc_id: str, player_message: str, 
                            relationship_level: str, current_mood: str) -> Tuple[str, Dict[str, Any]]:
        """Continue an ongoing conversation."""
        if npc_id not in self.conversation_memories:
            return "I'm sorry, what were we talking about?", {}
        
        memory = self.conversation_memories[npc_id]
        if not memory.current_conversation:
            return "Let's start fresh, shall we?", {}
        
        conversation = memory.current_conversation
        
        # Add player turn
        conversation.add_turn(
            speaker="player",
            message=player_message,
            topic=conversation.current_topic or ConversationTopic.WEATHER,
            emotional_tone="neutral"
        )
        
        # Generate NPC response
        response, new_topic = self._generate_contextual_response(
            memory, player_message, relationship_level, current_mood
        )
        
        # Add NPC response turn
        should_ask = self.conversation_generator.should_ask_question(
            conversation.get_conversation_length(),
            memory.question_frequency
        )
        
        conversation.add_turn(
            speaker=npc_id,
            message=response,
            topic=new_topic,
            emotional_tone=current_mood,
            asks_question=should_ask
        )
        
        context = memory.get_conversation_context()
        return response, context
    
    def _generate_contextual_response(self, memory: ConversationMemory, 
                                    player_message: str, relationship_level: str, 
                                    current_mood: str) -> Tuple[str, ConversationTopic]:
        """Generate contextual response based on conversation state."""
        conversation = memory.current_conversation
        
        # Get appropriate topics for this relationship level
        available_topics = memory.get_appropriate_topics(relationship_level, current_mood)
        
        # Choose topic based on context
        if conversation.current_state == ConversationState.WAITING_FOR_RESPONSE:
            # Player answered a question
            responses = ["I hadn't thought of it that way.", "That makes sense.", "I see your point."]
            response = f"Interesting perspective. {random.choice(responses)}"
            new_topic = conversation.current_topic or random.choice(available_topics)
            conversation.current_state = ConversationState.SMALL_TALK
        else:
            # Choose new topic, avoiding recently discussed ones
            recent_topics = set(list(conversation.topics_discussed)[-2:])
            fresh_topics = [t for t in available_topics if t not in recent_topics]
            
            if not fresh_topics:
                fresh_topics = available_topics
            
            new_topic = random.choice(fresh_topics)
            
            # Generate transition to new topic
            response = self.conversation_generator.generate_topic_transition(
                conversation.current_topic, new_topic, memory.chattiness_level
            )
        
        return response, new_topic
    
    def end_conversation(self, npc_id: str) -> Optional[str]:
        """End a conversation gracefully."""
        if npc_id in self.conversation_memories:
            memory = self.conversation_memories[npc_id]
            if memory.current_conversation:
                farewell = random.choice([
                    "Well, it's been good talking with you.",
                    "I should get back to what I was doing.",
                    "Thanks for the chat.",
                    "We should talk again soon.",
                    "Until next time, then."
                ])
                
                memory.current_conversation.add_turn(
                    speaker=npc_id,
                    message=farewell,
                    topic=ConversationTopic.WEATHER,  # Neutral farewell topic
                    emotional_tone="neutral"
                )
                
                memory.end_current_conversation()
                return farewell
        
        return None
    
    def get_conversation_summaries(self) -> Dict[str, str]:
        """Get conversation summaries for all NPCs."""
        summaries = {}
        for npc_id, memory in self.conversation_memories.items():
            if memory.current_conversation:
                summaries[npc_id] = memory.current_conversation.get_conversation_summary()
            elif memory.conversations:
                last_conv = memory.conversations[-1]
                summaries[npc_id] = f"Last conversation: {last_conv.get_conversation_summary()}"
        
        return summaries