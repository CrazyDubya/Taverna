# Functional Testing Checklist for The Living Rusted Tankard

## Core Gameplay Functions

### Player Actions
- [ ] **Movement & Exploration**
  - [ ] Player can look around and see room description
  - [ ] Player can see present NPCs
  - [ ] Player can check inventory
  - [ ] Player can check status (gold, tiredness, etc.)

- [ ] **Economic Actions**
  - [ ] Player can work all job types
  - [ ] Jobs have proper cooldowns
  - [ ] Jobs consume correct energy/tiredness
  - [ ] Jobs reward appropriate gold
  - [ ] Player can buy items from merchants
  - [ ] Player can sell items to merchants
  - [ ] Dynamic pricing works correctly

- [ ] **Gambling**
  - [ ] All three gambling games work (dice, coin, cards)
  - [ ] Win/loss calculations are correct
  - [ ] Betting limits are enforced
  - [ ] Player can't bet more than they have

- [ ] **Room & Storage**
  - [ ] Player can rent a room
  - [ ] Two-step confirmation prevents accidental loss
  - [ ] Storage chest can be rented
  - [ ] Items can be stored and retrieved
  - [ ] Storage persists between room rentals

### NPC Interactions
- [ ] **Presence & Scheduling**
  - [ ] NPCs appear/leave according to schedule
  - [ ] Time-based presence updates work
  - [ ] NPCs have correct descriptions

- [ ] **Conversations**
  - [ ] Player can talk to present NPCs
  - [ ] Relationship affects available topics
  - [ ] NPCs share contextual news
  - [ ] Special interactions work (buy/sell/etc.)

- [ ] **Relationships**
  - [ ] Actions affect NPC relationships
  - [ ] Relationships persist between sessions
  - [ ] Relationship gates work properly

### Quest System
- [ ] **Bounty Board**
  - [ ] Player can read notice board
  - [ ] Available bounties display correctly
  - [ ] Player can accept bounties
  - [ ] Active bounties track properly

- [ ] **Quest Progression**
  - [ ] Objectives can be completed
  - [ ] Multi-stage quests advance properly
  - [ ] Rewards are granted correctly
  - [ ] Reputation changes apply

### Time & World
- [ ] **Time System**
  - [ ] Game time advances properly
  - [ ] Fantasy calendar displays correctly
  - [ ] Time affects NPC schedules
  - [ ] Sleep advances time appropriately

- [ ] **World Events**
  - [ ] Economic events trigger
  - [ ] Events affect prices/availability
  - [ ] News system updates dynamically
  - [ ] Atmospheric messages appear

### Natural Language Processing
- [ ] **Command Parsing**
  - [ ] Natural language converts to commands
  - [ ] Common variations are understood
  - [ ] Fallback works when LLM unavailable
  - [ ] Context-aware responses

- [ ] **Narrative Generation**
  - [ ] Descriptions are dynamic
  - [ ] Narrative actions trigger mechanics
  - [ ] Memory system retains important events
  - [ ] Responses maintain consistency

### AI Player
- [ ] **Autonomous Behavior**
  - [ ] AI makes contextual decisions
  - [ ] Different personalities behave distinctly
  - [ ] AI avoids repetitive actions
  - [ ] AI responds to game state changes

- [ ] **Observer Mode**
  - [ ] Streaming shows AI thought process
  - [ ] Actions execute properly
  - [ ] Session management works
  - [ ] Multiple AI players can run

### Persistence
- [ ] **Save/Load**
  - [ ] Game state saves correctly
  - [ ] All data persists (inventory, relationships, etc.)
  - [ ] Loading restores exact state
  - [ ] No data corruption on save

- [ ] **Session Management**
  - [ ] Sessions are isolated
  - [ ] Concurrent sessions work
  - [ ] Session cleanup happens
  - [ ] No memory leaks

## Performance Requirements

### Response Times
- [ ] Command processing < 500ms (cached)
- [ ] Command processing < 2s (with LLM)
- [ ] Page load < 1s
- [ ] NPC updates < 100ms

### Scalability
- [ ] Supports 10+ concurrent sessions
- [ ] Memory usage stable over time
- [ ] Cache hit rates > 80%
- [ ] No performance degradation over long sessions

