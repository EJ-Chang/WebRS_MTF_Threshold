#!/usr/bin/env python3
"""
Initialize database tables in Replit PostgreSQL
This script should be run in Replit to create the required tables
"""
import os
from sqlalchemy import create_engine, text
from database import Base, DatabaseManager
from datetime import datetime

def init_replit_database():
    """Initialize database in Replit environment"""
    print("🚀 Initializing Replit PostgreSQL Database...")
    
    # Check if we're in Replit environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found. Make sure you're running this in Replit with PostgreSQL configured.")
        return False
    
    print(f"🔗 Connecting to database: {db_url.split('@')[0]}@***")
    
    try:
        # Create engine directly with DATABASE_URL
        engine = create_engine(db_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database connection successful!")
            print(f"📋 PostgreSQL version: {version[:50]}...")
        
        # Create all tables
        print("\n📊 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"✅ Successfully created {len(tables)} tables:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("❌ No tables found after creation")
                return False
        
        # Test DatabaseManager initialization
        print("\n🧪 Testing DatabaseManager...")
        db_manager = DatabaseManager()
        
        # Create a test participant and experiment
        test_participant = f"init_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"📝 Creating test participant: {test_participant}")
        
        participant = db_manager.create_participant(test_participant)
        print(f"✅ Test participant created successfully")
        
        experiment_id = db_manager.create_experiment(
            participant_id=test_participant,
            experiment_type="initialization_test",
            use_ado=False,
            num_trials=1,
            num_practice_trials=0,
            stimulus_duration=1.0,
            inter_trial_interval=0.5
        )
        print(f"✅ Test experiment created with ID: {experiment_id}")
        
        # Save a test trial
        trial_data = {
            'trial_number': 1,
            'is_practice': False,
            'left_stimulus': 0.6,
            'right_stimulus': 0.4,
            'stimulus_difference': 0.2,
            'response': 'left',
            'is_correct': True,
            'reaction_time': 1.234,
            'timestamp': datetime.now().isoformat()
        }
        
        trial_id = db_manager.save_trial(experiment_id, trial_data)
        print(f"✅ Test trial saved with ID: {trial_id}")
        
        # Verify data retrieval
        experiment_data = db_manager.get_experiment_data(experiment_id)
        if experiment_data and len(experiment_data['trials']) > 0:
            print("✅ Data retrieval test successful")
            print(f"   - Participant: {experiment_data['experiment']['participant_id']}")
            print(f"   - Experiment Type: {experiment_data['experiment']['experiment_type']}")
            print(f"   - Trials Count: {len(experiment_data['trials'])}")
        else:
            print("❌ Data retrieval test failed")
            return False
        
        print("\n🎉 Database initialization completed successfully!")
        print("Your Replit PostgreSQL database is now ready for use.")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def show_next_steps():
    """Show what to do after successful initialization"""
    print("\n📋 Next Steps:")
    print("1. Your database tables are now created and ready")
    print("2. Run your Streamlit app: python app.py")
    print("3. Your experiment data will now be saved to both CSV and PostgreSQL")
    print("4. You can check your data in the Database tab in Replit")

if __name__ == "__main__":
    print("🌐 Replit PostgreSQL Database Initialization")
    print("=" * 60)
    
    success = init_replit_database()
    
    if success:
        show_next_steps()
    else:
        print("\n💡 Troubleshooting:")
        print("1. Make sure DATABASE_URL is set correctly in Replit Secrets")
        print("2. Check that your Neon database is active and accessible")
        print("3. Verify the PostgreSQL connection string format")
        print("4. Try running this script again after fixing the issues")