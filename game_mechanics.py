import random
import logging
import math
from datetime import datetime, timedelta
from flask import request
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
        
    def process_action(self, user, game_state, action, params=None):
        """
        Process a game action from the web interface.
        
        Args:
            user: User model instance
            game_state: GameState model instance
            action: String indicating the action to perform
            params: Optional dictionary with additional parameters
            
        Returns:
            dict: Result of the action
        """
        try:
            if params is None:
                params = {}
                
            if action == "daily":
                return self._process_daily_claim(user, game_state)
            elif action == "mine":
                return self._process_mining(user, game_state)
            elif action == "create":
                return self._process_pixel_art(user, game_state)
            elif action == "build":
                # Check if this is just checking available buildings
                if params.get('check_only', False):
                    return self._process_building(user, game_state, check_only=True)
                    
                # Pass building type if specified
                building_type = params.get('building_type', 'mine')
                return self._process_building(user, game_state, building_type=building_type)
            elif action == "collect":
                return self._process_collection(user, game_state)
            elif action == "market":
                # TODO: Implement market actions
                return {
                    "success": False,
                    "message": "Market functionality is coming soon!",
                    "game_state": self._get_game_state_dict(game_state)
                }
            elif action == "upgrade":
                # TODO: Implement building upgrade functionality
                return {
                    "success": False, 
                    "message": "Building upgrades are coming soon!",
                    "game_state": self._get_game_state_dict(game_state)
                }
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
    
    def _process_building(self, user, game_state, building_type='mine', check_only=False):
        """Process building purchase action with enhanced mechanics."""
        # Get active events that affect building
        active_events = self._get_active_events(affecting_activity='building')
        building_multiplier = 1.0
        for event in active_events:
            building_multiplier *= event.building_multiplier
            
        # Apply skill level bonus
        skill_bonus = 1.0 + (game_state.building_skill * SKILL_LEVEL_BONUS)
        
        # Check available building types based on level
        available_buildings = []
        for b_type, b_info in BUILDING_TYPES.items():
            # Unlock buildings gradually based on level
            required_level = {
                'mine': 1,  # Available from start
                'studio': 3,
                'factory': 5,
                'market': 7,
                'bank': 10
            }
            
            if game_state.level >= required_level.get(b_type, 1):
                # Get actual cost with modifiers
                token_cost = b_info['base_cost'] * (1.0 - (skill_bonus - 1.0) * 0.5)  # Skill reduces cost
                if building_multiplier < 1.0:  # Crisis event increases cost
                    token_cost *= (2.0 - building_multiplier)  # Inverse effect on cost
                material_cost = b_info['material_cost']
                
                available_buildings.append({
                    'type': b_type,
                    'name': b_info['name'],
                    'description': b_info['description'],
                    'token_cost': round(token_cost, 2),
                    'material_cost': material_cost,
                    'produces': b_info['produces'],
                    'production_rate': b_info['production_rate']
                })
        
        # If the request is just to check available buildings
        if check_only:
            return {
                "success": True,
                "buildings": available_buildings,
                "game_state": self._get_game_state_dict(game_state)
            }
        
        # Find selected building info
        selected_building = next((b for b in available_buildings if b['type'] == building_type), None)
        if not selected_building:
            return {
                "success": False,
                "message": f"Building type '{building_type}' is not available at your current level.",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        token_cost = selected_building['token_cost']
        material_cost = selected_building['material_cost']
        
        # Check if user has enough resources
        if game_state.token_balance < token_cost:
            return {
                "success": False,
                "message": f"Not enough $PXPT! Current: {game_state.token_balance:.2f}, Need: {token_cost}",
                "game_state": self._get_game_state_dict(game_state)
            }
            
        if getattr(game_state, 'materials', 0) < material_cost:
            return {
                "success": False,
                "message": f"Not enough materials! Current: {getattr(game_state, 'materials', 0)}, Need: {material_cost}",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        # Create the new building
        new_building = Building(
            game_state_id=game_state.id,
            building_type=building_type,
            level=1,
            production_rate=selected_building['production_rate'],
            produces_tokens=selected_building['produces'] == 'tokens',
            produces_pixels=selected_building['produces'] == 'pixels',
            produces_materials=selected_building['produces'] == 'materials',
            produces_gems=selected_building['produces'] == 'gems',
            efficiency=building_multiplier  # Apply event multiplier to efficiency
        )
        
        # Update game state
        game_state.token_balance -= token_cost
        if material_cost > 0:
            game_state.materials -= material_cost
        game_state.buildings_owned += 1
        
        # Add experience and progress building skill
        xp_gained = 20
        game_state.experience += xp_gained
        
        building_skill_progress = random.randint(3, 5)  # Building gives good skill progress
        new_skill_level = self._progress_skill(game_state, 'building', building_skill_progress)
        
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
            amount=-token_cost,
            description=f'Purchased {selected_building["name"]}'
        )
        
        db.session.add(new_building)
        db.session.add(building_transaction)
        
        # Check if we should trigger a random event
        self._maybe_trigger_random_event(user, game_state)
        
        db.session.commit()
        
        # Build response message
        message = f"New {selected_building['name']} constructed! Cost: {token_cost} $PXPT"
        if material_cost > 0:
            message += f", {material_cost} Materials"
        if new_skill_level:
            message += f" | Building skill increased to level {game_state.building_skill}!"
            
        # Optional event notification
        event_message = self._get_active_event_message(active_events)
        if event_message:
            message += f" | {event_message}"
        
        return {
            "success": True,
            "message": message,
            "building": {
                "type": building_type,
                "name": selected_building["name"],
                "level": 1,
                "produces": selected_building["produces"],
                "production_rate": selected_building["production_rate"]
            },
            "token_cost": token_cost,
            "material_cost": material_cost,
            "buildings_owned": game_state.buildings_owned,
            "xp_gained": xp_gained,
            "level_up": level_up,
            "skill_up": new_skill_level,
            "game_state": self._get_game_state_dict(game_state),
            "active_events": [{"name": e.name, "multiplier": e.building_multiplier} for e in active_events] if active_events else []
        }
    
    def _process_collection(self, user, game_state):
        """Process building income collection action with enhanced mechanics."""
        # Check if user has buildings in database
        buildings = Building.query.filter_by(game_state_id=game_state.id).all()
        
        if not buildings and game_state.buildings_owned == 0:
            return {
                "success": False,
                "message": "You don't own any buildings yet!",
                "game_state": self._get_game_state_dict(game_state)
            }
        
        # Get active events that affect building income
        active_events = self._get_active_events(affecting_activity='building')
        building_multiplier = 1.0
        for event in active_events:
            building_multiplier *= event.building_multiplier
            
        # Apply skill level bonus
        skill_bonus = 1.0 + (game_state.building_skill * SKILL_LEVEL_BONUS)
        
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
        
        # Processing legacy buildings (old system) if any
        if game_state.buildings_owned > len(buildings):
            legacy_buildings = game_state.buildings_owned - len(buildings)
            legacy_income = BUILDING_INCOME_BASE * legacy_buildings * skill_bonus * building_multiplier
            legacy_income = round(legacy_income, 2)
            
            # Update game state for legacy buildings
            game_state.token_balance += legacy_income
        else:
            legacy_income = 0
            
        # Process each building based on its type
        total_tokens = legacy_income
        total_pixels = 0
        total_materials = 0
        total_gems = 0
        
        building_details = []
        
        for building in buildings:
            # Get time since last collection for this building
            time_factor = min(1.0, (now - building.last_collection).total_seconds() / cooldown_seconds)
            building_efficiency = building.efficiency * skill_bonus * building_multiplier * time_factor
            
            # Calculate production based on building type and level
            building_info = self._get_building_info(building.building_type, building.level)
            if not building_info:
                continue
                
            production_rate = building_info['production_rate'] * building_efficiency
            
            # Update game state based on what the building produces
            production_info = {
                'type': building.building_type,
                'name': building_info['name'],
                'level': building.level,
                'efficiency': round(building_efficiency * 100, 1),
                'produced': {}
            }
            
            if building.produces_tokens:
                # Special case for bank
                if building.building_type == 'bank':
                    # Bank produces interest on token balance
                    interest = game_state.token_balance * production_rate * 0.01  # Convert to percentage
                    interest = round(interest, 2)
                    game_state.token_balance += interest
                    total_tokens += interest
                    production_info['produced']['tokens'] = interest
                else:
                    # Normal token production
                    tokens = round(production_rate, 2)
                    game_state.token_balance += tokens
                    total_tokens += tokens
                    production_info['produced']['tokens'] = tokens
                    
            if building.produces_pixels:
                pixels = round(production_rate)
                game_state.pixels += pixels
                total_pixels += pixels
                production_info['produced']['pixels'] = pixels
                
            if building.produces_materials:
                materials = round(production_rate)
                game_state.materials += materials
                total_materials += materials
                production_info['produced']['materials'] = materials
                
            if building.produces_gems:
                gems = max(1, round(production_rate * 0.1))  # Gems are valuable, produce fewer
                game_state.gems += gems
                total_gems += gems
                production_info['produced']['gems'] = gems
                
            # Update building last collection time
            building.last_collection = now
            
            # Add to building details for response
            building_details.append(production_info)
            
        # Always give some XP for collection
        xp_gained = 5
        game_state.experience += xp_gained
        
        # Progress building skill
        building_skill_progress = random.randint(1, 2)  # Small progress for collection
        new_skill_level = self._progress_skill(game_state, 'building', building_skill_progress)
        
        # Check for level up
        level_up = False
        if game_state.experience >= game_state.level * XP_PER_LEVEL:
            game_state.experience -= game_state.level * XP_PER_LEVEL
            game_state.level += 1
            level_up = True
        
        # Record transaction
        resources_collected = []
        if total_tokens > 0:
            resources_collected.append(f"{total_tokens} $PXPT")
        if total_pixels > 0:
            resources_collected.append(f"{total_pixels} Pixels")
        if total_materials > 0:
            resources_collected.append(f"{total_materials} Materials")
        if total_gems > 0:
            resources_collected.append(f"{total_gems} Gems")
            
        description = f'Income collected: {", ".join(resources_collected)}'
        
        income_transaction = Transaction(
            user_id=user.id,
            type='building_income',
            amount=total_tokens,  # Record token amount in transaction
            description=description
        )
        db.session.add(income_transaction)
        
        # Check if we should trigger a random event
        self._maybe_trigger_random_event(user, game_state)
        
        db.session.commit()
        
        # Build response message
        message = f"Income collected!"
        if total_tokens > 0:
            message += f" +{total_tokens} $PXPT"
        if total_pixels > 0:
            message += f", +{total_pixels} Pixels"
        if total_materials > 0:
            message += f", +{total_materials} Materials"
        if total_gems > 0:
            message += f", +{total_gems} Gems"
            
        if new_skill_level:
            message += f" | Building skill increased to level {game_state.building_skill}!"
            
        # Optional event notification
        event_message = self._get_active_event_message(active_events)
        if event_message:
            message += f" | {event_message}"
        
        return {
            "success": True,
            "message": message,
            "income": {
                "tokens": total_tokens,
                "pixels": total_pixels,
                "materials": total_materials,
                "gems": total_gems
            },
            "building_details": building_details,
            "xp_gained": xp_gained,
            "level_up": level_up,
            "skill_up": new_skill_level,
            "game_state": self._get_game_state_dict(game_state),
            "active_events": [{"name": e.name, "multiplier": e.building_multiplier} for e in active_events] if active_events else []
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
            "xp_to_next_level": (game_state.level * XP_PER_LEVEL) - game_state.experience,
            # New fields for enhanced economy
            "materials": getattr(game_state, 'materials', 0),
            "gems": getattr(game_state, 'gems', 0),
            "mining_skill": getattr(game_state, 'mining_skill', 1),
            "art_skill": getattr(game_state, 'art_skill', 1),
            "building_skill": getattr(game_state, 'building_skill', 1),
            "trading_skill": getattr(game_state, 'trading_skill', 1),
            "market_transactions": getattr(game_state, 'market_transactions', 0),
        }
        
    def _progress_skill(self, game_state, skill_type, progress_amount):
        """
        Progress a skill by a given amount and check for level up.
        
        Args:
            game_state: GameState model instance
            skill_type: String indicating the skill to progress ('mining', 'art', 'building', 'trading')
            progress_amount: Integer amount of progress to add
            
        Returns:
            Boolean: True if skill leveled up, False otherwise
        """
        skill_attr = f"{skill_type}_skill"
        if not hasattr(game_state, skill_attr):
            logger.warning(f"Skill {skill_type} not found on game state")
            return False
            
        current_level = getattr(game_state, skill_attr)
        
        # Calculate progress needed based on current level
        progress_needed = SKILL_UP_THRESHOLD * current_level
        
        # Add progress and check for level up
        if progress_amount >= progress_needed:
            # Level up
            setattr(game_state, skill_attr, current_level + 1)
            return True
        else:
            # Not enough for level up yet
            # Note: We're not tracking partial progress yet, just returning False
            return False
        
    def _get_active_events(self, affecting_activity=None):
        """
        Get active game events, optionally filtered by activity type.
        
        Args:
            affecting_activity: Optional string to filter events by activity ('mining', 'art', 'building', 'market')
            
        Returns:
            List of GameEvent instances that are currently active
        """
        now = datetime.utcnow()
        query = GameEvent.query.filter(
            GameEvent.is_active == True,
            GameEvent.start_time <= now,
            GameEvent.end_time >= now
        )
        
        # Filter by activity if requested
        if affecting_activity == 'mining':
            # Events with mining multiplier not equal to 1.0
            query = query.filter(GameEvent.mining_multiplier != 1.0)
        elif affecting_activity == 'art':
            # Events with art multiplier not equal to 1.0
            query = query.filter(GameEvent.art_multiplier != 1.0)
        elif affecting_activity == 'building':
            # Events with building multiplier not equal to 1.0
            query = query.filter(GameEvent.building_multiplier != 1.0)
        elif affecting_activity == 'market':
            # Events with market fee multiplier not equal to 1.0
            query = query.filter(GameEvent.market_fee_multiplier != 1.0)
            
        return query.all()
    
    def _get_active_event_message(self, events):
        """
        Create a message string describing active events.
        
        Args:
            events: List of GameEvent instances
            
        Returns:
            String message or None if no events
        """
        if not events:
            return None
            
        if len(events) == 1:
            event = events[0]
            return f"Active event: {event.name} - {event.description}"
        else:
            return f"{len(events)} events active! Check the Events tab for details."
    
    def _maybe_trigger_random_event(self, user, game_state):
        """
        Check if a random event should be triggered and create it if so.
        
        Args:
            user: User model instance
            game_state: GameState model instance
            
        Returns:
            GameEvent instance if created, None otherwise
        """
        # Check if we should trigger an event
        if random.random() > EVENT_CHANCE_DAILY:
            return None
            
        # Check if there are already active events
        active_events = self._get_active_events()
        if len(active_events) >= 2:  # Limit active events
            return None
            
        now = datetime.utcnow()
        
        # Choose a random event type
        event_types = ['seasonal', 'special', 'crisis', 'boom']
        event_type = random.choice(event_types)
        
        # Calculate duration
        duration_days = random.randint(EVENT_DURATION_DAYS_MIN, EVENT_DURATION_DAYS_MAX)
        
        # Set up event effects based on type
        mining_mul = building_mul = art_mul = market_mul = 1.0
        event_name = ""
        event_description = ""
        
        if event_type == 'seasonal':
            event_name = random.choice(['Pixel Festival', 'Token Harvest', 'Digital Renaissance'])
            event_description = f"A {event_name} is happening! Bonuses for everyone!"
            # Slight boost to everything
            mining_mul = art_mul = building_mul = market_mul = 1.2
            
        elif event_type == 'special':
            # Boost one activity significantly
            target_activity = random.choice(['mining', 'art', 'building', 'market'])
            if target_activity == 'mining':
                event_name = "Mining Rush"
                event_description = "Rich pixel veins discovered! Mining yields are increased."
                mining_mul = 1.5
            elif target_activity == 'art':
                event_name = "Art Exhibition"
                event_description = "A special art exhibition is open! Art creations are more valuable."
                art_mul = 1.5
            elif target_activity == 'building':
                event_name = "Construction Boom"
                event_description = "Building efficiency is increased due to new techniques!"
                building_mul = 1.5
            else:
                event_name = "Market Frenzy"
                event_description = "The market is buzzing with activity! Reduced fees on all trades."
                market_mul = 0.7  # Reduced fees
        
        elif event_type == 'crisis':
            event_name = random.choice(['Pixel Drought', 'Token Inflation', 'Digital Recession'])
            event_description = f"A {event_name} is affecting the economy. Some activities are less productive."
            
            # Randomly choose which activities are affected negatively
            activities = ['mining', 'art', 'building', 'market']
            affected = random.sample(activities, k=random.randint(1, 2))
            
            if 'mining' in affected:
                mining_mul = 0.7
            if 'art' in affected:
                art_mul = 0.7
            if 'building' in affected:
                building_mul = 0.7
            if 'market' in affected:
                market_mul = 1.3  # Increased fees
        
        elif event_type == 'boom':
            event_name = "Economic Boom"
            event_description = "The Pixel Plaza economy is thriving! All activities are more rewarding."
            # Boost everything significantly
            mining_mul = art_mul = building_mul = 1.3
            market_mul = 0.8  # Reduced fees
            
        # Create the event
        event = GameEvent(
            name=event_name,
            description=event_description,
            event_type=event_type,
            mining_multiplier=mining_mul,
            art_multiplier=art_mul,
            building_multiplier=building_mul,
            market_fee_multiplier=market_mul,
            affects_tokens=True,
            affects_pixels=True,
            affects_materials=True if random.random() > 0.5 else False,
            affects_gems=True if random.random() > 0.7 else False,
            start_time=now,
            end_time=now + timedelta(days=duration_days),
            is_active=True
        )
        
        db.session.add(event)
        # Don't commit here - the caller will handle the commit
        
        return event
        
    def _get_building_info(self, building_type, level=1):
        """
        Get configuration information for a building type.
        
        Args:
            building_type: String indicating the building type
            level: Optional integer level of the building
            
        Returns:
            dict with building properties or None if type not found
        """
        if building_type not in BUILDING_TYPES:
            return None
            
        building_info = BUILDING_TYPES[building_type].copy()
        
        # Calculate level-based values
        if level > 1:
            building_info['production_rate'] *= building_info['level_multiplier'] ** (level - 1)
            building_info['base_cost'] *= BUILDING_UPGRADE_MULTIPLIER ** (level - 1)
            
        return building_info
        
    def _get_resource_market_price(self, resource_type):
        """
        Get the current market price for a resource.
        
        Args:
            resource_type: String indicating the resource ('pixels', 'materials', 'gems')
            
        Returns:
            Float price per unit
        """
        # Get latest market history for this resource
        latest = MarketHistory.query.filter_by(
            resource_type=resource_type
        ).order_by(MarketHistory.timestamp.desc()).first()
        
        if not latest:
            # Default prices if no history exists
            if resource_type == 'pixels':
                return 0.1
            elif resource_type == 'materials':
                return 0.5
            elif resource_type == 'gems':
                return 5.0
            else:
                return 1.0
                
        # Add some small random variation to the price (-5% to +5%)
        variation = random.uniform(-0.05, 0.05)
        price = latest.avg_price * (1 + variation)
        
        return round(price, 2)
