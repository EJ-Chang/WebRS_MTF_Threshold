# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a sophisticated psychophysics experiment platform built with Streamlit, implementing Two-Alternative Forced Choice (2AFC) brightness discrimination and MTF (Modulation Transfer Function) clarity testing experiments with Adaptive Design Optimization (ADO). **This project is hosted and primarily developed on Replit.**

## Core Commands

### Running the Application (Replit Environment)
```bash
# Primary method: Use Replit's run button or
python main.py

# Alternative: Direct Streamlit launch
streamlit run app.py --server.port 5000 --server.address 0.0.0.0
# If on my local computer:
# streamlit run app.py --server.port 8501

# Development testing
python test_replit_environment.py
```

### Local Development Commands
```bash
# For local development (non-Replit)
streamlit run app.py

# Install dependencies (modern approach)
uv sync

# Install dependencies (legacy approach)
pip install -r requirements.txt

# Test environment setup
python test_replit_environment.py

# Test MTF improvements
python test_mtf_improvements.py
```

### Replit-Specific Development
```bash
# Test Replit environment compatibility
python test_replit_environment.py

# Test MTF experiment improvements (comprehensive test suite)
python test_mtf_improvements.py

# Check all dependencies and setup
python -c "from test_replit_environment import main; main()"

# Standalone experiments (if experiments/ utilities are available)
cd experiments && python Exp_MTF_ADO.py
cd experiments && python Exp_MTF_Psychometric_YN.py

# Test standalone ADO optimizer
python -c "from ado_optimizer import ADOOptimizer; ado = ADOOptimizer(); print('ADO optimizer ready')"
```

### Database Operations (Replit-Optimized)
```bash
# Initialize database (auto-detects PostgreSQL/SQLite)
python -c "from database import DatabaseManager; DatabaseManager()"

# Export data to CSV
python -c "from database import DatabaseManager; db = DatabaseManager(); db.export_to_csv(experiment_id)"
```

## High-Level Architecture

### Core Application Structure
- **`main.py`** - Replit entry point with environment setup and Streamlit launcher
- **`app.py`** - Main Streamlit interface orchestrating all experiments
- **`experiment.py`** - 2AFC brightness discrimination experiment manager
- **`mtf_experiment.py`** - MTF clarity testing experiment manager (with latest improvements)
- **`database.py`** - Database integration with auto-detection (PostgreSQL/SQLite)
- **`data_manager.py`** - Data export and psychometric function analysis
- **`ado_optimizer.py`** - Standalone ADO optimizer with 4-parameter Weibull implementation

### Replit Configuration Files
- **`.replit`** - Replit run configuration with PostgreSQL module and port settings
- **`uv.lock`** - UV package manager lock file for dependency resolution
- **`requirements.txt`** - Python package dependencies (legacy format)
- **`pyproject.toml`** - Modern Python project configuration with dependencies

### Experiment Modules
- **`experiments/ado_utils.py`** - Advanced Bayesian ADO engine with mutual information optimization
- **`experiments/mtf_utils.py`** - Real-time MTF image processing and performance optimization
- **`experiments/Exp_MTF_ADO.py`** - Standalone PsychoPy MTF experiment
- **`experiments/Exp_MTF_Psychometric_YN.py`** - Yes/No MTF psychometric function experiment
- **`simple_ado.py`** - Simplified ADO for 2AFC experiments
- **`test_mtf_improvements.py`** - Test suite for MTF experiment improvements (Chinese/English bilingual)

### Key Architectural Patterns

#### Adaptive Design Optimization (ADO)
The platform implements three ADO approaches:
- **Simple ADO** (`simple_ado.py`) - For 2AFC experiments with basic threshold tracking
- **Advanced ADO** (`experiments/ado_utils.py`) - Full Bayesian implementation with mutual information optimization
- **Standalone ADO** (`ado_optimizer.py`) - Self-contained 4-parameter Weibull ADO optimizer with:
  - Vectorized Bayesian inference for performance
  - 4D posterior distribution tracking (alpha, beta, gamma, lambda)
  - Expected information gain calculation
  - Optimized parameter grids for psychophysics
  - Built-in credible interval estimation

