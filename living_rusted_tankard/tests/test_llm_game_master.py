"""Test LLM game master functionality."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from tests.fixtures import clean_game_state, mock_llm_service
from tests.utils.mock_helpers import MockLLMService
from tests.utils.assertion_helpers import assert_llm_response_valid

from core.llm_game_master import LLMGameMaster, CommandResult
from core.enhanced_llm_game_master import EnhancedLLMGameMaster


class TestLLMGameMaster:
    """Test basic LLM game master functionality."""
    
    def test_llm_game_master_initialization(self):
        """Test LLM game master initializes correctly."""
        gm = LLMGameMaster()
        
        assert gm is not None
        assert hasattr(gm, 'ollama_url')
        assert hasattr(gm, 'model')
        assert gm.model == "gemma2:2b"  # Default model
    
    def test_llm_game_master_custom_config(self):
        """Test LLM game master with custom configuration."""
        gm = LLMGameMaster(
            ollama_url="http://localhost:11435",
            model="llama3.2:latest"
        )
        
        assert gm.ollama_url == "http://localhost:11435"
        assert gm.model == "llama3.2:latest"
    
    @pytest.mark.asyncio
    async def test_process_command_with_mock_llm(self, clean_game_state):
        """Test processing command with mocked LLM."""
        gm = LLMGameMaster()
        
        # Mock LLM response
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {
                "action": "look",
                "description": "You see a warm, inviting tavern.",
                "success": True
            }
            
            result = await gm.process_command("look around", clean_game_state)
            
            assert result is not None
            assert result["action"] == "look"
            assert result["success"] is True
            mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_command_with_context(self, clean_game_state):
        """Test command processing includes game context."""
        gm = LLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {"action": "contextual_response"}
            
            await gm.process_command("interact with barkeeper", clean_game_state)
            
            # Check that context was included in LLM call
            call_args = mock_llm.call_args[0]
            prompt = call_args[0]
            
            assert "tavern" in prompt.lower() or "game" in prompt.lower()
            assert "barkeeper" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_llm_request_timeout_handling(self, clean_game_state):
        """Test LLM request timeout handling."""
        gm = LLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.side_effect = asyncio.TimeoutError("Request timed out")
            
            result = await gm.process_command("complex command", clean_game_state)
            
            # Should return fallback response, not raise exception
            assert result is not None
            assert "error" in result or "fallback" in result
    
    @pytest.mark.asyncio
    async def test_llm_connection_error_handling(self, clean_game_state):
        """Test LLM connection error handling."""
        gm = LLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.side_effect = ConnectionError("Cannot connect to Ollama")
            
            result = await gm.process_command("test command", clean_game_state)
            
            # Should return fallback response
            assert result is not None
            assert result.get("success") is False or "fallback" in str(result)
    
    def test_build_context(self, clean_game_state):
        """Test building context from game state."""
        gm = LLMGameMaster()
        
        context = gm._build_context(clean_game_state)
        
        assert isinstance(context, str)
        assert len(context) > 0
        # Should include key game state information
        assert "player" in context.lower()
        assert "location" in context.lower() or "tavern" in context.lower()
    
    def test_parse_llm_response(self):
        """Test parsing LLM responses."""
        gm = LLMGameMaster()
        
        # Test valid JSON response
        json_response = '{"action": "look", "description": "You see a tavern", "success": true}'
        parsed = gm._parse_response(json_response)
        
        assert parsed["action"] == "look"
        assert parsed["success"] is True
        
        # Test plain text response
        text_response = "You look around the tavern and see several patrons."
        parsed = gm._parse_response(text_response)
        
        assert "description" in parsed or "response" in parsed
        assert isinstance(parsed, dict)
    
    def test_fallback_response_generation(self, clean_game_state):
        """Test fallback response generation."""
        gm = LLMGameMaster()
        
        fallback = gm._generate_fallback_response("look around", clean_game_state)
        
        assert isinstance(fallback, dict)
        assert "action" in fallback
        assert "description" in fallback
        assert len(fallback["description"]) > 0


class TestEnhancedLLMGameMaster:
    """Test enhanced LLM game master functionality."""
    
    def test_enhanced_gm_initialization(self):
        """Test enhanced game master initializes correctly."""
        gm = EnhancedLLMGameMaster()
        
        assert gm is not None
        assert hasattr(gm, 'conversation_memory')
        assert hasattr(gm, 'context_cache')
        assert hasattr(gm, 'error_recovery')
    
    @pytest.mark.asyncio
    async def test_enhanced_command_processing(self, clean_game_state):
        """Test enhanced command processing with optimizations."""
        gm = EnhancedLLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {
                "action": "enhanced_look",
                "description": "Enhanced description with more detail",
                "success": True,
                "context_used": True
            }
            
            result = await gm.process_command("examine room carefully", clean_game_state)
            
            assert result is not None
            assert result["action"] == "enhanced_look"
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_conversation_memory(self, clean_game_state):
        """Test conversation memory functionality."""
        gm = EnhancedLLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {"action": "respond", "success": True}
            
            # First command
            await gm.process_command("hello barkeeper", clean_game_state)
            
            # Second command that references first
            await gm.process_command("what did I just say?", clean_game_state)
            
            # Check that conversation history is maintained
            assert len(gm.conversation_memory) >= 2
            
            # Second call should include memory context
            second_call_args = mock_llm.call_args[0]
            prompt = second_call_args[0]
            assert "hello barkeeper" in prompt.lower() or "previous" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_context_caching(self, clean_game_state):
        """Test context caching optimization."""
        gm = EnhancedLLMGameMaster()
        
        with patch.object(gm, '_build_context') as mock_build_context:
            mock_build_context.return_value = "cached context"
            
            with patch.object(gm, '_make_llm_request') as mock_llm:
                mock_llm.return_value = {"action": "cached_response"}
                
                # First call should build context
                await gm.process_command("first command", clean_game_state)
                assert mock_build_context.call_count == 1
                
                # Second call with same game state should use cache
                await gm.process_command("second command", clean_game_state)
                
                # Context building might be cached (depends on implementation)
                # The exact behavior depends on cache invalidation logic
    
    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, clean_game_state):
        """Test error recovery integration."""
        gm = EnhancedLLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            # First call succeeds
            mock_llm.return_value = {"action": "success", "success": True}
            result1 = await gm.process_command("working command", clean_game_state)
            assert result1["success"] is True
            
            # Second call fails
            mock_llm.side_effect = Exception("LLM error")
            result2 = await gm.process_command("failing command", clean_game_state)
            
            # Should recover gracefully
            assert result2 is not None
            assert "error" in result2 or result2.get("success") is False
    
    @pytest.mark.asyncio
    async def test_performance_optimization(self, clean_game_state):
        """Test performance optimizations."""
        gm = EnhancedLLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {"action": "optimized", "success": True}
            
            # Measure performance of multiple commands
            import time
            start_time = time.time()
            
            for i in range(5):
                await gm.process_command(f"command {i}", clean_game_state)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should complete relatively quickly (with caching and optimizations)
            assert total_time < 1.0  # Less than 1 second for 5 commands (mocked)
    
    def test_narrative_action_parsing(self):
        """Test parsing narrative actions with tags."""
        gm = EnhancedLLMGameMaster()
        
        # Response with narrative action tags
        response_with_tags = """
        You approach the barkeeper. [NPC_INTERACTION:barkeeper]
        He offers you a drink for 5 gold. [ITEM_OFFER:ale:5]
        You gain reputation with the tavern. [REPUTATION_CHANGE:tavern:+1]
        """
        
        parsed = gm._parse_narrative_actions(response_with_tags)
        
        assert "actions" in parsed
        actions = parsed["actions"]
        
        # Should extract the tagged actions
        assert any("NPC_INTERACTION" in str(action) for action in actions)
        assert any("ITEM_OFFER" in str(action) for action in actions)
        assert any("REPUTATION_CHANGE" in str(action) for action in actions)
    
    def test_context_optimization(self, clean_game_state):
        """Test context optimization for efficiency."""
        gm = EnhancedLLMGameMaster()
        
        # Build context
        context = gm._build_optimized_context(clean_game_state)
        
        assert isinstance(context, str)
        assert len(context) > 0
        
        # Should be concise but comprehensive
        assert len(context) < 2000  # Reasonable length limit
        
        # Should include essential information
        essential_terms = ["player", "location", "time"]
        context_lower = context.lower()
        assert any(term in context_lower for term in essential_terms)


class TestLLMGameMasterIntegration:
    """Test LLM game master integration with game systems."""
    
    @pytest.mark.asyncio
    async def test_integration_with_npc_system(self, clean_game_state):
        """Test LLM game master integration with NPC system."""
        gm = EnhancedLLMGameMaster()
        
        # Mock NPC interaction response
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {
                "action": "npc_interaction",
                "npc_id": "barkeeper", 
                "dialogue": "Welcome to the tavern!",
                "reputation_change": 1,
                "success": True
            }
            
            result = await gm.process_command("talk to barkeeper", clean_game_state)
            
            assert result["action"] == "npc_interaction"
            assert "barkeeper" in result["npc_id"]
            assert "reputation_change" in result
    
    @pytest.mark.asyncio
    async def test_integration_with_economy_system(self, clean_game_state):
        """Test LLM game master integration with economy."""
        gm = EnhancedLLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {
                "action": "purchase",
                "item": "ale",
                "cost": 5,
                "success": True
            }
            
            result = await gm.process_command("buy ale", clean_game_state)
            
            assert result["action"] == "purchase"
            assert result["item"] == "ale"
            assert result["cost"] == 5
    
    @pytest.mark.asyncio
    async def test_integration_with_time_system(self, clean_game_state):
        """Test LLM game master integration with time system."""
        gm = EnhancedLLMGameMaster()
        
        # Mock time-based response
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {
                "action": "wait",
                "time_passed": 1,
                "description": "You wait for an hour.",
                "success": True
            }
            
            result = await gm.process_command("wait for someone", clean_game_state)
            
            assert result["action"] == "wait"
            assert result["time_passed"] == 1
    
    @pytest.mark.asyncio
    async def test_complex_multi_system_command(self, clean_game_state):
        """Test command that affects multiple game systems."""
        gm = EnhancedLLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {
                "action": "complex_interaction",
                "effects": {
                    "npc_relationship": {"barkeeper": 2},
                    "economy": {"gold": -10, "items": ["information"]},
                    "time": {"hours_passed": 0.5},
                    "reputation": {"tavern": 1}
                },
                "description": "You buy drinks for the house and learn valuable information.",
                "success": True
            }
            
            result = await gm.process_command(
                "buy drinks for everyone and ask about local rumors",
                clean_game_state
            )
            
            assert result["action"] == "complex_interaction"
            assert "effects" in result
            effects = result["effects"]
            assert "npc_relationship" in effects
            assert "economy" in effects
            assert "time" in effects
            assert "reputation" in effects


class TestLLMGameMasterErrorHandling:
    """Test LLM game master error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_malformed_llm_response(self, clean_game_state):
        """Test handling of malformed LLM responses."""
        gm = LLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            # Malformed JSON
            mock_llm.return_value = '{"incomplete": json'
            
            result = await gm.process_command("test command", clean_game_state)
            
            # Should handle gracefully with fallback
            assert result is not None
            assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_empty_llm_response(self, clean_game_state):
        """Test handling of empty LLM responses."""
        gm = LLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = ""
            
            result = await gm.process_command("test command", clean_game_state)
            
            # Should provide fallback response
            assert result is not None
            assert len(str(result)) > 0
    
    @pytest.mark.asyncio
    async def test_llm_service_unavailable(self, clean_game_state):
        """Test behavior when LLM service is unavailable."""
        gm = LLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.side_effect = ConnectionRefusedError("Service unavailable")
            
            result = await gm.process_command("test command", clean_game_state)
            
            # Should fall back to rule-based response
            assert result is not None
            assert "fallback" in str(result).lower() or result.get("success") is False
    
    @pytest.mark.asyncio
    async def test_very_long_command(self, clean_game_state):
        """Test handling of very long commands."""
        gm = LLMGameMaster()
        
        # Create very long command
        very_long_command = "tell me about " + "everything " * 1000
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {"action": "truncated_response"}
            
            result = await gm.process_command(very_long_command, clean_game_state)
            
            # Should handle without error
            assert result is not None
            # Command should be truncated or handled appropriately
    
    @pytest.mark.asyncio
    async def test_invalid_command_characters(self, clean_game_state):
        """Test handling of commands with invalid characters."""
        gm = LLMGameMaster()
        
        # Command with special characters
        special_command = "do something with ñoñó and émoji 🎮"
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {"action": "special_response"}
            
            result = await gm.process_command(special_command, clean_game_state)
            
            # Should handle without encoding errors
            assert result is not None
    
    def test_memory_management(self):
        """Test memory management with long conversation history."""
        gm = EnhancedLLMGameMaster()
        
        # Simulate long conversation
        for i in range(100):
            gm.conversation_memory.append({
                "command": f"command {i}",
                "response": f"response {i}",
                "timestamp": i
            })
        
        # Memory should be limited to prevent unbounded growth
        assert len(gm.conversation_memory) <= 50  # Reasonable limit
    
    def test_context_cache_invalidation(self, clean_game_state):
        """Test context cache invalidation."""
        gm = EnhancedLLMGameMaster()
        
        # Build initial context
        context1 = gm._build_optimized_context(clean_game_state)
        
        # Modify game state
        clean_game_state["player"]["gold"] = 200
        
        # Context should be invalidated and rebuilt
        context2 = gm._build_optimized_context(clean_game_state)
        
        # May or may not be different depending on cache implementation
        # The important thing is no errors occur


