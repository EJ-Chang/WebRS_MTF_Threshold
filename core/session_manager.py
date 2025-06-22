"""
Session State Manager for WebRS MTF Threshold experiment.
Centralized management of all Streamlit session state variables.
"""
import streamlit as st
from typing import Any, Optional, Dict, List
from csv_data_manager import CSVDataManager
from database import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)

class SessionStateManager:
    """Centralized session state management"""
    
    def __init__(self):
        """Initialize session state manager"""
        self.initialize_default_states()
        self.initialize_managers()
        self.protect_session_settings()
    
    def initialize_default_states(self):
        """Initialize default session state values"""
        defaults = {
            # Experiment flow
            'experiment_stage': 'welcome',
            'participant_id': None,
            'current_trial': 0,
            'total_trials': 20,
            'is_practice': False,
            'practice_trials_completed': 0,
            
            # Experiment settings
            'show_trial_feedback': True,
            'show_trial_feedback_backup': None,
            'auto_advance_enabled': False,
            'fixation_duration': 3.0,
            
            # Data tracking
            'trial_results': [],
            'saved_trials': 0,
            'experiment_completed': False,
            
            # Manager states
            'managers_initialized': False,
            'csv_manager': None,
            'db_manager': None,
            'db_manager_initialized': False,
            
            # MTF experiment specific
            'mtf_trial_data': None,
            'mtf_response_pending': False,
            'mtf_show_feedback': True,
            'mtf_current_estimates': None,
            
            # Timing and performance
            'trial_start_time': None,
            'response_time': None,
            'fixation_start_time': None,
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                
        logger.debug("Default session states initialized")
    
    def initialize_managers(self):
        """Initialize data managers once at startup"""
        if st.session_state.managers_initialized:
            return
            
        # Initialize CSV manager
        if st.session_state.csv_manager is None:
            try:
                st.session_state.csv_manager = CSVDataManager()
                logger.info("✅ CSV Manager initialized")
            except Exception as e:
                logger.error(f"❌ CSV Manager initialization failed: {e}")
                st.session_state.csv_manager = None
        
        # Initialize database manager with error handling
        if st.session_state.db_manager is None:
            try:
                st.session_state.db_manager = DatabaseManager()
                st.session_state.db_manager_initialized = True
                logger.info("✅ Database Manager initialized successfully")
            except Exception as e:
                logger.error(f"⚠️ Database Manager initialization failed: {e}")
                st.session_state.db_manager = None
                st.session_state.db_manager_initialized = False
        
        # Mark managers as initialized
        st.session_state.managers_initialized = True
    
    def protect_session_settings(self):
        """Ensure critical session settings are preserved"""
        # Backup and restore show_trial_feedback if it gets lost
        if st.session_state.show_trial_feedback_backup is None:
            if st.session_state.show_trial_feedback is not None:
                st.session_state.show_trial_feedback_backup = st.session_state.show_trial_feedback
        
        # Restore from backup if main setting is lost
        if (st.session_state.show_trial_feedback is None and 
            st.session_state.show_trial_feedback_backup is not None):
            st.session_state.show_trial_feedback = st.session_state.show_trial_feedback_backup
            logger.info("🔧 Restored show_trial_feedback from backup")
    
    # Experiment stage management
    def get_experiment_stage(self) -> str:
        """Get current experiment stage"""
        return st.session_state.experiment_stage
    
    def set_experiment_stage(self, stage: str):
        """Set experiment stage"""
        st.session_state.experiment_stage = stage
        logger.debug(f"Experiment stage changed to: {stage}")
    
    def is_welcome_stage(self) -> bool:
        return self.get_experiment_stage() == 'welcome'
    
    def is_instructions_stage(self) -> bool:
        return self.get_experiment_stage() == 'instructions'
    
    def is_trial_stage(self) -> bool:
        return self.get_experiment_stage() == 'trial'
    
    def is_results_stage(self) -> bool:
        return self.get_experiment_stage() == 'results'
    
    def is_benchmark_stage(self) -> bool:
        return self.get_experiment_stage() == 'benchmark'
    
    # Participant management
    def get_participant_id(self) -> Optional[str]:
        """Get participant ID"""
        return st.session_state.participant_id
    
    def set_participant_id(self, participant_id: str):
        """Set participant ID"""
        st.session_state.participant_id = participant_id
        logger.info(f"Participant ID set: {participant_id}")
    
    def clear_participant_data(self):
        """Clear all participant-specific data"""
        keys_to_clear = [
            'participant_id', 'current_trial', 'trial_results', 
            'saved_trials', 'experiment_completed', 'mtf_trial_data',
            'mtf_response_pending', 'practice_trials_completed'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                st.session_state[key] = None if key == 'participant_id' else 0 if 'trial' in key else False
        
        logger.info("Participant data cleared")
    
    # Trial management
    def get_current_trial(self) -> int:
        """Get current trial number"""
        return st.session_state.current_trial
    
    def increment_trial(self):
        """Increment trial counter"""
        st.session_state.current_trial += 1
        logger.debug(f"Trial incremented to: {st.session_state.current_trial}")
    
    def get_total_trials(self) -> int:
        """Get total number of trials"""
        return st.session_state.total_trials
    
    def set_total_trials(self, total: int):
        """Set total number of trials"""
        st.session_state.total_trials = total
    
    def is_experiment_complete(self) -> bool:
        """Check if experiment is complete"""
        return st.session_state.current_trial >= st.session_state.total_trials
    
    # Practice mode
    def is_practice_mode(self) -> bool:
        """Check if in practice mode"""
        return st.session_state.is_practice
    
    def set_practice_mode(self, is_practice: bool):
        """Set practice mode"""
        st.session_state.is_practice = is_practice
        logger.debug(f"Practice mode: {is_practice}")
    
    def get_practice_trials_completed(self) -> int:
        """Get number of practice trials completed"""
        return st.session_state.practice_trials_completed
    
    def increment_practice_trials(self):
        """Increment practice trial counter"""
        st.session_state.practice_trials_completed += 1
    
    # Data management
    def add_trial_result(self, result: Dict[str, Any]):
        """Add trial result to session state"""
        if st.session_state.trial_results is None:
            st.session_state.trial_results = []
        st.session_state.trial_results.append(result)
        logger.debug(f"Trial result added. Total results: {len(st.session_state.trial_results)}")
    
    def get_trial_results(self) -> List[Dict[str, Any]]:
        """Get all trial results"""
        return st.session_state.trial_results or []
    
    def increment_saved_trials(self):
        """Increment saved trials counter"""
        st.session_state.saved_trials += 1
    
    def get_saved_trials(self) -> int:
        """Get number of saved trials"""
        return st.session_state.saved_trials
    
    # Manager access
    def get_csv_manager(self) -> Optional[CSVDataManager]:
        """Get CSV manager instance"""
        return st.session_state.csv_manager
    
    def get_db_manager(self) -> Optional[DatabaseManager]:
        """Get database manager instance"""
        return st.session_state.db_manager
    
    def is_db_manager_initialized(self) -> bool:
        """Check if database manager is initialized"""
        return st.session_state.db_manager_initialized
    
    # Settings management
    def get_show_trial_feedback(self) -> bool:
        """Get trial feedback setting"""
        return st.session_state.show_trial_feedback
    
    def set_show_trial_feedback(self, show: bool):
        """Set trial feedback setting"""
        st.session_state.show_trial_feedback = show
        st.session_state.show_trial_feedback_backup = show
    
    def get_auto_advance_enabled(self) -> bool:
        """Get auto advance setting"""
        return st.session_state.auto_advance_enabled
    
    def set_auto_advance_enabled(self, enabled: bool):
        """Set auto advance setting"""
        st.session_state.auto_advance_enabled = enabled
    
    def get_fixation_duration(self) -> float:
        """Get fixation duration"""
        return st.session_state.fixation_duration
    
    def set_fixation_duration(self, duration: float):
        """Set fixation duration"""
        st.session_state.fixation_duration = duration
    
    # MTF specific states
    def get_mtf_trial_data(self):
        """Get current MTF trial data"""
        return st.session_state.mtf_trial_data
    
    def set_mtf_trial_data(self, data):
        """Set MTF trial data"""
        st.session_state.mtf_trial_data = data
    
    def is_mtf_response_pending(self) -> bool:
        """Check if MTF response is pending"""
        return st.session_state.mtf_response_pending
    
    def set_mtf_response_pending(self, pending: bool):
        """Set MTF response pending state"""
        st.session_state.mtf_response_pending = pending
    
    def get_mtf_show_feedback(self) -> bool:
        """Get MTF feedback setting"""
        return st.session_state.mtf_show_feedback
    
    def set_mtf_show_feedback(self, show: bool):
        """Set MTF feedback setting"""
        st.session_state.mtf_show_feedback = show
    
    # Utility methods
    def reset_experiment(self):
        """Reset experiment to initial state"""
        self.set_experiment_stage('welcome')
        self.clear_participant_data()
        logger.info("Experiment reset to initial state")
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current session state"""
        return {
            'stage': self.get_experiment_stage(),
            'participant_id': self.get_participant_id(),
            'current_trial': self.get_current_trial(),
            'total_trials': self.get_total_trials(),
            'is_practice': self.is_practice_mode(),
            'experiment_complete': self.is_experiment_complete(),
            'saved_trials': self.get_saved_trials(),
            'managers_initialized': st.session_state.managers_initialized,
            'db_initialized': self.is_db_manager_initialized()
        }