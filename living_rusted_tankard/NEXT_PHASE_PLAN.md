# Next Development Phase Plan

## Current Status: Integration 90% Complete ✅

**Poetry Environment**: ✅ Working with all dependencies  
**Phase 2 (World)**: ✅ Fully integrated and functional  
**Phase 3 (NPCs)**: ⚠️ 90% complete, minor fixes needed  
**Phase 4 (Narrative)**: ⚠️ Ready for testing  

## Phase A: Integration Completion & Testing (IMMEDIATE - 1-2 weeks)

### A1: Fix Remaining Integration Issues (Days 1-2)
**Status**: In Progress
**Tasks**:
- [ ] Fix GoalType enum mismatches in goals.py
- [ ] Fix NPC validation errors (definition_id, npc_type requirements)  
- [ ] Test Phase 4 narrative engine initialization
- [ ] Verify all method signatures match usage

**Commands to Run**:
```bash
cd /Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard
poetry shell
python test_integration_simple.py  # Should pass all checks
```

### A2: AI Player Testing (Days 3-4)
**Status**: Ready for testing
**Tasks**:
- [ ] Test AI player with full integrated systems
- [ ] Fix GitHub Issue #3 (AI Observer 500 error)
- [ ] Verify dynamic NPC dialogue works
- [ ] Test atmospheric room descriptions

**Commands to Run**:
```bash
poetry run python simple_ai_demo.py
poetry run python ai-observer-global.sh
python main.py  # Manual testing
```

### A3: Quality Assurance (Days 5-7)
**Status**: Planned
**Tasks**:
- [ ] Run comprehensive test suite
- [ ] Performance testing with all systems
- [ ] Memory leak detection
- [ ] Document any remaining issues

## Phase B: Weather & Dynamic Environment (2-4 weeks)

### B1: Weather System Implementation
**Align with**: DEVELOPMENT_SPRINT_TRACKER.md Sprint 3-4
**Dependencies**: Phase A complete

**Tasks**:
- [ ] Implement core weather system
- [ ] Weather affects atmosphere (connect to existing AtmosphereManager)
- [ ] NPCs react to weather changes (connect to existing psychology system)
- [ ] Seasonal patterns and transitions

**Files to Create/Modify**:
- `core/world/weather.py` - Weather system
- `core/world/seasons.py` - Seasonal changes
- Enhance `core/world/atmosphere.py` - Weather-atmosphere connection
- Enhance `core/npc_systems/psychology.py` - Weather mood effects

### B2: Enhanced Audio Integration
**Dependencies**: Weather system

**Tasks**:
- [ ] Ambient weather sounds
- [ ] Atmospheric audio based on room + weather
- [ ] NPC sound cues during interactions
- [ ] Audio system connected to narrative tension

### B3: Dynamic Environment Effects
**Dependencies**: Audio system

**Tasks**:
- [ ] Time-based lighting changes (morning/evening/night)
- [ ] Weather-responsive room descriptions
- [ ] Seasonal tavern decorations
- [ ] Environmental storytelling through descriptions

## Phase C: Living NPCs & Social Dynamics (3-5 weeks)

### C1: NPC Activity System
**Build on**: Existing NPC psychology and schedules

**Tasks**:
- [ ] Visible NPC activities (cooking, cleaning, drinking)
- [ ] Schedule-based NPC movement between rooms
- [ ] Contextual behaviors based on mood/weather/time
- [ ] Player-observable NPC routines

### C2: Inter-NPC Social Network
**Build on**: Existing relationship system and gossip network

**Tasks**:
- [ ] NPCs talking to each other (observable conversations)
- [ ] Relationship changes over time based on interactions
- [ ] Group conversations player can join/observe
- [ ] Social events and gatherings

### C3: Advanced Psychology Integration
**Build on**: Existing NPCPsychologyManager

**Tasks**:
- [ ] NPCs remember previous conversations with player
- [ ] Mood changes affect ALL interactions (not just with player)
- [ ] Gossip spreads and affects NPC behaviors
- [ ] Emotional contagion between NPCs

## Phase D: Investigation & Mystery Gameplay (4-6 weeks)

### D1: Clue Discovery Framework
**Build on**: Existing secrets system

**Tasks**:
- [ ] Enhanced room searching mechanics
- [ ] Evidence collection and inventory
- [ ] Clue correlation and pattern recognition
- [ ] Investigation journal system

### D2: Mystery Quest System
**Build on**: Existing narrative engine

**Tasks**:
- [ ] Multi-step investigation quests
- [ ] Red herrings and false leads
- [ ] Player deduction challenges
- [ ] Multiple solution paths

### D3: Advanced Narrative Branching
**Build on**: Existing story thread system

**Tasks**:
- [ ] Player choice consequences affecting story threads
- [ ] Multiple simultaneous mystery types
- [ ] Investigation results affecting NPC relationships
- [ ] Reputation-based mystery access

## Development Priorities

### Priority 1: Complete Integration (This Week)
- Fix remaining Phase 3/4 issues
- Get AI player working with full systems
- Test all integrated features

### Priority 2: Weather System (Next 2-4 weeks)  
- Aligns with official roadmap Sprint 3-4
- Builds on existing atmosphere system
- Natural progression from current work

### Priority 3: Social Dynamics (Following month)
- Makes tavern feel truly alive
- Shows off integrated psychology system
- High player engagement value

### Priority 4: Investigation System (2-3 months out)
- Complex gameplay addition
- Requires stable foundation
- High development effort but high reward

## Success Metrics

### Phase A Success:
- [ ] `test_integration_simple.py` passes completely
- [ ] AI player runs without errors
- [ ] NPCs show dynamic dialogue
- [ ] Room descriptions include atmosphere
- [ ] Story threads advance based on actions

### Phase B Success:
- [ ] Weather changes affect NPC moods
- [ ] Room descriptions vary by weather
- [ ] Audio enhances atmosphere
- [ ] Seasonal events occur

### Phase C Success:
- [ ] NPCs perform visible activities
- [ ] NPCs talk to each other
- [ ] Social dynamics observable by player
- [ ] Gossip spreads realistically

### Phase D Success:
- [ ] Players can solve mysteries through investigation
- [ ] Multiple investigation types available
- [ ] Investigation affects story and relationships
- [ ] Replay value through different solutions

## Technical Notes

### Current Architecture Strengths:
- Event-driven system ready for complex interactions
- Phase systems properly separated and integrated
- Psychology system ready for expansion
- Narrative engine capable of complex storytelling

### Areas for Optimization:
- Performance testing with many NPCs
- Memory management for long sessions
- Save/load compatibility with new features
- Mobile/web interface considerations

This plan builds systematically on the current 90% integrated foundation while aligning with the existing project roadmap and documentation.