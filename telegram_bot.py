#!/usr/bin/env python
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import datetime
from models import User, GameState, Transaction
from app import db
from config import (
    TELEGRAM_TOKEN, WEBHOOK_URL, DAILY_REWARD, REFERRAL_BONUS,
    MINING_REWARD, BUILDING_COST, BUILDING_INCOME, PIXEL_ART_COST, PIXEL_ART_REWARD
)
from game_mechanics import GameMechanics

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize game mechanics
game = GameMechanics()

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name
    
    # Check if user exists in database
    existing_user = User.query.filter_by(telegram_id=telegram_id).first()
    
    # Check for referral
    referrer_id = None
    if context.args and len(context.args) > 0:
        referrer_id = context.args[0]
    
    if not existing_user:
        # Create new user
        new_user = User(
            username=username,
            telegram_id=telegram_id,
        )
        db.session.add(new_user)
        db.session.flush()  # Flush to get the ID without committing
        
        # Create initial game state
        new_game_state = GameState(
            user_id=new_user.id,
            token_balance=DAILY_REWARD,  # Initial tokens
        )
        db.session.add(new_game_state)
        
        # Record initial transaction
        welcome_transaction = Transaction(
            user_id=new_user.id,
            type='welcome_bonus',
            amount=DAILY_REWARD,
            description=f'Welcome bonus of {DAILY_REWARD} $PXPT'
        )
        db.session.add(welcome_transaction)
        
        # Process referral if provided
        if referrer_id:
            referrer = User.query.filter_by(telegram_id=referrer_id).first()
            if referrer and referrer.id != new_user.id:  # Prevent self-referral
                # Give bonus to referrer
                referrer_game_state = GameState.query.filter_by(user_id=referrer.id).first()
                if referrer_game_state:
                    referrer_game_state.token_balance += REFERRAL_BONUS
                    
                    # Record referral transaction
                    referral_transaction = Transaction(
                        user_id=referrer.id,
                        type='referral_bonus',
                        amount=REFERRAL_BONUS,
                        description=f'Referral bonus for inviting {username}'
                    )
                    db.session.add(referral_transaction)
        
        db.session.commit()
        
        await update.message.reply_text(
            f"Welcome to Pixel Plaza, {username}! 🏙️\n\n"
            f"You've received {DAILY_REWARD} $PXPT tokens as a welcome bonus! Start building your pixel empire and earn more tokens.\n\n"
            f"Use /help to see all available commands."
        )
    else:
        # User already exists
        await update.message.reply_text(
            f"Welcome back to Pixel Plaza, {username}! 🏙️\n\n"
            f"Continue building your pixel empire and earning $PXPT tokens.\n\n"
            f"Use /help to see all available commands."
        )
    
    # Show main menu
    await show_main_menu(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "🏙️ *Pixel Plaza Token ($PXPT) Game Commands* 🏙️\n\n"
        "*Basic Commands:*\n"
        "/start - Start the game\n"
        "/help - Show this help message\n"
        "/profile - View your profile\n"
        "/wallet - Set or view your wallet address\n\n"
        
        "*Game Commands:*\n"
        "/daily - Claim daily reward\n"
        "/mine - Mine for $PXPT tokens\n"
        "/create - Create pixel art for rewards\n"
        "/build - Purchase buildings for passive income\n"
        "/collect - Collect income from your buildings\n\n"
        
        "*Community Commands:*\n"
        "/leaderboard - View top players\n"
        "/invite - Get your referral link\n"
        "/stats - View game statistics\n\n"
        
        "*Web Dashboard:*\n"
        "/dashboard - Access your web dashboard\n\n"
        
        "Build your pixel empire and earn $PXPT tokens for the upcoming airdrop! 🚀"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display user profile information."""
    telegram_id = str(update.effective_user.id)
    user = User.query.filter_by(telegram_id=telegram_id).first()
    
    if not user:
        await update.message.reply_text("You need to start the game first! Use /start command.")
        return
    
    game_state = GameState.query.filter_by(user_id=user.id).first()
    
    if not game_state:
        await update.message.reply_text("Error retrieving your game state. Please contact support.")
        return
    
    profile_text = (
        f"🏙️ *Pixel Plaza Profile for {user.username}* 🏙️\n\n"
        f"*$PXPT Balance:* {game_state.token_balance:.2f} tokens\n"
        f"*Level:* {game_state.level}\n"
        f"*Experience:* {game_state.experience}/{game_state.level * 100}\n\n"
        
        f"*Game Statistics:*\n"
        f"🏢 Buildings Owned: {game_state.buildings_owned}\n"
        f"🎨 Pixel Art Created: {game_state.pixel_art_created}\n"
        f"🔋 Energy: {game_state.energy}/{100}\n"
        f"🖌️ Pixels: {game_state.pixels}\n"
        f"🔥 Daily Streak: {game_state.daily_streak} days\n\n"
        
        f"*Wallet:* {user.wallet_address if user.wallet_address else 'Not set. Use /wallet to set'}\n\n"
        
        f"Member since: {user.registration_date.strftime('%Y-%m-%d')}"
    )
    
    await update.message.reply_text(profile_text, parse_mode='Markdown')

async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set or view wallet address."""
    telegram_id = str(update.effective_user.id)
    user = User.query.filter_by(telegram_id=telegram_id).first()
    
    if not user:
        await update.message.reply_text("You need to start the game first! Use /start command.")
        return
    
    # Check if a wallet address is provided
    if context.args and len(context.args) > 0:
        wallet_address = context.args[0]
        
        # Simple validation (should be more robust in production)
        if not wallet_address.startswith('0x') or len(wallet_address) != 42:
            await update.message.reply_text(
                "Invalid Ethereum wallet address format. Please provide a valid ERC-20 compatible address."
            )
            return
        
        # Update user's wallet address
        user.wallet_address = wallet_address
        db.session.commit()
        
        await update.message.reply_text(
            f"Your wallet address has been set to: {wallet_address}\n\n"
            f"You'll receive your $PXPT tokens to this address during the airdrop."
        )
    else:
        # Display current wallet address
        if user.wallet_address:
            await update.message.reply_text(
                f"Your current wallet address: {user.wallet_address}\n\n"
                f"To update it, use /wallet [new_address]"
            )
        else:
            await update.message.reply_text(
                "You haven't set your wallet address yet. Please set it to be eligible for the airdrop.\n\n"
                "Use /wallet [your_address] to set your ERC-20 compatible wallet address."
            )

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Claim daily reward."""
    telegram_id = str(update.effective_user.id)
    user = User.query.filter_by(telegram_id=telegram_id).first()
    
    if not user:
        await update.message.reply_text("You need to start the game first! Use /start command.")
        return
    
    game_state = GameState.query.filter_by(user_id=user.id).first()
    
    if not game_state:
        await update.message.reply_text("Error retrieving your game state. Please contact support.")
        return
    
    # Check if user can claim daily reward
    now = datetime.datetime.utcnow()
    if game_state.last_daily_claim is not None:
        time_since_last_claim = now - game_state.last_daily_claim
        if time_since_last_claim.days < 1:
            next_claim_time = game_state.last_daily_claim + datetime.timedelta(days=1)
            hours_remaining = (next_claim_time - now).seconds // 3600
            minutes_remaining = ((next_claim_time - now).seconds % 3600) // 60
            
            await update.message.reply_text(
                f"You've already claimed your daily reward today.\n"
                f"Next claim available in: {hours_remaining}h {minutes_remaining}m"
            )
            return
    
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
    game_state.energy = min(game_state.energy + 50, 100)  # Refill some energy
    
    # Record transaction
    daily_transaction = Transaction(
        user_id=user.id,
        type='daily_reward',
        amount=total_reward,
        description=f'Daily reward ({game_state.daily_streak} day streak)'
    )
    db.session.add(daily_transaction)
    
    db.session.commit()
    
    await update.message.reply_text(
        f"✅ Daily reward claimed!\n\n"
        f"🪙 Received: {total_reward} $PXPT\n"
        f"🔥 Current streak: {game_state.daily_streak} days\n"
        f"⚡ Energy refilled: +50\n\n"
        f"Current balance: {game_state.token_balance:.2f} $PXPT"
    )

async def mine_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mine for $PXPT tokens."""
    telegram_id = str(update.effective_user.id)
    user = User.query.filter_by(telegram_id=telegram_id).first()
    
    if not user:
        await update.message.reply_text("You need to start the game first! Use /start command.")
        return
    
    game_state = GameState.query.filter_by(user_id=user.id).first()
    
    if not game_state:
        await update.message.reply_text("Error retrieving your game state. Please contact support.")
        return
    
    # Check if user has enough energy
    if game_state.energy < 10:
        await update.message.reply_text(
            "⚠️ Not enough energy to mine!\n\n"
            f"Current energy: {game_state.energy}/100\n"
            f"Required: 10 energy\n\n"
            f"Energy regenerates over time or claim your daily reward."
        )
        return
    
    # Process mining action
    reward = MINING_REWARD * game_state.level  # Scale reward with level
    pixels_found = 5 + (game_state.level - 1)  # Scale pixels with level
    
    # Update game state
    game_state.token_balance += reward
    game_state.energy -= 10
    game_state.pixels += pixels_found
    game_state.experience += 5
    
    # Check if level up
    if game_state.experience >= game_state.level * 100:
        game_state.experience -= game_state.level * 100
        game_state.level += 1
        level_up_message = f"\n🎉 Level Up! You're now level {game_state.level}!"
    else:
        level_up_message = ""
    
    # Record transaction
    mining_transaction = Transaction(
        user_id=user.id,
        type='mining',
        amount=reward,
        description=f'Mining reward'
    )
    db.session.add(mining_transaction)
    
    db.session.commit()
    
    await update.message.reply_text(
        f"⛏️ Mining successful!\n\n"
        f"🪙 Earned: {reward} $PXPT\n"
        f"🖌️ Pixels found: {pixels_found}\n"
        f"⚡ Energy used: 10\n"
        f"📈 XP gained: 5{level_up_message}\n\n"
        f"Current balance: {game_state.token_balance:.2f} $PXPT\n"
        f"Pixels: {game_state.pixels}\n"
        f"Energy: {game_state.energy}/100"
    )

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create pixel art for rewards."""
    telegram_id = str(update.effective_user.id)
    user = User.query.filter_by(telegram_id=telegram_id).first()
    
    if not user:
        await update.message.reply_text("You need to start the game first! Use /start command.")
        return
    
    game_state = GameState.query.filter_by(user_id=user.id).first()
    
    if not game_state:
        await update.message.reply_text("Error retrieving your game state. Please contact support.")
        return
    
    # Check if user has enough pixels and energy
    if game_state.pixels < PIXEL_ART_COST:
        await update.message.reply_text(
            f"⚠️ Not enough pixels to create art!\n\n"
            f"Current pixels: {game_state.pixels}\n"
            f"Required: {PIXEL_ART_COST} pixels\n\n"
            f"Mine more pixels using /mine command."
        )
        return
    
    if game_state.energy < 15:
        await update.message.reply_text(
            "⚠️ Not enough energy to create art!\n\n"
            f"Current energy: {game_state.energy}/100\n"
            f"Required: 15 energy\n\n"
            f"Energy regenerates over time or claim your daily reward."
        )
        return
    
    # Process creation action
    reward = PIXEL_ART_REWARD * game_state.level  # Scale reward with level
    
    # Update game state
    game_state.token_balance += reward
    game_state.pixels -= PIXEL_ART_COST
    game_state.energy -= 15
    game_state.pixel_art_created += 1
    game_state.experience += 10
    
    # Check if level up
    if game_state.experience >= game_state.level * 100:
        game_state.experience -= game_state.level * 100
        game_state.level += 1
        level_up_message = f"\n🎉 Level Up! You're now level {game_state.level}!"
    else:
        level_up_message = ""
    
    # Record transaction
    creation_transaction = Transaction(
        user_id=user.id,
        type='pixel_art',
        amount=reward,
        description=f'Pixel art creation reward'
    )
    db.session.add(creation_transaction)
    
    db.session.commit()
    
    await update.message.reply_text(
        f"🎨 Pixel art created successfully!\n\n"
        f"🪙 Earned: {reward} $PXPT\n"
        f"🖌️ Pixels used: {PIXEL_ART_COST}\n"
        f"⚡ Energy used: 15\n"
        f"📈 XP gained: 10{level_up_message}\n\n"
        f"Current balance: {game_state.token_balance:.2f} $PXPT\n"
        f"Total pixel art created: {game_state.pixel_art_created}"
    )

async def build_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Purchase buildings for passive income."""
    telegram_id = str(update.effective_user.id)
    user = User.query.filter_by(telegram_id=telegram_id).first()
    
    if not user:
        await update.message.reply_text("You need to start the game first! Use /start command.")
        return
    
    game_state = GameState.query.filter_by(user_id=user.id).first()
    
    if not game_state:
        await update.message.reply_text("Error retrieving your game state. Please contact support.")
        return
    
    # Check if user has enough tokens
    building_cost = BUILDING_COST + (game_state.buildings_owned * 10)  # Cost increases with more buildings
    
    if game_state.token_balance < building_cost:
        await update.message.reply_text(
            f"⚠️ Not enough $PXPT to purchase a building!\n\n"
            f"Current balance: {game_state.token_balance:.2f} $PXPT\n"
            f"Building cost: {building_cost} $PXPT\n\n"
            f"Earn more tokens and try again."
        )
        return
    
    # Process building purchase
    game_state.token_balance -= building_cost
    game_state.buildings_owned += 1
    game_state.experience += 20
    
    # Check if level up
    if game_state.experience >= game_state.level * 100:
        game_state.experience -= game_state.level * 100
        game_state.level += 1
        level_up_message = f"\n🎉 Level Up! You're now level {game_state.level}!"
    else:
        level_up_message = ""
    
    # Record transaction
    building_transaction = Transaction(
        user_id=user.id,
        type='building_purchase',
        amount=-building_cost,
        description=f'Building purchase'
    )
    db.session.add(building_transaction)
    
    db.session.commit()
    
    daily_income = BUILDING_INCOME * game_state.buildings_owned
    
    await update.message.reply_text(
        f"🏢 Building purchased successfully!\n\n"
        f"🪙 Cost: {building_cost} $PXPT\n"
        f"🏢 Buildings owned: {game_state.buildings_owned}\n"
        f"💰 Daily income: {daily_income} $PXPT\n"
        f"📈 XP gained: 20{level_up_message}\n\n"
        f"Current balance: {game_state.token_balance:.2f} $PXPT\n\n"
        f"Collect your building income with /collect command"
    )

async def collect_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Collect income from buildings."""
    telegram_id = str(update.effective_user.id)
    user = User.query.filter_by(telegram_id=telegram_id).first()
    
    if not user:
        await update.message.reply_text("You need to start the game first! Use /start command.")
        return
    
    game_state = GameState.query.filter_by(user_id=user.id).first()
    
    if not game_state:
        await update.message.reply_text("Error retrieving your game state. Please contact support.")
        return
    
    # Check if user has buildings
    if game_state.buildings_owned == 0:
        await update.message.reply_text(
            "You don't have any buildings yet. Purchase buildings with /build command first."
        )
        return
    
    # Calculate income
    now = datetime.datetime.utcnow()
    last_transaction = Transaction.query.filter_by(
        user_id=user.id, 
        type='building_income'
    ).order_by(Transaction.timestamp.desc()).first()
    
    if last_transaction and (now - last_transaction.timestamp).seconds < 86400:  # 24 hours in seconds
        next_collection_time = last_transaction.timestamp + datetime.timedelta(days=1)
        hours_remaining = (next_collection_time - now).seconds // 3600
        minutes_remaining = ((next_collection_time - now).seconds % 3600) // 60
        
        await update.message.reply_text(
            f"You've already collected your building income today.\n"
            f"Next collection available in: {hours_remaining}h {minutes_remaining}m"
        )
        return
    
    # Calculate income based on buildings owned
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
    
    await update.message.reply_text(
        f"💰 Building income collected!\n\n"
        f"🏢 Buildings: {game_state.buildings_owned}\n"
        f"🪙 Income: {income} $PXPT\n\n"
        f"Current balance: {game_state.token_balance:.2f} $PXPT"
    )

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show token leaderboard."""
    # Get top 10 users by token balance
    top_users = db.session.query(
        User, GameState
    ).join(
        GameState, User.id == GameState.user_id
    ).order_by(
        GameState.token_balance.desc()
    ).limit(10).all()
    
    if not top_users:
        await update.message.reply_text("No users found in the leaderboard yet.")
        return
    
    leaderboard_text = "🏆 *$PXPT Token Leaderboard* 🏆\n\n"
    
    for i, (user, game_state) in enumerate(top_users):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        leaderboard_text += f"{medal} {user.username}: {game_state.token_balance:.2f} $PXPT (Level {game_state.level})\n"
    
    # Add a note about web dashboard
    leaderboard_text += "\nView the full leaderboard on the web dashboard: /dashboard"
    
    await update.message.reply_text(leaderboard_text, parse_mode='Markdown')

async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a referral link."""
    telegram_id = str(update.effective_user.id)
    user = User.query.filter_by(telegram_id=telegram_id).first()
    
    if not user:
        await update.message.reply_text("You need to start the game first! Use /start command.")
        return
    
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={telegram_id}"
    
    await update.message.reply_text(
        f"🔗 *Your Referral Link* 🔗\n\n"
        f"{referral_link}\n\n"
        f"Share this link with friends! You'll earn {REFERRAL_BONUS} $PXPT for each new user who joins using your link.\n\n"
        f"*Note:* Your friends must set up their wallet address with /wallet command for you to receive the bonus.",
        parse_mode='Markdown'
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show game statistics."""
    # Get global statistics
    total_users = User.query.count()
    total_tokens = db.session.query(db.func.sum(GameState.token_balance)).scalar() or 0
    total_buildings = db.session.query(db.func.sum(GameState.buildings_owned)).scalar() or 0
    total_pixel_art = db.session.query(db.func.sum(GameState.pixel_art_created)).scalar() or 0
    
    stats_text = (
        "📊 *Pixel Plaza Game Statistics* 📊\n\n"
        f"👥 Total Players: {total_users}\n"
        f"🪙 Total $PXPT in Circulation: {total_tokens:.2f}\n"
        f"🏢 Total Buildings: {total_buildings}\n"
        f"🎨 Total Pixel Art Created: {total_pixel_art}\n\n"
        
        f"*Token Information:*\n"
        f"Name: Pixel Plaza Token\n"
        f"Symbol: $PXPT\n"
        f"Total Supply: 1,000,000,000 $PXPT\n"
        f"Airdrop Pool: 1,000,000 $PXPT\n\n"
        
        f"*Top Community Contributors:*\n"
    )
    
    # Get top 3 contributors
    top_contributors = db.session.query(
        User, GameState
    ).join(
        GameState, User.id == GameState.user_id
    ).order_by(
        (GameState.buildings_owned + GameState.pixel_art_created).desc()
    ).limit(3).all()
    
    for i, (user, game_state) in enumerate(top_contributors):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
        stats_text += f"{medal} {user.username}: {game_state.buildings_owned + game_state.pixel_art_created} contributions\n"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide web dashboard link."""
    telegram_id = str(update.effective_user.id)
    user = User.query.filter_by(telegram_id=telegram_id).first()
    
    if not user:
        await update.message.reply_text("You need to start the game first! Use /start command.")
        return
    
    # Generate dashboard link with user's Telegram ID
    dashboard_url = f"http://0.0.0.0:5000/dashboard?id={telegram_id}"
    
    # Create button for the dashboard
    keyboard = [
        [InlineKeyboardButton("Open Web Dashboard", url=dashboard_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📱 *Pixel Plaza Web Dashboard* 📱\n\n"
        "Access your personal dashboard to view detailed statistics, manage your pixel empire, and track your progress.\n\n"
        "Click the button below to open the dashboard:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main menu with buttons."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Profile", callback_data="profile"),
            InlineKeyboardButton("🪙 Daily Claim", callback_data="daily")
        ],
        [
            InlineKeyboardButton("⛏️ Mine", callback_data="mine"),
            InlineKeyboardButton("🎨 Create Art", callback_data="create")
        ],
        [
            InlineKeyboardButton("🏢 Build", callback_data="build"),
            InlineKeyboardButton("💰 Collect", callback_data="collect")
        ],
        [
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
            InlineKeyboardButton("🔗 Invite", callback_data="invite")
        ],
        [
            InlineKeyboardButton("🌐 Dashboard", callback_data="dashboard"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏙️ *Welcome to Pixel Plaza Token ($PXPT) Game* 🏙️\n\n"
        "Build your pixel empire, earn $PXPT tokens, and join our upcoming airdrop!\n\n"
        "Select an action from the menu below:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    # Map callback data to commands
    command_map = {
        "profile": profile_command,
        "daily": daily_command,
        "mine": mine_command,
        "create": create_command,
        "build": build_command,
        "collect": collect_command,
        "leaderboard": leaderboard_command,
        "invite": invite_command,
        "dashboard": dashboard_command,
        "help": help_command
    }
    
    # Execute the corresponding command
    if query.data in command_map:
        await command_map[query.data](update, context)
    
    # Show menu again after action
    await show_main_menu(update, context)

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("wallet", wallet_command))
    application.add_handler(CommandHandler("daily", daily_command))
    application.add_handler(CommandHandler("mine", mine_command))
    application.add_handler(CommandHandler("create", create_command))
    application.add_handler(CommandHandler("build", build_command))
    application.add_handler(CommandHandler("collect", collect_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("invite", invite_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("menu", show_main_menu))
    
    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
