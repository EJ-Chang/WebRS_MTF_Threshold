#!/usr/bin/env python3
"""
Test script to verify app.py database integration
"""
import sys
import os
sys.path.append(os.getcwd())

from database import DatabaseManager
from csv_data_manager import CSVDataManager
from datetime import datetime
import random

def test_app_database_integration():
    """Test the database integration as used in app.py"""
    print("🧪 Testing app.py database integration...")
    
    # Initialize managers (like in app.py)
    csv_manager = CSVDataManager()
    db_manager = DatabaseManager()
    
    # Simulate app.py participant creation
    participant_id = f"test_app_user_{random.randint(1000, 9999)}"
    experiment_type = "MTF_test"
    
    print(f"📝 Testing with participant: {participant_id}")
    
    # Simulate experiment configuration
    experiment_config = {
        'experiment_type': experiment_type,
        'use_ado': True,
        'num_trials': 10,
        'num_practice_trials': 2,
        'stimulus_duration': 1.0,
        'inter_trial_interval': 0.5
    }
    
    # Create CSV record (as in app.py)
    csv_manager.create_participant_record(participant_id, experiment_config)
    print("✅ CSV participant record created")
    
    # Create database records (as in app.py)
    try:
        db_manager.create_participant(participant_id)
        experiment_id = db_manager.create_experiment(
            participant_id=participant_id,
            experiment_type=experiment_type,
            use_ado=experiment_config.get('use_ado', False),
            num_trials=experiment_config.get('num_trials'),
            num_practice_trials=experiment_config.get('num_practice_trials'),
            stimulus_duration=experiment_config.get('stimulus_duration'),
            inter_trial_interval=experiment_config.get('inter_trial_interval')
        )
        print(f"✅ Database experiment created with ID: {experiment_id}")
    except Exception as db_error:
        print(f"❌ Database experiment creation failed: {db_error}")
        return False
    
    # Simulate trial data saving (as in app.py)
    trial_result = {
        'trial_number': 1,
        'is_practice': False,
        'left_stimulus': 0.6,
        'right_stimulus': 0.4,
        'stimulus_difference': 0.2,
        'mtf_value': 0.5,
        'ado_stimulus_value': 0.5,
        'stimulus_image_file': 'test_stimulus.png',
        'response': 'left',
        'is_correct': True,
        'reaction_time': 1.456,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save to CSV (primary backup)
    csv_manager.save_trial_data(participant_id, trial_result)
    print("✅ Trial data saved to CSV")
    
    # Save to database (secondary backup)
    if experiment_id:
        try:
            db_manager.save_trial(experiment_id, trial_result)
            print(f"✅ Trial data saved to database (experiment_id: {experiment_id})")
        except Exception as db_error:
            print(f"❌ Database trial save failed: {db_error}")
            return False
    
    # Verify data was saved correctly
    experiment_data = db_manager.get_experiment_data(experiment_id)
    if experiment_data and len(experiment_data['trials']) > 0:
        trial = experiment_data['trials'][0]
        print("✅ Data verification successful:")
        print(f"   - Response: {trial['response']}")
        print(f"   - Correct: {trial['is_correct']}")
        print(f"   - RT: {trial['reaction_time']}s")
        print(f"   - MTF Value: {trial['mtf_value']}")
    else:
        print("❌ Data verification failed")
        return False
    
    print("\n🎉 App database integration test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = test_app_database_integration()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)