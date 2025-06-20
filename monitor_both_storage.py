#!/usr/bin/env python3
"""
Monitor both CSV and Database storage simultaneously
This helps identify which storage method is working
"""
import os
import time
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

def monitor_storage():
    """Monitor both CSV and database storage"""
    print("👀 Monitoring Both Storage Systems")
    print("=" * 50)
    print("Run your experiment and watch both CSV and Database updates!")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    # Initialize tracking
    csv_dir = "experiment_data"
    prev_csv_files = set()
    prev_csv_sizes = {}
    
    # Database setup
    db_url = os.getenv('DATABASE_URL')
    db_engine = None
    if db_url:
        try:
            db_engine = create_engine(db_url)
            print("🐘 Database connection ready")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
    else:
        print("❌ DATABASE_URL not found")
    
    prev_db_counts = {'participants': 0, 'experiments': 0, 'trials': 0}
    
    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            changes_detected = False
            
            # Check CSV files
            if os.path.exists(csv_dir):
                current_csv_files = set(os.listdir(csv_dir))
                current_csv_sizes = {}
                
                for file in current_csv_files:
                    if file.endswith('.csv'):
                        file_path = os.path.join(csv_dir, file)
                        current_csv_sizes[file] = os.path.getsize(file_path)
                
                # Check for new files
                new_files = current_csv_files - prev_csv_files
                if new_files:
                    changes_detected = True
                    print(f"\n[{timestamp}] 📁 New CSV files:")
                    for file in new_files:
                        print(f"   + {file}")
                
                # Check for file size changes (new data)
                for file, size in current_csv_sizes.items():
                    prev_size = prev_csv_sizes.get(file, 0)
                    if size > prev_size:
                        changes_detected = True
                        print(f"\n[{timestamp}] 📝 CSV file updated:")
                        print(f"   📄 {file}: {prev_size} → {size} bytes")
                        
                        # Show latest data from CSV
                        try:
                            file_path = os.path.join(csv_dir, file)
                            df = pd.read_csv(file_path)
                            if len(df) > 0:
                                latest_row = df.iloc[-1]
                                print(f"   📊 Latest trial: {latest_row.get('trial_number', '?')} - {latest_row.get('response', '?')} (RT: {latest_row.get('reaction_time', '?')}s)")
                        except Exception as e:
                            print(f"   ❌ Error reading CSV: {e}")
                
                prev_csv_files = current_csv_files
                prev_csv_sizes = current_csv_sizes
            
            # Check database
            if db_engine:
                try:
                    with db_engine.connect() as conn:
                        # Get current counts
                        result = conn.execute(text("SELECT COUNT(*) FROM participants"))
                        participants = result.fetchone()[0]
                        
                        result = conn.execute(text("SELECT COUNT(*) FROM experiments"))
                        experiments = result.fetchone()[0]
                        
                        result = conn.execute(text("SELECT COUNT(*) FROM trials"))
                        trials = result.fetchone()[0]
                        
                        current_db_counts = {
                            'participants': participants,
                            'experiments': experiments, 
                            'trials': trials
                        }
                        
                        # Check for changes
                        for table, count in current_db_counts.items():
                            if count > prev_db_counts[table]:
                                changes_detected = True
                                diff = count - prev_db_counts[table]
                                print(f"\n[{timestamp}] 🐘 Database update:")
                                print(f"   📊 {table}: +{diff} (total: {count})")
                                
                                # Show latest database entry
                                if table == 'trials' and diff > 0:
                                    result = conn.execute(text("""
                                        SELECT experiment_id, trial_number, response, is_correct, reaction_time
                                        FROM trials ORDER BY timestamp DESC LIMIT 1
                                    """))
                                    latest_trial = result.fetchone()
                                    if latest_trial:
                                        exp_id, trial_num, response, correct, rt = latest_trial
                                        correct_icon = "✅" if correct else "❌"
                                        print(f"   📝 Latest trial: Exp {exp_id}, Trial {trial_num} - {response} {correct_icon} (RT: {rt}s)")
                        
                        prev_db_counts = current_db_counts
                        
                except Exception as e:
                    print(f"[{timestamp}] ❌ Database check error: {e}")
            
            # Show status every 30 seconds if no changes
            if not changes_detected and datetime.now().second % 30 == 0:
                csv_count = len([f for f in os.listdir(csv_dir) if f.endswith('.csv')]) if os.path.exists(csv_dir) else 0
                db_status = f"{prev_db_counts['trials']}T" if db_engine else "No DB"
                print(f"[{timestamp}] 💓 Monitoring... (CSV files: {csv_count}, DB: {db_status})")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

def compare_storage():
    """Compare data between CSV and database"""
    print("🔍 Comparing CSV and Database Storage")
    print("=" * 40)
    
    # Check CSV data
    csv_dir = "experiment_data"
    csv_data = {}
    
    if os.path.exists(csv_dir):
        csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
        print(f"📁 CSV files found: {len(csv_files)}")
        
        total_csv_trials = 0
        for file in csv_files:
            file_path = os.path.join(csv_dir, file)
            try:
                df = pd.read_csv(file_path)
                participant_id = file.replace('_data.csv', '')
                csv_data[participant_id] = len(df)
                total_csv_trials += len(df)
                print(f"   📄 {participant_id}: {len(df)} trials")
            except Exception as e:
                print(f"   ❌ Error reading {file}: {e}")
        
        print(f"📊 Total CSV trials: {total_csv_trials}")
    else:
        print("❌ No CSV directory found")
    
    # Check database data
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                # Get database counts
                result = conn.execute(text("SELECT COUNT(*) FROM participants"))
                db_participants = result.fetchone()[0]
                
                result = conn.execute(text("SELECT COUNT(*) FROM experiments"))
                db_experiments = result.fetchone()[0]
                
                result = conn.execute(text("SELECT COUNT(*) FROM trials"))
                db_trials = result.fetchone()[0]
                
                print(f"\n🐘 Database records:")
                print(f"   👥 Participants: {db_participants}")
                print(f"   🔬 Experiments: {db_experiments}")
                print(f"   📝 Trials: {db_trials}")
                
                # Compare totals
                if csv_data:
                    print(f"\n📊 Comparison:")
                    print(f"   CSV participants: {len(csv_data)}")
                    print(f"   DB participants: {db_participants}")
                    print(f"   CSV trials: {total_csv_trials}")
                    print(f"   DB trials: {db_trials}")
                    
                    if total_csv_trials == db_trials:
                        print("✅ Data counts match!")
                    else:
                        print("⚠️ Data counts don't match")
                
        except Exception as e:
            print(f"❌ Database check failed: {e}")
    else:
        print("❌ DATABASE_URL not found")

if __name__ == "__main__":
    print("Choose monitoring option:")
    print("1. Real-time monitoring")
    print("2. Compare current data")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        monitor_storage()
    elif choice == "2":
        compare_storage()
    else:
        print("Invalid choice. Running comparison...")
        compare_storage()