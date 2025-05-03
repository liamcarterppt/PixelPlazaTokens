"""
Configuration settings for the Pixel Plaza Token game.
"""

# Referral System
REFERRER_BONUS = 5  # $PXPT bonus for referring someone
REFEREE_BONUS = 3   # $PXPT bonus for being referred
REFERRER_LEVEL_REQUIREMENT = 3  # Minimum level to generate a referral code
REFERRAL_CODE_LENGTH = 8  # Length of generated referral codes

# Task System
# Task types: 'one_time', 'daily', 'weekly'
# Objective types: 'login', 'mining', 'pixel_art', 'building', 'wallet', 'referral'
DEFAULT_TASKS = [
    # One-time tasks
    {
        'name': 'First Login',
        'description': 'Log in to the game for the first time',
        'task_type': 'one_time',
        'objective_type': 'login',
        'objective_value': 1,
        'token_reward': 2,
        'pixel_reward': 50,
        'experience_reward': 10
    },
    {
        'name': 'Set Up Wallet',
        'description': 'Set up your wallet address to receive tokens',
        'task_type': 'one_time',
        'objective_type': 'wallet',
        'objective_value': 1,
        'token_reward': 5,
        'pixel_reward': 0,
        'experience_reward': 20
    },
    {
        'name': 'First Mine',
        'description': 'Mine pixels for the first time',
        'task_type': 'one_time',
        'objective_type': 'mining',
        'objective_value': 1,
        'token_reward': 3,
        'pixel_reward': 25,
        'experience_reward': 10
    },
    {
        'name': 'First Artwork',
        'description': 'Create your first pixel artwork',
        'task_type': 'one_time',
        'objective_type': 'pixel_art',
        'objective_value': 1,
        'token_reward': 5,
        'pixel_reward': 0,
        'experience_reward': 15
    },
    {
        'name': 'First Building',
        'description': 'Purchase your first building',
        'task_type': 'one_time',
        'objective_type': 'building',
        'objective_value': 1,
        'token_reward': 10,
        'pixel_reward': 0,
        'experience_reward': 25
    },
    {
        'name': 'First Referral',
        'description': 'Refer your first friend to the game',
        'task_type': 'one_time',
        'objective_type': 'referral',
        'objective_value': 1,
        'token_reward': 10,
        'pixel_reward': 100,
        'experience_reward': 50
    },
    
    # Daily tasks
    {
        'name': 'Daily Login',
        'description': 'Log in to the game today',
        'task_type': 'daily',
        'objective_type': 'login',
        'objective_value': 1,
        'token_reward': 1,
        'pixel_reward': 10,
        'experience_reward': 5
    },
    {
        'name': 'Daily Mining',
        'description': 'Mine 3 times today',
        'task_type': 'daily',
        'objective_type': 'mining',
        'objective_value': 3,
        'token_reward': 2,
        'pixel_reward': 30,
        'experience_reward': 10
    },
    {
        'name': 'Daily Creation',
        'description': 'Create 2 pixel artworks today',
        'task_type': 'daily',
        'objective_type': 'pixel_art',
        'objective_value': 2,
        'token_reward': 3,
        'pixel_reward': 0,
        'experience_reward': 15
    },
    
    # Weekly tasks
    {
        'name': 'Building Collector',
        'description': 'Purchase 5 buildings this week',
        'task_type': 'weekly',
        'objective_type': 'building',
        'objective_value': 5,
        'token_reward': 15,
        'pixel_reward': 100,
        'experience_reward': 50
    },
    {
        'name': 'Mining Marathon',
        'description': 'Mine 20 times this week',
        'task_type': 'weekly',
        'objective_type': 'mining',
        'objective_value': 20,
        'token_reward': 10,
        'pixel_reward': 200,
        'experience_reward': 40
    },
    {
        'name': 'Art Gallery',
        'description': 'Create 10 pixel artworks this week',
        'task_type': 'weekly',
        'objective_type': 'pixel_art',
        'objective_value': 10,
        'token_reward': 12,
        'pixel_reward': 0,
        'experience_reward': 45
    },
    {
        'name': 'Community Builder',
        'description': 'Refer 3 friends this week',
        'task_type': 'weekly',
        'objective_type': 'referral',
        'objective_value': 3,
        'token_reward': 20,
        'pixel_reward': 200,
        'experience_reward': 100
    }
]

# Game Economy
DAILY_REWARD = 5  # Base daily reward
DAILY_STREAK_BONUS = 0.5  # Additional reward per day of streak
MINING_REWARD_MIN = 1
MINING_REWARD_MAX = 3
MINING_ENERGY_COST = 10
MINING_PIXEL_GAIN = 20
MINING_MATERIAL_CHANCE = 0.3  # 30% chance to find materials while mining
MINING_MATERIAL_MIN = 1
MINING_MATERIAL_MAX = 5
MINING_GEM_CHANCE = 0.05  # 5% chance to find gems while mining
MINING_GEM_MIN = 1
MINING_GEM_MAX = 2

