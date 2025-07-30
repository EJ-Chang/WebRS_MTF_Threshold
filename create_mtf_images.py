#!/usr/bin/env python3
"""
創建不同 MTF 值的圖片處理腳本
使用 us_newsimg.png 作為源圖片，生成 MTF=10% 和 MTF=50% 的處理結果
"""

import cv2
import numpy as np
import os
import sys

def mtf_to_sigma(mtf_percent, frequency_lpmm, pixel_size_mm):
    """計算對應 MTF 的 sigma 值"""
    mtf_ratio = mtf_percent / 100.0
    if mtf_ratio <= 0 or mtf_ratio >= 1:
        raise ValueError(f"MTF ratio ({mtf_percent}) must be between 0 and 100 (exclusive)")
    
    f = frequency_lpmm
    sigma_mm = np.sqrt(-np.log(mtf_ratio) / (2 * (np.pi * f) ** 2))
    sigma_pixels = sigma_mm / pixel_size_mm
    return sigma_pixels

def apply_mtf_to_image(image, mtf_percent, frequency_lpmm=44.25, pixel_size_mm=0.169333):
    """對圖片套用 MTF 模糊效果"""
    
    # 輸入驗證
    if not isinstance(image, np.ndarray):
        raise TypeError("輸入必須是 numpy 陣列")
    
    if len(image.shape) != 3 or image.shape[2] != 3:
        raise ValueError("輸入圖片必須是 RGB 格式 (高度, 寬度, 3)")
    
    if not (0 < mtf_percent < 100):
        raise ValueError(f"MTF 百分比 ({mtf_percent}) 必須介於 0~100 之間 (不含邊界值)")
    
    # 計算 sigma 值
    sigma_pixels = mtf_to_sigma(mtf_percent, frequency_lpmm, pixel_size_mm)
    
    print(f"🔬 MTF調試信息:")
    print(f"   MTF輸入: {mtf_percent}% -> ratio: {mtf_percent/100.0:.4f}")
    print(f"   頻率: {frequency_lpmm} 線對/毫米")
    print(f"   像素大小: {pixel_size_mm:.6f} 毫米")
    print(f"   計算得出 sigma_pixels: {sigma_pixels:.2f} 像素")
    
    # 套用高斯模糊
    img_blurred = cv2.GaussianBlur(
        image, 
        (0, 0), 
        sigmaX=sigma_pixels, 
        sigmaY=sigma_pixels,
        borderType=cv2.BORDER_REFLECT
    )
    
    print(f"✅ 已套用高斯模糊 sigma={sigma_pixels:.2f} 像素")
    return img_blurred

def load_and_prepare_image(image_path, use_right_half=True):
    """載入並準備圖片"""
    
    # 載入圖片
    img_bgr = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img_bgr is None:
        raise FileNotFoundError(f"找不到圖片檔案：{image_path}")
    
    # 轉換為 RGB 格式
    if len(img_bgr.shape) == 3:
        if img_bgr.shape[2] == 4:  # BGRA
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGRA2RGB)
        else:  # BGR
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    else:
        raise ValueError("不支援的圖片格式")
    
    if use_right_half:
        # 檢查是否為文字圖片
        image_name = os.path.basename(image_path).lower()
        
        if 'stimuli_img' in image_name:
            # 原始stimuli_img：取右半邊
            width = img_rgb.shape[1]
            mid_point = width // 2
            img_rgb = img_rgb[:, mid_point:]
            print(f"stimuli_img裁切：從 {width} 取右半邊，結果寬度 {img_rgb.shape[1]}")
        else:
            # 其他圖片：取中央部分
            height, width = img_rgb.shape[:2]
            target_width = width // 2  # 目標寬度為原圖的一半
            
            # 計算中央區域的起始和結束位置
            center_x = width // 2
            start_x = center_x - target_width // 2
            end_x = start_x + target_width
            
            # 確保不超出圖片邊界
            start_x = max(0, start_x)
            end_x = min(width, end_x)
            
            img_rgb = img_rgb[:, start_x:end_x]
            print(f"{image_name}裁切：從 {width}x{height} 裁切中央部分到 {img_rgb.shape[1]}x{img_rgb.shape[0]}")
    
    return img_rgb

def main():
    """主程式"""
    
    # ===== 參數設定 =====
    name = "us_newsimg"
    image_path = 'stimuli_preparation/us_newsimg.png'
    output_dir = 'stimuli_preparation/mtf_output'
    
    # 顯示器規格設定 (與 [OE] MTF_test_v0.3.py 相同)
    panel_size = 27     # inch
    panel_resolution_H = 3840     # 水平
    panel_resolution_V = 2160     # 垂直
    panel_resolution_D = (panel_resolution_H**2 + panel_resolution_V**2)**0.5     # 對角
    pixel_size_mm = (panel_size * 25.4) / panel_resolution_D     # 像素大小 (mm)
    frequency_lpmm = round(panel_resolution_D / (panel_size * 25.4) * 0.5 * 0.6, 2)     # 空間頻率
    
    print(f'載入圖片: {image_path}')
    print(f'顯示器參數:')
    print(f'  面板大小: {panel_size}" ({panel_resolution_H}×{panel_resolution_V})')
    print(f'  對角解析度: {panel_resolution_D:.2f} pixels')
    print(f'  像素大小: {pixel_size_mm:.6f} mm')
    print(f'  空間頻率: {frequency_lpmm} lp/mm')
    
    try:
        # 載入並準備圖片
        img = load_and_prepare_image(image_path, use_right_half=True)
        print(f'圖片尺寸: {img.shape}')
        
        # 創建輸出目錄
        os.makedirs(output_dir, exist_ok=True)
        
        # 創建 MTF=10% 的圖片
        print('\n處理 MTF=10%...')
        img_mtf_10 = apply_mtf_to_image(img, 10.0, frequency_lpmm, pixel_size_mm)
        
        # 創建 MTF=50% 的圖片
        print('\n處理 MTF=50%...')
        img_mtf_50 = apply_mtf_to_image(img, 50.0, frequency_lpmm, pixel_size_mm)
        
        # 儲存圖片（轉換回 BGR 格式）
        output_path_10 = f'{output_dir}/{name}_MTF_10.png'
        output_path_50 = f'{output_dir}/{name}_MTF_50.png'
        
        cv2.imwrite(output_path_10, cv2.cvtColor(img_mtf_10, cv2.COLOR_RGB2BGR))
        cv2.imwrite(output_path_50, cv2.cvtColor(img_mtf_50, cv2.COLOR_RGB2BGR))
        
        print(f'\n✅ 成功儲存兩張 MTF 處理圖片:')
        print(f'   - {output_path_10} (MTF=10%)')
        print(f'   - {output_path_50} (MTF=50%)')
        
        # 顯示檔案大小
        size_10 = os.path.getsize(output_path_10) / 1024
        size_50 = os.path.getsize(output_path_50) / 1024
        print(f'\n檔案大小:')
        print(f'   - MTF 10%: {size_10:.1f} KB')
        print(f'   - MTF 50%: {size_50:.1f} KB')
        
    except Exception as e:
        print(f'❌ 錯誤: {e}')
        sys.exit(1)

if __name__ == "__main__":
    main()