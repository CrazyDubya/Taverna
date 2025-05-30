# Quality Improvement Plan for The Living Rusted Tankard

## Executive Summary

This plan outlines a systematic approach to improve code quality, test coverage, and overall robustness of The Living Rusted Tankard project. The goal is to ensure functional, maintainable code through rigorous testing and iterative improvement, with a commitment to never reward hacks or bypass proper validation.

## Current State Analysis

### Strengths
- Well-structured modular architecture
- Comprehensive type hints throughout
- Good separation of concerns
- Extensive documentation
- Solid foundation for core game mechanics

### Critical Issues Identified

#### 1. **Test Coverage Gaps**
**Missing Tests for Critical Systems:**
- AI Player system (completely untested)
- API layer (no endpoint tests)
- Error recovery system (no tests)
- Memory management (no tests)
- Performance optimizations (no verification)
- Database/session management (no tests)
- Audio, bounties, reputation systems (no tests)

#### 2. **Code Quality Issues**
- **Global State**: AI player uses global instance (`_ai_player`)
- **Thread Safety**: Async LLM pipeline lacks proper synchronization
- **Resource Leaks**: HTTP streaming without cleanup
- **Complex Functions**: `GameState.process_command()` handles too many cases
- **Error Handling**: Generic `except:` clauses without proper logging
- **Hardcoded Values**: Magic numbers throughout (cooldowns, limits)
- **Two-Step Commands**: Hacky implementation for rent confirmation

#### 3. **Test Quality Problems**
- Over-reliance on mocking
- Tests that always pass (checking for substring in error)
- Fixed random seeds hiding edge cases
- No integration or end-to-end tests
- No performance regression tests

## Implementation Plan

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Establish testing infrastructure and fix critical issues

#### 1.1 Testing Infrastructure
```python
# Create test framework standards
tests/
├── unit/           # Isolated component tests
├── integration/    # Component interaction tests
├── e2e/           # End-to-end gameplay tests
├── performance/   # Performance regression tests
└── fixtures/      # Shared test data
```

**Actions:**
1. Create `tests/conftest.py` with proper fixtures
2. Implement test database isolation
3. Create gameplay scenario builders
4. Add performance benchmarking framework

#### 1.2 Fix Critical Issues
1. **Remove Global State**
   ```python
   # Bad (current)
   _ai_player = None
   
   # Good (target)
   class AIPlayerManager:
       def __init__(self):
           self._players: Dict[str, AIPlayer] = {}
   ```

2. **Add Thread Safety**
   ```python
   # Add proper locking to async_llm_pipeline.py
   import threading
   
   class AsyncLLMPipeline:
       def __init__(self):
           self._lock = threading.RLock()
           self.active_requests: Dict[str, LLMRequest] = {}
       
       def add_request(self, request_id: str, request: LLMRequest):
           with self._lock:
               self.active_requests[request_id] = request
   ```

3. **Resource Cleanup**
   ```python
   # Implement context managers for resources
   class AIPlayerSession:
       async def __aenter__(self):
           self.session = aiohttp.ClientSession()
           return self
       
       async def __aexit__(self, exc_type, exc_val, exc_tb):
           await self.session.close()
   ```

### Phase 2: Test Coverage (Weeks 3-4)
**Goal**: Achieve 80%+ test coverage for critical systems

#### 2.1 Unit Test Implementation

**AI Player Tests** (`tests/unit/test_ai_player.py`):
```python
class TestAIPlayer:
    def test_personality_affects_commands(self):
        # Test each personality generates appropriate commands
        
    def test_action_history_limits(self):
        # Verify history doesn't grow unbounded
        
    def test_error_handling(self):
        # Test graceful fallbacks when LLM fails
        
    @pytest.mark.asyncio
    async def test_streaming_generation(self):
        # Test real streaming behavior
```

**API Tests** (`tests/unit/test_api.py`):
```python
class TestGameAPI:
    def test_command_endpoint_validation(self):
        # Test input validation
        
    def test_session_isolation(self):
        # Verify sessions don't interfere
        
    def test_concurrent_requests(self):
        # Test thread safety
        
    def test_error_responses(self):
        # Verify proper error codes
```

