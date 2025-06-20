#!/usr/bin/env python3
"""
Test script specifically for Replit PostgreSQL connection
This script will help diagnose database connection issues in Replit
"""
import os
from database import DatabaseManager
from datetime import datetime

def test_replit_database():
    """Test Replit database connection and basic operations"""
    print("🌐 Testing Replit PostgreSQL connection...")
    
    # Check environment variables
    print("\n📋 Environment Variables Check:")
    db_url = os.getenv('DATABASE_URL')
    pg_database = os.getenv('PGDATABASE')
    pg_host = os.getenv('PGHOST')
    pg_user = os.getenv('PGUSER')
    pg_password = os.getenv('PGPASSWORD')
    pg_port = os.getenv('PGPORT')
    
    if db_url:
        print(f"✅ DATABASE_URL found: {db_url[:30]}...")
    else:
        print("❌ DATABASE_URL not found")
    
    if pg_database:
        print(f"✅ PGDATABASE found: {pg_database}")
    if pg_host:
        print(f"✅ PGHOST found: {pg_host}")
    if pg_user:
        print(f"✅ PGUSER found: {pg_user}")
    if pg_password:
        print("✅ PGPASSWORD found: [HIDDEN]")
    if pg_port:
        print(f"✅ PGPORT found: {pg_port}")
    
    # Test database manager initialization
    print("\n🔗 Testing DatabaseManager initialization...")
    try:
        db_manager = DatabaseManager()
        print("✅ DatabaseManager initialized successfully")
        
        # Test basic operations
        print("\n🧪 Testing basic database operations...")
        
        # Test participant creation
        test_participant = f"replit_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        participant = db_manager.create_participant(test_participant)
        print(f"✅ Test participant created: {test_participant}")
        
        # Test experiment creation  
        experiment_id = db_manager.create_experiment(
            participant_id=test_participant,
            experiment_type="replit_test",
            use_ado=False,
            num_trials=1,
            num_practice_trials=0,
            stimulus_duration=1.0,
            inter_trial_interval=0.5
        )
        print(f"✅ Test experiment created with ID: {experiment_id}")
        
        # Test trial saving
        trial_data = {
            'trial_number': 1,
            'is_practice': False,
            'left_stimulus': 0.5,
            'right_stimulus': 0.3,
            'stimulus_difference': 0.2,
            'mtf_value': 0.4,
            'response': 'left',
            'is_correct': True,
            'reaction_time': 1.123,
            'timestamp': datetime.now().isoformat()
        }
        
        trial_id = db_manager.save_trial(experiment_id, trial_data)
        print(f"✅ Test trial saved with ID: {trial_id}")
        
        # Test data retrieval
        experiment_data = db_manager.get_experiment_data(experiment_id)
        if experiment_data:
            print("✅ Data retrieval successful")
            print(f"   Participant: {experiment_data['experiment']['participant_id']}")
            print(f"   Trials: {len(experiment_data['trials'])}")
        else:
            print("❌ Data retrieval failed")
        
        print("\n🎉 All Replit database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def show_database_url_format():
    """Show the expected DATABASE_URL format"""
    print("\n📋 Expected DATABASE_URL format:")
    print("postgresql://username:password@hostname:port/database_name")
    print("\nFor Replit Neon PostgreSQL, it should look like:")
    print("postgresql://neondb_owner:your_password@ep-xxxxx.us-east-2.aws.neon.tech:5432/neondb")

if __name__ == "__main__":
    print("🚀 Replit Database Test Script")
    print("=" * 50)
    
    if not os.getenv('DATABASE_URL'):
        print("⚠️  DATABASE_URL not found in environment")
        print("This script is designed for Replit with PostgreSQL configured")
        show_database_url_format()
        print("\nRunning test anyway (will use SQLite fallback)...")
    
    success = test_replit_database()
    
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure DATABASE_URL is set in Replit Secrets")
        print("2. Check if your Neon database is active")
        print("3. Verify the connection string format")
        show_database_url_format()