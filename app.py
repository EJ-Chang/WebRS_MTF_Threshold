import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime
import json
import plotly.graph_objects as go
import plotly.express as px
from experiment import ExperimentManager
from data_manager import DataManager
from mtf_experiment import MTFExperimentManager
from csv_data_manager import CSVDataManager
import cv2
from PIL import Image
import base64
from io import BytesIO
import os

# 環境檢測：根據不同環境設定不同端口
def detect_environment():
    """檢測當前運行環境並設定相應的端口"""
    import platform
    
    # 檢查是否在 Replit 環境
    if os.path.exists('/home/runner') or 'REPL_ID' in os.environ:
        # Replit 環境
        os.environ['STREAMLIT_SERVER_PORT'] = '5000'
        os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
        print("🌐 檢測到 Replit 環境，使用端口 5000")
    elif platform.system() == 'Linux' and 'ubuntu' in platform.platform().lower():
        # Ubuntu Server 環境 (非Replit)
        os.environ['STREAMLIT_SERVER_PORT'] = '3838'
        os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
        print("🖥️ 檢測到 Ubuntu Server 環境，使用端口 3838 (共用 R Shiny port)")
    else:
        # 本地環境 (Windows/macOS)
        os.environ['STREAMLIT_SERVER_PORT'] = '8501'
        os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
        # print("💻 檢測到本地環境，使用端口 8501")  # 已關閉控制台輸出

# 執行環境檢測
detect_environment()

# Configure page
st.set_page_config(
    page_title="Psychophysics 2AFC Experiment",
    page_icon="🧠",
    layout="wide",  # Changed to wide for better image display
    initial_sidebar_state="collapsed"
)

def crop_image_to_viewport(image_array, target_width=800, target_height=600):
    """
    Crop image to fit viewport while maintaining aspect ratio and centering
    """
    if image_array is None:
        return None
    
    h, w = image_array.shape[:2]
    
    # Calculate aspect ratios
    img_aspect = w / h
    target_aspect = target_width / target_height
    
    if img_aspect > target_aspect:
        # Image is wider than target, crop width
        new_width = int(h * target_aspect)
        start_x = (w - new_width) // 2
        cropped = image_array[:, start_x:start_x + new_width]
    else:
        # Image is taller than target, crop height
        new_height = int(w / target_aspect)
        start_y = (h - new_height) // 2
        cropped = image_array[start_y:start_y + new_height, :]
    
    # Resize to target dimensions
    resized = cv2.resize(cropped, (target_width, target_height))
    return resized

