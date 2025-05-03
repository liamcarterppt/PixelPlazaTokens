import random
import string
import logging
from datetime import datetime, timedelta
from models import User, GameState, Transaction, Task, UserTask
from app import db
from config import (
    REFERRAL_CODE_LENGTH, REFERRAL_BONUS, REFERRAL_BONUS_REFEREE,
    TASK_REWARD_FIRST_MINE, TASK_REWARD_FIRST_ART, TASK_REWARD_FIRST_BUILDING, TASK_REWARD_SET_WALLET,
    TASK_REWARD_DAILY_MINE_5, TASK_REWARD_DAILY_ART_3,
    TASK_REWARD_WEEKLY_LOGIN_5, TASK_REWARD_WEEKLY_REFERRAL,
    DAILY_TASK_RESET_HOUR, WEEKLY_TASK_RESET_DAY
)

logger = logging.getLogger(__name__)

def generate_referral_code(length=REFERRAL_CODE_LENGTH):
    """Generate a unique referral code."""
    while True:
        # Generate a random string of letters and numbers
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        
        # Check if code is unique
        if User.query.filter_by(referral_code=code).first() is None:
            return code

def process_referral(referrer_id, referee):
    """Process a referral and award bonuses."""
    try:
        # Get the referrer
        referrer = User.query.get(referrer_id)
        if not referrer:
            logger.error(f"Referrer with ID {referrer_id} not found")
            return False
        
        referrer_game_state = GameState.query.filter_by(user_id=referrer.id).first()
        if not referrer_game_state:
            logger.error(f"Game state for referrer with ID {referrer_id} not found")
            return False
        
        referee_game_state = GameState.query.filter_by(user_id=referee.id).first()
        if not referee_game_state:
            logger.error(f"Game state for referee with ID {referee.id} not found")
            return False
        
        # Award bonuses
        # Bonus for referrer
        referrer_game_state.token_balance += REFERRAL_BONUS
        referrer_game_state.referral_count += 1
        
        # Record transaction for referrer
        referrer_transaction = Transaction(
            user_id=referrer.id,
            type='referral_bonus',
            amount=REFERRAL_BONUS,
            description=f'Referral bonus for inviting {referee.username}'
        )
        db.session.add(referrer_transaction)
        
        # Bonus for referee
        referee_game_state.token_balance += REFERRAL_BONUS_REFEREE
        
        # Record transaction for referee
        referee_transaction = Transaction(
            user_id=referee.id,
            type='referee_bonus',
            amount=REFERRAL_BONUS_REFEREE,
            description=f'Bonus for using {referrer.username}\'s referral code'
        )
        db.session.add(referee_transaction)
        
        # Update progress for referral tasks
        update_task_progress(referrer.id, 'referral', 1)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing referral: {str(e)}")
        return False

def initialize_tasks():
    """Initialize the task system with default tasks if they don't exist."""
    try:
        # Check if tasks already exist
        if Task.query.first():
            return
        
        # One-time tasks
        tasks = [
            # One-time tasks
            Task(
                name="First Mining Operation",
                description="Complete your first mining operation",
                task_type="one_time",
                objective_type="mining",
                objective_value=1,
                token_reward=TASK_REWARD_FIRST_MINE,
                experience_reward=5
            ),
            Task(
                name="Pixel Artist",
                description="Create your first pixel art",
                task_type="one_time",
                objective_type="pixel_art",
                objective_value=1,
                token_reward=TASK_REWARD_FIRST_ART,
                experience_reward=10
            ),
            Task(
                name="Property Owner",
                description="Purchase your first building",
                task_type="one_time",
                objective_type="building",
                objective_value=1,
                token_reward=TASK_REWARD_FIRST_BUILDING,
                experience_reward=15
            ),
            Task(
                name="Ready for Airdrop",
                description="Set your wallet address",
                task_type="one_time",
                objective_type="wallet",
                objective_value=1,
                token_reward=TASK_REWARD_SET_WALLET,
                experience_reward=5
            ),
            
            # Daily tasks
            Task(
                name="Daily Miner",
                description="Mine 5 times in a day",
                task_type="daily",
                objective_type="mining",
                objective_value=5,
                token_reward=TASK_REWARD_DAILY_MINE_5,
                experience_reward=10
            ),
            Task(
                name="Artistic Streak",
                description="Create 3 pixel arts in a day",
                task_type="daily",
                objective_type="pixel_art",
                objective_value=3,
                token_reward=TASK_REWARD_DAILY_ART_3,
                experience_reward=15
            ),
            
            # Weekly tasks
            Task(
                name="Dedicated Player",
                description="Log in for 5 days this week",
                task_type="weekly",
                objective_type="login",
                objective_value=5,
                token_reward=TASK_REWARD_WEEKLY_LOGIN_5,
                experience_reward=20
            ),
            Task(
                name="Community Builder",
                description="Refer a new user this week",
                task_type="weekly",
                objective_type="referral",
                objective_value=1,
                token_reward=TASK_REWARD_WEEKLY_REFERRAL,
                experience_reward=25
            )
        ]
        
        for task in tasks:
            db.session.add(task)
        
        db.session.commit()
        logger.info("Task system initialized with default tasks")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing tasks: {str(e)}")
        return False

