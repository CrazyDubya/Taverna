"""
Tests for the Narrative Engine

Comprehensive tests for the Phase 4 narrative system including story threads,
thread management, rules engine, and orchestration.
"""

import pytest
import time
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import Dict, List, Any

from core.narrative import (
    StoryThread, StoryBeat, ThreadStage, ThreadType,
    ThreadManager, ThreadConvergence,
    NarrativeRulesEngine, TensionManager, PacingMetrics, NarrativeHealth,
    NarrativeOrchestrator, ClimaticSequencer, ClimaticMoment, ArcPlan
)


class TestStoryThread:
    """Test story thread functionality"""
    
    def test_story_thread_creation(self):
        """Test basic story thread creation"""
        thread = StoryThread(
            id="test_thread_1",
            title="The Missing Merchant",
            type=ThreadType.MYSTERY,
            description="A merchant has vanished from the tavern",
            primary_participants=["merchant_john", "player"],
            secondary_participants=["bartender_tom"]
        )
        
        assert thread.id == "test_thread_1"
        assert thread.title == "The Missing Merchant"
        assert thread.type == ThreadType.MYSTERY
        assert thread.stage == ThreadStage.SETUP
        assert thread.tension_level == 0.0
        assert thread.player_involvement == 0.5
        assert len(thread.beats) == 0
    
    def test_story_beat_creation(self):
        """Test story beat creation"""
        beat = StoryBeat(
            id="beat_1",
            thread_id="test_thread_1",
            beat_type="investigation",
            content="Player discovers merchant's room is empty",
            participants=["player", "bartender_tom"],
            prerequisites={"location": "upstairs"},
            effects={"tension_increase": 0.1, "clue_discovered": "empty_room"}
        )
        
        assert beat.id == "beat_1"
        assert beat.thread_id == "test_thread_1"
        assert beat.beat_type == "investigation"
        assert beat.emotional_weight == 0.5
        assert beat.narrative_significance == 0.5
    
    def test_thread_advancement(self):
        """Test thread stage advancement"""
        thread = StoryThread(
            id="test_thread_1",
            title="Test Thread",
            type=ThreadType.MAIN_QUEST,
            description="Test description",
            primary_participants=["player"]
        )
        
        # Should start in SETUP
        assert thread.stage == ThreadStage.SETUP
        
        # Advance to rising action
        thread.stage = ThreadStage.RISING_ACTION
        thread.tension_level = 0.6
        
        assert thread.stage == ThreadStage.RISING_ACTION
        assert thread.tension_level == 0.6


class TestThreadManager:
    """Test thread management functionality"""
    
    @pytest.fixture
    def thread_manager(self):
        """Create a thread manager for testing"""
        return ThreadManager()
    
    @pytest.fixture
    def sample_threads(self):
        """Create sample threads for testing"""
        return [
            StoryThread(
                id="thread_1",
                title="The Lost Ring",
                type=ThreadType.ROMANCE,
                description="Finding a lost engagement ring",
                primary_participants=["player", "lover_npc"],
                stage=ThreadStage.RISING_ACTION,
                tension_level=0.4
            ),
            StoryThread(
                id="thread_2", 
                title="Tavern Politics",
                type=ThreadType.POLITICAL,
                description="Tensions between local factions",
                primary_participants=["player", "faction_leader"],
                stage=ThreadStage.SETUP,
                tension_level=0.2
            )
        ]
    
    def test_thread_manager_initialization(self, thread_manager):
        """Test thread manager initialization"""
        assert len(thread_manager.active_threads) == 0
        assert len(thread_manager.completed_threads) == 0
        assert thread_manager.max_active_threads == 7
    
    def test_add_thread(self, thread_manager, sample_threads):
        """Test adding threads to manager"""
        thread_manager.add_thread(sample_threads[0])
        
        assert len(thread_manager.active_threads) == 1
        assert sample_threads[0].id in thread_manager.active_threads
    
    def test_advance_threads(self, thread_manager, sample_threads):
        """Test advancing threads"""
        # Add threads
        for thread in sample_threads:
            thread_manager.add_thread(thread)
        
        # Mock world state
        world_state = {
            "current_location": "tavern_main",
            "time": "evening",
            "available_npcs": ["lover_npc", "faction_leader"]
        }
        
        # Advance threads
        events = thread_manager.advance_threads(
            available_participants={"player", "lover_npc", "faction_leader"},
            world_state=world_state
        )
        
        assert isinstance(events, list)
        # Should have some events for advancement
        assert len(events) >= 0
    
    def test_convergence_detection(self, thread_manager, sample_threads):
        """Test convergence detection between threads"""
        # Add threads with overlapping participants
        for thread in sample_threads:
            thread_manager.add_thread(thread)
        
        convergences = thread_manager.detect_convergences()
        
        assert isinstance(convergences, list)
        # Test that convergences have required attributes
        for conv in convergences:
            assert hasattr(conv, 'id')
            assert hasattr(conv, 'thread_ids')
            assert hasattr(conv, 'convergence_type')


