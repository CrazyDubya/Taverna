# Immediate Action Plan: Next 4 Weeks

**Goal:** Build momentum with quick wins while fixing foundation

---

## Week 1: Foundation Fixes (Critical Path)

### Priority 1: Thread Safety Issues ⚠️
**File:** `living_rusted_tankard/core/async_llm_pipeline.py`
**Problem:** Threading without proper locks around shared state
**Time:** 8 hours

**Tasks:**
```python
# Lines 201-202: Add proper locking
self._lock = threading.RLock()  # ✓ Already exists
self._stats_lock = threading.Lock()  # ✓ Already exists

# But need to audit ALL shared state access:
1. Review self.active_requests access patterns
2. Review self.request_queue access patterns
3. Ensure all _stats modifications use _update_stats()
4. Test concurrent access with 20+ simultaneous requests
```

**Test Plan:**
- [ ] Create stress test: 50 concurrent LLM requests
- [ ] Run with thread sanitizer
- [ ] Verify no race conditions

---

### Priority 2: Database Migrations 🔧
**Problem:** No migration system = schema changes break production
**Time:** 6 hours

**Tasks:**
1. Install Alembic: `poetry add alembic`
2. Initialize: `alembic init migrations`
3. Create initial migration from current schema
4. Document migration workflow in docs/
5. Add migration check to startup

**Files to create:**
- `migrations/versions/001_initial_schema.py`
- `docs/DATABASE_MIGRATIONS.md`

---

### Priority 3: Resource Cleanup 🧹
**File:** `living_rusted_tankard/core/ai_player.py:331`
**Problem:** Global `_ai_player` instance never cleaned up
**Time:** 4 hours

**Solution:**
```python
# Replace global instance with session-based management
class AIPlayerManager:
    def __init__(self):
        self._sessions: Dict[str, AIPlayer] = {}

    def create_session(self, session_id: str) -> AIPlayer:
        """Create AI player for session"""

    def cleanup_session(self, session_id: str) -> None:
        """Clean up AI player resources"""

    async def cleanup_all(self) -> None:
        """Cleanup on shutdown"""
```

**Tasks:**
- [ ] Refactor global instance to manager pattern
- [ ] Add cleanup on session end
- [ ] Add cleanup on server shutdown
- [ ] Test for memory leaks (run 100 sessions)

---

## Week 2: Quick Win - Event Bus Library 🎯

### Day 1-2: Extraction (15 hours)

**Create new repository:**
```bash
mkdir event-bus-py
cd event-bus-py
poetry init
```

**Files to create:**
```
event-bus-py/
├── event_bus/
│   ├── __init__.py
│   ├── bus.py           # Core EventBus class
│   ├── event.py         # Event base class
│   └── decorators.py    # @event_handler decorator
├── tests/
│   ├── test_bus.py
│   ├── test_decorators.py
│   └── test_performance.py
├── examples/
│   ├── basic_usage.py
│   ├── game_engine.py
│   └── discord_bot.py
├── docs/
│   ├── index.md
│   ├── quickstart.md
│   └── api.md
├── README.md
├── pyproject.toml
└── LICENSE (MIT)
```

**Enhancements beyond current code:**
```python
# Add decorator support
@event_handler(EventType.PLAYER_MOVE)
def on_player_move(event: Event):
    ...

# Add middleware
bus.add_middleware(LoggingMiddleware())
bus.add_middleware(ValidationMiddleware())

# Add async support
await bus.dispatch_async(event)
```

---

### Day 3: Testing & Docs (6 hours)

**Test Coverage Requirements:**
- [ ] 95%+ coverage
- [ ] Unit tests for all methods
- [ ] Integration tests for common patterns
- [ ] Performance benchmarks (1M events/sec target)

**Documentation:**
- [ ] Comprehensive README with examples
- [ ] API documentation (docstrings)
- [ ] Quickstart tutorial
- [ ] Comparison with alternatives (pyee, blinker)

---

### Day 4: Publishing (3 hours)

**PyPI Setup:**
```bash
poetry build
poetry publish

# Or use GitHub Actions for auto-publish
```

**Create:**
- [ ] GitHub repository with good README
- [ ] GitHub Actions CI/CD
- [ ] PyPI package listing
- [ ] Read the Docs setup

**Marketing:**
- [ ] Blog post: "Building Decoupled Systems with Event Buses"
- [ ] Post to r/Python
- [ ] Tweet thread with code examples
- [ ] Submit to PyPI trending

---

## Week 3: Mystery System Prototype 🔍

### Day 1-2: Data Model (12 hours)

