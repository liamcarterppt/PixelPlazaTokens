import os
import logging
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

# Configure SQLite database for development
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///pixel_plaza.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models after db initialization to avoid circular imports
    from models import User, GameState, Transaction
    db.create_all()

# Import game mechanics after models
from game_mechanics import GameMechanics

# Initialize game mechanics
game = GameMechanics()

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
    
    user.wallet_address = wallet_address
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Wallet address updated successfully'})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
