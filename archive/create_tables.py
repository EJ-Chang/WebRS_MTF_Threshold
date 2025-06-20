#!/usr/bin/env python3
"""
Simple script to create database tables
Run this in Replit to initialize your PostgreSQL database
"""
import os
from database import DatabaseManager

def create_tables():
    """Create database tables"""
    print("📊 Creating database tables...")
    
    try:
        # Initialize DatabaseManager (this will create tables automatically)
        db_manager = DatabaseManager()
        print("✅ Database tables created successfully!")
        
        # Test with a simple query
        participants = db_manager.get_all_participants()
        print(f"📋 Current participants in database: {len(participants)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Creating Database Tables")
    print("=" * 30)
    
    # Check environment
    if os.getenv('DATABASE_URL'):
        print("🐘 Using PostgreSQL (Replit)")
    else:
        print("💾 Using SQLite (Local)")
    
    success = create_tables()
    
    if success:
        print("\n🎉 Tables created successfully!")
        print("You can now run your experiments and data will be saved to the database.")
    else:
        print("\n❌ Table creation failed.")
        print("Check the error messages above for details.")