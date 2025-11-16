"""Integration tests for AI Player functionality."""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch

from tests.fixtures import (
    clean_game_state,
    mock_llm_service,
    isolated_db_session,
    new_player,
    performance_monitor,
)
from tests.utils.mock_helpers import MockLLMService, mock_http_session
from tests.utils.assertion_helpers import (
    assert_game_state_valid,
    assert_llm_response_valid,
    assert_api_response_format,
)

from core.ai_player import AIPlayer
from core.ai_player_manager import AIPlayerManager, AIPlayerPersonality


class TestAIPlayerIntegration:
    """Integration tests for AI Player with real components."""

    @pytest.mark.asyncio
    async def test_ai_player_session_lifecycle(
        self, clean_game_state, isolated_db_session
    ):
        """Test complete AI player session lifecycle."""
        # Create AI player manager
        manager = AIPlayerManager()

        # Create a session
        personality = AIPlayerPersonality(
            name="Curious Explorer",
            traits=["curious", "social"],
            goals=["explore", "learn"],
        )

        session = manager.create_session(personality, "TestAI")
        assert session is not None
        assert session.name == "TestAI"

        # Test session activation
        await session.activate(clean_game_state)
        assert session.is_active

        # Test basic decision making (mocked)
        with patch.object(session.ai_player, "_make_llm_request") as mock_llm:
            mock_llm.return_value = {
                "action": "look",
                "reasoning": "I want to observe my surroundings",
            }

            decision = await session.ai_player.make_decision(clean_game_state)
            assert decision is not None
            assert "action" in decision
            mock_llm.assert_called_once()

        # Test session deactivation
        await session.deactivate()
        assert not session.is_active

        # Cleanup
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_ai_player_with_mock_llm_service(self, clean_game_state):
        """Test AI player with mocked LLM service."""
        mock_service = MockLLMService()
        mock_service.queue_response(
            {
                "action": "greet",
                "target": "Barkeep Bob",
                "reasoning": "I should introduce myself to the barkeeper",
            }
        )

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            ai_player = AIPlayer()

            # Set personality
            personality = AIPlayerPersonality(
                name="Friendly Newcomer",
                traits=["friendly", "polite"],
                goals=["make_friends"],
            )
            ai_player.set_personality(personality)

            # Make decision
            decision = await ai_player.make_decision(clean_game_state)

            assert decision is not None
            assert decision["action"] == "greet"
            assert mock_service.get_call_count() == 1

            # Verify LLM was called with game state context
            last_call = mock_service.get_last_call()
            assert "prompt" in last_call
            assert (
                "game_state" in last_call["prompt"] or "location" in last_call["prompt"]
            )

    @pytest.mark.asyncio
    async def test_ai_player_error_recovery(self, clean_game_state):
        """Test AI player error recovery mechanisms."""
        mock_service = MockLLMService()
        mock_service.set_failure_mode(True, "LLM service unavailable")

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            ai_player = AIPlayer()

            # First attempt should fail and use fallback
            decision = await ai_player.make_decision(clean_game_state)

            # Should get a fallback decision instead of None
            assert decision is not None
            assert "action" in decision
            # Fallback actions are typically basic ones
            assert decision["action"] in ["wait", "look", "rest", "observe"]

    @pytest.mark.asyncio
    async def test_ai_player_personality_influence(self, clean_game_state):
        """Test that personality influences AI decisions."""
        mock_service = MockLLMService()

        # Set up different responses for different personalities
        aggressive_response = {
            "action": "challenge",
            "target": "Town Guard",
            "reasoning": "I want to test my strength",
        }

        peaceful_response = {
            "action": "chat",
            "target": "Barkeep Bob",
            "reasoning": "I prefer peaceful conversation",
        }

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Test aggressive personality
            mock_service.queue_response(aggressive_response)

            aggressive_ai = AIPlayer()
            aggressive_personality = AIPlayerPersonality(
                name="Aggressive Warrior",
                traits=["aggressive", "bold"],
                goals=["prove_strength"],
            )
            aggressive_ai.set_personality(aggressive_personality)

            decision1 = await aggressive_ai.make_decision(clean_game_state)

            # Test peaceful personality
            mock_service.queue_response(peaceful_response)

            peaceful_ai = AIPlayer()
            peaceful_personality = AIPlayerPersonality(
                name="Peaceful Scholar",
                traits=["peaceful", "curious"],
                goals=["learn", "socialize"],
            )
            peaceful_ai.set_personality(peaceful_personality)

            decision2 = await peaceful_ai.make_decision(clean_game_state)

            # Verify different decisions based on personality
            assert decision1["action"] != decision2["action"]
            assert mock_service.get_call_count() == 2

            # Verify personality was included in prompts
            calls = mock_service.call_history
            assert len(calls) == 2

            # Check that personality traits were mentioned in prompts
            first_prompt = calls[0]["prompt"]
            second_prompt = calls[1]["prompt"]

            assert "aggressive" in first_prompt or "bold" in first_prompt
            assert "peaceful" in second_prompt or "curious" in second_prompt

    @pytest.mark.asyncio
    async def test_ai_player_game_state_awareness(self, new_player):
        """Test that AI player is aware of game state changes."""
        # Create modified game state
        game_state = {
            "player": {
                "name": new_player.name,
                "gold": new_player.gold,
                "health": 50,  # Low health
                "location": "tavern",
            },
            "npcs": [
                {"name": "Healer", "location": "tavern", "services": ["healing"]},
                {"name": "Barkeep Bob", "location": "tavern", "services": ["drinks"]},
            ],
            "available_actions": ["talk", "buy", "rest", "heal"],
        }

        mock_service = MockLLMService()
        mock_service.queue_response(
            {
                "action": "heal",
                "target": "Healer",
                "reasoning": "My health is low, I should seek healing",
            }
        )

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            ai_player = AIPlayer()

            decision = await ai_player.make_decision(game_state)

            assert decision["action"] == "heal"

            # Verify that game state context was included in LLM prompt
            last_call = mock_service.get_last_call()
            prompt = last_call["prompt"]

            # Should include health information
            assert "health" in prompt.lower() or "50" in prompt
            # Should include available NPCs
            assert "Healer" in prompt or "healer" in prompt

    @pytest.mark.asyncio
    async def test_ai_player_session_isolation(self):
        """Test that AI player sessions are properly isolated."""
        manager = AIPlayerManager()

        # Create two different sessions
        personality1 = AIPlayerPersonality(
            name="Explorer A", traits=["adventurous"], goals=["explore"]
        )

        personality2 = AIPlayerPersonality(
            name="Explorer B", traits=["cautious"], goals=["survive"]
        )

        session1 = manager.create_session(personality1, "AI_A")
        session2 = manager.create_session(personality2, "AI_B")

        # Verify sessions are different instances
        assert session1 is not session2
        assert session1.name != session2.name
        assert session1.ai_player is not session2.ai_player

        # Verify personalities are isolated
        assert (
            session1.ai_player.personality.name != session2.ai_player.personality.name
        )
        assert (
            session1.ai_player.personality.traits
            != session2.ai_player.personality.traits
        )

        # Cleanup
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_ai_player_performance_monitoring(
        self, clean_game_state, performance_monitor
    ):
        """Test AI player performance under load."""
        mock_service = MockLLMService()
        mock_service.default_response = {
            "action": "wait",
            "reasoning": "Observing the situation",
        }

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            ai_player = AIPlayer()

            # Measure performance of multiple decisions
            with performance_monitor.measure("ai_decision_making"):
                decisions = []
                for i in range(10):
                    decision = await ai_player.make_decision(clean_game_state)
                    decisions.append(decision)

            # Verify all decisions completed
            assert len(decisions) == 10
            assert all(d is not None for d in decisions)

            # Check performance metrics
            performance_monitor.assert_performance_thresholds(
                {
                    "max_execution_time": 2.0,  # Should complete 10 decisions in under 2 seconds
                    "max_memory_mb": 50,  # Should not use excessive memory
                }
            )

    @pytest.mark.asyncio
    async def test_ai_player_concurrent_sessions(self):
        """Test multiple AI player sessions running concurrently."""
        manager = AIPlayerManager()
        mock_service = MockLLMService()

        # Queue responses for multiple AIs
        responses = [
            {"action": "greet", "reasoning": "Being friendly"},
            {"action": "observe", "reasoning": "Watching carefully"},
            {"action": "rest", "reasoning": "Taking a break"},
        ]

        for response in responses:
            mock_service.queue_response(response)

        with patch("core.llm.narrator.LLMService", return_value=mock_service):
            # Create multiple sessions
            sessions = []
            for i in range(3):
                personality = AIPlayerPersonality(
                    name=f"AI_{i}", traits=["active"], goals=["participate"]
                )
                session = manager.create_session(personality, f"ConcurrentAI_{i}")
                sessions.append(session)

            # Create simple game state
            game_state = {
                "player": {"name": "TestPlayer", "location": "tavern"},
                "npcs": [{"name": "NPC", "location": "tavern"}],
            }

            # Run concurrent decisions
            tasks = []
            for session in sessions:
                task = session.ai_player.make_decision(game_state)
                tasks.append(task)

            decisions = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all sessions completed successfully
            assert len(decisions) == 3
            assert all(not isinstance(d, Exception) for d in decisions)
            assert all(d is not None and "action" in d for d in decisions)

            # Verify LLM service was called for each session
            assert mock_service.get_call_count() == 3

        # Cleanup
        await manager.cleanup()


