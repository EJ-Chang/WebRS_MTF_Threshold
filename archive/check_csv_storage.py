#!/usr/bin/env python3
"""
Check CSV storage functionality
This script will help diagnose why CSV files might not be created
"""
import os
import pandas as pd
from csv_data_manager import CSVDataManager
from datetime import datetime

def check_csv_directory():
    """Check CSV data directory and files"""
    print("📁 Checking CSV Storage")
    print("=" * 40)
    
    # Check data directory
    data_dir = "experiment_data"
    print(f"📂 Data directory: {data_dir}")
    
    if os.path.exists(data_dir):
        print("✅ Data directory exists")
        
        # List all files
        files = os.listdir(data_dir)
        if files:
            print(f"📋 Files found ({len(files)}):")
            for file in sorted(files):
                file_path = os.path.join(data_dir, file)
                file_size = os.path.getsize(file_path)
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"   - {file} ({file_size} bytes, modified: {modified_time})")
                
                # If it's a CSV file, show content preview
                if file.endswith('.csv'):
                    try:
                        df = pd.read_csv(file_path)
                        print(f"     Rows: {len(df)}, Columns: {len(df.columns)}")
                        if len(df) > 0:
                            print(f"     Latest row: {df.iloc[-1].to_dict()}")
                    except Exception as e:
                        print(f"     Error reading CSV: {e}")
        else:
            print("📭 No files found in data directory")
    else:
        print("❌ Data directory does not exist")
    
    return os.path.exists(data_dir) and len(os.listdir(data_dir)) > 0

def test_csv_manager():
    """Test CSV manager functionality"""
    print("\n🧪 Testing CSV Manager")
    print("=" * 30)
    
    try:
        # Initialize CSV manager
        csv_manager = CSVDataManager()
        print("✅ CSV Manager initialized")
        
        # Test participant creation
        test_participant = f"csv_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        experiment_config = {
            'experiment_type': 'csv_test',
            'use_ado': False,
            'num_trials': 1
        }
        
        print(f"📝 Creating test participant: {test_participant}")
        csv_manager.create_participant_record(test_participant, experiment_config)
        
        # Test trial data saving
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
        
        print("💾 Saving test trial data...")
        csv_manager.save_trial_data(test_participant, trial_data)
        
        # Verify file was created
        csv_file = csv_manager.get_participant_file_path(test_participant)
        summary_file = csv_manager.get_experiment_summary_path(test_participant)
        
        if os.path.exists(csv_file):
            print(f"✅ CSV file created: {csv_file}")
            df = pd.read_csv(csv_file)
            print(f"   Rows: {len(df)}")
            print(f"   Content: {df.iloc[0].to_dict()}")
        else:
            print(f"❌ CSV file not found: {csv_file}")
        
        if os.path.exists(summary_file):
            print(f"✅ Summary file created: {summary_file}")
            with open(summary_file, 'r') as f:
                import json
                summary = json.load(f)
                print(f"   Content: {summary}")
        else:
            print(f"❌ Summary file not found: {summary_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ CSV Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_permissions():
    """Check directory permissions"""
    print("\n🔒 Checking Permissions")
    print("=" * 25)
    
    current_dir = os.getcwd()
    print(f"📂 Current directory: {current_dir}")
    print(f"   Readable: {os.access(current_dir, os.R_OK)}")
    print(f"   Writable: {os.access(current_dir, os.W_OK)}")
    print(f"   Executable: {os.access(current_dir, os.X_OK)}")
    
    data_dir = "experiment_data"
    if os.path.exists(data_dir):
        print(f"📂 Data directory: {data_dir}")
        print(f"   Readable: {os.access(data_dir, os.R_OK)}")
        print(f"   Writable: {os.access(data_dir, os.W_OK)}")
        print(f"   Executable: {os.access(data_dir, os.X_OK)}")
    
    # Test write permission
    try:
        test_file = os.path.join(current_dir, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Write permission test passed")
    except Exception as e:
        print(f"❌ Write permission test failed: {e}")

def show_debug_info():
    """Show debug information that might help"""
    print("\n🔍 Debug Information")
    print("=" * 25)
    
    print(f"Python working directory: {os.getcwd()}")
    print(f"Python path: {os.path.dirname(os.path.abspath(__file__))}")
    
    # Show environment variables that might affect file operations
    relevant_env_vars = ['HOME', 'USER', 'PWD', 'TMPDIR', 'TMP']
    for var in relevant_env_vars:
        value = os.getenv(var)
        if value:
            print(f"Environment {var}: {value}")

if __name__ == "__main__":
    print("🩺 CSV Storage Diagnostic Tool")
    print("=" * 50)
    
    # Run all checks
    check_permissions()
    show_debug_info()
    has_csv_files = check_csv_directory()
    csv_test_passed = test_csv_manager()
    
    print("\n📊 Summary")
    print("=" * 15)
    print(f"CSV files exist: {'✅' if has_csv_files else '❌'}")
    print(f"CSV manager works: {'✅' if csv_test_passed else '❌'}")
    
    if not has_csv_files and csv_test_passed:
        print("\n💡 CSV manager works but no existing files found.")
        print("This suggests data might not be reaching the CSV save function.")
        print("Check your Streamlit app logs for CSV save messages.")
    elif has_csv_files:
        print("\n✅ CSV storage is working correctly!")
    else:
        print("\n❌ CSV storage has issues. Check the errors above.")