"""
Main application for WebRS MTF Threshold experiment - Refactored version.
This file serves as the main router for the experiment.
"""
import streamlit as st
import time

# Initialize configuration
from config.settings import detect_environment, PAGE_CONFIG
from config.logging_config import setup_logging

# Initialize logging with reduced verbosity
setup_logging(level='WARNING')

# Detect environment
environment = detect_environment()

# Configure Streamlit page
st.set_page_config(**PAGE_CONFIG)

# Core modules
from core.session_manager import SessionStateManager
from core.experiment_controller import ExperimentController

# UI modules
from ui.screens.welcome_screen import display_welcome_screen
from ui.components.progress_indicators import show_experiment_status

# Utilities
from utils.logger import get_logger
from utils.helpers import show_error_message

logger = get_logger(__name__)

def initialize_app():
    """Initialize the application"""
    try:
        # Initialize session manager (this handles all session state)
        if 'session_manager' not in st.session_state:
            st.session_state.session_manager = SessionStateManager()
            logger.info("Session manager initialized")
        
        # Initialize experiment controller
        if 'experiment_controller' not in st.session_state:
            st.session_state.experiment_controller = ExperimentController(
                st.session_state.session_manager
            )
            logger.info("Experiment controller initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize app: {e}")
        show_error_message("Failed to initialize application", e)
        return False

def route_to_screen():
    """Route to appropriate screen based on experiment stage with complete page clearing"""
    try:
        session_manager = st.session_state.session_manager
        stage = session_manager.get_experiment_stage()
        
        # Initialize page container if not exists
        if 'main_container' not in st.session_state:
            st.session_state.main_container = st.empty()
        
        # Clear previous content completely before switching
        previous_stage = st.session_state.get('previous_stage', None)
        if previous_stage != stage:
            st.session_state.main_container.empty()  # Complete page clear
            st.session_state.previous_stage = stage
            logger.debug(f"🧹 Page cleared: {previous_stage} → {stage}")
        
        # Show experiment status in sidebar with rich information (separate from main content)
        show_experiment_status(stage, session_manager.get_participant_id(), session_manager)
        
        # Use container for main content to ensure clean transitions
        with st.session_state.main_container.container():
            # Route to appropriate screen
            if stage == 'welcome':
                display_welcome_screen(session_manager)
            
            elif stage == 'instructions':
                from ui.screens.instructions_screen import display_instructions_screen
                display_instructions_screen(session_manager)
            
            elif stage == 'trial':
                from ui.screens.trial_screen import display_trial_screen
                # Get experiment controller, it might be None after reset
                experiment_controller = st.session_state.get('experiment_controller', None)
                display_trial_screen(session_manager, experiment_controller)
            
            elif stage == 'results':
                from ui.screens.results_screen import display_results_screen
                display_results_screen(session_manager)
            
            elif stage == 'stimuli_preview':
                from ui.screens.stimuli_preview_screen import display_stimuli_preview_screen
                display_stimuli_preview_screen(session_manager)
            
            elif stage == 'benchmark':
                from ui.screens.benchmark_screen import display_benchmark_screen
                display_benchmark_screen()
            
            else:
                logger.warning(f"Unknown experiment stage: {stage}")
                st.error(f"Unknown experiment stage: {stage}")
                session_manager.set_experiment_stage('welcome')
                st.rerun()
            
    except Exception as e:
        logger.error(f"Error in screen routing: {e}")
        show_error_message("Error in application routing", e)
        
        # Reset to welcome screen on error
        try:
            if 'main_container' in st.session_state:
                st.session_state.main_container.empty()
            st.session_state.session_manager.set_experiment_stage('welcome')
            st.rerun()
        except:
            st.error("Critical error: Please refresh the page")

def main():
    """Main application entry point"""
    try:
        # Initialize the application
        if not initialize_app():
            st.stop()
        
        # Route to appropriate screen
        route_to_screen()
        
        # Add debug info in sidebar for development
        if environment == 'local':
            with st.sidebar:
                st.markdown("---")
                st.markdown("### 🔧 Debug Info")
                show_debug = st.checkbox("Show Session State", value=False, key="debug_session_state")
                if show_debug:
                    session_summary = st.session_state.session_manager.get_state_summary()
                    st.json(session_summary)
                    
                    # Additional debug info
                    st.markdown("**Full Session State:**")
                    debug_state = {k: str(v)[:100] + "..." if len(str(v)) > 100 else v 
                                 for k, v in st.session_state.items() 
                                 if not k.startswith('_') and not callable(v)}
                    st.json(debug_state)
        
    except Exception as e:
        logger.critical(f"Critical error in main application: {e}")
        st.error("🚨 Critical Error")
        st.error(f"The application encountered a critical error: {e}")
        st.error("Please refresh the page to restart the application.")
        
        # Show detailed error in development
        if environment == 'local':
            st.exception(e)

if __name__ == "__main__":
    main()