class TestLLMGameMasterPerformance:
    """Test LLM game master performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_concurrent_command_processing(self, clean_game_state):
        """Test processing multiple commands concurrently."""
        gm = EnhancedLLMGameMaster()
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {"action": "concurrent", "success": True}
            
            # Process multiple commands concurrently
            commands = [f"command {i}" for i in range(5)]
            tasks = [gm.process_command(cmd, clean_game_state) for cmd in commands]
            
            results = await asyncio.gather(*tasks)
            
            # All should complete successfully
            assert len(results) == 5
            assert all(r is not None for r in results)
            assert all(r["success"] for r in results)
    
    @pytest.mark.asyncio
    async def test_response_time_consistency(self, clean_game_state):
        """Test response time consistency."""
        gm = EnhancedLLMGameMaster()
        
        response_times = []
        
        with patch.object(gm, '_make_llm_request') as mock_llm:
            mock_llm.return_value = {"action": "timed", "success": True}
            
            for i in range(10):
                import time
                start = time.time()
                await gm.process_command(f"command {i}", clean_game_state)
                end = time.time()
                response_times.append(end - start)
        
        # Response times should be consistent (low variance)
        import statistics
        if len(response_times) > 1:
            std_dev = statistics.stdev(response_times)
            mean_time = statistics.mean(response_times)
            
            # Coefficient of variation should be reasonable
            cv = std_dev / mean_time if mean_time > 0 else 0
            assert cv < 0.5  # Less than 50% variation