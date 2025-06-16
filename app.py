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
from database import DatabaseManager
import cv2
from PIL import Image
import base64
from io import BytesIO
import os

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

def display_fullscreen_image(image_data, caption="", mtf_value=None):
    """
    Display image in fullscreen mode with proper sizing
    保持原始像素比例，根據視窗智能裁切中心區域
    """
    if image_data is None:
        return
    
    # If image_data is base64 string, decode it
    if isinstance(image_data, str) and image_data.startswith('data:image'):
        # Extract base64 data
        base64_data = image_data.split(',')[1]
        img_bytes = base64.b64decode(base64_data)
        img = Image.open(BytesIO(img_bytes))
        image_array = np.array(img)
    elif isinstance(image_data, np.ndarray):
        image_array = image_data
    else:
        # Convert other types to numpy array
        image_array = np.array(image_data)
    
    # Ensure we have a valid numpy array
    if not isinstance(image_array, np.ndarray):
        st.error("無法處理圖片格式")
        return
    
    # 根據視窗大小智能裁切中心區域，保持 1:1 像素比例
    h, w = image_array.shape[:2]
    
    # 最大化利用畫布空間，優先保持原始尺寸
    # 只有在圖片過大時才裁切
    max_display_width = 1400  # 增大最大寬度
    max_display_height = 1000  # 增大最大高度
    
    # 計算需要裁切的尺寸，保持中心位置
    if w > max_display_width or h > max_display_height:
        # 需要裁切時，盡可能保持更大的尺寸
        if w > max_display_width:
            crop_width = max_display_width
        else:
            crop_width = w
            
        if h > max_display_height:
            crop_height = max_display_height
        else:
            crop_height = h
        
        # 計算中心裁切座標
        start_x = (w - crop_width) // 2
        start_y = (h - crop_height) // 2
        
        # 裁切中心區域
        processed_img = image_array[start_y:start_y + crop_height, start_x:start_x + crop_width]
    else:
        # 圖片尺寸適合，直接使用
        processed_img = image_array
    
    # Convert to PIL for display
    img_pil = Image.fromarray(processed_img)
    
    # Convert to base64 for HTML display
    buffer = BytesIO()
    img_pil.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # Display using HTML with maximum canvas utilization
    html_content = f"""
    <div style="text-align: center; margin: 0; padding: 0; width: 100%; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center;">
        <img src="data:image/png;base64,{img_str}" 
             style="max-width: 100vw; max-height: 90vh; width: auto; height: auto; object-fit: contain; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;">
        <p style="margin: 5px 0 0 0; font-size: 12px; color: #666; position: absolute; bottom: 10px;">{caption}</p>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

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
                except:
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
        except:
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
            except:
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
    st.title("🧠 Psychophysics 2AFC Experiment")
    st.markdown("---")
    
    # Add performance testing option
    st.sidebar.markdown("### 🔧 Developer Tools")
    if st.sidebar.button("📊 ADO Performance Test"):
        st.session_state.experiment_stage = 'ado_benchmark'
        st.rerun()
    
    st.header("Welcome to the Experiment")
    st.write("""
    This is a Two-Alternative Forced Choice (2AFC) psychophysics experiment. 
    You will be presented with pairs of stimuli and asked to make choices between them.
    """)
    
    st.subheader("Instructions:")
    st.write("""
    1. **Setup**: First, enter your participant ID and configure the experiment
    2. **Practice**: Complete a few practice trials to familiarize yourself
    3. **Main Experiment**: Complete all experimental trials
    4. **Completion**: Your data will be automatically saved
    """)
    
    st.markdown("---")
    
    # Participant ID input
    participant_id = st.text_input(
        "Enter Participant ID:",
        value="",
        help="Enter a unique identifier (e.g., your initials + date)"
    )
    
    # Experiment type selection
    st.subheader("Experiment Type")
    experiment_type = st.radio(
        "Choose experiment type:",
        ["Brightness Discrimination (2AFC)", "MTF Clarity Testing (Y/N)"],
        help="Select the type of psychophysical experiment to run"
    )
    
    if experiment_type == "Brightness Discrimination (2AFC)":
        st.info("Traditional 2AFC brightness discrimination task with two circles")
    else:
        st.info("MTF (Modulation Transfer Function) clarity testing with image stimuli")
    
    # Experiment configuration
    st.subheader("Experiment Configuration")
    
    if experiment_type == "Brightness Discrimination (2AFC)":
        col1, col2 = st.columns(2)
        with col1:
            num_trials = st.slider("Number of trials:", 10, 100, 30)
            stimulus_duration = st.slider("Stimulus duration (seconds):", 0.5, 5.0, 2.0, 0.1)
        
        with col2:
            inter_trial_interval = st.slider("Inter-trial interval (seconds):", 0.5, 3.0, 1.0, 0.1)
            num_practice_trials = st.slider("Practice trials:", 3, 10, 5)
    else:
        # MTF experiment parameters
        col1, col2 = st.columns(2)
        with col1:
            max_trials = st.slider("Maximum trials:", 20, 100, 50)
            min_trials = st.slider("Minimum trials:", 10, 30, 15)
        
        with col2:
            convergence_threshold = st.slider("Convergence threshold:", 0.05, 0.3, 0.15, 0.01)
            stimulus_duration = st.slider("Stimulus duration (seconds):", 0.5, 5.0, 1.0, 0.1)
    
    # ADO configuration
    st.subheader("Adaptive Design Optimization (ADO)")
    use_ado = st.checkbox(
        "Enable ADO for optimal stimulus selection", 
        value=True,
        help="ADO adaptively selects stimuli to maximize information gain about the psychometric function"
    )
    
    if use_ado:
        st.info("ADO will intelligently select stimuli to efficiently estimate your psychometric function parameters")
    
    # Start experiment button
    if st.button("Start Experiment", type="primary"):
        if participant_id.strip():
            st.session_state.participant_id = participant_id.strip()
            st.session_state.experiment_type = experiment_type
            
            if experiment_type == "Brightness Discrimination (2AFC)":
                # Ensure variables are defined with defaults
                num_trials_val = locals().get('num_trials', 30)
                num_practice_trials_val = locals().get('num_practice_trials', 5)
                inter_trial_interval_val = locals().get('inter_trial_interval', 1.0)
                
                st.session_state.experiment_manager = ExperimentManager(
                    num_trials=num_trials_val,
                    num_practice_trials=num_practice_trials_val,
                    stimulus_duration=stimulus_duration,
                    inter_trial_interval=inter_trial_interval_val,
                    participant_id=st.session_state.participant_id,
                    use_ado=use_ado
                )
            else:
                # Ensure variables are defined with defaults
                max_trials_val = locals().get('max_trials', 50)
                min_trials_val = locals().get('min_trials', 15)
                convergence_threshold_val = locals().get('convergence_threshold', 0.15)
                
                st.session_state.mtf_experiment_manager = MTFExperimentManager(
                    max_trials=max_trials_val,
                    min_trials=min_trials_val,
                    convergence_threshold=convergence_threshold_val,
                    participant_id=st.session_state.participant_id
                )
                st.session_state.stimulus_duration = stimulus_duration
            
            st.session_state.experiment_stage = 'instructions'
            st.rerun()
        else:
            st.error("Please enter a valid Participant ID")
    
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
    """Display detailed instructions before practice"""
    st.title("📋 Experiment Instructions")
    st.markdown("---")
    
    st.header("Task Description")
    st.write("""
    In this experiment, you will see two circles presented side by side. Your task is to:
    
    1. **Look at both circles carefully**
    2. **Choose which circle appears brighter** (has more light/luminance)
    3. **Respond as quickly and accurately as possible**
    """)
    
    st.header("How to Respond")
    st.write("""
    - Click the **Left** button to choose the left circle (if it's brighter)
    - Click the **Right** button to choose the right circle (if it's brighter)
    - Or use keyboard shortcuts: **'A'** for left, **'L'** for right
    """)
    
    st.header("Important Notes")
    st.info("""
    - There are no "correct" or "incorrect" answers - respond based on your perception
    - Try to respond as quickly as possible while still being thoughtful
    - Take breaks between trials if needed
    - The experiment will automatically save your responses
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Setup"):
            st.session_state.experiment_stage = 'welcome'
            st.rerun()
    
    with col2:
        experiment_type = st.session_state.get('experiment_type', 'Brightness Discrimination (2AFC)')
        
        if experiment_type == "Brightness Discrimination (2AFC)":
            if st.button("Start Practice Trials →", type="primary"):
                st.session_state.experiment_stage = 'practice'
                if hasattr(st.session_state, 'experiment_manager') and st.session_state.experiment_manager:
                    st.session_state.experiment_manager.start_practice()
                # Reset trial state for new session
                st.session_state.trial_locked = False
                st.session_state.current_trial_data = None
                st.session_state.awaiting_response = False
                st.rerun()
        else:
            if st.button("Start MTF Experiment →", type="primary"):
                st.session_state.experiment_stage = 'mtf_trial'
                st.rerun()

def practice_screen():
    """Handle practice trials"""
    exp_manager = st.session_state.experiment_manager
    
    st.title("🎯 Practice Trials")
    st.markdown("---")
    
    if exp_manager.practice_completed:
        st.success("✅ Practice completed!")
        st.write("Great job! You're ready for the main experiment.")
        
        if st.button("Start Main Experiment →", type="primary"):
            st.session_state.experiment_stage = 'experiment'
            exp_manager.start_main_experiment()
            # Reset trial state for new session
            st.session_state.trial_locked = False
            st.session_state.current_trial_data = None
            st.session_state.awaiting_response = False
            st.rerun()
        return
    
    # Display practice progress
    progress = exp_manager.current_practice_trial / exp_manager.num_practice_trials
    st.progress(progress)
    st.write(f"Practice Trial {exp_manager.current_practice_trial + 1} of {exp_manager.num_practice_trials}")
    
    # Run trial
    run_trial(is_practice=True)

def experiment_screen():
    """Handle main experiment trials"""
    exp_manager = st.session_state.experiment_manager
    
    st.title("🧪 Main Experiment")
    st.markdown("---")
    
    if exp_manager.experiment_completed:
        st.success("🎉 Experiment completed!")
        st.balloons()
        
        # Display summary
        total_trials = len(exp_manager.trial_data)
        if total_trials > 0:
            avg_rt = np.mean([trial['reaction_time'] for trial in exp_manager.trial_data])
            accuracy = np.mean([trial.get('is_correct', False) for trial in exp_manager.trial_data])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Trials", total_trials)
            with col2:
                st.metric("Average RT", f"{avg_rt:.2f}s")
            with col3:
                st.metric("Accuracy", f"{accuracy:.1%}")
        
        # Generate and display psychometric function
        st.subheader("Your Psychometric Function")
        plot_psychometric_function(exp_manager.trial_data)
        
        # Show ADO results if ADO was used
        if exp_manager.use_ado:
            st.subheader("ADO Results")
            ado_summary = exp_manager.get_ado_summary()
            
            if ado_summary:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Threshold Estimation:**")
                    st.write(f"- Estimated Threshold: {ado_summary.get('threshold_estimate', 0):.3f}")
                    st.write(f"- Final Accuracy: {ado_summary.get('recent_accuracy', 0):.1%}")
                with col2:
                    st.write("**Algorithm Performance:**")
                    st.write(f"- Trials Completed: {ado_summary.get('n_trials', 0)}")
                    st.write(f"- Converged: {'Yes' if ado_summary.get('converged', False) else 'No'}")
                    st.write(f"- Final Difference: {ado_summary.get('current_difference', 0):.3f}")
        
        # Save data
        if st.button("Download Results", type="primary"):
            csv_data = st.session_state.data_manager.export_to_csv(exp_manager.trial_data, exp_manager.participant_id)
            st.download_button(
                label="📊 Download CSV File",
                data=csv_data,
                file_name=f"experiment_results_{exp_manager.participant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        if st.button("Start New Experiment"):
            # Reset session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return
    
    # Display experiment progress
    progress = exp_manager.current_trial / exp_manager.num_trials
    st.progress(progress)
    
    # Show trial info and ADO status
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"Trial {exp_manager.current_trial + 1} of {exp_manager.num_trials}")
    with col2:
        if exp_manager.use_ado:
            entropy = exp_manager.get_ado_entropy()
            st.write(f"ADO Uncertainty: {entropy:.2f}")
    
    # Show real-time ADO parameter estimates during experiment
    if exp_manager.use_ado and exp_manager.current_trial > 0:
        with st.expander("ADO Algorithm Status", expanded=False):
            ado_summary = exp_manager.get_ado_summary()
            if ado_summary:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Current Estimates:**")
                    st.write(f"Threshold: {ado_summary.get('threshold_estimate', 0):.3f}")
                    st.write(f"Current Difference: {ado_summary.get('current_difference', 0):.3f}")
                with col2:
                    st.write("**Performance:**")
                    st.write(f"Trials: {ado_summary.get('n_trials', 0)}")
                    st.write(f"Recent Accuracy: {ado_summary.get('recent_accuracy', 0):.1%}")
                    st.write(f"Converged: {'Yes' if ado_summary.get('converged', False) else 'No'}")
    
    # Run trial
    run_trial(is_practice=False)

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
    col1, col2, col3 = st.columns([1, 2, 1])
    
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
    col1, col2, col3 = st.columns([1, 2, 1])
    
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



def save_experiment_data(trial_result, is_practice=False):
    """Save experiment data to database"""
    try:
        if 'db_manager' not in st.session_state:
            st.session_state.db_manager = DatabaseManager()
        
        db = st.session_state.db_manager
        
        # Get current experiment ID from session
        experiment_id = st.session_state.get('current_experiment_id')
        if not experiment_id:
            # Create new experiment if not exists
            participant_id = st.session_state.get('participant_id', 'unknown')
            experiment_type = st.session_state.get('experiment_type', 'unknown')
            
            # Get experiment parameters
            exp_manager = st.session_state.get('experiment_manager')
            if exp_manager:
                experiment_id = db.create_experiment(
                    participant_id=participant_id,
                    experiment_type=experiment_type,
                    use_ado=exp_manager.use_ado,
                    num_trials=exp_manager.num_trials,
                    num_practice_trials=exp_manager.num_practice_trials,
                    stimulus_duration=exp_manager.stimulus_duration,
                    inter_trial_interval=exp_manager.inter_trial_interval
                )
            else:
                experiment_id = db.create_experiment(
                    participant_id=participant_id,
                    experiment_type=experiment_type
                )
            
            st.session_state.current_experiment_id = experiment_id
        
        # Calculate derived fields
        if 'left_stimulus' in trial_result and 'right_stimulus' in trial_result:
            trial_result['stimulus_difference'] = abs(trial_result['left_stimulus'] - trial_result['right_stimulus'])
            if trial_result['response'] in ['left', 'right']:
                expected = 'left' if trial_result['left_stimulus'] > trial_result['right_stimulus'] else 'right'
                trial_result['is_correct'] = trial_result['response'] == expected
        
        # Save trial to database
        db.save_trial(experiment_id, trial_result)
        
        # Update session state for tracking
        if 'saved_trials' not in st.session_state:
            st.session_state.saved_trials = 0
        st.session_state.saved_trials += 1
        
    except Exception as e:
        st.error(f"Error saving data to database: {str(e)}")

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
    save_experiment_data(trial_result, is_practice)
    
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
    """Handle MTF clarity testing trials with smooth single-page flow"""
    if 'mtf_experiment_manager' not in st.session_state:
        st.error("MTF experiment not properly initialized")
        st.session_state.experiment_stage = 'welcome'
        st.rerun()
        return
    
    exp_manager = st.session_state.mtf_experiment_manager
    
    # Check if experiment is complete
    if exp_manager.is_experiment_complete():
        st.session_state.experiment_stage = 'mtf_results'
        st.rerun()
        return
    
    # Initialize trial state for smooth flow
    if 'mtf_trial_start_time' not in st.session_state:
        st.session_state.mtf_trial_start_time = None
        st.session_state.mtf_current_trial = None
        st.session_state.mtf_precise_stimulus_onset = None
        st.session_state.mtf_response_recorded = False
        st.session_state.mtf_feedback_start_time = None
    
    # Get current trial if needed
    if st.session_state.mtf_current_trial is None and not st.session_state.mtf_response_recorded:
        current_trial = exp_manager.get_next_trial()
        if current_trial is None:
            st.session_state.experiment_stage = 'mtf_results'
            st.rerun()
            return
        
        st.session_state.mtf_current_trial = current_trial
        st.session_state.mtf_trial_start_time = time.time()
        st.session_state.mtf_precise_stimulus_onset = None
        st.session_state.mtf_response_recorded = False
    
    current_trial = st.session_state.mtf_current_trial
    if current_trial is None:
        return
    
    # Calculate elapsed time
    current_time = time.time()
    elapsed = current_time - st.session_state.mtf_trial_start_time if st.session_state.mtf_trial_start_time else 0
    
    # Container for smooth layout
    header_container = st.container()
    stimulus_container = st.container()
    response_container = st.container()
    feedback_container = st.container()
    
    with header_container:
        st.title(f"MTF Clarity Test - Trial {current_trial['trial_number']}")
        
        # Progress indicator
        progress_col1, progress_col2 = st.columns([3, 1])
        with progress_col1:
            progress_val = min(elapsed / 2.0, 1.0)  # 2秒完整周期
            st.progress(progress_val)
        with progress_col2:
            st.write(f"Trial {current_trial['trial_number']}")
    
    with stimulus_container:
        if elapsed < 1.0:
            # Fixation phase with animation
            show_animated_fixation(elapsed)
        else:
            # Stimulus phase
            if st.session_state.mtf_precise_stimulus_onset is None:
                # 記錄精確的stimulus onset時間
                st.session_state.mtf_precise_stimulus_onset = exp_manager.precise_timer.get_precise_onset_time()
            
            # Show stimulus image
            if current_trial['stimulus_image']:
                display_fullscreen_image(
                    current_trial['stimulus_image'], 
                    caption=f"Is this image clear? MTF: {current_trial['mtf_value']:.1f}%",
                    mtf_value=current_trial['mtf_value']
                )
            else:
                # Fallback test pattern
                mtf_value = current_trial['mtf_value']
                if 'cached_pattern' not in st.session_state:
                    pattern_size = 800
                    checker_size = 20
                    pattern = np.zeros((pattern_size, pattern_size), dtype=np.uint8)
                    x, y = np.meshgrid(np.arange(pattern_size), np.arange(pattern_size))
                    checker_mask = ((x // checker_size) + (y // checker_size)) % 2 == 0
                    pattern[checker_mask] = 255
                    pattern_rgb = np.stack([pattern, pattern, pattern], axis=-1)
                    st.session_state.cached_pattern = pattern_rgb
                
                base_pattern = st.session_state.cached_pattern.copy()
                sigma = ((100 - mtf_value) / 100.0) * 10.0
                
                if sigma > 0.5:
                    blurred = cv2.GaussianBlur(base_pattern, (0, 0), sigmaX=sigma, sigmaY=sigma)
                else:
                    blurred = base_pattern
                
                display_fullscreen_image(
                    blurred, 
                    caption=f"Test Pattern MTF {mtf_value:.1f}% (σ={sigma:.2f})",
                    mtf_value=mtf_value
                )
    
    with response_container:
        if elapsed >= 1.5 and not st.session_state.mtf_response_recorded:
            # Response buttons enabled after sufficient viewing time
            st.markdown("### Your Response:")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✓ Clear", key="clear_button", type="primary", use_container_width=True):
                    record_mtf_response_smooth(current_trial, True)
            
            with col2:
                if st.button("✗ Not Clear", key="not_clear_button", use_container_width=True):
                    record_mtf_response_smooth(current_trial, False)
                    
            # Keyboard shortcuts
            st.markdown("*Use keyboard: **Y** for Clear, **N** for Not Clear*")
            
        elif elapsed >= 1.0 and elapsed < 1.5:
            # Show countdown for when buttons will be enabled
            countdown = 1.5 - elapsed
            st.markdown("### Please observe the image...")
            col1, col2 = st.columns(2)
            
            with col1:
                st.button("✓ Clear", key="clear_button_disabled", disabled=True, use_container_width=True)
            with col2:
                st.button("✗ Not Clear", key="not_clear_button_disabled", disabled=True, use_container_width=True)
            
            st.markdown(f"*Buttons enabled in {countdown:.1f}s*")
    
    # Handle feedback and auto-advance
    if st.session_state.mtf_response_recorded:
        if st.session_state.mtf_feedback_start_time is None:
            st.session_state.mtf_feedback_start_time = time.time()
        
        feedback_elapsed = time.time() - st.session_state.mtf_feedback_start_time
        
        if feedback_elapsed < 1.5:  # Show feedback for 1.5 seconds
            # Feedback is shown in the record_mtf_response_smooth function
            pass
        else:
            # Auto-advance to next trial
            auto_advance_mtf_trial()
    
    # Display ADO monitoring in sidebar (always visible)
    display_ado_monitor(exp_manager, current_trial['trial_number'])
    
    # Auto-refresh for timing (only during active phases)
    if not st.session_state.mtf_response_recorded and elapsed < 10.0:  # Safety timeout
        time.sleep(0.1)  # Prevent too frequent updates
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
    
    # Get estimates before update
    old_estimates = exp_manager.get_current_estimates() if trial_data['trial_number'] > 1 else None
    
    # Create trial result for data saving
    mtf_trial_result = {
        'trial_number': trial_data['trial_number'],
        'mtf_value': trial_data['mtf_value'],
        'response': 'clear' if is_clear else 'not_clear',
        'reaction_time': raw_rt,
        'timestamp': datetime.now().isoformat(),
        'participant_id': st.session_state.get('participant_id', 'unknown'),
        'experiment_type': 'MTF_Clarity'
    }
    
    # Record the response with precise timing
    exp_manager.record_response(
        trial_data, 
        is_clear, 
        raw_rt, 
        st.session_state.mtf_precise_stimulus_onset
    )
    
    # Auto-save MTF data
    save_experiment_data(mtf_trial_result, is_practice=False)
    
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
                except:
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
    
    # Get estimates before update
    old_estimates = exp_manager.get_current_estimates() if trial_data['trial_number'] > 1 else None
    
    # Create trial result for data saving
    mtf_trial_result = {
        'trial_number': trial_data['trial_number'],
        'mtf_value': trial_data['mtf_value'],
        'response': 'clear' if is_clear else 'not_clear',
        'reaction_time': reaction_time,
        'timestamp': datetime.now().isoformat(),
        'participant_id': st.session_state.get('participant_id', 'unknown'),
        'experiment_type': 'MTF_Clarity'
    }
    
    # Record the response
    exp_manager.record_response(trial_data, is_clear, reaction_time)
    
    # Auto-save MTF data
    save_experiment_data(mtf_trial_result, is_practice=False)
    
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
            except:
                st.metric("Next MTF", "Computing...")
        else:
            st.metric("Next MTF", "Complete" if exp_manager.is_experiment_complete() else "N/A")
    
    # Show optimization details
    if hasattr(exp_manager, 'ado_engine') and exp_manager.ado_engine:
        try:
            entropy = exp_manager.get_ado_entropy()
            st.caption(f"Posterior Entropy: {entropy:.3f} (lower = more certain)")
        except:
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
        except:
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
        design_range = st.slider("MTF range", 10, 90, (10, 90), step=5)
        
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
                threshold_range=(5, 95),
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
                response = np.random.choice([0, 1])
                ado_engine.update_posterior(optimal_mtf, response)
            
            progress_bar.progress(100)
            status_text.text("✅ 基準測試完成!")
            
            # Calculate statistics
            mean_time = np.mean(trial_times)
            max_time = np.max(trial_times)
            min_time = np.min(trial_times)
            std_time = np.std(trial_times)
            
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
    """Display information about database storage"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗄️ Database Storage")
    
    try:
        if 'db_manager' not in st.session_state:
            st.session_state.db_manager = DatabaseManager()
        
        db = st.session_state.db_manager
        
        # Show current experiment info
        if 'current_experiment_id' in st.session_state:
            experiment_id = st.session_state.current_experiment_id
            saved_trials = st.session_state.get('saved_trials', 0)
            
            st.sidebar.success("Data is being saved to PostgreSQL database!")
            st.sidebar.write(f"**Current Experiment ID:** {experiment_id}")
            st.sidebar.write(f"**Trials Saved:** {saved_trials}")
            
            # Show download button for current experiment
            if st.sidebar.button("📥 Download Current Experiment"):
                try:
                    csv_data = db.export_to_csv(experiment_id)
                    if csv_data:
                        participant_id = st.session_state.get('participant_id', 'unknown')
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"experiment_{experiment_id}_{participant_id}_{timestamp}.csv"
                        
                        st.sidebar.download_button(
                            label="Download CSV",
                            data=csv_data,
                            file_name=filename,
                            mime='text/csv'
                        )
                    else:
                        st.sidebar.error("No data found for current experiment")
                except Exception as e:
                    st.sidebar.error(f"Error exporting data: {str(e)}")
        
        # Show participant history
        participant_id = st.session_state.get('participant_id')
        if participant_id:
            try:
                experiments = db.get_participant_experiments(participant_id)
                if experiments:
                    st.sidebar.write("**Previous Experiments:**")
                    for exp in experiments[-3:]:  # Show last 3 experiments
                        status = "✅ Complete" if exp['completed_at'] else "🔄 In Progress"
                        st.sidebar.write(f"• ID {exp['id']}: {exp['experiment_type']} {status}")
            except Exception as e:
                st.sidebar.write("Database connection established")
        else:
            st.sidebar.info("Enter participant ID to see database storage")
            
    except Exception as e:
        st.sidebar.error(f"Database connection error: {str(e)}")
        st.sidebar.info("PostgreSQL database is available but connection failed")

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
    
    experiment_type = st.session_state.get('experiment_type', 'Brightness Discrimination (2AFC)')
    
    # Handle different experiment stages
    if st.session_state.experiment_stage == 'welcome':
        welcome_screen()
    elif st.session_state.experiment_stage == 'ado_benchmark':
        ado_benchmark_screen()
    elif st.session_state.experiment_stage == 'instructions':
        instructions_screen()
    elif st.session_state.experiment_stage == 'practice':
        if experiment_type == "Brightness Discrimination (2AFC)":
            practice_screen()
        else:
            # MTF experiments skip practice, go directly to trials
            st.session_state.experiment_stage = 'mtf_trial'
            st.rerun()
    elif st.session_state.experiment_stage == 'experiment':
        experiment_screen()
    elif st.session_state.experiment_stage == 'mtf_trial':
        mtf_trial_screen()
    elif st.session_state.experiment_stage == 'mtf_results':
        mtf_results_screen()
    
    # Add footer
    st.markdown("---")
    st.markdown("*Psychophysics Experiment Platform*")

if __name__ == "__main__":
    main()
