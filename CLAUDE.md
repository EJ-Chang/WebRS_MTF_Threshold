# CLAUDE.md - WebRS_MTF_Threshold

This file provides guidance for working with the WebRS MTF Threshold Streamlit application.

## Quick Start

### Local Development
```bash
python run_app.py
```

### Streamlit Direct
```bash
streamlit run app.py
```

### Replit Deployment
```bash
python main.py
```

## Key Commands

### Development
- `python run_app.py` - Local development (recommended)
- `streamlit run app.py` - Direct Streamlit execution
- `python main.py` - Replit environment

### Testing
- `python tests/test_basic.py` - Basic functionality tests
- `python tests/test_session_manager.py` - Session state tests
- `python pixel_perfect_test.py` - Image display validation

### Data Management
- `python preview_results.py` - Preview experiment results
- `python database_manager.py` - Database operations

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
- `experiments/mtf_utils.py` - **MTF image processing utilities (v0.4 algorithm integrated)**
- `experiments/high_dpi_utils.py` - High DPI image processing system

### Data Storage
- `database.py` - PostgreSQL/SQLite database operations
- `csv_data_manager.py` - CSV file management and backup
- `data_manager.py` - Unified data management interface

### Stimulus Preparation Tools
- `stimuli_preparation/[OE] MTF_test_v0.4.py` - Advanced MTF stimulus generation with lookup table system
- `stimuli_preparation/preprocess_mtf_images.py` - **Image preprocessing utilities (v0.4 algorithm integrated)**
- `stimuli_preparation/high_dpi/` - High DPI stimulus variants (2x, 3x scaling)

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
python "[OE] MTF_test_v0.4.py"
```

**Output**:
- Individual MTF-blurred images: `{name}_{mtf_value}MTF_Blur.png`
- MTF analysis plots with sigma value annotations

## MTF Algorithm (v0.4) Integration

### 🎯 New MTF Processing System

**Core Enhancements**:
- **Dynamic Parameter Calculation**: Automatic pixel size and Nyquist frequency computation based on panel specifications
- **Lookup Table System**: Pre-computed MTF-to-sigma mapping for consistent and efficient processing
- **Batch Processing**: Optimized for multiple MTF levels generation
- **Backwards Compatibility**: Maintains support for legacy algorithm

### Key Functions (experiments/mtf_utils.py)

**New v0.4 Functions**:
```python
# Dynamic parameter calculation
calculate_dynamic_mtf_parameters(panel_size=27, panel_resolution_H=3840, panel_resolution_V=2160)

# Lookup table system
sigma_vs_mtf(f_lpmm, pixel_size_mm, sigma_pixel_max=5)
lookup_sigma_from_mtf(target_table, mtf_list)

# Enhanced MTF processing with algorithm selection
apply_mtf_to_image(image, mtf_percent, use_v4_algorithm=True)  # Default: v0.4
apply_mtf_to_image_v4(image, mtf_percent)  # Direct v0.4 usage
```

**Algorithm Comparison**:
| Feature | Legacy Algorithm | v0.4 Algorithm |
|---------|------------------|----------------|
| Pixel Size | Fixed (0.169333 mm) | Dynamic calculation |
| Frequency | Fixed (3.0 lp/mm) | Nyquist frequency |
| Processing | Direct calculation | Lookup table |
| Accuracy | Approximation | Physics-based precision |

### Integration Points

**Main Experiment System** (`mtf_experiment.py`):
- Automatic v0.4 algorithm selection for stimulus generation
- Dynamic parameter initialization during experiment setup
- Fallback support for environments without full v0.4 utilities

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
# Generate images with v0.4 algorithm
cd stimuli_preparation/
python preprocess_mtf_images.py  # Uses v0.4 by default
```

## Important Notes

- **PRODUCTION READY**: v2.2 stable version with modular architecture
- **MTF ALGORITHM v0.4**: **Integrated advanced MTF processing with dynamic parameters and lookup table system**
- **ADO System**: Fully functional with Bayesian optimization
- **High DPI Support**: 144 DPI precision display system implemented
- **Dual Storage**: CSV + Database backup for data reliability
- **Environment Standardization**: Pixel-perfect display through controlled environment
- **Refactoring Complete**: Reduced from monolithic 2,174 lines to clean modular design
- **Algorithm Compatibility**: Supports both v0.4 (default) and legacy MTF processing methods

## Documentation Links

- **[[REFACTORING_PLAN.md]]** - Technical debt management and improvement strategy
- **[[replit.md]]** - Deployment configuration and system architecture
- **[[HIGH_DPI_SETUP_GUIDE.md]]** - High DPI image system setup guide
- **[[browser_pixel_perfect_guide.md]]** - Browser optimization for pixel-perfect display
- **[[MTF_Explanation.md]]** - MTF processing principles and technical analysis
- **[[ADO_Early_Termination_Analysis.md]]** - ADO early termination feature assessment
- **[[image_test/README.md]]** - Image display testing tools