import os
import logging
import random
import string
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import csv
from io import StringIO
from datetime import datetime

# Initialize Flask application
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "pixel_plaza_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure PostgreSQL database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models after db initialization to avoid circular imports
    from models import User, GameState, Transaction, Task, UserTask
    db.create_all()

# Import game mechanics and utilities after models
from game_mechanics import GameMechanics
from utils import (
    generate_referral_code, process_referral, initialize_tasks, 
    assign_tasks_to_user, update_task_progress, get_user_tasks
)
from config import REFERRER_LEVEL_REQUIREMENT

# Initialize game mechanics
game = GameMechanics()

# Initialize tasks
with app.app_context():
    initialize_tasks()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    # Get telegram ID from query parameters
    telegram_id = request.args.get('id')
    if not telegram_id:
        flash('Please access this page through the Telegram bot', 'danger')
        return redirect(url_for('index'))
    
    # Get user data
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        flash('User not found. Please register through the Telegram bot', 'danger')
        return redirect(url_for('index'))
    
    game_state = GameState.query.filter_by(user_id=user.id).first()
    if not game_state:
        flash('Game state not found', 'danger')
        return redirect(url_for('index'))
    
    # Get recent transactions
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).limit(5).all()
    
    return render_template(
        'dashboard.html', 
        user=user, 
        game_state=game_state, 
        transactions=transactions
    )

@app.route('/web-game')
def web_game():
    """Web-based game interface compatible with Telegram UI"""
    # Check if there's a telegram ID in the query parameters
    telegram_id = request.args.get('id')
    
    # For existing Telegram users
    if telegram_id:
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if user:
            game_state = GameState.query.filter_by(user_id=user.id).first()
            if game_state:
                # Get recent transactions
                transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).limit(5).all()
                
                # Get user tasks
                user_tasks = get_user_tasks(user.id)
                
                # Update login task progress
                update_task_progress(user.id, 'login', 1)
                
                # Check if user has a referral code
                if not user.referral_code and game_state.level >= REFERRER_LEVEL_REQUIREMENT:
                    user.referral_code = generate_referral_code()
                    db.session.commit()
                
                return render_template(
                    'web_game.html', 
                    user=user, 
                    game_state=game_state, 
                    transactions=transactions, 
                    tasks=user_tasks,
                    login_required=False
                )
    
    # For users who aren't logged in yet
    return render_template('web_game.html', login_required=True)

@app.route('/tasks')
def tasks():
    """View all tasks for a user"""
    telegram_id = request.args.get('id')
    if not telegram_id:
        flash('Please access this page through the game', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('index'))
    
    # Get user tasks
    user_tasks = get_user_tasks(user.id)
    
    # Group tasks by type
    one_time_tasks = []
    daily_tasks = []
    weekly_tasks = []
    
    for user_task, task in user_tasks:
        if task.task_type == 'one_time':
            one_time_tasks.append((user_task, task))
        elif task.task_type == 'daily':
            daily_tasks.append((user_task, task))
        elif task.task_type == 'weekly':
            weekly_tasks.append((user_task, task))
    
    return render_template(
        'tasks.html', 
        user=user,
        one_time_tasks=one_time_tasks,
        daily_tasks=daily_tasks,
        weekly_tasks=weekly_tasks
    )

@app.route('/referrals')
def referrals():
    """View and manage referrals"""
    telegram_id = request.args.get('id')
    if not telegram_id:
        flash('Please access this page through the game', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('index'))
    
    game_state = GameState.query.filter_by(user_id=user.id).first()
    if not game_state:
        flash('Game state not found', 'danger')
        return redirect(url_for('index'))
    
    # Generate referral code if user doesn't have one but meets level requirement
    if not user.referral_code and game_state.level >= REFERRER_LEVEL_REQUIREMENT:
        user.referral_code = generate_referral_code()
        db.session.commit()
    
    # Get referred users
    referred_users = User.query.filter_by(referred_by_id=user.id).all()
    
    return render_template(
        'referrals.html',
        user=user,
        game_state=game_state,
        referred_users=referred_users,
        min_level=REFERRER_LEVEL_REQUIREMENT
    )

