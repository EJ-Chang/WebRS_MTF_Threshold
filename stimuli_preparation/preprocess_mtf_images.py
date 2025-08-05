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

def calculate_dynamic_mtf_parameters(panel_size=27, panel_resolution_H=3840, panel_resolution_V=2160):
    """動態計算 MTF 參數 (v0.4 算法)"""
    panel_resolution_D = (panel_resolution_H**2 + panel_resolution_V**2)**0.5
    pixel_size_mm = (panel_size * 25.4) / panel_resolution_D
    nyquist_lpmm = round(1/(2*pixel_size_mm)*2, 2)
    frequency_lpmm = nyquist_lpmm
    return pixel_size_mm, frequency_lpmm

def sigma_vs_mtf(f_lpmm, pixel_size_mm, sigma_pixel_max=5):
    """建立 sigma_pixel 掃描範圍並計算對應 MTF (v0.4 算法)"""
    sigma_pixel_range = np.linspace(0, sigma_pixel_max, 10000)
    sigma_mm = sigma_pixel_range * pixel_size_mm
    # 計算對應 MTF
    mtf_values = np.exp(-2 * (np.pi**2) * (sigma_mm**2) * (f_lpmm**2))
    mtf_percent = mtf_values * 100
    # 標記每 5% MTF 所對應的 sigma_pixel
    target_mtf_levels = np.arange(100, -5, -5)  # 100, 95, ..., 0
    result_table = []
    for target_mtf in target_mtf_levels:
        idx = np.argmin(np.abs(mtf_percent - target_mtf))
        sig_val = sigma_pixel_range[idx]
        result_table.append((target_mtf, sig_val))
    return result_table

def lookup_sigma_from_mtf(target_table, mtf_list):
    """從預計算表中查找對應的 sigma 值 (v0.4 算法)"""
    mtf_values, sigma_values = zip(*target_table)
    results = []
    for mtf_target in mtf_list:
        idx = np.argmin(np.abs(np.array(mtf_values) - mtf_target))
        sigma_pixel = sigma_values[idx]
        results.append((mtf_target, sigma_pixel))
    return results

def mtf_to_sigma(mtf_percent, frequency_lpmm, pixel_size_mm):
    """傳統 MTF 到 sigma 轉換 (備用)"""
    mtf_ratio = mtf_percent / 100.0
    if mtf_ratio <= 0 or mtf_ratio >= 1:
        raise ValueError(f"MTF ratio ({mtf_ratio:.2f}) 必須介於 0~1 之間（不含）。請確保 MTF 百分比在 0~99 之間。")
    f = frequency_lpmm
    sigma_mm = np.sqrt(-np.log(mtf_ratio) / (2 * (np.pi * f) ** 2))
    sigma_pixels = sigma_mm / pixel_size_mm
    return sigma_pixels

