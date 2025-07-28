# 🔬 圖片顯示測試工具

← Back to [[CLAUDE.md]] | Image Quality: [[HIGH_DPI_SETUP_GUIDE.md]] | Browser Guide: [[browser_pixel_perfect_guide.md]]

## 🔗 Related Documentation
- **[[CLAUDE.md]]** - Main project overview and image quality strategies
- **[[HIGH_DPI_SETUP_GUIDE.md]]** - High DPI image system setup
- **[[browser_pixel_perfect_guide.md]]** - Browser pixel-perfect display techniques
- **[[MTF_Explanation.md]]** - Technical foundation for image processing
- **[[REFACTORING_PLAN.md]]** - Future improvements to image quality systems

用於測試刺激圖片是否因為Streamlit而被壓縮的純HTML測試頁面。

## 📁 文件結構

```
image_test/
├── index.html          # 主要測試網頁
├── style.css          # 樣式文件
├── simple_server.py   # HTTP服務器腳本
├── README.md          # 使用說明
└── images/            # 刺激圖片目錄
    ├── stimuli_img.png
    ├── text_img.png
    ├── tw_newsimg.png
    ├── us_newsimg.png
    ├── bilingual_news.png
    └── working.png
```

## 🚀 使用方法

### 1. 啟動服務器
```bash
cd image_test
python3 simple_server.py
```

### 2. 開啟瀏覽器
服務器會自動開啟瀏覽器，或手動訪問：
```
http://localhost:8000/index.html
```

### 3. 測試不同模式
- **渲染模式**：切換 pixelated, auto, crisp-edges, smooth
- **縮放比例**：測試原始尺寸、適應容器、放大縮小
- **容器框線**：顯示/隱藏圖片邊界

## 🔍 測試重點

### 與Streamlit比較
1. **圖片清晰度**：是否有明顯的壓縮或模糊
2. **像素精確性**：邊緣是否銳利
3. **顏色保真度**：色彩是否準確
4. **尺寸一致性**：顯示尺寸是否正確

### 與Mac Preview比較
1. **渲染差異**：pixelated vs 系統預設
2. **縮放品質**：不同縮放比例的效果
3. **細節保留**：文字和細節的清晰度
4. **視覺感受**：整體視覺品質差異

## 📊 系統信息

測試頁面會顯示：
- 瀏覽器信息
- 設備像素比 (devicePixelRatio)
- 螢幕解析度
- 圖片原始尺寸 vs 顯示尺寸

## 💡 診斷指南

### 如果圖片在純HTML中也模糊：
- 問題可能來自瀏覽器本身的圖片處理
- 不是Streamlit特有的問題
- 需要調整渲染模式或檢查圖片格式

### 如果圖片在純HTML中清晰：
- 問題可能來自Streamlit的圖片處理機制
- 需要調整Streamlit的圖片顯示方式
- 可能需要繞過Streamlit的圖片壓縮

## 🛠️ 故障排除

### 端口被占用
```bash
python3 simple_server.py 8001  # 使用不同端口
```

### 圖片不顯示
- 檢查 images/ 目錄是否存在
- 確認圖片文件是否完整
- 查看瀏覽器控制台錯誤信息

### 樣式問題
- 清除瀏覽器緩存
- 確認 style.css 文件存在
- 檢查網絡連接

## 📝 測試記錄

建議記錄以下信息：
- 瀏覽器版本
- 操作系統版本
- 螢幕規格
- 設備像素比
- 各種模式下的視覺效果差異

## 🎯 結論判斷

**如果純HTML版本也有壓縮/模糊問題**：
→ 問題來源於瀏覽器圖片處理，而非Streamlit

**如果純HTML版本清晰**：
→ 問題來源於Streamlit的圖片處理機制

這個測試工具幫助您準確定位問題來源，為後續優化提供方向。