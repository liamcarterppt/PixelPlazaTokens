import os

# Telegram Bot Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# Flask Web Application Configuration
FLASK_SECRET_KEY = os.environ.get("SESSION_SECRET", "pixel_plaza_secret_key")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///pixel_plaza.db")

# Game Configuration
DAILY_REWARD = 10  # Base $PXPT tokens awarded daily
REFERRAL_BONUS = 5  # $PXPT tokens for successful referrals
MAX_ENERGY = 100  # Maximum energy a player can have
ENERGY_REGEN_RATE = 10  # Energy regenerated per hour
XP_PER_LEVEL = 100  # Experience points needed to level up

# Economy Simulation Parameters
MINING_REWARD = 0.5  # $PXPT tokens per mining action
BUILDING_COST = 50  # $PXPT tokens to purchase a building
BUILDING_INCOME = 1  # $PXPT tokens generated per building per day
PIXEL_ART_COST = 10  # Pixels required to create pixel art
PIXEL_ART_REWARD = 2  # $PXPT tokens rewarded for creating pixel art

# Token Distribution
AIRDROP_POOL = 1000000  # Total $PXPT tokens in the airdrop pool
