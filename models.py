from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    telegram_id = db.Column(db.String(20), unique=True, nullable=False)
    wallet_address = db.Column(db.String(42), nullable=True)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Referral system
    referral_code = db.Column(db.String(16), unique=True)
    referred_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    game_state = db.relationship('GameState', backref='user', lazy=True, uselist=False)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    referred_users = db.relationship('User', backref=db.backref('referred_by', remote_side=[id]), lazy=True)
    user_tasks = db.relationship('UserTask', backref='user', lazy=True)
    
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
    gems = db.Column(db.Integer, default=0)  # Premium currency for special items
    materials = db.Column(db.Integer, default=0)  # Building materials for construction
    
    # Game progression
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    
    # Skill levels affecting game mechanics
    mining_skill = db.Column(db.Integer, default=1)
    art_skill = db.Column(db.Integer, default=1)
    building_skill = db.Column(db.Integer, default=1)
    trading_skill = db.Column(db.Integer, default=1)
    
    # Market participation
    market_transactions = db.Column(db.Integer, default=0)
    last_market_action = db.Column(db.DateTime, nullable=True)
    
    # Referral system stats
    referral_count = db.Column(db.Integer, default=0)
    tasks_completed = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    buildings = db.relationship('Building', backref='owner_state', lazy=True)
    market_orders = db.relationship('MarketOrder', backref='owner_state', lazy=True)
    
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

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)  # 'one_time', 'daily', 'weekly'
    objective_type = db.Column(db.String(50), nullable=False)  # 'mining', 'pixel_art', 'building', 'referral'
    objective_value = db.Column(db.Integer, nullable=False)  # target count/value
    token_reward = db.Column(db.Float, nullable=False)
    pixel_reward = db.Column(db.Integer, default=0)
    experience_reward = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user_tasks = db.relationship('UserTask', backref='task', lazy=True)
    
    def __repr__(self):
        return f'<Task {self.name}>'

class UserTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    
    # Task progress
    current_progress = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_reset = db.Column(db.DateTime, default=datetime.utcnow)  # For daily/weekly tasks
    
    def __repr__(self):
        return f'<UserTask {self.task_id} for User {self.user_id}>'

class Building(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_state_id = db.Column(db.Integer, db.ForeignKey('game_state.id'), nullable=False)
    
    # Building properties
    building_type = db.Column(db.String(50), nullable=False)  # 'mine', 'studio', 'factory', 'market', 'bank'
    level = db.Column(db.Integer, default=1)
    production_rate = db.Column(db.Float, nullable=False)  # Base production rate
    
    # Resource production focus
    produces_tokens = db.Column(db.Boolean, default=True)
    produces_pixels = db.Column(db.Boolean, default=False)
    produces_materials = db.Column(db.Boolean, default=False)
    produces_gems = db.Column(db.Boolean, default=False)
    
    # Building state
    last_collection = db.Column(db.DateTime, default=datetime.utcnow)
    efficiency = db.Column(db.Float, default=1.0)  # Multiplier for production (affected by events)
    
    # Building costs
    upgrade_token_cost = db.Column(db.Float, default=10.0)
    upgrade_material_cost = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_upgraded = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Building {self.building_type} (Level {self.level}) for GameState {self.game_state_id}>'

class MarketOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_state_id = db.Column(db.Integer, db.ForeignKey('game_state.id'), nullable=False)
    
    # Order details
    order_type = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    resource_type = db.Column(db.String(20), nullable=False)  # 'pixels', 'materials', 'gems'
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    filled_quantity = db.Column(db.Integer, default=0)
    
    # Order status
    is_active = db.Column(db.Boolean, default=True)
    is_cancelled = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<MarketOrder {self.order_type} {self.quantity} {self.resource_type} at {self.price_per_unit} $PXPT each>'

class MarketHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Market data
    resource_type = db.Column(db.String(20), nullable=False)  # 'pixels', 'materials', 'gems'
    avg_price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.Integer, nullable=False)  # Total traded volume
    
    # Price changes
    price_change_24h = db.Column(db.Float, default=0.0)  # Percentage change in 24 hours
    highest_price = db.Column(db.Float, nullable=False)
    lowest_price = db.Column(db.Float, nullable=False)
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MarketHistory {self.resource_type} Avg: {self.avg_price} $PXPT on {self.timestamp}>'

class GameEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Event details
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # 'seasonal', 'special', 'crisis', 'boom'
    
    # Event effects
    mining_multiplier = db.Column(db.Float, default=1.0)
    art_multiplier = db.Column(db.Float, default=1.0)
    building_multiplier = db.Column(db.Float, default=1.0)
    market_fee_multiplier = db.Column(db.Float, default=1.0)
    
    # Resources affected
    affects_tokens = db.Column(db.Boolean, default=True)
    affects_pixels = db.Column(db.Boolean, default=False)
    affects_materials = db.Column(db.Boolean, default=False)
    affects_gems = db.Column(db.Boolean, default=False)
    
    # Event duration
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<GameEvent {self.name} ({self.event_type})>'
