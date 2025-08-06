"""
Trial screen for WebRS MTF Threshold experiment.
"""
import streamlit as st
import time
from ui.components.image_display import display_mtf_stimulus_image
from ui.components.response_buttons import create_response_buttons
from ui.components.progress_indicators import (
    show_trial_progress, show_animated_fixation, show_feedback_message
)
from utils.logger import get_logger
from config.settings import PRACTICE_TRIAL_LIMIT, MAX_TRIALS, MIN_TRIALS, CONVERGENCE_THRESHOLD, STIMULUS_DURATION

logger = get_logger(__name__)

def _perform_ado_computation_during_fixation(session_manager, experiment_controller):
    """
    Perform ADO computation during fixation period and update previous trial
    
    Args:
        session_manager: SessionStateManager instance
        experiment_controller: ExperimentController instance
    """
    try:
        # Only perform ADO computation if we have completed at least one trial
        trial_results = session_manager.get_trial_results()
        if not trial_results:
            logger.debug("No previous trials for ADO computation")
            return
        
        # Skip ADO computation for practice trials
        if session_manager.is_practice_mode():
            logger.debug("Skipping ADO computation in practice mode")
            return
        
        # Ensure experiment_controller is available
        if experiment_controller is None:
            logger.warning("Experiment controller not available for ADO computation")
            return
        
        # Compute next stimulus value using ADO
        next_stimulus_value = experiment_controller.compute_next_stimulus_ado()
        if next_stimulus_value is not None:
            # Update the previous trial's ado_stimulus_value with the computed value
            success = experiment_controller.update_previous_trial_ado_value(next_stimulus_value)
            if success:
                logger.info(f"ADO computation completed: next stimulus = {next_stimulus_value:.2f}")
            else:
                logger.warning("Failed to update previous trial with ADO computation result")
        else:
            logger.warning("ADO computation returned no result")
            
    except Exception as e:
        logger.error(f"Error during ADO computation in fixation: {e}")

def _log_trial_counter_status(session_manager):
    """Log current trial counter status for debugging"""
    logger.debug(f"📊 Trial counter status:")
    logger.debug(f"   Practice mode: {session_manager.is_practice_mode()}")
    logger.debug(f"   Current trial: {session_manager.get_current_trial()}")
    logger.debug(f"   Experiment trial: {session_manager.get_experiment_trial()}")
    logger.debug(f"   Practice trials completed: {session_manager.get_practice_trials_completed()}")
    logger.debug(f"   Total trials: {session_manager.get_total_trials()}")

def display_trial_screen(session_manager, experiment_controller) -> None:
    """
    Display trial screen for MTF experiment
    
    Args:
        session_manager: SessionStateManager instance
        experiment_controller: ExperimentController instance
    """
    try:
        # Ensure experiment_controller is available
        if experiment_controller is None:
            from core.experiment_controller import ExperimentController
            experiment_controller = ExperimentController(session_manager)
            st.session_state.experiment_controller = experiment_controller
            logger.info("🔧 Recreated experiment controller for trial screen")
        
        # Add counter validation and debug logging
        _log_trial_counter_status(session_manager)
        
        # Check practice mode completion first
        if session_manager.is_practice_mode():
            practice_completed = session_manager.get_practice_trials_completed()
            if practice_completed >= PRACTICE_TRIAL_LIMIT:  # Practice limit: configurable trials
                logger.info(f"📋 Practice mode completed: {practice_completed}/{PRACTICE_TRIAL_LIMIT} trials")
                _display_practice_completion(session_manager)
                return
        
        # Note: Experiment completion check moved to AFTER trial processing
        # This ensures the last trial is properly processed and saved
        
        # Show progress
        progress = experiment_controller.get_experiment_progress()
        show_trial_progress(
            progress['current_trial'],
            progress['total_trials'],
            progress['is_practice'],
            session_manager.get_practice_trials_completed()
        )
        
        # Get current trial data
        trial_data = session_manager.get_mtf_trial_data()
        
        # If no trial data, prepare new trial
        if trial_data is None:
            trial_data = experiment_controller.prepare_trial()
            if trial_data is None:
                st.error("無法準備試驗數據")
                return
        
        # Display trial content
        _display_trial_content(trial_data, session_manager, experiment_controller)
        
    except Exception as e:
        logger.error(f"Error in trial screen: {e}")
        st.error(f"Error in trial screen: {e}")

