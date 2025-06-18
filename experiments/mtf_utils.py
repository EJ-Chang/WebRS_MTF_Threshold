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

def get_project_root():
    """獲取專案根目錄的絕對路徑。
    
    Returns:
        str: 專案根目錄的絕對路徑
    """
    # 獲取腳本所在目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 往上一層到專案根目錄
    return os.path.dirname(script_dir)

def apply_mtf_to_image(image, mtf_percent, frequency_lpmm=44.25, pixel_size_mm=0.005649806841172989):
    """對圖片套用指定的 MTF 值
    
    將輸入圖片透過高斯模糊來模擬指定的 MTF (調制傳遞函數) 效果。
    MTF 值越低，圖片越模糊；MTF 值越高，圖片越清晰。
    
    Args:
        image (numpy.ndarray): 輸入圖片陣列，格式為 RGB (H, W, 3)
        mtf_percent (float): MTF 百分比，範圍 0.1-99.9 (不含 0 和 100)
        frequency_lpmm (float, optional): 空間頻率 (線對/毫米)，預設 44.25
        pixel_size_mm (float, optional): 像素大小 (毫米)，預設約 0.00565
    
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
    
    # MTF 百分比轉換為比例
    mtf_ratio = mtf_percent / 100.0
    
    # 計算對應的高斯模糊 sigma 值
    # 基於 MTF = exp(-2π²f²σ²) 的公式反推 σ
    f = frequency_lpmm
    sigma_mm = np.sqrt(-np.log(mtf_ratio) / (2 * (np.pi * f) ** 2))
    sigma_pixels = sigma_mm / pixel_size_mm
    
    # 套用高斯模糊
    # 使用 (0, 0) 讓 OpenCV 自動計算核心大小
    img_blurred = cv2.GaussianBlur(
        image, 
        (0, 0), 
        sigmaX=sigma_pixels, 
        sigmaY=sigma_pixels,
        borderType=cv2.BORDER_REFLECT
    )
    
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