**Error Recovery Tests** (`tests/unit/test_error_recovery.py`):
```python
class TestErrorRecovery:
    def test_llm_failure_fallback(self):
        # Test graceful degradation
        
    def test_database_error_recovery(self):
        # Test transaction rollback
        
    def test_memory_pressure_handling(self):
        # Test behavior under memory constraints
```

#### 2.2 Integration Tests

**Game Flow Tests** (`tests/integration/test_game_flow.py`):
```python
class TestGameFlow:
    def test_complete_quest_flow(self):
        """Test accepting, progressing, and completing a quest"""
        # No mocking - use real components
        
    def test_economy_interaction(self):
        """Test jobs -> gold -> purchases flow"""
        
    def test_npc_relationship_progression(self):
        """Test building relationships over time"""
```

#### 2.3 End-to-End Tests

**Gameplay Scenarios** (`tests/e2e/test_scenarios.py`):
```python
class TestGameplayScenarios:
    @pytest.mark.slow
    def test_new_player_first_hour(self):
        """Simulate typical first hour of gameplay"""
        
    def test_economic_progression(self):
        """Test player can progress economically"""
        
    def test_quest_completion_paths(self):
        """Test all quest paths are completable"""
```

### Phase 3: Code Quality Improvements (Weeks 5-6)
**Goal**: Refactor problematic code patterns

#### 3.1 Refactor Complex Functions

**Split `process_command()`**:
```python
class CommandProcessor:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.handlers = {
            'rent': RentCommandHandler(),
            'store': StorageCommandHandler(),
            'interact': InteractionHandler(),
            # ... etc
        }
    
    def process(self, command: str) -> CommandResult:
        parsed = self.parse_command(command)
        handler = self.handlers.get(parsed.command)
        if handler:
            return handler.execute(self.game_state, parsed)
        return self.handle_unknown(parsed)
```

#### 3.2 Extract Configuration

**Create `config.py`**:
```python
from dataclasses import dataclass

@dataclass
class GameConfig:
    # Economy
    STARTING_GOLD: int = 20
    JOB_COOLDOWN: int = 10
    ROOM_RENT_COST: int = 10
    CHEST_COST: int = 5
    
    # NPCs
    NPC_UPDATE_INTERVAL: float = 0.1
    MAX_RELATIONSHIP: float = 1.0
    MIN_RELATIONSHIP: float = -1.0
    
    # Performance
    CACHE_TTL: float = 1.0
    MAX_EVENTS: int = 100
    
    @classmethod
    def from_env(cls) -> 'GameConfig':
        """Load config from environment"""
        return cls()
```

#### 3.3 Improve Error Handling

**Structured Error Types**:
```python
class GameError(Exception):
    """Base game error"""
    pass

class InvalidCommandError(GameError):
    """Invalid command syntax"""
    pass

class InsufficientResourcesError(GameError):
    """Not enough gold/items"""
    pass

class NPCNotPresentError(GameError):
    """NPC not in location"""
    pass

# Use specific errors
def perform_job(self, job_id: str, player: Player) -> JobResult:
    if player.gold < job.cost:
        raise InsufficientResourcesError(
            f"Need {job.cost} gold, have {player.gold}"
        )
```

### Phase 4: Performance Testing (Weeks 7-8)
**Goal**: Ensure optimizations actually work

#### 4.1 Performance Test Suite

**Benchmark Tests** (`tests/performance/test_benchmarks.py`):
```python
class TestPerformance:
    @pytest.mark.benchmark
    def test_npc_lookup_performance(self, benchmark):
        """Verify O(1) NPC lookups"""
        game_state = create_large_game_state(npcs=100)
        
        def lookup_npcs():
            for _ in range(1000):
                game_state.is_npc_present("test_npc")
        
        result = benchmark(lookup_npcs)
        assert result.stats['mean'] < 0.001  # < 1ms average
    
    @pytest.mark.benchmark
    def test_snapshot_creation_performance(self, benchmark):
        """Verify snapshot caching works"""
        game_state = create_complex_game_state()
        
        result = benchmark(game_state.get_snapshot)
        assert result.stats['mean'] < 0.01  # < 10ms
```