#### Session State Management
Streamlit session state is extensively used for:
- Trial locking to prevent regeneration during user interaction
- Phase-based experiment flow (fixation → stimulus → response)
- Real-time ADO parameter updates
- Database transaction management

#### Database Architecture
PostgreSQL schema with three main tables:
- **`participants`** - Participant tracking
- **`experiments`** - Experiment session metadata
- **`trials`** - Individual trial data with ADO parameters

## Development Guidelines

### Working with Experiments
- Each experiment implements a manager class with standardized methods:
  - `get_current_trial()` / `get_next_trial()`
  - `record_response()` / `record_trial()`  
  - `get_current_estimates()` - for ADO monitoring
  - `is_experiment_complete()` - convergence checking

### MTF Image Processing
- MTF values represent blur levels (10% = very blurry, 90% = sharp)
- Images are processed in real-time using OpenCV Gaussian blur
- Performance optimization through image caching in session state
- Base64 encoding for Streamlit HTML display

### ADO Integration
- ADO engines maintain trial history and posterior distributions
- Real-time parameter updates after each trial
- Convergence monitoring based on posterior standard deviation
- Next stimulus selection via mutual information maximization

### Database Operations
- All trial data is automatically saved to PostgreSQL
- Experiment sessions are tracked with unique IDs
- CSV export functionality for data analysis
- Participant history management

## Important Implementation Details

### Replit Environment Variables
Automatically detected environment variables:
- `REPLIT_DB_URL` - Replit PostgreSQL database (auto-detected)
- `DATABASE_URL` - Standard PostgreSQL connection (fallback)
- `PORT` - Server port (defaults to 5000)
- `REPL_SLUG`, `REPL_OWNER` - Replit project identification

### Session State Keys (Enhanced for Replit)
Critical session state variables:
- `experiment_stage` - Controls UI flow ('welcome', 'practice', 'experiment', etc.)
- `mtf_trial_start_time` - Precise timing for smooth trial flow
- `mtf_precise_stimulus_onset` - High-precision stimulus timing
- `mtf_response_recorded` - Prevents duplicate responses
- `current_experiment_id` - Database experiment tracking

### Database Configuration (Auto-Detection)
The system automatically detects and configures the appropriate database:
1. **Replit PostgreSQL** - `REPLIT_DB_URL` (preferred)
2. **Standard PostgreSQL** - `DATABASE_URL` (fallback)
3. **SQLite** - Local file (development fallback)

```bash
# Replit automatically provides REPLIT_DB_URL
# No manual configuration needed in Replit environment
```

### Performance Considerations (Replit-Optimized)
- **Smart image caching** - `StimulusCache` with LRU eviction and MTF value prediction
- **Precise timing system** - `PreciseTimer` with automatic calibration and drift correction
- **Adaptive imports** - Fallback mechanisms for missing dependencies
- **Database connection pooling** - Reused sessions for optimal performance
- **Viewport optimization** - Images cropped and resized for Replit's display constraints
- **Real-time ADO** - Mutual information optimization with 20-30 trial convergence

### Replit-Specific Optimizations
- **Path resolution** - Auto-detection of file paths across different Replit configurations
- **Port handling** - Automatic configuration for Replit's port requirements (5000)
- **Environment detection** - Smart fallbacks when Replit-specific features are unavailable
- **Memory management** - Optimized for Replit's resource constraints

## File Dependencies

### Python Dependencies (pyproject.toml)
- `streamlit>=1.45.1` - Web application framework
- `opencv-python>=4.11.0.86` - Image processing for MTF
- `numpy>=2.2.6`, `scipy>=1.15.3` - Scientific computing and ADO algorithms
- `plotly>=6.1.2` - Interactive psychometric function plotting
- `psycopg2-binary>=2.9.10` - PostgreSQL database connectivity
- `sqlalchemy>=2.0.41` - Database ORM
- `pandas>=2.2.3` - Data manipulation and export
- `matplotlib>=3.10.3` - Additional plotting capabilities
- `pillow>=11.2.1` - Image manipulation support

