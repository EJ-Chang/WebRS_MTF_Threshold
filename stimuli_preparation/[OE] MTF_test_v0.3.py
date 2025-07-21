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

    ratio = np.clip((distances - start_distance) / (max_distance - start_distance), 0, 1)
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

def create_2afc_display(img_rgb, mtf_left, mtf_right, frequency_lpmm, pixel_size_mm):
    # 計算兩個MTF的sigma值
    sigma_left = mtf_to_sigma(mtf_left, frequency_lpmm, pixel_size_mm)
    sigma_right = mtf_to_sigma(mtf_right, frequency_lpmm, pixel_size_mm)
    
    # 對原始圖像進行不同MTF的模糊處理
    img_left = cv2.GaussianBlur(img_rgb, (0, 0), sigmaX=sigma_left, sigmaY=sigma_left)
    img_right = cv2.GaussianBlur(img_rgb, (0, 0), sigmaX=sigma_right, sigmaY=sigma_right)
    
    # 創建一個新的畫布，寬度是原圖的兩倍
    h, w = img_rgb.shape[:2]
    combined_img = np.zeros((h, w*2, 3), dtype=np.uint8)
    
    # 將兩個圖像並排放置
    combined_img[:, :w] = img_left
    combined_img[:, w:] = img_right
    
    return combined_img

# ===== 參數設定 =====
name = "linepair"
image_path = r"C:\Users\Asus_user\Desktop\Python Code\MTF test pattern\linepair.png"     #圖片位置
save_path = r"C:\Users\Asus_user\Desktop\Python Code\MTF test pattern\\"    #儲存圖片位置
panel_size = 28     #inch
panel_resolution_H = 3840     #水平
panel_resolution_V = 2160     #垂直
panel_resolution_D = (panel_resolution_H**2 + panel_resolution_V**2)**0.5     #對角
pixel_size_mm = (panel_size * 25.4)/panel_resolution_D     # fiexd(panel規格)
frequency_lpmm = round(panel_resolution_D / (panel_size * 25.4)*0.5*0.6, 2)       # fixed(panel規格)

# ===== 設定拖影參數 =====
max_blur_length = 5  # 拖影程度(pixel)
edge_percentage = 30  # 邊緣拖影範圍百分比
curve = 'linear'

# ===== 讀取彩色圖像 =====
img_bgr = cv2.imread(image_path, cv2.IMREAD_COLOR)
if img_bgr is None:
    raise FileNotFoundError(f"Cannot find the image at {image_path}")

img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

# ===== 計算 sigma 值 =====
test1_MTF = 65  #MTF模糊百分比
test2_MTF = 1   #MTF模糊百分比
sigma_1_mtf = mtf_to_sigma(test1_MTF, frequency_lpmm, pixel_size_mm)
sigma_2_mtf = mtf_to_sigma(test2_MTF, frequency_lpmm, pixel_size_mm)

print(f"Sigma for 80% MTF: {sigma_1_mtf:.4f} pixels")
print(f"Sigma for 10% MTF: {sigma_2_mtf:.4f} pixels")
print(f"motion movement for : {max_blur_length} pixels")

# ===== 模糊處理（保留彩色）=====
img_1_mtf = cv2.GaussianBlur(img_rgb, (0, 0), sigmaX=sigma_1_mtf, sigmaY=sigma_1_mtf)
img_2_mtf = cv2.GaussianBlur(img_rgb, (0, 0), sigmaX=sigma_2_mtf, sigmaY=sigma_2_mtf)

# ===== 模擬拖影 =====
img_motion_blur = apply_radial_motion_blur(img_rgb, max_blur_length, edge_percentage, curve)

# ===== 拖影與MTF模糊處理 =====
img_motion_blur_mtf = apply_radial_motion_blur(img_rgb, max_blur_length, edge_percentage, curve)
img_motion_blur_mtf = cv2.GaussianBlur(img_motion_blur_mtf, (0, 0), sigmaX=sigma_1_mtf, sigmaY=sigma_1_mtf)

# ===== 2AFC實驗參數 =====
mtf_left = 20  # 左側MTF百分比
mtf_right = 40  # 右側MTF百分比

# ===== 創建2AFC顯示畫面 =====
img_2afc = create_2afc_display(img_rgb, mtf_left, mtf_right, frequency_lpmm, pixel_size_mm)

# ===== 顯示結果 =====

# 1. 原圖
fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.imshow(img_rgb)
ax.axis('off')
#fig.savefig(save_path + f"{name}_Original_MTF_Simulation.png", dpi=100)
plt.close()

# 2. 第一個MTF模糊圖
fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.imshow(img_1_mtf)
ax.axis('off')
fig.savefig(save_path + f"{name}_{test1_MTF}_MTF_Simulation.png", dpi=100)
plt.close()

# 3. 第二個MTF模糊圖
fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.imshow(img_2_mtf)
ax.axis('off')
fig.savefig(save_path + f"{name}_{test2_MTF}_MTF_Simulation.png", dpi=100)
plt.close()

# 4. 拖影模糊圖
fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.imshow(img_motion_blur)
ax.axis('off')
#fig.savefig(save_path + f"{name}_{max_blur_length}p MotionBlur_Simulation.png", dpi=100)
plt.close()

# 5. 拖影與MTF模糊圖
fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.imshow(img_motion_blur_mtf)
ax.axis('off')
#fig.savefig(save_path + f"{name}_{max_blur_length}p_motion_{test1_MTF}MTF_BlurSimulation.png", dpi=100)
plt.close()

# ===== 顯示2AFC結果 =====
fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.imshow(img_2afc)
ax.axis('off')
fig.savefig(save_path + f"{name}_2AFC_{mtf_left}vs{mtf_right}_MTF.png", dpi=100)
plt.close()