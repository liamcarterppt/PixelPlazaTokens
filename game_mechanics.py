import random
import logging
import math
from datetime import datetime, timedelta
from models import User, GameState, Transaction, Building, MarketOrder, MarketHistory, GameEvent
from app import db
from config import (
    DAILY_REWARD, DAILY_STREAK_BONUS, 
    MINING_REWARD_MIN, MINING_REWARD_MAX, MINING_ENERGY_COST, MINING_PIXEL_GAIN,
    MINING_MATERIAL_CHANCE, MINING_MATERIAL_MIN, MINING_MATERIAL_MAX,
    MINING_GEM_CHANCE, MINING_GEM_MIN, MINING_GEM_MAX,
    ART_TOKEN_REWARD_MIN, ART_TOKEN_REWARD_MAX, ART_ENERGY_COST, ART_PIXEL_COST,
    ART_GEM_CHANCE, ART_GEM_MIN, ART_GEM_MAX,
    BUILDING_TYPES, BUILDING_COST_BASE, BUILDING_COST_MULTIPLIER, 
    BUILDING_INCOME_BASE, COLLECTION_COOLDOWN_HOURS, BUILDING_UPGRADE_MULTIPLIER,
    MARKET_FEE_PERCENTAGE, MARKET_ORDER_EXPIRY_DAYS, MARKET_MIN_TOKEN_BALANCE,
    MARKET_MAX_ACTIVE_ORDERS, MARKET_PRICE_FLUCTUATION,
    SKILL_UP_THRESHOLD, SKILL_LEVEL_BONUS,
    EVENT_CHANCE_DAILY, EVENT_DURATION_DAYS_MIN, EVENT_DURATION_DAYS_MAX,
    XP_PER_LEVEL
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
        total_reward = DAILY_REWARD + (streak_bonus - 1) * DAILY_STREAK_BONUS
        
        # Update game state
        game_state.token_balance += total_reward
        game_state.last_daily_claim = now
        game_state.energy = min(game_state.energy + 50, 100)  # Refill energy
        
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
        """Process mining action with enhanced mechanics."""
        # Check if user has enough energy
        if game_state.energy < MINING_ENERGY_COST:
            return {
                "success": False,
                "message": f"Not enough energy! Current: {game_state.energy}/100, Need: {MINING_ENERGY_COST}",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        # Get active events that affect mining
        active_events = self._get_active_events(affecting_activity='mining')
        mining_multiplier = 1.0
        for event in active_events:
            mining_multiplier *= event.mining_multiplier
        
        # Apply skill level bonus
        skill_bonus = 1.0 + (game_state.mining_skill * SKILL_LEVEL_BONUS)
        
        # Calculate mining reward with enhanced mechanics
        base_reward = MINING_REWARD_MIN + (game_state.level * 0.2)  # Increase reward with level
        max_reward = MINING_REWARD_MAX + (game_state.level * 0.2)
        reward = round(random.uniform(base_reward, max_reward) * skill_bonus * mining_multiplier, 2)
        
        # Calculate pixel gain with skill bonus
        pixel_gain = round(MINING_PIXEL_GAIN * skill_bonus * mining_multiplier)
        
        # Chance to find materials based on events and skill
        material_found = 0
        if random.random() < MINING_MATERIAL_CHANCE * skill_bonus * mining_multiplier:
            material_found = random.randint(MINING_MATERIAL_MIN, MINING_MATERIAL_MAX)
            game_state.materials += material_found
        
        # Chance to find gems based on events and skill (rare resource)
        gems_found = 0
        if random.random() < MINING_GEM_CHANCE * skill_bonus * mining_multiplier:
            gems_found = random.randint(MINING_GEM_MIN, MINING_GEM_MAX)
            game_state.gems += gems_found
        
        # Update game state
        game_state.token_balance += reward
        game_state.energy -= MINING_ENERGY_COST
        game_state.pixels += pixel_gain
        
        # Always add experience
        xp_gained = 5 + round(2 * mining_multiplier)  # Bonus XP during events
        game_state.experience += xp_gained
        
        # Progress mining skill
        mining_skill_progress = random.randint(1, 3)
        new_skill_level = self._progress_skill(game_state, 'mining', mining_skill_progress)
        
        # Check for level up
        level_up = False
        if game_state.experience >= game_state.level * XP_PER_LEVEL:
            game_state.experience -= game_state.level * XP_PER_LEVEL
            game_state.level += 1
            level_up = True
        
        # Record transaction
        reward_description = 'Mining reward'
        if mining_multiplier > 1.0:
            reward_description += f' (Event bonus: {mining_multiplier:.1f}x)'
        
        mining_transaction = Transaction(
            user_id=user.id,
            type='mining',
            amount=reward,
            description=reward_description
        )
        db.session.add(mining_transaction)
        
        # Check if we should trigger a random event
        self._maybe_trigger_random_event(user, game_state)
        
        db.session.commit()
        
        # Build response message
        message = f"Mining successful! +{reward} $PXPT, +{pixel_gain} Pixels"
        if material_found > 0:
            message += f", +{material_found} Materials"
        if gems_found > 0:
            message += f", +{gems_found} Gems"
        if new_skill_level:
            message += f" | Mining skill increased to level {game_state.mining_skill}!"
        
        # Optional event notification
        event_message = self._get_active_event_message(active_events)
        if event_message:
            message += f" | {event_message}"
        
        return {
            "success": True,
            "message": message,
            "reward": reward,
            "pixels_found": pixel_gain,
            "materials_found": material_found,
            "gems_found": gems_found,
            "energy_used": MINING_ENERGY_COST,
            "xp_gained": xp_gained,
            "level_up": level_up,
            "skill_up": new_skill_level,
            "game_state": self._get_game_state_dict(game_state),
            "active_events": [{"name": e.name, "multiplier": e.mining_multiplier} for e in active_events] if active_events else []
        }
    
    def _process_pixel_art(self, user, game_state):
        """Process pixel art creation action with enhanced mechanics."""
        # Check if user has enough pixels and energy
        if game_state.pixels < ART_PIXEL_COST:
            return {
                "success": False,
                "message": f"Not enough pixels! Current: {game_state.pixels}, Need: {ART_PIXEL_COST}",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        if game_state.energy < ART_ENERGY_COST:
            return {
                "success": False,
                "message": f"Not enough energy! Current: {game_state.energy}/100, Need: {ART_ENERGY_COST}",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        # Get active events that affect art creation
        active_events = self._get_active_events(affecting_activity='art')
        art_multiplier = 1.0
        for event in active_events:
            art_multiplier *= event.art_multiplier
            
        # Apply skill level bonus
        skill_bonus = 1.0 + (game_state.art_skill * SKILL_LEVEL_BONUS)
        
        # Calculate reward with enhanced mechanics
        base_reward = ART_TOKEN_REWARD_MIN + (game_state.level * 0.5)
        max_reward = ART_TOKEN_REWARD_MAX + (game_state.level * 0.5)
        # Higher quality art will fetch better prices
        quality_factor = random.uniform(0.8, 1.2)  # Random quality of the art
        reward = round(random.uniform(base_reward, max_reward) * skill_bonus * art_multiplier * quality_factor, 2)
        
        # Chance to find gems based on events and skill (special resource from art)
        gems_found = 0
        if random.random() < ART_GEM_CHANCE * skill_bonus * art_multiplier:
            gems_found = random.randint(ART_GEM_MIN, ART_GEM_MAX)
            game_state.gems += gems_found
        
        # Calculate pixel cost reduction based on skill (more efficient art creation)
        actual_pixel_cost = max(10, ART_PIXEL_COST - math.floor(game_state.art_skill / 2) * 5)
        
        # Update game state
        game_state.token_balance += reward
        game_state.pixels -= actual_pixel_cost
        game_state.energy -= ART_ENERGY_COST
        game_state.pixel_art_created += 1
        
        # Always add experience with potential event bonus
        xp_gained = 10 + round(3 * art_multiplier)
        game_state.experience += xp_gained
        
        # Progress art skill
        art_skill_progress = random.randint(2, 4) # Art creation is better for skill progression
        new_skill_level = self._progress_skill(game_state, 'art', art_skill_progress)
        
        # Check for level up
        level_up = False
        if game_state.experience >= game_state.level * XP_PER_LEVEL:
            game_state.experience -= game_state.level * XP_PER_LEVEL
            game_state.level += 1
            level_up = True
        
        # Record transaction with quality info
        quality_desc = "Standard"
        if quality_factor > 1.1:
            quality_desc = "Masterpiece"
        elif quality_factor > 1.0:
            quality_desc = "High quality"
        elif quality_factor < 0.9:
            quality_desc = "Basic"
            
        reward_description = f'Pixel art creation reward ({quality_desc})'
        if art_multiplier > 1.0:
            reward_description += f' (Event bonus: {art_multiplier:.1f}x)'
            
        creation_transaction = Transaction(
            user_id=user.id,
            type='pixel_art',
            amount=reward,
            description=reward_description
        )
        db.session.add(creation_transaction)
        
        # Check if we should trigger a random event
        self._maybe_trigger_random_event(user, game_state)
        
        db.session.commit()
        
        # Build response message
        message = f"Pixel art created! +{reward} $PXPT ({quality_desc})"
        if gems_found > 0:
            message += f", +{gems_found} Gems"
        if actual_pixel_cost < ART_PIXEL_COST:
            message += f" | Efficiency bonus: {ART_PIXEL_COST - actual_pixel_cost} pixels saved!"
        if new_skill_level:
            message += f" | Art skill increased to level {game_state.art_skill}!"
            
        # Optional event notification
        event_message = self._get_active_event_message(active_events)
        if event_message:
            message += f" | {event_message}"
        
        return {
            "success": True,
            "message": message,
            "reward": reward,
            "pixels_used": actual_pixel_cost,
            "energy_used": ART_ENERGY_COST,
            "gems_found": gems_found,
            "quality_factor": quality_factor,
            "quality_desc": quality_desc,
            "xp_gained": xp_gained,
            "level_up": level_up,
            "skill_up": new_skill_level,
            "game_state": self._get_game_state_dict(game_state),
            "active_events": [{"name": e.name, "multiplier": e.art_multiplier} for e in active_events] if active_events else []
        }
    
    def _process_building(self, user, game_state):
        """Process building purchase action."""
        # Calculate building cost (increases with more buildings)
        building_cost = BUILDING_COST_BASE * (BUILDING_COST_MULTIPLIER ** game_state.buildings_owned)
        building_cost = round(building_cost, 2)
        
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
            "daily_income": BUILDING_INCOME_BASE * game_state.buildings_owned,
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
        
        cooldown_seconds = COLLECTION_COOLDOWN_HOURS * 3600  # Convert hours to seconds
        
        if last_transaction and (now - last_transaction.timestamp).seconds < cooldown_seconds:
            next_collection_time = last_transaction.timestamp + timedelta(hours=COLLECTION_COOLDOWN_HOURS)
            hours_remaining = (next_collection_time - now).seconds // 3600
            minutes_remaining = ((next_collection_time - now).seconds % 3600) // 60
            
            return {
                "success": False,
                "message": f"Collection not available yet. Next collection in {hours_remaining}h {minutes_remaining}m",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        # Calculate income
        income = BUILDING_INCOME_BASE * game_state.buildings_owned
        
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
