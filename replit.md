# WebRS MTF Threshold - Replit Configuration

← Back to [[CLAUDE.md]] | Refactoring: [[REFACTORING_PLAN.md]] | Features: [[ADO_Early_Termination_Analysis.md]]

## 🔗 Related Documentation
- **[[CLAUDE.md]]** - Complete project overview and development guidance
- **[[REFACTORING_PLAN.md]]** - Future architecture improvements and optimization plans
- **[[HIGH_DPI_SETUP_GUIDE.md]]** - Image quality enhancement system
- **[[ADO_Early_Termination_Analysis.md]]** - ADO functionality analysis
- **[[MTF_Explanation.md]]** - Technical foundation for MTF processing

## Overview

This is a modular psychophysics research platform for conducting MTF (Modulation Transfer Function) clarity testing experiments using Adaptive Design Optimization (ADO). The application is built with Streamlit and has been recently refactored from a monolithic 2,174-line application into a clean, modular architecture.

The platform conducts single-interval Y/N judgment tasks where participants view images with varying levels of clarity and make judgments about their sharpness. The system uses ADO algorithms to dynamically adjust stimulus difficulty for optimal parameter estimation.

## System Architecture

The application follows a modular architecture pattern with clear separation of concerns:

**Frontend**: Streamlit web interface with responsive design and keyboard shortcuts
**Backend**: Python-based experiment controller with real-time ADO computation  
**Data Storage**: Dual storage system using both PostgreSQL (production) and CSV (fallback)
**Image Processing**: Real-time MTF blur application using OpenCV

The refactored architecture reduced the main application file from 2,174 lines to 135 lines through strategic modularization while maintaining full functionality.

## Key Components

### Core Modules
- **SessionStateManager**: Centralized management of all Streamlit session state variables, reducing scattered state management from 222 occurrences to a single controlled interface
- **ExperimentController**: Handles experiment flow, trial progression, and completion logic
- **MTFExperimentManager**: Integrates MTF processing with ADO algorithms for stimulus selection

### UI Components  
- **Modular Screen System**: Welcome, instructions, trial, results, and benchmark screens
- **Reusable Components**: Response buttons, image display, progress indicators with consistent styling
- **Image Display System**: Real-time MTF blur application with viewport optimization

### Data Management
- **CSVDataManager**: Primary data storage using structured CSV files with participant tracking
- **DatabaseManager**: PostgreSQL integration for production environments with SQLAlchemy ORM
- **Dual Storage Strategy**: Automatic fallback from database to CSV for reliability

### Experiment Engine
- **ADOEngine**: Complete implementation of Adaptive Design Optimization with Bayesian parameter estimation
- **MTF Utilities**: Real-time image processing for applying modulation transfer function effects
- **Timing System**: Precise stimulus presentation timing with caching for performance

## Data Flow

1. **Participant Registration**: Collect participant ID and stimulus preferences
2. **Experiment Initialization**: Configure ADO parameters and initialize data managers
3. **Trial Loop**: 
   - ADO selects optimal MTF value
   - Apply real-time blur to stimulus image
   - Present stimulus with precise timing
   - Collect response and reaction time
   - Update Bayesian parameter estimates
4. **Data Storage**: Simultaneous CSV and database storage with error handling
5. **Results Analysis**: Generate psychometric curves and export data

The system uses a dual storage approach where data is written to both CSV files (experiment_data/) and PostgreSQL database simultaneously, ensuring data integrity.

## External Dependencies

### Core Dependencies
- `streamlit>=1.46.0` - Web application framework
- `numpy>=2.3.0` - Numerical computing
- `opencv-python>=4.11.0.86` - Image processing for MTF effects
- `scipy>=1.15.3` - Statistical functions for ADO
- `pandas>=2.3.0` - Data manipulation

### Database Support
- `sqlalchemy>=2.0.41` - Database ORM
- `psycopg2-binary>=2.9.10` - PostgreSQL adapter

### Visualization
- `plotly>=6.1.2` - Interactive plotting for results
- `pillow>=11.2.1` - Image handling

The application automatically detects the runtime environment (Replit, Ubuntu, or local) and configures appropriate database connections and port settings.

## Deployment Strategy

### Environment Detection
The application automatically detects three environments:
- **Replit**: Uses port 5000, connects to Replit PostgreSQL
- **Ubuntu Server**: Uses port 3838, configures for server deployment  
- **Local Development**: Uses port 8501, falls back to SQLite

### Database Configuration
- **Production**: PostgreSQL with automatic table creation
- **Development**: SQLite fallback with identical schema
- **Backup**: CSV storage always active regardless of database status

### Performance Optimizations
- Image caching system to reduce processing overhead
- Streamlined session state management
- Lazy loading of experiment modules
- Efficient MTF computation with reusable kernels

## Changelog

- June 22, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.