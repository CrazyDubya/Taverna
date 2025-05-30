# Missing Test Coverage Analysis

## 1. Core Modules with NO Test Files

### Critical Systems Missing Tests:
- **error_recovery.py** - No tests found for error recovery mechanisms
- **fantasy_calendar.py** - No tests for fantasy calendar system
- **callable_registry.py** - No tests for callable registry
- **api.py** - No tests for core API module
- **audio_system.py** - No tests for audio system
- **economy_balancing.py** - No tests for economy balancing
- **memory.py** - No tests for memory system
- **news_manager.py** - No tests for news manager
- **npc_loader.py** - No tests for NPC loader
- **reputation.py** - No tests for reputation system
- **time_display.py** - No tests for time display utilities
- **performance_api_integration.py** - No tests
- **performance_optimizations.py** - No tests
- **ux_api_integration.py** - No tests
- **narrative_actions.py** - No tests for narrative actions
- **llm_game_master.py** - No tests (only enhanced version tested)

### Database Layer:
- **db/session.py** - No dedicated tests for database session management

### Services:
- **services/session_service.py** - No tests for session service

### Models:
- **models/persistence_models.py** - No tests for persistence models

## 2. Core Modules with Partial Test Coverage

### Partially Tested:
- **clock.py** - Imported in some tests but no dedicated test_clock.py
- **event_bus.py** - Used in tests but no dedicated test file
- **room.py** - Has test_room_manager.py but may need more comprehensive tests
- **event.py** - Used in various tests but no dedicated test_event.py
- **bounties.py** - Used in test_core_mechanics.py but could use dedicated tests
- **economy.py** - Has test_economy.py but may need more scenarios

### LLM Subsystem:
- **async_llm_optimization.py** - No tests
- **async_llm_pipeline.py** - Has test_integration_llm_pipeline.py but could use unit tests
- **llm/narrative_decorators.py** - No dedicated tests
- **llm/ollama_client.py** - Used in tests but no dedicated test file

## 3. Critical Systems Needing Comprehensive Testing

### High Priority:
1. **error_recovery.py** - Critical for game stability
2. **event_bus.py** - Central to game event system
3. **clock.py** - Core time management system
4. **fantasy_calendar.py** - Game world time system
5. **memory.py** - Player/NPC memory management
6. **reputation.py** - Player reputation tracking

### Medium Priority:
1. **callable_registry.py** - Command registration system
2. **audio_system.py** - Audio feedback system
3. **news_manager.py** - Dynamic news generation
4. **time_display.py** - Time formatting utilities
5. **narrative_actions.py** - Narrative action system

### Database/Persistence:
1. **db/session.py** - Database session management
2. **models/persistence_models.py** - Data persistence models
3. **services/session_service.py** - Session management service

## Recommendations

1. Create dedicated test files for all critical systems
2. Ensure each core module has at least 80% test coverage
3. Add integration tests for systems that work together (e.g., clock + fantasy_calendar)
4. Create test fixtures for commonly used objects
5. Add performance tests for optimization modules