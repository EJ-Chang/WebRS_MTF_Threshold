import cv2
import numpy as np
import matplotlib.pyplot as plt

#MTD模糊
def mtf_to_sigma(mtf_percent, frequency_lpmm, pixel_size_mm):
    mtf_ratio = mtf_percent / 100.0
    if mtf_ratio <= 0 or mtf_ratio >= 1:
        raise ValueError("MTF ratio must be between 0 and 100 (exclusive)")

    f = frequency_lpmm  # lp/mm
    sigma_mm = np.sqrt(-np.log(mtf_ratio) / (2 * (np.pi * f) ** 2))
    sigma_pixels = sigma_mm / pixel_size_mm
    return sigma_pixels

#拖影模糊
def apply_radial_motion_blur(image, max_blur_length, edge_percentage, curve='linear'):
    h, w, _ = image.shape
    center_x, center_y = w / 2, h / 2

    output = np.zeros_like(image, dtype=np.float32)

    y_indices, x_indices = np.indices((h, w))
    dx = x_indices - center_x
    dy = y_indices - center_y
    distances = np.sqrt(dx**2 + dy**2)
    angles = np.arctan2(dy, dx)

    max_distance = np.sqrt(center_x**2 + center_y**2)
    start_distance = edge_percentage * max_distance

    ratio = np.clip((distances / max_distance), 0, 1)
    if curve == 'quadratic':
        ratio = ratio ** 2

    blur_lengths = (ratio * max_blur_length).astype(np.int32)

    for i in range(h):
        for j in range(w):
            length = blur_lengths[i, j]
            if length > 0:
                angle = angles[i, j]
                step_x = np.cos(angle)
                step_y = np.sin(angle)
                accum = np.zeros(3, dtype=np.float32)
                count = 0
                for k in range(length):
                    x = j + step_x * k
                    y = i + step_y * k
                    x0, y0 = int(np.floor(x)), int(np.floor(y))
                    if 0 <= x0 < w-1 and 0 <= y0 < h-1:
                        # bilinear interpolation
                        dx_frac = x - x0
                        dy_frac = y - y0
                        top_left = image[y0, x0]
                        top_right = image[y0, x0+1]
                        bottom_left = image[y0+1, x0]
                        bottom_right = image[y0+1, x0+1]
                        top = top_left * (1 - dx_frac) + top_right * dx_frac
                        bottom = bottom_left * (1 - dx_frac) + bottom_right * dx_frac
                        pixel = top * (1 - dy_frac) + bottom * dy_frac
                        accum += pixel
                        count += 1
                if count > 0:
                    output[i, j] = accum / count
                else:
                    output[i, j] = image[i, j]
            else:
                output[i, j] = image[i, j]

    output = np.clip(output, 0, 255).astype(np.uint8)
    return output

def scanMTF(frequency_lpmm, pixel_size_mm):
    # 已知參數
    #pixel_size_mm = 0.1        # 例如 0.1 mm/pixel
    #frequency_lpmm = 20                # 頻率 20 lp/mm

    # sigma_pixel 掃描範圍
    sigma_pixel_range = np.linspace(0, 5, 1000)
    sigma_mm = sigma_pixel_range * pixel_size_mm

    # 計算對應的 MTF 值
    mtf_values = np.exp(-2 * (np.pi**2) * (sigma_mm**2) * (frequency_lpmm**2))
    mtf_percent = mtf_values * 100

    # 初始化圖形
    plt.figure(figsize=(10, 6))
    plt.plot(sigma_pixel_range, mtf_percent, label="MTF Curve", color='blue')

    # 標記每 5% MTF 所對應的 sigma_pixel
    target_mtf_levels = np.arange(100, -5, -5)  # 100, 95, ..., 0

    for target_mtf in target_mtf_levels:
        idx = np.argmin(np.abs(mtf_percent - target_mtf))  # 找最接近的索引
        sig_val = sigma_pixel_range[idx]
        mtf_val = mtf_percent[idx]
        plt.plot(sig_val, mtf_val, 'ro')  # 紅點
        plt.text(sig_val, mtf_val + 2, f"{sig_val:.2f}", ha='center', fontsize=8, color='red')

    # 標示與格式
    plt.xlabel("Sigma (pixel)")
    plt.ylabel("MTF (%)")  
    plt.title(f"MTF vs Sigma (f = {frequency_lpmm} lp/mm, pixel size = {pixel_size_mm} mm)")
    plt.grid(True)
    plt.ylim(0, 105)
    plt.legend()
    plt.show()

def sigma_vs_mtf(f_lpmm, pixel_size_mm, sigma_pixel_max=5):
    # 建立 sigma_pixel 掃描範圍
    sigma_pixel_range = np.linspace(0, sigma_pixel_max, 10000)
    sigma_mm = sigma_pixel_range * pixel_size_mm

    # 計算對應 MTF
    mtf_values = np.exp(-2 * (np.pi**2) * (sigma_mm**2) * (f_lpmm**2))
    mtf_percent = mtf_values * 100

    # 標記每 5% MTF 所對應的 sigma_pixel
    target_mtf_levels = np.arange(100, -5, -5)  # 100, 95, ..., 0
    result_table = []

    print(f"\nMTF (f = {f_lpmm} lp/mm, pixel size = {pixel_size_mm} mm)")
    print("-" * 40)
    for target_mtf in target_mtf_levels:
        idx = np.argmin(np.abs(mtf_percent - target_mtf))
        sig_val = sigma_pixel_range[idx]
        result_table.append((target_mtf, sig_val))
        print(f"MTF {target_mtf:>3}% → sigma_pixel ≈ {sig_val:.4f}")
    
    return result_table

