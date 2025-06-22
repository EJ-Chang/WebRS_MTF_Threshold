#!/usr/bin/env python3
"""
Simple Streamlit runner for Replit deployment
Ensures proper server configuration and startup with signal handling
"""
import os
import sys
import subprocess
import signal

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    print(f"\n🛑 收到信號 {signum}，正在優雅地關閉...")
    sys.exit(0)

def main():
    """Run Streamlit with proper Replit configuration"""
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
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
    
    print("🌐 檢測到 Replit 環境，使用端口 5000")
    print("💡 提示：使用 Ctrl+C 可以正常終止程序")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 程序已被用戶中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 程序啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()