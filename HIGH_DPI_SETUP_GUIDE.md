# 高DPI圖片系統設置指南

← Back to [[CLAUDE.md]] | Related: [[browser_pixel_perfect_guide.md]] | Technical: [[MTF_Explanation.md]]

## 🔗 Related Documentation
- **[[CLAUDE.md]]** - Main project overview and system architecture
- **[[browser_pixel_perfect_guide.md]]** - Complementary browser optimization techniques
- **[[MTF_Explanation.md]]** - Technical foundation for image processing
- **[[REFACTORING_PLAN.md]]** - Future improvements to the high DPI system
- **[[image_test/README.md]]** - Testing tools for validating DPI improvements

## 概述

這個指南說明如何使用新實現的高DPI圖片系統來達成144 DPI精緻顯示效果。

## 系統架構

### 目錄結構
```
stimuli_preparation/
├── standard/           # 標準解析度圖片
├── high_dpi/
│   ├── 2x/            # 2倍解析度圖片
│   ├── 3x/            # 3倍解析度圖片  
│   └── original/      # 原始高解析度圖片
└── preprocess_mtf_images.py
```

### 核心模組
- `experiments/high_dpi_utils.py` - 高DPI圖片處理工具
- `ui/screens/stimuli_preview_screen.py` - 預覽界面（已更新支援高DPI）

## 使用方法

### 1. 準備高DPI圖片

#### 方法A: 使用Mac截圖工具（推薦）
1. 在Mac上使用截圖工具以2倍解析度截取圖片
2. 確保圖片DPI為144
3. 將圖片放置在 `stimuli_preparation/high_dpi/2x/` 目錄

#### 方法B: 批次轉換
```python
from experiments.high_dpi_utils import batch_convert_to_high_dpi

# 批次轉換所有圖片為2x版本
results = batch_convert_to_high_dpi("standard", "2x")
```

### 2. 在預覽界面中使用

1. 啟動應用程式並進入刺激預覽畫面
2. 勾選「🔍 高DPI預覽」選項
3. 勾選「📏 1/2濃縮」來體驗144 DPI精緻效果
4. 系統會自動檢測最佳DPI等級並載入相應圖片

### 3. DPI檢測邏輯

系統會根據以下邏輯自動選擇最佳DPI等級：

```python
# 高信賴度檢測 (confidence > 0.7)
if dpi >= 200:    # Retina顯示器 (如220 DPI)
    return "3x"
elif dpi >= 120:  # 中等DPI顯示器
    return "2x"  
else:             # 標準DPI顯示器 (72, 96 DPI)
    return "standard"

# 低信賴度時保守選擇
if dpi >= 150:
    return "2x"
else:
    return "standard"
```

## 核心功能

### 高DPI圖片載入
```python
from experiments.high_dpi_utils import load_and_prepare_high_dpi_image

# 自動檢測最佳DPI版本
high_dpi_img = load_and_prepare_high_dpi_image('stimuli_img.png')

# 指定DPI等級
high_dpi_img = load_and_prepare_high_dpi_image('stimuli_img.png', target_dpi='2x')
```

### 1/2濃縮預覽
```python
from experiments.high_dpi_utils import create_high_dpi_preview

# 創建壓縮預覽（瀏覽器會進行高品質放大）
compressed_img = create_high_dpi_preview(
    high_dpi_img, 
    scale_factor=0.5,
    add_info_overlay=True
)
```

### DPI資訊檢測
```python
from experiments.high_dpi_utils import get_image_dpi_info

# 獲取圖片DPI資訊
info = get_image_dpi_info('path/to/image.png')
print(f"DPI: {info['dpi_x']}x{info['dpi_y']}")
```

## 與現有系統整合

### MTF處理
```python
from experiments.high_dpi_utils import apply_mtf_to_high_dpi_image

# 對高DPI圖片套用MTF濾鏡，自動調整參數
mtf_img = apply_mtf_to_high_dpi_image(high_dpi_img, mtf_percent=30.0)
```

### 校準系統整合
高DPI系統完全整合現有的校準系統：
- 自動使用校準系統檢測的DPI值
- 根據檢測信賴度調整策略
- 支援手動校準結果

## 瀏覽器高品質顯示原理

### GUI設計師經驗應用
1. **高DPI圖片源**: 準備2x或3x解析度的圖片
2. **CSS尺寸控制**: 在HTML/CSS中設定顯示為實際需要的大小
3. **瀏覽器縮放**: 讓瀏覽器自動進行高品質向下縮放

### 實現細節
```python
# 載入2x圖片 (如 800x600)
high_dpi_img = load_high_dpi_image('stimulus.png')

# 壓縮為1/2尺寸 (400x300)
compressed_img = create_high_dpi_preview(high_dpi_img, scale_factor=0.5)

# 在Streamlit中顯示，瀏覽器會將400x300放大顯示
# 由於原始圖片是高DPI，放大後仍保持精緻效果
display_mtf_stimulus_image(compressed_img)
```

## 故障排除

### 常見問題

1. **高DPI圖片不存在**
   - 系統會自動回退到標準圖片
   - 檢查 `stimuli_preparation/high_dpi/2x/` 目錄是否有相應圖片

2. **DPI檢測失敗**
   - 系統會使用預設2x等級
   - 可進入校準畫面手動校準

3. **預覽效果不佳**
   - 確認瀏覽器縮放設定為100%
   - 檢查顯示器是否支援高DPI

### 除錯資訊
```python
from experiments.high_dpi_utils import detect_optimal_dpi_level

# 檢查系統檢測的DPI等級
dpi_level = detect_optimal_dpi_level()
print(f"建議DPI等級: {dpi_level}")
```

## 性能考量

- 高DPI圖片載入時間略長，但在可接受範圍內
- 1/2濃縮預覽可減少傳輸和顯示負擔
- 系統會快取檢測結果以提升性能

## 未來擴展

1. **自動批次轉換**: 實現自動從標準圖片生成高DPI版本
2. **更多DPI等級**: 支援更細緻的DPI等級劃分
3. **實時品質檢測**: 實時檢測顯示品質並動態調整

---

**更新日期**: 2025-07-23  
**版本**: 1.0  
**相關文件**: CLAUDE.md

---

## 🔗 Navigation
- **← Back to [[CLAUDE.md]]** - Return to main project documentation
- **🌐 Browser Guide: [[browser_pixel_perfect_guide.md]]** - Complementary browser optimization techniques
- **🧬 Technical Foundation: [[MTF_Explanation.md]]** - Understanding image processing requirements
- **🔧 Future Plans: [[REFACTORING_PLAN.md]]** - Planned improvements to high DPI system
- **🧪 Testing: [[image_test/README.md]]** - Validate high DPI improvements