ART_TOKEN_REWARD_MIN = 3
ART_TOKEN_REWARD_MAX = 10
ART_ENERGY_COST = 20
ART_PIXEL_COST = 50
ART_GEM_CHANCE = 0.1  # 10% chance to find gems while creating art
ART_GEM_MIN = 1
ART_GEM_MAX = 3

# Building types and their properties
BUILDING_TYPES = {
    'mine': {
        'name': 'Pixel Mine',
        'description': 'Produces pixels over time',
        'base_cost': 10,
        'produces': 'pixels',
        'production_rate': 10,  # Pixels per collection
        'material_cost': 0,
        'level_multiplier': 1.5  # Production increases by this factor per level
    },
    'studio': {
        'name': 'Art Studio',
        'description': 'Creates pixel art and generates tokens',
        'base_cost': 25,
        'produces': 'tokens',
        'production_rate': 2,  # Tokens per collection
        'material_cost': 10,
        'level_multiplier': 1.3
    },
    'factory': {
        'name': 'Material Factory',
        'description': 'Produces building materials',
        'base_cost': 50,
        'produces': 'materials',
        'production_rate': 5,  # Materials per collection
        'material_cost': 20,
        'level_multiplier': 1.4
    },
    'market': {
        'name': 'Pixel Marketplace',
        'description': 'Reduces market fees and increases trading profits',
        'base_cost': 75,
        'produces': 'tokens',
        'production_rate': 5,  # Tokens per collection
        'material_cost': 30,
        'level_multiplier': 1.2
    },
    'bank': {
        'name': 'Token Bank',
        'description': 'Generates interest on your token balance',
        'base_cost': 100,
        'produces': 'tokens',
        'production_rate': 0.01,  # % of balance per collection
        'material_cost': 50,
        'level_multiplier': 1.2
    }
}

BUILDING_COST_BASE = 10
BUILDING_COST_MULTIPLIER = 1.5
BUILDING_INCOME_BASE = 1
COLLECTION_COOLDOWN_HOURS = 4
BUILDING_UPGRADE_MULTIPLIER = 2.0  # Cost multiplier for each level upgrade

# Market economy
MARKET_FEE_PERCENTAGE = 5  # 5% fee on market transactions
MARKET_ORDER_EXPIRY_DAYS = 7  # Orders expire after 7 days
MARKET_MIN_TOKEN_BALANCE = 1.0  # Minimum token balance required to place orders
MARKET_MAX_ACTIVE_ORDERS = 5  # Maximum active orders per user
MARKET_PRICE_FLUCTUATION = 0.1  # 10% max random price fluctuation daily

# Skill progression
SKILL_UP_THRESHOLD = 100  # Actions needed to level up a skill
SKILL_LEVEL_BONUS = 0.1  # 10% bonus per skill level

# Event system
EVENT_CHANCE_DAILY = 0.2  # 20% chance of a random event each day
EVENT_DURATION_DAYS_MIN = 1
EVENT_DURATION_DAYS_MAX = 7

# Progression
XP_PER_LEVEL = 100  # Experience points needed per level

# Telegram Bot Configuration
import os
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "")

# Mini-Games System
MINI_GAME_COOLDOWN_HOURS = 12  # Hours before a player can play the same mini-game again
MINI_GAME_TOKEN_REWARDS = {
    'pixel_match': 5,
    'token_puzzle': 7,
    'resource_rush': 6,
    'gem_hunter': 8,
    'pattern_predictor': 10
}
MINI_GAME_RESOURCE_REWARDS = {
    'pixel_match': {
        'pixels': 50,
        'materials': 10,
        'gems': 1
    },
    'token_puzzle': {
        'pixels': 30,
        'materials': 20,
        'gems': 2
    },
    'resource_rush': {
        'pixels': 100,
        'materials': 25,
        'gems': 1
    },
    'gem_hunter': {
        'pixels': 30,
        'materials': 15,
        'gems': 5
    },
    'pattern_predictor': {
        'pixels': 40,
        'materials': 20,
        'gems': 3
    }
}
MINI_GAME_XP_REWARDS = {
    'pixel_match': 20,
    'token_puzzle': 25,
    'resource_rush': 20,
    'gem_hunter': 30,
    'pattern_predictor': 35
}

# Token Economy
MAX_SUPPLY = 1000000  # Maximum token supply
AIRDROP_ALLOCATION = 100000  # Tokens allocated for airdrop
TEAM_ALLOCATION = 200000  # Tokens allocated for team
RESERVE_ALLOCATION = 200000  # Tokens allocated for future development
COMMUNITY_ALLOCATION = 500000  # Tokens allocated for community incentives