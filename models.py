from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    telegram_id = db.Column(db.String(20), unique=True, nullable=False)
    wallet_address = db.Column(db.String(42), nullable=True)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    game_state = db.relationship('GameState', backref='user', lazy=True, uselist=False)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class GameState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Game economy statistics
    token_balance = db.Column(db.Float, default=0.0)
    pixel_art_created = db.Column(db.Integer, default=0)
    buildings_owned = db.Column(db.Integer, default=0)
    daily_streak = db.Column(db.Integer, default=0)
    last_daily_claim = db.Column(db.DateTime, nullable=True)
    
    # Resources for economy simulation
    pixels = db.Column(db.Integer, default=100)
    energy = db.Column(db.Integer, default=100)
    
    # Game progression
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GameState for User {self.user_id}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Transaction details
    type = db.Column(db.String(50), nullable=False)  # e.g., 'daily_reward', 'building_purchase', etc.
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction {self.type} for User {self.user_id}>'
