"""
Utility functions for the Pixel Plaza Token game.
"""

import random
import string
import logging
from datetime import datetime, timedelta

from app import db
from models import User, GameState, Transaction, Task, UserTask
from config import (
    REFERRAL_CODE_LENGTH, REFERRER_BONUS, REFEREE_BONUS, 
    DEFAULT_TASKS
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_referral_code(length=REFERRAL_CODE_LENGTH):
    """Generate a unique referral code."""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        # Check if code already exists
        existing = User.query.filter_by(referral_code=code).first()
        if not existing:
            return code

def process_referral(referrer_id, referee):
    """Process a referral and award bonuses."""
    try:
        # Get referrer
        referrer = User.query.get(referrer_id)
        if not referrer:
            logger.error(f"Referrer with ID {referrer_id} not found")
            return False
        
        # Get game states
        referrer_game_state = GameState.query.filter_by(user_id=referrer.id).first()
        referee_game_state = GameState.query.filter_by(user_id=referee.id).first()
        
        if not referrer_game_state or not referee_game_state:
            logger.error("Game state not found for referrer or referee")
            return False
        
        # Award bonuses
        referrer_game_state.token_balance += REFERRER_BONUS
        referee_game_state.token_balance += REFEREE_BONUS
        
        # Increment referral count
        referrer_game_state.referral_count += 1
        
        # Create transactions
        referrer_transaction = Transaction(
            user_id=referrer.id,
            type='referral_bonus',
            amount=REFERRER_BONUS,
            description=f'Referral bonus for inviting {referee.username}'
        )
        
        referee_transaction = Transaction(
            user_id=referee.id,
            type='referral_bonus',
            amount=REFEREE_BONUS,
            description=f'Bonus for using {referrer.username}\'s referral code'
        )
        
        db.session.add(referrer_transaction)
        db.session.add(referee_transaction)
        
        # Update task progress for referrer
        update_task_progress(referrer.id, 'referral', 1)
        
        db.session.commit()
        logger.info(f"Referral processed: {referrer.username} referred {referee.username}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing referral: {str(e)}")
        return False

def initialize_tasks():
    """Initialize the task system with default tasks if they don't exist."""
    try:
        # Check if tasks already exist
        existing_tasks = Task.query.count()
        if existing_tasks > 0:
            logger.info(f"Tasks already initialized ({existing_tasks} tasks found)")
            return
        
        # Create default tasks
        for task_data in DEFAULT_TASKS:
            task = Task(
                name=task_data['name'],
                description=task_data['description'],
                task_type=task_data['task_type'],
                objective_type=task_data['objective_type'],
                objective_value=task_data['objective_value'],
                token_reward=task_data['token_reward'],
                pixel_reward=task_data['pixel_reward'],
                experience_reward=task_data['experience_reward'],
                is_active=True
            )
            db.session.add(task)
        
        db.session.commit()
        logger.info(f"Task system initialized with {len(DEFAULT_TASKS)} tasks")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing tasks: {str(e)}")

def assign_tasks_to_user(user_id):
    """Assign all active tasks to a user if they don't already have them."""
    try:
        # Get all active tasks
        active_tasks = Task.query.filter_by(is_active=True).all()
        
        # Check which tasks the user already has
        existing_user_tasks = UserTask.query.filter_by(user_id=user_id).all()
        existing_task_ids = [ut.task_id for ut in existing_user_tasks]
        
        # Assign missing tasks
        for task in active_tasks:
            if task.id not in existing_task_ids:
                user_task = UserTask(
                    user_id=user_id,
                    task_id=task.id,
                    current_progress=0,
                    completed=False,
                    last_reset=datetime.utcnow()
                )
                db.session.add(user_task)
        
        db.session.commit()
        logger.info(f"Tasks assigned to user {user_id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error assigning tasks to user {user_id}: {str(e)}")

def update_task_progress(user_id, objective_type, increment=1):
    """Update progress for tasks with the given objective type."""
    try:
        # Get user's tasks for this objective type
        user_tasks = UserTask.query.join(Task).filter(
            UserTask.user_id == user_id,
            Task.objective_type == objective_type,
            Task.is_active == True
        ).all()
        
        # Update each matching task
        for user_task in user_tasks:
            task = Task.query.get(user_task.task_id)
            
            # Check if daily/weekly tasks need to be reset
            if should_reset_task(user_task, task):
                user_task.current_progress = 0
                user_task.completed = False
                user_task.last_reset = datetime.utcnow()
            
            # Only update if task is not already completed
            if not user_task.completed:
                user_task.current_progress += increment
                
                # Check if task is now completed
                if user_task.current_progress >= task.objective_value:
                    user_task.completed = True
                    user_task.completed_at = datetime.utcnow()
                    
                    # Record task completion in game state
                    game_state = GameState.query.filter_by(user_id=user_id).first()
                    if game_state:
                        game_state.tasks_completed += 1
        
        db.session.commit()
        logger.info(f"Updated {objective_type} task progress for user {user_id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating task progress: {str(e)}")

def should_reset_task(user_task, task):
    """Check if a daily or weekly task should be reset based on its last reset time."""
    now = datetime.utcnow()
    
    if task.task_type == 'daily':
        # Check if last reset was on a previous day
        yesterday = now - timedelta(days=1)
        return user_task.last_reset.date() <= yesterday.date()
        
    elif task.task_type == 'weekly':
        # Check if last reset was in a previous week
        # Reset on Monday (weekday 0)
        days_since_monday = (now.weekday() - 0) % 7
        last_monday = now - timedelta(days=days_since_monday)
        last_monday = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        return user_task.last_reset < last_monday
    
    return False

def complete_task(user_id, user_task, task):
    """Process task completion and award rewards."""
    try:
        # Get user's game state
        game_state = GameState.query.filter_by(user_id=user_id).first()
        if not game_state:
            logger.error(f"Game state not found for user {user_id}")
            return False
        
        # Update game state with rewards
        game_state.token_balance += task.token_reward
        game_state.pixels += task.pixel_reward
        game_state.experience += task.experience_reward
        
        # Record transaction
        transaction = Transaction(
            user_id=user_id,
            type='task_reward',
            amount=task.token_reward,
            description=f'Reward for completing task: {task.name}'
        )
        db.session.add(transaction)
        
        # Reset task progress for repeatable tasks
        if task.task_type in ['daily', 'weekly']:
            user_task.completed = False
            user_task.current_progress = 0
            user_task.last_reset = datetime.utcnow()
        
        db.session.commit()
        logger.info(f"Task {task.name} completed for user {user_id}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error completing task: {str(e)}")
        return False

def get_user_tasks(user_id):
    """Get all tasks for a user with their progress."""
    try:
        # Assign any missing tasks to the user
        assign_tasks_to_user(user_id)
        
        # Get all user tasks with their task info
        user_tasks = db.session.query(
            UserTask, Task
        ).join(
            Task, UserTask.task_id == Task.id
        ).filter(
            UserTask.user_id == user_id,
            Task.is_active == True
        ).all()
        
        # Reset any tasks that need it
        for user_task, task in user_tasks:
            if should_reset_task(user_task, task):
                user_task.current_progress = 0
                user_task.completed = False
                user_task.last_reset = datetime.utcnow()
        
        db.session.commit()
        
        return user_tasks
        
    except Exception as e:
        logger.error(f"Error getting user tasks: {str(e)}")
        return []