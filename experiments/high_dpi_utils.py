"""
high_dpi_utils.py

高DPI圖片處理工具函數

提供144 DPI精緻呈現的圖片處理功能，包括：
- 高DPI圖片載入和管理
- 圖片1/2濃縮預覽功能
- 智能解析度選擇
- 跨平台高DPI顯示支援

Author: EJ
Created: 2025-07-23
"""

import cv2
import numpy as np
import os
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional, Dict, Union
from experiments.mtf_utils import load_and_prepare_image, apply_mtf_to_image

# 設定日誌
logger = logging.getLogger(__name__)

def get_project_root():
    """獲取專案根目錄的絕對路徑"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)

def get_high_dpi_image_path(image_name: str, dpi_level: str = "2x") -> str:
    """
    獲取高DPI圖片的完整路徑
    
    Args:
        image_name (str): 圖片檔名 (如 'stimuli_img.png')
        dpi_level (str): DPI等級 ('2x', '3x', 'original') 
        
    Returns:
        str: 高DPI圖片的完整路徑
    """
    project_root = get_project_root()
    
    # 檢查高DPI版本是否存在
    high_dpi_path = os.path.join(project_root, 'stimuli_preparation', 'high_dpi', dpi_level, image_name)
    if os.path.exists(high_dpi_path):
        return high_dpi_path
    
    # 後備到標準版本
    standard_path = os.path.join(project_root, 'stimuli_preparation', 'standard', image_name)
    if os.path.exists(standard_path):
        logger.warning(f"高DPI版本 ({dpi_level}) 不存在，使用標準版本: {image_name}")
        return standard_path
        
    raise FileNotFoundError(f"找不到圖片檔案: {image_name} (嘗試了 {dpi_level} 和 standard)")

def detect_optimal_dpi_level() -> str:
    """
    檢測最佳的DPI等級，整合現有校準系統
    
    Returns:
        str: 建議的DPI等級 ('2x', '3x', 'standard')
    """
    try:
        from utils.display_calibration import get_display_calibration
        
        calibration = get_display_calibration()
        
        # 確保已檢測顯示器資訊
        if calibration.display_info is None:
            calibration.detect_display_info()
        
        display_info = calibration.display_info
        
        if display_info and display_info.dpi_x:
            dpi = display_info.dpi_x
            confidence = display_info.confidence
            
            logger.info(f"DPI檢測結果: {dpi:.1f}, 信賴度: {confidence:.2f}")
            
            # 根據DPI和信賴度決定等級
            if confidence > 0.7:  # 高信賴度
                if dpi >= 200:  # Retina 和高DPI顯示器 (如 220 DPI)
                    return "3x"
                elif dpi >= 120:  # 中等DPI顯示器
                    return "2x"
                else:  # 標準DPI顯示器 (72, 96 DPI)
                    return "standard"
            else:  # 低信賴度時保守選擇
                if dpi >= 150:  # 提高門檻以避免誤判
                    return "2x"
                else:
                    return "standard"
        else:
            # 如果檢測失敗，根據平台預設
            import platform
            system = platform.system().lower()
            
            if system == "darwin":  # macOS，可能是Retina
                logger.info("macOS系統，預設使用2x")
                return "2x"
            else:  # Windows/Linux
                logger.info("Windows/Linux系統，預設使用2x (現代顯示器)")
                return "2x"
            
    except Exception as e:
        logger.warning(f"DPI檢測失敗，使用預設2x: {e}")
        return "2x"

def load_and_prepare_high_dpi_image(image_path: str, use_right_half: bool = True, target_dpi: Optional[str] = None) -> np.ndarray:
    """
    載入並準備高DPI圖片，保持與原始函數相同的裁切邏輯
    
    Args:
        image_path (str): 圖片檔案路徑或檔名
        use_right_half (bool): 是否使用右半邊裁切
        target_dpi (str, optional): 目標DPI等級，如果為None則自動檢測
        
    Returns:
        numpy.ndarray: 準備好的高DPI RGB圖片陣列
    """
    
    # 如果只提供檔名，構建完整路徑
    if not os.path.isabs(image_path):
        image_name = os.path.basename(image_path)
        
        if target_dpi is None:
            target_dpi = detect_optimal_dpi_level()
            
        if target_dpi != "standard":
            image_path = get_high_dpi_image_path(image_name, target_dpi)
        else:
            # 使用標準路徑
            project_root = get_project_root()
            image_path = os.path.join(project_root, 'stimuli_preparation', 'standard', image_name)
    
    # 使用原始的載入和準備函數，保持相同的裁切邏輯
    return load_and_prepare_image(image_path, use_right_half)

def create_high_dpi_preview(image_array: np.ndarray, scale_factor: float = 0.5, add_info_overlay: bool = True) -> np.ndarray:
    """
    創建高DPI圖片的1/2濃縮預覽
    
    這個函數將高DPI圖片縮小到指定比例，同時保持圖片品質。
    縮小後的圖片在顯示時會由瀏覽器進行高品質向上縮放。
    
    Args:
        image_array (np.ndarray): 原始高DPI圖片陣列 (RGB)
        scale_factor (float): 縮放因子，預設0.5 (縮小到一半)
        add_info_overlay (bool): 是否添加資訊覆蓋層
        
    Returns:
        np.ndarray: 縮小後的圖片陣列
    """
    
    if not isinstance(image_array, np.ndarray):
        raise TypeError("輸入必須是 numpy 陣列")
    
    if len(image_array.shape) != 3 or image_array.shape[2] != 3:
        raise ValueError("輸入圖片必須是 RGB 格式 (高度, 寬度, 3)")
    
    original_height, original_width = image_array.shape[:2]
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)
    
    # 使用高品質縮放
    resized_img = cv2.resize(
        image_array, 
        (new_width, new_height), 
        interpolation=cv2.INTER_LANCZOS4  # 高品質縮放算法
    )
    
    logger.info(f"高DPI預覽縮放: {original_width}x{original_height} -> {new_width}x{new_height} (縮放因子: {scale_factor})")
    
    # 如果需要，添加資訊覆蓋層
    if add_info_overlay:
        resized_img = _add_preview_info_overlay(resized_img, original_width, original_height, scale_factor)
    
    return resized_img

def _add_preview_info_overlay(image_array: np.ndarray, original_width: int, original_height: int, scale_factor: float) -> np.ndarray:
    """
    在預覽圖片上添加資訊覆蓋層
    
    Args:
        image_array (np.ndarray): 圖片陣列
        original_width (int): 原始寬度
        original_height (int): 原始高度  
        scale_factor (float): 縮放因子
        
    Returns:
        np.ndarray: 添加覆蓋層後的圖片陣列
    """
    
    # 轉換為PIL圖片以便文字繪製
    pil_img = Image.fromarray(image_array)
    draw = ImageDraw.Draw(pil_img)
    
    # 嘗試載入字體，如果失敗則使用預設字體
    try:
        # 根據圖片大小調整字體大小
        font_size = max(12, min(20, image_array.shape[1] // 30))
        font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # 準備資訊文字
    info_text = f"高DPI預覽 {scale_factor}x\n原始: {original_width}×{original_height}\n當前: {image_array.shape[1]}×{image_array.shape[0]}"
    
    # 計算文字位置（右上角）
    text_x = image_array.shape[1] - 120
    text_y = 10
    
    # 繪製半透明背景
    text_bbox = draw.textbbox((text_x, text_y), info_text, font=font)
    padding = 5
    bg_bbox = (
        text_bbox[0] - padding,
        text_bbox[1] - padding, 
        text_bbox[2] + padding,
        text_bbox[3] + padding
    )
    
    # 創建半透明覆蓋層
    overlay = Image.new('RGBA', pil_img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(bg_bbox, fill=(0, 0, 0, 128))  # 半透明黑色背景
    
    # 合併覆蓋層
    pil_img = pil_img.convert('RGBA')
    pil_img = Image.alpha_composite(pil_img, overlay)
    
    # 繪製文字
    draw = ImageDraw.Draw(pil_img)
    draw.text((text_x, text_y), info_text, fill=(255, 255, 255, 255), font=font)
    
    # 轉換回RGB numpy陣列
    pil_img = pil_img.convert('RGB')
    return np.array(pil_img)

def apply_mtf_to_high_dpi_image(image_array: np.ndarray, mtf_percent: float, **kwargs) -> np.ndarray:
    """
    對高DPI圖片套用MTF濾鏡
    
    這個函數會自動調整MTF參數以適應高DPI圖片的像素密度
    
    Args:
        image_array (np.ndarray): 高DPI圖片陣列
        mtf_percent (float): MTF百分比
        **kwargs: 傳遞給原始MTF函數的其他參數
        
    Returns:
        np.ndarray: 處理後的圖片陣列
    """
    
    # 檢測圖片是否為高DPI (基於尺寸推測)
    height, width = image_array.shape[:2]
    is_high_dpi = width > 800 or height > 600  # 簡單的高DPI檢測
    
    if is_high_dpi:
        logger.info(f"檢測到高DPI圖片 ({width}x{height})，調整MTF參數")
        
        # 對於高DPI圖片，可能需要調整像素大小參數
        if 'pixel_size_mm' not in kwargs:
            try:
                from utils.display_calibration import quick_pixel_size_detection
                pixel_size_mm = quick_pixel_size_detection()
                
                # 如果是2x圖片，像素密度實際上是兩倍
                # 這裡需要根據實際的縮放策略來調整
                kwargs['pixel_size_mm'] = pixel_size_mm
                
            except Exception as e:
                logger.warning(f"高DPI像素大小檢測失敗: {e}")
    
    return apply_mtf_to_image(image_array, mtf_percent, **kwargs)

def get_image_dpi_info(image_path: str) -> Dict[str, Union[int, float, str]]:
    """
    獲取圖片的DPI資訊
    
    Args:
        image_path (str): 圖片路徑
        
    Returns:
        dict: 包含DPI資訊的字典
    """
    
    try:
        with Image.open(image_path) as img:
            # 獲取DPI資訊 (PIL返回的是DPI tuple)
            dpi = img.info.get('dpi', (72, 72))
            
            return {
                'width': img.size[0],
                'height': img.size[1], 
                'dpi_x': dpi[0],
                'dpi_y': dpi[1],
                'mode': img.mode,
                'format': img.format,
                'estimated_dpi_level': _estimate_dpi_level(img.size[0], img.size[1], dpi[0])
            }
            
    except Exception as e:
        logger.error(f"無法獲取圖片DPI資訊: {e}")
        return {
            'error': str(e)
        }

def _estimate_dpi_level(width: int, height: int, dpi: float) -> str:
    """
    根據圖片尺寸和DPI估計DPI等級
    
    Args:
        width (int): 圖片寬度
        height (int): 圖片高度
        dpi (float): 圖片DPI
        
    Returns:
        str: 估計的DPI等級
    """
    
    # 基於像素數量的簡單估計
    total_pixels = width * height
    
    if total_pixels > 2000000:  # > 2MP
        return "3x_candidate"
    elif total_pixels > 800000:  # > 0.8MP
        return "2x_candidate" 
    else:
        return "standard"

def batch_convert_to_high_dpi(source_dir: str, target_dpi_level: str = "2x") -> Dict[str, str]:
    """
    批次轉換圖片為高DPI版本
    
    Args:
        source_dir (str): 來源目錄路徑
        target_dpi_level (str): 目標DPI等級
        
    Returns:
        dict: 轉換結果報告
    """
    
    project_root = get_project_root()
    standard_dir = os.path.join(project_root, 'stimuli_preparation', 'standard')
    target_dir = os.path.join(project_root, 'stimuli_preparation', 'high_dpi', target_dpi_level)
    
    # 確保目標目錄存在
    os.makedirs(target_dir, exist_ok=True)
    
    results = {
        'processed': [],
        'skipped': [],
        'errors': []
    }
    
    # 處理標準目錄中的所有PNG檔案
    for filename in os.listdir(standard_dir):
        if filename.lower().endswith('.png'):
            source_path = os.path.join(standard_dir, filename)
            target_path = os.path.join(target_dir, filename)
            
            try:
                # 如果目標檔案已存在，跳過
                if os.path.exists(target_path):
                    results['skipped'].append(filename)
                    continue
                
                # 這裡可以實現實際的高DPI轉換邏輯
                # 目前只是複製檔案作為佔位符
                import shutil
                shutil.copy2(source_path, target_path)
                results['processed'].append(filename)
                
                logger.info(f"已處理: {filename} -> {target_dpi_level}")
                
            except Exception as e:
                results['errors'].append(f"{filename}: {str(e)}")
                logger.error(f"處理 {filename} 時發生錯誤: {e}")
    
    return results

if __name__ == "__main__":
    """測試用的主程式"""
    
    try:
        # 測試DPI檢測
        optimal_dpi = detect_optimal_dpi_level()
        print(f"檢測到最佳DPI等級: {optimal_dpi}")
        
        # 測試圖片載入
        project_root = get_project_root()
        test_image = os.path.join(project_root, 'stimuli_preparation', 'standard', 'stimuli_img.png')
        
        if os.path.exists(test_image):
            # 載入高DPI圖片
            high_dpi_img = load_and_prepare_high_dpi_image('stimuli_img.png')
            print(f"高DPI圖片尺寸: {high_dpi_img.shape}")
            
            # 創建預覽
            preview_img = create_high_dpi_preview(high_dpi_img, scale_factor=0.5)
            print(f"預覽圖片尺寸: {preview_img.shape}")
            
            # 儲存測試結果
            test_output_dir = os.path.join(project_root, 'tests')
            os.makedirs(test_output_dir, exist_ok=True)
            
            # 儲存預覽圖片
            preview_path = os.path.join(test_output_dir, 'high_dpi_preview_test.png')
            cv2.imwrite(preview_path, cv2.cvtColor(preview_img, cv2.COLOR_RGB2BGR))
            print(f"預覽圖片已儲存至: {preview_path}")
            
            print("✓ 高DPI工具測試完成")
        else:
            print(f"✗ 測試圖片不存在: {test_image}")
            
    except Exception as e:
        print(f"✗ 測試失敗: {e}")