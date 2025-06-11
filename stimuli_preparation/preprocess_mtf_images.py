import cv2
import numpy as np
import os
from datetime import datetime
import time
import platform
import psutil
import statistics

def get_project_root():
    """獲取專案根目錄的絕對路徑。
    
    Returns:
        str: 專案根目錄的絕對路徑
    """
    # 獲取腳本所在目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 往上一層到專案根目錄
    return os.path.dirname(script_dir)

def mtf_to_sigma(mtf_percent, frequency_lpmm, pixel_size_mm):
    mtf_ratio = mtf_percent / 100.0
    if mtf_ratio <= 0 or mtf_ratio >= 1:
        raise ValueError(f"MTF ratio ({mtf_ratio:.2f}) 必須介於 0~1 之間（不含）。請確保 MTF 百分比在 0~99 之間。")
    f = frequency_lpmm
    sigma_mm = np.sqrt(-np.log(mtf_ratio) / (2 * (np.pi * f) ** 2))
    sigma_pixels = sigma_mm / pixel_size_mm
    return sigma_pixels

def preprocess_images(image_path, mtf_values, frequency_lpmm, pixel_size_mm, output_dir):
    """預處理所有MTF值對應的圖片並儲存，確保在PsychoPy中能正確顯示"""
    # 建立輸出目錄
    os.makedirs(output_dir, exist_ok=True)
    
    # 載入原始圖片
    img_bgr = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img_bgr is None:
        raise FileNotFoundError(f"找不到圖片：{image_path}")

    if img_bgr.shape[2] == 4:
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGRA2RGB)
    else:
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    # 取得右半邊圖片
    width = img_rgb.shape[1]
    mid_point = width // 2
    right_half = img_rgb[:, mid_point:]
    
    # 儲存右半邊原圖（未模糊處理）
    right_half_path = os.path.join(output_dir, "right_half_original.png")
    cv2.imwrite(right_half_path, cv2.cvtColor(right_half, cv2.COLOR_RGB2BGR))
    
    # 用於儲存每個 MTF 值的處理時間
    processing_times = []
    
    # 處理每個 MTF 值
    for mtf in mtf_values:
        start_time = time.time()  # 開始計時
        
        sigma = mtf_to_sigma(mtf, frequency_lpmm, pixel_size_mm)
        img_blurred = cv2.GaussianBlur(right_half, (0, 0), sigmaX=sigma, sigmaY=sigma)
        
        # 儲存模糊後的圖片
        output_path = os.path.join(output_dir, f"mtf_{mtf:03d}.png")
        cv2.imwrite(output_path, cv2.cvtColor(img_blurred, cv2.COLOR_RGB2BGR))
        
        end_time = time.time()  # 結束計時
        processing_time = (end_time - start_time) * 1000  # 轉換為毫秒
        processing_times.append(processing_time)
        
        print(f"已生成 MTF {mtf}% 的圖片：{output_path} (處理時間：{processing_time:.2f} ms)")
    
    return processing_times

def get_system_info():
    """獲取系統資訊"""
    info = {
        "作業系統": platform.system(),
        "CPU": platform.processor(),
        "CPU核心數": psutil.cpu_count(logical=False),
        "CPU邏輯核心數": psutil.cpu_count(logical=True),
        "記憶體總量": f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
        "可用記憶體": f"{psutil.virtual_memory().available / (1024**3):.1f} GB"
    }
    return info

def benchmark_processing(image_path, mtf_values, frequency_lpmm, pixel_size_mm, iterations=5):
    """進行效能測試，重複多次處理並計算統計數據"""
    # 載入原始圖片
    img_bgr = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img_bgr is None:
        raise FileNotFoundError(f"找不到圖片：{image_path}")

    if img_bgr.shape[2] == 4:
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGRA2RGB)
    else:
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    width = img_rgb.shape[1]
    mid_point = width // 2
    right_half = img_rgb[:, mid_point:]
    
    # 儲存每個 MTF 值的處理時間
    all_times = {mtf: [] for mtf in mtf_values}
    
    print(f"\n開始效能測試，每個 MTF 值將重複處理 {iterations} 次...")
    
    for i in range(iterations):
        print(f"\n第 {i+1} 次測試：")
        for mtf in mtf_values:
            start_time = time.time()
            
            sigma = mtf_to_sigma(mtf, frequency_lpmm, pixel_size_mm)
            img_blurred = cv2.GaussianBlur(right_half, (0, 0), sigmaX=sigma, sigmaY=sigma)
            
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000  # 轉換為毫秒
            all_times[mtf].append(processing_time)
            
            print(f"MTF {mtf}%: {processing_time:.2f} ms")
    
    # 計算統計數據
    stats = {}
    for mtf in mtf_values:
        times = all_times[mtf]
        stats[mtf] = {
            "平均": statistics.mean(times),
            "中位數": statistics.median(times),
            "標準差": statistics.stdev(times) if len(times) > 1 else 0,
            "最小值": min(times),
            "最大值": max(times)
        }
    
    return stats

def main():
    # 獲取專案根目錄
    project_root = get_project_root()
    
    # 顯示系統資訊
    print("系統資訊：")
    for key, value in get_system_info().items():
        print(f"{key}: {value}")
    
    # 參數設定
    pixel_size_mm = 0.005649806841172989
    frequency_lpmm = 44.25
    mtf_values = list(range(5, 100, 5))  # 5% 到 95%，每 5% 一級
    
    # 設定輸入輸出路徑
    input_image = os.path.join(project_root, 'stimuli_preparation', 'stimuli_img.png')
    output_dir = os.path.join(project_root, 'mtf_stimuli')
    
    try:
        # 進行效能測試
        stats = benchmark_processing(input_image, mtf_values, frequency_lpmm, pixel_size_mm)
        
        # 顯示統計結果
        print("\n效能測試結果：")
        print("-" * 80)
        print(f"{'MTF值':>6} {'平均時間(ms)':>12} {'中位數(ms)':>12} {'標準差(ms)':>12} {'最小值(ms)':>12} {'最大值(ms)':>12}")
        print("-" * 80)
        
        for mtf in mtf_values:
            s = stats[mtf]
            print(f"{mtf:6d} {s['平均']:12.2f} {s['中位數']:12.2f} {s['標準差']:12.2f} {s['最小值']:12.2f} {s['最大值']:12.2f}")
        
        # 計算整體統計
        all_means = [s['平均'] for s in stats.values()]
        print("\n整體統計：")
        print(f"所有 MTF 值的平均處理時間：{statistics.mean(all_means):.2f} ms")
        print(f"所有 MTF 值的處理時間標準差：{statistics.stdev(all_means):.2f} ms")
        print(f"最快處理時間：{min(all_means):.2f} ms")
        print(f"最慢處理時間：{max(all_means):.2f} ms")
        
        # 生成所有 MTF 圖片
        print("\n開始生成 MTF 圖片...")
        processing_times = preprocess_images(input_image, mtf_values, frequency_lpmm, pixel_size_mm, output_dir)
        print(f"\n所有圖片已生成並儲存至：{output_dir}")
        
    except Exception as e:
        print(f"\n錯誤：{str(e)}")
        print("程式執行失敗。")

if __name__ == "__main__":
    main()