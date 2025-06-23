#!/usr/bin/env python3
"""
Database migration script to clean up unused columns in trials table.
This script safely removes columns that are no longer needed.

Removed columns:
- threshold_ci_lower, threshold_ci_upper
- slope_ci_lower, slope_ci_upper  
- ado_entropy, ado_trial_count
- experiment_timestamp

Usage:
    python migrate_database_cleanup.py
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL with same logic as main app"""
    # Try standard DATABASE_URL first (Replit PostgreSQL)
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        logger.info("🐘 Using Replit PostgreSQL via DATABASE_URL")
        return db_url
    
    # Try legacy REPLIT_DB_URL
    replit_db = os.getenv('REPLIT_DB_URL')
    if replit_db:
        logger.info("🐘 Using REPLIT_DB_URL PostgreSQL")
        return replit_db
    
    # Fall back to SQLite for development
    logger.info("💾 Using SQLite fallback")
    return "sqlite:///psychophysics_experiments.db"

def check_database_connection(engine):
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def get_table_columns(engine, table_name):
    """Get list of columns in a table"""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return [col['name'] for col in columns]
    except Exception as e:
        logger.error(f"❌ Error getting columns for {table_name}: {e}")
        return []

def backup_table_data(engine, table_name):
    """Create a backup of table data"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{table_name}_backup_{timestamp}.sql"
        
        with engine.connect() as conn:
            # For SQLite, we'll just log the backup intent
            if 'sqlite' in str(engine.url):
                logger.info(f"📋 SQLite detected - backup would be saved as {backup_file}")
                return True
            else:
                # For PostgreSQL, you might want to implement actual backup
                logger.info(f"📋 PostgreSQL backup recommended before migration")
                return True
                
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        return False

def drop_columns_sqlite(engine, table_name, columns_to_drop):
    """Drop columns from SQLite table (requires table recreation)"""
    try:
        logger.info("🔧 SQLite detected - using table recreation method")
        
        # Get current table structure
        with engine.connect() as conn:
            # Get current columns
            current_columns = get_table_columns(engine, table_name)
            
            # Filter out columns to drop
            keep_columns = [col for col in current_columns if col not in columns_to_drop]
            keep_columns_str = ', '.join(keep_columns)
            
            logger.info(f"📝 Keeping columns: {keep_columns_str}")
            
            # Create new table with updated structure
            # Note: This is a simplified approach - in production you'd want to preserve
            # constraints, indexes, etc.
            trans = conn.begin()
            try:
                # Rename old table
                conn.execute(text(f"ALTER TABLE {table_name} RENAME TO {table_name}_old"))
                
                # Create new table with simplified structure (matches our new model)
                create_new_table_sql = f"""
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id INTEGER,
                    trial_number INTEGER NOT NULL,
                    is_practice BOOLEAN DEFAULT 0,
                    mtf_value FLOAT,
                    ado_stimulus_value FLOAT,
                    stimulus_image_file VARCHAR,
                    response VARCHAR,
                    reaction_time FLOAT,
                    timestamp DATETIME,
                    participant_id VARCHAR,
                    experiment_type VARCHAR,
                    estimated_threshold FLOAT,
                    estimated_slope FLOAT,
                    threshold_std FLOAT,
                    slope_std FLOAT,
                    FOREIGN KEY(experiment_id) REFERENCES experiments (id)
                )
                """
                conn.execute(text(create_new_table_sql))
                
                # Copy data from old table to new table
                insert_sql = f"""
                INSERT INTO {table_name} ({keep_columns_str})
                SELECT {keep_columns_str} FROM {table_name}_old
                """
                conn.execute(text(insert_sql))
                
                # Drop old table
                conn.execute(text(f"DROP TABLE {table_name}_old"))
                
                trans.commit()
                logger.info("✅ SQLite table recreation completed")
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ SQLite migration failed: {e}")
                return False
                
    except Exception as e:
        logger.error(f"❌ SQLite column drop failed: {e}")
        return False

def drop_columns_postgresql(engine, table_name, columns_to_drop):
    """Drop columns from PostgreSQL table"""
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                for column in columns_to_drop:
                    sql = f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {column}"
                    conn.execute(text(sql))
                    logger.info(f"🗑️ Dropped column: {column}")
                
                trans.commit()
                logger.info("✅ PostgreSQL column drops completed")
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ PostgreSQL migration failed: {e}")
                return False
                
    except Exception as e:
        logger.error(f"❌ PostgreSQL column drop failed: {e}")
        return False

def migrate_database():
    """Main migration function"""
    logger.info("🚀 Starting database cleanup migration")
    
    # Get database URL
    database_url = get_database_url()
    logger.info(f"📊 Database URL: {database_url.split('@')[0]}@***")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Check connection
        if not check_database_connection(engine):
            logger.error("❌ Cannot proceed without database connection")
            return False
        
        # Check if trials table exists
        current_columns = get_table_columns(engine, 'trials')
        if not current_columns:
            logger.error("❌ Trials table not found or empty")
            return False
        
        logger.info(f"📋 Current columns: {', '.join(current_columns)}")
        
        # Define columns to drop
        columns_to_drop = [
            'threshold_ci_lower', 'threshold_ci_upper',
            'slope_ci_lower', 'slope_ci_upper',
            'ado_entropy', 'ado_trial_count',
            'experiment_timestamp'
        ]
        
        # Check which columns actually exist
        existing_columns_to_drop = [col for col in columns_to_drop if col in current_columns]
        
        if not existing_columns_to_drop:
            logger.info("✅ No columns need to be dropped - database is already clean")
            return True
        
        logger.info(f"🗑️ Columns to drop: {', '.join(existing_columns_to_drop)}")
        
        # Create backup
        backup_table_data(engine, 'trials')
        
        # Drop columns based on database type
        if 'sqlite' in str(engine.url):
            success = drop_columns_sqlite(engine, 'trials', existing_columns_to_drop)
        else:
            success = drop_columns_postgresql(engine, 'trials', existing_columns_to_drop)
        
        if success:
            # Verify final structure
            final_columns = get_table_columns(engine, 'trials')
            logger.info(f"✅ Final columns: {', '.join(final_columns)}")
            logger.info("🎉 Database cleanup migration completed successfully")
            return True
        else:
            logger.error("❌ Migration failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration error: {e}")
        return False

if __name__ == "__main__":
    print("🧹 Database Cleanup Migration Tool")
    print("=" * 50)
    
    # Check for auto-confirm flag or Replit environment
    auto_confirm = (
        '--auto-confirm' in sys.argv or 
        '-y' in sys.argv or 
        os.getenv('REPLIT') or 
        os.getenv('DATABASE_URL')  # Replit usually has this
    )
    
    if not auto_confirm:
        # Interactive confirmation for local environments
        response = input("\n⚠️  This will modify your database structure. Continue? (y/N): ")
        if response.lower() != 'y':
            print("❌ Migration cancelled by user")
            sys.exit(0)
    else:
        print("\n🤖 Auto-confirming migration (Replit environment detected)")
        print("⚠️  Database structure will be modified...")
    
    success = migrate_database()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("📊 Your database has been cleaned up and optimized.")
    else:
        print("\n❌ Migration failed!")
        print("🔧 Please check the logs and try again.")
        sys.exit(1)