**Create files:**
```
living_rusted_tankard/core/
├── mystery/
│   ├── __init__.py
│   ├── mystery.py       # Mystery, Clue, Solution classes
│   ├── manager.py       # MysteryManager
│   └── evaluator.py     # Solution checking logic
```

**Core classes:**
```python
@dataclass
class Clue:
    id: str
    mystery_id: str
    text: str
    revealed_by: str  # NPC or location
    reliability: float  # 0.0-1.0
    requires_relationship: float  # -1.0 to 1.0
    requires_previous_clues: List[str]
    contradicts: List[str]
    is_red_herring: bool
    discovery_method: DiscoveryMethod  # CONVERSATION, OBSERVATION, ITEM

@dataclass
class Mystery:
    id: str
    title: str
    description: str
    difficulty: Difficulty
    clues: List[Clue]
    solution_clues: List[str]  # IDs of clues needed for solution
    false_solutions: List[Solution]  # Common wrong answers
    correct_solution: Solution
    rewards: List[Reward]

class MysteryManager:
    def discover_clue(self, clue_id: str, player: Player) -> Optional[Clue]:
        """Check if player can discover this clue"""

    def check_solution(self, mystery_id: str, solution: Solution) -> SolutionResult:
        """Evaluate player's proposed solution"""

    def get_available_clues(self, mystery_id: str, player: Player) -> List[Clue]:
        """Get clues player can currently discover"""
```

---

### Day 3-4: First Mystery (10 hours)

**"The Cellar Secret" - Complete Design:**

```yaml
mystery:
  id: cellar_secret
  title: "The Cellar Secret"
  description: "Strange noises from the tavern cellar. Gene is evasive about what's down there."
  difficulty: MEDIUM

clues:
  - id: clue_01
    text: "Gene goes to the cellar only after midnight"
    revealed_by: "observation"
    reliability: 1.0
    requires_relationship: 0.0

  - id: clue_02
    text: "Sarah mentions Gene's ale supplier never visits during the day"
    revealed_by: "sarah"
    reliability: 0.9
    requires_relationship: 0.3

  - id: clue_03
    text: "Marcus claims he saw boats near the river behind the tavern"
    revealed_by: "marcus"
    reliability: 0.7
    requires_relationship: 0.5
    requires_previous_clues: [clue_01]

  # ... 12 more clues ...

  - id: clue_red_01
    text: "Gene has a gambling debt to the local guild"
    revealed_by: "gossip"
    reliability: 0.5
    is_red_herring: true

solutions:
  correct:
    description: "Underground river access used for smuggling illegal goods"
    requires_clues: [clue_01, clue_02, clue_03, clue_07, clue_11]

  false_solutions:
    - description: "Gene is hiding treasure"
      common_mistake: true
    - description: "Cellar is haunted"
      requires_clues: [clue_red_01]
```

**Write the mystery:**
- [ ] Create YAML file with all clues
- [ ] Write NPC dialogue for each clue reveal
- [ ] Design solution branches (3 endings based on player choice)
- [ ] Write outcome narratives

---

### Day 5: Integration (6 hours)

**Connect mystery to existing systems:**
- [ ] Add mystery state to GameState
- [ ] Modify NPC conversations to reveal clues
- [ ] Add "investigate" command
- [ ] Add "accuse" command
- [ ] Track discovered clues in player state

**Test:**
- [ ] Playthrough from start to each ending
- [ ] Verify clue dependencies work
- [ ] Test with different relationship levels

---

## Week 4: Evidence Board UI Mockup 🎨

### Day 1-2: UI Design (10 hours)

**Create HTML/CSS mockup:**
```
living_rusted_tankard/game/templates/
├── evidence_board.html
└── components/
    ├── clue_card.html
    └── connection_line.html
```

**Technology choice:**
- Option A: Canvas API (full control, harder)
- Option B: Cytoscape.js (graph library, easier)
- **Recommendation:** Cytoscape.js for MVP

**Features:**
- [ ] Visual nodes for each clue
- [ ] Drag to connect related clues
- [ ] Color-coding by reliability
- [ ] Filter by NPC source
- [ ] Highlight contradictions
- [ ] "Solve mystery" button

---

### Day 3: Basic Interactions (8 hours)

**JavaScript functionality:**
```javascript
class EvidenceBoard {
    constructor(mysteryId) {
        this.cy = cytoscape({...});
        this.clues = [];
    }

    addClue(clue) {
        // Add node to graph
    }

    connectClues(clueA, clueB, relationship) {
        // Add edge
    }

    highlightContradictions() {
        // Find and highlight contradictory clues
    }

    proposeSolution() {
        // Submit player's theory
    }
}
```

**Tasks:**
- [ ] Implement drag-and-drop
- [ ] Implement clue connections
- [ ] Add filters and search
- [ ] Create accusation modal
- [ ] Connect to backend API