def display_mtf_stimulus_image(image_data, caption=""):
    """
    Display MTF stimulus image for the experiment
    Returns: dict with image dimensions for button positioning
    """
    if image_data is None:
        st.error("❌ Stimulus image not available")
        return None
    
    # Process image data format
    if isinstance(image_data, str):
        if image_data.startswith('data:image'):
            # Extract base64 data
            base64_data = image_data.split(',')[1]
            img_bytes = base64.b64decode(base64_data)
            img = Image.open(BytesIO(img_bytes))
            image_array = np.array(img)
        else:
            st.error("❌ Invalid image data format")
            return None
    elif isinstance(image_data, np.ndarray):
        image_array = image_data
    else:
        try:
            image_array = np.array(image_data)
        except Exception as e:
            st.error(f"❌ Failed to convert to numpy array: {e}")
            return None
    
    if not isinstance(image_array, np.ndarray):
        st.error("❌ Invalid image array")
        return None
    
    # Process the image for display
    processed_img = image_array
    
    # Convert to PIL for display
    img_pil = Image.fromarray(processed_img)
    
    # Convert to base64 for HTML display
    buffer = BytesIO()
    img_pil.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # Add unique ID for positioning calculation
    img_id = f"mtf_img_{int(time.time() * 1000)}"
    final_h, final_w = processed_img.shape[:2]
    
    # Clean HTML for stimulus display
    html_content = f"""
    <div style="text-align: center; margin: 20px 0;">
        <img id="{img_id}" src="data:image/png;base64,{img_str}" 
             style="max-width: 100%; height: auto;">
        <p style="margin: 10px 0; color: #666; font-size: 14px;">{caption}</p>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)
    
    # Return image dimensions for button positioning
    return {
        'display_height': final_h,
        'center_position': final_h / 2,
        'original_width': final_w,
        'original_height': final_h,
        'no_scaling': True
    }

def display_fullscreen_image(image_data, caption=""):
    """
    Legacy function - redirect to MTF stimulus display
    """
    return display_mtf_stimulus_image(image_data, caption)

def display_ado_monitor(exp_manager, trial_number):
    """
    Display ADO monitoring information in a sidebar or expander
    """
    if not hasattr(exp_manager, 'ado_engine') or exp_manager.ado_engine is None:
        return
    
    try:
        estimates = exp_manager.get_current_estimates()
        
        # Create monitoring display
        with st.sidebar:
            st.markdown("### 🔬 ADO 監控")
            st.markdown("---")
            
            # Current estimates
            col1, col2 = st.columns(2)
            with col1:
                st.metric("閾值估計", f"{estimates.get('threshold_mean', 0):.1f}%")
            with col2:
                st.metric("不確定性", f"±{estimates.get('threshold_sd', 0):.1f}")
            
            # Progress indicators
            st.markdown("**學習進度:**")
            uncertainty = estimates.get('threshold_sd', 20)
            progress = max(0, min(1, (20 - uncertainty) / 15))  # Normalize uncertainty to progress
            st.progress(progress)
            
            # Trial information
            st.markdown(f"**試驗次數:** {trial_number}")
            
            # Convergence status
            if uncertainty < 5:
                st.success("✅ 高精度")
            elif uncertainty < 10:
                st.warning("⚡ 中等精度")
            else:
                st.info("🔄 學習中")
                
            # Show detailed trial history
            if hasattr(exp_manager, 'trial_data') and len(exp_manager.trial_data) > 0:
                st.markdown("**試驗歷史:**")
                recent_trials = exp_manager.trial_data[-5:]  # Last 5 trials
                for trial in recent_trials:
                    response_text = "✓ 清晰" if trial.get('response', False) else "✗ 不清晰"
                    rt = trial.get('reaction_time', 0)
                    st.text(f"T{trial.get('trial_number', 0)}: {trial.get('mtf_value', 0):.1f}% → {response_text} ({rt:.1f}s)")
            
            # ADO optimization details
            st.markdown("**優化詳情:**")
            if hasattr(exp_manager, 'ado_engine') and exp_manager.ado_engine:
                try:
                    entropy = exp_manager.get_ado_entropy()
                    st.metric("後驗熵值", f"{entropy:.3f}")
                    st.caption("熵值越低 = 不確定性越小")
                except Exception:
                    st.caption("計算優化指標中...")
            
            # Parameter evolution
            if trial_number > 3:
                st.markdown("**參數收斂:**")
                st.caption(f"閾值: {estimates.get('threshold_mean', 0):.1f}% (±{estimates.get('threshold_sd', 0):.1f})")
                st.caption(f"斜率: {estimates.get('slope_mean', 0):.2f} (±{estimates.get('slope_sd', 0):.2f})")
                    
    except Exception as e:
        st.sidebar.error(f"ADO監控錯誤: {str(e)}")

def plot_psychometric_function(trial_data):
    """Generate and display psychometric function from participant data"""
    if not trial_data:
        st.warning("No trial data available for plotting")
        return
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(trial_data)
    
    # Group by stimulus difference and calculate accuracy
    grouped = df.groupby('stimulus_difference').agg({
        'is_correct': ['count', 'sum', 'mean'],
        'reaction_time': 'mean'
    }).round(3)
    
    # Flatten column names
    grouped.columns = ['n_trials', 'n_correct', 'accuracy', 'mean_rt']
    grouped = grouped.reset_index()
    
    # Filter out groups with very few trials (less than 2)
    grouped = grouped[grouped['n_trials'] >= 2]
    
    if len(grouped) == 0:
        st.warning("Not enough data points for psychometric function")
        return
    
    # Create the plot
    fig = go.Figure()
    
    # Add data points
    fig.add_trace(go.Scatter(
        x=grouped['stimulus_difference'],
        y=grouped['accuracy'],
        mode='markers+lines',
        marker=dict(
            size=grouped['n_trials'] * 3,  # Size represents number of trials
            color=grouped['mean_rt'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Mean RT (s)")
        ),
        line=dict(width=2),
        name='Observed Accuracy',
        hovertemplate=
        'Stimulus Difference: %{x:.3f}<br>' +
        'Accuracy: %{y:.1%}<br>' +
        'Trials: %{text}<br>' +
        'Mean RT: %{marker.color:.2f}s<extra></extra>',
        text=grouped['n_trials']
    ))
    
    # Add threshold line (75% correct)
    fig.add_hline(
        y=0.75, 
        line_dash="dash", 
        line_color="red",
        annotation_text="75% Threshold"
    )
    
    # Estimate threshold (interpolation to 75% point)
    if len(grouped) >= 2:
        # Find threshold by interpolation
        try:
            threshold_estimate = np.interp(0.75, grouped['accuracy'], grouped['stimulus_difference'])
            fig.add_vline(
                x=threshold_estimate,
                line_dash="dash",
                line_color="orange",
                annotation_text=f"Est. Threshold: {threshold_estimate:.3f}"
            )
        except Exception:
            pass
    
    # Update layout
    fig.update_layout(
        title="Psychometric Function - Brightness Discrimination",
        xaxis_title="Stimulus Difference (Brightness)",
        yaxis_title="Proportion Correct",
        yaxis=dict(range=[0, 1], tickformat='.0%'),
        width=700,
        height=500,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show data table
    with st.expander("Detailed Results by Stimulus Difference"):
        st.dataframe(grouped, use_container_width=True)
    
    # Summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trials", len(df))
    with col2:
        overall_accuracy = df['is_correct'].mean()
        st.metric("Overall Accuracy", f"{overall_accuracy:.1%}")
    with col3:
        if len(grouped) >= 2:
            try:
                threshold_est = np.interp(0.75, grouped['accuracy'], grouped['stimulus_difference'])
                st.metric("75% Threshold", f"{threshold_est:.3f}")
            except Exception:
                st.metric("75% Threshold", "N/A")
        else:
            st.metric("75% Threshold", "N/A")

# Initialize session state variables
if 'experiment_stage' not in st.session_state:
    st.session_state.experiment_stage = 'welcome'
if 'participant_id' not in st.session_state:
    st.session_state.participant_id = None
if 'experiment_manager' not in st.session_state:
    st.session_state.experiment_manager = None
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()
if 'trial_start_time' not in st.session_state:
    st.session_state.trial_start_time = None
if 'awaiting_response' not in st.session_state:
    st.session_state.awaiting_response = False
if 'current_trial_data' not in st.session_state:
    st.session_state.current_trial_data = None
if 'trial_locked' not in st.session_state:
    st.session_state.trial_locked = False

def welcome_screen():
    """Display welcome screen and collect participant information"""
    st.title("🧠 MTF Clarity Testing Experiment")
    st.markdown("---")
    
    # Add performance testing option
    st.sidebar.markdown("### 🔧 Developer Tools")
    if st.sidebar.button("📊 ADO Performance Test"):
        st.session_state.experiment_stage = 'ado_benchmark'
        st.rerun()
    
    st.header("Welcome to the MTF Clarity Test")
    st.write("""
    This is an MTF (Modulation Transfer Function) clarity testing experiment using Adaptive Design Optimization (ADO). 
    You will view images with varying levels of clarity and make judgments about their sharpness.
    """)
    
    st.subheader("Instructions:")
    st.write("""
    1. **Setup**: Enter your participant ID and configure the experiment parameters
    2. **Practice**: Complete a few practice trials to familiarize yourself with the task
    3. **Main Experiment**: Respond to image clarity questions - the experiment adapts based on your responses
    4. **Completion**: Your data will be automatically saved to the database
    """)
    
    st.markdown("---")
    
    # Participant ID input
    participant_id = st.text_input(
        "Enter Participant ID:",
        value="",
        help="Enter a unique identifier (e.g., your initials + date)"
    )
    
    # Stimulus image selection
    st.subheader("Stimulus Image Selection")
    
    # Get available images
    stimuli_dir = "stimuli_preparation"
    available_images = []
    image_files = ["stimuli_img.png", "text_img.png", "tw_newsimg.png", "us_newsimg.png"]  # Known image files
    
    for img_file in image_files:
        img_path = os.path.join(stimuli_dir, img_file)
        if os.path.exists(img_path):
            available_images.append((img_file, img_path))
    
    if available_images:
        st.write("Select the stimulus image for your experiment:")
        
        # Create columns for image preview
        cols = st.columns(len(available_images))
        
        for i, (img_name, img_path) in enumerate(available_images):
            with cols[i]:
                # Display thumbnail with proper aspect ratio preservation
                try:
                    from PIL import Image
                    img = Image.open(img_path)
                    
                    # Calculate proper thumbnail size maintaining aspect ratio
                    original_width, original_height = img.size
                    max_size = 200
                    
                    # Calculate scaling factor to fit within max_size while preserving aspect ratio
                    scale_factor = min(max_size / original_width, max_size / original_height)
                    new_width = int(original_width * scale_factor)
                    new_height = int(original_height * scale_factor)
                    
                    # Resize image maintaining aspect ratio
                    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Display with fixed width to ensure consistent layout
                    # Create descriptive captions
                    caption_map = {
                        'stimuli_img.png': 'Original Stimulus',
                        'text_img.png': 'Text Image',
                        'tw_newsimg.png': 'Taiwan News',
                        'us_newsimg.png': 'US News'
                    }
                    display_name = caption_map.get(img_name, img_name.replace('.png', ''))
                    
                    st.image(img_resized, caption=display_name, width=new_width)
                    st.caption(f"Size: {original_width}×{original_height}")
                    
                    # Selection button
                    if st.button(f"Select {display_name}", key=f"select_{img_name}"):
                        st.session_state.selected_stimulus_image = img_path
                        st.rerun()
                except Exception as e:
                    st.error(f"Error loading {img_name}: {e}")
        
        # Show current selection
        if 'selected_stimulus_image' in st.session_state:
            selected_filename = os.path.basename(st.session_state.selected_stimulus_image)
            caption_map = {
                'stimuli_img.png': 'Original Stimulus',
                'text_img.png': 'Text Image',
                'tw_newsimg.png': 'Taiwan News',
                'us_newsimg.png': 'US News'
            }
            selected_name = caption_map.get(selected_filename, selected_filename.replace('.png', ''))
            st.success(f"✅ Selected stimulus: **{selected_name}**")
        else:
            st.info("👆 Please select a stimulus image above")
    else:
        st.warning("No stimulus images found in stimuli_preparation folder")
    
    st.markdown("---")
    
    # MTF experiment configuration
    st.subheader("Experiment Configuration")
    col1, col2 = st.columns(2)
    with col1:
        max_trials = st.slider("Maximum trials:", 20, 100, 50)
        min_trials = st.slider("Minimum trials:", 10, 30, 15)
    
    with col2:
        convergence_threshold = st.slider("Convergence threshold:", 0.05, 0.3, 0.15, 0.01)
        stimulus_duration = st.slider("Stimulus duration (seconds):", 0.5, 5.0, 1.0, 0.1)
    
    # MTF display options
    st.subheader("Display Options")
    show_trial_feedback = st.checkbox(
        "Show trial feedback (ADO results after each response)",
        value=True,
        help="If unchecked, experiment will proceed directly to next trial after response"
    )
    
    # ADO configuration
    st.subheader("Adaptive Design Optimization (ADO)")
    st.info("ADO is enabled by default and will intelligently select MTF values to efficiently estimate your clarity perception threshold")
    
    # Start experiment button
    if st.button("Start MTF Experiment", type="primary"):
        # Validation
        if not participant_id.strip():
            st.error("Please enter a valid Participant ID")
        elif 'selected_stimulus_image' not in st.session_state:
            st.error("Please select a stimulus image")
        else:
            st.session_state.participant_id = participant_id.strip()
            st.session_state.experiment_type = "MTF Clarity Testing"
            
            # Initialize MTF experiment manager with selected image
            st.session_state.mtf_experiment_manager = MTFExperimentManager(
                max_trials=max_trials,
                min_trials=min_trials,
                convergence_threshold=convergence_threshold,
                participant_id=st.session_state.participant_id,
                base_image_path=st.session_state.selected_stimulus_image
            )
            st.session_state.stimulus_duration = stimulus_duration
            st.session_state.show_trial_feedback = show_trial_feedback
            
            st.session_state.experiment_stage = 'instructions'
            st.rerun()
    
    st.markdown("---")
    
    # Data analysis section
    st.subheader("📊 Analyze Previous Data")
    st.markdown("Upload CSV data from a previous experiment to visualize the psychometric function:")
    
    uploaded_file = st.file_uploader(
        "Choose CSV file", 
        type=['csv'],
        help="Upload a CSV file from a previous experiment to analyze"
    )
    
    if uploaded_file is not None:
        try:
            # Read the uploaded CSV
            df = pd.read_csv(uploaded_file)
            
            # Display basic info about the dataset
            st.success(f"Data loaded successfully! Found {len(df)} trials.")
            
            # Show a preview of the data
            with st.expander("Data Preview"):
                st.dataframe(df.head(10))
                
                # Show column info
                st.write("**Columns found:**", list(df.columns))
                st.write("**Data types:**")
                for col in df.columns:
                    st.write(f"- {col}: {df[col].dtype}")
            
            # Convert DataFrame back to trial data format for plotting
            trial_data = df.to_dict('records')
            
            # Generate psychometric function
            st.subheader("Psychometric Function from Uploaded Data")
            plot_psychometric_function(trial_data)
            
            # Show stimulus image information if available
            if 'stimulus_image_file' in df.columns:
                stimulus_files = df['stimulus_image_file'].dropna().unique()
                if len(stimulus_files) > 0:
                    # Create descriptive names for display
                    caption_map = {
                        'stimuli_img.png': 'Original Stimulus',
                        'text_img.png': 'Text Image',
                        'tw_newsimg.png': 'Taiwan News',
                        'us_newsimg.png': 'US News',
                        'test_pattern': 'Test Pattern'
                    }
                    
                    stimulus_info = []
                    for file in stimulus_files:
                        display_name = caption_map.get(file, file)
                        stimulus_info.append(f"**{display_name}** ({file})")
                    
                    st.info(f"📸 Stimulus images used: {', '.join(stimulus_info)}")
            
            # Show summary statistics
            if 'is_correct' in df.columns:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Trials", len(df))
                with col2:
                    accuracy = df['is_correct'].mean()
                    st.metric("Overall Accuracy", f"{accuracy:.1%}")
                with col3:
                    if 'reaction_time' in df.columns:
                        avg_rt = df['reaction_time'].mean()
                        st.metric("Average RT", f"{avg_rt:.2f}s")
            
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            st.info("Please make sure the CSV file has the correct format with columns like 'stimulus_difference', 'is_correct', 'reaction_time', etc.")
            
            # Show expected format
            with st.expander("Expected CSV Format"):
                sample_data = {
                    'trial_number': [1, 2, 3],
                    'stimulus_difference': [0.1, 0.2, 0.15],
                    'is_correct': [True, False, True],
                    'reaction_time': [1.2, 1.5, 1.1],
                    'left_stimulus': [0.4, 0.4, 0.4],
                    'right_stimulus': [0.5, 0.6, 0.55],
                    'response': ['right', 'left', 'right']
                }
                sample_df = pd.DataFrame(sample_data)
                st.dataframe(sample_df)

def instructions_screen():
    """Display MTF experiment instructions"""
    st.title("📋 MTF Clarity Testing Instructions")
    st.markdown("---")
    
    # Show selected stimulus image
    if 'selected_stimulus_image' in st.session_state:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.subheader("Your Stimulus:")
            try:
                from PIL import Image
                img = Image.open(st.session_state.selected_stimulus_image)
                img.thumbnail((150, 150))
                st.image(img, caption=os.path.basename(st.session_state.selected_stimulus_image).replace('.png', ''))
            except Exception:
                st.text("Preview not available")
        with col2:
            st.subheader("Task Description")
            st.write("""
            In this experiment, you will view images with different levels of clarity and judge their sharpness:
            
            1. **Look at each image carefully**
            2. **Judge whether the image appears clear or blurry**
            3. **Respond based on your immediate perception**
            """)
    else:
        st.header("Task Description")
        st.write("""
        In this experiment, you will view images with different levels of clarity and judge their sharpness:
        
        1. **Look at each image carefully**
        2. **Judge whether the image appears clear or blurry**
        3. **Respond based on your immediate perception**
        """)
    
    st.header("How to Respond")
    st.write("""
    - Click **"✓ Clear"** if the image appears sharp and clear
    - Click **"✗ Not Clear"** if the image appears blurry or unclear
    - Trust your first impression - don't overthink
    """)
    
    st.header("About Adaptive Design Optimization (ADO)")
    st.info("""
    - The system learns from your responses to find your clarity perception threshold
    - Early trials may seem very easy or very hard as the system calibrates
    - The experiment will automatically converge on your personal threshold
    - Each response helps the algorithm select the next optimal test level
    """)
    
    st.header("Important Notes")
    st.warning("""
    - Focus on the overall clarity of the entire image
    - Maintain consistent viewing distance from your screen
    - Ensure good lighting conditions
    - Take breaks if you feel tired - quality responses are important
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Setup"):
            st.session_state.experiment_stage = 'welcome'
            st.rerun()
    
    with col2:
        if st.button("Start MTF Experiment →", type="primary"):
            # Initialize MTF trial state properly
            st.session_state.experiment_stage = 'mtf_trial'
            # Reset MTF session state
            st.session_state.mtf_trial_phase = 'new_trial'
            st.session_state.mtf_current_trial = None
            st.session_state.mtf_response_recorded = False
            st.rerun()

