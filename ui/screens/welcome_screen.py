"""
Welcome screen for WebRS MTF Threshold experiment.
"""
import streamlit as st
import pandas as pd
import os
from PIL import Image
from typing import List, Tuple, Optional
from mtf_experiment import MTFExperimentManager
from ui.components.response_buttons import create_action_button
from utils.logger import get_logger

logger = get_logger(__name__)

def display_welcome_screen(session_manager) -> None:
    """
    Display welcome screen and collect participant information
    
    Args:
        session_manager: SessionStateManager instance
    """
    try:
        st.title("🧠 MTF 清晰度測試實驗")
        st.markdown("*重構版本 - 模組化架構*")
        st.markdown("---")

        # Add performance testing option
        st.sidebar.markdown("### 🔧 Developer Tools")
        if st.sidebar.button("📊 ADO Performance Test"):
            session_manager.set_experiment_stage('benchmark')
            st.rerun()
        st.write("""
        這是一個使用適應性設計優化 (ADO) 技術的 MTF (調制轉變函數) 清晰度測試實驗。
        您將觀看不同清晰度的圖像，並對其銳利度進行判斷。
        """)

        _display_instructions()
        
        st.markdown("---")

        # Participant ID input
        participant_id = st.text_input(
            "輸入參與者ID：",
            value="",
            help="請輸入受測者ID（例如：名字縮寫 + 日期）"
        )

        # Stimulus image selection
        st.subheader("刺激圖像選擇")
        _display_stimulus_selection()

        st.markdown("---")

        # Experiment configuration
        config = _display_experiment_configuration()
        
        # Display options
        show_trial_feedback = _display_display_options()

        # ADO configuration info
        _display_ado_info()

        # Start experiment button
        if create_action_button("開始 MTF 實驗", key="start_mtf_experiment"):
            if _validate_experiment_setup(participant_id):
                _initialize_experiment(session_manager, participant_id, config, show_trial_feedback)

        st.markdown("---")

        # Data analysis section
        _display_data_analysis_section()
        
    except Exception as e:
        logger.error(f"Error in welcome screen: {e}")
        st.error(f"顯示歡迎畫面時發生錯誤：{e}")

def _display_instructions() -> None:
    """Display experiment instructions"""
    st.subheader("實驗說明：")
    st.write("""
    1. **設定**：輸入您的參與者ID並設定實驗參數
    2. **練習**：完成幾個練習試驗以熟悉任務
    3. **正式實驗**：回答圖像清晰度問題 - 實驗會根據您的回應進行調整
    4. **完成**：您的數據將自動儲存到資料庫
    """)

def _display_stimulus_selection() -> None:
    """Display stimulus image selection interface"""
    try:
        # Get available images
        stimuli_dir = "stimuli_preparation"
        available_images = _get_available_images(stimuli_dir)

        if available_images:
            st.write("請選擇實驗使用的刺激圖像：")
            _display_image_grid(available_images)
            _show_current_selection()
        else:
            st.warning("在 stimuli_preparation 資料夾中找不到刺激圖像")
            
    except Exception as e:
        logger.error(f"Error in stimulus selection: {e}")
        st.error("載入刺激圖像時發生錯誤")

def _get_available_images(stimuli_dir: str) -> List[Tuple[str, str]]:
    """Get list of available stimulus images"""
    available_images = []
    image_files = ["stimuli_img.png", "text_img.png", "tw_newsimg.png", "us_newsimg.png"]

    for img_file in image_files:
        img_path = os.path.join(stimuli_dir, img_file)
        if os.path.exists(img_path):
            available_images.append((img_file, img_path))
    
    return available_images