class TestAIPlayerAPIIntegration:
    """Integration tests for AI Player API endpoints."""

    @pytest.mark.asyncio
    async def test_ai_player_api_session_creation(self, isolated_db_session):
        """Test AI player session creation via API."""
        from api.routers.ai_player import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        with TestClient(app) as client:
            # Test session creation
            response = client.post(
                "/ai-player/session",
                json={
                    "personality": {
                        "name": "Test AI",
                        "traits": ["curious", "friendly"],
                        "goals": ["explore"],
                    },
                    "name": "APITestAI",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert_api_response_format(data, "success")
            assert "session_id" in data["data"]

    @pytest.mark.asyncio
    async def test_ai_player_api_decision_making(self):
        """Test AI player decision making via API."""
        # This would test the full API endpoint for AI decision making
        # Implementation depends on actual API structure
        pass

    @pytest.mark.asyncio
    async def test_ai_player_api_error_handling(self):
        """Test AI player API error handling."""
        from api.routers.ai_player import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        with TestClient(app) as client:
            # Test invalid session creation
            response = client.post(
                "/ai-player/session", json={"invalid_field": "invalid_value"}
            )

            assert response.status_code == 422  # Validation error


class TestAIPlayerResourceManagement:
    """Test AI Player resource cleanup and management."""

    @pytest.mark.asyncio
    async def test_ai_player_http_session_cleanup(self):
        """Test that HTTP sessions are properly cleaned up."""
        ai_player = AIPlayer()

        # Mock the session creation
        mock_session = Mock()
        mock_session.closed = False
        mock_session.close = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            # Trigger session creation
            session = await ai_player._get_session()
            assert session is mock_session

            # Cleanup
            await ai_player.cleanup()

            # Verify session was closed
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_player_manager_cleanup(self):
        """Test AI player manager cleanup functionality."""
        manager = AIPlayerManager()

        # Create multiple sessions
        personalities = [
            AIPlayerPersonality(name=f"AI_{i}", traits=["test"], goals=["test"])
            for i in range(3)
        ]

        sessions = []
        for i, personality in enumerate(personalities):
            session = manager.create_session(personality, f"TestAI_{i}")
            sessions.append(session)

        # Verify sessions were created
        assert len(manager.active_sessions) == 3

        # Cleanup manager
        await manager.cleanup()

        # Verify all sessions were cleaned up
        assert len(manager.active_sessions) == 0

        # Verify individual sessions were deactivated
        for session in sessions:
            assert not session.is_active