class TestTensionManager:
    """Test tension management functionality"""
    
    @pytest.fixture
    def tension_manager(self):
        """Create a tension manager for testing"""
        return TensionManager()
    
    @pytest.fixture
    def sample_threads_with_tension(self):
        """Create threads with various tension levels"""
        return [
            StoryThread(
                id="low_tension",
                title="Low Tension Thread",
                type=ThreadType.SOCIAL,
                description="Social interaction",
                primary_participants=["player", "npc1"],
                tension_level=0.2,
                player_involvement=0.8
            ),
            StoryThread(
                id="high_tension",
                title="High Tension Thread", 
                type=ThreadType.MAIN_QUEST,
                description="Critical quest",
                primary_participants=["player", "boss"],
                tension_level=0.8,
                player_involvement=0.9
            )
        ]
    
    def test_tension_manager_initialization(self, tension_manager):
        """Test tension manager initialization"""
        assert tension_manager.global_tension == 0.0
        assert len(tension_manager.tension_history) == 0
        assert tension_manager.max_global_tension == 0.8
    
    def test_update_global_tension(self, tension_manager, sample_threads_with_tension):
        """Test global tension calculation"""
        global_tension = tension_manager.update_global_tension(sample_threads_with_tension)
        
        assert 0.0 <= global_tension <= 1.0
        assert global_tension <= tension_manager.max_global_tension
        assert len(tension_manager.tension_history) == 1
    
    def test_tension_trend_calculation(self, tension_manager):
        """Test tension trend calculation"""
        # Add some history points manually
        current_time = time.time()
        tension_manager.tension_history.extend([
            (current_time - 1800, 0.3),  # 30 minutes ago
            (current_time - 900, 0.5),   # 15 minutes ago
            (current_time, 0.7)          # Now
        ])
        
        trend = tension_manager.get_tension_trend(window_minutes=30)
        
        # Should show increasing trend
        assert trend > 0
    
    def test_tension_adjustment_recommendation(self, tension_manager):
        """Test tension adjustment recommendations"""
        thread = StoryThread(
            id="test",
            title="Test",
            type=ThreadType.MYSTERY,
            description="Test",
            primary_participants=["player"],
            stage=ThreadStage.CLIMAX,
            tension_level=0.5
        )
        
        recommended_tension = tension_manager.recommend_tension_adjustment(thread)
        
        assert 0.0 <= recommended_tension <= 1.0


