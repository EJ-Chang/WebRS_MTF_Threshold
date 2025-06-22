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
        st.title("🧠 MTF Clarity Testing Experiment")
        st.markdown("*Refactored Version - Modular Architecture*")
        st.markdown("---")

        # Add performance testing option
        st.sidebar.markdown("### 🔧 Developer Tools")
        if st.sidebar.button("📊 ADO Performance Test"):
            session_manager.set_experiment_stage('benchmark')
            st.rerun()
        st.write("""
        This is an MTF (Modulation Transfer Function) clarity testing experiment using Adaptive Design Optimization (ADO). 
        You will view images with varying levels of clarity and make judgments about their sharpness.
        """)

        _display_instructions()
        
        st.markdown("---")

        # Participant ID input
        participant_id = st.text_input(
            "Enter Participant ID:",
            value="",
            help="Enter a unique identifier (e.g., your initials + date)"
        )

        # Stimulus image selection
        st.subheader("Stimulus Image Selection")
        _display_stimulus_selection()

        st.markdown("---")

        # Experiment configuration
        config = _display_experiment_configuration()
        
        # Display options
        show_trial_feedback = _display_display_options()

        # ADO configuration info
        _display_ado_info()

        # Start experiment button
        if create_action_button("Start MTF Experiment", key="start_mtf_experiment"):
            if _validate_experiment_setup(participant_id):
                _initialize_experiment(session_manager, participant_id, config, show_trial_feedback)

        st.markdown("---")

        # Data analysis section
        _display_data_analysis_section()
        
    except Exception as e:
        logger.error(f"Error in welcome screen: {e}")
        st.error(f"Error displaying welcome screen: {e}")

def _display_instructions() -> None:
    """Display experiment instructions"""
    st.subheader("Instructions:")
    st.write("""
    1. **Setup**: Enter your participant ID and configure the experiment parameters
    2. **Practice**: Complete a few practice trials to familiarize yourself with the task
    3. **Main Experiment**: Respond to image clarity questions - the experiment adapts based on your responses
    4. **Completion**: Your data will be automatically saved to the database
    """)

def _display_stimulus_selection() -> None:
    """Display stimulus image selection interface"""
    try:
        # Get available images
        stimuli_dir = "stimuli_preparation"
        available_images = _get_available_images(stimuli_dir)

        if available_images:
            st.write("Select the stimulus image for your experiment:")
            _display_image_grid(available_images)
            _show_current_selection()
        else:
            st.warning("No stimulus images found in stimuli_preparation folder")
            
    except Exception as e:
        logger.error(f"Error in stimulus selection: {e}")
        st.error("Error loading stimulus images")

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
        'stimuli_img.png': 'Original Stimulus',
        'text_img.png': 'Text Image',
        'tw_newsimg.png': 'Taiwan News',
        'us_newsimg.png': 'US News'
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
                
                if st.button(f"Select {display_name}", key=f"select_{img_name}"):
                    st.session_state.selected_stimulus_image = img_path
                    st.rerun()
                    
            except Exception as e:
                logger.error(f"Error loading {img_name}: {e}")
                st.error(f"Error loading {img_name}: {e}")

def _show_current_selection() -> None:
    """Show currently selected stimulus image"""
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

