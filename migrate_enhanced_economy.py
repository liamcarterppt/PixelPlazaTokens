"""
Database migration script to add new columns and tables for the enhanced economy simulation.
This is a one-time script to update the database schema.
"""

import os
import sys
import logging
from datetime import datetime
from app import app, db
from sqlalchemy import text, inspect, MetaData, Table, Column, Integer, Float, String, Boolean, DateTime, ForeignKey

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the database migration to add new columns and tables for enhanced economy."""
    try:
        logger.info("Starting database migration for enhanced economy...")
        
        # Connect to database
        with app.app_context():
            # Get database inspector
            inspector = inspect(db.engine)
            
            # 1. Add new columns to GameState table
            logger.info("Adding new columns to GameState table...")
            columns_to_add = {
                'gems': 'INTEGER DEFAULT 0',
                'materials': 'INTEGER DEFAULT 0',
                'mining_skill': 'INTEGER DEFAULT 1',
                'art_skill': 'INTEGER DEFAULT 1',
                'building_skill': 'INTEGER DEFAULT 1',
                'trading_skill': 'INTEGER DEFAULT 1',
                'market_transactions': 'INTEGER DEFAULT 0',
                'last_market_action': 'TIMESTAMP'
            }
            
            existing_columns = {col['name'] for col in inspector.get_columns('game_state')}
            
            for column_name, column_type in columns_to_add.items():
                if column_name not in existing_columns:
                    db.engine.execute(text(f"ALTER TABLE game_state ADD COLUMN {column_name} {column_type}"))
                    logger.info(f"Added column {column_name} to game_state table")
                else:
                    logger.info(f"Column {column_name} already exists in game_state table")
            
            # 2. Create Building table if it doesn't exist
            if 'building' not in inspector.get_table_names():
                logger.info("Creating Building table...")
                db.engine.execute(text("""
                    CREATE TABLE building (
                        id SERIAL PRIMARY KEY,
                        game_state_id INTEGER NOT NULL REFERENCES game_state(id) ON DELETE CASCADE,
                        building_type VARCHAR(50) NOT NULL,
                        level INTEGER DEFAULT 1,
                        production_rate FLOAT NOT NULL,
                        produces_tokens BOOLEAN DEFAULT TRUE,
                        produces_pixels BOOLEAN DEFAULT FALSE,
                        produces_materials BOOLEAN DEFAULT FALSE,
                        produces_gems BOOLEAN DEFAULT FALSE,
                        last_collection TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        efficiency FLOAT DEFAULT 1.0,
                        upgrade_token_cost FLOAT DEFAULT 10.0,
                        upgrade_material_cost INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_upgraded TIMESTAMP
                    )
                """))
                logger.info("Building table created")
            else:
                logger.info("Building table already exists")
            
            # 3. Create MarketOrder table if it doesn't exist
            if 'market_order' not in inspector.get_table_names():
                logger.info("Creating MarketOrder table...")
                db.engine.execute(text("""
                    CREATE TABLE market_order (
                        id SERIAL PRIMARY KEY,
                        game_state_id INTEGER NOT NULL REFERENCES game_state(id) ON DELETE CASCADE,
                        order_type VARCHAR(10) NOT NULL,
                        resource_type VARCHAR(20) NOT NULL,
                        quantity INTEGER NOT NULL,
                        price_per_unit FLOAT NOT NULL,
                        filled_quantity INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_cancelled BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                """))
                logger.info("MarketOrder table created")
            else:
                logger.info("MarketOrder table already exists")
            
            # 4. Create MarketHistory table if it doesn't exist
            if 'market_history' not in inspector.get_table_names():
                logger.info("Creating MarketHistory table...")
                db.engine.execute(text("""
                    CREATE TABLE market_history (
                        id SERIAL PRIMARY KEY,
                        resource_type VARCHAR(20) NOT NULL,
                        avg_price FLOAT NOT NULL,
                        volume INTEGER NOT NULL,
                        price_change_24h FLOAT DEFAULT 0.0,
                        highest_price FLOAT NOT NULL,
                        lowest_price FLOAT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                logger.info("MarketHistory table created")
            else:
                logger.info("MarketHistory table already exists")
            
            # 5. Create GameEvent table if it doesn't exist
            if 'game_event' not in inspector.get_table_names():
                logger.info("Creating GameEvent table...")
                db.engine.execute(text("""
                    CREATE TABLE game_event (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        description VARCHAR(500) NOT NULL,
                        event_type VARCHAR(50) NOT NULL,
                        mining_multiplier FLOAT DEFAULT 1.0,
                        art_multiplier FLOAT DEFAULT 1.0,
                        building_multiplier FLOAT DEFAULT 1.0,
                        market_fee_multiplier FLOAT DEFAULT 1.0,
                        affects_tokens BOOLEAN DEFAULT TRUE,
                        affects_pixels BOOLEAN DEFAULT FALSE,
                        affects_materials BOOLEAN DEFAULT FALSE,
                        affects_gems BOOLEAN DEFAULT FALSE,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP NOT NULL,
                        is_active BOOLEAN DEFAULT FALSE
                    )
                """))
                logger.info("GameEvent table created")
            else:
                logger.info("GameEvent table already exists")
                
            # Create initial market history entries
            if db.session.query(db.metadata.tables['market_history']).count() == 0:
                logger.info("Creating initial market history entries...")
                db.engine.execute(text("""
                    INSERT INTO market_history (resource_type, avg_price, volume, highest_price, lowest_price)
                    VALUES 
                    ('pixels', 0.1, 1000, 0.12, 0.08),
                    ('materials', 0.5, 500, 0.55, 0.45),
                    ('gems', 5.0, 100, 5.5, 4.5)
                """))
                logger.info("Initial market history entries created")
                
            logger.info("Database migration completed successfully!")
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    run_migration()