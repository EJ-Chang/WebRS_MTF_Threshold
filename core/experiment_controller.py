"""
Experiment controller for WebRS MTF Threshold experiment.
Handles experiment flow and business logic.
"""
import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, Optional
from core.session_manager import SessionStateManager
from utils.logger import get_logger

logger = get_logger(__name__)

class ExperimentController:
    """Controls experiment flow and business logic"""
    
    def __init__(self, session_manager: SessionStateManager):
        """
        Initialize experiment controller
        
        Args:
            session_manager: Session state manager instance
        """
        self.session = session_manager
        logger.debug("ExperimentController initialized")
    
    def start_experiment(self, experiment_type: str = "MTF Clarity Testing") -> bool:
        """
        Start the experiment
        
        Args:
            experiment_type: Type of experiment to start
            
        Returns:
            True if experiment started successfully
        """
        try:
            if not self.session.get_participant_id():
                logger.error("Cannot start experiment: No participant ID")
                return False
            
            # Reset trial counters
            st.session_state.current_trial = 0
            st.session_state.trial_results = []
            st.session_state.saved_trials = 0
            st.session_state.experiment_completed = False
            
            # Set experiment type
            st.session_state.experiment_type = experiment_type
            
            # Note: Database experiment record is created in instructions_screen.py
            # when starting the experiment (for non-practice mode)
            
            logger.info(f"Experiment started for participant: {self.session.get_participant_id()}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting experiment: {e}")
            return False
    
    def prepare_trial(self) -> Optional[Dict[str, Any]]:
        """
        Prepare next trial
        
        Returns:
            Trial data dictionary or None if experiment is complete
        """
        try:
            if self.session.is_experiment_complete():
                logger.info("Experiment is complete, no more trials")
                return None
            
            # Get trial data from MTF experiment manager
            if 'mtf_experiment_manager' in st.session_state:
                exp_manager = st.session_state.mtf_experiment_manager
                
                if hasattr(exp_manager, 'get_next_trial'):
                    trial_data = exp_manager.get_next_trial()
                    if trial_data:
                        self.session.set_mtf_trial_data(trial_data)
                        st.session_state.trial_start_time = time.time()
                        logger.debug(f"Trial {self.session.get_current_trial() + 1} prepared")
                        return trial_data
                
            return None
            
        except Exception as e:
            logger.error(f"Error preparing trial: {e}")
            return None
    
    def process_response(self, response: str, response_time: Optional[float] = None) -> bool:
        """
        Process trial response
        
        Args:
            response: User response ('clear' or 'not_clear')
            response_time: Response time in seconds
            
        Returns:
            True if response processed successfully
        """
        try:
            trial_data = self.session.get_mtf_trial_data()
            if not trial_data:
                logger.error("No trial data available for response processing")
                return False
            
            # Calculate response time if not provided
            if response_time is None and st.session_state.trial_start_time:
                response_time = time.time() - st.session_state.trial_start_time
            
            # Get ADO estimates and statistics if available
            ado_data = {}
            if 'mtf_experiment_manager' in st.session_state:
                exp_manager = st.session_state.mtf_experiment_manager
                if hasattr(exp_manager, 'get_current_estimates'):
                    estimates = exp_manager.get_current_estimates()
                    ado_data.update({
                        'estimated_threshold': estimates.get('threshold_mean'),
                        'estimated_slope': estimates.get('slope_mean'),
                        'threshold_std': estimates.get('threshold_sd'),
                        'slope_std': estimates.get('slope_sd')
                    })
                    
                    # Calculate confidence intervals (95% CI = mean ± 1.96 * std)
                    if estimates.get('threshold_mean') is not None and estimates.get('threshold_sd') is not None:
                        threshold_ci = 1.96 * estimates.get('threshold_sd', 0)
                        ado_data.update({
                            'threshold_ci_lower': estimates.get('threshold_mean', 0) - threshold_ci,
                            'threshold_ci_upper': estimates.get('threshold_mean', 0) + threshold_ci
                        })
                    
                    if estimates.get('slope_mean') is not None and estimates.get('slope_sd') is not None:
                        slope_ci = 1.96 * estimates.get('slope_sd', 0)
                        ado_data.update({
                            'slope_ci_lower': estimates.get('slope_mean', 0) - slope_ci,
                            'slope_ci_upper': estimates.get('slope_mean', 0) + slope_ci
                        })
                
                # Get ADO entropy and trial count
                if hasattr(exp_manager, 'get_ado_entropy'):
                    ado_data['ado_entropy'] = exp_manager.get_ado_entropy()
                
                if hasattr(exp_manager, 'current_trial'):
                    ado_data['ado_trial_count'] = exp_manager.current_trial
                
                # Get stimulus image file name
                if hasattr(exp_manager, 'base_image_path') and exp_manager.base_image_path:
                    if exp_manager.base_image_path == "test_pattern":
                        ado_data['stimulus_image_file'] = "test_pattern"
                    else:
                        import os
                        ado_data['stimulus_image_file'] = os.path.basename(exp_manager.base_image_path)
                else:
                    # Fallback: try to get from session state
                    selected_image = st.session_state.get('selected_stimulus_image')
                    if selected_image:
                        ado_data['stimulus_image_file'] = selected_image
            
            # Create trial result with all ADO data
            trial_result = {
                'trial_number': self.session.get_current_trial() + 1,
                'participant_id': self.session.get_participant_id(),
                'mtf_value': trial_data.get('mtf_value'),
                'ado_stimulus_value': trial_data.get('mtf_value'),  # Initial value, will be updated with next trial's ADO computation
                'response': response,
                'reaction_time': response_time,
                'timestamp': datetime.now().isoformat(),
                'is_practice': self.session.is_practice_mode(),
                'experiment_type': st.session_state.get('experiment_type', 'MTF Clarity Testing'),
                'max_trials': st.session_state.get('max_trials', self.session.get_total_trials()),  # Include user's max_trials setting
                **ado_data  # Include all ADO computation results
            }
            
            # Add to session state
            self.session.add_trial_result(trial_result)
            
            # Process with MTF experiment manager
            if 'mtf_experiment_manager' in st.session_state:
                exp_manager = st.session_state.mtf_experiment_manager
                if hasattr(exp_manager, 'record_response'):
                    # Get the stimulus onset time from session state or trial data
                    stimulus_onset_time = st.session_state.get('trial_start_time')
                    exp_manager.record_response(
                        trial_data, 
                        response == 'clear', 
                        response_time,
                        stimulus_onset_time
                    )
            
            # Increment trial counter
            if not self.session.is_practice_mode():
                self.session.increment_trial()
            else:
                self.session.increment_practice_trials()
            
            logger.debug(f"Response processed: {response}, RT: {response_time:.3f}s")
            return True
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return False
    
    def save_trial_data(self, trial_result: Dict[str, Any]) -> bool:
        """
        Save trial data to storage (only for non-practice trials)
        
        Args:
            trial_result: Trial result dictionary
            
        Returns:
            True if data saved successfully
        """
        try:
            # Skip saving practice trials
            if trial_result.get('is_practice', False):
                logger.debug("Skipping save for practice trial")
                return True  # Return True to indicate no error, just skipped
            
            saved_successfully = False
            
            # Save to CSV
            csv_manager = self.session.get_csv_manager()
            if csv_manager:
                try:
                    participant_id = self.session.get_participant_id()
                    csv_manager.save_trial_data(participant_id, trial_result)
                    saved_successfully = True
                    logger.debug("Trial data saved to CSV")
                except Exception as e:
                    logger.error(f"Failed to save to CSV: {e}")
            
            # Save to database
            db_manager = self.session.get_db_manager()
            if db_manager and self.session.is_db_manager_initialized():
                try:
                    experiment_id = self.session.get_experiment_id()
                    if experiment_id:
                        db_manager.save_trial(experiment_id, trial_result)
                        saved_successfully = True
                        logger.debug("Trial data saved to database")
                    else:
                        logger.warning("No experiment_id available for database saving")
                except Exception as e:
                    logger.error(f"Failed to save to database: {e}")
            
            if saved_successfully:
                self.session.increment_saved_trials()
                return True
            else:
                logger.warning("No storage methods available for saving trial data")
                return False
                
        except Exception as e:
            logger.error(f"Error saving trial data: {e}")
            return False
    
    def check_experiment_completion(self) -> bool:
        """
        Check if experiment should be completed
        
        Returns:
            True if experiment is complete
        """
        try:
            # Check trial count
            if self.session.is_experiment_complete():
                return True
            
            # Check MTF experiment manager completion
            if 'mtf_experiment_manager' in st.session_state:
                exp_manager = st.session_state.mtf_experiment_manager
                if hasattr(exp_manager, 'is_experiment_complete'):
                    if exp_manager.is_experiment_complete():
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking experiment completion: {e}")
            return False
    
    def complete_experiment(self) -> bool:
        """
        Complete the experiment
        
        Returns:
            True if experiment completed successfully
        """
        try:
            st.session_state.experiment_completed = True
            
            # Generate summary data
            self.generate_experiment_summary()
            
            logger.info(f"Experiment completed for participant: {self.session.get_participant_id()}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing experiment: {e}")
            return False
    
    def generate_experiment_summary(self) -> Dict[str, Any]:
        """
        Generate experiment summary
        
        Returns:
            Dictionary containing experiment summary
        """
        try:
            trial_results = self.session.get_trial_results()
            
            if not trial_results:
                return {}
            
            # Calculate basic statistics
            total_trials = len(trial_results)
            clear_responses = sum(1 for r in trial_results if r.get('response') == 'clear')
            clear_rate = clear_responses / total_trials if total_trials > 0 else 0
            
            reaction_times = [r.get('reaction_time', 0) for r in trial_results if r.get('reaction_time')]
            avg_reaction_time = sum(reaction_times) / len(reaction_times) if reaction_times else 0
            
            summary = {
                'participant_id': self.session.get_participant_id(),
                'experiment_type': st.session_state.get('experiment_type', 'MTF Clarity Testing'),
                'total_trials': total_trials,
                'clear_responses': clear_responses,
                'clear_rate': clear_rate,
                'average_reaction_time': avg_reaction_time,
                'completion_time': datetime.now().isoformat(),
                'saved_trials': self.session.get_saved_trials()
            }
            
            # Save summary
            st.session_state.experiment_summary = summary
            
            logger.debug(f"Generated experiment summary: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating experiment summary: {e}")
            return {}
    
    def reset_experiment(self) -> bool:
        """
        Reset experiment to initial state
        
        Returns:
            True if reset successful
        """
        try:
            self.session.reset_experiment()
            
            # Clear MTF experiment manager
            if 'mtf_experiment_manager' in st.session_state:
                del st.session_state.mtf_experiment_manager
            
            # Clear other experiment-specific data
            keys_to_clear = [
                'experiment_type', 'stimulus_duration', 'selected_stimulus_image',
                'experiment_summary', 'trial_start_time', 'mtf_trial_data'
            ]
            
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            logger.info("Experiment reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting experiment: {e}")
            return False
    
    def compute_next_stimulus_ado(self) -> Optional[float]:
        """
        ADO computation has been disabled to ensure timing accuracy.
        This function now returns None to maintain interface compatibility.
        
        Returns:
            None (ADO computation disabled)
        """
        logger.debug("ADO computation disabled for timing accuracy")
        return None
    
    def update_previous_trial_ado_value(self, ado_stimulus_value: float) -> bool:
        """
        ADO value update has been disabled to ensure timing accuracy.
        This function now returns True to maintain interface compatibility.
        
        Args:
            ado_stimulus_value: The computed ADO stimulus value (ignored)
            
        Returns:
            True (ADO update disabled but interface maintained)
        """
        logger.debug("ADO value update disabled for timing accuracy")
        return True

    def get_experiment_progress(self) -> Dict[str, Any]:
        """
        Get current experiment progress
        
        Returns:
            Dictionary containing progress information
        """
        try:
            current_trial = self.session.get_current_trial()
            total_trials = self.session.get_total_trials()
            progress_percentage = (current_trial / total_trials * 100) if total_trials > 0 else 0
            
            return {
                'current_trial': current_trial,
                'total_trials': total_trials,
                'progress_percentage': progress_percentage,
                'saved_trials': self.session.get_saved_trials(),
                'is_practice': self.session.is_practice_mode(),
                'practice_completed': self.session.get_practice_trials_completed()
            }
            
        except Exception as e:
            logger.error(f"Error getting experiment progress: {e}")
            return {}