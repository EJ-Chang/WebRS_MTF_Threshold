#!/usr/bin/env python3
"""
檢查刺激圖片的完整處理流程和尺寸變化
"""

import numpy as np
import cv2
import os
from PIL import Image
import sys

# 添加模組路徑
sys.path.append('.')
sys.path.append('./experiments')

try:
    from experiments.mtf_utils import apply_mtf_to_image, load_and_prepare_image
    MTF_UTILS_AVAILABLE = True
    print("✅ MTF utilities loaded successfully")
except ImportError as e:
    print(f"⚠️ MTF utilities not available: {e}")
    MTF_UTILS_AVAILABLE = False

def check_original_image():
    """檢查原始圖片尺寸"""
    img_path = "stimuli_preparation/stimuli_img.png"
    
    if not os.path.exists(img_path):
        print(f"❌ 圖片不存在: {img_path}")
        return None
    
    # 使用OpenCV讀取
    img_cv = cv2.imread(img_path)
    if img_cv is None:
        print(f"❌ 無法讀取圖片: {img_path}")
        return None
    
    # 使用PIL讀取
    img_pil = Image.open(img_path)
    
    print("🖼️ 原始圖片資訊:")
    print(f"  OpenCV 格式: {img_cv.shape} (H, W, C)")
    print(f"  PIL 格式: {img_pil.size} (W, H)")
    print(f"  檔案大小: {os.path.getsize(img_path)} bytes")
    print(f"  色彩模式: {img_pil.mode}")
    
    return {
        'opencv_shape': img_cv.shape,
        'pil_size': img_pil.size,
        'opencv_image': img_cv,
        'pil_image': img_pil
    }

def check_right_half_crop(original_data):
    """檢查取右半邊後的尺寸"""
    if not original_data:
        return None
    
    img_cv = original_data['opencv_image']
    
    # 模擬 load_and_prepare_image 的右半邊裁切
    h, w, c = img_cv.shape
    mid_point = w // 2
    right_half = img_cv[:, mid_point:]  # 取右半邊
    
    print("✂️ 裁切右半邊後:")
    print(f"  原始尺寸: {img_cv.shape}")
    print(f"  中點位置: {mid_point}")
    print(f"  右半邊尺寸: {right_half.shape}")
    print(f"  寬度縮減: {w} → {right_half.shape[1]} ({right_half.shape[1]/w*100:.1f}%)")
    
    return {
        'shape': right_half.shape,
        'image': right_half,
        'reduction_ratio': right_half.shape[1] / w
    }

def check_mtf_application(cropped_data, mtf_value=50.0):
    """檢查MTF濾鏡應用後的尺寸"""
    if not cropped_data:
        return None
    
    img = cropped_data['image']
    
    if MTF_UTILS_AVAILABLE:
        # 使用真實的MTF函數
        try:
            mtf_img = apply_mtf_to_image(img, mtf_value)
            print(f"🎛️ MTF濾鏡應用 (MTF={mtf_value}%):")
            print(f"  處理前: {img.shape}")
            print(f"  處理後: {mtf_img.shape}")
            
            if img.shape == mtf_img.shape:
                print("  ✅ MTF處理保持原始尺寸")
            else:
                print("  ⚠️ MTF處理改變了圖片尺寸")
            
            return {
                'shape': mtf_img.shape,
                'image': mtf_img,
                'size_changed': img.shape != mtf_img.shape
            }
        except Exception as e:
            print(f"  ❌ MTF處理失敗: {e}")
            return None
    else:
        # 使用fallback實現
        sigma = (100 - mtf_value) / 20.0
        mtf_img = cv2.GaussianBlur(img, (0, 0), sigmaX=sigma, sigmaY=sigma)
        
        print(f"🎛️ MTF濾鏡應用 (Fallback, MTF={mtf_value}%):")
        print(f"  Sigma值: {sigma}")
        print(f"  處理前: {img.shape}")
        print(f"  處理後: {mtf_img.shape}")
        
        return {
            'shape': mtf_img.shape,
            'image': mtf_img,
            'size_changed': img.shape != mtf_img.shape
        }

