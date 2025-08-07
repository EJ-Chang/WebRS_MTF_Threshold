# CLAUDE.md - WebRS_MTF_Threshold

This file provides guidance for working with the WebRS MTF Threshold Streamlit application.

## Quick Start

### Virtual Environment Setup (Required)
The project uses a dedicated Python virtual environment for dependency management:

```bash
# Activate virtual environment (required for all operations)
source psychophysics_env/bin/activate  # Linux/macOS
# or
./psychophysics_env/bin/python  # Direct execution

# Verify installation
./psychophysics_env/bin/python -c "import cv2, numpy, streamlit; print('✅ Dependencies available')"
```

### Local Development
```bash
# Using virtual environment directly (recommended)
./psychophysics_env/bin/python run_app.py

# Or after activating environment
source psychophysics_env/bin/activate
python run_app.py
```

### Streamlit Direct
```bash
./psychophysics_env/bin/streamlit run app.py
# or
source psychophysics_env/bin/activate && streamlit run app.py
```

### Replit Deployment
```bash
python main.py  # Uses system Python in Replit
```

## Key Commands

### Development (All commands require virtual environment)
- `./psychophysics_env/bin/python run_app.py` - Local development (recommended)
- `./psychophysics_env/bin/streamlit run app.py` - Direct Streamlit execution
- `python main.py` - Replit environment (uses system Python)

### Testing
- `./psychophysics_env/bin/python tests/test_basic.py` - Basic functionality tests
- `./psychophysics_env/bin/python tests/test_session_manager.py` - Session state tests
- `./psychophysics_env/bin/python pixel_perfect_test.py` - Image display validation

### Data Management
- `./psychophysics_env/bin/python preview_results.py` - Preview experiment results  
- `./psychophysics_env/bin/python database_manager.py` - Database operations

## Architecture

### Core Application
- `app.py` - Main Streamlit application (135 lines, refactored from 2,174)
- `run_app.py` - Local environment launcher
- `main.py` - Replit environment launcher
- `mtf_experiment.py` - MTF experiment management core

### Modular Structure
- `core/session_manager.py` - Centralized Streamlit session state management
- `core/experiment_controller.py` - Experiment flow and trial progression
- `ui/screens/` - Modular screen system (welcome, instructions, trial, results)
- `ui/components/` - Reusable UI components (buttons, progress indicators)

### Experiment System
- `experiments/ado_utils.py` - Complete ADO engine implementation
- `experiments/mtf_utils.py` - **MTF image processing utilities (v0.4 lookup table system integrated)**
- `experiments/high_dpi_utils.py` - High DPI image processing system

### Data Storage
- `database.py` - PostgreSQL/SQLite database operations
- `csv_data_manager.py` - CSV file management and backup
- `data_manager.py` - Unified data management interface

### Stimulus Preparation Tools
- `stimuli_preparation/[OE] MTF_test_v0.4.py` - Advanced MTF stimulus generation with lookup table system
- `stimuli_preparation/preprocess_mtf_images.py` - **Image preprocessing utilities (v0.4 algorithm integrated)**
- `stimuli_preparation/high_dpi/` - High DPI stimulus variants (2x, 3x scaling)

## ⚠️ CRITICAL: Psychophysical Experiment Requirements

### 🚫 ABSOLUTE PROHIBITION: Image Scaling in Psychophysical Experiments

**NEVER scale, resize, or modify stimulus image dimensions in any way during display.**

#### Why This Is Critical:
- **Scientific Validity**: Scaling destroys the precise MTF calculations and spatial frequency relationships
- **Experimental Accuracy**: Even small scaling changes can invalidate threshold measurements
- **Reproducibility**: Results become non-comparable across different display setups
- **Research Integrity**: Scaling violates fundamental psychophysical experiment principles

#### Implementation Rules:
1. **Images must always display at 1:1 pixel ratio** - no exceptions
2. **Container sizes adapt to image dimensions**, never the reverse
3. **UI layout problems must be solved through spacing and positioning**, not image scaling
4. **All image processing functions must maintain original pixel dimensions**

#### Code Enforcement:
- `ui/components/image_display.py`: Contains safeguards against accidental scaling
- `experiments/mtf_utils.py`: Processes images without size modifications beyond cropping
- All display functions must preserve exact pixel dimensions from stimulus generation

