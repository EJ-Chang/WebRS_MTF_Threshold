"""
Stimuli preview screen for WebRS MTF Threshold experiment.
Allows users to preview the selected stimulus image after cropping.
"""
import streamlit as st
import os
from PIL import Image
from experiments.mtf_utils import load_and_prepare_image
from ui.components.response_buttons import create_action_button, apply_ui_scaling
from ui.components.image_display import display_mtf_stimulus_image
from utils.logger import get_logger

logger = get_logger(__name__)

def display_stimuli_preview_screen(session_manager) -> None:
    """
    Display stimuli preview screen showing cropped stimulus image
    
    Args:
        session_manager: SessionStateManager instance
    """
    try:
        # Apply 1.5x UI scaling
        apply_ui_scaling()
        
        st.title("🔍 刺激圖像預覽")
        st.markdown("---")

        if 'selected_stimulus_image' not in st.session_state:
            st.error("❌ 尚未選擇刺激圖像。請返回歡迎頁面選擇圖像。")
            if st.button("🏠 返回歡迎頁面"):
                session_manager.set_experiment_stage('welcome')
                st.rerun()
            return

        _display_main_preview(session_manager)
        _display_navigation_buttons(session_manager)
        
    except Exception as e:
        logger.error(f"Error in stimuli preview screen: {e}")
        st.error(f"顯示刺激預覽時發生錯誤：{e}")

def _display_main_preview(session_manager) -> None:
    """Display the main stimulus preview"""
    try:
        stimulus_path = st.session_state.selected_stimulus_image
        
        st.subheader(f"📸 選定的刺激圖像：{os.path.basename(stimulus_path)}")
        
        # Load and display image
        img_array = load_and_prepare_image(stimulus_path, use_right_half=True)
        if img_array is not None:
            display_result = display_mtf_stimulus_image(
                img_array,
                caption=f"處理後圖像: {img_array.shape[1]} × {img_array.shape[0]} 像素"
            )
            
            _display_image_info(stimulus_path, img_array.shape)
        else:
            st.error("❌ 無法載入圖像")
            
    except Exception as e:
        logger.error(f"Error displaying main preview: {e}")
        st.error(f"顯示預覽時發生錯誤：{e}")

def _display_image_info(stimulus_path: str, processed_shape: tuple) -> None:
    """Display image processing information"""
    try:
        st.subheader("📊 圖像處理信息")
        
        # Original image info
        if os.path.exists(stimulus_path):
            original_img = Image.open(stimulus_path)
            original_size = original_img.size  # (width, height)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("原始尺寸", f"{original_size[0]} × {original_size[1]} 像素")
                st.metric("原始檔案", os.path.basename(stimulus_path))
                
            with col2:
                st.metric("處理後尺寸", f"{processed_shape[1]} × {processed_shape[0]} 像素")
                processing_method = "使用右半邊" if "stimuli_img" in os.path.basename(stimulus_path) else "使用中央區域"
                st.metric("處理方式", processing_method)
                
            st.info("💡 **說明**: 圖像經過預處理以符合實驗需求。MTF模糊效果將在實際實驗中套用。")
        
    except Exception as e:
        logger.error(f"Error displaying image info: {e}")
        st.error("無法顯示圖像信息")

def _display_navigation_buttons(session_manager) -> None:
    """Display navigation buttons"""
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if create_action_button("⬅️ 返回選擇", key="back_to_selection"):
            session_manager.set_experiment_stage('welcome')
            st.rerun()
    
    with col2:
        if create_action_button("✅ 確認並繼續", key="confirm_and_continue"):
            # Validate that we have a valid experiment setup
            if hasattr(st.session_state, 'mtf_experiment_manager'):
                session_manager.set_experiment_stage('instructions')
                st.rerun()
            else:
                st.error("❌ 實驗管理器未初始化。請返回歡迎頁面重新設定。")

def _show_preview_tips() -> None:
    """Show tips for preview usage"""
    with st.expander("💡 預覽使用提示"):
        st.markdown("""
        **關於此預覽**：
        - 這是經過處理的刺激圖像，將用於 MTF 實驗
        - 圖像可能已經過裁切或調整以符合實驗需求
        - 實際實驗中，此圖像將套用不同程度的 MTF 模糊效果
        
        **下一步**：
        - 確認圖像品質符合預期後，點擊「確認並繼續」
        - 或返回重新選擇其他刺激圖像
        """)