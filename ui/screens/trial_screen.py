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

logger = get_logger(__name__)

def display_trial_screen(session_manager, experiment_controller) -> None:
    """
    Display trial screen for MTF experiment
    
    Args:
        session_manager: SessionStateManager instance
        experiment_controller: ExperimentController instance
    """
    try:
        # Check practice mode completion first
        if session_manager.is_practice_mode():
            practice_completed = session_manager.get_practice_trials_completed()
            if practice_completed >= 5:  # Practice limit: 5 trials
                _display_practice_completion(session_manager)
                return
        
        # Check if experiment is complete
        if experiment_controller.check_experiment_completion():
            experiment_controller.complete_experiment()
            session_manager.set_experiment_stage('results')
            st.rerun()
            return
        
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
    
    current_time = time.time()
    phase_elapsed = current_time - st.session_state.phase_start_time
    
    if st.session_state.trial_phase == 'fixation':
        # Show fixation cross
        show_animated_fixation(phase_elapsed)
        
        # Check if fixation period is over
        fixation_duration = session_manager.get_fixation_duration()
        if phase_elapsed >= fixation_duration:
            st.session_state.trial_phase = 'stimulus'
            st.session_state.phase_start_time = current_time
            st.rerun()
        else:
            # Auto-refresh every 100ms to update animation
            time.sleep(0.1)
            st.rerun()
    
    elif st.session_state.trial_phase == 'stimulus':
        # Show stimulus image
        st.subheader("請判斷圖像是否清楚")
        
        image_data = trial_data.get('stimulus_image')
        mtf_value = trial_data.get('mtf_value', 0)
        
        display_mtf_stimulus_image(
            image_data,
            caption=f"MTF 值: {mtf_value:.1f}" if session_manager.get_show_trial_feedback() else ""
        )
        
        # Response buttons
        left_pressed, right_pressed = create_response_buttons(
            left_label="不清楚",
            right_label="清楚",
            key_suffix=f"trial_{session_manager.get_current_trial()}"
        )
        
        # Process response
        if left_pressed or right_pressed:
            response = "not_clear" if left_pressed else "clear"
            response_time = time.time() - st.session_state.phase_start_time
            
            # Process the response
            if experiment_controller.process_response(response, response_time):
                # Note: Practice trial counter is incremented in experiment_controller.process_response()
                # No need to increment here to avoid double counting
                
                # Save trial data
                trial_results = session_manager.get_trial_results()
                if trial_results:
                    latest_result = trial_results[-1]
                    experiment_controller.save_trial_data(latest_result)
                
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
    """Prepare for next trial"""
    # Clear trial-specific session state
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
    st.success("您已完成 5 次練習試驗")
    
    st.markdown("### 練習結果概要")
    practice_completed = session_manager.get_practice_trials_completed()
    st.info(f"完成練習次數: {practice_completed} 次")
    
    st.markdown("### 下一步選擇")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 再練習一次", key="retry_practice", use_container_width=True):
            # Reset practice trials and stay in practice mode
            st.session_state.practice_trials_completed = 0
            session_manager.set_mtf_trial_data(None)
            # Clear trial-specific session state
            keys_to_clear = ['trial_phase', 'phase_start_time', 'feedback_response', 'feedback_time']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        if st.button("🚀 開始正式實驗", key="start_experiment", use_container_width=True):
            # Switch to experiment mode
            session_manager.set_practice_mode(False)
            st.session_state.current_trial = 0  # Reset trial counter
            session_manager.set_mtf_trial_data(None)
            # Clear trial-specific session state
            keys_to_clear = ['trial_phase', 'phase_start_time', 'feedback_response', 'feedback_time']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            logger.info("Practice completed, starting main experiment")
            st.rerun()
    
    st.markdown("---")
    st.info("💡 **提示**: 練習模式的數據不會被記錄，正式實驗的數據將被保存")

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
                        help="估計的標準偏差，越小表示越確定"
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
                        help="斜率估計的標準偏差"
                    )
                
                # Display current trial MTF value
                if trial_data and 'mtf_value' in trial_data:
                    st.info(f"🎯 本次試驗 MTF 值: {trial_data['mtf_value']:.1f}%")
                
                # Show convergence information
                threshold_sd = estimates.get('threshold_sd', float('inf'))
                if threshold_sd < 0.15:  # Convergence threshold
                    st.success("✅ ADO 已收斂，估計較為可靠")
                else:
                    remaining_uncertainty = threshold_sd - 0.15
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