def _display_image_grid(available_images: List[Tuple[str, str]]) -> None:
    """Display grid of available images for selection"""
    cols = st.columns(len(available_images))

    caption_map = {
        'stimuli_img.png': '原始刺激圖',
        'text_img.png': '文字圖像',
        'tw_newsimg.png': '台灣新聞',
        'us_newsimg.png': '美國新聞'
    }

    for i, (img_name, img_path) in enumerate(available_images):
        with cols[i]:
            try:
                img = Image.open(img_path)
                
                # Calculate thumbnail size
                original_width, original_height = img.size
                max_size = 200
                scale_factor = min(max_size / original_width, max_size / original_height)
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                display_name = caption_map.get(img_name, img_name.replace('.png', ''))
                
                st.image(img_resized, caption=display_name, width=new_width)
                st.caption(f"Size: {original_width}×{original_height}")
                
                if st.button(f"選擇 {display_name}", key=f"select_{img_name}"):
                    st.session_state.selected_stimulus_image = img_path
                    st.rerun()
                    
            except Exception as e:
                logger.error(f"Error loading {img_name}: {e}")
                st.error(f"載入 {img_name} 時發生錯誤: {e}")

def _show_current_selection() -> None:
    """Show currently selected stimulus image"""
    if 'selected_stimulus_image' in st.session_state:
        selected_filename = os.path.basename(st.session_state.selected_stimulus_image)
        caption_map = {
            'stimuli_img.png': '原始刺激圖',
            'text_img.png': '文字圖像',
            'tw_newsimg.png': '台灣新聞',
            'us_newsimg.png': '美國新聞'
        }
        selected_name = caption_map.get(selected_filename, selected_filename.replace('.png', ''))
        st.success(f"✅ 已選擇刺激圖像： **{selected_name}**")
    else:
        st.info("👆 請在上方選擇一個刺激圖像")

def _display_experiment_configuration() -> dict:
    """Display experiment configuration options"""
    st.subheader("實驗配置")
    
    col1, col2 = st.columns(2)
    with col1:
        max_trials = st.slider("最大試驗次數：", 20, 100, 50)
        min_trials = st.slider("最小試驗次數：", 10, 30, 15)

    with col2:
        convergence_threshold = st.slider("收斂值：", 0.05, 0.3, 0.15, 0.01)
        stimulus_duration = st.slider("刺激持續時間（秒）：", 0.5, 5.0, 1.0, 0.1)
    
    return {
        'max_trials': max_trials,
        'min_trials': min_trials,
        'convergence_threshold': convergence_threshold,
        'stimulus_duration': stimulus_duration
    }

def _display_display_options() -> bool:
    """Display display options"""
    st.subheader("顯示選項")
    return st.checkbox(
        "顯示試驗回饋（每次回應後顯示 ADO 結果）",
        value=False,
        help="如果不勾選，實驗將在回應後直接進行下一個試驗"
    )

def _display_ado_info() -> None:
    """Display ADO configuration information"""
    st.subheader("適應性設計優化 (ADO)")
    st.info("ADO 預設啟用，將自動選擇 MTF 值以高效率推算您的清晰度知覺閾值")

def _validate_experiment_setup(participant_id: str) -> bool:
    """Validate experiment setup"""
    if not participant_id.strip():
        st.error("請輸入有效的參與者ID")
        return False
    elif 'selected_stimulus_image' not in st.session_state:
        st.error("請選擇一個刺激圖像")
        return False
    return True

def _initialize_experiment(session_manager, participant_id: str, config: dict, show_trial_feedback: bool) -> None:
    """Initialize experiment with given configuration"""
    try:
        session_manager.set_participant_id(participant_id.strip())
        st.session_state.experiment_type = "MTF Clarity Testing"

        # Set total trials in session manager to match user configuration
        session_manager.set_total_trials(config['max_trials'])
        
        # Initialize MTF experiment manager
        st.session_state.mtf_experiment_manager = MTFExperimentManager(
            max_trials=config['max_trials'],
            min_trials=config['min_trials'],
            convergence_threshold=config['convergence_threshold'],
            participant_id=session_manager.get_participant_id(),
            base_image_path=st.session_state.selected_stimulus_image
        )
        
        st.session_state.stimulus_duration = config['stimulus_duration']
        session_manager.set_show_trial_feedback(show_trial_feedback)
        
        logger.info(f"🔧 Trial configuration: max_trials={config['max_trials']}, min_trials={config['min_trials']}")
        logger.info(f"🔧 Trial feedback setting saved: {show_trial_feedback}")
        
        session_manager.set_experiment_stage('instructions')
        st.rerun()
        
    except Exception as e:
        logger.error(f"Error initializing experiment: {e}")
        st.error(f"初始化實驗時發生錯誤： {e}")

