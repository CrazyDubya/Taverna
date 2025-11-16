import unittest
from unittest.mock import MagicMock, patch
from core.player import PlayerState
from games.gambling import GamblingGames, GameResult, GameType
from games.gambling_manager import GamblingManager


class TestGamblingGames(unittest.TestCase):
    def setUp(self):
        self.games = GamblingGames()

    def test_play_dice_win_low(self):
        with patch("random.randint", return_value=2):  # Force a low roll (1-3)
            result = self.games.play_dice(10, 1)  # Bet 10 on low
            self.assertTrue(result.success)
            self.assertEqual(result.winnings, 20)  # 2x bet
            self.assertIn("win", result.message.lower())

    def test_play_dice_win_high(self):
        with patch("random.randint", return_value=5):  # Force a high roll (4-6)
            result = self.games.play_dice(10, 2)  # Bet 10 on high
            self.assertTrue(result.success)
            self.assertEqual(result.winnings, 20)
            self.assertIn("win", result.message.lower())

    def test_play_coin_flip_win(self):
        with patch("random.choice", return_value="heads"):
            result = self.games.play_coin_flip(10, "heads")
            self.assertTrue(result.success)
            self.assertEqual(result.winnings, 20)  # 2x bet
            self.assertIn("win", result.message.lower())

    def test_play_high_card_win(self):
        with patch("random.randint", side_effect=[10, 5]):  # Player 10, House 5
            result = self.games.play_high_card(10)
            self.assertTrue(result.success)
            self.assertEqual(result.winnings, 15)  # 1.5x bet
            self.assertIn("win", result.message.lower())


class TestGamblingManager(unittest.TestCase):
    def setUp(self):
        self.manager = GamblingManager()
        self.player = PlayerState()
        self.player.gold = 100

    def test_play_game_insufficient_funds(self):
        self.player.gold = 5
        result = self.manager.play_game(self.player, "dice", 10, guess=1)
        self.assertFalse(result["success"])
        self.assertIn("don't have enough gold", result["message"])

    @patch("games.gambling.GamblingGames.play_dice")
    def test_play_game_dice(self, mock_play_dice):
        # Setup mock
        mock_play_dice.return_value = GameResult(
            success=True,
            winnings=20,
            message="You win!",
            details={"roll": 2, "multiplier": 2},
        )

        result = self.manager.play_game(self.player, "dice", 10, guess=1)
        self.assertTrue(result["success"])
        # 100 - 10 + 20 = 110 (but our mock returns +20 net)
        self.assertEqual(self.player.gold, 120)
        self.assertEqual(result["gold_change"], 20)

    def test_get_player_stats(self):
        # Play some games
        with patch("random.randint", return_value=2):  # Force win
            self.manager.play_game(self.player, "dice", 10, guess=1)
        with patch("random.randint", return_value=5):  # Force loss
            self.manager.play_game(self.player, "dice", 10, guess=1)

        stats = self.manager.get_player_stats(self.player.id)
        self.assertEqual(stats["total_games_played"], 2)
        self.assertEqual(stats["games"]["dice"]["games_played"], 2)
        self.assertEqual(stats["games"]["dice"]["total_won"], 20)
        self.assertEqual(stats["games"]["dice"]["total_lost"], 10)


if __name__ == "__main__":
    unittest.main()