def _display_trial_content(trial_data, session_manager, experiment_controller):
    """Display the actual trial content"""
    
    # Show fixation or stimulus based on timing
    if 'trial_phase' not in st.session_state:
        st.session_state.trial_phase = 'fixation'
        st.session_state.phase_start_time = time.time()
    
    # Safely calculate phase elapsed time with None check
    current_time = time.time()
    phase_start_time = st.session_state.get('phase_start_time')
    if phase_start_time is not None:
        phase_elapsed = current_time - phase_start_time
    else:
        # Fallback: reset phase start time to now
        logger.warning("phase_start_time is None, resetting to current time")
        st.session_state.phase_start_time = current_time
        phase_elapsed = 0.0
    
    if st.session_state.trial_phase == 'fixation':
        # Show fixation cross
        show_animated_fixation(phase_elapsed)
        
        # ADO computation during fixation has been disabled to ensure timing accuracy
        # If you need ADO computation, it can be re-enabled in future versions
        
        # Check if fixation period is over
        fixation_duration = session_manager.get_fixation_duration()
        if phase_elapsed >= fixation_duration:
            st.session_state.trial_phase = 'stimulus'
            st.session_state.phase_start_time = current_time
            # ADO computation flag reset removed (ADO computation disabled)
            st.rerun()
        else:
            # Auto-refresh every 100ms to update animation
            time.sleep(0.1)
            st.rerun()
        
        # Explicitly return to prevent any UI elements below from rendering during fixation
        return
    
    elif st.session_state.trial_phase == 'stimulus':
        # Show stimulus image
        st.subheader("請判斷圖像是否清楚")
        
        image_data = trial_data.get('stimulus_image')
        mtf_value = trial_data.get('mtf_value', 0)
        
        display_mtf_stimulus_image(
            image_data,
            caption=f"MTF 值: {mtf_value:.1f}" if session_manager.get_show_trial_feedback() else ""
        )
        
        # Add spacing to prevent button overlap with image
        st.markdown("<div style='margin: 30px 0;'></div>", unsafe_allow_html=True)
        
        # Response buttons (restored to original horizontal layout)
        # Use appropriate trial counter based on mode
        trial_key = session_manager.get_experiment_trial() if not session_manager.is_practice_mode() else session_manager.get_practice_trials_completed()
        left_pressed, right_pressed = create_response_buttons(
            left_label="不清楚",
            right_label="清楚",
            key_suffix=f"trial_{trial_key}_{'exp' if not session_manager.is_practice_mode() else 'practice'}"
        )
        
        # Process response
        if left_pressed or right_pressed:
            response = "not_clear" if left_pressed else "clear"
            # Safely calculate response time with None check
            phase_start_time = st.session_state.get('phase_start_time')
            if phase_start_time is not None:
                response_time = time.time() - phase_start_time
            else:
                logger.warning("phase_start_time is None, using default response time")
                response_time = 0.5  # Default fallback response time
            
            # Process the response
            if experiment_controller.process_response(response, response_time):
                # Save trial data using simplified practice/experiment logic
                trial_results = session_manager.get_trial_results()
                if trial_results:
                    latest_result = trial_results[-1]
                    
                    # Double-check practice mode using session manager state as primary source
                    is_practice_trial = session_manager.is_practice_mode()
                    trial_number = latest_result.get('trial_number', 'unknown')
                    
                    # Also verify with trial data as secondary check
                    data_is_practice = latest_result.get('is_practice', False)
                    if is_practice_trial != data_is_practice:
                        logger.warning(f"⚠️ Practice mode mismatch: session={is_practice_trial}, data={data_is_practice}")
                    
                    if is_practice_trial == False:  # Experiment trial
                        # Storage enabled - save data immediately and verify success
                        logger.info(f"🖾 Attempting to save EXPERIMENT trial {trial_number}")
                        save_success = experiment_controller.save_trial_data(latest_result)
                        if save_success:
                            logger.info(f"✅ EXPERIMENT trial {trial_number} data saved successfully")
                        else:
                            logger.error(f"❌ Failed to save EXPERIMENT trial {trial_number} data")
                            st.error("⚠️ 資料儲存失敗，請記下此試驗結果")
                    
                    elif is_practice_trial == True:  # Practice trial
                        # Storage disabled - only log the event
                        logger.info(f"🏃 PRACTICE trial {trial_number} - storage disabled")
                
                # Show feedback if enabled
                if session_manager.get_show_trial_feedback():
                    st.session_state.trial_phase = 'feedback'
                    st.session_state.feedback_response = response
                    st.session_state.feedback_time = response_time
                else:
                    # Go directly to next trial
                    _prepare_next_trial(session_manager)
                
                st.rerun()
    
    elif st.session_state.trial_phase == 'feedback':
        # Show neutral feedback without right/wrong judgment
        response = st.session_state.get('feedback_response', 'unknown')
        response_time = st.session_state.get('feedback_time', 0)
        
        # Show response confirmation and timing
        st.success(f"✅ 回應已記錄: {'清楚' if response == 'clear' else '不清楚'}")
        st.info(f"⏱️ 反應時間: {response_time * 1000:.0f} ms")
        
        # Show ADO data if available and enabled
        _display_ado_feedback(trial_data, session_manager)
        
        # Continue button
        if st.button("繼續下一試驗", key="continue_trial"):
            _prepare_next_trial(session_manager)
            st.rerun()

