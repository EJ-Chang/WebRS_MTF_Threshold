"""
Instructions screen for WebRS MTF Threshold experiment.
"""
import streamlit as st
from ui.components.response_buttons import create_navigation_buttons
from utils.logger import get_logger

logger = get_logger(__name__)

def display_instructions_screen(session_manager) -> None:
    """
    Display experiment instructions
    
    Args:
        session_manager: SessionStateManager instance
    """
    try:
        st.header("🎯 實驗說明")
        st.markdown("---")
        
        # Main instructions
        st.subheader("實驗流程")
        st.markdown("""
        1. **觀看圖像**: 您將看到一系列具有不同清晰度的圖像
        2. **做出判斷**: 對每張圖像，您需要判斷它是否**清楚**
        3. **快速回應**: 請根據您的第一印象快速回應
        4. **自適應設計**: 系統會根據您的回應自動調整難度
        """)
        
        st.subheader("如何回應")
        st.markdown("""
        - 👈 **左側按鈕「不清楚」**: 如果您認為圖像模糊或不清晰
        - 👉 **右側按鈕「清楚」**: 如果您認為圖像清晰可見
        - ⌨️ **鍵盤快捷鍵**: 您也可以使用左右箭頭鍵進行回應
        """)
        
        st.subheader("⏱️ 時間安排")
        st.markdown(f"""
        - **固視時間**: {session_manager.get_fixation_duration():.1f} 秒
        - **刺激呈現**: {st.session_state.get('stimulus_duration', 1.0):.1f} 秒
        - **總試驗數**: 最多 {session_manager.get_total_trials()} 次
        - **預計時間**: 約 5-10 分鐘
        """)
        
        st.subheader("📋 注意事項")
        st.info("""
        - 請保持專注，避免分心
        - 確保螢幕亮度適中
        - 保持正常的觀看距離（約 50-70 公分）
        - 如有任何不適，請立即停止實驗
        """)
        
        # Practice mode option
        st.markdown("---")
        st.subheader("🎯 練習模式")
        
        current_practice = session_manager.is_practice_mode()
        practice_mode = st.checkbox(
            "啟用練習模式 (建議)",
            value=current_practice,
            help="練習模式讓您熟悉實驗流程，數據不會被記錄"
        )
        
        if practice_mode != current_practice:
            session_manager.set_practice_mode(practice_mode)
        
        if practice_mode:
            st.success("✅ 練習模式已啟用 - 您可以先熟悉實驗流程")
        else:
            st.warning("⚠️ 正式模式 - 數據將被記錄")
        
        st.markdown("---")
        
        # Navigation buttons
        back_pressed, next_pressed = create_navigation_buttons(
            show_back=True,
            show_next=True,
            back_label="返回設定",
            next_label="開始實驗",
            key_suffix="instructions"
        )
        
        if back_pressed:
            session_manager.set_experiment_stage('welcome')
            st.rerun()
        
        if next_pressed:
            # Create experiment record for non-practice mode
            if not practice_mode:
                experiment_id = session_manager.create_experiment_record(
                    experiment_type="MTF_Clarity",
                    use_ado=True,
                    num_trials=20,
                    num_practice_trials=0
                )
                if experiment_id:
                    logger.info(f"✅ Experiment record created: {experiment_id}")
                else:
                    logger.warning("⚠️ Failed to create experiment record, continuing with CSV-only storage")
            
            session_manager.set_experiment_stage('trial')
            logger.info(f"Starting experiment - Practice mode: {practice_mode}")
            st.rerun()
            
    except Exception as e:
        logger.error(f"Error in instructions screen: {e}")
        st.error(f"Error displaying instructions: {e}")