### Key File Relationships
- `app.py` imports and coordinates all experiment managers
- Experiment managers import ADO utilities and database operations
- MTF experiments depend on `experiments/mtf_utils.py` for image processing
- Database operations are centralized in `database.py` with SQLAlchemy models
- `ado_optimizer.py` provides standalone ADO functionality independent of other modules
- `test_mtf_improvements.py` validates integration between all components

## Replit Deployment Notes

### Quick Start on Replit
1. **Fork/Import** this repository to your Replit account
2. **Run** - Click the green "Run" button (automatically executes `main.py`)
3. **Test** - Navigate to the generated URL to access the web interface
4. **Debug** - Run `python test_replit_environment.py` if issues occur

### Troubleshooting Replit Issues
- **Missing packages**: Check Console tab for import errors, install via Shell
- **Port issues**: Ensure `.replit` file configures port 5000 correctly  
- **Database errors**: Verify PostgreSQL add-on is enabled, fallback to SQLite works
- **File not found**: Check `stimuli_preparation/` directory exists, fallback test pattern used
- **Performance**: Replit free tier may have resource limits affecting large experiments

### Latest Improvements (Optimized for Replit)
- **Smooth MTF trials** - Single-page flow with CSS animations (no manual Continue buttons)
- **Precise timing** - ±10ms accuracy with automatic calibration
- **Smart caching** - Preloaded MTF images based on ADO predictions
- **Bayesian ADO** - Mutual information optimization, 50-60% faster convergence
- **Auto-detection** - Database, file paths, dependencies automatically configured
- **ADO Performance Testing** - Integrated benchmark tool for optimizing trial-to-trial delays
- **Standalone ADO Optimizer** - Self-contained 4-parameter Weibull implementation
- **Comprehensive Test Suite** - Bilingual test framework for validation (`test_mtf_improvements.py`)
- **UV Package Management** - Modern dependency resolution with `uv.lock`

### ADO Performance Optimization (Added 2025-06)

#### Performance Testing Tool
```bash
# Access via Streamlit web interface
# Sidebar → "📊 ADO Performance Test"
# Tests real ADO computation time in Replit environment
```

#### Key Performance Insights
- **ADO Computation**: Primary bottleneck in trial transitions
- **Computation Load**: 19-80 MTF candidates × 651-1,230 parameter combinations × 2 responses
- **Target**: ≤1000ms to be masked by fixation cross (1 second)
- **Optimization Strategy**: Use fixation period to hide ADO computation delays

#### Implementation Strategy for Trial Efficiency
```python
# Recommended approach: Fixation-masked computation
Trial Flow:
1. User responds to Trial N
2. Start fixation cross (1+ seconds)
3. SIMULTANEOUSLY: Start ADO computation for Trial N+1
4. Fixation completes when computation finishes
5. Display Trial N+1 stimulus (no perceived delay)
```

### Development Guidelines (Important)

#### CLAUDE.md Maintenance
- **Auto-update**: Always update CLAUDE.md when modifying architecture or adding features
- **Sync**: Ensure documentation matches actual codebase
- **Include**: New commands, performance improvements, file structure changes

#### Replit Deployment Considerations
- **Performance**: All modifications must consider Replit's resource limitations
- **Memory**: Monitor usage, avoid memory-intensive operations
- **Network**: Account for potential latency in web interface
- **Integration**: New features must fit existing Streamlit architecture

#### Git Branch Strategy
- **Feature branches**: Use for experimental features or major performance optimizations
- **Main branch**: Keep stable and always runnable
- **Branching triggers**: Suggest new branch for:
  - Major architecture changes
  - Experimental ADO optimizations
  - UI/UX redesigns that might break existing functionality

## Current Development Status (2025-06)