# 2AFC functions removed - this app now focuses exclusively on MTF clarity testing

def run_trial(is_practice=False):
    """Run a single trial"""
    exp_manager = st.session_state.experiment_manager
    
    # Handle feedback display phase
    if st.session_state.get('show_feedback', False):
        if time.time() - st.session_state.get('feedback_start_time', 0) >= st.session_state.get('feedback_duration', 1.0):
            # Feedback period is over, clear it and continue
            st.session_state.show_feedback = False
            st.session_state.feedback_start_time = None
            st.session_state.feedback_duration = None
            st.rerun()
        else:
            # Still showing feedback, don't display new trial yet
            return
    
    # Check if we need to generate a new trial or use the locked one
    if not st.session_state.trial_locked or st.session_state.current_trial_data is None:
        # Get new trial data and lock it
        current_trial = exp_manager.get_current_trial(is_practice)
        
        if current_trial is None:
            st.error("Error loading trial data")
            return
        
        # Lock the trial data to prevent regeneration
        st.session_state.current_trial_data = current_trial.copy()
        st.session_state.trial_locked = True
        st.session_state.awaiting_response = False
    else:
        # Use the locked trial data
        current_trial = st.session_state.current_trial_data
    
    # Display stimuli
    st.subheader("Which one is brighter?")
    st.caption("Click the button below the brighter circle")
    
    # Debug information (temporary)
    if st.session_state.get('show_debug', False):
        left_val = current_trial['left_stimulus']
        right_val = current_trial['right_stimulus']
        expected_correct = 'left' if left_val > right_val else 'right'
        st.info(f"DEBUG: Left={left_val:.3f}, Right={right_val:.3f}, Correct={expected_correct}")
    
    # Create stimulus display
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        # Display stimuli side by side
        stim_col1, stim_col2 = st.columns(2)
        
        with stim_col1:
            st.markdown("### Left Stimulus")
            # Display stimulus with better contrast visibility
            left_intensity = current_trial['left_stimulus']
            # Convert to grayscale value (0=black, 255=white)
            gray_value = int(left_intensity * 255)
            st.markdown(f"""
            <div style="
                width: 150px; 
                height: 150px; 
                border-radius: 50%; 
                background-color: rgb({gray_value}, {gray_value}, {gray_value}); 
                margin: 20px auto;
                border: 3px solid #333;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);
            "></div>
            <p style="text-align: center; font-size: 12px; color: #666;">
                Brightness: {left_intensity:.3f}
            </p>
            <p style="text-align: center; font-size: 10px; color: #999;">
                {'BRIGHTER' if left_intensity > current_trial['right_stimulus'] else 'dimmer'}
            </p>
            """, unsafe_allow_html=True)
        
        with stim_col2:
            st.markdown("### Right Stimulus")
            right_intensity = current_trial['right_stimulus']
            # Convert to grayscale value (0=black, 255=white)
            gray_value = int(right_intensity * 255)
            st.markdown(f"""
            <div style="
                width: 150px; 
                height: 150px; 
                border-radius: 50%; 
                background-color: rgb({gray_value}, {gray_value}, {gray_value}); 
                margin: 20px auto;
                border: 3px solid #333;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);
            "></div>
            <p style="text-align: center; font-size: 12px; color: #666;">
                Brightness: {right_intensity:.3f}
            </p>
            <p style="text-align: center; font-size: 10px; color: #999;">
                {'BRIGHTER' if right_intensity > current_trial['left_stimulus'] else 'dimmer'}
            </p>
            """, unsafe_allow_html=True)
    
    # Record trial start time if not already recorded
    if not st.session_state.awaiting_response:
        st.session_state.trial_start_time = time.time()
        st.session_state.awaiting_response = True
    
    # Response buttons
    st.markdown("---")
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        button_col1, button_col2 = st.columns(2)
        
        with button_col1:
            if st.button("Left is Brighter", key="left_button", use_container_width=True):
                record_response("left", current_trial, is_practice)
        
        with button_col2:
            if st.button("Right is Brighter", key="right_button", use_container_width=True):
                record_response("right", current_trial, is_practice)
    
    # Keyboard shortcuts info
    st.markdown("*Use keyboard: **A** for Left, **L** for Right*")
    
    # Debug toggle
    if st.checkbox("Show debug info (for troubleshooting)", key="debug_toggle"):
        st.session_state.show_debug = True
    else:
        st.session_state.show_debug = False



