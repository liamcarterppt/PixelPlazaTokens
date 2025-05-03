import random
import logging
from datetime import datetime, timedelta
from models import User, GameState, Transaction
from app import db
from config import (
    DAILY_REWARD, REFERRAL_BONUS, MAX_ENERGY, ENERGY_REGEN_RATE,
    XP_PER_LEVEL, MINING_REWARD, BUILDING_COST, BUILDING_INCOME,
    PIXEL_ART_COST, PIXEL_ART_REWARD
)

logger = logging.getLogger(__name__)

class GameMechanics:
    """
    Game mechanics for the Pixel Plaza Token game.
    This class handles all game logic and economy simulation.
    """
    
    def __init__(self):
        """Initialize game mechanics."""
        logger.info("Initializing game mechanics")
        
    def process_action(self, user, game_state, action):
        """
        Process a game action from the web interface.
        
        Args:
            user: User model instance
            game_state: GameState model instance
            action: String indicating the action to perform
            
        Returns:
            dict: Result of the action
        """
        try:
            if action == "daily":
                return self._process_daily_claim(user, game_state)
            elif action == "mine":
                return self._process_mining(user, game_state)
            elif action == "create":
                return self._process_pixel_art(user, game_state)
            elif action == "build":
                return self._process_building(user, game_state)
            elif action == "collect":
                return self._process_collection(user, game_state)
            else:
                return {
                    "success": False,
                    "message": f"Unknown action: {action}"
                }
        except Exception as e:
            logger.error(f"Error processing action {action}: {str(e)}")
            return {
                "success": False,
                "message": f"Error occurred: {str(e)}"
            }
    
    def _process_daily_claim(self, user, game_state):
        """Process daily claim action."""
        now = datetime.utcnow()
        
        # Check if user can claim daily reward
        if game_state.last_daily_claim is not None:
            time_since_last_claim = now - game_state.last_daily_claim
            if time_since_last_claim.days < 1:
                next_claim_time = game_state.last_daily_claim + timedelta(days=1)
                hours_remaining = (next_claim_time - now).seconds // 3600
                minutes_remaining = ((next_claim_time - now).seconds % 3600) // 60
                
                return {
                    "success": False,
                    "message": f"Daily reward already claimed. Next claim in {hours_remaining}h {minutes_remaining}m",
                    "game_state": self._get_game_state_dict(game_state)
                }
        
        # Calculate streak and reward
        if game_state.last_daily_claim is not None and (now - game_state.last_daily_claim).days == 1:
            # Continuing streak
            game_state.daily_streak += 1
        elif game_state.last_daily_claim is None or (now - game_state.last_daily_claim).days > 1:
            # Reset streak
            game_state.daily_streak = 1
        
        # Calculate bonus based on streak
        streak_bonus = min(game_state.daily_streak, 7)  # Cap bonus at 7 days
        total_reward = DAILY_REWARD + (streak_bonus - 1)
        
        # Update game state
        game_state.token_balance += total_reward
        game_state.last_daily_claim = now
        game_state.energy = min(game_state.energy + 50, MAX_ENERGY)  # Refill energy
        
        # Record transaction
        daily_transaction = Transaction(
            user_id=user.id,
            type='daily_reward',
            amount=total_reward,
            description=f'Daily reward ({game_state.daily_streak} day streak)'
        )
        db.session.add(daily_transaction)
        
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Daily reward claimed! +{total_reward} $PXPT (Streak: {game_state.daily_streak})",
            "reward": total_reward,
            "streak": game_state.daily_streak,
            "energy_added": 50,
            "game_state": self._get_game_state_dict(game_state)
        }
    
    def _process_mining(self, user, game_state):
        """Process mining action."""
        # Check if user has enough energy
        if game_state.energy < 10:
            return {
                "success": False,
                "message": f"Not enough energy! Current: {game_state.energy}/100, Need: 10",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        # Calculate mining reward with some randomness
        base_reward = MINING_REWARD * game_state.level
        randomness = random.uniform(0.8, 1.2)  # ±20% random variation
        reward = round(base_reward * randomness, 2)
        
        # Calculate pixels found
        pixels_found = 5 + (game_state.level - 1) + random.randint(0, 3)
        
        # Update game state
        game_state.token_balance += reward
        game_state.energy -= 10
        game_state.pixels += pixels_found
        game_state.experience += 5
        
        # Check for level up
        level_up = False
        if game_state.experience >= game_state.level * XP_PER_LEVEL:
            game_state.experience -= game_state.level * XP_PER_LEVEL
            game_state.level += 1
            level_up = True
        
        # Record transaction
        mining_transaction = Transaction(
            user_id=user.id,
            type='mining',
            amount=reward,
            description=f'Mining reward'
        )
        db.session.add(mining_transaction)
        
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Mining successful! +{reward} $PXPT, +{pixels_found} Pixels",
            "reward": reward,
            "pixels_found": pixels_found,
            "energy_used": 10,
            "xp_gained": 5,
            "level_up": level_up,
            "game_state": self._get_game_state_dict(game_state)
        }
    
    def _process_pixel_art(self, user, game_state):
        """Process pixel art creation action."""
        # Check if user has enough pixels and energy
        if game_state.pixels < PIXEL_ART_COST:
            return {
                "success": False,
                "message": f"Not enough pixels! Current: {game_state.pixels}, Need: {PIXEL_ART_COST}",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        if game_state.energy < 15:
            return {
                "success": False,
                "message": f"Not enough energy! Current: {game_state.energy}/100, Need: 15",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        # Calculate reward with some randomness
        base_reward = PIXEL_ART_REWARD * game_state.level
        quality_factor = random.uniform(0.9, 1.5)  # Represents art quality
        reward = round(base_reward * quality_factor, 2)
        
        # Update game state
        game_state.token_balance += reward
        game_state.pixels -= PIXEL_ART_COST
        game_state.energy -= 15
        game_state.pixel_art_created += 1
        game_state.experience += 10
        
        # Check for level up
        level_up = False
        if game_state.experience >= game_state.level * XP_PER_LEVEL:
            game_state.experience -= game_state.level * XP_PER_LEVEL
            game_state.level += 1
            level_up = True
        
        # Record transaction
        creation_transaction = Transaction(
            user_id=user.id,
            type='pixel_art',
            amount=reward,
            description=f'Pixel art creation reward'
        )
        db.session.add(creation_transaction)
        
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Pixel art created! +{reward} $PXPT",
            "reward": reward,
            "pixels_used": PIXEL_ART_COST,
            "energy_used": 15,
            "xp_gained": 10,
            "level_up": level_up,
            "game_state": self._get_game_state_dict(game_state)
        }
    
    def _process_building(self, user, game_state):
        """Process building purchase action."""
        # Calculate building cost (increases with more buildings)
        building_cost = BUILDING_COST + (game_state.buildings_owned * 10)
        
        # Check if user has enough tokens
        if game_state.token_balance < building_cost:
            return {
                "success": False,
                "message": f"Not enough $PXPT! Current: {game_state.token_balance:.2f}, Need: {building_cost}",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        # Update game state
        game_state.token_balance -= building_cost
        game_state.buildings_owned += 1
        game_state.experience += 20
        
        # Check for level up
        level_up = False
        if game_state.experience >= game_state.level * XP_PER_LEVEL:
            game_state.experience -= game_state.level * XP_PER_LEVEL
            game_state.level += 1
            level_up = True
        
        # Record transaction
        building_transaction = Transaction(
            user_id=user.id,
            type='building_purchase',
            amount=-building_cost,
            description=f'Building purchase'
        )
        db.session.add(building_transaction)
        
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Building purchased! Cost: {building_cost} $PXPT",
            "cost": building_cost,
            "buildings_owned": game_state.buildings_owned,
            "daily_income": BUILDING_INCOME * game_state.buildings_owned,
            "xp_gained": 20,
            "level_up": level_up,
            "game_state": self._get_game_state_dict(game_state)
        }
    
    def _process_collection(self, user, game_state):
        """Process building income collection action."""
        # Check if user has buildings
        if game_state.buildings_owned == 0:
            return {
                "success": False,
                "message": "You don't own any buildings yet!",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        # Check if collection is available
        now = datetime.utcnow()
        last_transaction = Transaction.query.filter_by(
            user_id=user.id, 
            type='building_income'
        ).order_by(Transaction.timestamp.desc()).first()
        
        if last_transaction and (now - last_transaction.timestamp).seconds < 86400:  # 24 hours in seconds
            next_collection_time = last_transaction.timestamp + timedelta(days=1)
            hours_remaining = (next_collection_time - now).seconds // 3600
            minutes_remaining = ((next_collection_time - now).seconds % 3600) // 60
            
            return {
                "success": False,
                "message": f"Collection not available yet. Next collection in {hours_remaining}h {minutes_remaining}m",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        # Calculate income
        income = BUILDING_INCOME * game_state.buildings_owned
        
        # Update game state
        game_state.token_balance += income
        
        # Record transaction
        income_transaction = Transaction(
            user_id=user.id,
            type='building_income',
            amount=income,
            description=f'Income from {game_state.buildings_owned} buildings'
        )
        db.session.add(income_transaction)
        
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Income collected! +{income} $PXPT from {game_state.buildings_owned} buildings",
            "income": income,
            "buildings_owned": game_state.buildings_owned,
            "game_state": self._get_game_state_dict(game_state)
        }
    
    def _get_game_state_dict(self, game_state):
        """Convert GameState model to dictionary for API response."""
        return {
            "token_balance": game_state.token_balance,
            "level": game_state.level,
            "experience": game_state.experience,
            "buildings_owned": game_state.buildings_owned,
            "pixel_art_created": game_state.pixel_art_created,
            "pixels": game_state.pixels,
            "energy": game_state.energy,
            "daily_streak": game_state.daily_streak,
            "xp_to_next_level": (game_state.level * XP_PER_LEVEL) - game_state.experience
        }
