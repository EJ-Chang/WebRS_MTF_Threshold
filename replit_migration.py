"""
Simplified migration script specifically for Replit environment
Ensures database stores all experimental data like CSV
"""
import os
import sys
from datetime import datetime

def check_replit_database():
    """Check and migrate Replit database to match CSV format"""
    print("🔧 Replit Database Migration Check")
    print("=" * 40)
    
    try:
        from database import DatabaseManager
        
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Check database connection
        db_url = db_manager.database_url
        is_replit = 'DATABASE_URL' in os.environ or 'REPLIT_DB_URL' in os.environ
        
        print(f"🌐 Environment: {'Replit' if is_replit else 'Local'}")
        print(f"📊 Database: {db_url.split('@')[0] if '@' in db_url else 'SQLite'}")
        
        # Test creating a participant and experiment
        test_participant = f"migration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n🧪 Testing with participant: {test_participant}")
        
        # Create participant
        db_manager.create_participant(test_participant)
        print("✅ Participant created")
        
        # Create experiment
        experiment_id = db_manager.create_experiment(
            participant_id=test_participant,
            experiment_type="MTF_Clarity_Test",
            use_ado=False,
            num_trials=1
        )
        print(f"✅ Experiment created (ID: {experiment_id})")
        
        # Test trial data with all CSV fields
        test_data = {
            'trial_number': 1,
            'mtf_value': 75.0,
            'response': 'clear',
            'reaction_time': 2.345,
            'timestamp': datetime.now().isoformat(),
            'participant_id': test_participant,
            'experiment_type': 'MTF_Clarity_Test',
            'stimulus_image_file': 'test_migration.png',
            'is_correct': None,
            'left_stimulus': None,
            'right_stimulus': None,
            'stimulus_difference': None,
            'ado_stimulus_value': 75.0,
            'is_practice': False,
            'experiment_timestamp': datetime.now().isoformat()
        }
        
        # Save trial
        trial_id = db_manager.save_trial(experiment_id, test_data)
        print(f"✅ Trial saved (ID: {trial_id})")
        
        # Verify retrieval
        experiment_data = db_manager.get_experiment_data(experiment_id)
        
        if experiment_data and experiment_data['trials']:
            trial = experiment_data['trials'][0]
            
            # Check critical experimental fields
            critical_fields = [
                'participant_id', 'trial_number', 'mtf_value', 
                'stimulus_image_file', 'response', 'reaction_time'
            ]
            
            print(f"\n📊 Critical experimental data verification:")
            all_good = True
            
            for field in critical_fields:
                value = trial.get(field)
                status = "✅" if value is not None else "❌"
                print(f"   {status} {field}: {value}")
                
                if value is None:
                    all_good = False
            
            if all_good:
                print(f"\n🎉 SUCCESS: All critical experimental data stored correctly!")
                print(f"💾 Database is ready to store:")
                print(f"   - Participant information")
                print(f"   - Trial numbers and MTF values") 
                print(f"   - Stimulus images used")
                print(f"   - Participant responses")
                print(f"   - Reaction times")
            else:
                print(f"\n❌ ISSUE: Some critical experimental data is missing")
                print(f"🔧 You may need to run database migration")
                
        else:
            print("❌ Failed to retrieve saved trial data")
            
        print(f"\n" + "=" * 40)
        return all_good
        
    except Exception as e:
        print(f"❌ Migration check failed: {e}")
        print(f"🔧 Error type: {type(e).__name__}")
        
        # Provide troubleshooting advice
        print(f"\n💡 Troubleshooting:")
        print(f"   1. Check database connection")
        print(f"   2. Verify environment variables")
        print(f"   3. Run: python migrate_database.py")
        
        return False

if __name__ == "__main__":
    success = check_replit_database()
    if success:
        print("✅ Database is ready for experimental data!")
    else:
        print("⚠️ Database needs attention before use.")
        sys.exit(1)