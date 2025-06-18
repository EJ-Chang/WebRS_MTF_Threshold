# 4K螢幕Pixel-Perfect設定指南

## 系統設定

### Windows 4K螢幕設定
1. **顯示設定** → **縮放與版面配置** → 設定為 **100%**
2. **進階縮放設定** → 關閉 "讓Windows嘗試修正應用程式，使其不會模糊"

### macOS 4K螢幕設定  
1. **系統偏好設定** → **顯示器** → 選擇 **縮放** → **更多空間**
2. 或使用 **預設解析度** 而非 **最佳的Retina顯示器**

### 瀏覽器設定

#### Chrome/Edge
1. 設定 → 外觀 → 頁面縮放 → **100%**
2. 網址列輸入: `chrome://settings/` → 進階 → 重設設定
3. **關鍵：** 按 `Ctrl+0` (Windows) 或 `Cmd+0` (Mac) 重設縮放

#### Firefox  
1. 檢視 → 縮放 → **僅縮放文字** (取消勾選)
2. 縮放設定為 **100%**
3. `about:config` → `layout.css.devPixelsPerPx` → 設為 **1.0**

## 實驗前檢查清單

### 1. 檢查Device Pixel Ratio
開啟瀏覽器開發者工具 (F12)，在Console輸入：
```javascript
console.log('Device Pixel Ratio:', window.devicePixelRatio);
verifyPixelPerfect(); // 使用我們的驗證函數
```

**目標：** `devicePixelRatio` 應該等於 1.0

### 2. 驗證圖像尺寸
在實驗頁面上查看顯示的信息：
- **Target:** 應顯示預期的像素尺寸 (如 800×600px)
- **DPR:** 應顯示 1.0
- **Console log:** 應顯示 "Pixel perfect: true"

### 3. 測量實際尺寸 (進階)
使用螢幕測量工具確認：
- Windows: 內建的「小畫家」尺規功能
- macOS: 數位色彩測量儀 或 PixelStick app
- 線上工具: ruler.onl

## 常見問題解決

### 問題1: DPR不等於1
**原因：** 系統或瀏覽器縮放啟用
**解決：** 
- 檢查系統顯示縮放設定
- 重設瀏覽器縮放 (Ctrl+0 / Cmd+0)
- 重新啟動瀏覽器

### 問題2: 圖像仍然被縮放
**原因：** CSS being overridden
**解決：**
- F12 檢查圖像元素的computed style
- 確認 width/height 顯示為目標像素值
- 檢查是否有其他CSS規則影響

### 問題3: 不同瀏覽器顯示不同
**原因：** 瀏覽器預設行為差異
**解決：**
- 建議使用 Chrome 或 Edge (Chromium-based)
- 避免使用 Safari (macOS縮放行為複雜)

## 推薦實驗設定

### 最佳配置
- **螢幕：** 4K @ 100% 縮放
- **瀏覽器：** Chrome @ 100% 縮放  
- **解析度：** 3840×2160 (原生4K)
- **檢查：** DPR = 1.0

### 替代配置 (如果無法達成100%縮放)
- **螢幕：** 1920×1080 外接螢幕
- **說明：** 使用FHD螢幕可完全避免縮放問題

## 驗證Pixel-Perfect顯示

在實驗執行前，請：
1. 確認DPR顯示為1.0
2. 使用 `verifyPixelPerfect()` 檢查
3. 目視確認圖像清晰度沒有模糊
4. 如有疑慮，使用測量工具驗證實際像素尺寸

**注意：** Pixel-perfect顯示對心理物理學實驗至關重要，任何縮放都可能影響實驗結果的有效性。