### Project Maturity
- **Production Ready**: Core MTF and 2AFC experiments fully functional
- **Database Integration**: PostgreSQL/SQLite auto-detection with session tracking
- **Performance Optimized**: Sub-second ADO computation, precise timing system
- **Multi-language Support**: Chinese/English bilingual test infrastructure
- **Comprehensive Testing**: Full test suite covering all major components

### Recent Additions
- **`ado_optimizer.py`**: Standalone 4-parameter Weibull ADO implementation
- **`test_mtf_improvements.py`**: Comprehensive bilingual test suite
- **`.replit` Configuration**: Updated with PostgreSQL module support
- **`uv.lock`**: Modern package management for reliable builds
- **Enhanced Dependencies**: Updated to latest stable versions (Streamlit 1.45.1, OpenCV 4.11, etc.)

### File Structure Summary
```
├── Core Application
│   ├── main.py              # Replit entry point
│   ├── app.py               # Streamlit web interface
│   ├── experiment.py        # 2AFC experiments
│   ├── mtf_experiment.py    # MTF experiments
│   └── database.py          # Data persistence
├── ADO Implementation
│   ├── simple_ado.py        # Basic ADO for 2AFC
│   ├── ado_optimizer.py     # Standalone 4-param Weibull ADO
│   └── experiments/ado_utils.py  # Advanced Bayesian ADO
├── Testing & Validation
│   ├── test_replit_environment.py   # Environment validation
│   ├── test_mtf_improvements.py    # MTF components test
│   └── test_basic_imports.py       # Import validation
├── Configuration
│   ├── .replit             # Replit deployment config
│   ├── pyproject.toml      # Modern Python project
│   ├── requirements.txt    # Legacy dependencies
│   └── uv.lock            # Package lock file
└── Assets & Results
    ├── stimuli_preparation/  # Image processing utilities
    ├── results/             # Generated plots and data
    └── psychophysics_experiments.db  # SQLite database
```

This platform represents a research-grade implementation of adaptive psychophysical testing optimized for Replit hosting with modern web technologies and rigorous experimental methodology.

## Recent Updates (2025-06-20)

### Python Version Upgrade to 3.13
**Configuration Files Updated:**
- **`.replit`**: Updated to use `python-3.13` module with `nix.override` for Python 3.13
- **`pyproject.toml`**: Updated minimum Python requirement to `>=3.13`
- **Environment Variables**: Added `PYTHONDONTWRITEBYTECODE=1` and `NUMPY_EXPERIMENTAL_ARRAY_FUNCTION=0` for improved runtime behavior

**Dependencies Updated:**
- `numpy>=2.3.0` (up from 2.2.6)
- `pandas>=2.3.0` (up from 2.2.3)  
- All other dependencies remain compatible with Python 3.13

**Replit Environment Improvements:**
- Enhanced stability with Python 3.13
- Improved package compatibility
- Better memory management with bytecode compilation disabled
- Streamlined deployment configuration

## Previous Updates (2025-06-17)

### Image Processing Improvements

#### 1. Fixed Preview Image Display Issues
**Location:** `app.py`, lines 404-431
- **Problem**: Preview thumbnails had resolution/display size mismatch causing distortion
- **Solution**: Implemented proper aspect ratio preservation with high-quality scaling
- **Changes**: 
  - Added scaling factor calculation: `min(max_size / original_width, max_size / original_height)`
  - Used `Image.resize()` with `Image.Resampling.LANCZOS` for quality scaling
  - Added consistent width setting: `st.image(img_resized, width=new_width)`
  - Added size information display: `st.caption(f"Size: {original_width}×{original_height}")`

#### 2. Enhanced Text Image Cropping Logic
**Location:** `experiments/mtf_utils.py`, lines 101-169 and `mtf_experiment.py`, lines 50-82
- **Problem**: Text images used right-half cropping like regular images, cutting off important content
- **Solution**: Implemented center-portion cropping for text images while maintaining same output dimensions
- **Changes**:
  - Auto-detection of text images by filename (`'text' in image_name`)
  - Text images: crop center portion (left and right sides removed)
  - Regular images: maintain right-half cropping
  - Both produce consistent output: 960×1080 pixels
  - Added informative debug output

