"""
Trial screen for WebRS MTF Threshold experiment.
"""
import streamlit as st
import time
from ui.components.image_display import display_mtf_stimulus_image
from ui.components.response_buttons import create_response_buttons
from ui.components.progress_indicators import (
    show_trial_progress, show_animated_fixation, show_css_fixation_with_timer, show_feedback_message
)
try:
    from ui.components.gif_animations import show_gif_fixation_with_timer
    GIF_ANIMATION_AVAILABLE = True
except ImportError:
    GIF_ANIMATION_AVAILABLE = False
from utils.logger import get_logger
from config.settings import (
    PRACTICE_TRIAL_LIMIT, MAX_TRIALS, MIN_TRIALS, CONVERGENCE_THRESHOLD, STIMULUS_DURATION,
    FIXATION_ANIMATION_TYPE
)

logger = get_logger(__name__)

def _pregenerate_next_image_during_fixation(session_manager, experiment_controller):
    """
    Pregenerate next trial's image during fixation period to improve performance
    
    This function utilizes the 3-second fixation window to:
    1. Predict the next MTF value using ADO or statistical methods
    2. Pre-generate and cache the stimulus image + base64 encoding
    3. Dramatically reduce trial display latency from 3s to <100ms
    
    Args:
        session_manager: SessionStateManager instance
        experiment_controller: ExperimentController instance
    """
    try:
        # Check if pregeneration has already been done for this fixation
        if hasattr(st.session_state, 'pregeneration_completed') and st.session_state.pregeneration_completed:
            return
            
        # Only pregenerate if MTF experiment manager is available
        if 'mtf_experiment_manager' not in st.session_state:
            logger.debug("MTF experiment manager not available for pregeneration")
            return
            
        exp_manager = st.session_state.mtf_experiment_manager
        
        # Skip pregeneration for practice trials (use simpler random prediction)
        if session_manager.is_practice_mode():
            logger.debug("Using simple prediction for practice mode pregeneration")
            # Simple random prediction for practice
            import numpy as np
            predicted_mtf = float(np.random.choice(np.arange(20, 80, 10)))
        else:
            # Try to predict next MTF value using ADO
            predicted_mtf = _predict_next_mtf_value(exp_manager, session_manager)
            
        if predicted_mtf is not None:
            logger.info(f"🚀 Pregeneration started: MTF {predicted_mtf:.1f}% during fixation")
            
            # Pre-generate and cache the base64 image
            start_time = time.time()
            pregenerated_base64 = exp_manager.generate_and_cache_base64_image(predicted_mtf)
            end_time = time.time()
            
            if pregenerated_base64:
                pregeneration_time = (end_time - start_time) * 1000
                logger.info(f"✅ Pregeneration completed in {pregeneration_time:.2f}ms: MTF {predicted_mtf:.1f}%")
                
                # Store pregeneration info for debugging
                st.session_state.pregeneration_mtf = predicted_mtf
                st.session_state.pregeneration_time = pregeneration_time
                st.session_state.pregeneration_completed = True
                
            else:
                logger.warning(f"⚠️ Pregeneration failed for MTF {predicted_mtf:.1f}%")
        else:
            logger.debug("No MTF prediction available, skipping pregeneration")
            
    except Exception as e:
        logger.error(f"Error during image pregeneration in fixation: {e}")

def _predict_next_mtf_value(exp_manager, session_manager):
    """
    Predict the next MTF value using available methods
    
    Returns:
        float or None: Predicted MTF value
    """
    try:
        # Method 1: Use ADO engine prediction if available
        if hasattr(exp_manager, 'ado_engine') and exp_manager.ado_engine is not None:
            try:
                predicted_mtf = exp_manager.ado_engine.get_optimal_design()
                if predicted_mtf is not None:
                    logger.debug(f"ADO prediction: {predicted_mtf:.1f}%")
                    return predicted_mtf
            except Exception as e:
                logger.debug(f"ADO prediction failed: {e}")
        
        # Method 2: Statistical prediction based on trial history
        trial_results = session_manager.get_trial_results()
        if trial_results and len(trial_results) >= 2:
            # Simple trend-based prediction using last few trials
            recent_mtf_values = [trial.get('mtf_value', 50) for trial in trial_results[-3:]]
            if recent_mtf_values:
                import numpy as np
                # Use median of recent values with some randomness
                base_prediction = np.median(recent_mtf_values)
                # Add some variation based on response pattern
                variation = np.random.normal(0, 10)  # ±10% variation
                predicted_mtf = np.clip(base_prediction + variation, 5, 95)
                logger.debug(f"Statistical prediction: {predicted_mtf:.1f}% (based on {recent_mtf_values})")
                return predicted_mtf
                
        # Method 3: Fallback to common range
        import numpy as np
        fallback_mtf = float(np.random.choice([20, 30, 40, 50, 60, 70, 80]))
        logger.debug(f"Fallback prediction: {fallback_mtf:.1f}%")
        return fallback_mtf
        
    except Exception as e:
        logger.error(f"Error in MTF prediction: {e}")
        return None