---

### Day 4: Integration + Polish (6 hours)

**Connect to mystery system:**
- [ ] API endpoint: GET /mystery/:id/clues
- [ ] API endpoint: POST /mystery/:id/solution
- [ ] WebSocket for real-time updates
- [ ] Save board state to session

**Polish:**
- [ ] Responsive design (mobile friendly)
- [ ] Animations for clue discovery
- [ ] Sound effects (optional)
- [ ] Tutorial overlay

---

## Week 4 End: Playtest & Iterate 🎮

### Playtest Session (4 hours)

**Recruit 3-5 testers:**
- [ ] 1 experienced player
- [ ] 2 new players
- [ ] 1 non-gamer

**Observe:**
- Can they discover clues naturally?
- Do they understand the evidence board?
- How long to solve the mystery?
- Where do they get stuck?
- What's fun vs frustrating?

**Collect feedback:**
- [ ] Written survey
- [ ] Video recordings (with permission)
- [ ] Analytics (time spent, actions taken)

---

### Iterate Based on Feedback (6 hours)

**Common issues to fix:**
- Clues too hard to discover → Add hints
- Mystery too easy → Add red herrings
- UI confusing → Simplify, add tutorial
- Pacing slow → Reduce busywork

---

## Success Metrics for Month 1

### Technical
- [x] Thread safety issues resolved
- [x] Database migrations working
- [x] Resource cleanup implemented
- [x] Event bus library published
- [x] Mystery system functional

### Product
- [x] 1 complete mystery playable
- [x] Evidence board UI working
- [x] 3+ playtesters completed mystery
- [x] Average completion time: 5-7 hours

### Business
- [x] Event bus: 10+ GitHub stars
- [x] Event bus: 20+ PyPI downloads
- [x] Blog post: 500+ views
- [x] Foundation for next components

---

## Daily Schedule Template (Part-Time)

**Weekdays (3 hours/day):**
- Hour 1: Focus work (coding, writing)
- Hour 2: Testing & debugging
- Hour 3: Documentation & planning

**Weekends (6 hours/day):**
- Hours 1-3: Deep work on complex features
- Hour 4: Testing & integration
- Hours 5-6: Community, marketing, learning

**Total:** ~25 hours/week = realistic sustainable pace

---

## Immediate Next Commands

```bash
# 1. Create branch for foundation fixes
git checkout -b fix/foundation-cleanup

# 2. Install Alembic
poetry add alembic

# 3. Create test for thread safety
touch tests/test_thread_safety.py

# 4. Create mystery system directory
mkdir -p living_rusted_tankard/core/mystery

# 5. Create event-bus-py repository
cd ..
mkdir event-bus-py
cd event-bus-py
poetry init
```

---

## Resources & References

### Learning Materials
- **Alembic Tutorial:** https://alembic.sqlalchemy.org/en/latest/tutorial.html
- **Thread Safety in Python:** https://realpython.com/intro-to-python-threading/
- **Cytoscape.js Docs:** https://js.cytoscape.org/
- **PyPI Publishing:** https://packaging.python.org/tutorials/packaging-projects/

### Inspiration
- **Return of the Obra Dinn** (mystery mechanics)
- **Disco Elysium** (dialogue depth)
- **AI Dungeon** (AI integration)
- **Among Us** (social deduction)

---

## Questions to Answer This Week

1. **Component vs Product focus:** 80/20 split? 50/50? Decide based on your goals.

2. **Mystery difficulty:** Should first mystery be easy tutorial or engaging challenge?

3. **UI framework:** Stick with current stack or add Vue/React for evidence board?

4. **Release strategy:** Closed alpha → Beta → Public? Or soft launch immediately?

5. **Monetization timing:** When to add payment? Month 3? Month 6? At launch?

---

## The "One Thing" Each Week

**Week 1:** Fix the foundation (not sexy, but essential)
**Week 2:** Ship event-bus library (first public win)
**Week 3:** Make mysteries fun (core gameplay validation)
**Week 4:** Evidence board feels cool (visual impact)

**Focus on ONE thing. Ship it. Celebrate. Repeat.**

---

## Emergency Brake Points

**If you're stuck on anything for more than 4 hours:**
1. Take a break
2. Ask for help (Discord, forums, contractor)
3. Simplify the scope
4. Move to next task and return later

**If you're not having fun for 2+ weeks:**
1. Take a full week off
2. Reassess what you enjoy
3. Adjust roadmap to focus on fun parts
4. Consider pausing or pivoting

**This should be energizing, not draining.**

---

**Ready to start? Pick one task from Week 1 and begin. 🚀**