def lookup_sigma_from_mtf(target_table, mtf_list):
    mtf_values, sigma_values = zip(*target_table)
    results = []
    for mtf_target in mtf_list:
        idx = np.argmin(np.abs(np.array(mtf_values) - mtf_target))
        sigma_pixel = sigma_values[idx]
        results.append((mtf_target, sigma_pixel))
    return results

# ===== 參數設定 =====
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
name = "us_newsimg.png" # 刺激原圖名稱
image_path = script_dir + "/"     #圖片位置 (使用腳本所在目錄的絕對路徑)
save_path = script_dir + "/mtf_output/"    #儲存圖片位置 (使用腳本所在目錄的絕對路徑)

# 確保輸出目錄存在
os.makedirs(save_path, exist_ok=True)
panel_size = 27     #inch
panel_resolution_H = 3840     #水平
panel_resolution_V = 2160     #垂直
panel_resolution_D = (panel_resolution_H**2 + panel_resolution_V**2)**0.5     #對角
pixel_size_mm = (panel_size * 25.4)/panel_resolution_D     # fiexd(panel規格)
#nyquist_lpmm = round(panel_resolution_D / (panel_size * 25.4)*0.5, 2)       # fixed(panel規格)
nyquist_lpmm = round(1/(2*pixel_size_mm)*2, 2)
frequency_lpmm = nyquist_lpmm
print('Pixel size:', pixel_size_mm)
print('Frequency:', frequency_lpmm)
# ===== 設定拖影參數 =====
max_blur_length = 12  # 拖影程度(pixel)
edge_percentage = 30  # 邊緣拖影範圍百分比
curve = 'linear'

# ===== 讀取彩色圖像 =====
full_image_path = image_path + name
img_bgr = cv2.imread(full_image_path, cv2.IMREAD_COLOR)
if img_bgr is None:
    raise FileNotFoundError(f"Cannot find the image at {full_image_path}")

img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

# ===== 掃描 MTF & sigma_pixel 值 =====
target_table = sigma_vs_mtf(frequency_lpmm, pixel_size_mm)
scanMTF(frequency_lpmm, pixel_size_mm)

# ===== 計算 sigma 值 =====
test1_MTF = [80, 60, 40, 20]  #MTF模糊百分比

# ===== 查找每個 MTF 對應的 sigma_pixel =====
sigma_mtf_pairs = lookup_sigma_from_mtf(target_table, test1_MTF)
#sigma_1_mtf = mtf_to_sigma(test1_MTF, frequency_lpmm, pixel_size_mm)

# ===== 模糊處理（保留彩色）=====
#img_1_mtf = cv2.GaussianBlur(img_rgb, (0, 0), sigmaX=sigma_1_mtf, sigmaY=sigma_1_mtf)
#img_2_mtf = cv2.GaussianBlur(img_rgb, (0, 0), sigmaX=sigma_2_mtf, sigmaY=sigma_2_mtf)

# ===== 模擬拖影 =====
#img_motion_blur = apply_radial_motion_blur(img_rgb, max_blur_length, edge_percentage, curve)

# ===== 拖影與MTF模糊處理 =====
#img_motion_blur_mtf = cv2.GaussianBlur(img_rgb, (0, 0), sigmaX=sigma_1_mtf, sigmaY=sigma_1_mtf)
#img_motion_blur_mtf = apply_radial_motion_blur(img_motion_blur_mtf, max_blur_length, edge_percentage, curve)


# ===== 顯示結果 =====

# 1. 原圖
#fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
#ax = fig.add_axes([0, 0, 1, 1])
#ax.imshow(img_rgb)
#ax.axis('off')
#fig.savefig(save_path + f"{name}_Original_MTF_Simulation.png", dpi=100)
#plt.close()

# 2. 生成MTF模糊圖
for mtf_value, sigma_mm in sigma_mtf_pairs:
    sigma_pixel = sigma_mm/pixel_size_mm
    img_blurred = cv2.GaussianBlur(img_rgb, (0, 0), sigmaX=sigma_pixel, sigmaY=sigma_pixel)
    
    # 顯示或儲存
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img_blurred)
    ax.axis('off')
    fig.savefig(save_path + f"{name}_{mtf_value}MTF_Blur.png", dpi=100)
    plt.close()
    print(f"Saved: {mtf_value}% MTF → sigma ≈ {sigma_pixel:.4f}")

# 4. 拖影模糊圖
#fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
#ax = fig.add_axes([0, 0, 1, 1])
#ax.imshow(img_motion_blur)
#ax.axis('off')
#fig.savefig(save_path + f"{name}_{max_blur_length}p MotionBlur_Simulation.png", dpi=100)
#plt.close()

# 5. 拖影與MTF模糊圖
#fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
#ax = fig.add_axes([0, 0, 1, 1])
#ax.imshow(img_motion_blur_mtf)
#ax.axis('off')
#fig.savefig(save_path + f"{name}_{max_blur_length}p_motion_{test1_MTF}MTF_BlurSimulation.png", dpi=100)
#plt.close()


# 附註：
# 這是 Tingwei Aug. 4th 提供的 MTF_test_v0.3.py 的修改版本
# 修改內容： 標題編號，在我這邊是第四版了