def check_web_display_processing(mtf_data):
    """檢查網頁顯示時的處理"""
    if not mtf_data:
        return None
    
    img = mtf_data['image']
    h, w = img.shape[:2]
    
    print("🌐 網頁顯示處理:")
    print(f"  MTF處理後尺寸: {img.shape}")
    print(f"  新策略: 移除強制裁切，保持原始像素尺寸")
    print(f"  CSS控制: max-width: 100%, max-height: 80vh, object-fit: contain")
    print(f"  最終像素尺寸: {img.shape} (保持不變)")
    print(f"  長寬比: {w/h:.3f} (保持不變)")
    
    # 新邏輯：不進行像素級裁切，保持原始尺寸
    processed_img = img
    
    print(f"  ✅ 像素尺寸保持不變")
    print(f"  ✅ 長寬比由CSS保護")
    print(f"  📏 瀏覽器將根據容器大小自動縮放")
    
    return {
        'shape': processed_img.shape,
        'image': processed_img,
        'was_cropped': False,
        'aspect_ratio_preserved': True
    }

def analyze_aspect_ratio_preservation():
    """分析長寬比保持情況"""
    print("\n📐 長寬比分析:")
    
    # 檢查完整流程
    original = check_original_image()
    if not original:
        return
    
    cropped = check_right_half_crop(original)
    if not cropped:
        return
    
    mtf_applied = check_mtf_application(cropped, 50.0)
    if not mtf_applied:
        return
    
    web_processed = check_web_display_processing(mtf_applied)
    if not web_processed:
        return
    
    # 計算各階段的長寬比
    original_h, original_w = original['opencv_shape'][:2]
    original_ratio = original_w / original_h
    
    cropped_h, cropped_w = cropped['shape'][:2]
    cropped_ratio = cropped_w / cropped_h
    
    mtf_h, mtf_w = mtf_applied['shape'][:2]
    mtf_ratio = mtf_w / mtf_h
    
    web_h, web_w = web_processed['shape'][:2]
    web_ratio = web_w / web_h
    
    print(f"  原始圖片: {original_w}x{original_h}, 比例 {original_ratio:.3f}")
    print(f"  右半邊後: {cropped_w}x{cropped_h}, 比例 {cropped_ratio:.3f}")
    print(f"  MTF處理後: {mtf_w}x{mtf_h}, 比例 {mtf_ratio:.3f}")
    print(f"  網頁處理後: {web_w}x{web_h}, 比例 {web_ratio:.3f}")
    
    # 檢查比例變化
    print("\n📊 比例變化分析:")
    print(f"  裁切階段變化: {original_ratio:.3f} → {cropped_ratio:.3f} (差異: {abs(original_ratio-cropped_ratio):.3f})")
    print(f"  MTF階段變化: {cropped_ratio:.3f} → {mtf_ratio:.3f} (差異: {abs(cropped_ratio-mtf_ratio):.3f})")
    print(f"  網頁階段變化: {mtf_ratio:.3f} → {web_ratio:.3f} (差異: {abs(mtf_ratio-web_ratio):.3f})")
    
    # 檢查是否保持比例
    tolerance = 0.001
    if abs(cropped_ratio - mtf_ratio) < tolerance and abs(mtf_ratio - web_ratio) < tolerance:
        print("  ✅ 長寬比在處理過程中保持一致")
    else:
        print("  ⚠️ 長寬比在處理過程中有變化")

def check_css_scaling_impact():
    """檢查CSS縮放對圖片的影響"""
    print("\n🎨 CSS縮放影響分析:")
    
    # 模擬display_fullscreen_image中的CSS設定
    css_style = """
    max-width: 100%; 
    width: auto; 
    height: auto; 
    object-fit: contain;
    """
    
    print("  當前CSS設定:")
    print(f"    max-width: 100%")
    print(f"    width: auto")
    print(f"    height: auto") 
    print(f"    object-fit: contain")
    
    print("\n  CSS行為分析:")
    print("    ✅ max-width: 100% - 限制圖片不超過容器寬度")
    print("    ✅ width/height: auto - 保持原始長寬比")
    print("    ✅ object-fit: contain - 確保整張圖片都顯示")
    
    print("\n  🎯 建議優化:")
    print("    1. 當前設定已經能保持長寬比")
    print("    2. 如需固定尺寸，建議設定具體的width和height")
    print("    3. 可考慮用CSS transform: scale()來控制大小")

if __name__ == "__main__":
    print("🔍 MTF刺激圖片尺寸檢查報告")
    print("=" * 50)
    
    analyze_aspect_ratio_preservation()
    check_css_scaling_impact()
    
    print("\n" + "=" * 50)
    print("✅ 檢查完成")