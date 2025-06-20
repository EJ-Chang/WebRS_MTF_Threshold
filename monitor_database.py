#!/usr/bin/env python3
"""
Real-time monitor for Replit PostgreSQL database
Run this while conducting experiments to see data being saved in real-time
"""
import os
import time
from sqlalchemy import create_engine, text
from datetime import datetime

def monitor_database():
    """Monitor database for new data in real-time"""
    print("👀 Real-time Database Monitor")
    print("=" * 50)
    print("This will show new data as it's added to your Replit PostgreSQL database")
    print("Run your experiment in another tab and watch the data appear here!")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 50)
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found. Run this in Replit!")
        return
    
    engine = create_engine(db_url)
    
    # Track previous counts
    prev_participants = 0
    prev_experiments = 0
    prev_trials = 0
    
    try:
        while True:
            with engine.connect() as conn:
                # Get current counts
                result = conn.execute(text("SELECT COUNT(*) FROM participants"))
                participants = result.fetchone()[0]
                
                result = conn.execute(text("SELECT COUNT(*) FROM experiments"))
                experiments = result.fetchone()[0]
                
                result = conn.execute(text("SELECT COUNT(*) FROM trials"))
                trials = result.fetchone()[0]
                
                # Check for changes
                if (participants != prev_participants or 
                    experiments != prev_experiments or 
                    trials != prev_trials):
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"\n[{timestamp}] 📊 Database Update Detected!")
                    
                    if participants > prev_participants:
                        print(f"  👥 New Participants: {participants - prev_participants}")
                        # Show new participants
                        result = conn.execute(text("""
                            SELECT id, created_at FROM participants 
                            ORDER BY created_at DESC 
                            LIMIT :limit
                        """), {"limit": participants - prev_participants})
                        for pid, created_at in result.fetchall():
                            print(f"     - {pid}")
                    
                    if experiments > prev_experiments:
                        print(f"  🔬 New Experiments: {experiments - prev_experiments}")
                        # Show new experiments
                        result = conn.execute(text("""
                            SELECT id, participant_id, experiment_type FROM experiments 
                            ORDER BY started_at DESC 
                            LIMIT :limit
                        """), {"limit": experiments - prev_experiments})
                        for exp_id, p_id, exp_type in result.fetchall():
                            print(f"     - Exp {exp_id}: {p_id} ({exp_type})")
                    
                    if trials > prev_trials:
                        print(f"  📝 New Trials: {trials - prev_trials}")
                        # Show recent trials
                        result = conn.execute(text("""
                            SELECT t.experiment_id, t.trial_number, t.response, 
                                   t.is_correct, t.reaction_time 
                            FROM trials t
                            ORDER BY t.timestamp DESC 
                            LIMIT :limit
                        """), {"limit": min(5, trials - prev_trials)})
                        for exp_id, trial_num, response, correct, rt in result.fetchall():
                            correct_icon = "✅" if correct else "❌"
                            print(f"     - Exp {exp_id}, Trial {trial_num}: {response} {correct_icon} (RT: {rt}s)")
                    
                    # Update counts
                    prev_participants = participants
                    prev_experiments = experiments
                    prev_trials = trials
                    
                    print(f"  📊 Total: {participants} participants, {experiments} experiments, {trials} trials")
                
                # Show current status every 30 seconds
                current_time = datetime.now()
                if current_time.second % 30 == 0:
                    timestamp = current_time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] 💓 Monitoring... (Total: {participants}P, {experiments}E, {trials}T)")
            
            time.sleep(1)  # Check every second
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped")
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")

def show_latest_data():
    """Show the most recent data in the database"""
    print("📋 Latest Database Entries")
    print("=" * 30)
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Latest participant
            result = conn.execute(text("""
                SELECT id, created_at FROM participants 
                ORDER BY created_at DESC LIMIT 1
            """))
            latest_participant = result.fetchone()
            if latest_participant:
                print(f"👤 Latest Participant: {latest_participant[0]} ({latest_participant[1]})")
            
            # Latest experiment
            result = conn.execute(text("""
                SELECT id, participant_id, experiment_type, started_at 
                FROM experiments 
                ORDER BY started_at DESC LIMIT 1
            """))
            latest_experiment = result.fetchone()
            if latest_experiment:
                print(f"🔬 Latest Experiment: ID {latest_experiment[0]} - {latest_experiment[1]} ({latest_experiment[2]})")
            
            # Latest trials (last 3)
            result = conn.execute(text("""
                SELECT experiment_id, trial_number, response, is_correct, reaction_time, timestamp
                FROM trials 
                ORDER BY timestamp DESC LIMIT 3
            """))
            latest_trials = result.fetchall()
            if latest_trials:
                print("📝 Latest Trials:")
                for exp_id, trial_num, response, correct, rt, timestamp in latest_trials:
                    correct_icon = "✅" if correct else "❌"
                    print(f"   - Exp {exp_id}, Trial {trial_num}: {response} {correct_icon} (RT: {rt}s) at {timestamp}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Monitor database in real-time")
    print("2. Show latest database entries")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        monitor_database()
    elif choice == "2":
        show_latest_data()
    else:
        print("Invalid choice. Showing latest data...")
        show_latest_data()