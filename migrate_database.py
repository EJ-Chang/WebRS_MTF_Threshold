#!/usr/bin/env python3
"""
Database migration script to add new ADO fields to existing tables
Safely adds new columns without affecting existing data
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from database import DatabaseManager

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        # For PostgreSQL
        result = engine.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = :table_name AND column_name = :column_name
        """), table_name=table_name, column_name=column_name)
        
        return result.fetchone() is not None
    except:
        try:
            # For SQLite fallback
            result = engine.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]
            return column_name in columns
        except:
            return False

def add_column_safely(engine, table_name, column_name, column_type, default_value=None):
    """Safely add a column to a table if it doesn't exist"""
    try:
        if not check_column_exists(engine, table_name, column_name):
            default_clause = f" DEFAULT {default_value}" if default_value is not None else ""
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{default_clause}"
            engine.execute(text(sql))
            print(f"✅ Added column: {table_name}.{column_name}")
            return True
        else:
            print(f"⏭️ Column already exists: {table_name}.{column_name}")
            return False
    except Exception as e:
        print(f"❌ Error adding column {table_name}.{column_name}: {e}")
        return False

def migrate_database():
    """Run database migration to add new ADO fields"""
    
    print("🔄 Starting database migration...")
    print("=" * 60)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    if not db_manager.engine:
        print("❌ Database not available, migration aborted")
        return False
    
    engine = db_manager.engine
    
    # Check database type
    db_url = str(engine.url)
    is_postgresql = 'postgresql' in db_url
    is_sqlite = 'sqlite' in db_url
    
    print(f"🗄️ Database type: {'PostgreSQL' if is_postgresql else 'SQLite' if is_sqlite else 'Unknown'}")
    print(f"🔗 Database URL: {db_url.split('@')[0]}@***" if '@' in db_url else f"🔗 Database: {db_url}")
    
    # Define new columns to add
    new_columns = [
        # ADO computation results
        ('estimated_threshold', 'REAL', None),
        ('estimated_slope', 'REAL', None), 
        ('threshold_std', 'REAL', None),
        ('slope_std', 'REAL', None),
        ('threshold_ci_lower', 'REAL', None),
        ('threshold_ci_upper', 'REAL', None),
        ('slope_ci_lower', 'REAL', None),
        ('slope_ci_upper', 'REAL', None),
        ('ado_entropy', 'REAL', None),
        ('ado_trial_count', 'INTEGER', None),
    ]
    
    # Start migration
    try:
        print(f"\n📋 Adding {len(new_columns)} new columns to 'trials' table...")
        
        success_count = 0
        for column_name, column_type, default_value in new_columns:
            if add_column_safely(engine, 'trials', column_name, column_type, default_value):
                success_count += 1
        
        print(f"\n📊 Migration Summary:")
        print(f"   ✅ Successfully added: {success_count} columns")
        print(f"   ⏭️ Already existed: {len(new_columns) - success_count} columns")
        
        # Verify migration
        print(f"\n🔍 Verifying migration...")
        
        verification_failed = []
        for column_name, _, _ in new_columns:
            if not check_column_exists(engine, 'trials', column_name):
                verification_failed.append(column_name)
        
        if verification_failed:
            print(f"❌ Verification failed for columns: {verification_failed}")
            return False
        else:
            print("✅ All new columns verified successfully")
        
        # Test a simple query to make sure table is working
        try:
            result = engine.execute(text("SELECT COUNT(*) FROM trials"))
            row_count = result.fetchone()[0]
            print(f"📊 Existing trials in database: {row_count}")
        except Exception as e:
            print(f"⚠️ Warning: Could not count existing trials: {e}")
        
        print("\n🎉 DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("📝 Changes made:")
        print("   • Added 10 new ADO-related columns to trials table")
        print("   • All existing data preserved")
        print("   • New experiments will now save complete ADO information")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def check_migration_status():
    """Check if migration has already been applied"""
    print("🔍 Checking current database schema...")
    
    db_manager = DatabaseManager()
    if not db_manager.engine:
        print("❌ Database not available")
        return False
    
    required_columns = [
        'estimated_threshold', 'estimated_slope', 'threshold_std', 'slope_std',
        'threshold_ci_lower', 'threshold_ci_upper', 'slope_ci_lower', 'slope_ci_upper',
        'ado_entropy', 'ado_trial_count'
    ]
    
    missing_columns = []
    existing_columns = []
    
    for column in required_columns:
        if check_column_exists(db_manager.engine, 'trials', column):
            existing_columns.append(column)
        else:
            missing_columns.append(column)
    
    print(f"✅ Existing ADO columns ({len(existing_columns)}): {existing_columns}")
    print(f"❌ Missing ADO columns ({len(missing_columns)}): {missing_columns}")
    
    if missing_columns:
        print(f"\n⚠️ Migration needed: {len(missing_columns)} columns missing")
        return False
    else:
        print(f"\n✅ Migration already complete: All ADO columns present")
        return True

def main():
    """Main migration function"""
    print("🚀 Database Migration Tool")
    print("Adds new ADO fields to existing trials table")
    print("=" * 60)
    
    # Check current status
    if check_migration_status():
        print("\n✅ No migration needed - database already up to date")
        return True
    
    print(f"\n🔄 Starting migration process...")
    
    # Run migration
    success = migrate_database()
    
    if success:
        print(f"\n🎉 Migration completed successfully!")
        print(f"📋 Your database is now ready for enhanced ADO data collection")
    else:
        print(f"\n❌ Migration failed!")
        print(f"📋 Please check the error messages above and try again")
    
    return success

if __name__ == "__main__":
    main()