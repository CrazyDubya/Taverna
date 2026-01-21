# GameState Refactoring Plan

## Current State
- Single file: `core/game_state.py` (3,016 lines)
- 88 methods in one monolithic GameState class
- Multiple concerns mixed: player, world, NPCs, events, persistence

## Target Structure

```
core/game_state/
├── __init__.py         # Main GameState class + public API
├── player_manager.py   # Player state, inventory, items
├── world_manager.py    # World state, atmosphere, areas
├── npc_manager.py      # NPC tracking, spawning, interactions
├── event_manager.py    # Event processing, observers, updates
├── persistence.py      # Database, caching, snapshots
└── README.md           # This file
```

## Method Distribution Analysis

### Player-related (6 methods → player_manager.py)
- `_update_player_status()`
- `_handle_inventory()`
- `_handle_buy()`
- `_handle_use()`
- `_handle_store_item()`
- `_handle_retrieve_item()`

### NPC-related (12 methods → npc_manager.py)
- `_update_present_npcs()`
- `_add_npc_to_room()`
- `_remove_npc_from_room()`
- `_setup_npc_event_handlers()`
- `handle_npc_spawn()`
- `handle_npc_depart()`
- `handle_npc_interaction()`
- `interact_with_npc()`
- `get_interactive_npcs()`
- `_check_bounty_objective_report_to_npc()`
- `get_present_npcs_optimized()`
- `_invalidate_npc_cache()`

### Event/Update-related (15+ methods → event_manager.py)
- `_add_event()`
- `_setup_event_handlers()`
- `_handle_time_based_events()`
- `add_observer()`
- `_notify_observers()`
- `dispatch()`
- `update()`
- `_update_narrative_systems()`
- `_update_phase_systems()`
- `_update_travelling_merchant_event()`
- All command handlers

### World-related (→ world_manager.py)
- Phase 2 system integration
- Atmosphere management
- Area management
- Floor management

### Persistence-related (→ persistence.py)
- Database operations
- Caching logic
- Snapshot management
- Performance optimizations

## Implementation Strategy

### Phase 1: Create manager classes (Week 1)
1. Create empty manager classes with __init__
2. Move related state variables to each manager
3. Keep all logic in original file

### Phase 2: Extract methods incrementally (Week 2)
1. Move one manager's methods at a time
2. Test after each move
3. Update imports progressively

### Phase 3: Refactor GameState to orchestrator (Week 3)
1. GameState becomes coordination layer
2. Delegates to managers
3. Maintains backward compatibility

### Phase 4: Clean up and optimize (Week 4)
1. Remove duplication
2. Optimize interfaces
3. Update documentation

## Success Criteria
- ✅ All files < 800 lines
- ✅ Clear separation of concerns
- ✅ All tests passing
- ✅ No breaking changes to public API
- ✅ Improved maintainability

## Status
- **Phase 1**: Not started
- **Current**: Planning complete
- **Next**: Create manager skeletons
