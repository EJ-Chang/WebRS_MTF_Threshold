"""
Stimuli preview screen for WebRS MTF Threshold experiment.
Allows users to preview the selected stimulus image after cropping.
"""
import streamlit as st
import os
from PIL import Image
from experiments.mtf_utils import load_and_prepare_image
from ui.components.response_buttons import create_action_button
from utils.logger import get_logger

logger = get_logger(__name__)

def display_stimuli_preview_screen(session_manager) -> None:
    """
    Display stimuli preview screen showing cropped stimulus image
    
    Args:
        session_manager: SessionStateManager instance
    """
    try:
        st.title("🔍 刺激圖像預覽")
        st.markdown("---")
        
        # Check if stimulus is selected
        if 'selected_stimulus_image' not in st.session_state:
            st.error("未選擇刺激圖像，請返回設定頁面選擇圖像")
            _display_back_to_settings_button(session_manager)
            return
        
        stimulus_path = st.session_state.selected_stimulus_image
        
        # Display stimulus information
        _display_stimulus_info(stimulus_path)
        
        # Load and display cropped stimulus
        _display_cropped_stimulus(stimulus_path)
        
        # Navigation buttons
        _display_navigation_buttons(session_manager)
        
    except Exception as e:
        logger.error(f"Error in stimuli preview screen: {e}")
        st.error(f"顯示刺激預覽時發生錯誤：{e}")
        _display_back_to_settings_button(session_manager)

def _display_stimulus_info(stimulus_path: str) -> None:
    """Display information about the selected stimulus"""
    stimulus_filename = os.path.basename(stimulus_path)
    
    # Caption mapping
    caption_map = {
        'stimuli_img.png': '原始刺激圖',
        'text_img.png': '文字圖像',
        'tw_newsimg.png': '台灣新聞',
        'us_newsimg.png': '美國新聞',
        'bilingual_news.png': '雙語新聞',
        'working.png': 'working scenario'
    }
    
    display_name = caption_map.get(stimulus_filename, stimulus_filename.replace('.png', ''))
    
    st.subheader("已選擇的刺激圖像")
    st.info(f"📸 **{display_name}** ({stimulus_filename})")
    
    # Display original image info
    try:
        original_img = Image.open(stimulus_path)
        original_width, original_height = original_img.size
        st.write(f"**原始尺寸：** {original_width} × {original_height} 像素")
    except Exception as e:
        logger.warning(f"無法載入原始圖像資訊：{e}")

def _display_cropped_stimulus(stimulus_path: str) -> None:
    """Display the cropped stimulus image"""
    st.subheader("裁剪後的刺激圖像")
    st.write("這是實驗中將使用的圖像（已裁剪但未套用 MTF 濾鏡）：")
    
    try:
        # Load and prepare the image (cropping only, no MTF filter)
        cropped_img_array = load_and_prepare_image(stimulus_path, use_right_half=True)
        
        # Convert numpy array back to PIL Image for display
        cropped_img_pil = Image.fromarray(cropped_img_array)
        
        # Display the cropped image
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(
                cropped_img_pil, 
                caption=f"裁剪後尺寸：{cropped_img_array.shape[1]} × {cropped_img_array.shape[0]} 像素",
                use_column_width=True
            )
        
        # Display cropping information
        _display_cropping_info(stimulus_path, cropped_img_array.shape)
        
    except Exception as e:
        logger.error(f"載入或處理刺激圖像時發生錯誤：{e}")
        st.error(f"無法載入刺激圖像：{e}")

def _display_cropping_info(stimulus_path: str, cropped_shape: tuple) -> None:
    """Display information about the cropping process"""
    stimulus_filename = os.path.basename(stimulus_path).lower()
    
    st.markdown("### 裁剪資訊")
    
    if 'stimuli_img' in stimulus_filename:
        st.info("📌 **裁剪方式：** 取右半邊（保持原有 stimuli_img 的處理方式）")
    else:
        st.info("📌 **裁剪方式：** 取中央部分（適用於文字和新聞圖像）")
    
    # Display the final dimensions
    height, width = cropped_shape[:2]
    st.write(f"**最終尺寸：** {width} × {height} 像素")
    
    # Additional note
    st.markdown("""
    > **注意：** 這是經過裁剪但尚未套用 MTF 濾鏡的圖像。  
    > 在實際實驗中，會根據 ADO 算法動態調整 MTF 值來產生不同清晰度的圖像。
    """)

def _display_navigation_buttons(session_manager) -> None:
    """Display navigation buttons"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if create_action_button("⬅️ 返回設定", key="back_to_settings"):
            session_manager.set_experiment_stage('welcome')
            st.rerun()
    
    with col2:
        if create_action_button("🔄 重新載入", key="reload_preview"):
            st.rerun()
    
    with col3:
        # Check if we can start experiment (need participant ID)
        participant_id = session_manager.get_participant_id()
        if participant_id:
            if create_action_button("▶️ 開始實驗", key="start_from_preview"):
                session_manager.set_experiment_stage('instructions')
                st.rerun()
        else:
            st.button("▶️ 開始實驗", disabled=True, help="請先在設定頁面輸入參與者ID")

def _display_back_to_settings_button(session_manager) -> None:
    """Display back to settings button when there's an error"""
    st.markdown("---")
    if create_action_button("⬅️ 返回設定頁面", key="back_to_settings_error"):
        session_manager.set_experiment_stage('welcome')
        st.rerun()