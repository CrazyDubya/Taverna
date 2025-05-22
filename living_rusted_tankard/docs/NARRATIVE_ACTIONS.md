# Narrative Action System

The Narrative Action System bridges the gap between story choices and game mechanics in The Living Rusted Tankard. This system allows LLM-generated narrative responses to trigger real mechanical changes in the game world.

## Overview

When players make choices through conversation options or natural language commands, the LLM generates narrative responses. These responses can contain embedded action tags that trigger specific game mechanics:

- Purchase items and affect gold/inventory
- Start, progress, or complete quests
- Modify NPC relationships and reputation
- Change NPC moods and behaviors
- Trigger world events
- Execute complex command sequences

## Action Types

### COMMAND Actions
Execute standard game commands embedded in narrative responses.

```
[COMMAND:buy old_toms_surprise]
[COMMAND:inventory]
[COMMAND:status]
```

### Quest Management
Dynamically manage quest progression through story choices.

```
[QUEST_START:find_the_missing_key]
[QUEST_PROGRESS:find_the_missing_key talked_to_bartender]
[QUEST_COMPLETE:find_the_missing_key]
```

### NPC Relationships
Track and modify how NPCs perceive and interact with the player.

```
[REPUTATION:barkeep +1]
[REPUTATION:mysterious_stranger -2]
[NPC_MOOD:barkeep happy]
[NPC_MOOD:old_tom suspicious]
```

### Item Management
Add items to player inventory through narrative events.

```
[ITEM_GIVE:mysterious_key]
[ITEM_GIVE:old_toms_surprise]
[ITEM_GIVE:ancient_coin]
```

### World Events
Trigger larger changes to the game world and environment.

```
[EVENT_TRIGGER:tavern_celebration]
[EVENT_TRIGGER:mysterious_visitor_arrives]
```

## How It Works

### 1. LLM Response Generation
The Game Master generates narrative responses to player actions, embedding action tags where appropriate.

### 2. Action Extraction
The `NarrativeActionProcessor` scans the response text for embedded action tags using regex patterns.

### 3. Action Processing
Each extracted action is processed according to its type:
- Commands are executed via the game's command system
- Quest actions update the quest state
- Reputation changes are applied to NPC relationships
- Items are added to player inventory
- Events trigger world state changes

### 4. Text Cleaning
Action tags are removed from the final narrative text shown to the player, leaving only the story content.

## Implementation Details

### Core Components

**NarrativeActionProcessor** (`core/narrative_actions.py`)
- Handles action extraction, processing, and text cleaning
- Manages different action types through dedicated methods
- Integrates with existing game systems

**LLMGameMaster Integration** (`core/llm_game_master.py`)
- Processes narrative actions after LLM response generation
- Returns both cleaned narrative text and action results
- Maintains story flow while triggering mechanics

### Action Processing Flow

1. **Extract**: Find all `[ACTION_TYPE:parameters]` patterns in LLM response
2. **Validate**: Ensure action types are recognized and parameters are valid
3. **Execute**: Process each action according to its type
4. **Track**: Record action results for debugging and player feedback
5. **Clean**: Remove action tags from final narrative text

### Error Handling

- Invalid action types are logged but don't break the narrative flow
- Failed actions (e.g., insufficient gold) are recorded with error messages
- Players see natural narrative responses even when mechanics fail

## Usage Examples

### Purchase Integration
```
LLM Response: "You hand over 3 gold coins to Old Tom, who slides the mysterious concoction across the bar with a knowing wink. [COMMAND:buy old_toms_surprise]"

Result: 
- Player gold decreases by 3
- "Old Tom's Surprise" added to inventory
- Player sees: "You hand over 3 gold coins to Old Tom, who slides the mysterious concoction across the bar with a knowing wink."
```

### Quest Progression
```
LLM Response: "The bartender nods thoughtfully at your question about the missing key. 'Aye, I've heard whispers,' he says. 'Check with Old Tom - he knows more than he lets on.' [QUEST_PROGRESS:find_the_missing_key talked_to_bartender]"

Result:
- Quest "find_the_missing_key" progress updated
- New quest objective: "talked_to_bartender"
- Player sees natural dialogue without mechanical notation
```

### Reputation Changes
```
LLM Response: "Your generous tip brings a genuine smile to the bartender's weathered face. 'Much obliged, friend,' he says warmly. [REPUTATION:barkeep +1]"

Result:
- Bartender's opinion of player improves
- Future interactions may be more friendly
- Player sees emotional narrative response
```

## Configuration

### System Prompt Integration
The LLM is instructed to use action tags when narrative choices should have mechanical consequences:

```
When player choices should affect game mechanics, embed action tags in your response:
- [COMMAND:action] for game commands
- [QUEST_START:quest_id] for new quests
- [REPUTATION:npc_id +/-value] for relationship changes
- [ITEM_GIVE:item_id] for rewards
```

### Action Tag Format
All action tags follow the pattern: `[ACTION_TYPE:parameters]`
- Case-insensitive action types
- Parameters separated by spaces
- Multiple actions supported in single response

## Benefits

### For Players
- Story choices have real mechanical consequences
- Seamless integration between narrative and gameplay
- Enhanced immersion through meaningful decisions

### For Game Masters (LLM)
- Clear framework for triggering game mechanics
- Flexible system supporting various action types
- Maintains narrative flow while enabling complex interactions

### For Developers
- Extensible action system for new mechanics
- Clean separation between narrative and mechanical concerns
- Comprehensive logging and debugging support

## Future Enhancements

- **Conditional Actions**: Actions that only trigger under specific conditions
- **Delayed Actions**: Actions that execute after a time delay
- **Compound Actions**: Complex multi-step action sequences
- **Player Feedback**: Optional mechanical feedback for triggered actions
- **Action History**: Tracking of all actions for replay and analysis

## Testing

The narrative action system includes comprehensive tests covering:
- Action extraction and parsing
- Individual action type processing
- Integration with game systems
- Error handling and edge cases
- Text cleaning and formatting

Run tests with:
```bash
pytest tests/test_narrative_actions.py -v
```