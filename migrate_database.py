"""
Database migration script to add new columns to trials table
for consistency with CSV format - ensures all experimental data is stored
"""
import os
from sqlalchemy import create_engine, text, inspect
from database import DatabaseManager

def migrate_database():
    """Add new columns to trials table if they don't exist"""
    print("🔧 Starting database migration...")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        engine = db_manager.engine
        
        # Check if we're using PostgreSQL (Replit) or SQLite
        db_url = db_manager.database_url
        is_postgres = 'postgresql' in db_url
        
        print(f"📊 Database type: {'PostgreSQL' if is_postgres else 'SQLite'}")
        print(f"🔗 Database URL: {db_url.split('@')[0] if '@' in db_url else db_url}")
        
        with engine.connect() as conn:
            # Check current table structure
            inspector = inspect(engine)
            columns = inspector.get_columns('trials')
            existing_columns = [col['name'] for col in columns]
            
            print(f"📋 Current columns in trials table: {existing_columns}")
            
            # Define new columns we need for CSV compatibility
            new_columns = {
                'participant_id': 'TEXT',
                'experiment_type': 'TEXT', 
                'experiment_timestamp': 'TEXT'
            }
            
            migration_needed = False
            
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    migration_needed = True
                    try:
                        # Different syntax for PostgreSQL vs SQLite
                        if is_postgres:
                            conn.execute(text(f"ALTER TABLE trials ADD COLUMN {col_name} VARCHAR"))
                        else:
                            conn.execute(text(f"ALTER TABLE trials ADD COLUMN {col_name} {col_type}"))
                        
                        conn.commit()
                        print(f"✅ Added column: {col_name}")
                    except Exception as e:
                        print(f"⚠️ Failed to add column {col_name}: {e}")
                        # Column might already exist in some cases
                        if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                            print(f"✓ Column {col_name} already exists")
                        else:
                            raise e
                else:
                    print(f"✓ Column {col_name} already exists")
            
            if not migration_needed:
                print("✅ No migration needed - all columns present")
            else:
                print("✅ Database migration completed successfully")
                
                # Verify migration
                inspector = inspect(engine)
                updated_columns = inspector.get_columns('trials')
                updated_column_names = [col['name'] for col in updated_columns]
                print(f"📋 Updated columns in trials table: {updated_column_names}")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("💡 This might happen if:")
        print("   - Database is not accessible")
        print("   - Insufficient permissions")
        print("   - Connection issues")
        raise e

def verify_data_integrity():
    """Verify that the database can store and retrieve all CSV fields"""
    print("\n🔍 Verifying data integrity...")
    
    try:
        db_manager = DatabaseManager()
        
        # Create a test participant
        test_participant_id = "test_migration_user"
        db_manager.create_participant(test_participant_id)
        
        # Create a test experiment
        experiment_id = db_manager.create_experiment(
            participant_id=test_participant_id,
            experiment_type="MTF_Clarity",
            use_ado=False,
            num_trials=1
        )
        
        # Test data with all CSV fields
        test_trial_data = {
            'trial_number': 1,
            'mtf_value': 50.0,
            'response': 'clear',
            'reaction_time': 1.234,
            'timestamp': '2025-06-20T18:00:00.000000',
            'participant_id': test_participant_id,
            'experiment_type': 'MTF_Clarity',
            'stimulus_image_file': 'test_image.png',
            'is_correct': None,
            'left_stimulus': None,
            'right_stimulus': None,
            'stimulus_difference': None,
            'ado_stimulus_value': 50.0,
            'is_practice': False,
            'experiment_timestamp': '2025-06-20T17:59:00.000000'
        }
        
        # Save test trial
        trial_id = db_manager.save_trial(experiment_id, test_trial_data)
        print(f"✅ Test trial saved with ID: {trial_id}")
        
        # Retrieve and verify
        experiment_data = db_manager.get_experiment_data(experiment_id)
        if experiment_data and experiment_data['trials']:
            trial = experiment_data['trials'][0]
            print(f"📊 Retrieved trial data fields: {list(trial.keys())}")
            
            # Check key fields
            key_fields = ['participant_id', 'mtf_value', 'stimulus_image_file', 'response', 'reaction_time']
            missing_fields = [field for field in key_fields if field not in trial or trial[field] is None]
            
            if missing_fields:
                print(f"⚠️ Missing or null key fields: {missing_fields}")
            else:
                print("✅ All key experimental fields present and non-null")
        
        print("✅ Data integrity verification completed")
        
    except Exception as e:
        print(f"❌ Data integrity verification failed: {e}")
        raise e

if __name__ == "__main__":
    print("🚀 Database Migration and Verification Tool")
    print("=" * 50)
    
    try:
        # Step 1: Migrate database structure
        migrate_database()
        
        # Step 2: Verify data integrity
        verify_data_integrity()
        
        print("\n" + "=" * 50)
        print("🎉 Migration and verification completed successfully!")
        print("💾 Database is now fully compatible with CSV format")
        
    except Exception as e:
        print(f"\n❌ Process failed: {e}")
        print("Please check the error messages above and fix any issues.")