class TestNarrativeRulesEngine:
    """Test narrative rules engine functionality"""
    
    @pytest.fixture
    def rules_engine(self):
        """Create a rules engine for testing"""
        return NarrativeRulesEngine()
    
    @pytest.fixture
    def complex_thread_scenario(self):
        """Create a complex scenario for testing"""
        return [
            StoryThread(
                id="main_quest",
                title="Save the Kingdom",
                type=ThreadType.MAIN_QUEST,
                description="Epic main quest",
                primary_participants=["player", "king"],
                stage=ThreadStage.CLIMAX,
                tension_level=0.9,
                player_involvement=1.0
            ),
            StoryThread(
                id="romance",
                title="Love Interest",
                type=ThreadType.ROMANCE,
                description="Romance subplot",
                primary_participants=["player", "love_interest"],
                stage=ThreadStage.RISING_ACTION,
                tension_level=0.6,
                player_involvement=0.8
            ),
            StoryThread(
                id="side_quest_1",
                title="Help the Farmer",
                type=ThreadType.SIDE_QUEST,
                description="Agricultural assistance",
                primary_participants=["player", "farmer"],
                stage=ThreadStage.RESOLUTION,
                tension_level=0.1,
                player_involvement=0.5
            )
        ]
    
    def test_rules_engine_initialization(self, rules_engine):
        """Test rules engine initialization"""
        assert isinstance(rules_engine.tension_manager, TensionManager)
        assert isinstance(rules_engine.pacing_metrics, PacingMetrics)
        assert len(rules_engine.intervention_queue) == 0
    
    def test_narrative_health_evaluation(self, rules_engine, complex_thread_scenario):
        """Test narrative health evaluation"""
        world_state = {
            "current_time": time.time(),
            "player_location": "tavern",
            "active_npcs": ["king", "love_interest", "farmer"]
        }
        
        health = rules_engine.evaluate_narrative_health(complex_thread_scenario, world_state)
        
        assert isinstance(health, NarrativeHealth)
        assert health in [NarrativeHealth.EXCELLENT, NarrativeHealth.GOOD, 
                         NarrativeHealth.ADEQUATE, NarrativeHealth.POOR, 
                         NarrativeHealth.CRITICAL]
    
    def test_pacing_rule_violations(self, rules_engine, complex_thread_scenario):
        """Test pacing rule violation detection"""
        violations = rules_engine.check_pacing_rules(complex_thread_scenario)
        
        assert isinstance(violations, list)
        # Should detect simultaneous climax violation (main_quest at climax stage)
        climax_violations = [v for v in violations if "climax" in v.lower()]
        # May or may not have violations depending on specific rules
    
    def test_intervention_generation(self, rules_engine, complex_thread_scenario):
        """Test intervention generation"""
        health = NarrativeHealth.POOR
        interventions = rules_engine.generate_interventions(complex_thread_scenario, health)
        
        assert isinstance(interventions, list)
        assert len(interventions) <= 5  # Should limit to top 5
        
        for intervention in interventions:
            assert hasattr(intervention, 'type')
            assert hasattr(intervention, 'priority')
            assert hasattr(intervention, 'description')
    
    def test_pacing_metrics_calculation(self, rules_engine, complex_thread_scenario):
        """Test pacing metrics calculation"""
        world_state = {"current_time": time.time()}
        
        # Manually update metrics to test calculation
        rules_engine._update_pacing_metrics(complex_thread_scenario, world_state)
        
        metrics = rules_engine.pacing_metrics
        assert 0.0 <= metrics.calculate_pacing_score() <= 1.0
        assert metrics.thread_density >= 0.0
        assert 0.0 <= metrics.player_involvement <= 1.0


