#!/usr/bin/env python3
"""
Simple Streamlit runner for Replit deployment
Ensures proper server configuration and startup
"""
import os
import sys
import subprocess

def main():
    """Run Streamlit with proper Replit configuration"""
    
    # Set environment variables for Replit
    os.environ['STREAMLIT_SERVER_PORT'] = '5000'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # Start Streamlit directly
    cmd = [
        sys.executable, 
        '-m',
        'streamlit',
        'run',
        'app.py',
        '--server.port=5000',
        '--server.address=0.0.0.0',
        '--server.headless=true',
        '--browser.gatherUsageStats=false',
        '--server.enableCORS=false',
        '--server.enableXsrfProtection=false'
    ]
    
    print("Starting Streamlit server for Replit...")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()