#### If UI Layout Issues Occur:
- ✅ Adjust container spacing and margins
- ✅ Modify button positioning and layout
- ✅ Change page layout and CSS styling
- ❌ **NEVER** scale or resize stimulus images

---

## Configuration

### Experiment Settings (config/settings.py)
- MAX_TRIALS: 45
- MIN_TRIALS: 15
- CONVERGENCE_THRESHOLD: 0.15
- STIMULUS_DURATION: 1.0 seconds
- PRACTICE_TRIAL_LIMIT: 1

### Environment Detection
- **Replit**: PostgreSQL, port 5000
- **Ubuntu Server**: port 3838
- **Local**: SQLite, port 8501

### High DPI System
- Directory: `stimuli_preparation/high_dpi/`
- Levels: 2x, 3x resolutions for pixel-perfect display
- Smart DPI detection and automatic optimization

### MTF Stimulus Generation Tool ([OE] MTF_test_v0.4.py)

**Version Information**: Based on MTF_test_v0.3.py provided by Tingwei (Aug. 4th), enhanced with lookup table system

**Required Configuration Parameters**:
```python
# Line 143: Output filename (without extension)
name = "your_stimulus_name"

# Line 144: Source image file path
image_path = "path/to/your/source_image.png"

# Line 145: Output directory for generated MTF images
save_path = "output/directory/"

# Line 146: Display panel size in inches
panel_size = 27

# Lines 147-148: Panel resolution
panel_resolution_H = 3840    # Horizontal resolution
panel_resolution_V = 2160    # Vertical resolution

# Line 173: List of desired MTF percentages for batch generation
test1_MTF = [80, 60, 40, 20]  # Generates images at these MTF levels
```

**Key Features**:
- **Precise MTF Calculation**: Physics-based sigma computation using optical MTF formula
- **Lookup Table System**: Pre-computed MTF-to-sigma mapping for efficiency
- **Batch Generation**: Creates multiple MTF-blurred images in single run
- **Panel-Specific Calibration**: Automatic pixel size and Nyquist frequency calculation
- **Visual Analysis**: Generates MTF curve plots with marked sigma values

**Usage**:
```bash
cd stimuli_preparation/
# Use virtual environment for standalone execution
../psychophysics_env/bin/python "[OE] MTF_test_v0.4.py"
```

**Output**:
- Individual MTF-blurred images: `{name}_{mtf_value}MTF_Blur.png`
- MTF analysis plots with sigma value annotations

## MTF Algorithm (v0.4) Integration

### 🎯 MTF Lookup Table System (Latest Update)

**Major Performance Upgrade (August 2025)**:
- **🚀 From Direct Calculation to Lookup Table**: MTF processing completely refactored from real-time formula calculation to pre-computed lookup table system
- **10-100x Performance Improvement**: Instant sigma value lookup vs. repeated mathematical computation
- **Initialization Optimization**: Lookup table pre-built during experiment initialization for maximum efficiency
- **Memory Efficient**: Global lookup table reused throughout entire experiment session

**Core Enhancements**:
- **Dynamic Parameter Calculation**: Automatic pixel size and Nyquist frequency computation based on panel specifications
- **Global Lookup Table System**: Pre-computed MTF-to-sigma mapping with 21 precision data points (100%-5%, every 5%)
- **Smart Initialization**: Automatic table building during experiment startup with parameter validation
- **Intelligent Fallback**: Seamless degradation to direct calculation if lookup table fails
- **Boundary Safety**: Automatic handling of extreme MTF values (prevents OpenCV errors)

### Key Functions (experiments/mtf_utils.py)

**New v0.4 Lookup Table Functions**:
```python
# Global lookup table management
initialize_mtf_lookup_table(pixel_size_mm=None, frequency_lpmm=None, force_rebuild=False)
get_sigma_from_mtf_lookup(mtf_percent)  # Fast O(n) lookup
get_mtf_lookup_table_info()  # Table status and diagnostics

# Dynamic parameter calculation
calculate_dynamic_mtf_parameters(panel_size=27, panel_resolution_H=3840, panel_resolution_V=2160)

# Legacy lookup table functions (still available)
sigma_vs_mtf(f_lpmm, pixel_size_mm, sigma_pixel_max=5)
lookup_sigma_from_mtf(target_table, mtf_list)

# Enhanced MTF processing with lookup table integration
apply_mtf_to_image(image, mtf_percent, use_v4_algorithm=True)  # Now uses lookup table
apply_mtf_to_image_v4(image, mtf_percent)  # Direct v0.4 usage with lookup
```