def assign_tasks_to_user(user_id):
    """Assign all active tasks to a user if they don't already have them."""
    try:
        # Get all active tasks
        active_tasks = Task.query.filter_by(is_active=True).all()
        
        # Check which tasks the user already has
        existing_user_tasks = UserTask.query.filter_by(user_id=user_id).all()
        existing_task_ids = [ut.task_id for ut in existing_user_tasks]
        
        # Assign tasks that the user doesn't have yet
        for task in active_tasks:
            if task.id not in existing_task_ids:
                user_task = UserTask(
                    user_id=user_id,
                    task_id=task.id,
                    current_progress=0,
                    completed=False
                )
                db.session.add(user_task)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error assigning tasks to user {user_id}: {str(e)}")
        return False

def update_task_progress(user_id, objective_type, increment=1):
    """Update progress for tasks with the given objective type."""
    try:
        # Get user tasks that match the objective type
        user_tasks = db.session.query(UserTask, Task).join(
            Task, UserTask.task_id == Task.id
        ).filter(
            UserTask.user_id == user_id,
            Task.objective_type == objective_type,
            UserTask.completed == False,
            Task.is_active == True
        ).all()
        
        # Update progress for each matching task
        for user_task, task in user_tasks:
            # Only update if the task type matches and isn't already completed
            if (task.task_type == "one_time" or
                should_reset_task(user_task, task) == False):
                
                user_task.current_progress += increment
                
                # Check if task is now completed
                if user_task.current_progress >= task.objective_value:
                    complete_task(user_id, user_task, task)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating task progress for user {user_id}: {str(e)}")
        return False

def should_reset_task(user_task, task):
    """Check if a daily or weekly task should be reset based on its last reset time."""
    now = datetime.utcnow()
    
    if task.task_type == "daily":
        # Reset if last reset was before today's reset hour
        reset_time = datetime(now.year, now.month, now.day, DAILY_TASK_RESET_HOUR)
        if now < reset_time:
            reset_time -= timedelta(days=1)
        
        if user_task.last_reset < reset_time:
            user_task.current_progress = 0
            user_task.completed = False
            user_task.last_reset = now
            return True
    
    elif task.task_type == "weekly":
        # Calculate the last weekly reset time
        days_since_reset_day = (now.weekday() - WEEKLY_TASK_RESET_DAY) % 7
        last_reset = now - timedelta(days=days_since_reset_day)
        reset_time = datetime(last_reset.year, last_reset.month, last_reset.day, DAILY_TASK_RESET_HOUR)
        
        if user_task.last_reset < reset_time:
            user_task.current_progress = 0
            user_task.completed = False
            user_task.last_reset = now
            return True
    
    return False

def complete_task(user_id, user_task, task):
    """Process task completion and award rewards."""
    try:
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return False
        
        game_state = GameState.query.filter_by(user_id=user_id).first()
        if not game_state:
            logger.error(f"Game state for user with ID {user_id} not found")
            return False
        
        # Mark task as completed
        user_task.completed = True
        user_task.completed_at = datetime.utcnow()
        
        # Update game state
        game_state.token_balance += task.token_reward
        game_state.pixels += task.pixel_reward
        game_state.experience += task.experience_reward
        game_state.tasks_completed += 1
        
        # Record transaction
        transaction = Transaction(
            user_id=user_id,
            type='task_reward',
            amount=task.token_reward,
            description=f'Reward for completing task: {task.name}'
        )
        db.session.add(transaction)
        
        # Check for level up
        from config import XP_PER_LEVEL
        if game_state.experience >= game_state.level * XP_PER_LEVEL:
            game_state.experience -= game_state.level * XP_PER_LEVEL
            game_state.level += 1
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error completing task for user {user_id}: {str(e)}")
        return False

def get_user_tasks(user_id):
    """Get all tasks for a user with their progress."""
    try:
        # Check for task resets before returning
        user_tasks = db.session.query(UserTask, Task).join(
            Task, UserTask.task_id == Task.id
        ).filter(
            UserTask.user_id == user_id,
            Task.is_active == True
        ).all()
        
        # Check each task for potential reset
        for user_task, task in user_tasks:
            should_reset_task(user_task, task)
        
        db.session.commit()
        
        # Return the updated tasks
        return db.session.query(UserTask, Task).join(
            Task, UserTask.task_id == Task.id
        ).filter(
            UserTask.user_id == user_id,
            Task.is_active == True
        ).all()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error getting tasks for user {user_id}: {str(e)}")
        return []