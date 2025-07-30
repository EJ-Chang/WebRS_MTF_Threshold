"""
mtf_utils.py

MTF (Modulation Transfer Function) 圖片處理工具函數

提供即時對圖片套用 MTF 模糊效果的功能，適用於心理物理實驗。
支援任意 MTF 百分比值和不同的輸入圖片。

Author: EJ  
Last reviewed: 2025-06
"""

import cv2
import numpy as np
import time
import os
import logging

# 設定日誌
logger = logging.getLogger(__name__)

def get_project_root():
    """獲取專案根目錄的絕對路徑。
    
    Returns:
        str: 專案根目錄的絕對路徑
    """
    # 獲取腳本所在目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 往上一層到專案根目錄
    return os.path.dirname(script_dir)

def apply_mtf_to_image(image, mtf_percent, frequency_lpmm=3.0, pixel_size_mm=0.169333):
    """對圖片套用指定的 MTF 值
    
    將輸入圖片透過高斯模糊來模擬指定的 MTF (調制傳遞函數) 效果。
    MTF 值越低，圖片越模糊；MTF 值越高，圖片越清晰。
    
    Args:
        image (numpy.ndarray): 輸入圖片陣列，格式為 RGB (H, W, 3)
        mtf_percent (float): MTF 百分比，範圍 0.1-99.9 (不含 0 和 100)
        frequency_lpmm (float, optional): 空間頻率 (線對/毫米)，預設 3.0
        pixel_size_mm (float, optional): 像素大小 (毫米)，默認 150 DPI
    
    Returns:
        numpy.ndarray: 處理後的圖片陣列，格式與輸入相同
        
    Raises:
        ValueError: 當 MTF 百分比不在有效範圍內時
        TypeError: 當輸入圖片格式不正確時
        
    Example:
        >>> import cv2
        >>> img = cv2.imread('test.png')
        >>> img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        >>> img_mtf_50 = apply_mtf_to_image(img_rgb, 50.0)
    """
    
    # 輸入驗證
    if not isinstance(image, np.ndarray):
        raise TypeError("輸入必須是 numpy 陣列")
    
    if len(image.shape) != 3 or image.shape[2] != 3:
        raise ValueError("輸入圖片必須是 RGB 格式 (高度, 寬度, 3)")
    
    if not (0 < mtf_percent < 100):
        raise ValueError(f"MTF 百分比 ({mtf_percent}) 必須介於 0~100 之間 (不含邊界值)")
    
    # 使用固定像素大小 (150 DPI = 0.169333 mm/pixel)
    logger.debug(f"📏 使用固定像素大小: {pixel_size_mm:.6f} mm (150 DPI)")
    
    # MTF 百分比轉換為比例
    mtf_ratio = mtf_percent / 100.0
    
    # 計算對應的高斯模糊 sigma 值
    # 基於 MTF = exp(-2π²f²σ²) 的公式反推 σ
    f = frequency_lpmm
    sigma_mm = np.sqrt(-np.log(mtf_ratio) / (2 * (np.pi * f) ** 2))
    sigma_pixels = sigma_mm / pixel_size_mm
    
    # 🔍 調試日誌：顯示所有計算步驟
    print(f"🔬 MTF調試信息:")
    print(f"   MTF輸入: {mtf_percent}% -> ratio: {mtf_ratio:.4f}")
    print(f"   頻率: {f} 線對/毫米")
    print(f"   像素大小: {pixel_size_mm:.6f} 毫米")
    print(f"   計算得出 sigma_mm: {sigma_mm:.6f} 毫米")
    print(f"   計算得出 sigma_pixels: {sigma_pixels:.2f} 像素")
    
    # 如果 sigma 太小，強制設定最小值
    if sigma_pixels < 0.5:
        print(f"⚠️  Sigma太小 ({sigma_pixels:.2f})，設定為最小值 0.5")
        sigma_pixels = 0.5
    
    # 套用高斯模糊
    # 使用 (0, 0) 讓 OpenCV 自動計算核心大小
    img_blurred = cv2.GaussianBlur(
        image, 
        (0, 0), 
        sigmaX=sigma_pixels, 
        sigmaY=sigma_pixels,
        borderType=cv2.BORDER_REFLECT
    )
    
    print(f"✅ 已套用高斯模糊 sigma={sigma_pixels:.2f} 像素")
    
    return img_blurred