**Algorithm Evolution**:
| Feature | Legacy Algorithm | v0.4 Direct | v0.4 Lookup Table (Current) |
|---------|------------------|-------------|----------------------------|
| Pixel Size | Fixed (0.169333 mm) | Dynamic calculation | Dynamic + Cached |
| Frequency | Fixed (3.0 lp/mm) | Nyquist frequency | Nyquist + Cached |
| Processing | Direct calculation | Direct calculation | Pre-computed lookup |
| Performance | Moderate | Moderate | **10-100x faster** |
| Accuracy | Approximation | Physics-based precision | Physics-based precision |
| Memory | Low | Low | Minimal (21 data points) |
| Initialization | Instant | Instant | **Pre-built during startup** |

### Integration Points

**Main Experiment System** (`mtf_experiment.py`):
- **Automatic Lookup Table Pre-building**: MTF lookup table constructed during experiment initialization
- **Intelligent Parameter Management**: Dynamic parameter calculation with global caching
- **Performance Monitoring**: Real-time lookup table status reporting and diagnostics
- **Robust Fallback Chain**: Lookup table → Direct v0.4 → Legacy algorithm degradation

**Preprocessing Tools** (`preprocess_mtf_images.py`):
- v0.4 algorithm as default for batch image generation
- Performance comparison between algorithms
- Separate output directories for algorithm comparison

### Usage Examples

**Experiment Runtime**:
```python
# Automatic v0.4 usage in experiment
img_stimulus = generate_stimulus_image(mtf_value=45.0)  # Uses v0.4 by default
```

**Manual Processing**:
```python
# Direct v0.4 algorithm usage
from experiments.mtf_utils import apply_mtf_to_image_v4
img_processed = apply_mtf_to_image_v4(base_image, 30.0)

# Algorithm comparison
img_v4 = apply_mtf_to_image(base_image, 30.0, use_v4_algorithm=True)
img_legacy = apply_mtf_to_image(base_image, 30.0, use_v4_algorithm=False)
```

**Batch Processing**:
```bash
# Generate images with v0.4 lookup table algorithm
cd stimuli_preparation/
../psychophysics_env/bin/python preprocess_mtf_images.py  # Uses v0.4 lookup by default
```

### 🧪 Testing Lookup Table System

**Test Basic Functionality**:
```bash
# Test lookup table initialization and performance
./psychophysics_env/bin/python -c "
from experiments.mtf_utils import initialize_mtf_lookup_table, get_mtf_lookup_table_info, get_sigma_from_mtf_lookup
import time

# Initialize lookup table
success = initialize_mtf_lookup_table()
print(f'Lookup table initialized: {success}')

# Check table info
info = get_mtf_lookup_table_info()
print(f'Table size: {info[\"table_size\"]} data points')
print(f'Parameters: pixel_size={info[\"pixel_size_mm\"]:.6f}mm, freq={info[\"frequency_lpmm\"]}lp/mm')

# Performance test
start = time.time()
for mtf in [20, 40, 60, 80]:
    sigma = get_sigma_from_mtf_lookup(mtf)
    print(f'MTF {mtf}% → sigma = {sigma:.4f} pixels')
end = time.time()
print(f'Lookup performance: {(end-start)*1000:.2f}ms for 4 queries')
"
```

**Test Full Integration**:
```bash
# Test complete experiment system with lookup table
./psychophysics_env/bin/python -c "
from mtf_experiment import MTFExperimentManager

# Initialize experiment (will pre-build lookup table)
manager = MTFExperimentManager(max_trials=3, participant_id='lookup_test', is_practice=True)

# Generate trial (uses lookup table)
trial = manager.get_next_trial()
if trial and trial['stimulus_image'] is not None:
    print(f'✅ Trial generated successfully: MTF={trial[\"mtf_value\"]:.1f}%')
    print(f'   Stimulus shape: {trial[\"stimulus_image\"].shape}')
else:
    print('⚠️ Trial generation issue')
"
```

## Important Notes