def save_experiment_data(trial_result):
    """Save experiment data to CSV file"""
    try:
        if 'csv_manager' not in st.session_state:
            st.session_state.csv_manager = CSVDataManager()
        
        csv_manager = st.session_state.csv_manager
        
        # Get participant ID from session
        participant_id = st.session_state.get('participant_id')
        if not participant_id:
            participant_id = 'unknown'
        
        # Create participant record if not exists
        if not hasattr(st.session_state, 'participant_created'):
            experiment_type = st.session_state.get('experiment_type', 'unknown')
            
            # Get experiment parameters
            exp_manager = st.session_state.get('experiment_manager')
            if exp_manager:
                experiment_config = {
                    'experiment_type': experiment_type,
                    'use_ado': exp_manager.use_ado,
                    'num_trials': exp_manager.num_trials,
                    'num_practice_trials': exp_manager.num_practice_trials,
                    'stimulus_duration': exp_manager.stimulus_duration,
                    'inter_trial_interval': exp_manager.inter_trial_interval
                }
            else:
                experiment_config = {
                    'experiment_type': experiment_type
                }
            
            csv_manager.create_participant_record(participant_id, experiment_config)
            st.session_state.participant_created = True
        
        # Calculate derived fields
        if 'left_stimulus' in trial_result and 'right_stimulus' in trial_result:
            trial_result['stimulus_difference'] = abs(trial_result['left_stimulus'] - trial_result['right_stimulus'])
            if trial_result['response'] in ['left', 'right']:
                expected = 'left' if trial_result['left_stimulus'] > trial_result['right_stimulus'] else 'right'
                trial_result['is_correct'] = trial_result['response'] == expected
        
        # Save trial to CSV
        csv_manager.save_trial_data(participant_id, trial_result)
        
        # Update session state for tracking
        if 'saved_trials' not in st.session_state:
            st.session_state.saved_trials = 0
        st.session_state.saved_trials += 1
        
    except Exception as e:
        st.error(f"Error saving data to CSV: {str(e)}")

def record_response(response, trial_data, is_practice=False):
    """Record participant response and reaction time"""
    if st.session_state.trial_start_time is None:
        st.error("Error: Trial timing not recorded properly")
        return
    
    # Calculate reaction time
    reaction_time = time.time() - st.session_state.trial_start_time
    
    # Record trial data
    trial_result = {
        'trial_number': trial_data['trial_number'],
        'is_practice': is_practice,
        'left_stimulus': trial_data['left_stimulus'],
        'right_stimulus': trial_data['right_stimulus'],
        'response': response,
        'reaction_time': reaction_time,
        'timestamp': datetime.now().isoformat(),
        'participant_id': st.session_state.get('participant_id', 'unknown')
    }
    
    # Add ADO stimulus value if available
    if 'ado_stimulus_value' in trial_data:
        trial_result['ado_stimulus_value'] = trial_data['ado_stimulus_value']
    
    # Add to experiment manager
    exp_manager = st.session_state.experiment_manager
    exp_manager.record_trial(trial_result, is_practice)
    
    # Auto-save data after each trial
    save_experiment_data(trial_result)
    
    # Reset trial state to allow new trial generation
    st.session_state.trial_start_time = None
    st.session_state.awaiting_response = False
    st.session_state.trial_locked = False
    st.session_state.current_trial_data = None
    
    # Show detailed feedback
    left_val = trial_data['left_stimulus']
    right_val = trial_data['right_stimulus'] 
    expected_correct = 'left' if left_val > right_val else 'right'
    is_correct = response == expected_correct
    
    if is_correct:
        st.success(f"✓ Correct! (RT: {reaction_time:.2f}s)")
    else:
        st.error(f"✗ Your response: {response.upper()}, Correct: {expected_correct.upper()} (RT: {reaction_time:.2f}s)")
        st.write(f"Left brightness: {left_val:.3f}, Right brightness: {right_val:.3f}")
    
    # Use session state for smoother transitions instead of sleep
    st.session_state.show_feedback = True
    st.session_state.feedback_start_time = time.time()
    st.session_state.feedback_duration = min(exp_manager.inter_trial_interval, 1.5)  # Cap at 1.5s
    st.rerun()



# MTF Experiment Functions
def show_animated_fixation(elapsed: float):
    """顯示帶動畫效果的注視點"""
    progress = min(elapsed / 1.0, 1.0)
    opacity = 0.3 + 0.7 * progress  # 逐漸清晰
    
    st.markdown(f"""
    <div style="
        text-align: center; 
        padding: 100px 0;
        transition: all 0.3s ease-in-out;
    ">
        <div style="
            font-size: 120px; 
            font-weight: bold; 
            color: rgba(51, 51, 51, {opacity});
            transform: scale({0.8 + 0.2 * progress});
            transition: all 0.5s ease-out;
        ">+</div>
        <div style="
            font-size: 18px; 
            color: #666; 
            margin-top: 20px;
            opacity: {progress};
        ">準備中... {elapsed:.1f}s</div>
    </div>
    """, unsafe_allow_html=True)

