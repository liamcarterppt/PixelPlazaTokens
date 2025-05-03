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
ART_TOKEN_REWARD_MIN = 3
ART_TOKEN_REWARD_MAX = 10
ART_ENERGY_COST = 20
ART_PIXEL_COST = 50
BUILDING_COST_BASE = 10
BUILDING_COST_MULTIPLIER = 1.5
BUILDING_INCOME_BASE = 1
COLLECTION_COOLDOWN_HOURS = 4

# Progression
XP_PER_LEVEL = 100  # Experience points needed per level

# Token Economy
MAX_SUPPLY = 1000000  # Maximum token supply
AIRDROP_ALLOCATION = 100000  # Tokens allocated for airdrop
TEAM_ALLOCATION = 200000  # Tokens allocated for team
RESERVE_ALLOCATION = 200000  # Tokens allocated for future development
COMMUNITY_ALLOCATION = 500000  # Tokens allocated for community incentives