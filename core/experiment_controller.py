"""
Experiment controller for WebRS MTF Threshold experiment.
Handles experiment flow and business logic.
"""
import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, Optional
from core.session_manager import SessionStateManager
from core.async_image_processor import get_async_processor
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
            st.session_state.experiment_trial = 0  # Reset experiment-specific counter
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
    
    def _enhance_trial_data_with_async_image(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance trial data with async processed image if available
        
        Args:
            trial_data: Original trial data
            
        Returns:
            Enhanced trial data with async image if available
        """
        try:
            if not trial_data:
                return trial_data
            
            current_trial = self.session.get_current_trial()
            mtf_value = trial_data.get('mtf_value', 0)
            
            # Check for async processed image
            async_task_key = f"async_task_trial_{current_trial}"
            
            if async_task_key in st.session_state:
                task_info = st.session_state[async_task_key]
                task_id = task_info['task_id']
                expected_mtf = task_info['mtf_value']
                
                # Check if MTF values match (within tolerance)
                if abs(expected_mtf - mtf_value) < 0.1:
                    async_processor = get_async_processor()
                    async_image = async_processor.get_processed_image(task_id, timeout=0.5)
                    
                    if async_image is not None:
                        # Replace stimulus image with async processed one
                        trial_data['stimulus_image'] = async_image
                        logger.info(f"✅ 使用異步預處理圖片增強試次數據 MTF {mtf_value:.1f}%")
                        # Clean up task info
                        del st.session_state[async_task_key]
                    else:
                        logger.debug(f"🕐 異步圖片未完成，保留原始試次數據 MTF {mtf_value:.1f}%")
            
            return trial_data
            
        except Exception as e:
            logger.error(f"Error enhancing trial data with async image: {e}")
            return trial_data
    
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
                
                # Use session state trial count instead of internal counter
                if self.session.is_practice_mode():
                    ado_data['ado_trial_count'] = self.session.get_practice_trials_completed()
                else:
                    ado_data['ado_trial_count'] = self.session.get_experiment_trial()
                
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
            # Use experiment trial counter for proper numbering (practice trials don't increment this)
            trial_number = self.session.get_experiment_trial() + 1 if not self.session.is_practice_mode() else self.session.get_practice_trials_completed() + 1
            
            # Validation logging
            is_practice = self.session.is_practice_mode()
            logger.info(f"📊 Trial counting debug - Mode: {'PRACTICE' if is_practice else 'EXPERIMENT'}, "
                       f"Trial number: {trial_number}, "
                       f"Experiment trials: {self.session.get_experiment_trial()}, "
                       f"Practice trials: {self.session.get_practice_trials_completed()}, "
                       f"Overall trials: {self.session.get_current_trial()}")
            
            trial_result = {
                'trial_number': trial_number,
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
            
            # Increment trial counters
            if not self.session.is_practice_mode():
                self.session.increment_experiment_trial()  # Only increment experiment counter for real trials
                logger.debug(f"Experiment trial incremented to: {self.session.get_experiment_trial()}")
            else:
                self.session.increment_practice_trials()
                logger.debug(f"Practice trial incremented to: {self.session.get_practice_trials_completed()}")
            
            # Always increment the overall trial counter for compatibility
            self.session.increment_trial()
            
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
            trial_number = trial_result.get('trial_number', 'unknown')
            participant_id = self.session.get_participant_id()
            
            # 雙重安全檢查：絕對不儲存practice trials
            if self.session.is_practice_mode():
                logger.warning(f"❌ Practice trial {trial_number} storage blocked by session state check")
                return False
            
            # 檢查trial data中的is_practice標記
            if trial_result.get('is_practice', False):
                logger.warning(f"❌ Trial {trial_number} marked as practice, storage blocked by data check")
                return False
            logger.info(f"Saving EXPERIMENT trial {trial_number} for participant {participant_id}")
            
            csv_saved = False
            db_saved = False
            
            # Save to CSV (primary storage)
            csv_manager = self.session.get_csv_manager()
            if csv_manager:
                try:
                    csv_manager.save_trial_data(participant_id, trial_result)
                    csv_saved = True
                    logger.info(f"✅ Trial {trial_number} saved to CSV")
                except Exception as e:
                    logger.error(f"❌ Failed to save trial {trial_number} to CSV: {e}")
            else:
                logger.warning(f"⚠️ No CSV manager available for trial {trial_number}")
            
            # Save to database (secondary storage)
            db_manager = self.session.get_db_manager()
            if db_manager and self.session.is_db_manager_initialized():
                try:
                    experiment_id = self.session.get_experiment_id()
                    if experiment_id:
                        db_manager.save_trial(experiment_id, trial_result)
                        db_saved = True
                        logger.info(f"✅ Trial {trial_number} saved to database")
                    else:
                        logger.warning(f"⚠️ No experiment_id available for trial {trial_number} database saving")
                except Exception as e:
                    logger.error(f"❌ Failed to save trial {trial_number} to database: {e}")
            else:
                logger.warning(f"⚠️ Database not available for trial {trial_number}")
            
            # Consider successful if at least one storage method succeeded
            if csv_saved or db_saved:
                self.session.increment_saved_trials()
                saved_count = self.session.get_saved_trials()
                experiment_count = self.session.get_experiment_trial()
                logger.info(f"✅ EXPERIMENT trial {trial_number} saved successfully (CSV: {csv_saved}, DB: {db_saved}) - "
                           f"Saved count: {saved_count}, Experiment trials: {experiment_count}")
                return True
            else:
                logger.error(f"❌ Failed to save EXPERIMENT trial {trial_number} to any storage method")
                return False
                
        except Exception as e:
            logger.error(f"❌ Critical error saving trial data: {e}")
            return False
    
    def check_experiment_completion(self) -> bool:
        """
        Check if experiment should be completed
        
        Returns:
            True if experiment is complete
        """
        try:
            # ONLY use session manager completion check for consistency
            # This ensures single source of truth for trial counting
            is_complete = self.session.is_experiment_complete()
            
            if is_complete:
                logger.info(f"Experiment completion detected by session manager")
                logger.info(f"   Experiment trials completed: {self.session.get_experiment_trial()}")
                logger.info(f"   Total trials required: {self.session.get_total_trials()}")
                logger.info(f"   Practice mode: {self.session.is_practice_mode()}")
            
            return is_complete
            
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
    
    # reset_experiment() method has been removed and will be reimplemented later
    
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

    def ensure_all_data_saved(self) -> bool:
        """
        Ensure all trial data is saved to storage
        
        Returns:
            True if all data saved successfully
        """
        try:
            trial_results = self.session.get_trial_results()
            saved_trials = self.session.get_saved_trials()
            participant_id = self.session.get_participant_id()
            
            # Filter out practice trials for counting
            non_practice_trials = [t for t in trial_results if not t.get('is_practice', False)]
            
            logger.info(f"🔍 Data save check for participant {participant_id}:")
            logger.info(f"   Total trials: {len(trial_results)}")
            logger.info(f"   Non-practice trials: {len(non_practice_trials)}")
            logger.info(f"   Saved trials counter: {saved_trials}")
            
            # Check if there are unsaved trials
            if len(non_practice_trials) > saved_trials:
                unsaved_count = len(non_practice_trials) - saved_trials
                logger.warning(f"⚠️ Found {unsaved_count} potentially unsaved trials, attempting to save...")
                
                # Save any unsaved trials
                save_attempts = 0
                save_successes = 0
                
                for i, trial_result in enumerate(trial_results):
                    # Skip practice trials
                    if trial_result.get('is_practice', False):
                        continue
                    
                    # Check if this trial index is beyond our saved count
                    trial_index = len([t for t in trial_results[:i+1] if not t.get('is_practice', False)]) - 1
                    if trial_index >= saved_trials:
                        save_attempts += 1
                        trial_number = trial_result.get('trial_number', trial_index + 1)
                        
                        if self.save_trial_data(trial_result):
                            save_successes += 1
                            logger.info(f"✅ Saved trial {trial_number}")
                        else:
                            logger.error(f"❌ Failed to save trial {trial_number}")
                
                logger.info(f"📊 Save attempts: {save_attempts}, successes: {save_successes}")
            
            # Final verification
            final_saved = self.session.get_saved_trials()
            
            if len(non_practice_trials) == final_saved:
                logger.info(f"✅ Data save verification PASSED: All {final_saved} experiment trials saved")
                return True
            else:
                logger.error(f"❌ Data save verification FAILED: {len(non_practice_trials)} trials vs {final_saved} saved")
                
                # Detailed breakdown for debugging
                logger.error("📋 Detailed trial breakdown:")
                for i, trial in enumerate(trial_results):
                    is_practice = trial.get('is_practice', False)
                    trial_num = trial.get('trial_number', i+1)
                    logger.error(f"   Trial {trial_num}: {'PRACTICE' if is_practice else 'EXPERIMENT'}")
                
                return False
                
        except Exception as e:
            logger.error(f"❌ Critical error ensuring data saved: {e}")
            return False
    
    def finalize_experiment_in_database(self) -> bool:
        """
        Finalize experiment record in database with completion time
        
        Returns:
            True if finalized successfully
        """
        try:
            db_manager = self.session.get_db_manager()
            experiment_id = self.session.get_experiment_id()
            
            if not db_manager or not experiment_id:
                logger.warning("Cannot finalize experiment: missing database manager or experiment ID")
                return False
            
            # Update experiment completion time
            if hasattr(db_manager, 'complete_experiment'):
                try:
                    db_manager.complete_experiment(experiment_id)
                    logger.info(f"✅ Experiment {experiment_id} completed in database")
                    return True
                except Exception as e:
                    logger.error(f"❌ Failed to complete experiment {experiment_id}: {e}")
                    return False
            else:
                logger.warning("Database manager does not support experiment completion")
                return False
                
        except Exception as e:
            logger.error(f"Error finalizing experiment in database: {e}")
            return False

    def get_experiment_progress(self) -> Dict[str, Any]:
        """
        Get current experiment progress
        
        Returns:
            Dictionary containing progress information
        """
        try:
            if self.session.is_practice_mode():
                current_trial = self.session.get_practice_trials_completed()
                total_trials = 3  # Practice limit
            else:
                current_trial = self.session.get_experiment_trial()
                total_trials = self.session.get_total_trials()
            
            progress_percentage = (current_trial / total_trials * 100) if total_trials > 0 else 0
            
            return {
                'current_trial': current_trial,
                'total_trials': total_trials,
                'progress_percentage': progress_percentage,
                'saved_trials': self.session.get_saved_trials(),
                'is_practice': self.session.is_practice_mode(),
                'practice_completed': self.session.get_practice_trials_completed(),
                'experiment_trial': self.session.get_experiment_trial()
            }
            
        except Exception as e:
            logger.error(f"Error getting experiment progress: {e}")
            return {}