"""
Session State Manager for WebRS MTF Threshold experiment.
Centralized management of all Streamlit session state variables.
"""
import streamlit as st
from typing import Any, Optional, Dict, List
from utils.csv_data_manager import CSVDataManager
from utils.database_manager import DatabaseManager
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
            'experiment_trial': 0,  # Separate counter for experiment trials only
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
            'experiment_id': None,
            
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
    
    def is_stimuli_preview_stage(self) -> bool:
        return self.get_experiment_stage() == 'stimuli_preview'
    
    # Participant management
    def get_participant_id(self) -> Optional[str]:
        """Get participant ID"""
        return st.session_state.participant_id
    
    def set_participant_id(self, participant_id: str):
        """Set participant ID and initialize participant records"""
        st.session_state.participant_id = participant_id
        logger.info(f"Participant ID set: {participant_id}")
        
        # Initialize CSV participant record
        csv_manager = self.get_csv_manager()
        if csv_manager:
            try:
                # Get experiment config from session state if available
                experiment_config = {
                    "experiment_type": "MTF Clarity Testing",
                    "max_trials": st.session_state.get('max_trials', 50),
                    "min_trials": st.session_state.get('min_trials', 15),
                    "convergence_threshold": st.session_state.get('convergence_threshold', 0.15),
                    "stimulus_duration": st.session_state.get('stimulus_duration', 1.0)
                }
                csv_manager.create_participant_record(participant_id, experiment_config)
                logger.info(f"✅ CSV participant record created for: {participant_id}")
            except Exception as e:
                logger.error(f"❌ Failed to create CSV participant record: {e}")
        
        # Initialize database participant record
        db_manager = self.get_db_manager()
        if db_manager and self.is_db_manager_initialized():
            try:
                db_manager.create_participant(participant_id)
                logger.info(f"✅ Database participant record created for: {participant_id}")
            except Exception as e:
                logger.error(f"❌ Failed to create database participant record: {e}")
    
    def clear_participant_data(self):
        """Clear all participant-specific data"""
        reset_values = {
            'participant_id': None,
            'experiment_id': None,
            'current_trial': 0,
            'experiment_trial': 0,
            'trial_results': [],  # Must be empty list, not False
            'saved_trials': 0,
            'practice_trials_completed': 0,
            'experiment_completed': False,
            'mtf_trial_data': None,
            'mtf_response_pending': False,
            'is_practice': False,  # Reset practice mode state
            'selected_stimulus_image': None,  # Clear stimulus selection
            'max_trials': None,  # Clear experiment configuration
            'min_trials': None,
            'convergence_threshold': None,
            'stimulus_duration': None,
            'experiment_type': None
        }
        
        for key, value in reset_values.items():
            if key in st.session_state:
                st.session_state[key] = value
        
        # Clear MTF experiment manager and related caches
        mtf_related_keys = [
            'mtf_experiment_manager', 'experiment_controller',
            'trial_phase', 'phase_start_time', 'feedback_response', 'feedback_time',
            'trial_start_time', 'response_time', 'fixation_start_time'
        ]
        
        for key in mtf_related_keys:
            if key in st.session_state:
                st.session_state[key] = None
        
        logger.info("Participant data and experiment state cleared completely")
    
    def reset_practice_counters(self):
        """Reset practice-specific counters only"""
        st.session_state.practice_trials_completed = 0
        logger.info("Practice counters reset")
    
    def reset_experiment_counters(self):
        """Reset experiment-specific counters for transition from practice to experiment"""
        st.session_state.current_trial = 0
        st.session_state.experiment_trial = 0
        st.session_state.saved_trials = 0
        # Don't reset practice_trials_completed - keep for record
        logger.info(f"Experiment counters reset (practice trials completed: {st.session_state.practice_trials_completed})")
    
    # Experiment ID management
    def get_experiment_id(self) -> Optional[int]:
        """Get experiment ID"""
        return st.session_state.experiment_id
    
    def set_experiment_id(self, experiment_id: int):
        """Set experiment ID"""
        st.session_state.experiment_id = experiment_id
        logger.info(f"Experiment ID set: {experiment_id}")
    
    def create_experiment_record(self, experiment_type: str = "MTF_Clarity", **kwargs):
        """Create experiment record in database"""
        db_manager = self.get_db_manager()
        participant_id = self.get_participant_id()
        
        if not db_manager or not participant_id:
            logger.warning("Cannot create experiment record: missing database manager or participant ID")
            return None
        
        try:
            experiment_id = db_manager.create_experiment(
                participant_id=participant_id,
                experiment_type=experiment_type,
                use_ado=kwargs.get('use_ado', True),
                num_trials=kwargs.get('num_trials', st.session_state.get('total_trials', 50)),
                num_practice_trials=kwargs.get('num_practice_trials', 0),
                max_trials=kwargs.get('max_trials', st.session_state.get('max_trials', 50)),
                min_trials=kwargs.get('min_trials', st.session_state.get('min_trials', 15)),
                convergence_threshold=kwargs.get('convergence_threshold', st.session_state.get('convergence_threshold', 0.15)),
                stimulus_duration=kwargs.get('stimulus_duration', st.session_state.get('stimulus_duration', 1.0)),
                inter_trial_interval=kwargs.get('inter_trial_interval', 0.5)
            )
            
            if experiment_id:
                self.set_experiment_id(experiment_id)
                logger.info(f"✅ Experiment record created with ID: {experiment_id}")
                return experiment_id
            else:
                logger.error("❌ Failed to create experiment record")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating experiment record: {e}")
            return None
    
    # Trial management
    def get_current_trial(self) -> int:
        """Get current trial number (legacy - use for overall tracking)"""
        return st.session_state.current_trial
    
    def get_experiment_trial(self) -> int:
        """Get current experiment trial number (separate from practice)"""
        return st.session_state.experiment_trial
    
    def increment_trial(self):
        """Increment trial counter (legacy)"""
        st.session_state.current_trial += 1
        logger.debug(f"Trial incremented to: {st.session_state.current_trial}")
    
    def increment_experiment_trial(self):
        """Increment experiment trial counter (only for non-practice trials)"""
        st.session_state.experiment_trial += 1
        logger.debug(f"Experiment trial incremented to: {st.session_state.experiment_trial}")
    
    def get_total_trials(self) -> int:
        """Get total number of trials"""
        return st.session_state.total_trials
    
    def set_total_trials(self, total: int):
        """Set total number of trials"""
        st.session_state.total_trials = total
    
    def is_experiment_complete(self) -> bool:
        """Check if experiment is complete"""
        if self.is_practice_mode():
            return False  # Practice mode never "completes" via this check
        # Use >= to check if we have completed all required trials
        # experiment_trial is the count of COMPLETED trials
        # We want to stop when we have completed exactly max_trials
        completed_trials = st.session_state.experiment_trial
        max_trials = st.session_state.total_trials
        
        logger.debug(f"Experiment completion check: {completed_trials}/{max_trials} trials completed")
        return completed_trials >= max_trials
    
    # Practice mode
    def is_practice_mode(self) -> bool:
        """Check if in practice mode"""
        return st.session_state.is_practice
    
    def set_practice_mode(self, is_practice: bool):
        """Set practice mode and reset appropriate counters"""
        old_practice_mode = st.session_state.get('is_practice', False)
        st.session_state.is_practice = is_practice
        
        # If transitioning from practice to experiment mode
        if old_practice_mode == True and is_practice == False:
            logger.info("🔄 Transitioning from practice to experiment mode")
            self.reset_experiment_counters()
        # If transitioning from experiment to practice mode (retry practice)
        elif old_practice_mode == False and is_practice == True:
            logger.info("🔄 Transitioning from experiment to practice mode")
            self.reset_practice_counters()
        
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
    @staticmethod
    def simulate_page_reload():
        """
        Simulate a complete page reload by clearing all state and re-initializing
        This is the closest we can get to F5 refresh without actually reloading the page
        """
        try:
            logger.info("🔄 Simulating complete page reload...")
            
            # 1. Clear Streamlit caches first (before clearing session state)
            try:
                st.cache_data.clear()
                st.cache_resource.clear()
                logger.info("   ✅ Streamlit caches cleared")
            except Exception as e:
                logger.warning(f"   ⚠️ Cache clearing failed (not critical): {e}")
            
            # 2. Completely clear session state - don't preserve anything
            st.session_state.clear()
            logger.info("   ✅ Session state cleared")
            
            # 3. Re-initialize core components (avoid st.set_page_config issue)
            # Initialize session manager first
            st.session_state.session_manager = SessionStateManager()
            logger.info("   ✅ SessionStateManager re-created")
            
            # Initialize experiment controller
            from core.experiment_controller import ExperimentController
            st.session_state.experiment_controller = ExperimentController(
                st.session_state.session_manager
            )
            logger.info("   ✅ ExperimentController re-created")
            
            # 4. Ensure we're on the welcome screen
            st.session_state.session_manager.set_experiment_stage('welcome')
            logger.info("   ✅ Redirected to welcome screen")
            return True
                
        except Exception as e:
            logger.error(f"❌ Page reload simulation failed: {e}")
            # Fallback: try basic reset
            try:
                st.session_state.clear()
                # Re-create basic session manager
                st.session_state.session_manager = SessionStateManager()
                st.session_state.session_manager.set_experiment_stage('welcome')
                logger.info("   ✅ Fallback reset completed")
                return True
            except Exception as e2:
                logger.error(f"❌ Even fallback reset failed: {e2}")
                return False
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current session state"""
        return {
            'stage': self.get_experiment_stage(),
            'participant_id': self.get_participant_id(),
            'current_trial': self.get_current_trial(),
            'experiment_trial': self.get_experiment_trial(),
            'total_trials': self.get_total_trials(),
            'is_practice': self.is_practice_mode(),
            'experiment_complete': self.is_experiment_complete(),
            'saved_trials': self.get_saved_trials(),
            'managers_initialized': st.session_state.managers_initialized,
            'db_initialized': self.is_db_manager_initialized()
        }