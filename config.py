import os

# Telegram Bot Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# Flask Web Application Configuration
FLASK_SECRET_KEY = os.environ.get("SESSION_SECRET", "pixel_plaza_secret_key")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///pixel_plaza.db")

# Game Configuration
DAILY_REWARD = 10  # Base $PXPT tokens awarded daily
MAX_ENERGY = 100  # Maximum energy a player can have
ENERGY_REGEN_RATE = 10  # Energy regenerated per hour
XP_PER_LEVEL = 100  # Experience points needed to level up

# Economy Simulation Parameters
MINING_REWARD = 0.5  # $PXPT tokens per mining action
BUILDING_COST = 50  # $PXPT tokens to purchase a building
BUILDING_INCOME = 1  # $PXPT tokens generated per building per day
PIXEL_ART_COST = 10  # Pixels required to create pixel art
PIXEL_ART_REWARD = 2  # $PXPT tokens rewarded for creating pixel art

# Referral System
REFERRAL_CODE_LENGTH = 8  # Length of referral codes
REFERRAL_BONUS = 5  # $PXPT tokens for successful referrals
REFERRAL_BONUS_REFEREE = 3  # $PXPT tokens for the person who used a referral code
REFERRER_LEVEL_REQUIREMENT = 2  # Minimum level to generate a referral code

# Task System
DAILY_TASK_RESET_HOUR = 0  # Hour of the day to reset daily tasks (UTC)
WEEKLY_TASK_RESET_DAY = 0  # Day of the week to reset weekly tasks (0 = Monday)

# Task Rewards - One-time tasks
TASK_REWARD_FIRST_MINE = 2  # $PXPT for first mining action
TASK_REWARD_FIRST_ART = 3  # $PXPT for first art creation
TASK_REWARD_FIRST_BUILDING = 5  # $PXPT for first building purchase
TASK_REWARD_SET_WALLET = 5  # $PXPT for setting wallet address

# Task Rewards - Daily tasks
TASK_REWARD_DAILY_MINE_5 = 3  # $PXPT for mining 5 times in a day
TASK_REWARD_DAILY_ART_3 = 5  # $PXPT for creating 3 pixel arts in a day

# Task Rewards - Weekly tasks
TASK_REWARD_WEEKLY_LOGIN_5 = 10  # $PXPT for logging in 5 days in a week
TASK_REWARD_WEEKLY_REFERRAL = 15  # $PXPT for referring a new user in a week

# Token Distribution
AIRDROP_POOL = 1000000  # Total $PXPT tokens in the airdrop pool
