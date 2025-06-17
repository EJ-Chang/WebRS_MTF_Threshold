# Psychophysics 2AFC Experiment Platform

## Overview

This is a sophisticated web-based psychophysics experiment platform built with Streamlit, implementing Two-Alternative Forced Choice (2AFC) brightness discrimination and MTF (Modulation Transfer Function) clarity assessment experiments. The platform features adaptive design optimization (ADO) for efficient threshold estimation and provides comprehensive data collection and analysis capabilities.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application with responsive design
- **User Interface**: Clean, experiment-focused interface with real-time stimulus presentation
- **Image Processing**: OpenCV-based image manipulation with MTF blur simulation
- **Visualization**: Plotly-based charts for real-time performance feedback and data analysis
- **Deployment**: Optimized for Replit cloud hosting with automatic scaling

### Backend Architecture
- **Application Server**: Streamlit server with custom configuration for Replit
- **Experiment Logic**: Modular experiment managers for different paradigms (2AFC, MTF)
- **Data Processing**: Real-time adaptive stimulus selection using simplified ADO algorithms
- **Session Management**: Streamlit's built-in session state for experiment continuity

### Database Design
- **Primary**: PostgreSQL for production (Replit environment)
- **Fallback**: SQLite for development and testing
- **ORM**: SQLAlchemy with declarative models
- **Schema**: Participant -> Experiment -> Trial hierarchical structure

## Key Components

### Experiment Managers
1. **ExperimentManager**: Handles 2AFC brightness discrimination experiments
2. **MTFExperimentManager**: Manages MTF clarity assessment with image blur simulation
3. **ADO Integration**: Adaptive stimulus selection for efficient parameter estimation

### Data Management
- **DatabaseManager**: SQLAlchemy-based database operations with automatic fallbacks
- **DataManager**: CSV export, data validation, and analysis utilities
- **Real-time Storage**: Session-based temporary storage with persistent database backup

### Image Processing Pipeline
- **MTF Simulation**: Gaussian blur-based MTF degradation simulation
- **Stimulus Caching**: Optimized image caching for repeated presentations
- **Viewport Optimization**: Automatic image cropping and resizing for consistent presentation

### Adaptive Algorithms
- **SimpleADO**: Simplified adaptive design optimization for threshold estimation
- **Performance Tracking**: Moving window accuracy calculation for convergence detection
- **Stimulus Selection**: Dynamic difficulty adjustment based on recent performance

## Data Flow

1. **Experiment Setup**: Participant creates session with customizable parameters
2. **Practice Phase**: Fixed stimulus differences for familiarization
3. **Adaptive Testing**: ADO-driven stimulus selection based on performance history
4. **Data Collection**: Real-time trial data storage with reaction time measurement
5. **Analysis**: Immediate performance visualization and statistical summaries
6. **Export**: CSV data export with comprehensive trial information

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework
- **OpenCV**: Image processing and computer vision
- **NumPy/SciPy**: Scientific computing and statistical analysis
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive data visualization

### Database
- **PostgreSQL**: Primary database (Replit environment)
- **SQLite**: Development fallback
- **SQLAlchemy**: Database ORM and migrations

### Image Processing
- **Pillow**: Image format handling and basic operations
- **Base64**: Image encoding for web display

## Deployment Strategy

### Replit Configuration
- **Runtime**: Python 3.11 with PostgreSQL 16
- **Server**: Streamlit on port 5000 with headless configuration
- **Auto-scaling**: Replit's automatic deployment scaling
- **Environment**: Automatic detection of Replit vs local development

### Fallback Mechanisms
- **Database**: Automatic PostgreSQL/SQLite detection and fallback
- **Dependencies**: Graceful degradation when optional packages unavailable
- **Error Handling**: Comprehensive error catching with user-friendly messages

### Performance Optimizations
- **Image Caching**: In-memory stimulus caching for repeated presentations
- **Lazy Loading**: Deferred loading of heavy dependencies
- **Efficient Rendering**: Optimized Streamlit components for smooth interaction

## Changelog

```
Changelog:
- June 17, 2025. Initial setup
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```