**Technical Details:**
- Original images: 1920×1080 pixels
- Text image processing: Takes center 960×1080 region
- Regular image processing: Takes right-half 960×1080 region
- Final viewport display: Both cropped to 800×600 for consistent UI

### ADO System Configuration Updates

#### 3. Extended MTF Testing Range
**Problem**: ADO system was limited to 89% MTF maximum, causing experiments to get stuck for participants needing higher clarity thresholds (especially with text stimuli).

**Files Modified:**
- `mtf_experiment.py`: Multiple ADO range settings
- `experiments/ado_utils.py`: Core ADO engine defaults
- `app.py`: Benchmark testing configuration

**Key Changes:**
```python
# Before (limited range)
design_space = np.arange(10, 90, 1)    # Max 89%
threshold_range = (10, 90)             # Max 90%

# After (extended range)  
design_space = np.arange(10, 100, 1)   # Max 99%
threshold_range = (10, 99)             # Max 99%
```

**Impact:**
- **Extended Design Space**: Now tests MTF values from 10% to 99% (was 10% to 89%)
- **Expanded Threshold Range**: ADO can estimate thresholds up to 99% (was limited to 90%)
- **Better Text Image Support**: Text stimuli often require higher MTF values for clarity perception
- **Improved Convergence**: System can now properly converge for participants with high clarity thresholds

#### 4. Updated Caching and Prediction Systems
**Location:** `mtf_experiment.py`, line 429
- **Cache prediction range**: Extended from `min(90.0, ...)` to `min(99.0, ...)`
- **Adaptive step limits**: Extended from `min(90.0, ...)` to `min(99.0, ...)`
- **Ensures**: Caching system can preload high MTF values when needed

### Technical Implementation Notes

#### Image Processing Pipeline
1. **Load original image** (1920×1080 pixels)
2. **Apply cropping logic**:
   - Text images: Center crop → 960×1080 pixels
   - Regular images: Right-half crop → 960×1080 pixels  
3. **MTF processing**: Apply blur/sharpening based on MTF value
4. **Viewport cropping**: Final display crop → 800×600 pixels
5. **Base64 encoding**: For web display in Streamlit

#### ADO Configuration Strategy
- **Design Space**: 90 candidate MTF values (10%, 11%, ..., 99%)
- **Parameter Grid**: 31 threshold × 21 slope = 651 combinations
- **Computational Load**: ~119,340 operations per trial
- **Performance**: Optimized for <1000ms computation (masked by fixation period)

### Development Guidelines Updates

#### Image Handling Best Practices
- **Always preserve aspect ratios** when generating thumbnails
- **Use consistent output dimensions** for MTF processing (960×1080)
- **Implement intelligent cropping** based on image content type
- **Test with both text and natural images** to ensure proper cropping

#### ADO Range Configuration
- **Design space should extend to 99%** for comprehensive threshold estimation
- **Threshold ranges should match design space** to avoid convergence issues
- **Cache prediction ranges must align** with ADO capabilities
- **Consider stimulus type requirements** when setting ranges (text vs natural images)

#### Testing and Validation
- **Test with extreme thresholds** (both very low and very high)
- **Verify image cropping** with different stimulus types
- **Check ADO convergence** across full MTF range
- **Validate preview displays** maintain proper aspect ratios

### Known Optimizations Applied

1. **Smart Image Caching**: LRU cache with MTF value prediction for preloading
2. **Precise Timing System**: ±10ms accuracy with automatic calibration  
3. **Extended MTF Range**: Full 10-99% coverage for comprehensive testing
4. **Intelligent Cropping**: Content-aware processing for different image types
5. **Quality Scaling**: High-quality thumbnail generation with aspect ratio preservation

This ensures the platform can handle diverse experimental requirements while maintaining optimal performance and user experience.