def _display_stimulus_with_staged_loading(trial_data, session_manager, experiment_controller):
    """Display stimulus screen with staged loading for better UX"""
    try:
        from ui.components.staged_loading import show_loading_progress
        
        # Initialize staged containers if not exists
        if 'stimulus_containers' not in st.session_state:
            st.session_state.stimulus_containers = {
                'header': st.empty(),
                'progress': st.empty(),
                'content': st.empty(),
                'controls': st.empty()
            }
            
            # Flag to track if this is first load of stimulus
            st.session_state.stimulus_first_load = True
        
        containers = st.session_state.stimulus_containers
        
        # Stage 1: Header (immediate)
        with containers['header'].container():
            st.subheader("請判斷圖像是否清楚")
        
        # Stage 2: Progress indicator (quick)
        if st.session_state.stimulus_first_load:
            time.sleep(0.05)  # Very brief delay
            
        with containers['progress'].container():
            progress = experiment_controller.get_experiment_progress()
            from ui.components.progress_indicators import show_trial_progress
            show_trial_progress(
                progress['current_trial'],
                progress['total_trials'],
                progress['is_practice'],
                session_manager.get_practice_trials_completed()
            )
        
        # Stage 3: Content area with loading (medium delay)
        if st.session_state.stimulus_first_load:
            with containers['content'].container():
                show_loading_progress("載入刺激圖片", steps=3, step_delay=0.15)
            
        # Stage 4: Actual image (after loading)
        with containers['content'].container():
            image_data = trial_data.get('stimulus_image')
            mtf_value = trial_data.get('mtf_value', 0)
            
            display_mtf_stimulus_image(
                image_data,
                caption=f"MTF 值: {mtf_value:.1f}" if session_manager.get_show_trial_feedback() else "",
                staged_loading=False  # Already staged at higher level
            )
            
            # Add spacing
            st.markdown("<div style='margin: 30px 0;'></div>", unsafe_allow_html=True)
        
        # Stage 5: Controls (final stage - response buttons)
        with containers['controls'].container():
            # Use appropriate trial counter based on mode  
            trial_key = session_manager.get_experiment_trial() if not session_manager.is_practice_mode() else session_manager.get_practice_trials_completed()
            
            left_pressed, right_pressed = create_response_buttons(
                left_label="不清楚",
                right_label="清楚",
                key_suffix=f"trial_{trial_key}_{'exp' if not session_manager.is_practice_mode() else 'practice'}"
            )
            
            # Store response data in session state for processing outside this function
            st.session_state.trial_response_data = {
                'left_pressed': left_pressed,
                'right_pressed': right_pressed
            }
        
        # Mark that first load is complete
        st.session_state.stimulus_first_load = False
        
    except Exception as e:
        logger.error(f"Error in staged stimulus loading: {e}")
        # Fallback to regular display
        st.subheader("請判斷圖像是否清楚")
        
        image_data = trial_data.get('stimulus_image')
        mtf_value = trial_data.get('mtf_value', 0)
        
        display_mtf_stimulus_image(
            image_data,
            caption=f"MTF 值: {mtf_value:.1f}" if session_manager.get_show_trial_feedback() else ""
        )
        
        st.markdown("<div style='margin: 30px 0;'></div>", unsafe_allow_html=True)

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
        fixation_duration = session_manager.get_fixation_duration()
        
        # Choose animation type based on configuration
        if phase_elapsed < 0.1:  # Only initialize animation once at the beginning
            animation_started = False
            
            if FIXATION_ANIMATION_TYPE == "gif" and GIF_ANIMATION_AVAILABLE:
                try:
                    show_gif_fixation_with_timer(fixation_duration, show_progress=True)
                    logger.debug(f"🎬 Started GIF fixation animation for {fixation_duration:.1f}s")
                    animation_started = True
                except Exception as e:
                    logger.warning(f"GIF animation failed: {e}, falling back to CSS")
            
            if not animation_started and FIXATION_ANIMATION_TYPE in ["css", "gif"]:
                # Use CSS animation (default or fallback)
                show_css_fixation_with_timer(fixation_duration, show_progress=True)
                logger.debug(f"🎬 Started CSS fixation animation for {fixation_duration:.1f}s")
                animation_started = True
            
            if not animation_started:
                # Legacy fallback
                show_animated_fixation(phase_elapsed)
                logger.debug(f"🎬 Using legacy fixation animation")
        
        # Pregenerate next image during fixation to improve performance
        # This utilizes the 3-second fixation window for image preparation
        if phase_elapsed >= 1.5:  # Start pregeneration after 1.5 seconds (avoid early animation period)
            _pregenerate_next_image_during_fixation(session_manager, experiment_controller)
        
        # Check if fixation period is over
        if phase_elapsed >= fixation_duration:
            st.session_state.trial_phase = 'stimulus'
            st.session_state.phase_start_time = current_time
            st.rerun()
        else:
            # Refresh rate depends on animation type
            if FIXATION_ANIMATION_TYPE == "legacy":
                time.sleep(0.1)  # Frequent updates needed for legacy animation
            else:
                time.sleep(0.2)  # Less frequent updates for CSS/GIF animations
            st.rerun()
        
        # Explicitly return to prevent any UI elements below from rendering during fixation
        return
    
    elif st.session_state.trial_phase == 'stimulus':
        # Use staged loading for better UX: header → progress → placeholder → controls → image
        _display_stimulus_with_staged_loading(trial_data, session_manager, experiment_controller)
        
        # Get response data from staged loading
        response_data = st.session_state.get('trial_response_data', {'left_pressed': False, 'right_pressed': False})
        left_pressed = response_data['left_pressed']
        right_pressed = response_data['right_pressed']
        
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
        'trial_phase', 'phase_start_time', 'feedback_response', 'feedback_time',
        'pregeneration_completed', 'pregeneration_mtf', 'pregeneration_time',  # Clear pregeneration flags
        'stimulus_containers', 'stimulus_first_load', 'trial_response_data',  # Clear staged loading data
        'image_container'  # Clear image containers
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
            keys_to_clear = ['trial_phase', 'phase_start_time', 'feedback_response', 'feedback_time', 
                           'pregeneration_completed', 'pregeneration_mtf', 'pregeneration_time']
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
            keys_to_clear = ['trial_phase', 'phase_start_time', 'feedback_response', 'feedback_time', 
                           'pregeneration_completed', 'pregeneration_mtf', 'pregeneration_time']
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