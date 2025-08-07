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

## TODOs
1. 檢查是什麼地方卡我時間
	1. 檢查繪圖時間
	2. MTF計算時間
	3. ADO計算時間
2. 預先製圖成本多高？
	1. 佔用記憶體？佔用多少？
	2. 可以需要的時候再讀？