def mtf_trial_screen():
    """Handle MTF clarity testing trials with proper timing sequence"""
    # Debug session state
    debug_info = []
    for key in st.session_state:
        if 'mtf' in key.lower() or 'experiment' in key.lower():
            debug_info.append(f"{key}: {type(st.session_state[key])}")
    
    if 'mtf_experiment_manager' not in st.session_state:
        st.error("MTF experiment manager not found in session state")
        st.write("Available session state keys with 'mtf' or 'experiment':")
        for info in debug_info:
            st.write(f"- {info}")
        
        st.error("The experiment was not properly initialized. Please go back to setup.")
        if st.button("Return to Welcome Screen"):
            st.session_state.experiment_stage = 'welcome'
            st.rerun()
        return
    
    exp_manager = st.session_state.mtf_experiment_manager
    
    if exp_manager is None:
        st.error("MTF experiment manager is None")
        st.write("Session state debug info:")
        for info in debug_info:
            st.write(f"- {info}")
        
        if st.button("Return to Welcome Screen"):
            st.session_state.experiment_stage = 'welcome'
            st.rerun()
        return
    
    # Check if experiment is complete
    if exp_manager.is_experiment_complete():
        st.session_state.experiment_stage = 'mtf_results'
        st.rerun()
        return
    
    # Initialize trial timing state
    if 'mtf_trial_phase' not in st.session_state:
        st.session_state.mtf_trial_phase = 'new_trial'
        st.session_state.mtf_current_trial = None
        st.session_state.mtf_response_recorded = False
    
    # Ensure all required session state variables exist
    # Note: Do NOT reset mtf_phase_start_time here to avoid timing issues
    if 'mtf_current_trial' not in st.session_state:
        st.session_state.mtf_current_trial = None
    if 'mtf_response_recorded' not in st.session_state:
        st.session_state.mtf_response_recorded = False
    
    # Phase 1: Show fixation cross and wait 3 seconds with Python timing
    if st.session_state.mtf_trial_phase == 'new_trial':
        # Get next trial if not already available
        if st.session_state.mtf_current_trial is None:
            current_trial = exp_manager.get_next_trial()
            if current_trial is None:
                st.session_state.experiment_stage = 'mtf_results'
                st.rerun()
                return
            st.session_state.mtf_current_trial = current_trial
        
        current_trial = st.session_state.mtf_current_trial
        
        # Show fixation cross - no countdown needed
        st.markdown("""
        <div style="
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 60vh;
            text-align: center;
        ">
            <div style="
                font-size: 120px; 
                font-weight: bold; 
                color: #333;
                margin-bottom: 30px;
            ">+</div>
            <div style="
                color: #666; 
                font-size: 18px;
            ">請注視中心十字，實驗即將開始...</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show trial info at bottom
        st.markdown("---")
        st.title(f"MTF Clarity Test - Trial {current_trial['trial_number']}")
        total_trials = exp_manager.max_trials
        progress = current_trial['trial_number'] / total_trials
        st.progress(progress)
        st.write(f"Trial {current_trial['trial_number']} of {total_trials}")
        
        # Python controls the timing - wait exactly 3 seconds
        time.sleep(3.0)
        
        # Time up, advance to stimulus phase
        st.session_state.mtf_trial_phase = 'stimulus'
        st.session_state.mtf_stimulus_onset_time = time.time()
        st.rerun()
    
    # Phase 2: Show stimulus and accept responses (after 1 sec viewing)
    elif st.session_state.mtf_trial_phase == 'stimulus':
        current_trial = st.session_state.mtf_current_trial
        
        if current_trial is None:
            st.error("Trial data missing, restarting...")
            st.session_state.mtf_trial_phase = 'new_trial'
            st.rerun()
            return
        
        # Layout: Image on left, buttons on right (buttons vertically centered in viewport)
        main_col1, main_col2 = st.columns([3, 1])  # 3:1 ratio for image:buttons
        
        with main_col1:
            # Display stimulus first and get image dimensions
            img_info = None
            stimulus_image = current_trial.get('stimulus_image')
            
            # Display stimulus image
            if stimulus_image and isinstance(stimulus_image, str) and stimulus_image.startswith('data:image'):
                img_info = display_mtf_stimulus_image(
                    stimulus_image, 
                    caption=f"MTF: {current_trial['mtf_value']:.1f}%"
                )
            else:
                # Fallback: use test pattern if no valid stimulus image
                mtf_value = current_trial['mtf_value']
                if 'test_pattern' not in st.session_state:
                    rng = np.random.default_rng(42)  # Fixed seed for reproducibility
                    pattern = rng.integers(0, 255, (400, 400, 3), dtype=np.uint8)
                    st.session_state.test_pattern = pattern
                
                pattern = st.session_state.test_pattern.copy()
                sigma = ((100 - mtf_value) / 100.0) * 5.0
                if sigma > 0.1:
                    blurred = cv2.GaussianBlur(pattern, (0, 0), sigmaX=sigma, sigmaY=sigma)
                else:
                    blurred = pattern
                st.image(blurred, caption=f"Test Pattern (MTF: {mtf_value:.1f}%)", use_container_width=True)
                
                # Provide fallback image info for button positioning
                img_info = {
                    'display_height': 400,
                    'center_position': 200,
                    'original_width': 400,
                    'original_height': 400
                }
        
        with main_col2:
            # Response buttons aligned with image center height
            if not st.session_state.mtf_response_recorded:
                # Calculate button positioning based on EXACT image dimensions (no scaling)
                if img_info and 'center_position' in img_info and img_info.get('no_scaling'):
                    # Use exact pixel positioning - image is now displayed at full size
                    center_pixels = img_info['center_position']
                    # Convert to vh based on typical screen height, but more conservatively
                    center_vh = (center_pixels / 1080) * 100
                    padding_top = max(15, min(45, center_vh - 5))  # More range for exact positioning
                else:
                    # Fallback positioning
                    padding_top = 30
                
                st.markdown(f"""
                <div style="
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-start;
                    align-items: center;
                    padding-top: {padding_top}vh;
                    min-height: 70vh;
                    gap: 20px;
                ">
                """, unsafe_allow_html=True)
                
                st.markdown("### Is this image clear?")
                
                # Clear button
                if st.button("✓ Clear", key=f"clear_{current_trial['trial_number']}", type="primary", use_container_width=True):
                    record_mtf_response_and_advance(current_trial, True)
                
                # Not Clear button
                if st.button("✗ Not Clear", key=f"not_clear_{current_trial['trial_number']}", use_container_width=True):
                    record_mtf_response_and_advance(current_trial, False)
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                # Response already recorded - this should not be reached due to immediate transition
                st.markdown("---")
                st.success("Response recorded! Proceeding to feedback...")
                st.session_state.mtf_trial_phase = 'feedback'
                st.session_state.mtf_phase_start_time = time.time()
                st.rerun()
        
        # Header information at the bottom
        st.markdown("---")
        st.title(f"MTF Clarity Test - Trial {current_trial['trial_number']}")
        total_trials = exp_manager.max_trials
        progress = current_trial['trial_number'] / total_trials
        st.progress(progress)
        st.write(f"Trial {current_trial['trial_number']} of {total_trials}")
    
    # Phase 3: Show ADO feedback (1 second)
    elif st.session_state.mtf_trial_phase == 'feedback':
        current_trial = st.session_state.mtf_current_trial
        
        if current_trial is None:
            st.error("Trial data missing in feedback phase, restarting...")
            st.session_state.mtf_trial_phase = 'new_trial'
            st.rerun()
            return
        
        # Header
        st.title(f"MTF Clarity Test - Trial {current_trial['trial_number']}")
        
        # Clear the stimulus area
        st.markdown("### Response Recorded")
        
        # Show ADO feedback
        response_type = st.session_state.get('last_mtf_response', 'Unknown')
        st.success(f"Your response: {response_type}")
        
        # ADO parameters display
        if hasattr(exp_manager, 'get_current_estimates'):
            estimates = exp_manager.get_current_estimates()
            
            st.markdown("### ADO Parameters")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Threshold Estimate", f"{estimates.get('threshold_mean', 0):.1f}%")
            with col2:
                st.metric("Posterior SD", f"{estimates.get('threshold_sd', 0):.2f}")
            with col3:
                # Get next MTF value
                if not exp_manager.is_experiment_complete():
                    try:
                        if hasattr(exp_manager, 'ado_engine') and exp_manager.ado_engine:
                            next_mtf = exp_manager.ado_engine.get_optimal_design()
                            st.metric("Next MTF", f"{next_mtf:.1f}%")
                        else:
                            st.metric("Next MTF", "Computing...")
                    except Exception:
                        st.metric("Next MTF", "Ready")
                else:
                    st.metric("Status", "Complete!")
        
        # Simple continue button instead of auto-advance
        st.markdown("---")
        if st.button("Continue to Next Trial →", type="primary", key="next_trial"):
            # Reset for next trial
            st.session_state.mtf_trial_phase = 'new_trial'
            st.session_state.mtf_current_trial = None
            st.session_state.mtf_response_recorded = False
            if 'last_mtf_response' in st.session_state:
                del st.session_state.last_mtf_response
            st.rerun()
    
    # Display ADO monitoring in sidebar
    trial_num = 1
    if st.session_state.mtf_current_trial and 'trial_number' in st.session_state.mtf_current_trial:
        trial_num = st.session_state.mtf_current_trial['trial_number']
    display_ado_monitor(exp_manager, trial_num)

def record_mtf_response_and_advance(trial_data, is_clear):
    """Record MTF response and advance based on show_trial_feedback setting"""
    # Prevent double recording
    if st.session_state.get('mtf_response_recorded', False):
        return
    
    if 'mtf_stimulus_onset_time' not in st.session_state:
        st.error("Trial timing error")
        return
    
    # Mark as recorded immediately to prevent double clicks
    st.session_state.mtf_response_recorded = True
    
    # Calculate reaction time
    reaction_time = time.time() - st.session_state.mtf_stimulus_onset_time
    exp_manager = st.session_state.mtf_experiment_manager
    
    # Create trial result
    # Get stimulus image file name
    stimulus_image_file = "unknown"
    if 'selected_stimulus_image' in st.session_state and st.session_state.selected_stimulus_image:
        stimulus_image_file = os.path.basename(st.session_state.selected_stimulus_image)
    
    mtf_trial_result = {
        'trial_number': int(trial_data['trial_number']),
        'mtf_value': float(trial_data['mtf_value']),
        'response': 'clear' if is_clear else 'not_clear',
        'reaction_time': float(reaction_time),
        'timestamp': datetime.now().isoformat(),
        'participant_id': st.session_state.get('participant_id', 'unknown'),
        'experiment_type': 'MTF_Clarity',
        'stimulus_image_file': stimulus_image_file  # 記錄使用的圖片檔名
    }
    
    # Record and save
    exp_manager.record_response(trial_data, is_clear, reaction_time)
    save_experiment_data(mtf_trial_result)
    
    # Check if we should show feedback or go directly to next trial
    show_feedback = st.session_state.get('show_trial_feedback', True)
    
    if show_feedback:
        # Store response for feedback
        st.session_state.last_mtf_response = 'Clear' if is_clear else 'Not Clear'
        
        # Advance to feedback phase
        st.session_state.mtf_trial_phase = 'feedback'
        st.session_state.mtf_phase_start_time = time.time()
    else:
        # Skip feedback, go directly to next trial
        st.session_state.mtf_trial_phase = 'new_trial'
        st.session_state.mtf_fixation_started = False
        # mtf_phase_start_time will be set when fixation actually starts
        st.session_state.mtf_current_trial = None
        st.session_state.mtf_response_recorded = False
        if 'last_mtf_response' in st.session_state:
            del st.session_state.last_mtf_response
    
    # Immediately rerun
    st.rerun()

def record_mtf_response_smooth(trial_data, is_clear):
    """Record MTF response with smooth auto-advance flow"""
    if 'mtf_precise_stimulus_onset' not in st.session_state or st.session_state.mtf_precise_stimulus_onset is None:
        st.error("Trial timing error")
        return
    
    # Calculate precise reaction time
    response_time = time.time()
    raw_rt = response_time - st.session_state.mtf_precise_stimulus_onset
    exp_manager = st.session_state.mtf_experiment_manager
    
    # Create trial result for data saving - ensure proper data types
    # Get stimulus image file name
    stimulus_image_file = "unknown"
    if 'selected_stimulus_image' in st.session_state and st.session_state.selected_stimulus_image:
        stimulus_image_file = os.path.basename(st.session_state.selected_stimulus_image)
    
    mtf_trial_result = {
        'trial_number': int(trial_data['trial_number']),
        'mtf_value': float(trial_data['mtf_value']),
        'response': 'clear' if is_clear else 'not_clear',
        'reaction_time': float(raw_rt),  # Ensure it's a standard Python float
        'timestamp': datetime.now().isoformat(),
        'participant_id': st.session_state.get('participant_id', 'unknown'),
        'experiment_type': 'MTF_Clarity',
        'stimulus_image_file': stimulus_image_file  # 記錄使用的圖片檔名
    }
    
    # Record the response with precise timing
    exp_manager.record_response(
        trial_data, 
        is_clear, 
        raw_rt, 
        st.session_state.mtf_precise_stimulus_onset
    )
    
    # Auto-save MTF data
    save_experiment_data(mtf_trial_result)
    
    # Get estimates after update
    new_estimates = exp_manager.get_current_estimates()
    
    # Mark response as recorded
    st.session_state.mtf_response_recorded = True
    
    # Show brief feedback (will be displayed for 1.5 seconds)
    feedback_container = st.container()
    with feedback_container:
        st.success(f"Response: {'Clear' if is_clear else 'Not Clear'} (RT: {raw_rt:.2f}s)")
        
        # Compact ADO feedback
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Trial MTF", f"{trial_data['mtf_value']:.1f}%")
        
        with col2:
            st.metric("Threshold Est.", f"{new_estimates.get('threshold_mean', 0):.1f}%")
            current_sd = new_estimates.get('threshold_sd', 0)
            if current_sd < 5:
                st.caption("🎯 High precision")
            elif current_sd < 10:
                st.caption("📈 Converging")
            else:
                st.caption("🔄 Learning")
        
        with col3:
            # Show next MTF preview
            if hasattr(exp_manager, 'ado_engine') and exp_manager.ado_engine and not exp_manager.is_experiment_complete():
                try:
                    next_mtf = exp_manager.ado_engine.get_optimal_design()
                    st.metric("Next MTF", f"{next_mtf:.1f}%")
                except Exception:
                    st.metric("Next MTF", "...")
            else:
                completion_text = "Complete!" if exp_manager.is_experiment_complete() else "Preparing..."
                st.metric("Status", completion_text)

def auto_advance_mtf_trial():
    """Automatically advance to the next MTF trial"""
    # Reset trial state for next trial
    st.session_state.mtf_current_trial = None
    st.session_state.mtf_trial_start_time = None
    st.session_state.mtf_precise_stimulus_onset = None
    st.session_state.mtf_response_recorded = False
    st.session_state.mtf_feedback_start_time = None
    
    # Trigger rerun to load next trial
    st.rerun()

def record_mtf_response(trial_data, is_clear):
    """Record MTF trial response with detailed ADO feedback"""
    if 'mtf_stimulus_onset_time' not in st.session_state or st.session_state.mtf_stimulus_onset_time is None:
        st.error("Trial timing error")
        return
    
    reaction_time = time.time() - st.session_state.mtf_stimulus_onset_time
    exp_manager = st.session_state.mtf_experiment_manager
    
    # Create trial result for data saving
    # Get stimulus image file name
    stimulus_image_file = "unknown"
    if 'selected_stimulus_image' in st.session_state and st.session_state.selected_stimulus_image:
        stimulus_image_file = os.path.basename(st.session_state.selected_stimulus_image)
    
    mtf_trial_result = {
        'trial_number': trial_data['trial_number'],
        'mtf_value': trial_data['mtf_value'],
        'response': 'clear' if is_clear else 'not_clear',
        'reaction_time': reaction_time,
        'timestamp': datetime.now().isoformat(),
        'participant_id': st.session_state.get('participant_id', 'unknown'),
        'experiment_type': 'MTF_Clarity',
        'stimulus_image_file': stimulus_image_file  # 記錄使用的圖片檔名
    }
    
    # Record the response
    exp_manager.record_response(trial_data, is_clear, reaction_time)
    
    # Auto-save MTF data
    save_experiment_data(mtf_trial_result)
    
    # Get estimates after update
    new_estimates = exp_manager.get_current_estimates()
    
    # Show detailed ADO feedback
    st.success(f"Response: {'Clear' if is_clear else 'Not Clear'} (RT: {reaction_time:.2f}s)")
    
    # ADO Trial Summary
    st.markdown("### ADO Trial Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Trial MTF", f"{trial_data['mtf_value']:.1f}%")
        st.metric("Response", "Clear" if is_clear else "Not Clear")
    
    with col2:
        st.metric("Posterior Threshold", f"{new_estimates.get('threshold_mean', 0):.1f}%")
        current_sd = new_estimates.get('threshold_sd', 0)
        st.metric("Posterior SD", f"{current_sd:.2f}")
        if old_estimates:
            sd_change = current_sd - old_estimates.get('threshold_sd', 0)
            st.caption(f"SD Change: {sd_change:+.2f}")
    
    with col3:
        # Get next MTF value from ADO
        if hasattr(exp_manager, 'ado_engine') and exp_manager.ado_engine and not exp_manager.is_experiment_complete():
            try:
                # Preview next optimal design
                next_mtf = exp_manager.ado_engine.get_optimal_design()
                st.metric("Next MTF", f"{next_mtf:.1f}%")
            except Exception:
                st.metric("Next MTF", "Computing...")
        else:
            st.metric("Next MTF", "Complete" if exp_manager.is_experiment_complete() else "N/A")
    
    # Show optimization details
    if hasattr(exp_manager, 'ado_engine') and exp_manager.ado_engine:
        try:
            entropy = exp_manager.get_ado_entropy()
            st.caption(f"Posterior Entropy: {entropy:.3f} (lower = more certain)")
        except Exception:
            pass
    
    # Convergence status
    uncertainty = new_estimates.get('threshold_sd', 20)
    if uncertainty < 3:
        st.info("High precision achieved")
    elif uncertainty < 6:
        st.info("Good convergence progress")
    else:
        st.info("Learning in progress")
    
    # Reset trial state for next trial
    st.session_state.mtf_current_trial = None
    st.session_state.mtf_trial_phase = 'get_trial'
    st.session_state.mtf_phase_start_time = None
    st.session_state.mtf_stimulus_onset_time = None
    st.session_state.mtf_awaiting_response = False
    
    # Auto-advance to next trial (remove manual Continue button)
    st.success("Response recorded! Moving to next trial...")
    
    # Reset trial state for automatic continuation
    st.session_state.mtf_current_trial = None
    st.session_state.mtf_trial_phase = 'get_trial'
    st.session_state.mtf_phase_start_time = None
    st.session_state.mtf_stimulus_onset_time = None
    st.session_state.mtf_awaiting_response = False
    
    # Brief delay then auto-advance
    time.sleep(1.0)
    st.rerun()

def mtf_results_screen():
    """Display MTF experiment results"""
    if 'mtf_experiment_manager' not in st.session_state:
        st.error("No MTF experiment data found")
        return
    
    exp_manager = st.session_state.mtf_experiment_manager
    summary = exp_manager.get_experiment_summary()
    trial_data = exp_manager.export_data()
    
    st.title("🎉 MTF Experiment Complete!")
    st.balloons()
    
    # Summary metrics
    if summary:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Trials", summary.get('total_trials', 0))
        with col2:
            st.metric("Clear Responses", f"{summary.get('clear_responses', 0)}")
        with col3:
            st.metric("Average RT", f"{summary.get('average_reaction_time', 0):.2f}s")
        
        # Final threshold estimate
        if not np.isnan(summary.get('final_threshold', np.nan)):
            st.subheader("Final Results")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("MTF Threshold", f"{summary['final_threshold']:.1f}%")
            with col2:
                st.metric("Uncertainty", f"±{summary.get('threshold_uncertainty', 0):.1f}")
            
            convergence_status = "Yes" if summary.get('converged', False) else "No"
            st.info(f"Experiment converged: {convergence_status}")
        
        # Show stimulus image information
        stimulus_file = summary.get('stimulus_image_file', 'unknown')
        if stimulus_file != 'unknown':
            # Create descriptive name for display
            caption_map = {
                'stimuli_img.png': 'Original Stimulus',
                'text_img.png': 'Text Image',
                'tw_newsimg.png': 'Taiwan News',
                'us_newsimg.png': 'US News',
                'test_pattern': 'Test Pattern'
            }
            display_name = caption_map.get(stimulus_file, stimulus_file)
            st.info(f"📸 Stimulus used: **{display_name}** ({stimulus_file})")
    
    # Generate psychometric function for MTF data
    st.subheader("Your MTF Function")
    if trial_data:
        plot_mtf_psychometric_function(trial_data)
    
    # Data export
    st.subheader("Download Data")
    if st.button("Download MTF Results", type="primary"):
        # Convert trial data to CSV format
        df = pd.DataFrame(trial_data)
        csv_data = df.to_csv(index=False)
        
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"mtf_experiment_{summary.get('participant_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # Restart option
    if st.button("Start New Experiment"):
        # Clear session state
        keys_to_remove = []
        for key in st.session_state.keys():
            if str(key).startswith('mtf_'):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state[key]
        
        # Also clear experiment manager
        if 'mtf_experiment_manager' in st.session_state:
            del st.session_state.mtf_experiment_manager
            
        st.session_state.experiment_stage = 'welcome'
        st.rerun()

def plot_mtf_psychometric_function(trial_data):
    """Plot psychometric function for MTF data"""
    if not trial_data:
        st.warning("No trial data available for plotting")
        return
    
    df = pd.DataFrame(trial_data)
    
    # Group by MTF value and calculate proportion clear
    grouped = df.groupby('mtf_value').agg({
        'response': ['count', 'sum', 'mean'],
        'reaction_time': 'mean'
    }).round(3)
    
    grouped.columns = ['n_trials', 'n_clear', 'prop_clear', 'mean_rt']
    grouped = grouped.reset_index()
    
    # Filter groups with sufficient data
    grouped = grouped[grouped['n_trials'] >= 1]
    
    if len(grouped) == 0:
        st.warning("Not enough data points for psychometric function")
        return
    
    # Create plot
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=grouped['mtf_value'],
        y=grouped['prop_clear'],
        mode='markers+lines',
        marker=dict(
            size=grouped['n_trials'] * 3,
            color=grouped['mean_rt'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Mean RT (s)")
        ),
        line=dict(width=2),
        name='Proportion Clear',
        hovertemplate=
        'MTF Value: %{x:.1f}%<br>' +
        'Proportion Clear: %{y:.2f}<br>' +
        'Trials: %{text}<br>' +
        'Mean RT: %{marker.color:.2f}s<extra></extra>',
        text=grouped['n_trials']
    ))
    
    # Add 50% threshold line
    fig.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="50% Threshold")
    
    # Estimate threshold
    if len(grouped) >= 2:
        try:
            threshold_estimate = np.interp(0.5, grouped['prop_clear'], grouped['mtf_value'])
            fig.add_vline(
                x=threshold_estimate,
                line_dash="dash",
                line_color="orange",
                annotation_text=f"Est. Threshold: {threshold_estimate:.1f}%"
            )
        except Exception:
            pass
    
    fig.update_layout(
        title="MTF Psychometric Function - Clarity Judgments",
        xaxis_title="MTF Value (%)",
        yaxis_title="Proportion Clear",
        yaxis=dict(range=[0, 1]),
        width=700,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show data table
    with st.expander("Detailed Results by MTF Value"):
        st.dataframe(grouped, use_container_width=True)

def ado_benchmark_screen():
    """ADO Performance Benchmark Testing Screen"""
    st.title("📊 ADO Performance Benchmark")
    st.markdown("---")
    
    st.info("This page tests ADO computation time in the current Replit environment to optimize fixation duration.")
    
    # Back button
    if st.button("← Back to Main"):
        st.session_state.experiment_stage = 'welcome'
        st.rerun()
    
    st.header("Test Configuration")
    
    # Configuration options
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Design Space")
        design_step = st.select_slider(
            "MTF step size", 
            options=[1, 2, 5, 10], 
            value=5,
            help="Smaller steps = more candidate MTF values = longer computation"
        )
        design_range = st.slider("MTF range", 10, 99, (10, 99), step=5)
        
    with col2:
        st.subheader("Parameter Grid")
        threshold_points = st.slider("Threshold points", 10, 50, 31)
        slope_points = st.slider("Slope points", 10, 30, 21)
    
    # Calculate computational load
    design_space_size = len(range(design_range[0], design_range[1], design_step))
    param_combinations = threshold_points * slope_points
    total_operations = design_space_size * param_combinations * 2  # 2 for both responses
    
    st.info(f"""
    **Computational Load:**
    - Design space: {design_space_size} MTF values
    - Parameter grid: {param_combinations:,} combinations  
    - Total operations per trial: {total_operations:,}
    """)
    
    # Run benchmark
    if st.button("🚀 Run Benchmark", type="primary"):
        try:
            # Import ADO engine
            from mtf_experiment import MTFExperimentManager
            from experiments.ado_utils import ADOEngine
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.empty()
            
            # Test configuration
            design_space = np.arange(design_range[0], design_range[1], design_step)
            
            status_text.text("初始化 ADO 引擎...")
            progress_bar.progress(10)
            
            # Initialize ADO engine with test configuration
            start_init = time.time()
            ado_engine = ADOEngine(
                design_space=design_space,
                threshold_range=(5, 99),
                slope_range=(0.05, 5.0),
                threshold_points=threshold_points,
                slope_points=slope_points
            )
            init_time = (time.time() - start_init) * 1000
            
            progress_bar.progress(20)
            status_text.text("執行基準測試...")
            
            # Run multiple trials
            trial_times = []
            num_trials = 5
            
            for i in range(num_trials):
                status_text.text(f"執行 Trial {i+1}/{num_trials}...")
                progress_bar.progress(20 + (i * 60 // num_trials))
                
                # Time the critical operation
                start_time = time.time()
                optimal_mtf = ado_engine.get_optimal_design()
                end_time = time.time()
                
                trial_time = (end_time - start_time) * 1000  # Convert to ms
                trial_times.append(trial_time)
                
                # Simulate response for next iteration
                rng = np.random.default_rng(i)  # Use iteration as seed for reproducibility
                response = rng.choice([0, 1])
                ado_engine.update_posterior(optimal_mtf, response)
            
            progress_bar.progress(100)
            status_text.text("✅ 基準測試完成!")
            
            # Calculate statistics
            mean_time = np.mean(trial_times)
            max_time = np.max(trial_times)
            min_time = np.min(trial_times)
            
            # Display results
            with results_container.container():
                st.success("🎯 基準測試結果")
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("平均時間", f"{mean_time:.0f} ms")
                with col2:
                    st.metric("最大時間", f"{max_time:.0f} ms")
                with col3:
                    st.metric("最小時間", f"{min_time:.0f} ms")
                with col4:
                    st.metric("初始化", f"{init_time:.0f} ms")
                
                # Fixation time analysis
                st.subheader("Fixation時間分析")
                
                fixation_times = [500, 750, 1000, 1250, 1500]  # Different fixation durations
                
                for fix_time in fixation_times:
                    if max_time <= fix_time:
                        st.success(f"✅ {fix_time}ms fixation 可完全遮蓋運算延遲 (最大: {max_time:.0f}ms)")
                        break
                else:
                    needed_time = int(np.ceil(max_time / 100) * 100)  # Round up to nearest 100ms
                    st.warning(f"⚠️ 建議使用 {needed_time}ms fixation時間")
                
                # Detailed breakdown
                with st.expander("詳細測試數據"):
                    results_df = pd.DataFrame({
                        'Trial': range(1, len(trial_times) + 1),
                        'Time (ms)': [f"{t:.1f}" for t in trial_times]
                    })
                    st.dataframe(results_df, use_container_width=True)
                    
                    st.write("**配置詳情:**")
                    st.write(f"- 設計空間大小: {design_space_size} 個MTF值")
                    st.write(f"- 參數網格: {threshold_points} × {slope_points} = {param_combinations:,} 組合")
                    st.write(f"- 每次trial總運算: {total_operations:,} 次")
                    st.write(f"- 平均每次運算: {mean_time/total_operations*1000:.3f} μs")
                
                # Recommendations
                st.subheader("🎯 建議")
                
                if max_time <= 1000:
                    st.success("""
                    **結果很好！** 當前配置可以用1秒fixation完全遮蓋運算時間。
                    
                    **建議實作策略:**
                    - 在fixation開始時啟動ADO運算
                    - 保持1秒固定fixation時間
                    - 用戶感受不到任何延遲
                    """)
                elif max_time <= 1500:
                    st.warning(f"""
                    **需要調整！** 建議使用 {int(np.ceil(max_time/100)*100)}ms fixation時間。
                    
                    **建議實作策略:**
                    - 動態調整fixation時間 (最少1秒，必要時延長)
                    - 或簡化ADO配置以加速運算
                    """)
                else:
                    st.error("""
                    **需要優化！** 運算時間過長，建議:
                    
                    1. 減少設計空間大小 (增大step size)
                    2. 減少參數網格點數
                    3. 考慮pipeline預運算策略
                    """)
                    
        except ImportError as e:
            st.error(f"❌ 無法導入ADO模組: {e}")
            st.info("請確認 experiments/ado_utils.py 存在且可正常運作")
        except Exception as e:
            st.error(f"❌ 測試失敗: {e}")
            st.info("請檢查ADO引擎配置")

# Main app logic
def show_data_storage_info():
    """Display information about CSV data storage"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 CSV Data Storage")
    
    try:
        if 'csv_manager' not in st.session_state:
            st.session_state.csv_manager = CSVDataManager()
        
        csv_manager = st.session_state.csv_manager
        
        # Show current participant info
        if 'participant_id' in st.session_state:
            participant_id = st.session_state.participant_id
            saved_trials = st.session_state.get('saved_trials', 0)
            
            st.sidebar.success("Data is being saved to CSV files!")
            st.sidebar.write(f"**Current Participant:** {participant_id}")
            st.sidebar.write(f"**Trials Saved:** {saved_trials}")
            
            # Show selected stimulus image
            if 'selected_stimulus_image' in st.session_state:
                st.sidebar.markdown("---")
                st.sidebar.markdown("**🖼️ Current Stimulus:**")
                stimulus_name = os.path.basename(st.session_state.selected_stimulus_image).replace('.png', '')
                st.sidebar.success(f"{stimulus_name}")
            
            # Show download button for current participant data
            if st.sidebar.button("📥 Download Current Data"):
                try:
                    participant_id = st.session_state.get('participant_id', 'unknown')
                    csv_data = csv_manager.export_to_csv_string(participant_id)
                    if csv_data:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"data_{participant_id}_{timestamp}.csv"
                        
                        st.sidebar.download_button(
                            label="Download CSV",
                            data=csv_data,
                            file_name=filename,
                            mime='text/csv'
                        )
                    else:
                        st.sidebar.error("No data found for current participant")
                except Exception as e:
                    st.sidebar.error(f"Error exporting data: {str(e)}")
        
        # Show participant history
        participant_id = st.session_state.get('participant_id')
        if participant_id:
            try:
                summary = csv_manager.get_experiment_summary(participant_id)
                if summary:
                    status = "✅ Complete" if summary.get('status') == 'completed' else "🔄 In Progress"
                    experiment_type = summary.get('experiment_config', {}).get('experiment_type', 'Unknown')
                    st.sidebar.write(f"**Current Experiment:** {experiment_type} {status}")
            except Exception as e:
                st.sidebar.write("CSV storage ready")
        else:
            st.sidebar.info("Enter participant ID to see data storage")
            
    except Exception as e:
        st.sidebar.error(f"CSV storage error: {str(e)}")
        st.sidebar.info("CSV data storage is available")

