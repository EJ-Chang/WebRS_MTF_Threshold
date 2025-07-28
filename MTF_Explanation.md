# MTF處理原理與sigma pixels用途解析

← Back to [[CLAUDE.md]] | Setup: [[HIGH_DPI_SETUP_GUIDE.md]] | Pixel Guide: [[browser_pixel_perfect_guide.md]]

## 🔗 Related Documentation
- **[[CLAUDE.md]]** - Main project overview and system architecture
- **[[HIGH_DPI_SETUP_GUIDE.md]]** - High DPI implementation for precise MTF display
- **[[browser_pixel_perfect_guide.md]]** - Browser optimization for pixel-perfect rendering
- **[[REFACTORING_PLAN.md]]** - Future improvements to MTF processing
- **[[image_test/README.md]]** - Testing tools for MTF image validation

基於 `stimuli_preparation/[OE] MTF_test_v0.3.py` 的技術解析

## MTF核心處理流程

### 1. MTF轉sigma計算原理

```python
def mtf_to_sigma(mtf_percent, frequency_lpmm, pixel_size_mm):
    mtf_ratio = mtf_percent / 100.0
    f = frequency_lpmm  # lp/mm (線對/毫米)
    sigma_mm = np.sqrt(-np.log(mtf_ratio) / (2 * (np.pi * f) ** 2))
    sigma_pixels = sigma_mm / pixel_size_mm
    return sigma_pixels
```

**數學原理**：
- 基於MTF公式：`MTF = exp(-2π²f²σ²)`
- 反推求σ：`σ = √[-ln(MTF) / (2π²f²)]`
- 將毫米單位的σ轉換為像素單位

**參數說明**：
- `mtf_percent`: MTF百分比 (0-100)
- `frequency_lpmm`: 空間頻率 (線對/毫米)
- `pixel_size_mm`: 像素大小 (毫米)

### 2. sigma pixels計算後的主要處理步驟

#### **第一步：計算具體的sigma值**
```python
test1_MTF = 65  # MTF模糊百分比
test2_MTF = 1   # MTF模糊百分比
sigma_1_mtf = mtf_to_sigma(test1_MTF, frequency_lpmm, pixel_size_mm)
sigma_2_mtf = mtf_to_sigma(test2_MTF, frequency_lpmm, pixel_size_mm)
```

#### **第二步：應用高斯模糊處理**
```python
img_1_mtf = cv2.GaussianBlur(img_rgb, (0, 0), sigmaX=sigma_1_mtf, sigmaY=sigma_1_mtf)
img_2_mtf = cv2.GaussianBlur(img_rgb, (0, 0), sigmaX=sigma_2_mtf, sigmaY=sigma_2_mtf)
```

**關鍵參數**：
- `(0, 0)`：讓OpenCV自動計算核心大小
- `sigmaX=sigma_pixels, sigmaY=sigma_pixels`：使用計算出的sigma值進行各向同性模糊

### 3. 進階應用：2AFC實驗

```python
def create_2afc_display(img_rgb, mtf_left, mtf_right, frequency_lpmm, pixel_size_mm):
    # 計算兩個MTF的sigma值
    sigma_left = mtf_to_sigma(mtf_left, frequency_lpmm, pixel_size_mm)
    sigma_right = mtf_to_sigma(mtf_right, frequency_lpmm, pixel_size_mm)
    
    # 對原始圖像進行不同MTF的模糊處理
    img_left = cv2.GaussianBlur(img_rgb, (0, 0), sigmaX=sigma_left, sigmaY=sigma_left)
    img_right = cv2.GaussianBlur(img_rgb, (0, 0), sigmaX=sigma_right, sigmaY=sigma_right)
    
    # 創建並排顯示
    combined_img = np.zeros((h, w*2, 3), dtype=np.uint8)
    combined_img[:, :w] = img_left    # 左半邊
    combined_img[:, w:] = img_right   # 右半邊
```

## sigma pixels的核心用途

### **算出sigma pixels後的主要用途**：

1. **作為高斯模糊的標準差參數**：
   ```python
   cv2.GaussianBlur(image, (0,0), sigmaX=sigma_pixels, sigmaY=sigma_pixels)
   ```

2. **模擬指定MTF值的視覺效果**：
   - 通過控制模糊程度來模擬不同的清晰度水平
   - MTF值越低 → sigma越大 → 圖像越模糊

3. **用於心理物理實驗**：
   - 創建不同清晰度的刺激圖像供受試者比較
   - 支援2AFC (Two Alternative Forced Choice) 實驗設計

### **物理意義**：
- **sigma pixels** 代表高斯核的標準差（以像素為單位）
- 決定了模糊效果的強度：sigma越大，圖像越模糊
- 通過精確的數學計算，確保模糊效果對應到特定的MTF百分比

### **實驗參數範例**：
```python
# 硬體規格
panel_size = 27     # 螢幕大小 (英吋)
panel_resolution_H = 3840     # 水平解析度
panel_resolution_V = 2160     # 垂直解析度
pixel_size_mm = (panel_size * 25.4)/panel_resolution_D     # 像素大小計算
frequency_lpmm = round(panel_resolution_D / (panel_size * 25.4)*0.5*0.6, 2)  # 空間頻率

# MTF測試範例
test1_MTF = 65  # 65% MTF (較清晰)
test2_MTF = 1   # 1% MTF (非常模糊)
```

## 與現有系統的關聯

這個原理正是 `experiments/mtf_utils.py` 中 `apply_mtf_to_image()` 函數所使用的相同技術：

```python
def apply_mtf_to_image(image, mtf_percent, frequency_lpmm=44.25, pixel_size_mm=None):
    # 計算sigma值
    mtf_ratio = mtf_percent / 100.0
    f = frequency_lpmm
    sigma_mm = np.sqrt(-np.log(mtf_ratio) / (2 * (np.pi * f) ** 2))
    sigma_pixels = sigma_mm / pixel_size_mm
    
    # 應用高斯模糊
    img_blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=sigma_pixels, sigmaY=sigma_pixels)
    return img_blurred
```

---

**總結**：sigma pixels是連接理論MTF值與實際圖像模糊效果的關鍵參數，通過精確的數學計算確保心理物理實驗的科學性和可重現性。

*文檔創建時間：2025-01-25*