@app.route('/leaderboard')
def leaderboard():
    # Get top 20 users by token balance
    top_users = db.session.query(
        User, GameState
    ).join(
        GameState, User.id == GameState.user_id
    ).order_by(
        GameState.token_balance.desc()
    ).limit(20).all()
    
    return render_template('leaderboard.html', top_users=top_users)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Simple admin authentication
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'pixel_plaza_admin')
        
        if password == admin_password:
            session['admin'] = True
        else:
            flash('Invalid password', 'danger')
            return redirect(url_for('admin'))
    
    if not session.get('admin'):
        return render_template('admin.html', authenticated=False)
    
    # Get all users with their game states
    users = db.session.query(
        User, GameState
    ).join(
        GameState, User.id == GameState.user_id
    ).order_by(
        GameState.token_balance.desc()
    ).all()
    
    return render_template('admin.html', authenticated=True, users=users)

@app.route('/export_csv')
def export_csv():
    if not session.get('admin'):
        flash('Admin authentication required', 'danger')
        return redirect(url_for('admin'))
    
    # Create CSV file
    si = StringIO()
    csv_writer = csv.writer(si)
    
    # Write headers
    csv_writer.writerow(['Username', 'Telegram ID', 'Wallet Address', 'Token Balance', 'Last Active'])
    
    # Get all eligible users (with wallet address filled)
    users = db.session.query(
        User, GameState
    ).join(
        GameState, User.id == GameState.user_id
    ).filter(
        User.wallet_address.isnot(None)
    ).order_by(
        GameState.token_balance.desc()
    ).all()
    
    # Write user data
    for user, game_state in users:
        csv_writer.writerow([
            user.username, 
            user.telegram_id, 
            user.wallet_address, 
            game_state.token_balance,
            game_state.last_active.strftime('%Y-%m-%d %H:%M:%S') if game_state.last_active else 'Never'
        ])
    
    output = si.getvalue()
    
    return app.response_class(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename=pixel_plaza_airdrop_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@app.route('/api/game_action', methods=['POST'])
def game_action():
    telegram_id = request.form.get('telegram_id')
    action = request.form.get('action')
    
    if not telegram_id or not action:
        return jsonify({'success': False, 'message': 'Missing parameters'})
    
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    game_state = GameState.query.filter_by(user_id=user.id).first()
    if not game_state:
        return jsonify({'success': False, 'message': 'Game state not found'})
    
    # Process game action
    result = game.process_action(user, game_state, action)
    
    # Update task progress based on action type
    if result['success']:
        if action == 'mine':
            update_task_progress(user.id, 'mining', 1)
        elif action == 'create':
            update_task_progress(user.id, 'pixel_art', 1)
        elif action == 'build':
            update_task_progress(user.id, 'building', 1)
    
    # Update game state
    game_state.last_active = datetime.now()
    db.session.commit()
    
    return jsonify(result)

@app.route('/api/update_wallet', methods=['POST'])
def update_wallet():
    telegram_id = request.form.get('telegram_id')
    wallet_address = request.form.get('wallet_address')
    
    if not telegram_id or not wallet_address:
        return jsonify({'success': False, 'message': 'Missing parameters'})
    
    # Simple wallet validation (should be more robust in production)
    if not wallet_address.startswith('0x') or len(wallet_address) != 42:
        return jsonify({'success': False, 'message': 'Invalid wallet address format'})
    
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Update wallet address
    user.wallet_address = wallet_address
    
    # Update task progress if this is the first time setting wallet
    if not user.wallet_address:
        update_task_progress(user.id, 'wallet', 1)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Wallet address updated successfully'})

@app.route('/api/web_register', methods=['POST'])
def web_register():
    """API endpoint for web-based user registration"""
    username = request.form.get('username')
    referral_code = request.form.get('referral_code')
    
    if not username:
        return jsonify({'success': False, 'message': 'Username is required'})
    
    # Generate a unique telegram_id for web users (prefixed with 'web_')
    web_id = f"web_{int(datetime.now().timestamp())}"
    
    # Check if username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Username already taken'})
    
    try:
        # Check referral code if provided
        referrer = None
        if referral_code:
            referrer = User.query.filter_by(referral_code=referral_code).first()
            if not referrer:
                return jsonify({'success': False, 'message': 'Invalid referral code'})
        
        # Create new user
        new_user = User(
            username=username,
            telegram_id=web_id,
            referred_by_id=referrer.id if referrer else None
        )
        db.session.add(new_user)
        db.session.flush()  # Flush to get the ID without committing
        
        # Create initial game state
        new_game_state = GameState(
            user_id=new_user.id,
            token_balance=10,  # Initial tokens
        )
        db.session.add(new_game_state)
        
        # Record initial transaction
        welcome_transaction = Transaction(
            user_id=new_user.id,
            type='welcome_bonus',
            amount=10,
            description=f'Welcome bonus of 10 $PXPT'
        )
        db.session.add(welcome_transaction)
        
        # Assign tasks to the new user
        assign_tasks_to_user(new_user.id)
        
        db.session.commit()
        
        # Process referral after successful user creation
        if referrer:
            process_referral(referrer.id, new_user)
        
        return jsonify({
            'success': True, 
            'message': 'Registration successful', 
            'telegram_id': web_id
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error during web registration: {str(e)}")
        return jsonify({'success': False, 'message': f'Registration failed: {str(e)}'})

@app.route('/api/claim_task_reward', methods=['POST'])
def claim_task_reward():
    """API endpoint for claiming completed task rewards"""
    telegram_id = request.form.get('telegram_id')
    task_id = request.form.get('task_id')
    
    if not telegram_id or not task_id:
        return jsonify({'success': False, 'message': 'Missing parameters'})
    
    try:
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        user_task = UserTask.query.filter_by(user_id=user.id, task_id=task_id).first()
        if not user_task:
            return jsonify({'success': False, 'message': 'Task not found for this user'})
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'})
        
        if not user_task.completed:
            return jsonify({'success': False, 'message': 'Task not completed yet'})
        
        # Award the rewards
        game_state = GameState.query.filter_by(user_id=user.id).first()
        if not game_state:
            return jsonify({'success': False, 'message': 'Game state not found'})
        
        # Update game state
        game_state.token_balance += task.token_reward
        game_state.pixels += task.pixel_reward
        game_state.experience += task.experience_reward
        
        # Record transaction
        transaction = Transaction(
            user_id=user.id,
            type='task_reward',
            amount=task.token_reward,
            description=f'Reward for completing task: {task.name}'
        )
        db.session.add(transaction)
        
        # Mark task as claimed and reset progress
        user_task.completed = False
        user_task.current_progress = 0
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Task reward claimed: +{task.token_reward} $PXPT, +{task.pixel_reward} Pixels, +{task.experience_reward} XP'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error claiming task reward: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to claim reward: {str(e)}'})

@app.route('/api/generate_referral_code', methods=['POST'])
def generate_referral_code_api():
    """API endpoint for generating a referral code"""
    telegram_id = request.form.get('telegram_id')
    
    if not telegram_id:
        return jsonify({'success': False, 'message': 'Missing parameters'})
    
    try:
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        game_state = GameState.query.filter_by(user_id=user.id).first()
        if not game_state:
            return jsonify({'success': False, 'message': 'Game state not found'})
        
        # Check level requirement
        if game_state.level < REFERRER_LEVEL_REQUIREMENT:
            return jsonify({
                'success': False, 
                'message': f'You need to reach level {REFERRER_LEVEL_REQUIREMENT} to generate a referral code'
            })
        
        # Generate a new referral code
        if user.referral_code:
            return jsonify({
                'success': False, 
                'message': f'You already have a referral code: {user.referral_code}'
            })
        
        user.referral_code = generate_referral_code()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Referral code generated: {user.referral_code}',
            'referral_code': user.referral_code
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error generating referral code: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to generate referral code: {str(e)}'})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