def preprocess_images(image_path, mtf_values, frequency_lpmm, pixel_size_mm, output_dir, use_v4_algorithm=True):
    """預處理所有MTF值對應的圖片並儲存 (支援 v0.4 算法)"""
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
    
    # 選擇算法
    if use_v4_algorithm:
        print(f"使用 v0.4 新算法處理 {len(mtf_values)} 個 MTF 值")
        # 建立查表
        target_table = sigma_vs_mtf(frequency_lpmm, pixel_size_mm)
        sigma_mtf_pairs = lookup_sigma_from_mtf(target_table, mtf_values)
        
        # 批量處理
        for mtf_value, sigma_pixel in sigma_mtf_pairs:
            start_time = time.time()  # 開始計時
            
            img_blurred = cv2.GaussianBlur(right_half, (0, 0), sigmaX=sigma_pixel, sigmaY=sigma_pixel)
            
            # 儲存模糊後的圖片
            output_path = os.path.join(output_dir, f"mtf_{mtf_value:03d}.png")
            cv2.imwrite(output_path, cv2.cvtColor(img_blurred, cv2.COLOR_RGB2BGR))
            
            end_time = time.time()  # 結束計時
            processing_time = (end_time - start_time) * 1000  # 轉換為毫秒
            processing_times.append(processing_time)
            
            print(f"已生成 MTF {mtf_value}% 的圖片 (v0.4)：{output_path} (sigma={sigma_pixel:.4f}, 時間：{processing_time:.2f} ms)")
    else:
        print(f"使用傳統算法處理 {len(mtf_values)} 個 MTF 值")
        # 傳統逐一處理
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
            
            print(f"已生成 MTF {mtf}% 的圖片 (傳統)：{output_path} (sigma={sigma:.4f}, 時間：{processing_time:.2f} ms)")
    
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
    
    # 使用 v0.4 動態參數計算
    pixel_size_mm, frequency_lpmm = calculate_dynamic_mtf_parameters()
    mtf_values = list(range(5, 100, 5))  # 5% 到 95%，每 5% 一級
    
    print(f"\n✅ MTF v0.4 參數:")
    print(f"   像素大小: {pixel_size_mm:.6f} mm")
    print(f"   Nyquist 頻率: {frequency_lpmm} lp/mm")
    print(f"   處理 MTF 值: {len(mtf_values)} 個級別")
    
    # 設定輸入輸出路徑
    input_image = os.path.join(project_root, 'stimuli_preparation', 'stimuli_img.png')
    output_dir = os.path.join(project_root, 'mtf_stimuli_v04')
    
    try:
        # 比較新舊算法的效能測試
        print("\n🔄 效能測試比較 (v0.4 vs 傳統)...")
        
        # v0.4 算法測試
        stats_v4 = benchmark_processing_v4(input_image, mtf_values, frequency_lpmm, pixel_size_mm)
        
        # 傳統算法測試
        old_pixel_size = 0.005649806841172989
        old_frequency = 44.25
        stats_old = benchmark_processing(input_image, mtf_values, old_frequency, old_pixel_size)
        
        # 顯示比較結果
        print("\n📊 效能比較結果：")
        print("-" * 90)
        print(f"{'MTF值':>6} {'v0.4平均(ms)':>12} {'傳統平均(ms)':>12} {'改善%':>10} {'v0.4 sigma':>12} {'傳統 sigma':>12}")
        print("-" * 90)
        
        # 建立查表用於比較
        target_table = sigma_vs_mtf(frequency_lpmm, pixel_size_mm)
        
        for mtf in mtf_values:
            s_v4 = stats_v4[mtf]
            s_old = stats_old[mtf]
            improvement = ((s_old['平均'] - s_v4['平均']) / s_old['平均']) * 100
            
            # 計算 sigma 值比較
            sigma_pairs = lookup_sigma_from_mtf(target_table, [mtf])
            v4_sigma = sigma_pairs[0][1] if sigma_pairs else 0
            old_sigma = mtf_to_sigma(mtf, old_frequency, old_pixel_size)
            
            print(f"{mtf:6d} {s_v4['平均']:12.2f} {s_old['平均']:12.2f} {improvement:10.1f} {v4_sigma:12.4f} {old_sigma:12.4f}")
        
        # 生成所有 MTF 圖片 (使用 v0.4 算法)
        print(f"\n🎯 開始生成 MTF 圖片 (v0.4 算法)...")
        processing_times = preprocess_images(input_image, mtf_values, frequency_lpmm, pixel_size_mm, output_dir, use_v4_algorithm=True)
        print(f"\n✅ 所有 v0.4 圖片已生成並儲存至：{output_dir}")
        
        # 額外生成傳統算法對比
        output_dir_old = os.path.join(project_root, 'mtf_stimuli_old')
        print(f"\n🔄 生成傳統算法對比圖片...")
        processing_times_old = preprocess_images(input_image, mtf_values, old_frequency, old_pixel_size, output_dir_old, use_v4_algorithm=False)
        print(f"✅ 傳統算法圖片已生成並儲存至：{output_dir_old}")
        
    except Exception as e:
        print(f"\n❌ 錯誤：{str(e)}")
        print("程式執行失敗。")

def benchmark_processing_v4(image_path, mtf_values, frequency_lpmm, pixel_size_mm, iterations=5):
    """進行 v0.4 算法效能測試"""
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
    
    # 建立查表 (只需建立一次)
    target_table = sigma_vs_mtf(frequency_lpmm, pixel_size_mm)
    sigma_mtf_pairs = lookup_sigma_from_mtf(target_table, mtf_values)
    
    # 儲存每個 MTF 值的處理時間
    all_times = {mtf: [] for mtf in mtf_values}
    
    print(f"\n開始 v0.4 算法效能測試，每個 MTF 值將重複處理 {iterations} 次...")
    
    for i in range(iterations):
        print(f"\nv0.4 第 {i+1} 次測試：")
        for mtf_value, sigma_pixel in sigma_mtf_pairs:
            start_time = time.time()
            
            img_blurred = cv2.GaussianBlur(right_half, (0, 0), sigmaX=sigma_pixel, sigmaY=sigma_pixel)
            
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000  # 轉換為毫秒
            all_times[mtf_value].append(processing_time)
            
            print(f"MTF {mtf_value}%: {processing_time:.2f} ms")
    
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

if __name__ == "__main__":
    main()