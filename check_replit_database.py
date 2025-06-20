#!/usr/bin/env python3
"""
Check Replit PostgreSQL database content
This script connects directly to your Replit PostgreSQL and shows what's actually stored
"""
import os
from sqlalchemy import create_engine, text
from datetime import datetime

def check_replit_database():
    """Check what's actually in the Replit PostgreSQL database"""
    print("🔍 Checking Replit PostgreSQL Database Content")
    print("=" * 60)
    
    # Get DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found. Make sure you're running this in Replit.")
        return False
    
    print(f"🔗 Connecting to: {db_url.split('@')[0]}@***")
    
    try:
        # Create engine
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Check PostgreSQL version
            print("\n📋 Database Info:")
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"   PostgreSQL: {version.split(',')[0]}")
            
            # List all tables
            print("\n📊 Tables in Database:")
            result = conn.execute(text("""
                SELECT table_name, 
                       (SELECT COUNT(*) FROM information_schema.columns 
                        WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = result.fetchall()
            if tables:
                for table_name, column_count in tables:
                    print(f"   ✅ {table_name} ({column_count} columns)")
            else:
                print("   ❌ No tables found")
                return False
            
            # Check participants table
            print("\n👥 Participants Table:")
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM participants"))
                participant_count = result.fetchone()[0]
                print(f"   Total participants: {participant_count}")
                
                if participant_count > 0:
                    result = conn.execute(text("""
                        SELECT id, created_at 
                        FROM participants 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """))
                    participants = result.fetchall()
                    print("   Recent participants:")
                    for pid, created_at in participants:
                        print(f"     - {pid} (created: {created_at})")
                else:
                    print("   No participants found")
            except Exception as e:
                print(f"   ❌ Error checking participants: {e}")
            
            # Check experiments table
            print("\n🔬 Experiments Table:")
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM experiments"))
                experiment_count = result.fetchone()[0]
                print(f"   Total experiments: {experiment_count}")
                
                if experiment_count > 0:
                    result = conn.execute(text("""
                        SELECT id, participant_id, experiment_type, started_at, completed_at
                        FROM experiments 
                        ORDER BY started_at DESC 
                        LIMIT 5
                    """))
                    experiments = result.fetchall()
                    print("   Recent experiments:")
                    for exp_id, p_id, exp_type, started, completed in experiments:
                        status = "✅ Completed" if completed else "🔄 In Progress"
                        print(f"     - ID:{exp_id} | {p_id} | {exp_type} | {status}")
                else:
                    print("   No experiments found")
            except Exception as e:
                print(f"   ❌ Error checking experiments: {e}")
            
            # Check trials table
            print("\n📝 Trials Table:")
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM trials"))
                trial_count = result.fetchone()[0]
                print(f"   Total trials: {trial_count}")
                
                if trial_count > 0:
                    result = conn.execute(text("""
                        SELECT t.id, t.experiment_id, t.trial_number, t.response, 
                               t.is_correct, t.reaction_time, t.timestamp
                        FROM trials t
                        ORDER BY t.timestamp DESC 
                        LIMIT 10
                    """))
                    trials = result.fetchall()
                    print("   Recent trials:")
                    for trial_id, exp_id, trial_num, response, correct, rt, timestamp in trials:
                        correct_icon = "✅" if correct else "❌"
                        print(f"     - Trial {trial_num} (Exp:{exp_id}) | {response} {correct_icon} | RT:{rt}s | {timestamp}")
                else:
                    print("   No trials found")
            except Exception as e:
                print(f"   ❌ Error checking trials: {e}")
            
            # Summary
            print(f"\n📊 Database Summary:")
            print(f"   Tables: {len(tables) if tables else 0}")
            try:
                print(f"   Participants: {participant_count}")
                print(f"   Experiments: {experiment_count}")
                print(f"   Trials: {trial_count}")
            except:
                pass
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def insert_test_data():
    """Insert test data to verify database is working"""
    print("\n🧪 Inserting Test Data...")
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Insert test participant
            test_id = f"replit_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            conn.execute(text("""
                INSERT INTO participants (id, created_at) 
                VALUES (:id, :created_at)
            """), {"id": test_id, "created_at": datetime.now()})
            
            # Insert test experiment
            result = conn.execute(text("""
                INSERT INTO experiments (participant_id, experiment_type, use_ado, started_at) 
                VALUES (:participant_id, :experiment_type, :use_ado, :started_at)
                RETURNING id
            """), {
                "participant_id": test_id,
                "experiment_type": "replit_verification_test",
                "use_ado": False,
                "started_at": datetime.now()
            })
            exp_id = result.fetchone()[0]
            
            # Insert test trial
            conn.execute(text("""
                INSERT INTO trials (experiment_id, trial_number, response, is_correct, reaction_time, timestamp)
                VALUES (:experiment_id, :trial_number, :response, :is_correct, :reaction_time, :timestamp)
            """), {
                "experiment_id": exp_id,
                "trial_number": 1,
                "response": "left",
                "is_correct": True,
                "reaction_time": 1.234,
                "timestamp": datetime.now()
            })
            
            conn.commit()
            
            print(f"✅ Test data inserted:")
            print(f"   Participant: {test_id}")
            print(f"   Experiment ID: {exp_id}")
            print(f"   Trial: 1 record")
            
            return True
            
    except Exception as e:
        print(f"❌ Test data insertion failed: {e}")
        return False

if __name__ == "__main__":
    # Check current database content
    success = check_replit_database()
    
    if success:
        print("\n" + "=" * 60)
        user_input = input("Do you want to insert test data? (y/n): ").lower().strip()
        if user_input == 'y':
            insert_test_data()
            print("\n🔄 Checking database again after test data insertion...")
            check_replit_database()
    else:
        print("\n💡 Make sure:")
        print("1. You're running this in Replit")
        print("2. DATABASE_URL is set in Secrets")
        print("3. psycopg2-binary is installed")