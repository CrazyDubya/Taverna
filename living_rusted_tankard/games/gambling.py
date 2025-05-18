from typing import Dict, Tuple, Optional, List, Any
import random
from dataclasses import dataclass
from enum import Enum, auto

class GameType(Enum):
    DICE = "dice"
    COIN_FLIP = "coin_flip"
    HIGH_CARD = "high_card"

@dataclass
class GameResult:
    success: bool
    winnings: int
    message: str
    details: Optional[Dict] = None

class GamblingGames:
    """Handles all gambling mini-games in the tavern."""
    
    @staticmethod
    def play_dice(bet: int, guess: int) -> GameResult:
        """Play a dice game where player guesses high/low.
        
        Args:
            bet: Amount of gold wagered
            guess: 1 for low (1-3), 2 for high (4-6)
            
        Returns:
            GameResult with outcome and winnings
        """
        if bet <= 0:
            return GameResult(False, 0, "Bet must be positive!")
            
        roll = random.randint(1, 6)
        win = (guess == 1 and roll <= 3) or (guess == 2 and roll >= 4)
        
        if win:
            winnings = bet * 2
            return GameResult(
                True,
                winnings,
                f"The die shows {roll}! You win {winnings} gold!",
                {"roll": roll, "multiplier": 2}
            )
        else:
            return GameResult(
                False,
                -bet,
                f"The die shows {roll}. Better luck next time!",
                {"roll": roll}
            )
    
    @staticmethod
    def play_coin_flip(bet: int, guess: str) -> GameResult:
        """Simple coin flip game with 50/50 odds.
        
        Args:
            bet: Amount of gold wagered
            guess: 'heads' or 'tails'
            
        Returns:
            GameResult with outcome and winnings
        """
        if bet <= 0:
            return GameResult(False, 0, "Bet must be positive!")
            
        if guess.lower() not in ['heads', 'tails']:
            return GameResult(False, 0, "Please guess 'heads' or 'tails'!")
            
        result = random.choice(['heads', 'tails'])
        win = guess.lower() == result
        
        if win:
            winnings = bet * 2
            return GameResult(
                True,
                winnings,
                f"It's {result}! You win {winnings} gold!",
                {"result": result, "multiplier": 2}
            )
        else:
            return GameResult(
                False,
                -bet,
                f"It's {result}. Better luck next time!",
                {"result": result}
            )
    
    @staticmethod
    def play_high_card(bet: int) -> GameResult:
        """High card game against the house.
        
        Args:
            bet: Amount of gold wagered
            
        Returns:
            GameResult with outcome and winnings
        """
        if bet <= 0:
            return GameResult(False, 0, "Bet must be positive!")
            
        player_card = random.randint(1, 13)
        house_card = random.randint(1, 13)
        
        if player_card > house_card:
            winnings = int(bet * 1.5)
            return GameResult(
                True,
                winnings,
                f"You drew a {player_card} vs house's {house_card}. You win {winnings} gold!",
                {"player_card": player_card, "house_card": house_card, "multiplier": 1.5}
            )
        elif player_card < house_card:
            return GameResult(
                False,
                -bet,
                f"You drew a {player_card} vs house's {house_card}. Better luck next time!",
                {"player_card": player_card, "house_card": house_card}
            )
        else:
            return GameResult(
                True,
                0,
                f"It's a tie! Both drew {player_card}. Your bet is returned.",
                {"player_card": player_card, "house_card": house_card}
            )
    
    @classmethod
    def get_available_games(cls) -> List[Dict[str, Any]]:
        """Get a list of available gambling games and their rules."""
        return [
            {
                'id': 'dice',
                'name': 'Dice Game',
                'description': 'Guess high (4-6) or low (1-3) on a 6-sided die.',
                'min_bet': 1,
                'max_bet': 100,
                'payout': '2x bet'
            },
            {
                'id': 'coin_flip',
                'name': 'Coin Flip',
                'description': 'Heads or tails - 50/50 chance to double your bet.',
                'min_bet': 1,
                'max_bet': 50,
                'payout': '2x bet'
            },
            {
                'id': 'high_card',
                'name': 'High Card',
                'description': 'Draw a card higher than the house to win 1.5x your bet!',
                'min_bet': 5,
                'max_bet': 200,
                'payout': '1.5x bet (win only)'
            }
        ]
