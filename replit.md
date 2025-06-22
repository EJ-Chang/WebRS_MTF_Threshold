# Psychophysics 2AFC Experiment Platform

## Overview

This is a sophisticated psychophysics experiment platform built with Streamlit, implementing Two-Alternative Forced Choice (2AFC) brightness discrimination and MTF (Modulation Transfer Function) clarity assessment experiments. The platform features adaptive design optimization (ADO), multiple experiment types, and comprehensive data management capabilities.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application
- **UI Components**: Interactive experiment interface with stimulus presentation
- **Responsive Design**: Wide layout optimized for image display
- **Real-time Feedback**: Progress tracking and trial-by-trial results

### Backend Architecture
- **Experiment Management**: Modular experiment managers for different task types
- **Data Processing**: Real-time trial data collection and analysis
- **Image Processing**: OpenCV-based MTF simulation and stimulus generation
- **Adaptive Algorithms**: Custom ADO implementation for optimal stimulus selection

### Data Storage Solutions
- **Primary**: CSV-based data storage system
- **Backup**: Database support with SQLAlchemy ORM (PostgreSQL/SQLite)
- **Export**: Multiple format support (CSV, JSON)
- **Structure**: Participant-based file organization with experiment summaries

## Key Components

### Core Experiment Modules
1. **ExperimentManager** (`experiment.py`): Manages 2AFC brightness discrimination trials
2. **MTFExperimentManager** (`mtf_experiment.py`): Handles MTF clarity assessment experiments
3. **SimpleADO** (`simple_ado.py`): Simplified adaptive design optimization for threshold estimation
4. **ADOOptimizer** (`ado_optimizer.py`): Advanced ADO with Bayesian parameter estimation

### Data Management
1. **CSVDataManager** (`csv_data_manager.py`): Primary CSV-based storage system
2. **DataManager** (`data_manager.py`): Legacy data handling with export capabilities
3. **Database Models** (`database.py`): SQLAlchemy models for PostgreSQL integration

### Image Processing Pipeline
1. **MTF Utils** (`experiments/mtf_utils.py`): MTF blur simulation and image processing
2. **Stimulus Preparation**: Preprocessing tools for experimental stimuli
3. **Real-time Processing**: Dynamic MTF application during experiments

### Environment Configuration
1. **Multi-platform Support**: Automatic environment detection (Replit/Local/Ubuntu)
2. **Port Management**: Dynamic port configuration based on deployment environment
3. **Dependency Management**: Comprehensive package management with fallback handling

## Data Flow

### Experiment Workflow
1. **Initialization**: Participant setup and experiment configuration
2. **Trial Generation**: ADO-based or random stimulus selection
3. **Stimulus Presentation**: Real-time image processing and display
4. **Response Collection**: User input capture with reaction time measurement
5. **Data Storage**: Immediate CSV logging with backup options
6. **Analysis**: Real-time threshold estimation and convergence checking

### Data Processing Pipeline
1. **Input Validation**: Parameter checking and sanitization
2. **Image Processing**: MTF application with configurable parameters
3. **Response Recording**: Structured data capture with metadata
4. **Export Generation**: Multi-format data export capabilities

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework
- **OpenCV**: Image processing and computer vision
- **NumPy/SciPy**: Scientific computing and statistical functions
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive data visualization
- **PIL/Pillow**: Image handling and format conversion

### Optional Dependencies
- **SQLAlchemy**: Database ORM for PostgreSQL integration
- **psycopg2**: PostgreSQL database adapter
- **scikit-learn**: Machine learning utilities for data analysis

### Environment-Specific
- **Replit**: Nix package management with system libraries
- **Local Development**: Standard Python package installation
- **Production**: Streamlit Cloud deployment support

## Deployment Strategy

### Multi-Environment Support
1. **Replit Deployment**: 
   - Port 5000 with public access
   - Nix-based dependency management
   - Automatic environment detection
2. **Local Development**:
   - Port 8501 for localhost access
   - pip/uv-based package management
3. **Streamlit Cloud**:
   - Standard deployment configuration
   - Requirements-based dependency resolution

### Configuration Management
- Environment-specific port binding
- Automatic dependency detection and installation
- Fallback mechanisms for missing components
- Cross-platform compatibility

### Data Persistence
- CSV-based primary storage (no external database required)
- Optional PostgreSQL integration for advanced deployments
- Local file system organization for participant data

## Changelog
- June 22, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.