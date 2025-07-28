#!/usr/bin/env python3
"""
簡單的HTTP服務器，用於測試圖片顯示
避免瀏覽器的本地文件限制
"""

import http.server
import socketserver
import os
import sys
import webbrowser
from pathlib import Path

# 服務器配置
PORT = 8000
HOST = 'localhost'

def start_server():
    """啟動HTTP服務器"""
    
    # 切換到image_test目錄
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    print("🚀 啟動圖片測試服務器...")
    print(f"📁 服務目錄: {script_dir}")
    print(f"🌐 服務地址: http://{HOST}:{PORT}")
    print(f"📊 測試頁面: http://{HOST}:{PORT}/index.html")
    print()
    
    # 檢查必要文件
    required_files = ['index.html', 'style.css']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        return False
    
    # 檢查圖片目錄
    images_dir = Path('images')
    if not images_dir.exists():
        print("❌ 找不到images目錄")
        return False
    
    # 列出可用的圖片
    image_files = list(images_dir.glob('*.png'))
    if not image_files:
        print("❌ images目錄中沒有PNG圖片")
        return False
    
    print("📸 可用的圖片:")
    for img in sorted(image_files):
        file_size = img.stat().st_size
        print(f"   • {img.name} ({file_size:,} bytes)")
    print()
    
    # 創建HTTP請求處理器
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            """自定義日誌格式"""
            print(f"📡 {self.address_string()} - {format % args}")
        
        def end_headers(self):
            """添加自定義響應頭"""
            # 禁用緩存，確保圖片總是最新的
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            
            # 支援跨域請求 (如果需要)
            self.send_header('Access-Control-Allow-Origin', '*')
            
            # 確保PNG圖片的正確MIME類型
            if self.path.endswith('.png'):
                self.send_header('Content-Type', 'image/png')
            
            super().end_headers()
    
    try:
        # 創建服務器
        with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✅ 服務器已啟動在 http://{HOST}:{PORT}")
            print("💡 提示:")
            print("   • 在瀏覽器中開啟上述地址來查看測試頁面")
            print("   • 使用 Ctrl+C 停止服務器")
            print("   • 可以嘗試不同的渲染模式和縮放選項")
            print("   • 比較與Mac Preview的顯示差異")
            print()
            
            # 自動開啟瀏覽器 (可選)
            try:
                webbrowser.open(f'http://{HOST}:{PORT}/index.html')
                print("🌐 已自動開啟瀏覽器")
            except Exception as e:
                print(f"⚠️ 無法自動開啟瀏覽器: {e}")
                print(f"   請手動開啟: http://{HOST}:{PORT}/index.html")
            
            print("\n" + "="*50)
            print("🔬 測試建議:")
            print("1. 切換不同的渲染模式 (pixelated vs auto)")
            print("2. 比較原始尺寸與縮放後的效果")
            print("3. 觀察圖片邊緣的銳利度")
            print("4. 記錄系統信息用於分析")
            print("5. 與Streamlit版本進行對比")
            print("="*50)
            print()
            
            # 啟動服務器主循環
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 服務器已停止")
        return True
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ 端口 {PORT} 已被占用")
            print(f"   請嘗試使用其他端口或關閉占用該端口的程序")
            return False
        else:
            print(f"❌ 服務器啟動失敗: {e}")
            return False
    except Exception as e:
        print(f"❌ 未預期的錯誤: {e}")
        return False

def check_environment():
    """檢查運行環境"""
    print("🔍 環境檢查:")
    print(f"   Python版本: {sys.version}")
    print(f"   操作系統: {os.name}")
    print(f"   當前目錄: {os.getcwd()}")
    print()

if __name__ == '__main__':
    print("🖼️  圖片顯示測試服務器")
    print("=" * 40)
    print()
    
    check_environment()
    
    # 如果有命令行參數指定端口
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
            print(f"📝 使用指定端口: {PORT}")
        except ValueError:
            print("❌ 無效的端口號，使用預設端口 8000")
    
    success = start_server()
    
    if success:
        print("\n✅ 測試完成")
    else:
        print("\n❌ 測試失敗")
        sys.exit(1)