- **PRODUCTION READY**: v2.2 stable version with modular architecture
- **🚀 MTF LOOKUP TABLE SYSTEM (August 2025)**: **Complete performance overhaul from direct calculation to pre-computed lookup table**
- **MTF ALGORITHM v0.4**: **Integrated advanced MTF processing with dynamic parameters and high-performance lookup system**
- **VIRTUAL ENVIRONMENT REQUIRED**: All local operations must use `./psychophysics_env/bin/python` for dependency management
- **ADO System**: Fully functional with Bayesian optimization
- **High DPI Support**: 144 DPI precision display system implemented
- **Dual Storage**: CSV + Database backup for data reliability
- **Environment Standardization**: Pixel-perfect display through controlled environment
- **Refactoring Complete**: Reduced from monolithic 2,174 lines to clean modular design
- **Performance Optimized**: 10-100x MTF processing speed improvement through lookup table system
- **Algorithm Compatibility**: Supports lookup table (default), direct v0.4, and legacy MTF processing methods

## Troubleshooting

### Virtual Environment Issues

**Common Error**: `ModuleNotFoundError: No module named 'cv2'`
```bash
# Solution: Always use virtual environment
./psychophysics_env/bin/python your_script.py  # Instead of: python your_script.py
```

**Check Dependencies**:
```bash
# Verify all required packages are installed
./psychophysics_env/bin/python -c "
import cv2, numpy, streamlit, pandas, matplotlib
print('✅ All core dependencies available')
print(f'OpenCV: {cv2.__version__}')
print(f'NumPy: {numpy.__version__}')
"
```

**Lookup Table Troubleshooting**:
```bash
# Debug lookup table initialization
./psychophysics_env/bin/python -c "
from experiments.mtf_utils import initialize_mtf_lookup_table, get_mtf_lookup_table_info
import logging
logging.basicConfig(level=logging.DEBUG)

success = initialize_mtf_lookup_table(force_rebuild=True)
info = get_mtf_lookup_table_info()
print(f'Initialization: {success}')
print(f'Table info: {info}')
"
```

### Performance Monitoring

**MTF Processing Performance**:
- **Lookup Table**: ~0.1ms per MTF value
- **Direct v0.4**: ~5-10ms per MTF value  
- **Legacy Algorithm**: ~3-8ms per MTF value

**Memory Usage**:
- **Lookup Table**: ~2KB (21 data points)
- **Base Image Cache**: ~3-8MB per image
- **Total Runtime**: ~15-50MB depending on cache usage

## Documentation Links

- **[[REFACTORING_PLAN.md]]** - Technical debt management and improvement strategy
- **[[replit.md]]** - Deployment configuration and system architecture
- **[[HIGH_DPI_SETUP_GUIDE.md]]** - High DPI image system setup guide
- **[[browser_pixel_perfect_guide.md]]** - Browser optimization for pixel-perfect display
- **[[MTF_Explanation.md]]** - MTF processing principles and technical analysis
- **[[ADO_Early_Termination_Analysis.md]]** - ADO early termination feature assessment
- **[[image_test/README.md]]** - Image display testing tools

## 性能優化進度 (2025年8月)

### 已識別的主要性能瓶頸
1. **st.rerun() 過度使用** ⭐⭐⭐⭐⭐
   - 每個 trial 需要 5-8 次頁面重載 (位置: `trial_screen.py:153,236`)
   - **延遲**: 網站環境下 6-12 秒
   - **原因**: fixation 動畫每 100ms 觸發完整頁面刷新

2. **實時 MTF 圖片生成** ⭐⭐⭐⭐
   - 每張 1600×1600 圖片即時高斯模糊處理 (位置: `mtf_experiment.py:558-584`)
   - **延遲**: 網站環境下 2-5 秒
   - **原因**: 服務器 CPU 資源限制，即使有 v0.4 lookup table 依然需要 OpenCV 處理

3. **ADO 貝葉斯計算** ⭐⭐⭐
   - 95×41×30 網格搜尋互資訊計算 (位置: `ado_utils.py:114`)
   - **延遲**: 網站環境下 1-3 秒
   - **原因**: 116,850 次心理測量函數計算

4. **圖片編碼傳輸** ⭐⭐
   - 7.68MB 圖片無損 PNG 編碼和 Base64 轉換
   - **延遲**: 網站環境下 1-2 秒

### 優化實施計劃

#### 階段一：減少 st.rerun() 使用 (2025-08-07)
- [x] 修改 `trial_screen.py` - 移除 fixation 期間重複 rerun (**已還原** - 不是主要瓶頸)
- [x] 修改 `progress_indicators.py` - 改用 CSS 動畫 (**已實施** - 保留備用)
- [x] **發現**: st.rerun() 不是主要瓶頸，真正問題在圖片編碼
- [x] **風險**: 低 - 不影響實驗精度

