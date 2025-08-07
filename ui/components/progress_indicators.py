"""
Progress indicators and status displays for WebRS MTF Threshold experiment.
"""
import streamlit as st
import time
from typing import Optional
from utils.logger import get_logger
from config.settings import PRACTICE_TRIAL_LIMIT

logger = get_logger(__name__)

def show_animated_fixation(elapsed: float) -> None:
    """
    Display animated fixation cross with progress indication (Legacy - use show_css_fixation_with_timer for better performance)
    
    Args:
        elapsed: Elapsed time in seconds
    """
    try:
        # Calculate rotation angle based on elapsed time
        rotation_angle = (elapsed * 360) % 360
        
        # Create animated fixation cross
        fixation_html = f"""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: 300px;
            font-size: 48px;
            color: #333;
            background: #f0f0f0;
            border-radius: 10px;
            margin: 20px 0;
        ">
            <div style="
                transform: rotate({rotation_angle}deg);
                transition: transform 0.1s ease-in-out;
                font-weight: bold;
            ">+</div>
        </div>
        """
        
        st.markdown(fixation_html, unsafe_allow_html=True)
        
        # Show elapsed time
        st.info(f"⏱️ Fixation: {elapsed:.1f}s")
        
    except Exception as e:
        logger.error(f"Error showing animated fixation: {e}")
        # Fallback to simple display
        st.markdown("### <center>+</center>", unsafe_allow_html=True)

def show_resumable_css_fixation(duration: float, elapsed_time: float) -> None:
    """
    Display a CSS-animated fixation cross that can be resumed.
    This version uses animation-delay to sync with Python's rerun loop.
    
    Args:
        duration: Total duration of the fixation in seconds.
        elapsed_time: The time that has already passed in seconds.
    """
    try:
        # Unique ID for this instance to avoid CSS conflicts
        fixation_id = f"fixation_{int(time.time() * 1000)}"
        
        # Negative animation-delay starts the animation partway through
        animation_delay = -elapsed_time
        
        fixation_html = f"""
        <style>
        #{fixation_id} .fixation-cross {{
            font-weight: bold;
            animation: rotate-pulse {duration}s linear {animation_delay}s;
            animation-play-state: running;
        }}
        
        #{fixation_id} .progress-ring {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 100px;
            height: 100px;
            border: 3px solid #ddd;
            border-top: 3px solid #007bff;
            border-radius: 50%;
            animation: progress-fill {duration}s linear {animation_delay}s;
            animation-play-state: running;
            opacity: 0.7;
        }}

        @keyframes rotate-pulse {{
            0% {{ transform: rotate(0deg) scale(1); }}
            25% {{ transform: rotate(90deg) scale(1.1); }}
            50% {{ transform: rotate(180deg) scale(1); }}
            75% {{ transform: rotate(270deg) scale(1.1); }}
            100% {{ transform: rotate(360deg) scale(1); }}
        }}
        
        @keyframes progress-fill {{
            0% {{ transform: translate(-50%, -50%) rotate(0deg); }}
            100% {{ transform: translate(-50%, -50%) rotate(360deg); }}
        }}
        </style>
        
        <div id="{fixation_id}" style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: 300px;
            font-size: 48px;
            color: #333;
            background: #f0f0f0;
            border-radius: 10px;
            margin: 20px 0;
            position: relative;
        ">
            <div class="fixation-cross">+</div>
            <div class="progress-ring"></div>
        </div>
        """
        st.markdown(fixation_html, unsafe_allow_html=True)

    except Exception as e:
        logger.error(f"Error showing resumable CSS fixation: {e}")
        st.markdown("### <center>+</center>", unsafe_allow_html=True)
        
        st.markdown(fixation_html, unsafe_allow_html=True)
        
    except Exception as e:
        logger.error(f"Error showing CSS fixation: {e}")
        # Fallback to simple display
        st.markdown("### <center>+</center>", unsafe_allow_html=True)

def show_trial_progress(current_trial: int, total_trials: int, is_practice: bool = False, practice_completed: int = 0) -> None:
    """
    Display trial progress information
    
    Args:
        current_trial: Current trial number
        total_trials: Total number of trials
        is_practice: Whether in practice mode
        practice_completed: Number of practice trials completed
    """
    try:
        if is_practice:
            # Display practice counter starting from 1 for user-friendly display
            display_count = practice_completed + 1 if practice_completed < PRACTICE_TRIAL_LIMIT else PRACTICE_TRIAL_LIMIT
            practice_progress = practice_completed / PRACTICE_TRIAL_LIMIT if PRACTICE_TRIAL_LIMIT > 0 else 0
            st.progress(practice_progress)
            st.info(f"🎯 練習試驗: {display_count}/{PRACTICE_TRIAL_LIMIT} ({practice_progress:.1%})")
        else:
            progress = current_trial / total_trials if total_trials > 0 else 0
            st.progress(progress)
            st.write(f"📊 試驗進度: {current_trial}/{total_trials} ({progress:.1%})")
            
    except Exception as e:
        logger.error(f"Error showing trial progress: {e}")