def normalize_for_psychopy(image):
    """將圖片正規化到 PsychoPy 要求的 -1 到 1 範圍
    
    Args:
        image (numpy.ndarray): RGB 圖片陣列 (0-255 範圍)
        
    Returns:
        numpy.ndarray: 正規化後的圖片陣列 (-1 到 1 範圍)
    """
    # 轉換為 float 並正規化到 -1 到 1
    # 正確公式：(0-255) -> (0-1) -> (-1 到 1)
    return (image.astype(np.float32) / 255.0) * 2.0 - 1.0


def load_and_prepare_image(image_path, use_right_half=True):
    """載入圖片並準備用於 MTF 處理
    
    載入圖片檔案，轉換為 RGB 格式，並根據圖片類型選擇不同的裁切方式。
    - stimuli_img.png: 取右半邊（保持原有行為）
    - 其他圖片 (text_img.png, tw_newsimg.png, us_newsimg.png): 取中央部分，裁切左右兩側
    
    Args:
        image_path (str): 圖片檔案路徑
        use_right_half (bool, optional): 是否只取右半邊，預設 True
        
    Returns:
        numpy.ndarray: 準備好的 RGB 圖片陣列
        
    Raises:
        FileNotFoundError: 當圖片檔案不存在時
        ValueError: 當圖片無法正確載入時
        
    Example:
        >>> # 一般圖片用途
        >>> base_img = load_and_prepare_image('stimuli_img.png')
        >>> # 文字圖片用途
        >>> text_img = load_and_prepare_image('text_img.png')
        >>> img_mtf = apply_mtf_to_image(base_img, 45.0)
    """
    
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
    
    # 根據圖片類型和參數決定裁切方式
    if use_right_half:
        # 檢查是否為文字圖片
        image_name = os.path.basename(image_path).lower()
        
        if 'stimuli_img' in image_name:
            # 原始stimuli_img：取右半邊（保持原有行為）
            width = img_rgb.shape[1]
            mid_point = width // 2
            img_rgb = img_rgb[:, mid_point:]
            print(f"stimuli_img裁切：從 {width} 取右半邊，結果寬度 {img_rgb.shape[1]}")
        else:
            # 其他圖片（text_img, tw_newsimg, us_newsimg）：取中央部分
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


def benchmark_mtf_processing(image, mtf_values, iterations=10, **mtf_params):
    """測試 MTF 處理的效能
    
    對指定的 MTF 值進行多次處理，計算平均處理時間。
    
    Args:
        image (numpy.ndarray): 基礎圖片陣列
        mtf_values (list): 要測試的 MTF 值列表
        iterations (int, optional): 每個 MTF 值的重複次數，預設 10
        **mtf_params: 傳遞給 apply_mtf_to_image 的其他參數
        
    Returns:
        dict: 包含每個 MTF 值的效能統計
        
    Example:
        >>> img = load_and_prepare_image('test.png')
        >>> test_mtf = [20, 40, 60, 80]
        >>> stats = benchmark_mtf_processing(img, test_mtf)
        >>> print(f"平均處理時間：{stats['overall_mean']:.2f} ms")
    """
    
    results = {}
    all_times = []
    
    print(f"開始 MTF 處理效能測試 ({iterations} 次重複)...")
    print("-" * 50)
    
    for mtf in mtf_values:
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            _ = apply_mtf_to_image(image, mtf, **mtf_params)
            end_time = time.time()
            
            processing_time = (end_time - start_time) * 1000  # 轉換為毫秒
            times.append(processing_time)
        
        # 計算統計
        mean_time = np.mean(times)
        std_time = np.std(times)
        min_time = np.min(times)
        max_time = np.max(times)
        
        results[mtf] = {
            'mean': mean_time,
            'std': std_time,
            'min': min_time,
            'max': max_time,
            'times': times
        }
        
        all_times.extend(times)
        
        print(f"MTF {mtf:5.1f}%: {mean_time:6.2f} ± {std_time:5.2f} ms "
              f"(範圍: {min_time:.2f} - {max_time:.2f})")
    
    # 整體統計
    overall_mean = np.mean(all_times)
    overall_std = np.std(all_times)
    overall_min = np.min(all_times)
    overall_max = np.max(all_times)
    
    results['overall'] = {
        'mean': overall_mean,
        'std': overall_std, 
        'min': overall_min,
        'max': overall_max
    }
    
    print("-" * 50)
    print(f"整體統計：{overall_mean:.2f} ± {overall_std:.2f} ms")
    print(f"範圍：{overall_min:.2f} - {overall_max:.2f} ms")
    
    return results


