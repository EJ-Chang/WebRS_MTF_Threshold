#!/usr/bin/env python3
"""
簡化版圖片修復腳本 - 無需額外依賴
"""

import os
import sys
from pathlib import Path

def analyze_images():
    """分析圖片並給出建議"""
    print("🔍 圖片模糊問題分析")
    print("=" * 40)
    
    images_dir = Path("images")
    if not images_dir.exists():
        print("❌ 找不到 images 目錄")
        return
    
    png_files = list(images_dir.glob("*.png"))
    
    if not png_files:
        print("❌ 沒有找到PNG圖片")
        return
    
    print(f"📸 分析 {len(png_files)} 張圖片:")
    print()
    
    for img_path in png_files:
        # 使用系統命令分析
        print(f"📷 {img_path.name}:")
        
        # 獲取文件信息
        size = img_path.stat().st_size
        print(f"   文件大小: {size:,} bytes")
        
        # 使用file命令獲取圖片信息
        import subprocess
        try:
            result = subprocess.run(['file', str(img_path)], capture_output=True, text=True)
            info = result.stdout.strip()
            print(f"   圖片信息: {info.split(':', 1)[1].strip()}")
            
            # 提取解析度信息
            if "x" in info:
                parts = info.split()
                for i, part in enumerate(parts):
                    if "x" in part and part.replace("x", "").replace(",", "").isdigit():
                        dimensions = part.rstrip(',')
                        print(f"   解析度: {dimensions}")
                        
                        # 判斷是否為高解析度
                        width, height = map(int, dimensions.split('x'))
                        if width >= 3840 or height >= 2160:
                            print(f"   🔍 檢測到4K解析度 - 可能需要縮放")
                        elif width >= 1920 or height >= 1080:
                            print(f"   📺 Full HD解析度")
                        break
        except Exception as e:
            print(f"   ❌ 無法分析: {e}")
        
        print()
    
    print("🔬 問題診斷:")
    print("1. 您的圖片有不同的解析度:")
    print("   • 1920×1080 (Full HD)")
    print("   • 3840×2160 (4K)")
    print()
    print("2. 在Retina顯示器上，瀏覽器會對不同解析度進行不同的縮放處理")
    print("3. 這種縮放可能使用了內插算法，導致圖片模糊")
    print()
    
    print("💡 解決方案建議:")
    print("1. 【立即測試】打開 debug.html 查看不同渲染模式的效果")
    print("2. 【CSS修復】使用 image-rendering: pixelated 強制像素完美渲染")
    print("3. 【Canvas渲染】使用Canvas API繞過瀏覽器的圖片縮放")
    print("4. 【統一解析度】將所有圖片調整為相同解析度")
    print()
    
    print("🚀 測試步驟:")
    print("1. 啟動服務器: python3 simple_server.py")
    print("2. 開啟診斷頁面: http://localhost:8000/debug.html")
    print("3. 比較不同渲染模式的清晰度")
    print("4. 檢查Canvas版本是否更清晰")

def create_test_html():
    """創建簡單的測試頁面"""
    print("\n🛠️ 創建額外測試頁面...")
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Canvas vs IMG 測試</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .test { margin: 20px 0; padding: 20px; border: 2px solid #ccc; }
        .test h3 { color: #007acc; }
        img, canvas { border: 1px solid #999; margin: 10px; }
        .pixelated { image-rendering: pixelated; image-rendering: -moz-crisp-edges; image-rendering: crisp-edges; }
    </style>
</head>
<body>
    <h1>🔬 Canvas vs IMG 渲染測試</h1>
    
    <div class="test">
        <h3>1. IMG標籤 - 預設渲染</h3>
        <img src="images/stimuli_img.png" width="400" height="225" alt="預設">
    </div>
    
    <div class="test">
        <h3>2. IMG標籤 - 像素完美</h3>
        <img src="images/stimuli_img.png" width="400" height="225" class="pixelated" alt="像素完美">
    </div>
    
    <div class="test">
        <h3>3. Canvas渲染 - 關閉圖片平滑</h3>
        <canvas id="canvas1" width="400" height="225"></canvas>
        <script>
            const canvas = document.getElementById('canvas1');
            const ctx = canvas.getContext('2d');
            
            // 關閉所有圖片平滑
            ctx.imageSmoothingEnabled = false;
            ctx.webkitImageSmoothingEnabled = false;
            ctx.mozImageSmoothingEnabled = false;
            ctx.msImageSmoothingEnabled = false;
            
            const img = new Image();
            img.onload = function() {
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            };
            img.src = 'images/stimuli_img.png';
        </script>
    </div>
    
    <div class="test">
        <h3>4. 結論</h3>
        <p>比較以上三種渲染方式：</p>
        <ul>
            <li><strong>如果Canvas版本最清晰</strong> → 問題出在瀏覽器的IMG縮放</li>
            <li><strong>如果像素完美版本最清晰</strong> → CSS可以解決問題</li>
            <li><strong>如果都很模糊</strong> → 可能需要調整圖片本身</li>
        </ul>
    </div>
</body>
</html>'''
    
    with open('canvas_test.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ 已創建 canvas_test.html")
    print("   這個頁面專門測試Canvas vs IMG的差異")

if __name__ == '__main__':
    analyze_images()
    create_test_html()
    
    print("\n" + "="*50)
    print("🎯 下一步操作:")
    print("1. python3 simple_server.py")
    print("2. 瀏覽器開啟:")
    print("   • http://localhost:8000/debug.html (詳細診斷)")
    print("   • http://localhost:8000/canvas_test.html (Canvas測試)")
    print("3. 比較不同渲染方式的清晰度")
    print("="*50)