#!/usr/bin/env python3
"""
Legacy entry point - Use run.py for Replit deployment
This file is maintained for compatibility but run.py is preferred
"""

import os
import sys
import subprocess

def setup_replit_environment():
    """Set up environment variables and configurations for Replit"""

    # Set environment variables for Replit
    os.environ['STREAMLIT_SERVER_PORT'] = '5000'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

    # Ensure database URL is set for PostgreSQL in Replit
    if 'DATABASE_URL' not in os.environ:
        # Try to detect Replit PostgreSQL
        replit_db_url = os.environ.get('REPLIT_DB_URL')
        if replit_db_url:
            os.environ['DATABASE_URL'] = replit_db_url
        else:
            # Fallback to local SQLite for development
            os.environ['DATABASE_URL'] = 'sqlite:///./psychophysics.db'
            print("⚠️ No PostgreSQL detected, using SQLite fallback")

    print("🚀 Replit environment configured successfully")

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'streamlit', 'numpy', 'opencv-python', 'pandas', 
        'plotly', 'scipy', 'pillow', 'sqlalchemy'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        # print("Installing missing packages...")
        # for package in missing_packages:
            # subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        # print("✅ All packages installed")
    else:
        print("✅ All dependencies satisfied")

def detect_environment():
    """Detect the current hosting environment"""
    # Streamlit Community Cloud environment variables
    if (os.environ.get('STREAMLIT_SHARING') or 
        os.environ.get('STREAMLIT_CLOUD') or
        os.path.exists('/mount/src')):  # Streamlit Cloud mount path
        return 'streamlit_cloud'
    # Replit environment variables
    elif os.environ.get('REPLIT_DB_URL') or os.environ.get('REPL_SLUG'):
        return 'replit'
    else:
        return 'local'

def setup_database():
    """Setup database tables if they don't exist"""
    try:
        from database import DatabaseManager
        db_manager = DatabaseManager()
        print("✅ Database tables initialized")

        # Test database connection
        session = db_manager.get_session()
        session.close()
        print("🔗 Database connection verified")

    except Exception as e:
        print(f"⚠️ Database setup warning: {e}")
        print("🔄 Application will continue with fallback storage")

def main():
    """Main entry point for Replit - only runs on Replit"""
    env = detect_environment()

    if env == 'streamlit_cloud':
        print("🌐 Detected Streamlit Community Cloud environment")
        print("💡 Streamlit Cloud handles app startup automatically")
        print("💡 This script is designed for Replit hosting only")
        print("💡 Your app should start normally without this script")
        return

    print("🧠 MTF Psychophysics Experiment Platform (Replit)")
    print("=" * 50)

    # Setup Replit environment
    setup_replit_environment()

    # Check dependencies
    check_dependencies()

    # Import and run the main application
    try:
        print("🌐 Starting Streamlit server...")

        # Import here to ensure environment is set up first
        import streamlit.web.cli as stcli

        # Configure Streamlit for Replit
        sys.argv = [
            "streamlit",
            "run",
            "app.py",
            "--server.port=5000",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false"
        ]

        # Run Streamlit
        stcli.main()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()