#### 階段二：解決真正瓶頸 - Base64 重複編碼 (2025-08-07) ⭐
- [x] **問題識別**: 每次顯示圖片都重複進行 RGB→BGR + PNG編碼 + Base64 轉換
- [x] **位置**: `image_display.py:43-54` 的 `numpy_to_lossless_base64()` 函數
- [x] **延遲**: 網站環境下每次 1-3 秒 (PNG 最大壓縮級別 9)
- [x] **解決方案**: 實施 Base64 預編碼緩存系統
  - [x] 修改 `mtf_experiment.py` - 新增 `generate_and_cache_base64_image()`
  - [x] 修改 `image_display.py` - 支援預編碼 base64 字串
  - [x] 建立 base64 快取機制，避免重複編碼
- [x] **預期效果**: 從每次 1-3 秒降至 <100ms (快取命中時)
- [x] **風險**: 低 - 保持原有圖片品質和像素精度

#### 階段三：MTF 完整預生成系統 (未來執行)  
- [ ] 建立 MTF 圖片庫管理系統
- [ ] 實施按需載入機制 (91 個 MTF 級別，5%-95%)
- [ ] 智能快取策略 (記憶體佔用 ~100MB)
- [ ] **預期效果**: 進一步節省 MTF 計算時間
- [ ] **風險**: 中等 - 需要 200-300MB 磁碟空間

### 記憶體和儲存分析

#### 預生成成本
- **單一刺激圖片的 MTF 庫**: 91 個級別 × 7.68MB = ~700MB (未壓縮)
- **PNG 壓縮後**: 約 200-300MB 磁碟空間
- **智能快取**: 只在記憶體保持 10-15 張圖片 (~100MB RAM)

#### 載入策略
- **選擇性預生成**: 只處理用戶選中的刺激圖片
- **按需載入**: LRU 快取機制，避免全部載入記憶體
- **背景預載**: 根據 ADO 估計預載可能需要的 MTF 值

### 總體目標與實際結果
- **問題根源**: Base64 重複編碼，每次 1-3 秒延遲 (非 st.rerun())
- **現況**: 每個 trial 10+ 秒延遲 (網站環境)
- **階段二實施後**: 預期減少至 **3-5 秒** (Base64 快取命中時)
- **階段三完成後**: 進一步減少至 **2-3 秒** (完整預生成)
- **圖片品質**: ✅ 保持 100% 無損，像素完美顯示

## 技術實施細節

### 🎯 真正瓶頸：Base64 重複編碼問題
```python
# 問題: 每次 trial 都重複編碼 (image_display.py:43-54)
def numpy_to_lossless_base64(image_array):
    image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
    encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 9]  # 最大壓縮 = 慢！
    success, encoded_img = cv2.imencode('.png', image_bgr, encode_params)
    img_base64 = base64.b64encode(encoded_img.tobytes()).decode()  # 1-3秒延遲
    return img_base64

# 解決方案: Base64 預編碼快取
class MTFExperimentManager:
    def generate_and_cache_base64_image(self, mtf_value):
        # 1. 檢查 base64 快取
        if cache_hit: return cached_base64  # <1ms
        
        # 2. 生成 numpy 圖片 (一次)
        img_mtf = self.generate_stimulus_image(mtf_value)
        
        # 3. 編碼並快取 (一次)
        img_base64 = encode_to_base64(img_mtf)
        self.base64_cache[mtf_value] = img_base64
        return img_base64
```

### st.rerun() 優化策略 (已驗證非主要瓶頸)
```python
# 現在: fixation 每 100ms 重載 (保持原有邏輯)
show_animated_fixation(phase_elapsed)  
time.sleep(0.1)
st.rerun()  # 實際影響 < 1 秒

# 備用: CSS 動畫版本 (已實施，可選用)
show_css_fixation_with_timer(duration)  # 純前端，零重載
```

### Base64 快取架構 (已實施)
```python
class MTFExperimentManager:
    def __init__(self):
        self.stimulus_cache = {}      # numpy array 快取
        self.base64_cache = {}        # base64 字串快取 (新增)
        
    def generate_and_cache_base64_image(self, mtf_value):
        # 智能快取策略: numpy → base64 → 顯示
        # 避免重複編碼，大幅提升性能
```