def _display_data_analysis_section() -> None:
    """Display data analysis section for previous experiments"""
    st.subheader("📊 分析過去數據")
    st.markdown("上傳之前實驗的 CSV 數據以繪製心理計量函數：")

    uploaded_file = st.file_uploader(
        "選擇 CSV 檔案", 
        type=['csv'],
        help="上傳過去實驗的 CSV 檔案進行分析"
    )

    if uploaded_file is not None:
        _analyze_uploaded_data(uploaded_file)

def _analyze_uploaded_data(uploaded_file) -> None:
    """Analyze uploaded CSV data"""
    try:
        # Read the uploaded CSV
        df = pd.read_csv(uploaded_file)
        
        st.success(f"數據載入成功！找到 {len(df)} 個試驗。")
        
        # Show data preview
        with st.expander("數據預覽"):
            st.dataframe(df.head(10))
            st.write("**找到的欄位：**", list(df.columns))
            st.write("**數據類型：**")
            for col in df.columns:
                st.write(f"- {col}: {df[col].dtype}")

        # Convert to trial data format
        trial_data = df.to_dict('records')
        
        # Generate psychometric function
        st.subheader("上傳數據的心理計量函數")
        from utils.analysis_tools import plot_psychometric_function
        plot_psychometric_function(trial_data)
        
        # Show stimulus info
        _show_stimulus_info(df)
        
        # Show summary statistics
        _show_summary_statistics(df)
        
    except Exception as e:
        logger.error(f"Error analyzing uploaded data: {e}")
        st.error(f"讀取檔案時發生錯誤： {str(e)}")
        _show_expected_format()

def _show_stimulus_info(df: pd.DataFrame) -> None:
    """Show stimulus image information"""
    if 'stimulus_image_file' in df.columns:
        stimulus_files = df['stimulus_image_file'].dropna().unique()
        if len(stimulus_files) > 0:
            caption_map = {
                'stimuli_img.png': '原始刺激圖',
                'text_img.png': '文字圖像',
                'tw_newsimg.png': '台灣新聞',
                'us_newsimg.png': '美國新聞',
                'test_pattern': '測試圖案'
            }
            
            stimulus_info = []
            for file in stimulus_files:
                display_name = caption_map.get(file, file)
                stimulus_info.append(f"**{display_name}** ({file})")
            
            st.info(f"📸 使用的刺激圖像： {', '.join(stimulus_info)}")

def _show_summary_statistics(df: pd.DataFrame) -> None:
    """Show summary statistics"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("總試驗次數", len(df))
    
    with col2:
        if 'response' in df.columns:
            clear_rate = (df['response'] == 'clear').mean()
            st.metric("整體清晰率", f"{clear_rate:.1%}")
    
    with col3:
        if 'reaction_time' in df.columns:
            avg_rt = df['reaction_time'].mean()
            st.metric("平均反應時間", f"{avg_rt:.2f}s")

def _show_expected_format() -> None:
    """Show expected CSV format"""
    st.info("請確定 CSV 檔案具有正確的格式，包含 'mtf_value'、'response'、'reaction_time' 等欄位。")
    
    with st.expander("預期的 CSV 格式"):
        sample_data = {
            'trial_number': [1, 2, 3],
            'mtf_value': [45.5, 67.8, 52.3],
            'response': ['clear', 'not_clear', 'clear'],
            'reaction_time': [1.2, 1.5, 1.1],
            'participant_id': ['P001', 'P001', 'P001'],
            'stimulus_image_file': ['test_img.png', 'test_img.png', 'test_img.png']
        }
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df)