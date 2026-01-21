# 📋 TODO List - Taverna Code Quality Improvements

**Generated**: 2026-01-21  
**Based on**: Comprehensive Code Review (COMPREHENSIVE_CODE_REVIEW.md)  
**Overall Status**: 81/100 (B+) → Target: 90/100 (A)  
**Timeline**: 4-6 developer-months

---

## 🔴 CRITICAL PRIORITY (P0) - Do First

### 1. Split Monolithic `game_state.py` 
**File**: `living_rusted_tankard/core/game_state.py` (3,017 lines)  
**Impact**: 🔴 CRITICAL | **Effort**: HIGH (2-3 weeks)

- [ ] Create new module structure:
  - [ ] `core/game_state/player_state.py` - Player data and inventory
  - [ ] `core/game_state/world_state.py` - World and location state
  - [ ] `core/game_state/npc_state.py` - NPC tracking and relationships
  - [ ] `core/game_state/event_state.py` - Events and quest state
  - [ ] `core/game_state/__init__.py` - Public API and backward compatibility
- [ ] Migrate class by class (don't break tests)
- [ ] Update all imports across codebase
- [ ] Run full test suite after each migration step
- [ ] Delete original `game_state.py` once verified

**Success Metric**: Largest file < 800 lines

---

### 2. Consolidate Duplicate NPC Modules
**Impact**: 🔴 CRITICAL | **Effort**: MEDIUM (1-2 weeks)  
**Duplication**: 6,100+ lines (~20% of codebase)

Currently duplicated:
- [ ] `goals.py` (956 lines × 2)
- [ ] `schedules.py` (867 lines × 2)
- [ ] `interactions.py` (669 lines × 2)
- [ ] `relationships.py` (626 lines × 2)
- [ ] `gossip.py` (638 lines × 2)

**Action Plan**:
- [ ] Decide on single location: `core/npc/` (recommended)
- [ ] Move files from `npc_modules/` to `core/npc/`
- [ ] Delete `npc_systems/` directory
- [ ] Update all imports (search for `from core.npc_systems` and `from core.npc_modules`)
- [ ] Run tests to verify no breakage
- [ ] Clean up any stale imports

**Success Metric**: Zero duplication between NPC modules

---

## 🟡 HIGH PRIORITY (P1) - Next Sprint

### 3. Reorganize Test Files
**Impact**: 🟡 HIGH | **Effort**: LOW (2-3 days)

- [ ] Move root-level test files to `tests/` directory:
  - [ ] `test_gambling.py`
  - [ ] `test_global_state_fix.py`
  - [ ] `test_imports.py`
  - [ ] `validate_fix.py`
  - [ ] `validate_resource_cleanup.py`
  - [ ] `validate_thread_safety.py`
  - [ ] All other `test_*.py` files in root
- [ ] Update test discovery paths in `pyproject.toml` if needed
- [ ] Verify CI/CD pipeline finds all tests
- [ ] Add `.gitignore` entries for test artifacts (if missing)

**Success Metric**: All tests in `tests/` directory, none in root

---

### 4. Increase Test Coverage
**Current**: 29% (18,597 / 64,191 lines) | **Target**: 50%+  
**Impact**: 🟡 HIGH | **Effort**: HIGH (3-4 weeks)

**Need to add**: ~13,500 lines of tests (~45 new test files)

Priority areas for new tests:
- [ ] **Core Systems** (10 files):
  - [ ] `core/game_state.py` - State management tests
  - [ ] `core/clock.py` - Time simulation tests
  - [ ] `core/api.py` - API endpoint tests
  - [ ] `core/async_llm_pipeline.py` - Async pipeline tests
- [ ] **Narrative Engine** (10 files):
  - [ ] `core/narrative/dynamic_quest_generator.py`
  - [ ] `core/narrative/consequence_engine.py`
  - [ ] `core/narrative/story_orchestrator.py`
  - [ ] `core/narrative/conversation_continuity.py`
- [ ] **NPC Systems** (10 files):
  - [ ] `core/npc_*/goals.py` - Goal system tests
  - [ ] `core/npc_*/schedules.py` - Schedule tests
  - [ ] `core/npc_*/interactions.py` - Interaction tests
- [ ] **World Systems** (5 files):
  - [ ] `core/world/area_manager.py`
- [ ] **Integration Tests** (10 files):
  - [ ] End-to-end gameplay scenarios
  - [ ] Multi-system integration tests

**Success Metric**: Test coverage ≥ 50% (32,000+ test lines)

---

### 5. Refactor Large Files
**Impact**: 🟡 MEDIUM | **Effort**: MEDIUM (2 weeks)

Files exceeding 600-line maintainability threshold (20+ files):

**Top 5 to refactor**:
- [ ] `core/npc_systems/goals.py` (956 lines) → Split into goal types
- [ ] `core/narrative/dynamic_quest_generator.py` (909 lines) → Separate quest templates
- [ ] `core/world/area_manager.py` (888 lines) → Extract area types
- [ ] `core/npc_systems/schedules.py` (867 lines) → Separate schedule logic
- [ ] `core/llm_game_master.py` (769 lines) → Extract prompt builders

**Success Metric**: Average file size < 400 lines, max file < 800 lines

---

## 🟢 MEDIUM PRIORITY (P2) - Future Sprints

### 6. Document Public APIs
**Impact**: 🟡 MEDIUM | **Effort**: MEDIUM (1 week)

- [ ] Add docstrings to all public classes (594 classes)
- [ ] Add docstrings to all public functions (2,780 functions)
- [ ] Generate API documentation:
  - [ ] Use Sphinx or MkDocs for Python docs
  - [ ] Generate OpenAPI docs for FastAPI endpoints
- [ ] Create architecture diagram (auto-generate from code)
- [ ] Add inline code examples in docstrings

**Success Metric**: 90%+ of public APIs documented

---

### 7. Set Up Code Quality Automation
**Impact**: 🟡 MEDIUM | **Effort**: LOW (2-3 days)

- [ ] Install and configure tools:
  - [ ] `black` - Auto-formatting (already in deps)
  - [ ] `isort` - Import sorting (already in deps)
  - [ ] `flake8` - Linting (already in deps)
  - [ ] `mypy` - Type checking (already in deps)
  - [ ] `pytest-cov` - Coverage reporting (already in deps)
- [ ] Set up pre-commit hooks (`.pre-commit-config.yaml`)
- [ ] Add GitHub Actions workflow for:
  - [ ] Linting on PR
  - [ ] Type checking on PR
  - [ ] Test coverage report on PR
- [ ] Configure coverage minimum threshold (start at 29%, increase to 50%)

**Success Metric**: All quality checks automated in CI/CD

---

### 8. Upgrade Pydantic to v2
**Impact**: 🟢 LOW | **Effort**: MEDIUM (1 week)

**Current**: Pydantic v1.10.13  
**Target**: Pydantic v2.x (breaking changes!)

- [ ] Research breaking changes in Pydantic v2
- [ ] Create migration plan for models
- [ ] Test with SQLModel compatibility
- [ ] Update all model definitions
- [ ] Update validation logic
- [ ] Run full test suite
- [ ] Update documentation

**Success Metric**: Using Pydantic v2 with all tests passing

---

## 🔵 LOW PRIORITY (P3) - Nice to Have

### 9. Performance Optimization
**Impact**: 🟢 LOW | **Effort**: MEDIUM (2 weeks)

- [ ] Set up performance profiling:
  - [ ] Install `py-spy` or `cProfile`
  - [ ] Profile LLM integration hot paths
  - [ ] Profile game loop performance
- [ ] Identify bottlenecks:
  - [ ] Database queries (use SQLAlchemy profiling)
  - [ ] LLM API calls (async optimization)
  - [ ] Game state updates
- [ ] Implement optimizations:
  - [ ] Cache frequently accessed data
  - [ ] Optimize database queries
  - [ ] Batch LLM requests where possible
- [ ] Add performance benchmarks to CI/CD

**Success Metric**: 20% improvement in response times

---

### 10. Reduce Technical Debt
**Current**: 43,500 lines (52%) | **Target**: < 30% (< 25,000 lines)

**Breakdown**:
- [ ] Architecture Debt: 16,000 lines → Addressed by items #1, #2, #5
- [ ] Testing Debt: 13,500 lines → Addressed by item #4
- [ ] Documentation Debt: 9,000 lines → Addressed by item #6
- [ ] Performance Debt: 5,000 lines → Addressed by item #9

**Success Metric**: Technical debt < 30% of codebase

---

## 📅 SPRINT PLANNING

### Sprint 1 (Weeks 1-2): Architecture Cleanup
**Goal**: Eliminate duplication and split monolithic files

- Week 1: Consolidate NPC modules (#2)
- Week 2: Start splitting `game_state.py` (#1, first 2 modules)

**Deliverables**:
- ✅ Zero NPC module duplication
- ✅ At least 2 new game_state sub-modules created

---

### Sprint 2 (Weeks 3-4): Continue Refactoring
**Goal**: Complete game_state split and organize tests

- Week 3: Finish splitting `game_state.py` (#1)
- Week 4: Reorganize test files (#3)

**Deliverables**:
- ✅ `game_state.py` split into 5 modules
- ✅ All tests in proper directory

---

### Sprint 3 (Weeks 5-8): Testing Enhancement
**Goal**: Increase test coverage significantly

- Weeks 5-8: Add 45 new test files (#4)
  - 10-12 files per week
  - Focus on high-priority modules first

**Deliverables**:
- ✅ Test coverage ≥ 40% (checkpoint)
- ✅ Core systems fully tested

---

### Sprint 4 (Weeks 9-12): Quality & Documentation
**Goal**: Polish and document

- Week 9-10: Refactor remaining large files (#5)
- Week 11: Set up automation (#7)
- Week 12: Document APIs (#6)

**Deliverables**:
- ✅ All files < 800 lines
- ✅ CI/CD quality checks enabled
- ✅ API docs generated

---

### Sprint 5+ (Weeks 13-24): Optimization & Debt Reduction
**Goal**: Performance and technical debt

- Weeks 13-16: Continue testing to reach 50% (#4)
- Weeks 17-20: Performance optimization (#9)
- Weeks 21-24: Pydantic v2 migration (#8)

**Deliverables**:
- ✅ Test coverage ≥ 50%
- ✅ Performance benchmarks established
- ✅ Pydantic v2 migration complete

---

## 🎯 SUCCESS CRITERIA

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Overall Code Quality | 81/100 (B+) | 90/100 (A) | 🔴 In Progress |
| Largest File Size | 3,017 lines | < 800 lines | 🔴 Needs Work |
| Code Duplication | 20% | 0% | 🔴 Needs Work |
| Test Coverage | 29% | 50%+ | 🟡 Improving |
| Technical Debt | 52% | < 30% | 🟡 Improving |
| Avg File Size | 297 lines | < 400 lines | 🟢 Good |

---

## 📊 PROGRESS TRACKING

**Current Sprint**: _Not Started_  
**Last Updated**: 2026-01-21  
**Next Review**: After Sprint 1 (Week 2)

### Completed Tasks
- [x] Comprehensive code review completed
- [x] TODO list created

### In Progress
- [ ] None yet - awaiting sprint kickoff

### Blocked
- [ ] None

---

## 📝 NOTES

- **Priority Order**: P0 (Critical) → P1 (High) → P2 (Medium) → P3 (Low)
- **Effort Scale**: LOW (< 1 week) | MEDIUM (1-2 weeks) | HIGH (2-4 weeks)
- **Impact Scale**: 🔴 CRITICAL | 🟡 HIGH/MEDIUM | 🟢 LOW
- **Review Frequency**: Weekly during active sprints, bi-weekly during maintenance
- **Risk**: Refactoring carries risk of breaking existing functionality - test thoroughly!

---

## 🔗 RELATED DOCUMENTS

- [COMPREHENSIVE_CODE_REVIEW.md](./COMPREHENSIVE_CODE_REVIEW.md) - Full analysis with metrics
- [CODE_QUALITY_ANALYSIS.md](./CODE_QUALITY_ANALYSIS.md) - Existing quality report
- [pyproject.toml](./living_rusted_tankard/pyproject.toml) - Project configuration

---

**Remember**: Make small, incremental changes. Test after each change. Don't try to do everything at once!
