# LLM Integration Plan for Taverna

## Overview
This plan outlines how to integrate Claude (or another capable LLM) as a Game Master for "The Living Rusted Tankard", transforming it into a more flexible MUD-like experience where the LLM serves as both interpreter and storyteller.

## Core Concept
Rather than relying solely on a rigid command parser that responds with "I don't understand" for unrecognized commands, we'll implement an LLM layer that:

1. Interprets natural language inputs
2. Translates them to game commands when appropriate
3. Provides natural, contextual responses
4. Maintains narrative coherence
5. Guides users toward the correct interaction patterns

## Implementation Strategy

### Phase 1: LLM Integration Architecture
- Create a new middleware layer between the user interface and command parser
- Implement an API client to connect to Claude API
- Develop a context management system to track conversation history
- Design a prompt engineering system for effective LLM guidance

### Phase 2: Command Interpretation
- Design prompts that help the LLM understand game mechanics
- Build a system to extract structured commands from natural language
- Implement fallback responses for unclear inputs
- Create a response enrichment layer to add detail to simple parser outputs

### Phase 3: Enhanced Storytelling
- Develop a knowledge base of the game world for the LLM
- Create character personas for NPCs
- Implement narrative bridging between discrete game states
- Add descriptive embellishments to environment descriptions

### Phase 4: Player Guidance
- Design a scaffolding system to guide new players
- Implement contextual help that suggests possible actions
- Create a hint system for when players seem stuck
- Build a dynamic tutorial mode

## Technical Components

### 1. LLM Middleware
```python
class LLMGameMaster:
    def __init__(self, game_state, api_client):
        self.game_state = game_state
        self.api_client = api_client
        self.conversation_history = []
        
    def process_input(self, user_input):
        # Get game context
        context = self._build_context()
        
        # Generate LLM response
        llm_response = self._query_llm(context, user_input)
        
        # Extract commands if applicable
        commands = self._extract_commands(llm_response)
        
        # Execute commands if found
        game_response = None
        if commands:
            game_response = self._execute_commands(commands)
            
        # Generate final response
        final_response = self._generate_final_response(llm_response, game_response)
        
        # Update conversation history
        self._update_history(user_input, final_response)
        
        return final_response
```

### 2. Context Builder
```python
def _build_context(self):
    """Build rich context for the LLM including game state, player status, etc."""
    context = {
        "current_location": self.game_state.current_location,
        "time": self.game_state.clock.get_formatted_time(),
        "player": {
            "inventory": self.game_state.player.inventory.list_items_for_display(),
            "gold": self.game_state.player.gold,
            "status": self.game_state.player.get_status_effects()
        },
        "visible_npcs": [npc.name for npc in self.game_state.npc_manager.get_present_npcs()],
        "recent_events": [event.message for event in self.game_state.events[-5:]]
    }
    return context
```

### 3. Prompt Engineering
The system prompt for the LLM will include:

1. Game mechanics explanation
2. Description of the world
3. Available commands and their effects
4. Guidance on how to interpret and respond to natural language
5. Examples of inputs and appropriate responses
6. Character and tone guidelines

## API Integration

### 1. Claude API Client
```python
class ClaudeAPIClient:
    def __init__(self, api_key, model="claude-3-haiku-20240307"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
        
    def generate_response(self, system_prompt, conversation_history, user_input):
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        messages = self._format_messages(conversation_history, user_input)
        
        data = {
            "model": self.model,
            "system": system_prompt,
            "messages": messages,
            "max_tokens": 1000
        }
        
        response = requests.post(self.base_url, headers=headers, json=data)
        return response.json()["content"][0]["text"]
```

## User Experience Flow
1. User enters natural language input ("I want to talk to the bartender")
2. LLM interprets intent and context
3. LLM decides if a direct game command is needed ("talk gene_bartender")
4. Game engine processes command if needed
5. LLM crafts a natural language response incorporating game state changes
6. User receives a rich, contextually appropriate response

## Example Interactions

### Example 1: Simple Command Interpretation
**User Input:** "I want to check what I'm carrying"  
**LLM Processing:** Identifies intent to view inventory  
**Game Command:** "inventory"  
**Game Response:** List of items with quantities  
**Final Response:** "You reach into your pockets and bag, taking stock of your possessions. You're carrying a loaf of bread, a mug of ale, and 20 gold coins."

### Example 2: Ambiguous Input Clarification
**User Input:** "What can I do here?"  
**LLM Processing:** Identifies request for guidance  
**LLM Response:** "You're standing in the common room of The Rusted Tankard tavern. You could talk to the bartender or other patrons, order a drink, find work, or rent a room for the night. There's also a notice board on the wall that might have interesting opportunities. What would you like to do?"

### Example 3: Complex Action Interpretation
**User Input:** "I'd like to buy a round for everyone and see if I can get some information about the strange noises people have been hearing"  
**LLM Processing:** Identifies multiple intents (buy drinks, gather information)  
**Game Commands:** "buy ale" followed by investigation logic  
**Final Response:** "You generously purchase drinks for the patrons nearby, who raise their mugs in thanks. As the ale flows, tongues loosen. The old man in the corner leans in and mentions that he's heard odd scratching sounds coming from the cellar at night. The barkeeper overhears and quickly changes the subject."

## Implementation Phases and Timeline

### Immediate (1-2 days)
- Set up basic LLM API integration
- Create initial system prompts
- Implement conversation history tracking

### Short-term (3-5 days)
- Build command extraction logic
- Implement context building functions
- Create user interface adaptations

### Medium-term (1-2 weeks)
- Develop NPC personality profiles for LLM
- Add narrative enrichment
- Implement guidance system

### Long-term (3-4 weeks)
- Fine-tune the LLM with game-specific data
- Create advanced world-building elements
- Implement multimodal responses (text + simple visuals)

## Technical Requirements
- Claude API access (preferably Claude 3 Opus or Sonnet)
- API integration library
- Conversation history database
- Response templating system
- Enhanced game state monitoring