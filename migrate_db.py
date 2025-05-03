"""
Database migration script to add new columns and tables for referrals and tasks.
This is a one-time script to update the database schema.
"""

import os
import sys
from app import app, db
from models import User, GameState, Transaction, Task, UserTask

def run_migration():
    """Run the database migration to add new columns and tables."""
    print("Starting database migration...")
    
    with app.app_context():
        # Check if tables exist
        engine = db.engine
        inspector = db.inspect(engine)
        
        # Add Task and UserTask tables if they don't exist
        print("Creating Task and UserTask tables if they don't exist...")
        if not inspector.has_table('task'):
            Task.__table__.create(engine)
            print("Task table created.")
        else:
            print("Task table already exists.")
            
        if not inspector.has_table('user_task'):
            UserTask.__table__.create(engine)
            print("UserTask table created.")
        else:
            print("UserTask table already exists.")
        
        # Check if referral columns exist in User table
        user_columns = [col['name'] for col in inspector.get_columns('user')]
        
        # Add referral_code column if it doesn't exist
        if 'referral_code' not in user_columns:
            print("Adding referral_code column to User table...")
            with engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN referral_code VARCHAR(16) UNIQUE;"))
                conn.commit()
                print("referral_code column added.")
        else:
            print("referral_code column already exists.")
            
        # Add referred_by_id column if it doesn't exist
        if 'referred_by_id' not in user_columns:
            print("Adding referred_by_id column to User table...")
            with engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN referred_by_id INTEGER REFERENCES \"user\"(id);"))
                conn.commit()
                print("referred_by_id column added.")
        else:
            print("referred_by_id column already exists.")
        
        # Check if referral columns exist in GameState table
        game_state_columns = [col['name'] for col in inspector.get_columns('game_state')]
        
        # Add referral_count column if it doesn't exist
        if 'referral_count' not in game_state_columns:
            print("Adding referral_count column to GameState table...")
            with engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE game_state ADD COLUMN referral_count INTEGER DEFAULT 0;"))
                conn.commit()
                print("referral_count column added.")
        else:
            print("referral_count column already exists.")
            
        # Add tasks_completed column if it doesn't exist
        if 'tasks_completed' not in game_state_columns:
            print("Adding tasks_completed column to GameState table...")
            with engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE game_state ADD COLUMN tasks_completed INTEGER DEFAULT 0;"))
                conn.commit()
                print("tasks_completed column added.")
        else:
            print("tasks_completed column already exists.")
        
        print("Migration completed successfully!")
        return True

if __name__ == "__main__":
    run_migration()