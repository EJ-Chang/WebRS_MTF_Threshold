"""
Display calibration screen for WebRS MTF Threshold experiment.
"""
import streamlit as st
from ui.components.image_display import create_calibration_dashboard
from ui.components.response_buttons import create_action_button
from utils.logger import get_logger

logger = get_logger(__name__)

def display_calibration_screen(session_manager) -> None:
    """
    Display calibration screen with comprehensive calibration tools
    
    Args:
        session_manager: SessionStateManager instance
    """
    try:
        st.title("🎯 顯示器校準系統")
        st.markdown("*確保像素完美的刺激呈現*")
        st.markdown("---")
        
        # 說明文字
        st.info("""
        **為什麼需要校準？**  
        心理物理學實驗需要精確的刺激呈現。不同的顯示器具有不同的DPI和像素大小，
        這會影響MTF濾波器的精確性和實驗結果的可重現性。
        """)
        
        # 校準儀表板
        create_calibration_dashboard()
        
        st.markdown("---")
        
        # 導航按鈕
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if create_action_button("⬅️ 返回歡迎頁面", key="back_to_welcome"):
                session_manager.set_experiment_stage('welcome')
                st.rerun()
        
        with col2:
            # 如果校準狀態良好，允許直接開始實驗
            try:
                from utils.display_calibration import get_display_calibration
                calibration = get_display_calibration()
                status = calibration.get_calibration_status()
                
                if status['confidence'] > 0.5:
                    if create_action_button("▶️ 開始實驗", key="start_experiment_from_calibration"):
                        # 檢查是否有參與者ID
                        participant_id = session_manager.get_participant_id()
                        if participant_id:
                            session_manager.set_experiment_stage('instructions')
                            st.rerun()
                        else:
                            st.warning("請先返回歡迎頁面設定參與者ID")
                else:
                    st.button("▶️ 開始實驗", disabled=True, help="請先完成校準")
            except Exception as e:
                logger.error(f"Error checking calibration status: {e}")
                st.button("▶️ 開始實驗", disabled=True, help="校準系統異常")
        
        with col3:
            if create_action_button("🔄 重新載入", key="reload_calibration"):
                st.rerun()
        
        # 技術信息區域
        with st.expander("🔧 技術信息"):
            st.markdown("""
            ### 校準技術詳情
            
            **DPI 檢測方法**:
            1. **JavaScript 檢測**: 使用瀏覽器API檢測螢幕解析度和設備像素比
            2. **系統API檢測**: 
               - macOS: 使用 `system_profiler` 查詢顯示器信息
               - Windows: 使用 `wmic` 查詢顯示器規格
               - Linux: 使用 `xrandr` 查詢X11顯示器信息
            3. **手動校準**: 顯示已知尺寸的測試圖案供用戶測量
            
            **像素大小計算**:
            ```
            pixel_size_mm = 25.4 / dpi
            ```
            
            **MTF處理精確性**:
            MTF濾波器使用真實的像素大小來計算高斯模糊參數，確保
            空間頻率和調制傳遞函數的物理意義正確。
            
            **跨平台一致性**:
            系統會自動補償不同操作系統和瀏覽器的渲染差異，
            確保在macOS、Windows和Linux上都能獲得一致的視覺效果。
            """)
            
            # 顯示當前檢測到的技術參數
            try:
                from experiments.mtf_utils import get_current_pixel_size_info
                pixel_info = get_current_pixel_size_info()
                
                st.subheader("當前檢測參數")
                st.json(pixel_info)
                
            except Exception as e:
                st.warning(f"無法載入技術參數: {e}")
        
    except Exception as e:
        logger.error(f"Error in calibration screen: {e}")
        st.error(f"校準畫面發生錯誤：{e}")
        
        # 提供返回選項
        if create_action_button("⬅️ 返回歡迎頁面", key="back_to_welcome_error"):
            session_manager.set_experiment_stage('welcome')
            st.rerun()