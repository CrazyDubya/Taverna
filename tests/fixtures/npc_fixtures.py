"""
NPC-related test fixtures.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

try:
    from core.npc import NPC, NPCManager
    NPC_AVAILABLE = True
except ImportError:
    NPC_AVAILABLE = False


@pytest.fixture
def test_npc_data():
    """Provide test NPC data for fixtures."""
    return {
        "test_bartender": {
            "id": "test_bartender",
            "name": "Gene",
            "title": "Bartender",
            "description": "A friendly bartender who knows everyone's business.",
            "personality": "friendly",
            "schedule": {
                "always_present": True,
                "presence_hours": [0, 24]
            },
            "relationships": {},
            "conversation_topics": [
                "weather",
                "tavern_news",
                "local_gossip"
            ],
            "interactions": [
                {
                    "id": "talk",
                    "name": "Talk",
                    "description": "Have a conversation",
                    "conditions": [],
                    "actions": []
                },
                {
                    "id": "buy_drink",
                    "name": "Buy a drink",
                    "description": "Purchase an alcoholic beverage",
                    "conditions": [{"type": "gold", "amount": 2}],
                    "actions": [
                        {"type": "remove_gold", "amount": 2},
                        {"type": "add_item", "item": "ale", "quantity": 1}
                    ]
                }
            ]
        },
        "test_merchant": {
            "id": "test_merchant",
            "name": "Tom",
            "title": "Traveling Merchant",
            "description": "A merchant with various goods.",
            "personality": "business_minded",
            "schedule": {
                "always_present": False,
                "presence_hours": [9, 17]
            },
            "relationships": {},
            "conversation_topics": [
                "trade",
                "prices",
                "goods"
            ],
            "interactions": [
                {
                    "id": "trade",
                    "name": "Trade",
                    "description": "Browse merchant's wares",
                    "conditions": [],
                    "actions": []
                }
            ]
        },
        "test_patron": {
            "id": "test_patron",
            "name": "Bob",
            "title": "Tavern Patron",
            "description": "A regular customer who enjoys drinking.",
            "personality": "jovial",
            "schedule": {
                "always_present": False,
                "presence_hours": [18, 23]
            },
            "relationships": {},
            "conversation_topics": [
                "drinks",
                "stories",
                "rumors"
            ],
            "interactions": [
                {
                    "id": "chat",
                    "name": "Chat",
                    "description": "Have a casual conversation",
                    "conditions": [],
                    "actions": []
                }
            ]
        }
    }


@pytest.fixture
def mock_npc_manager(test_npc_data):
    """Create a mock NPC manager with test NPCs."""
    class MockNPCManager:
        def __init__(self):
            self.npcs = {}
            self.present_npcs = {}
            self.load_test_npcs(test_npc_data)
        
        def load_test_npcs(self, npc_data: Dict[str, Any]):
            """Load test NPCs into the manager."""
            for npc_id, data in npc_data.items():
                # Create a simple mock NPC
                npc = MagicMock()
                npc.id = npc_id
                npc.name = data["name"]
                npc.title = data["title"]
                npc.description = data["description"]
                npc.personality = data["personality"]
                npc.is_present = data["schedule"].get("always_present", False)
                npc.conversation_topics = data["conversation_topics"]
                npc.interactions = data["interactions"]
                npc.relationships = data.get("relationships", {})
                
                self.npcs[npc_id] = npc
                if npc.is_present:
                    self.present_npcs[npc_id] = npc
        
        def get_npc(self, npc_id: str):
            return self.npcs.get(npc_id)
        
        def get_present_npcs(self) -> Dict[str, Any]:
            return self.present_npcs.copy()
        
        def is_npc_present(self, npc_id: str) -> bool:
            return npc_id in self.present_npcs
        
        def force_npc_presence(self, npc_id: str, present: bool = True):
            """Force an NPC to be present or absent (for testing)."""
            if npc_id in self.npcs:
                npc = self.npcs[npc_id]
                npc.is_present = present
                if present:
                    self.present_npcs[npc_id] = npc
                else:
                    self.present_npcs.pop(npc_id, None)
        
        def update_all_npcs(self, current_time: float):
            """Mock NPC update method."""
            pass
        
        def interact_with_npc(self, npc_id: str, interaction_id: str, **kwargs):
            """Mock NPC interaction."""
            npc = self.get_npc(npc_id)
            if not npc or not self.is_npc_present(npc_id):
                return {"success": False, "message": "NPC not available"}
            
            # Find the interaction
            for interaction in npc.interactions:
                if interaction["id"] == interaction_id:
                    return {
                        "success": True,
                        "message": f"Interacted with {npc.name}: {interaction['description']}",
                        "actions": interaction.get("actions", [])
                    }
            
            return {"success": False, "message": "Unknown interaction"}
    
    return MockNPCManager()


@pytest.fixture
def npc_with_schedule():
    """Create an NPC with a specific schedule for time-based testing."""
    def _create_npc_with_schedule(presence_start: int = 9, presence_end: int = 17):
        if not NPC_AVAILABLE:
            # Return a mock if real NPC class not available
            npc = MagicMock()
            npc.id = "scheduled_npc"
            npc.name = "Scheduled NPC"
            npc.presence_start = presence_start
            npc.presence_end = presence_end
            
            def mock_is_present(current_hour):
                return presence_start <= current_hour < presence_end
            
            npc.is_present_at_time = mock_is_present
            return npc
        
        # Return actual NPC if available
        return NPC(
            npc_id="scheduled_npc",
            name="Scheduled NPC",
            schedule={"presence_hours": [presence_start, presence_end]}
        )
    
    return _create_npc_with_schedule


@pytest.fixture
def npc_relationship_test_setup():
    """Set up NPCs with predefined relationships for testing relationship mechanics."""
    relationships = {
        "friendly_npc": {
            "relationship_value": 0.7,
            "interaction_history": ["positive", "positive", "neutral"]
        },
        "neutral_npc": {
            "relationship_value": 0.0,
            "interaction_history": ["neutral"]
        },
        "hostile_npc": {
            "relationship_value": -0.5,
            "interaction_history": ["negative", "negative"]
        }
    }
    
    class MockRelationshipManager:
        def __init__(self):
            self.relationships = relationships
        
        def get_relationship(self, npc_id: str) -> float:
            return self.relationships.get(npc_id, {}).get("relationship_value", 0.0)
        
        def modify_relationship(self, npc_id: str, change: float):
            if npc_id not in self.relationships:
                self.relationships[npc_id] = {"relationship_value": 0.0, "interaction_history": []}
            
            self.relationships[npc_id]["relationship_value"] += change
            # Clamp between -1.0 and 1.0
            self.relationships[npc_id]["relationship_value"] = max(-1.0, min(1.0, 
                self.relationships[npc_id]["relationship_value"]))
        
        def add_interaction_history(self, npc_id: str, interaction_type: str):
            if npc_id not in self.relationships:
                self.relationships[npc_id] = {"relationship_value": 0.0, "interaction_history": []}
            
            self.relationships[npc_id]["interaction_history"].append(interaction_type)
    
    return MockRelationshipManager()


@pytest.fixture
def conversational_npc():
    """Create an NPC specifically set up for conversation testing."""
    class ConversationalNPC:
        def __init__(self):
            self.id = "chatty_npc"
            self.name = "Chatty"
            self.conversation_state = "greeting"
            self.topics_discussed = []
            self.available_topics = [
                "weather",
                "tavern_news", 
                "local_gossip",
                "personal_story",
                "trade_rumors"
            ]
        
        def start_conversation(self):
            self.conversation_state = "active"
            return "Hello there! What would you like to talk about?"
        
        def discuss_topic(self, topic: str) -> str:
            if topic in self.available_topics and topic not in self.topics_discussed:
                self.topics_discussed.append(topic)
                responses = {
                    "weather": "The weather has been quite pleasant lately.",
                    "tavern_news": "Did you hear about the new shipment of ale?",
                    "local_gossip": "There are rumors about strange lights in the forest.",
                    "personal_story": "I once traveled to the eastern kingdoms...",
                    "trade_rumors": "Merchants say prices will rise soon."
                }
                return responses.get(topic, "That's interesting to discuss.")
            elif topic in self.topics_discussed:
                return "We've already talked about that."
            else:
                return "I don't know much about that topic."
        
        def end_conversation(self):
            self.conversation_state = "ended"
            return "It was nice talking with you!"
    
    return ConversationalNPC()


@pytest.fixture
def npc_interaction_validator():
    """Provide utilities for validating NPC interactions."""
    class InteractionValidator:
        def __init__(self):
            self.interaction_log = []
        
        def log_interaction(self, npc_id: str, interaction_type: str, result: Dict[str, Any]):
            """Log an interaction for validation."""
            self.interaction_log.append({
                "npc_id": npc_id,
                "interaction_type": interaction_type,
                "result": result,
                "timestamp": "mock_timestamp"
            })
        
        def validate_interaction_success(self, npc_id: str, interaction_type: str) -> bool:
            """Validate that an interaction was successful."""
            for log_entry in self.interaction_log:
                if (log_entry["npc_id"] == npc_id and 
                    log_entry["interaction_type"] == interaction_type):
                    return log_entry["result"].get("success", False)
            return False
        
        def get_interaction_count(self, npc_id: str = None) -> int:
            """Get count of interactions, optionally filtered by NPC."""
            if npc_id:
                return len([log for log in self.interaction_log if log["npc_id"] == npc_id])
            return len(self.interaction_log)
        
        def clear_log(self):
            """Clear the interaction log."""
            self.interaction_log.clear()
    
    return InteractionValidator()