def _display_experiment_configuration() -> dict:
    """Display experiment configuration options"""
    st.subheader("Experiment Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        max_trials = st.slider("Maximum trials:", 20, 100, 50)
        min_trials = st.slider("Minimum trials:", 10, 30, 15)

    with col2:
        convergence_threshold = st.slider("Convergence threshold:", 0.05, 0.3, 0.15, 0.01)
        stimulus_duration = st.slider("Stimulus duration (seconds):", 0.5, 5.0, 1.0, 0.1)
    
    return {
        'max_trials': max_trials,
        'min_trials': min_trials,
        'convergence_threshold': convergence_threshold,
        'stimulus_duration': stimulus_duration
    }

def _display_display_options() -> bool:
    """Display display options"""
    st.subheader("Display Options")
    return st.checkbox(
        "Show trial feedback (ADO results after each response)",
        value=True,
        help="If unchecked, experiment will proceed directly to next trial after response"
    )

def _display_ado_info() -> None:
    """Display ADO configuration information"""
    st.subheader("Adaptive Design Optimization (ADO)")
    st.info("ADO is enabled by default and will intelligently select MTF values to efficiently estimate your clarity perception threshold")

def _validate_experiment_setup(participant_id: str) -> bool:
    """Validate experiment setup"""
    if not participant_id.strip():
        st.error("Please enter a valid Participant ID")
        return False
    elif 'selected_stimulus_image' not in st.session_state:
        st.error("Please select a stimulus image")
        return False
    return True

def _initialize_experiment(session_manager, participant_id: str, config: dict, show_trial_feedback: bool) -> None:
    """Initialize experiment with given configuration"""
    try:
        session_manager.set_participant_id(participant_id.strip())
        st.session_state.experiment_type = "MTF Clarity Testing"

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
        
        logger.info(f"🔧 Trial feedback setting saved: {show_trial_feedback}")
        
        session_manager.set_experiment_stage('instructions')
        st.rerun()
        
    except Exception as e:
        logger.error(f"Error initializing experiment: {e}")
        st.error(f"Error initializing experiment: {e}")

def _display_data_analysis_section() -> None:
    """Display data analysis section for previous experiments"""
    st.subheader("📊 Analyze Previous Data")
    st.markdown("Upload CSV data from a previous experiment to visualize the psychometric function:")

    uploaded_file = st.file_uploader(
        "Choose CSV file", 
        type=['csv'],
        help="Upload a CSV file from a previous experiment to analyze"
    )

    if uploaded_file is not None:
        _analyze_uploaded_data(uploaded_file)

def _analyze_uploaded_data(uploaded_file) -> None:
    """Analyze uploaded CSV data"""
    try:
        # Read the uploaded CSV
        df = pd.read_csv(uploaded_file)
        
        st.success(f"Data loaded successfully! Found {len(df)} trials.")
        
        # Show data preview
        with st.expander("Data Preview"):
            st.dataframe(df.head(10))
            st.write("**Columns found:**", list(df.columns))
            st.write("**Data types:**")
            for col in df.columns:
                st.write(f"- {col}: {df[col].dtype}")

        # Convert to trial data format
        trial_data = df.to_dict('records')
        
        # Generate psychometric function
        st.subheader("Psychometric Function from Uploaded Data")
        from app import plot_psychometric_function  # Import here to avoid circular import
        plot_psychometric_function(trial_data)
        
        # Show stimulus info
        _show_stimulus_info(df)
        
        # Show summary statistics
        _show_summary_statistics(df)
        
    except Exception as e:
        logger.error(f"Error analyzing uploaded data: {e}")
        st.error(f"Error reading file: {str(e)}")
        _show_expected_format()

def _show_stimulus_info(df: pd.DataFrame) -> None:
    """Show stimulus image information"""
    if 'stimulus_image_file' in df.columns:
        stimulus_files = df['stimulus_image_file'].dropna().unique()
        if len(stimulus_files) > 0:
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

def _show_summary_statistics(df: pd.DataFrame) -> None:
    """Show summary statistics"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Trials", len(df))
    
    with col2:
        if 'response' in df.columns:
            clear_rate = (df['response'] == 'clear').mean()
            st.metric("Overall Clear Rate", f"{clear_rate:.1%}")
    
    with col3:
        if 'reaction_time' in df.columns:
            avg_rt = df['reaction_time'].mean()
            st.metric("Average RT", f"{avg_rt:.2f}s")

def _show_expected_format() -> None:
    """Show expected CSV format"""
    st.info("Please make sure the CSV file has the correct format with columns like 'mtf_value', 'response', 'reaction_time', etc.")
    
    with st.expander("Expected CSV Format"):
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