#!/usr/bin/env python3
"""
修復瀏覽器圖片模糊問題的解決方案
"""

import sys
import os
from pathlib import Path
import numpy as np

# 添加主項目路徑以導入OpenCV和PIL
sys.path.append(str(Path(__file__).parent.parent))

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    OPENCV_AVAILABLE = True
    PIL_AVAILABLE = True
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    print("這個腳本需要OpenCV和PIL庫")
    OPENCV_AVAILABLE = False
    PIL_AVAILABLE = False

def analyze_image_properties(image_path):
    """分析圖片屬性"""
    print(f"\n🔍 分析圖片: {os.path.basename(image_path)}")
    
    if not PIL_AVAILABLE:
        print("❌ PIL不可用，跳過分析")
        return None
    
    try:
        with Image.open(image_path) as img:
            info = {
                'size': img.size,
                'mode': img.mode,
                'format': img.format,
                'dpi': img.info.get('dpi', None),
                'file_size': os.path.getsize(image_path)
            }
            
            print(f"   尺寸: {info['size']} pixels")
            print(f"   色彩模式: {info['mode']}")
            print(f"   DPI: {info['dpi'] if info['dpi'] else '未設定'}")
            print(f"   文件大小: {info['file_size']:,} bytes")
            
            return info
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        return None

def create_pixel_perfect_version(input_path, output_path, target_dpi=144):
    """創建像素完美版本的圖片"""
    print(f"\n🛠️ 創建像素完美版本: {os.path.basename(input_path)}")
    
    if not PIL_AVAILABLE:
        print("❌ PIL不可用，無法處理")
        return False
    
    try:
        with Image.open(input_path) as img:
            # 確保圖片是RGB模式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 設定高DPI，讓瀏覽器知道這是高品質圖片
            img.save(output_path, 'PNG', dpi=(target_dpi, target_dpi), optimize=False)
            
            print(f"✅ 已儲存到: {output_path}")
            print(f"   設定DPI: {target_dpi}")
            
            return True
    except Exception as e:
        print(f"❌ 處理失敗: {e}")
        return False

def create_canvas_friendly_version(input_path, output_path):
    """創建適合Canvas渲染的版本"""
    print(f"\n🎨 創建Canvas友好版本: {os.path.basename(input_path)}")
    
    if not OPENCV_AVAILABLE:
        print("❌ OpenCV不可用，無法處理")
        return False
    
    try:
        # 使用OpenCV讀取，保持像素精確性
        img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"❌ 無法讀取圖片: {input_path}")
            return False
        
        # 如果是BGRA，轉換為RGB
        if len(img.shape) == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        elif len(img.shape) == 3 and img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 轉換為PIL圖片以保存
        pil_img = Image.fromarray(img)
        
        # 保存時使用無壓縮設定
        pil_img.save(output_path, 'PNG', compress_level=0, optimize=False)
        
        print(f"✅ 已儲存Canvas版本到: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ 處理失敗: {e}")
        return False

def create_test_pattern():
    """創建測試圖案來驗證渲染品質"""
    print(f"\n🎯 創建測試圖案")
    
    if not PIL_AVAILABLE:
        print("❌ PIL不可用，無法創建測試圖案")
        return False
    
    try:
        # 創建測試圖案 (1920x1080)
        width, height = 1920, 1080
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # 繪製棋盤格圖案
        square_size = 20
        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                if (x // square_size + y // square_size) % 2 == 0:
                    draw.rectangle([x, y, x + square_size, y + square_size], fill='black')
        
        # 添加1像素線條測試
        for i in range(0, width, 100):
            draw.line([i, 0, i, height], fill='red', width=1)
        for i in range(0, height, 100):
            draw.line([0, i, width, i], fill='green', width=1)
        
        # 添加文字測試
        try:
            # 嘗試使用系統字體
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 50), "像素完美測試圖案", fill='blue', font=font)
        draw.text((50, 100), "Pixel Perfect Test Pattern", fill='blue', font=font)
        draw.text((50, 150), f"尺寸: {width}×{height}", fill='blue', font=font)
        
        # 保存測試圖案
        test_path = "images/pixel_perfect_test.png"
        img.save(test_path, 'PNG', dpi=(144, 144), optimize=False)
        
        print(f"✅ 測試圖案已保存到: {test_path}")
        return True
        
    except Exception as e:
        print(f"❌ 創建測試圖案失敗: {e}")
        return False

def main():
    print("🔧 圖片模糊問題修復工具")
    print("=" * 40)
    
    # 檢查images目錄
    images_dir = Path("images")
    if not images_dir.exists():
        print("❌ 找不到 images 目錄")
        return
    
    # 創建修復版本目錄
    fixed_dir = images_dir / "fixed"
    fixed_dir.mkdir(exist_ok=True)
    
    canvas_dir = images_dir / "canvas"
    canvas_dir.mkdir(exist_ok=True)
    
    # 處理所有PNG圖片
    png_files = list(images_dir.glob("*.png"))
    
    if not png_files:
        print("❌ 沒有找到PNG圖片")
        return
    
    print(f"📸 找到 {len(png_files)} 張圖片")
    
    for img_path in png_files:
        # 分析原始圖片
        analyze_image_properties(img_path)
        
        # 創建像素完美版本
        fixed_path = fixed_dir / img_path.name
        create_pixel_perfect_version(img_path, fixed_path)
        
        # 創建Canvas友好版本
        canvas_path = canvas_dir / img_path.name
        create_canvas_friendly_version(img_path, canvas_path)
    
    # 創建測試圖案
    create_test_pattern()
    
    print(f"\n✅ 處理完成！")
    print(f"📁 修復版本保存在: {fixed_dir}")
    print(f"📁 Canvas版本保存在: {canvas_dir}")
    print(f"💡 建議:")
    print(f"   1. 在debug.html中測試不同版本")
    print(f"   2. 比較渲染品質差異")
    print(f"   3. 選擇最適合的版本用於實驗")

if __name__ == '__main__':
    main()