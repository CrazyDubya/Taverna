"""Tests for the Economy class."""

import pytest
from unittest.mock import patch


class TestEconomy:
    def test_gamble_success(self, economy, player_state):
        """Test a successful gambling attempt."""
        initial_gold = player_state.gold

        with patch("random.random", return_value=0.5):  # Will win (0.5 < 0.6)
            won, winnings = economy.gamble(player_state, 10)

        assert won is True
        assert winnings == 10
        assert player_state.gold == initial_gold + 10

    def test_gamble_loss(self, economy, player_state):
        """Test a failed gambling attempt."""
        initial_gold = player_state.gold

        with patch("random.random", return_value=0.7):  # Will lose (0.7 > 0.6)
            won, winnings = economy.gamble(player_state, 10)

        assert won is False
        assert winnings == -10
        assert player_state.gold == initial_gold - 10

    def test_gamble_insufficient_funds(self, economy, player_state):
        """Test gambling with insufficient funds raises an error."""
        # Try to bet more than the player has
        with pytest.raises(ValueError, match="cannot afford"):
            economy.gamble(player_state, player_state.gold + 10)

    def test_gamble_invalid_wager(self, economy, player_state):
        """Test that zero or negative wagers are rejected."""
        with pytest.raises(ValueError, match="must be positive"):
            economy.gamble(player_state, 0)

        with pytest.raises(ValueError, match="must be positive"):
            economy.gamble(player_state, -10)

    @patch("random.choice")
    def test_get_side_job(self, mock_choice, economy, player_state):
        """Test getting a side job."""
        # Mock the job selection
        test_job = ("Test job", 15)
        mock_choice.return_value = test_job

        job = economy.get_side_job(player_state)
        assert job == test_job

    def test_get_side_job_min_reward(self, economy, player_state):
        """Test that side jobs respect minimum reward threshold."""
        # Set player's gold to 100, so min_reward should be 10 (10% of 100)
        player_state.gold = 100

        # This job's reward is too low (5 < 10)
        with patch("random.choice", return_value=("Low paying job", 5)):
            job = economy.get_side_job(player_state)
            assert job is None  # Should be filtered out

        # This job's reward is sufficient (15 > 10)
        with patch("random.choice", return_value=("Good job", 15)):
            job = economy.get_side_job(player_state)
            assert job is not None

    def test_complete_side_job(self, economy, player_state):
        """Test completing a side job rewards the player."""
        initial_gold = player_state.gold
        job = ("Test job", 20)

        economy.complete_side_job(player_state, job)

        assert player_state.gold == initial_gold + 20
