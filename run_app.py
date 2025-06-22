#!/usr/bin/env python3
"""
Streamlit 應用程式啟動腳本 - 重構版本
自動設定端口為 8501 並啟動新版應用程式
"""

import os
import sys
import subprocess
import time

def main():
    print("🚀 啟動 Psychophysics 實驗應用程式 - 重構版本")
    print("📍 端口: 8501")
    print("🌐 網址: http://localhost:8501")
    print("✨ 使用模組化架構 (app.py)")
    print("")
    
    # 設定環境變數
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
    
    # 檢查 app.py 是否存在
    if not os.path.exists('app.py'):
        print("❌ 錯誤: 找不到 app.py 檔案")
        print("💡 請確認您在正確的專案目錄中")
        sys.exit(1)
    
    # 檢查必要的模組目錄
    required_dirs = ['config', 'core', 'ui', 'utils']
    missing_dirs = []
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"❌ 錯誤: 缺少必要的模組目錄: {', '.join(missing_dirs)}")
        print("💡 請確認重構後的檔案結構完整")
        sys.exit(1)
    
    try:
        # 啟動 Streamlit 應用程式
        cmd = [sys.executable, '-m', 'streamlit', 'run', 'app.py', 
               '--server.port', '8501', 
               '--server.address', 'localhost']
        
        print("✅ 正在啟動應用程式...")
        print("📝 提示: 使用 Ctrl+C 停止應用程式")
        print("")
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 應用程式已停止")
    except FileNotFoundError:
        print("❌ 錯誤: 找不到 streamlit 命令")
        print("💡 請確認已安裝 streamlit: pip install streamlit")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()