def show_experiment_status(stage: str, participant_id: Optional[str] = None, session_manager=None) -> None:
    """
    Display current experiment status with rich information
    
    Args:
        stage: Current experiment stage
        participant_id: Participant identifier
        session_manager: Session manager for detailed info
    """
    try:
        st.sidebar.markdown("### 🔬 實驗狀態")
        
        status_messages = {
            'welcome': '🏠 歡迎頁面',
            'instructions': '📋 實驗說明',
            'trial': '🧪 實驗進行中',
            'results': '📊 結果頁面',
            'benchmark': '⚡ 效能基準測試'
        }
        
        status_text = status_messages.get(stage, f'❓ 未知階段: {stage}')
        st.sidebar.info(f"📍 當前狀態: {status_text}")
        
        if participant_id:
            st.sidebar.success(f"👤 參與者: {participant_id}")
        
        # Add rich experiment information if session manager is available
        if session_manager:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 📊 實驗資訊")
            
            # Show trial progress
            if stage == 'trial':
                current_trial = session_manager.get_current_trial()
                total_trials = session_manager.get_total_trials()
                is_practice = session_manager.is_practice_mode()
                
                if is_practice:
                    practice_completed = session_manager.get_practice_trials_completed()
                    # Display practice counter starting from 1 for user-friendly display
                    display_count = practice_completed + 1 if practice_completed < PRACTICE_TRIAL_LIMIT else PRACTICE_TRIAL_LIMIT
                    st.sidebar.metric("練習進度", f"{display_count}/{PRACTICE_TRIAL_LIMIT}")
                    st.sidebar.metric("練習模式", "✅ 啟用")
                else:
                    st.sidebar.metric("試驗進度", f"{current_trial}/{total_trials}")
                    st.sidebar.metric("正式實驗", "🚀 進行中")
            
            # Show settings
            show_feedback = session_manager.get_show_trial_feedback()
            fixation_duration = session_manager.get_fixation_duration()
            
            st.sidebar.metric("回饋顯示", "✅ 開啟" if show_feedback else "❌ 關閉")
            st.sidebar.metric("固視時間", f"{fixation_duration:.1f}s")
            
            # Show data status (separate practice and experiment trials)
            saved_trials = session_manager.get_saved_trials()
            all_trial_results = session_manager.get_trial_results()
            
            # Filter practice and experiment trials
            practice_trials = [t for t in all_trial_results if t.get('is_practice', False)]
            experiment_trials = [t for t in all_trial_results if not t.get('is_practice', False)]
            
            if saved_trials > 0 or len(experiment_trials) > 0 or len(practice_trials) > 0:
                st.sidebar.markdown("### 💾 資料狀態")
                st.sidebar.metric("已儲存試驗", saved_trials)
                if len(experiment_trials) > 0:
                    st.sidebar.metric("正式試驗記憶", len(experiment_trials))
                if len(practice_trials) > 0:
                    st.sidebar.metric("練習試驗記憶", len(practice_trials))
        
    except Exception as e:
        logger.error(f"Error showing experiment status: {e}")

def show_loading_spinner(message: str = "載入中...", duration: float = 1.0) -> None:
    """
    Show loading spinner with message
    
    Args:
        message: Loading message
        duration: Duration to show spinner
    """
    try:
        with st.spinner(message):
            time.sleep(duration)
    except Exception as e:
        logger.error(f"Error showing loading spinner: {e}")

def show_countdown(seconds: int, message: str = "實驗即將開始") -> None:
    """
    Show countdown timer
    
    Args:
        seconds: Number of seconds to count down
        message: Message to display
    """
    try:
        placeholder = st.empty()
        
        for i in range(seconds, 0, -1):
            placeholder.markdown(f"""
            <div style="text-align: center; font-size: 24px; margin: 20px 0;">
                <p>{message}</p>
                <h1 style="color: #ff6b6b;">{i}</h1>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(1)
        
        placeholder.empty()
        
    except Exception as e:
        logger.error(f"Error showing countdown: {e}")

def show_feedback_message(is_correct: bool, response_time: Optional[float] = None) -> None:
    """
    Show feedback message after trial response
    
    Args:
        is_correct: Whether the response was correct
        response_time: Response time in milliseconds
    """
    try:
        if is_correct:
            feedback_emoji = "✅"
            feedback_text = "正確！"
            feedback_color = "#28a745"
        else:
            feedback_emoji = "❌"
            feedback_text = "錯誤"
            feedback_color = "#dc3545"
        
        feedback_html = f"""
        <div style="
            text-align: center;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            background-color: {feedback_color}20;
            border: 2px solid {feedback_color};
        ">
            <h2 style="color: {feedback_color}; margin: 0;">
                {feedback_emoji} {feedback_text}
            </h2>
        """
        
        if response_time is not None:
            feedback_html += f"""
            <p style="margin: 10px 0; color: #666;">
                反應時間: {response_time:.0f} ms
            </p>
            """
        
        feedback_html += "</div>"
        
        st.markdown(feedback_html, unsafe_allow_html=True)
        
    except Exception as e:
        logger.error(f"Error showing feedback message: {e}")

def show_completion_celebration() -> None:
    """Show experiment completion celebration"""
    try:
        celebration_html = """
        <div style="
            text-align: center;
            padding: 30px;
            margin: 20px 0;
            border-radius: 15px;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            color: white;
        ">
            <h1>🎉 實驗完成！</h1>
            <p style="font-size: 18px;">感謝您的參與！</p>
        </div>
        """
        
        st.markdown(celebration_html, unsafe_allow_html=True)
        st.balloons()
        
    except Exception as e:
        logger.error(f"Error showing completion celebration: {e}")