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
    
    # 檢查可用版本
    has_original = os.path.exists('app.py')
    has_new = os.path.exists('app_new.py')
    
    if not has_original and not has_new:
        print("❌ 錯誤: 找不到應用程式檔案")
        print("💡 請確認 app.py 或 app_new.py 存在")
        sys.exit(1)
    
    # 版本選擇
    app_file = 'app.py'  # 預設使用原版本
    
    if has_new and has_original:
        print("📋 發現多個版本，請選擇:")
        print("  1. 原版本 (app.py)")
        print("  2. 重構版本 (app_new.py) - 推薦")
        print("")
        
        while True:
            choice = input("請選擇 (1/2) [預設: 2]: ").strip()
            if choice == '' or choice == '2':
                app_file = 'app_new.py'
                print("✨ 選擇重構版本 - 模組化架構")
                break
            elif choice == '1':
                app_file = 'app.py'
                print("📝 選擇原版本")
                break
            else:
                print("❌ 無效選擇，請輸入 1 或 2")
    elif has_new:
        app_file = 'app_new.py'
        print("✨ 使用重構版本 (app_new.py)")
    else:
        print("📝 使用原版本 (app.py)")
    
    # 設定環境變數
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
    
    try:
        # 啟動 Streamlit 應用程式
        cmd = [sys.executable, '-m', 'streamlit', 'run', app_file, 
               '--server.port', '8501', 
               '--server.address', 'localhost']
        
        print(f"✅ 正在啟動應用程式 ({app_file})...")
        print("📝 提示: 使用 Ctrl+C 停止應用程式")
        print("")
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 應用程式已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 