def apply_calibrated_mtf(image, mtf_percent, frequency_lpmm=44.25):
    """
    使用自動校準的像素大小進行 MTF 處理
    
    這是一個便利函數，專門用於心理物理學實驗中的精確MTF處理。
    它會自動檢測顯示器的像素大小，確保MTF濾波器的精確性。
    
    Args:
        image (numpy.ndarray): 輸入圖片陣列，格式為 RGB (H, W, 3)
        mtf_percent (float): MTF 百分比，範圍 0.1-99.9 (不含 0 和 100)
        frequency_lpmm (float, optional): 空間頻率 (線對/毫米)，預設 3.0
        
    Returns:
        tuple: (processed_image, pixel_size_used)
            - processed_image: 處理後的圖片陣列
            - pixel_size_used: 實際使用的像素大小 (mm)
    """
    try:
        from utils.display_calibration import get_display_calibration
        
        # 獲取校準的像素大小
        calibration = get_display_calibration()
        pixel_size_mm = calibration.calculate_mtf_pixel_size()
        
        # 處理圖片
        processed_image = apply_mtf_to_image(
            image, 
            mtf_percent, 
            frequency_lpmm=frequency_lpmm,
            pixel_size_mm=pixel_size_mm
        )
        
        logger.info(f"🎯 校準MTF處理完成 - MTF: {mtf_percent}%, 像素: {pixel_size_mm:.6f}mm")
        
        return processed_image, pixel_size_mm
        
    except Exception as e:
        logger.error(f"校準MTF處理失敗: {e}")
        # 使用默認處理作為後備
        processed_image = apply_mtf_to_image(image, mtf_percent, frequency_lpmm)
        return processed_image, 0.005649806841172989  # 返回默認值


def get_current_pixel_size_info():
    """
    獲取當前系統的像素大小信息
    
    Returns:
        dict: 包含像素大小信息的字典
    """
    try:
        from utils.display_calibration import get_display_calibration
        
        calibration = get_display_calibration()
        display_info = calibration.get_display_info()
        
        if display_info:
            return {
                'pixel_size_mm': display_info.pixel_size_mm,
                'dpi_x': display_info.dpi_x,
                'dpi_y': display_info.dpi_y,
                'resolution': f"{display_info.width_pixels}x{display_info.height_pixels}",
                'detection_method': display_info.detected_method,
                'confidence': display_info.confidence,
                'is_calibrated': True
            }
        else:
            return {
                'pixel_size_mm': 0.005649806841172989,
                'dpi_x': 96.0,
                'dpi_y': 96.0,
                'resolution': 'unknown',
                'detection_method': 'default_fallback',
                'confidence': 0.0,
                'is_calibrated': False
            }
            
    except Exception as e:
        logger.warning(f"無法獲取像素大小信息: {e}")
        return {
            'pixel_size_mm': 0.005649806841172989,
            'dpi_x': 96.0,
            'dpi_y': 96.0,
            'resolution': 'unknown',
            'detection_method': 'error_fallback',
            'confidence': 0.0,
            'is_calibrated': False,
            'error': str(e)
        }