def _prepare_next_trial(session_manager):
    """Prepare for next trial or complete experiment if done"""
    from core.experiment_controller import ExperimentController
    
    # Log trial counter status before completion check
    _log_trial_counter_status(session_manager)
    
    # Check if experiment is complete AFTER all trial processing is done
    experiment_controller = ExperimentController(session_manager)
    if experiment_controller.check_experiment_completion():
        logger.info(f"🏁 Experiment completion detected - transitioning to results")
        # All trials completed - proceed to results
        experiment_controller.finalize_experiment_in_database()
        experiment_controller.complete_experiment()
        session_manager.set_experiment_stage('results')
        return  # Don't clear trial data, let results screen handle it
    
    # Clear trial-specific session state for next trial
    keys_to_clear = [
        'trial_phase', 'phase_start_time', 'feedback_response', 'feedback_time'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear trial data to trigger new trial preparation
    session_manager.set_mtf_trial_data(None)

def _display_practice_completion(session_manager):
    """Display practice completion screen"""
    st.header("🎯 練習完成！")
    st.success(f"您已完成 {PRACTICE_TRIAL_LIMIT} 次練習試驗")
    
    st.markdown("### 練習結果概要")
    practice_completed = session_manager.get_practice_trials_completed()
    st.info(f"完成練習次數: {practice_completed} 次")
    
    st.markdown("### 下一步選擇")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 再練習一次", key="retry_practice", use_container_width=True):
            # Reset practice trials and stay in practice mode
            logger.info(f"🔄 Restarting practice mode")
            logger.info(f"   Previous practice trials: {session_manager.get_practice_trials_completed()}")
            
            # Reset practice counters properly
            session_manager.reset_practice_counters()
            session_manager.set_mtf_trial_data(None)
            
            # Validate reset
            logger.info(f"   Post-reset - Practice trials: {session_manager.get_practice_trials_completed()}")
            logger.info(f"   Post-reset - Practice mode: {session_manager.is_practice_mode()}")
            
            # Recreate MTF experiment manager for practice mode
            from mtf_experiment import MTFExperimentManager
            st.session_state.mtf_experiment_manager = MTFExperimentManager(
                max_trials=MAX_TRIALS,
                min_trials=MIN_TRIALS,
                convergence_threshold=CONVERGENCE_THRESHOLD,
                participant_id=session_manager.get_participant_id(),
                base_image_path=st.session_state.get('selected_stimulus_image'),
                is_practice=True  # Reset for practice mode
            )
            logger.info("🔄 MTF experiment manager recreated for practice mode (practice=True)")
            
            # Clear trial-specific session state
            keys_to_clear = ['trial_phase', 'phase_start_time', 'feedback_response', 'feedback_time']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        if st.button("🚀 開始正式實驗", key="start_experiment", use_container_width=True):
            # Switch to experiment mode and reset counters properly
            logger.info(f"🔄 Starting experiment mode transition")
            logger.info(f"   Practice trials completed: {session_manager.get_practice_trials_completed()}")
            
            # Use session manager's proper transition method
            session_manager.set_practice_mode(False)  # This will reset experiment counters
            session_manager.set_mtf_trial_data(None)
            
            # Validate counter reset
            logger.info(f"   Post-transition - Current trial: {session_manager.get_current_trial()}")
            logger.info(f"   Post-transition - Experiment trial: {session_manager.get_experiment_trial()}")
            logger.info(f"   Post-transition - Practice mode: {session_manager.is_practice_mode()}")
            
            # Recreate MTF experiment manager for main experiment (non-practice mode)
            from mtf_experiment import MTFExperimentManager
            st.session_state.mtf_experiment_manager = MTFExperimentManager(
                max_trials=MAX_TRIALS,
                min_trials=MIN_TRIALS,
                convergence_threshold=CONVERGENCE_THRESHOLD,
                participant_id=session_manager.get_participant_id(),
                base_image_path=st.session_state.get('selected_stimulus_image'),
                is_practice=False  # This is the main experiment
            )
            logger.info("🔄 MTF experiment manager recreated for main experiment (practice=False)")
            
            # Ensure experiment record is created for database storage
            if not session_manager.get_experiment_id():
                experiment_id = session_manager.create_experiment_record(
                    experiment_type="MTF_Clarity",
                    use_ado=True,
                    max_trials=MAX_TRIALS,
                    min_trials=MIN_TRIALS,
                    convergence_threshold=CONVERGENCE_THRESHOLD,
                    stimulus_duration=STIMULUS_DURATION,
                    num_practice_trials=session_manager.get_practice_trials_completed()
                )
                if experiment_id:
                    logger.info(f"✅ Experiment record created for main experiment: {experiment_id}")
                else:
                    logger.warning("⚠️ Failed to create experiment record, continuing with CSV-only storage")
            
            # Clear trial-specific session state
            keys_to_clear = ['trial_phase', 'phase_start_time', 'feedback_response', 'feedback_time']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            logger.info(f"🏁 Practice completed ({session_manager.get_practice_trials_completed()} trials), starting main experiment")
            logger.info(f"🖾 Experiment trial counter reset to: {session_manager.get_experiment_trial()}")
            st.rerun()
    
    st.markdown("---")
    st.info("💡 **提示**: 練習模式的數據不會被儲存，只有正式實驗的數據會被存下來")

def _display_ado_feedback(trial_data, session_manager):
    """Display ADO feedback information"""
    try:
        # Check if MTF experiment manager is available
        if 'mtf_experiment_manager' not in st.session_state:
            logger.warning("MTF experiment manager not available for ADO feedback")
            return
        
        exp_manager = st.session_state.mtf_experiment_manager
        
        # Check if ADO engine exists and has the required methods
        if not hasattr(exp_manager, 'ado_engine') or exp_manager.ado_engine is None:
            logger.warning("ADO engine not available for feedback")
            return
        
        ado_engine = exp_manager.ado_engine
        
        # Get parameter estimates
        if hasattr(ado_engine, 'get_parameter_estimates'):
            try:
                estimates = ado_engine.get_parameter_estimates()
                
                # Display ADO feedback
                st.markdown("### 🤖 ADO 回饋資訊")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "估計閾值 (MTF %)", 
                        f"{estimates.get('threshold_mean', 0):.1f}%",
                        help="ADO 目前估計的清晰度閾值"
                    )
                    st.metric(
                        "閾值不確定性", 
                        f"±{estimates.get('threshold_sd', 0):.2f}",
                        help="估計的標準差，越小表示越確定"
                    )
                
                with col2:
                    st.metric(
                        "斜率估計", 
                        f"{estimates.get('slope_mean', 0):.2f}",
                        help="心理測量函數的斜率"
                    )
                    st.metric(
                        "斜率不確定性", 
                        f"±{estimates.get('slope_sd', 0):.2f}",
                        help="斜率估計的標準差"
                    )
                
                # Display current trial MTF value
                if trial_data and 'mtf_value' in trial_data:
                    st.info(f"🎯 本次試驗 MTF 值: {trial_data['mtf_value']:.1f}%")
                
                # Show convergence information
                threshold_sd = estimates.get('threshold_sd', float('inf'))
                if threshold_sd < CONVERGENCE_THRESHOLD:  # Convergence threshold
                    st.success("✅ ADO 已收斂，估計值較為可靠")
                else:
                    remaining_uncertainty = threshold_sd - CONVERGENCE_THRESHOLD
                    st.warning(f"⏳ ADO 尚未收斂 (剩餘不確定性: {remaining_uncertainty:.2f})")
                
            except Exception as e:
                logger.error(f"Error getting ADO parameter estimates: {e}")
                st.warning("⚠️ 無法取得 ADO 參數估計")
        
        else:
            logger.warning("ADO engine does not have get_parameter_estimates method")
            st.warning("⚠️ ADO 引擎不支援參數估計顯示")
    
    except Exception as e:
        logger.error(f"Error displaying ADO feedback: {e}")
        st.warning("⚠️ ADO 回饋顯示錯誤")