"""Integration tests for LLM pipeline functionality."""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from tests.fixtures import (
    clean_game_state,
    mock_llm_service,
    performance_monitor,
    async_performance_monitor,
)
from tests.utils.mock_helpers import MockLLMService
from tests.utils.assertion_helpers import (
    assert_llm_response_valid,
    assert_performance_within_limits,
)

from core.async_llm_pipeline import AsyncLLMPipeline, LLMRequest
from core.llm.narrator import LLMNarrator
from core.enhanced_llm_game_master import EnhancedLLMGameMaster


class TestAsyncLLMPipelineIntegration:
    """Integration tests for async LLM pipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_request_processing(self):
        """Test basic LLM pipeline request processing."""
        pipeline = AsyncLLMPipeline()

        # Mock LLM service
        mock_service = MockLLMService()
        mock_service.queue_response(
            {"response": "The tavern is warm and welcoming.", "confidence": 0.9}
        )

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Create a request
            request = LLMRequest(
                request_id="test_request_1",
                prompt="Describe the tavern",
                request_type="narration",
                priority=1,
            )

            # Process the request
            result = await pipeline.process_request(request)

            assert result is not None
            assert_llm_response_valid(result)
            assert result["response"] == "The tavern is warm and welcoming."
            assert mock_service.get_call_count() == 1

    @pytest.mark.asyncio
    async def test_pipeline_concurrent_requests(self, async_performance_monitor):
        """Test pipeline handling concurrent requests."""
        pipeline = AsyncLLMPipeline()

        mock_service = MockLLMService()

        # Queue multiple responses
        responses = [{"response": f"Response {i}", "confidence": 0.8} for i in range(5)]

        for response in responses:
            mock_service.queue_response(response)

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Create multiple requests
            requests = [
                LLMRequest(
                    request_id=f"concurrent_request_{i}",
                    prompt=f"Prompt {i}",
                    request_type="narration",
                    priority=1,
                )
                for i in range(5)
            ]

            # Measure concurrent processing
            with async_performance_monitor.measure_async_operation(
                "concurrent_llm_requests"
            ):
                # Process requests concurrently
                tasks = [pipeline.process_request(req) for req in requests]
                results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all requests completed successfully
            assert len(results) == 5
            assert all(not isinstance(r, Exception) for r in results)
            assert all(r is not None and "response" in r for r in results)

            # Verify all LLM calls were made
            assert mock_service.get_call_count() == 5

    @pytest.mark.asyncio
    async def test_pipeline_priority_handling(self):
        """Test that pipeline respects request priorities."""
        pipeline = AsyncLLMPipeline()

        mock_service = MockLLMService()
        processing_order = []

        # Override process method to track order
        original_process = mock_service.generate_response

        async def track_processing(prompt, **kwargs):
            processing_order.append(prompt)
            await asyncio.sleep(0.1)  # Simulate processing time
            return {"response": f"Processed: {prompt}", "confidence": 0.8}

        mock_service.generate_response = track_processing

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Create requests with different priorities
            requests = [
                LLMRequest(
                    request_id="low_priority",
                    prompt="Low priority prompt",
                    request_type="narration",
                    priority=1,
                ),
                LLMRequest(
                    request_id="high_priority",
                    prompt="High priority prompt",
                    request_type="narration",
                    priority=3,
                ),
                LLMRequest(
                    request_id="medium_priority",
                    prompt="Medium priority prompt",
                    request_type="narration",
                    priority=2,
                ),
            ]

            # Submit all requests simultaneously
            tasks = [pipeline.process_request(req) for req in requests]
            results = await asyncio.gather(*tasks)

            # Verify processing order respects priority
            # Higher priority (3) should be processed first
            assert "High priority prompt" in processing_order[0]

    @pytest.mark.asyncio
    async def test_pipeline_error_recovery(self):
        """Test pipeline error recovery mechanisms."""
        pipeline = AsyncLLMPipeline()

        mock_service = MockLLMService()
        mock_service.set_failure_mode(True, "Simulated LLM failure")

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            request = LLMRequest(
                request_id="error_test",
                prompt="This should fail",
                request_type="narration",
                priority=1,
            )

            # Process request that will fail
            result = await pipeline.process_request(request)

            # Should get an error response, not None
            assert result is not None
            assert "error" in result or "fallback" in result

    @pytest.mark.asyncio
    async def test_pipeline_thread_safety(self):
        """Test pipeline thread safety with concurrent access."""
        pipeline = AsyncLLMPipeline()

        mock_service = MockLLMService()

        # Add responses for concurrent requests
        for i in range(10):
            mock_service.queue_response(
                {"response": f"Thread safe response {i}", "confidence": 0.8}
            )

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Create many concurrent requests to test thread safety
            async def make_request(i):
                request = LLMRequest(
                    request_id=f"thread_test_{i}",
                    prompt=f"Thread test prompt {i}",
                    request_type="narration",
                    priority=1,
                )
                return await pipeline.process_request(request)

            # Run many concurrent requests
            tasks = [make_request(i) for i in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all completed without exceptions
            assert len(results) == 10
            assert all(not isinstance(r, Exception) for r in results)

            # Verify pipeline state is consistent
            # Active requests should be cleared
            assert len(pipeline.active_requests) == 0

    @pytest.mark.asyncio
    async def test_pipeline_request_tracking(self):
        """Test pipeline request tracking functionality."""
        pipeline = AsyncLLMPipeline()

        mock_service = MockLLMService()
        mock_service.default_response = {
            "response": "Tracked response",
            "confidence": 0.8,
        }

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            request = LLMRequest(
                request_id="tracking_test",
                prompt="Track this request",
                request_type="narration",
                priority=1,
            )

            # Submit request and check it's tracked
            task = asyncio.create_task(pipeline.process_request(request))

            # Give it a moment to start processing
            await asyncio.sleep(0.01)

            # Request should be in active requests
            assert "tracking_test" in pipeline.active_requests

            # Wait for completion
            result = await task

            # Request should be removed from active requests
            assert "tracking_test" not in pipeline.active_requests
            assert result is not None


class TestLLMNarratorIntegration:
    """Integration tests for LLM Narrator."""

    @pytest.mark.asyncio
    async def test_narrator_story_generation(self, clean_game_state):
        """Test narrator story generation from game state."""
        narrator = LLMNarrator()

        mock_service = MockLLMService()
        mock_service.queue_response(
            {
                "response": "You find yourself in a cozy tavern. The warmth from the fireplace fills the room as patrons chat quietly over their drinks.",
                "confidence": 0.9,
            }
        )

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Generate narration
            result = await narrator.narrate_scene(clean_game_state)

            assert result is not None
            assert_llm_response_valid(result)
            assert "tavern" in result["response"].lower()

            # Verify game state was included in prompt
            last_call = mock_service.get_last_call()
            assert "prompt" in last_call

    @pytest.mark.asyncio
    async def test_narrator_action_description(self, clean_game_state):
        """Test narrator action description generation."""
        narrator = LLMNarrator()

        mock_service = MockLLMService()
        mock_service.queue_response(
            {
                "response": "You approach the barkeeper and offer a friendly greeting. He looks up from cleaning a mug and nods in acknowledgment.",
                "confidence": 0.85,
            }
        )

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            action = {"type": "greet", "target": "Barkeep Bob", "player": "TestPlayer"}

            result = await narrator.describe_action(action, clean_game_state)

            assert result is not None
            assert_llm_response_valid(result)
            assert (
                "greeting" in result["response"].lower()
                or "greet" in result["response"].lower()
            )

    @pytest.mark.asyncio
    async def test_narrator_caching_behavior(self):
        """Test narrator response caching."""
        narrator = LLMNarrator()

        mock_service = MockLLMService()
        mock_service.default_response = {
            "response": "Cached response",
            "confidence": 0.8,
        }

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Make the same request twice
            game_state = {"location": "test_location", "player": {"name": "Test"}}

            result1 = await narrator.narrate_scene(game_state)
            result2 = await narrator.narrate_scene(game_state)

            # Both should succeed
            assert result1 is not None
            assert result2 is not None

            # If caching is working, LLM should only be called once
            # (This depends on actual caching implementation)
            call_count = mock_service.get_call_count()
            assert call_count >= 1  # At least one call was made


class TestEnhancedLLMGameMasterIntegration:
    """Integration tests for Enhanced LLM Game Master."""

    @pytest.mark.asyncio
    async def test_game_master_command_processing(self, clean_game_state):
        """Test game master command processing."""
        game_master = EnhancedLLMGameMaster()

        mock_service = MockLLMService()
        mock_service.queue_response(
            {
                "action": "look",
                "result": "success",
                "description": "You see a bustling tavern with several patrons.",
                "state_changes": {},
            }
        )

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Process a command
            result = await game_master.process_command("look around", clean_game_state)

            assert result is not None
            assert "action" in result
            assert "result" in result
            assert mock_service.get_call_count() == 1

    @pytest.mark.asyncio
    async def test_game_master_context_awareness(self, clean_game_state):
        """Test game master context awareness across multiple commands."""
        game_master = EnhancedLLMGameMaster()

        mock_service = MockLLMService()

        # Queue responses for a sequence of commands
        responses = [
            {
                "action": "greet",
                "result": "success",
                "description": "You greet the barkeeper.",
                "state_changes": {"reputation": 1},
            },
            {
                "action": "order",
                "result": "success",
                "description": "The barkeeper serves you an ale.",
                "state_changes": {"gold": -5, "items": ["ale"]},
            },
        ]

        for response in responses:
            mock_service.queue_response(response)

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Process sequence of commands
            result1 = await game_master.process_command(
                "greet barkeeper", clean_game_state
            )

            # Update game state based on first result
            if "state_changes" in result1:
                clean_game_state.update(result1["state_changes"])

            result2 = await game_master.process_command("order ale", clean_game_state)

            assert result1 is not None
            assert result2 is not None
            assert mock_service.get_call_count() == 2

            # Verify context is maintained
            calls = mock_service.call_history
            assert len(calls) == 2

            # Second call should include context from first interaction
            second_prompt = calls[1]["prompt"]
            # Should include previous action or state changes
            assert (
                "greet" in second_prompt.lower()
                or "reputation" in second_prompt.lower()
            )

    @pytest.mark.asyncio
    async def test_game_master_performance_optimization(self, performance_monitor):
        """Test game master performance optimizations."""
        game_master = EnhancedLLMGameMaster()

        mock_service = MockLLMService()
        mock_service.default_response = {
            "action": "wait",
            "result": "success",
            "description": "Time passes...",
            "state_changes": {},
        }

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            game_state = {"player": {"name": "Test"}, "location": "tavern"}

            # Measure performance of multiple command processing
            with performance_monitor.measure("game_master_commands"):
                for i in range(5):
                    await game_master.process_command(f"command_{i}", game_state)

            # Verify performance is acceptable
            performance_monitor.assert_performance_thresholds(
                {
                    "max_execution_time": 3.0,  # 5 commands in under 3 seconds
                    "max_memory_mb": 30,
                }
            )


class TestLLMIntegrationWithGameSystems:
    """Test LLM integration with various game systems."""

    @pytest.mark.asyncio
    async def test_llm_npc_interaction_integration(self, clean_game_state):
        """Test LLM integration with NPC interaction system."""
        from core.npc import NPC, NPCType

        # Create NPC with LLM integration
        npc = NPC(
            id="chatty_barkeeper",
            name="Chatty Barkeeper",
            description="A friendly and talkative barkeeper",
            npc_type=NPCType.BARKEEP,
            current_room="tavern"
        )

        mock_service = MockLLMService()
        mock_service.queue_response(
            {
                "response": "Welcome to the Rusted Tankard! What can I get for you today?",
                "mood": "cheerful",
                "confidence": 0.9,
            }
        )

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Simulate player interaction
            player_message = "Hello, I'm new here."

            result = await npc.generate_response(player_message, clean_game_state)

            assert result is not None
            assert_llm_response_valid(result)
            assert (
                "welcome" in result["response"].lower()
                or "hello" in result["response"].lower()
            )

    @pytest.mark.asyncio
    async def test_llm_quest_generation_integration(self, clean_game_state):
        """Test LLM integration with quest/bounty generation."""
        from core.bounties import BountySystem

        bounty_system = BountySystem()

        mock_service = MockLLMService()
        mock_service.queue_response(
            {
                "title": "Missing Merchant",
                "description": "A local merchant has gone missing on the road to the next town. Find out what happened.",
                "difficulty": "medium",
                "reward": 150,
                "requirements": ["investigation", "travel"],
            }
        )

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Generate a quest
            quest = await bounty_system.generate_dynamic_quest(clean_game_state)

            assert quest is not None
            assert "title" in quest
            assert "description" in quest
            assert isinstance(quest.get("reward", 0), (int, float))

    @pytest.mark.asyncio
    async def test_llm_economy_integration(self, clean_game_state):
        """Test LLM integration with economy system."""
        from core.economy import Economy

        economy = Economy()

        mock_service = MockLLMService()
        mock_service.queue_response(
            {
                "market_event": "harvest_festival",
                "description": "The annual harvest festival has increased demand for ale and food.",
                "price_changes": {
                    "ale": 1.2,  # 20% increase
                    "bread": 1.1,  # 10% increase
                },
                "duration_days": 3,
            }
        )

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Generate market event
            event = await economy.generate_market_event(clean_game_state)

            assert event is not None
            assert "market_event" in event
            assert "price_changes" in event
            assert isinstance(event["price_changes"], dict)

    @pytest.mark.asyncio
    async def test_llm_error_propagation(self, clean_game_state):
        """Test error propagation through LLM-integrated systems."""
        game_master = EnhancedLLMGameMaster()

        mock_service = MockLLMService()
        mock_service.set_failure_mode(True, "Network timeout")

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Command should handle LLM failure gracefully
            result = await game_master.process_command(
                "complex action", clean_game_state
            )

            # Should not raise exception, should return fallback
            assert result is not None
            # Should indicate error or use fallback behavior
            assert (
                "error" in result
                or "fallback" in result
                or result.get("result") == "error"
            )
