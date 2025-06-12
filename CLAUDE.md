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

# Development testing
python test_replit_environment.py
```

### Local Development Commands
```bash
# For local development (non-Replit)
streamlit run app.py

# Install dependencies
pip install -r requirements.txt

# Test environment setup
python test_replit_environment.py
```

### Replit-Specific Development
```bash
# Test Replit environment compatibility
python test_replit_environment.py

# Check all dependencies and setup
python -c "from test_replit_environment import main; main()"

# Standalone experiments (if experiments/ utilities are available)
cd experiments && python Exp_MTF_ADO.py
cd experiments && python Exp_MTF_Psychometric_YN.py
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

### Replit Configuration Files
- **`.replit`** - Replit run configuration and port settings
- **`replit.nix`** - Nix package dependencies for Replit environment
- **`requirements.txt`** - Python package dependencies
- **`pyproject.toml`** - Modern Python project configuration

### Experiment Modules
- **`experiments/ado_utils.py`** - Advanced Bayesian ADO engine with mutual information optimization
- **`experiments/mtf_utils.py`** - Real-time MTF image processing and performance optimization
- **`experiments/Exp_MTF_ADO.py`** - Standalone PsychoPy MTF experiment
- **`simple_ado.py`** - Simplified ADO for 2AFC experiments

### Key Architectural Patterns

#### Adaptive Design Optimization (ADO)
The platform implements two ADO approaches:
- **Simple ADO** (`simple_ado.py`) - For 2AFC experiments with basic threshold tracking
- **Advanced ADO** (`experiments/ado_utils.py`) - Full Bayesian implementation with:
  - Mutual information maximization
  - Real-time parameter estimation
  - Convergence criteria monitoring
  - Posterior distribution tracking

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
- `streamlit` - Web application framework
- `opencv-python` - Image processing for MTF
- `numpy`, `scipy` - Scientific computing and ADO algorithms
- `plotly` - Interactive psychometric function plotting
- `psycopg2-binary` - PostgreSQL database connectivity
- `sqlalchemy` - Database ORM
- `pandas` - Data manipulation and export

### Key File Relationships
- `app.py` imports and coordinates all experiment managers
- Experiment managers import ADO utilities and database operations
- MTF experiments depend on `experiments/mtf_utils.py` for image processing
- Database operations are centralized in `database.py` with SQLAlchemy models

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

This platform represents a research-grade implementation of adaptive psychophysical testing optimized for Replit hosting with modern web technologies and rigorous experimental methodology.