"""
Mini-games and challenges for the Pixel Plaza Token game.
These provide additional ways for players to earn tokens, resources, and experience.
"""

import random
import logging
import json
from datetime import datetime, timedelta
from models import User, GameState, Transaction, MiniGameResult
from app import db
import config

logger = logging.getLogger(__name__)

class MiniGames:
    """Handles all mini-game interactions and logic."""
    
    def __init__(self):
        """Initialize mini-games."""
        logger.info("Initializing mini-games system")
        self.games = {
            'pixel_match': self._pixel_match_game,
            'token_puzzle': self._token_puzzle_game,
            'resource_rush': self._resource_rush_game,
            'gem_hunter': self._gem_hunter_game,
            'pattern_predictor': self._pattern_predictor_game
        }
        
    def get_available_games(self, user, game_state):
        """Get list of available games for a user.
        
        Args:
            user: User model instance
            game_state: GameState model instance
            
        Returns:
            List of game info dictionaries with name, description, and cooldown
        """
        now = datetime.utcnow()
        available_games = []
        
        # Get user's most recent mini-game results
        recent_games = MiniGameResult.query.filter_by(
            user_id=user.id
        ).order_by(MiniGameResult.played_at.desc()).all()
        
        # Track when each game was last played
        last_played = {}
        for result in recent_games:
            if result.game_type not in last_played:
                last_played[result.game_type] = result.played_at
        
        # Check availability for each game
        for game_type, game_func in self.games.items():
            game_info = {
                'type': game_type,
                'name': self._get_game_name(game_type),
                'description': self._get_game_description(game_type),
                'available': True,
                'cooldown_remaining': 0
            }
            
            # Check if game is on cooldown
            if game_type in last_played:
                time_since_played = now - last_played[game_type]
                cooldown_seconds = config.MINI_GAME_COOLDOWN_HOURS * 3600
                
                if time_since_played.total_seconds() < cooldown_seconds:
                    cooldown_remaining = cooldown_seconds - time_since_played.total_seconds()
                    hours = int(cooldown_remaining // 3600)
                    minutes = int((cooldown_remaining % 3600) // 60)
                    
                    game_info['available'] = False
                    game_info['cooldown_remaining'] = cooldown_remaining
                    game_info['cooldown_text'] = f"{hours}h {minutes}m"
            
            available_games.append(game_info)
            
        return available_games
    
    def play_game(self, user, game_state, game_type, game_data=None):
        """Play a mini-game.
        
        Args:
            user: User model instance
            game_state: GameState model instance
            game_type: String indicating which game to play
            game_data: Optional dict with game-specific parameters
            
        Returns:
            dict with game results
        """
        if game_type not in self.games:
            return {
                "success": False,
                "message": f"Unknown mini-game: {game_type}"
            }
        
        # Check if game is on cooldown
        now = datetime.utcnow()
        last_game = MiniGameResult.query.filter_by(
            user_id=user.id,
            game_type=game_type
        ).order_by(MiniGameResult.played_at.desc()).first()
        
        if last_game:
            time_since_played = now - last_game.played_at
            cooldown_seconds = config.MINI_GAME_COOLDOWN_HOURS * 3600
            
            if time_since_played.total_seconds() < cooldown_seconds:
                cooldown_remaining = cooldown_seconds - time_since_played.total_seconds()
                hours = int(cooldown_remaining // 3600)
                minutes = int((cooldown_remaining % 3600) // 60)
                
                return {
                    "success": False,
                    "message": f"This game is on cooldown. Available again in {hours}h {minutes}m"
                }
        
        # Call the appropriate game function
        if game_data is None:
            game_data = {}
            
        result = self.games[game_type](user, game_state, game_data)
        
        # Record the result
        game_result = MiniGameResult(
            user_id=user.id,
            game_type=game_type,
            score=result.get('score', 0),
            reward_tokens=result.get('reward_tokens', 0),
            reward_pixels=result.get('reward_pixels', 0),
            reward_materials=result.get('reward_materials', 0),
            reward_gems=result.get('reward_gems', 0),
            reward_xp=result.get('reward_xp', 0),
            game_data=json.dumps(result.get('game_data', {})),
            played_at=now
        )
        db.session.add(game_result)
        
        # Update user's game state with rewards
        if result['success']:
            game_state.token_balance += result.get('reward_tokens', 0)
            game_state.pixels += result.get('reward_pixels', 0)
            game_state.materials += result.get('reward_materials', 0)
            game_state.gems += result.get('reward_gems', 0)
            game_state.experience += result.get('reward_xp', 0)
            
            # Check for level up
            if game_state.experience >= game_state.level * 100:
                game_state.experience -= game_state.level * 100
                game_state.level += 1
                result['level_up'] = True
            else:
                result['level_up'] = False
            
            # Record transaction
            transaction = Transaction(
                user_id=user.id,
                type='mini_game',
                amount=result.get('reward_tokens', 0),
                description=f"Mini-game reward: {self._get_game_name(game_type)}"
            )
            db.session.add(transaction)
            
            db.session.commit()
            
        result['game_state'] = {
            "token_balance": game_state.token_balance,
            "level": game_state.level,
            "experience": game_state.experience,
            "pixels": game_state.pixels,
            "materials": getattr(game_state, 'materials', 0),
            "gems": getattr(game_state, 'gems', 0)
        }
        
        return result
    
    def _get_game_name(self, game_type):
        """Get display name for a game type."""
        names = {
            'pixel_match': 'Pixel Match',
            'token_puzzle': 'Token Puzzle',
            'resource_rush': 'Resource Rush',
            'gem_hunter': 'Gem Hunter',
            'pattern_predictor': 'Pattern Predictor'
        }
        return names.get(game_type, game_type.replace('_', ' ').title())
    
    def _get_game_description(self, game_type):
        """Get description for a game type."""
        descriptions = {
            'pixel_match': 'Match the pixel patterns to earn rewards. Test your memory!',
            'token_puzzle': 'Solve the token puzzle by arranging numbers in the correct order.',
            'resource_rush': 'Collect resources as they appear before time runs out!',
            'gem_hunter': 'Find hidden gems in the pixel mine by selecting the right locations.',
            'pattern_predictor': 'Predict the next symbol in the sequence to earn big rewards!'
        }
        return descriptions.get(game_type, 'A fun mini-game with rewards!')
    
    def _calculate_rewards(self, game_type, score, difficulty=1.0):
        """Calculate rewards based on game type, score and difficulty."""
        base_rewards = config.MINI_GAME_RESOURCE_REWARDS.get(game_type, {})
        
        # Apply score multiplier (0-1 range)
        score_factor = min(1.0, max(0.1, score / 100))
        
        # Calculate rewards
        reward_tokens = round(config.MINI_GAME_TOKEN_REWARDS.get(game_type, 5) * score_factor * difficulty, 2)
        reward_pixels = round(base_rewards.get('pixels', 0) * score_factor * difficulty)
        reward_materials = round(base_rewards.get('materials', 0) * score_factor * difficulty)
        reward_gems = round(base_rewards.get('gems', 0) * score_factor * difficulty)
        reward_xp = round(config.MINI_GAME_XP_REWARDS.get(game_type, 10) * score_factor * difficulty)
        
        return {
            'reward_tokens': reward_tokens,
            'reward_pixels': reward_pixels,
            'reward_materials': reward_materials,
            'reward_gems': reward_gems,
            'reward_xp': reward_xp
        }
    
    # Individual mini-game implementations
    def _pixel_match_game(self, user, game_state, game_data):
        """
        Memory-based game where players match pixel patterns.
        
        Game data:
            player_choices: List of indices the player selected
            
        Returns:
            Game result dict
        """
        # Parse player data
        player_choices = game_data.get('player_choices', [])
        
        # Generate game if needed
        if 'game_board' not in game_data:
            # For first-time access, return game board configuration
            # Generate a board of matching pairs
            symbols = ['🎮', '🎲', '🎯', '🎨', '🎭', '🎪', '🎫', '🎟️']
            pairs_count = 8  # 8 pairs = 16 cards
            
            # Create pairs of symbols
            all_symbols = []
            for symbol in symbols[:pairs_count]:
                all_symbols.extend([symbol, symbol])
                
            # Shuffle the board
            random.shuffle(all_symbols)
            
            return {
                'success': True,
                'message': 'Match the pairs of symbols!',
                'game_data': {
                    'game_board': all_symbols,
                    'matches_required': pairs_count
                }
            }
        
        # Process player's choices
        game_board = game_data.get('game_board', [])
        matches_required = game_data.get('matches_required', 8)
        correct_matches = 0
        
        # Count correct matches
        matched_indices = set()
        for i in range(0, len(player_choices) - 1, 2):
            if i + 1 < len(player_choices):
                idx1 = player_choices[i]
                idx2 = player_choices[i + 1]
                
                if (0 <= idx1 < len(game_board) and 
                    0 <= idx2 < len(game_board) and
                    idx1 != idx2 and 
                    game_board[idx1] == game_board[idx2] and
                    idx1 not in matched_indices and 
                    idx2 not in matched_indices):
                    correct_matches += 1
                    matched_indices.add(idx1)
                    matched_indices.add(idx2)
        
        # Calculate score based on matches
        score = (correct_matches / matches_required) * 100
        
        # Calculate rewards
        rewards = self._calculate_rewards('pixel_match', score)
        
        return {
            'success': True,
            'message': f'You matched {correct_matches} out of {matches_required} pairs!',
            'score': score,
            **rewards,
            'game_data': {
                'matches_found': correct_matches,
                'matches_required': matches_required
            }
        }
    
    def _token_puzzle_game(self, user, game_state, game_data):
        """
        Number puzzle game where players arrange tokens in order.
        
        Game data:
            player_solution: List representing the player's arrangement
            
        Returns:
            Game result dict
        """
        # Parse player data
        player_solution = game_data.get('player_solution', [])
        
        # Generate puzzle if needed
        if 'puzzle' not in game_data:
            # Create a sliding puzzle (4x4 grid)
            puzzle_size = 4
            puzzle = list(range(1, puzzle_size * puzzle_size))
            puzzle.append(0)  # Empty space represented by 0
            
            # Shuffle the puzzle (ensuring it's solvable)
            random.shuffle(puzzle)
            
            return {
                'success': True,
                'message': 'Arrange the numbers in order, with the empty space in the bottom right.',
                'game_data': {
                    'puzzle': puzzle,
                    'size': puzzle_size
                }
            }
        
        # Check player's solution
        puzzle_size = game_data.get('size', 4)
        correct_solution = list(range(1, puzzle_size * puzzle_size)) + [0]
        
        # Calculate how many tiles are in the correct position
        correct_positions = sum(1 for i, num in enumerate(player_solution) if num == correct_solution[i])
        total_positions = puzzle_size * puzzle_size
        
        # Calculate score
        score = (correct_positions / total_positions) * 100
        
        # Bonus for perfect solution
        if score == 100:
            score += 20  # Bonus points
        
        # Calculate rewards
        rewards = self._calculate_rewards('token_puzzle', score, difficulty=1.2)
        
        return {
            'success': True,
            'message': f'You got {correct_positions} out of {total_positions} positions correct!',
            'score': score,
            **rewards,
            'game_data': {
                'correct_positions': correct_positions,
                'total_positions': total_positions,
                'perfect_solution': score == 100
            }
        }
    
    def _resource_rush_game(self, user, game_state, game_data):
        """
        Time-based game where players collect falling resources.
        
        Game data:
            resources_collected: Dict of resource types and counts collected
            
        Returns:
            Game result dict
        """
        # Parse player data
        resources_collected = game_data.get('resources_collected', {})
        
        # If first time, return game configuration
        if not resources_collected:
            # Configure game parameters
            game_duration = 30  # seconds
            resource_types = ['pixel', 'material', 'gem', 'token']
            target_counts = {
                'pixel': 30,
                'material': 15,
                'gem': 5,
                'token': 10
            }
            
            return {
                'success': True,
                'message': 'Collect falling resources before time runs out!',
                'game_data': {
                    'duration': game_duration,
                    'resource_types': resource_types,
                    'target_counts': target_counts
                }
            }
        
        # Process results
        target_counts = game_data.get('target_counts', {
            'pixel': 30,
            'material': 15,
            'gem': 5,
            'token': 10
        })
        
        # Calculate percentage of targets reached
        completion_percentages = []
        for resource, target in target_counts.items():
            collected = resources_collected.get(resource, 0)
            percentage = min(100, (collected / target) * 100)
            completion_percentages.append(percentage)
        
        # Overall score is the average completion percentage
        score = sum(completion_percentages) / len(completion_percentages)
        
        # Calculate rewards with extra emphasis on the actual collected resources
        base_rewards = self._calculate_rewards('resource_rush', score, difficulty=1.3)
        
        # Add bonus rewards based on what they collected
        reward_tokens = base_rewards['reward_tokens'] + resources_collected.get('token', 0) * 0.5
        reward_pixels = base_rewards['reward_pixels'] + resources_collected.get('pixel', 0) * 2
        reward_materials = base_rewards['reward_materials'] + resources_collected.get('material', 0)
        reward_gems = base_rewards['reward_gems'] + resources_collected.get('gem', 0)
        
        return {
            'success': True,
            'message': f'You collected resources with a score of {score:.1f}%!',
            'score': score,
            'reward_tokens': reward_tokens,
            'reward_pixels': reward_pixels,
            'reward_materials': reward_materials,
            'reward_gems': reward_gems,
            'reward_xp': base_rewards['reward_xp'],
            'game_data': {
                'resources_collected': resources_collected,
                'target_counts': target_counts
            }
        }
    
    def _gem_hunter_game(self, user, game_state, game_data):
        """
        Strategy game where players search for hidden gems in a grid.
        
        Game data:
            selected_cells: List of cell coordinates the player selected
            
        Returns:
            Game result dict
        """
        # Parse player data
        selected_cells = game_data.get('selected_cells', [])
        
        # Generate game if needed
        if 'grid_size' not in game_data:
            # Configure the game
            grid_size = 5  # 5x5 grid
            gem_count = 7  # 7 gems hidden in the grid
            max_selections = 10  # Player can select up to 10 cells
            
            # Place gems randomly
            gem_positions = []
            while len(gem_positions) < gem_count:
                x, y = random.randint(0, grid_size-1), random.randint(0, grid_size-1)
                position = (x, y)
                if position not in gem_positions:
                    gem_positions.append(position)
            
            return {
                'success': True,
                'message': f'Find the {gem_count} hidden gems on the grid. You have {max_selections} attempts.',
                'game_data': {
                    'grid_size': grid_size,
                    'gem_count': gem_count,
                    'max_selections': max_selections,
                    'gem_positions': gem_positions
                }
            }
        
        # Process player selections
        grid_size = game_data.get('grid_size', 5)
        gem_positions = game_data.get('gem_positions', [])
        max_selections = game_data.get('max_selections', 10)
        
        # Count found gems
        found_gems = 0
        for x, y in selected_cells[:max_selections]:  # Limit to max_selections
            if (x, y) in gem_positions:
                found_gems += 1
        
        # Calculate score based on gem finding efficiency
        efficiency = found_gems / len(selected_cells) if selected_cells else 0
        base_score = (found_gems / len(gem_positions)) * 100
        
        # Reward efficiency with bonus points
        efficiency_bonus = efficiency * 50  # Up to 50 bonus points for perfect efficiency
        score = min(100, base_score + efficiency_bonus)
        
        # Calculate rewards with difficulty scaling based on grid size
        difficulty = 1.0 + (grid_size - 5) * 0.1  # Base difficulty = 1.0 for 5x5 grid
        rewards = self._calculate_rewards('gem_hunter', score, difficulty)
        
        # Extra gem rewards for gem hunter game
        rewards['reward_gems'] += found_gems
        
        return {
            'success': True,
            'message': f'You found {found_gems} out of {len(gem_positions)} gems with {len(selected_cells)} attempts!',
            'score': score,
            **rewards,
            'game_data': {
                'found_gems': found_gems,
                'total_gems': len(gem_positions),
                'efficiency': efficiency,
                'efficiency_bonus': efficiency_bonus
            }
        }
    
    def _pattern_predictor_game(self, user, game_state, game_data):
        """
        Logic game where players predict the next element in a pattern.
        
        Game data:
            player_answer: The player's predicted next element
            
        Returns:
            Game result dict
        """
        # Parse player data
        player_answer = game_data.get('player_answer')
        
        # Generate game if needed
        if 'sequence' not in game_data:
            # Define possible sequence types
            sequence_types = [
                'arithmetic',  # e.g., [2, 4, 6, 8, ...]
                'geometric',   # e.g., [2, 4, 8, 16, ...]
                'fibonacci',   # e.g., [1, 1, 2, 3, 5, ...]
                'alternating', # e.g., [1, 3, 1, 3, 1, ...]
                'symbol'       # e.g., ['A', 'B', 'C', 'A', 'B', ...]
            ]
            
            seq_type = random.choice(sequence_types)
            sequence = []
            correct_answer = None
            
            if seq_type == 'arithmetic':
                start = random.randint(1, 10)
                step = random.randint(1, 5)
                sequence = [start + step * i for i in range(5)]
                correct_answer = sequence[-1] + step
                
            elif seq_type == 'geometric':
                start = random.randint(1, 5)
                ratio = random.randint(2, 3)
                sequence = [start * (ratio ** i) for i in range(5)]
                correct_answer = sequence[-1] * ratio
                
            elif seq_type == 'fibonacci':
                # Modified Fibonacci with random start numbers
                a, b = random.randint(1, 5), random.randint(1, 5)
                sequence = [a, b]
                for _ in range(3):
                    a, b = b, a + b
                    sequence.append(b)
                correct_answer = sequence[-1] + sequence[-2]
                
            elif seq_type == 'alternating':
                a, b = random.randint(1, 10), random.randint(1, 10)
                while b == a:
                    b = random.randint(1, 10)
                pattern_length = random.randint(2, 3)
                
                if pattern_length == 2:
                    sequence = [a, b] * 2 + [a]
                    correct_answer = b
                else:
                    c = random.randint(1, 10)
                    while c == a or c == b:
                        c = random.randint(1, 10)
                    sequence = [a, b, c] + [a, b]
                    correct_answer = c
                    
            elif seq_type == 'symbol':
                symbols = ['⭐', '🔵', '🔴', '⚪', '🟠', '🟣', '🟢', '⚫']
                pattern_length = random.randint(2, 3)
                pattern = random.sample(symbols, pattern_length)
                
                # Repeat the pattern
                sequence = pattern * 2
                if len(sequence) > 5:
                    sequence = sequence[:5]
                else:
                    sequence = pattern * 3
                    sequence = sequence[:5]
                    
                correct_answer = pattern[len(sequence) % len(pattern)]
            
            # Difficulty is based on sequence type and length
            difficulty_map = {
                'arithmetic': 1.0,
                'alternating': 1.2,
                'fibonacci': 1.5,
                'geometric': 1.3,
                'symbol': 1.1
            }
            
            return {
                'success': True,
                'message': 'What comes next in this sequence?',
                'game_data': {
                    'sequence': sequence,
                    'sequence_type': seq_type,
                    'correct_answer': correct_answer,
                    'difficulty': difficulty_map.get(seq_type, 1.0)
                }
            }
        
        # Process player answer
        correct_answer = game_data.get('correct_answer')
        difficulty = game_data.get('difficulty', 1.0)
        
        # Check if answer is correct
        is_correct = player_answer == correct_answer
        
        # Calculate score - binary for this game
        score = 100 if is_correct else 0
        
        # Calculate rewards
        rewards = self._calculate_rewards('pattern_predictor', score, difficulty)
        
        message = "Correct! You predicted the pattern perfectly!" if is_correct else f"Incorrect. The next element was {correct_answer}."
        
        return {
            'success': True,
            'message': message,
            'score': score,
            **rewards,
            'game_data': {
                'correct': is_correct,
                'player_answer': player_answer,
                'correct_answer': correct_answer,
                'sequence_type': game_data.get('sequence_type')
            }
        }