#!/usr/bin/env python3
"""
Install PostgreSQL dependencies for Replit
Run this first before initializing the database
"""
import subprocess
import sys

def install_psycopg2():
    """Install psycopg2-binary for PostgreSQL support"""
    print("📦 Installing PostgreSQL dependencies...")
    
    try:
        # Install psycopg2-binary
        print("Installing psycopg2-binary...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary>=2.9.0"])
        print("✅ psycopg2-binary installed successfully")
        
        # Test import
        try:
            import psycopg2
            print("✅ psycopg2 import test successful")
            print(f"📋 psycopg2 version: {psycopg2.__version__}")
        except ImportError as e:
            print(f"❌ psycopg2 import failed: {e}")
            return False
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False

def main():
    print("🚀 Installing Database Dependencies for Replit")
    print("=" * 50)
    
    success = install_psycopg2()
    
    if success:
        print("\n🎉 All dependencies installed successfully!")
        print("\nNext steps:")
        print("1. Run: python init_replit_database.py")
        print("2. Or run: python create_tables.py")
    else:
        print("\n❌ Installation failed.")
        print("You may need to install dependencies manually:")
        print("pip install psycopg2-binary")

if __name__ == "__main__":
    main()