def validate_mtf_processing_accuracy(image, mtf_values, frequency_lpmm=44.25):
    """
    驗證MTF處理的精確性
    
    比較使用默認像素大小和校準像素大小的MTF處理結果。
    
    Args:
        image (numpy.ndarray): 測試圖片
        mtf_values (list): 要測試的MTF值列表
        frequency_lpmm (float): 空間頻率
        
    Returns:
        dict: 驗證結果
    """
    try:
        from utils.display_calibration import get_display_calibration
        
        calibration = get_display_calibration()
        calibrated_pixel_size = calibration.calculate_mtf_pixel_size()
        default_pixel_size = 0.005649806841172989
        
        results = {
            'calibrated_pixel_size': calibrated_pixel_size,
            'default_pixel_size': default_pixel_size,
            'pixel_size_difference_percent': abs(calibrated_pixel_size - default_pixel_size) / default_pixel_size * 100,
            'mtf_comparisons': {}
        }
        
        for mtf_value in mtf_values:
            # 使用校準像素大小
            img_calibrated = apply_mtf_to_image(image, mtf_value, frequency_lpmm, calibrated_pixel_size)
            
            # 使用默認像素大小  
            img_default = apply_mtf_to_image(image, mtf_value, frequency_lpmm, default_pixel_size)
            
            # 計算差異
            diff = np.mean(np.abs(img_calibrated.astype(float) - img_default.astype(float)))
            max_diff = np.max(np.abs(img_calibrated.astype(float) - img_default.astype(float)))
            
            results['mtf_comparisons'][mtf_value] = {
                'mean_difference': diff,
                'max_difference': max_diff,
                'difference_percentage': diff / 255.0 * 100
            }
        
        # 總體評估
        all_diffs = [comp['mean_difference'] for comp in results['mtf_comparisons'].values()]
        results['overall_assessment'] = {
            'avg_difference': np.mean(all_diffs),
            'max_difference': np.max(all_diffs),
            'calibration_impact': 'significant' if np.mean(all_diffs) > 1.0 else 'minimal'
        }
        
        return results
        
    except Exception as e:
        logger.error(f"MTF處理精確性驗證失敗: {e}")
        return {'error': str(e)}


if __name__ == "__main__":
    """測試用的主程式"""
    
    # 獲取專案根目錄
    project_root = get_project_root()
    
    # 測試基本功能
    try:
        # 載入測試圖片
        test_image_path = os.path.join(project_root, 'stimuli_preparation', 'stimuli_img.png')
        print(f"載入測試圖片：{test_image_path}")
        
        img = load_and_prepare_image(test_image_path)
        print(f"圖片尺寸：{img.shape}")
        
        # 測試單次處理
        print("\n測試單次 MTF 處理...")
        start = time.time()
        img_mtf_30 = apply_mtf_to_image(img, 30.0)
        end = time.time()
        print(f"MTF 30% 處理時間：{(end-start)*1000:.2f} ms")
        
        # 儲存處理後的圖片
        output_dir = os.path.join(project_root, 'tests')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'mtf_030_test.png')
        cv2.imwrite(output_path, cv2.cvtColor(img_mtf_30, cv2.COLOR_RGB2BGR))
        print(f"已儲存測試圖片至：{output_path}")
        
        # 效能測試
        print("\n進行效能測試...")
        test_mtf_values = [10, 25, 46.1, 67.5, 85]
        benchmark_mtf_processing(img, test_mtf_values, iterations=5)
        
        print("\n✓ 所有測試完成")
        
    except FileNotFoundError as e:
        print(f"✗ 檔案錯誤：{e}")
        print("請確認圖片路徑正確")
    except Exception as e:
        print(f"✗ 測試失敗：{e}")
