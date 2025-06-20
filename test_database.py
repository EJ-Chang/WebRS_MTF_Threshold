
#!/usr/bin/env python3
"""
Simple database test script - insert test data
"""
from database import DatabaseManager
from datetime import datetime
import random

def test_database_insert():
    """Test inserting data into the database"""
    print("🧪 Testing database connection...")
    
    # Initialize database
    db_manager = DatabaseManager()
    
    # Create test participant
    test_participant_id = f"test_user_{random.randint(1000, 9999)}"
    print(f"📝 Creating test participant: {test_participant_id}")
    
    participant = db_manager.create_participant(test_participant_id)
    print(f"✅ Participant created: {participant.id}")
    
    # Create test experiment
    print("🔬 Creating test experiment...")
    experiment_id = db_manager.create_experiment(
        participant_id=test_participant_id,
        experiment_type="test_experiment",
        use_ado=False,
        num_trials=1,
        num_practice_trials=0,
        stimulus_duration=1.0,
        inter_trial_interval=0.5
    )
    print(f"✅ Experiment created with ID: {experiment_id}")
    
    # Create test trial data
    test_trial_data = {
        'trial_number': 1,
        'is_practice': False,
        'left_stimulus': 0.5,
        'right_stimulus': 0.7,
        'stimulus_difference': 0.2,
        'mtf_value': None,
        'ado_stimulus_value': None,
        'stimulus_image_file': 'test_image.png',
        'response': 'right',
        'is_correct': True,
        'reaction_time': 1.234,
        'timestamp': datetime.now().isoformat()
    }
    
    print("💾 Saving test trial data...")
    trial_id = db_manager.save_trial(experiment_id, test_trial_data)
    print(f"✅ Trial saved with ID: {trial_id}")
    
    # Complete the experiment
    db_manager.complete_experiment(experiment_id)
    print("✅ Experiment marked as completed")
    
    # Retrieve and display the data
    print("\n📊 Retrieving saved data...")
    experiment_data = db_manager.get_experiment_data(experiment_id)
    
    if experiment_data:
        print("✅ Data retrieved successfully!")
        print(f"   Participant: {experiment_data['experiment']['participant_id']}")
        print(f"   Experiment Type: {experiment_data['experiment']['experiment_type']}")
        print(f"   Trials Count: {len(experiment_data['trials'])}")
        print(f"   First Trial Response: {experiment_data['trials'][0]['response']}")
        print(f"   First Trial RT: {experiment_data['trials'][0]['reaction_time']}s")
    else:
        print("❌ Failed to retrieve data")
    
    print("\n🎉 Database test completed successfully!")

if __name__ == "__main__":
    try:
        test_database_insert()
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