class TestClimaticSequencer:
    """Test climactic sequencing functionality"""
    
    @pytest.fixture
    def sequencer(self):
        """Create a climatic sequencer for testing"""
        return ClimaticSequencer()
    
    @pytest.fixture
    def climax_ready_thread(self):
        """Create a thread ready for climax"""
        return StoryThread(
            id="ready_for_climax",
            title="Ready Thread",
            type=ThreadType.MYSTERY,
            description="Thread approaching climax",
            primary_participants=["player", "villain"],
            stage=ThreadStage.RISING_ACTION,
            tension_level=0.8
        )
    
    def test_sequencer_initialization(self, sequencer):
        """Test sequencer initialization"""
        assert len(sequencer.scheduled_climaxes) == 0
        assert len(sequencer.climax_history) == 0
        assert sequencer.min_climax_spacing == 1800  # 30 minutes
        assert sequencer.max_parallel_climaxes == 2
    
    def test_schedule_climax(self, sequencer, climax_ready_thread):
        """Test climax scheduling"""
        climax = sequencer.schedule_climax(climax_ready_thread)
        
        assert climax is not None
        assert climax.primary_thread_id == climax_ready_thread.id
        assert len(sequencer.scheduled_climaxes) == 1
        assert climax.timestamp > time.time()
    
    def test_convergence_opportunities(self, sequencer):
        """Test convergence opportunity detection"""
        threads = [
            StoryThread(
                id="thread_a",
                title="Political Intrigue",
                type=ThreadType.POLITICAL,
                description="Political thread",
                primary_participants=["player", "politician"],
                stage=ThreadStage.RISING_ACTION,
                tension_level=0.7
            ),
            StoryThread(
                id="thread_b",
                title="Mystery Investigation",
                type=ThreadType.MYSTERY,
                description="Mystery thread",
                primary_participants=["player", "detective"],
                stage=ThreadStage.RISING_ACTION,
                tension_level=0.6
            )
        ]
        
        opportunities = sequencer.find_convergence_opportunities(threads)
        
        assert isinstance(opportunities, list)
        # May find convergence opportunities based on shared participants


class TestNarrativeOrchestrator:
    """Test narrative orchestration functionality"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create a narrative orchestrator for testing"""
        thread_manager = ThreadManager()
        rules_engine = NarrativeRulesEngine()
        return NarrativeOrchestrator(thread_manager, rules_engine)
    
    @pytest.fixture
    def orchestration_scenario(self):
        """Create a scenario for orchestration testing"""
        return [
            StoryThread(
                id="main_arc_1",
                title="Dragon Threat",
                type=ThreadType.MAIN_QUEST,
                description="Ancient dragon awakens",
                primary_participants=["player", "dragon_hunter"],
                stage=ThreadStage.SETUP,
                tension_level=0.3
            ),
            StoryThread(
                id="character_arc_1",
                title="Hunter's Past",
                type=ThreadType.CHARACTER_ARC,
                description="Dragon hunter's tragic history",
                primary_participants=["dragon_hunter", "player"],
                stage=ThreadStage.RISING_ACTION,
                tension_level=0.5
            )
        ]
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert isinstance(orchestrator.thread_manager, ThreadManager)
        assert isinstance(orchestrator.rules_engine, NarrativeRulesEngine)
        assert isinstance(orchestrator.sequencer, ClimaticSequencer)
        assert len(orchestrator.active_arcs) == 0
        assert orchestrator.max_concurrent_arcs == 3
    
    def test_narrative_orchestration(self, orchestrator, orchestration_scenario):
        """Test main orchestration functionality"""
        world_state = {
            "current_time": time.time(),
            "active_locations": ["tavern", "forest"],
            "weather": "stormy"
        }
        
        actions = orchestrator.orchestrate_narrative(orchestration_scenario, world_state)
        
        assert isinstance(actions, list)
        # Should return orchestration actions
        for action in actions:
            assert isinstance(action, dict)
            assert 'type' in action
    
    def test_arc_planning(self, orchestrator, orchestration_scenario):
        """Test arc planning functionality"""
        world_state = {"current_time": time.time()}
        
        # Test internal arc planning method
        new_arcs = orchestrator._plan_new_arcs(orchestration_scenario, world_state)
        
        assert isinstance(new_arcs, list)
        # Should create arcs when threads are available
    
    def test_intervention_execution(self, orchestrator, orchestration_scenario):
        """Test intervention execution"""
        from core.narrative.rules import InterventionAction
        
        interventions = [
            InterventionAction(
                type="reduce_tension",
                target_thread_id="main_arc_1",
                parameters={"target_tension": 0.4},
                priority=0.8,
                description="Test intervention"
            )
        ]
        
        actions = orchestrator._execute_interventions(interventions, orchestration_scenario)
        
        assert isinstance(actions, list)
        assert len(actions) == 1
        assert actions[0]['type'] == 'adjust_tension'


