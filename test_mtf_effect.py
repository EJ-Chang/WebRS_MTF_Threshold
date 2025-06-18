#!/usr/bin/env python3
"""
測試 MTF 處理效果是否明顯
"""

import numpy as np
import cv2
import os
from PIL import Image
import matplotlib.pyplot as plt

def test_mtf_effect():
    """測試不同MTF值的視覺效果"""
    
    # 檢查圖片檔案
    test_images = [
        "stimuli_preparation/stimuli_img.png",
        "stimuli_preparation/text_img.png",
        "stimuli_preparation/tw_newsimg.png",
        "stimuli_preparation/us_newsimg.png"
    ]
    
    print("=== MTF 效果測試 ===")
    
    for img_path in test_images:
        if not os.path.exists(img_path):
            print(f"❌ 圖片不存在: {img_path}")
            continue
            
        print(f"\n📸 測試圖片: {img_path}")
        
        # 載入圖片
        img_bgr = cv2.imread(img_path)
        if img_bgr is None:
            print(f"❌ 無法載入圖片: {img_path}")
            continue
            
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        print(f"✅ 圖片載入成功，尺寸: {img_rgb.shape}")
        
        # 裁切處理 (模擬實驗中的裁切)
        height, width = img_rgb.shape[:2]
        if 'stimuli_img' in img_path:
            # 取右半邊
            img_cropped = img_rgb[:, width//2:]
            print("📐 使用右半邊裁切")
        else:
            # 取中央部分
            target_width = width // 2
            center_x = width // 2
            start_x = center_x - target_width // 2
            end_x = start_x + target_width
            img_cropped = img_rgb[:, start_x:end_x]
            print("📐 使用中央裁切")
        
        print(f"📐 裁切後尺寸: {img_cropped.shape}")
        
        # 測試不同 MTF 值
        mtf_values = [10, 30, 50, 70, 90]
        
        for mtf in mtf_values:
            try:
                # 使用真正的MTF處理函數
                from experiments.mtf_utils import apply_mtf_to_image
                img_mtf = apply_mtf_to_image(img_cropped, mtf)
                print(f"✅ MTF {mtf}%: 處理成功")
                
                # 計算與原圖的差異
                diff = np.mean(np.abs(img_cropped.astype(float) - img_mtf.astype(float)))
                print(f"   與原圖差異: {diff:.2f}")
                
            except ImportError:
                print("⚠️ 使用 fallback MTF 處理")
                # Fallback MTF implementation
                sigma = (100 - mtf) / 20.0
                img_mtf = cv2.GaussianBlur(img_cropped, (0, 0), sigmaX=sigma, sigmaY=sigma)
                
                # 計算與原圖的差異
                diff = np.mean(np.abs(img_cropped.astype(float) - img_mtf.astype(float)))
                print(f"✅ MTF {mtf}% (fallback): 差異 {diff:.2f}")
                
            except Exception as e:
                print(f"❌ MTF {mtf}% 處理失敗: {e}")
        
        # 視覺化比較 (儲存到檔案)
        try:
            create_mtf_comparison(img_cropped, img_path)
        except Exception as e:
            print(f"⚠️ 視覺化失敗: {e}")

def create_mtf_comparison(img_cropped, img_path):
    """創建MTF效果比較圖"""
    
    # 創建比較圖
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(f'MTF Effect Comparison - {os.path.basename(img_path)}', fontsize=16)
    
    mtf_values = [90, 70, 50, 30, 10]
    
    # 原圖
    axes[0, 0].imshow(img_cropped)
    axes[0, 0].set_title('Original (100%)')
    axes[0, 0].axis('off')
    
    # 不同MTF值
    for i, mtf in enumerate(mtf_values):
        row = i // 3
        col = (i + 1) % 3
        
        try:
            from experiments.mtf_utils import apply_mtf_to_image
            img_mtf = apply_mtf_to_image(img_cropped, mtf)
        except ImportError:
            # Fallback
            sigma = (100 - mtf) / 20.0
            img_mtf = cv2.GaussianBlur(img_cropped, (0, 0), sigmaX=sigma, sigmaY=sigma)
        
        axes[row, col].imshow(img_mtf)
        axes[row, col].set_title(f'MTF {mtf}%')
        axes[row, col].axis('off')
    
    # 儲存比較圖
    output_path = f"results/mtf_comparison_{os.path.basename(img_path).replace('.png', '')}.png"
    os.makedirs("results", exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"💾 比較圖已儲存: {output_path}")

def test_sigma_calculation():
    """測試sigma計算是否合理"""
    print("\n=== Sigma 計算測試 ===")
    
    mtf_values = [10, 30, 50, 70, 90]
    
    print("MTF% → Sigma (fallback) → Sigma (真正公式)")
    for mtf in mtf_values:
        # Fallback計算
        sigma_fallback = (100 - mtf) / 20.0
        
        # 真正的MTF公式計算 (如果可用)
        try:
            from experiments.mtf_utils import apply_mtf_to_image
            # 無法直接取得sigma值，但可以觀察效果差異
            print(f"{mtf:2d}% → {sigma_fallback:4.1f} → (使用真正MTF公式)")
        except ImportError:
            print(f"{mtf:2d}% → {sigma_fallback:4.1f} → (fallback only)")

if __name__ == "__main__":
    test_sigma_calculation()
    test_mtf_effect()