### Reliability
- [ ] Graceful LLM failure handling
- [ ] Database errors don't crash game
- [ ] Network issues handled properly
- [ ] Recovery from unexpected errors

## Integration Points

### Web Interface
- [ ] Commands submit properly
- [ ] Response displays correctly
- [ ] Auto-scroll works
- [ ] Mobile responsive
- [ ] Command history persists

### API Endpoints
- [ ] /command processes all commands
- [ ] /state returns current snapshot
- [ ] /health shows system status
- [ ] Error responses use proper codes
- [ ] CORS configured correctly

### Database
- [ ] Transactions complete properly
- [ ] No duplicate key errors
- [ ] Referential integrity maintained
- [ ] Migrations work (when added)

## Edge Cases

### Economic Edge Cases
- [ ] Working with 0 gold
- [ ] Buying with exact gold amount
- [ ] Selling last item
- [ ] Job cooldown at exactly 0

### Storage Edge Cases
- [ ] Storing in room without chest
- [ ] Retrieving non-existent items
- [ ] Storage when room expires
- [ ] Maximum storage limits

### NPC Edge Cases
- [ ] Talking to departing NPC
- [ ] All NPCs absent
- [ ] Maximum relationship values
- [ ] Concurrent NPC updates

### Time Edge Cases
- [ ] Day/month boundaries
- [ ] Sleeping at day change
- [ ] Events at time boundaries
- [ ] Schedule edge times

## Security Checks

### Input Validation
- [ ] Command injection prevented
- [ ] SQL injection prevented
- [ ] Path traversal blocked
- [ ] Buffer overflow protection

### Session Security
- [ ] Sessions properly isolated
- [ ] No session hijacking
- [ ] Secure session tokens
- [ ] Proper session expiry

### Resource Limits
- [ ] Memory usage capped
- [ ] CPU usage limited
- [ ] Storage quotas enforced
- [ ] Rate limiting implemented

## Negative Testing

### Invalid Inputs
- [ ] Empty commands handled
- [ ] Extremely long commands rejected
- [ ] Invalid characters filtered
- [ ] Null/undefined handled

### System Stress
- [ ] Rapid command spam handled
- [ ] Large save files work
- [ ] Many NPCs present
- [ ] Complex game states

### Failure Scenarios
- [ ] LLM service down
- [ ] Database unavailable
- [ ] Network timeout
- [ ] Disk full

## Regression Testing

### After Each Change
- [ ] Existing commands still work
- [ ] Save/load compatibility maintained
- [ ] Performance not degraded
- [ ] No new security issues

### Version Upgrades
- [ ] Migration from old saves
- [ ] API compatibility
- [ ] Configuration changes documented
- [ ] Breaking changes noted

## Test Automation Requirements

### Unit Tests Must
- [ ] Test actual behavior, not mocks
- [ ] Cover edge cases
- [ ] Use realistic data
- [ ] Run quickly (< 5 min total)

### Integration Tests Must
- [ ] Use real components
- [ ] Test component interactions
- [ ] Verify data flow
- [ ] Clean up after themselves

### E2E Tests Must
- [ ] Simulate real gameplay
- [ ] Test full user journeys
- [ ] Verify observable behavior
- [ ] Be maintainable

## Definition of "Functional"

A feature is considered functional when:
1. ✅ It works as designed in the happy path
2. ✅ It handles all documented edge cases
3. ✅ It fails gracefully with clear errors
4. ✅ It performs within requirements
5. ✅ It doesn't break existing features
6. ✅ It has comprehensive test coverage
7. ✅ It's secure against common attacks
8. ✅ It's maintainable and documented

## Testing Philosophy

### We Test Because
- Real players will find every edge case
- Complexity grows exponentially
- Refactoring requires confidence
- Quality is not negotiable

### We Never
- Skip tests to meet deadlines
- Disable failing tests
- Test only the happy path
- Mock away the complexity
- Accept "works on my machine"

### We Always
- Test the actual behavior
- Consider edge cases
- Verify error handling
- Measure performance impact
- Maintain test quality

This checklist ensures The Living Rusted Tankard delivers a robust, enjoyable experience that handles real-world usage gracefully.