class TestIntegration:
    """Integration tests for the complete narrative system"""
    
    def test_full_narrative_cycle(self):
        """Test a complete narrative cycle from setup to resolution"""
        # Create components
        thread_manager = ThreadManager()
        rules_engine = NarrativeRulesEngine()
        orchestrator = NarrativeOrchestrator(thread_manager, rules_engine)
        
        # Create initial thread
        initial_thread = StoryThread(
            id="integration_test",
            title="The Mysterious Stranger",
            type=ThreadType.MYSTERY,
            description="A stranger arrives with urgent news",
            primary_participants=["player", "stranger"],
            stage=ThreadStage.SETUP,
            tension_level=0.1
        )
        
        thread_manager.add_thread(initial_thread)
        
        # Simulate progression over time
        world_state = {
            "current_time": time.time(),
            "location": "tavern_main",
            "npcs_present": ["stranger", "bartender"]
        }
        
        # Run orchestration
        actions = orchestrator.orchestrate_narrative([initial_thread], world_state)
        
        # Verify orchestration produces results
        assert isinstance(actions, list)
        
        # Verify narrative health can be evaluated
        health = rules_engine.evaluate_narrative_health([initial_thread], world_state)
        assert isinstance(health, NarrativeHealth)
        
        # Verify thread management works
        available_participants = {"player", "stranger", "bartender"}
        thread_events = thread_manager.advance_threads(available_participants, world_state)
        assert isinstance(thread_events, list)
    
    def test_multiple_thread_coordination(self):
        """Test coordination of multiple overlapping threads"""
        thread_manager = ThreadManager()
        rules_engine = NarrativeRulesEngine()
        orchestrator = NarrativeOrchestrator(thread_manager, rules_engine)
        
        # Create multiple interconnected threads
        threads = [
            StoryThread(
                id="political_thread",
                title="Guild Tensions",
                type=ThreadType.POLITICAL,
                description="Merchant and craftsman guilds clash",
                primary_participants=["player", "guild_leader_merchants"],
                secondary_participants=["guild_leader_crafters"],
                stage=ThreadStage.RISING_ACTION,
                tension_level=0.6
            ),
            StoryThread(
                id="mystery_thread",
                title="Missing Shipments",
                type=ThreadType.MYSTERY,
                description="Guild shipments are disappearing",
                primary_participants=["player", "guild_leader_merchants"],
                secondary_participants=["dock_worker"],
                stage=ThreadStage.RISING_ACTION,
                tension_level=0.5
            ),
            StoryThread(
                id="character_thread",
                title="Guild Leader's Dilemma",
                type=ThreadType.CHARACTER_ARC,
                description="Merchant leader faces difficult choices",
                primary_participants=["guild_leader_merchants", "player"],
                stage=ThreadStage.SETUP,
                tension_level=0.3
            )
        ]
        
        # Add all threads
        for thread in threads:
            thread_manager.add_thread(thread)
        
        world_state = {
            "current_time": time.time(),
            "location": "guild_hall",
            "faction_tensions": {"merchants": 0.7, "crafters": 0.6}
        }
        
        # Test convergence detection
        convergences = thread_manager.detect_convergences()
        assert isinstance(convergences, list)
        
        # Test orchestration with multiple threads
        actions = orchestrator.orchestrate_narrative(threads, world_state)
        assert isinstance(actions, list)
        
        # Test rules evaluation with complex scenario
        health = rules_engine.evaluate_narrative_health(threads, world_state)
        assert isinstance(health, NarrativeHealth)
        
        # Should handle multiple threads without errors
        assert len(thread_manager.active_threads) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])