#### 4.2 Load Testing

**Concurrent Session Tests** (`tests/performance/test_load.py`):
```python
class TestLoad:
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self):
        """Test 10+ concurrent game sessions"""
        sessions = []
        for i in range(10):
            session = await create_session(f"player_{i}")
            sessions.append(session)
        
        # Run commands concurrently
        tasks = []
        for session in sessions:
            task = run_game_commands(session, 100)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Verify no cross-contamination
        for i, result in enumerate(results):
            assert result.player_id == f"player_{i}"
```

### Phase 5: Continuous Quality (Ongoing)
**Goal**: Maintain quality through automation

#### 5.1 CI/CD Pipeline

**`.github/workflows/quality.yml`**:
```yaml
name: Quality Checks

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run Unit Tests
        run: pytest tests/unit -v --cov=living_rusted_tankard
      
      - name: Run Integration Tests
        run: pytest tests/integration -v
      
      - name: Check Coverage
        run: |
          coverage report --fail-under=80
      
      - name: Type Checking
        run: mypy living_rusted_tankard --strict
      
      - name: Linting
        run: |
          flake8 living_rusted_tankard
          black --check living_rusted_tankard
      
      - name: Security Scan
        run: bandit -r living_rusted_tankard
```

#### 5.2 Quality Metrics Dashboard

**Track Key Metrics**:
- Test coverage percentage
- Code complexity (cyclomatic complexity)
- Technical debt (TODO/FIXME count)
- Performance regression alerts
- Error rates in production

## Success Criteria

### Immediate (Phase 1-2)
- ✅ No global state in codebase
- ✅ Thread-safe async operations
- ✅ 80%+ test coverage for critical systems
- ✅ No "auto-passing" tests

### Short-term (Phase 3-4)
- ✅ All functions < 50 lines (single responsibility)
- ✅ Configuration extracted from code
- ✅ Structured error handling throughout
- ✅ Performance tests prevent regression

### Long-term (Phase 5+)
- ✅ 90%+ overall test coverage
- ✅ Automated quality gates in CI/CD
- ✅ Zero critical security vulnerabilities
- ✅ Load testing proves 100+ session capability

## Anti-Patterns to Avoid

### Never Do This:
1. **Skip Tests for Expedience**
   ```python
   # NEVER
   @pytest.mark.skip("Broken, fix later")
   def test_critical_feature():
       pass
   ```

2. **Mock Away Behavior**
   ```python
   # NEVER
   def test_ai_player():
       mock_llm = Mock(return_value="success")
       # Not testing actual behavior!
   ```

3. **Ignore Failing Tests**
   ```python
   # NEVER
   try:
       assert complex_operation()
   except:
       pass  # "It's flaky"
   ```

4. **Hardcode Test Data**
   ```python
   # NEVER
   def test_random_event():
       random.seed(42)  # Always same result
       assert event_occurs()
   ```

## Implementation Timeline

### Week 1-2: Foundation
- Set up test infrastructure
- Fix critical issues (global state, thread safety)
- Create first integration tests

### Week 3-4: Test Coverage
- Implement unit tests for uncovered systems
- Add integration test suite
- Create first E2E tests

### Week 5-6: Code Quality
- Refactor complex functions
- Extract configuration
- Improve error handling

### Week 7-8: Performance
- Implement performance test suite
- Add load testing
- Verify optimizations

### Ongoing: Continuous Quality
- Set up CI/CD pipeline
- Monitor quality metrics
- Regular refactoring sprints

## Commitment Statement

We commit to:
1. **Never bypassing tests** - If it doesn't pass, it doesn't ship
2. **Never simplifying for false success** - Tests must reflect real usage
3. **Always testing edge cases** - Happy path isn't enough
4. **Maintaining test quality** - Tests are code too
5. **Iterative improvement** - Small, tested changes over big rewrites

This plan ensures The Living Rusted Tankard achieves its goal of being a robust, well-tested game that provides a reliable and enjoyable experience for players while maintaining code quality for developers.