def main():
    """Main application logic"""
    # Initialize session state for smooth transitions
    if 'experiment_stage' not in st.session_state:
        st.session_state.experiment_stage = 'welcome'
    if 'trial_locked' not in st.session_state:
        st.session_state.trial_locked = False
    if 'show_feedback' not in st.session_state:
        st.session_state.show_feedback = False
    
    # Initialize MTF-specific session state
    if 'mtf_experiment_initialized' not in st.session_state:
        st.session_state.mtf_experiment_initialized = False
    if 'mtf_trial_phase' not in st.session_state:
        st.session_state.mtf_trial_phase = 'fixation'
    
    # Show data storage info in sidebar
    show_data_storage_info()
    
    # Handle different experiment stages - MTF only
    if st.session_state.experiment_stage == 'welcome':
        welcome_screen()
    elif st.session_state.experiment_stage == 'ado_benchmark':
        ado_benchmark_screen()
    elif st.session_state.experiment_stage == 'instructions':
        instructions_screen()
    elif st.session_state.experiment_stage == 'mtf_trial':
        mtf_trial_screen()
    elif st.session_state.experiment_stage == 'mtf_results':
        mtf_results_screen()
    
    # Add footer
    st.markdown("---")
    st.markdown("*Psychophysics Experiment Platform*")

if __name__ == "__main__":
    main()
