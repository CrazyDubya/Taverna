from typing import Dict, Any, Optional, List, Tuple
from dataclasses import asdict
from living_rusted_tankard.core.player import PlayerState
from living_rusted_tankard.games.gambling import GamblingGames, GameResult, GameType

class GamblingManager:
    """Manages gambling interactions and state in the game."""
    
    def __init__(self):
        self.games = GamblingGames()
        self.current_games: Dict[str, Dict[str, Any]] = {}
    
    def get_available_games(self) -> List[Dict[str, Any]]:
        """Get a list of available gambling games."""
        return self.games.get_available_games()
    
    def play_game(self, player: PlayerState, game_type: str, bet: int, **kwargs) -> Dict[str, Any]:
        """Play a gambling game.
        
        Args:
            player: The player playing the game
            game_type: Type of game to play
            bet: Amount of gold to bet
            **kwargs: Additional game-specific arguments
            
        Returns:
            Dict with game results and updated player state
        """
        # Validate player can afford the bet
        if player.gold < bet:
            return {
                'success': False,
                'message': "You don't have enough gold for that bet!"
            }
        
        # Play the selected game
        result = None
        game_type_enum = GameType(game_type)
        
        try:
            if game_type_enum == GameType.DICE:
                guess = kwargs.get('guess')
                if guess not in [1, 2]:
                    return {'success': False, 'message': "Invalid guess. Use 1 for low (1-3) or 2 for high (4-6)."}
                result = self.games.play_dice(bet, guess)
                
            elif game_type_enum == GameType.COIN_FLIP:
                guess = kwargs.get('guess', '').lower()
                if guess not in ['heads', 'tails']:
                    return {'success': False, 'message': "Please guess 'heads' or 'tails'!"}
                result = self.games.play_coin_flip(bet, guess)
                
            elif game_type_enum == GameType.HIGH_CARD:
                result = self.games.play_high_card(bet)
                
            else:
                return {'success': False, 'message': "Unknown game type!"}
                
            # Update player's gold
            player.gold += result.winnings
            
            # Prepare response
            response = {
                'success': result.success,
                'message': result.message,
                'gold_change': result.winnings,
                'new_balance': player.gold,
                'game_type': game_type,
                'details': dict(result.details) if result.details else {}
            }
            
            # Track game in current games (for potential leaderboards or stats)
            self._track_game(player.id, game_type, bet, result)
            
            return response
            
        except ValueError as e:
            return {'success': False, 'message': str(e)}
    
    def _track_game(self, player_id: str, game_type: str, bet: int, result: GameResult) -> None:
        """Track game results for statistics."""
        game_key = f"{player_id}:{game_type}"
        if game_key not in self.current_games:
            self.current_games[game_key] = {
                'games_played': 0,
                'total_won': 0,
                'total_lost': 0,
                'biggest_win': 0,
                'biggest_loss': 0
            }
        
        stats = self.current_games[game_key]
        stats['games_played'] += 1
        
        if result.winnings > 0:
            stats['total_won'] += result.winnings
            stats['biggest_win'] = max(stats['biggest_win'], result.winnings)
        elif result.winnings < 0:
            stats['total_lost'] += abs(result.winnings)
            stats['biggest_loss'] = max(stats['biggest_loss'], abs(result.winnings))
    
    def get_player_stats(self, player_id: str) -> Dict[str, Any]:
        """Get gambling statistics for a player."""
        stats = {
            'total_games_played': 0,
            'total_won': 0,
            'total_lost': 0,
            'net_profit': 0,
            'games': {}
        }
        
        # Filter games for this player
        player_games = {k: v for k, v in self.current_games.items() if k.startswith(f"{player_id}:")}
        
        for game_key, game_stats in player_games.items():
            game_type = game_key.split(':', 1)[1]
            stats['games'][game_type] = game_stats
            stats['total_games_played'] += game_stats['games_played']
            stats['total_won'] += game_stats['total_won']
            stats['total_lost'] += game_stats['total_lost']
        
        stats['net_profit'] = stats['total_won'] - stats['total_lost']
        return stats
