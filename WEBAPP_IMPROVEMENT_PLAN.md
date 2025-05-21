# Web Interface & API Improvement Plan

## Overview
This document outlines the plan to improve the Taverna (The Living Rusted Tankard) web interface and API, focusing on pre-alpha priorities. The goal is to create a functional, unified web experience that properly integrates with the core game mechanics.

## Phase 1: Framework Consolidation and Integration ✅
- [x] Identify existing web implementations (FastAPI and Flask)
- [x] Select FastAPI as the primary framework (already more complete)
- [x] Remove Flask implementation
- [x] Serve HTML template directly from FastAPI
- [x] Update FastAPI CORS settings for local development

## Phase 2: Connect Web UI to Game Engine ✅
- [x] Modify game.html to work with FastAPI endpoints
- [x] Update JavaScript to use proper session management
- [x] Create a consistent API response format
- [x] Connect command input to the actual game processing
- [x] Set up game state synchronization

## Phase 3: Basic Session Management ✅
- [x] Add session timeout (30 minutes of inactivity)
- [x] Implement session cleanup to prevent memory leaks
- [x] Add session listing endpoint for debugging
- [x] Create endpoint to reset/restart a game session

## Phase 4: Improve Error Handling ✅
- [x] Add more detailed error responses in API
- [x] Implement proper validation for all inputs
- [x] Display errors appropriately in the web UI
- [x] Add request/response logging for debugging

## Phase 5: Essential UI Improvements ✅
- [x] Update UI to use real game state data
- [x] Add command history (up/down arrow navigation)
- [x] Implement loading states during command processing
- [x] Improve display of game events/messages
- [x] Fix responsive layout issues

## Phase 6: Additional Game Integration
- [ ] Add proper display for NPCs and locations
- [ ] Implement game state persistence (saving/loading)
- [ ] Add help panel showing available commands
- [ ] Create simple visualizations for important game elements

## Phase 7: Testing and Stabilization
- [ ] Comprehensive testing of all API endpoints
- [ ] Browser compatibility testing
- [ ] Fix any identified UX issues
- [ ] Optimize performance for slower connections

## Implementation Priority
1. Consolidate frameworks and connect UI (Phases 1-2)
2. Implement basic session management (Phase 3)
3. Improve error handling (Phase 4)
4. Enhance UI essentials (Phase 5)
5. Integrate remaining game features (Phase 6)
6. Testing and refinement (Phase 7)

**Note:** This plan focuses on making the web interface functional and stable before adding more advanced features like multiplayer, mod support, or advanced visualizations.

## Execution Timeline
- Phases 1-2: Immediate priority (1-2 days)
- Phases 3-4: Secondary priority (2-3 days)
- Phases 5-6: Follow-up priority (3-5 days)
- Phase 7: Final pre-release priority (1-2 days)

Total estimated time: ~10 days of focused work to reach a functional pre-alpha web interface.