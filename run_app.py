#!/usr/bin/env python3
"""
Streamlit 應用程式啟動腳本
自動設定端口為 8501 並啟動應用程式
"""

import os
import sys
import subprocess
import time

def main():
    print("🚀 啟動 Psychophysics 實驗應用程式...")
    print("📍 端口: 8501")
    print("🌐 網址: http://localhost:8501")
    print("")
    
    # 設定環境變數
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
    
    # 檢查 app.py 是否存在
    if not os.path.exists('app.py'):
        print("❌ 錯誤: 找不到 app.py 檔案")
        sys.exit(1)
    
    try:
        # 啟動 Streamlit 應用程式
        cmd = [sys.executable, '-m', 'streamlit', 'run', 'app.py', 
               '--server.port', '8501', 
               '--server.address', 'localhost']
        
        print("✅ 正在啟動應用程式...")
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 應用程式已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 