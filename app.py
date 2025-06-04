import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime
import json
import base64
from experiment import ExperimentManager
from data_manager import DataManager
from stimulus_manager import StimulusManager

# Configure page
st.set_page_config(
    page_title="Psychophysics 2AFC Experiment",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables
if 'experiment_stage' not in st.session_state:
    st.session_state.experiment_stage = 'welcome'
if 'participant_id' not in st.session_state:
    st.session_state.participant_id = None
if 'experiment_manager' not in st.session_state:
    st.session_state.experiment_manager = None
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()
if 'stimulus_manager' not in st.session_state:
    st.session_state.stimulus_manager = StimulusManager()
if 'trial_start_time' not in st.session_state:
    st.session_state.trial_start_time = None
if 'awaiting_response' not in st.session_state:
    st.session_state.awaiting_response = False

def show_stimulus_preview_inline(stimulus_type):
    """Show a preview of the stimulus type"""
    st.subheader("Stimulus Preview")
    
    try:
        stimulus_manager = st.session_state.stimulus_manager
        
        if stimulus_type.startswith('visual') or stimulus_type in ['gabor', 'noise']:
            # Generate two example visual stimuli
            low_intensity = stimulus_manager.generate_visual_stimulus(stimulus_type, 0.3)
            high_intensity = stimulus_manager.generate_visual_stimulus(stimulus_type, 0.7)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Lower Intensity**")
                st.markdown(f'<img src="{low_intensity}" style="width: 150px; height: 150px; border: 1px solid #ccc;">', 
                           unsafe_allow_html=True)
            with col2:
                st.markdown("**Higher Intensity**")
                st.markdown(f'<img src="{high_intensity}" style="width: 150px; height: 150px; border: 1px solid #ccc;">', 
                           unsafe_allow_html=True)
                
        elif stimulus_type.startswith('auditory'):
            # Generate example audio stimuli
            low_audio = stimulus_manager.generate_audio_stimulus(stimulus_type, 0.3, duration=1.0)
            high_audio = stimulus_manager.generate_audio_stimulus(stimulus_type, 0.7, duration=1.0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Lower Intensity**")
                st.audio(low_audio, format='audio/wav')
            with col2:
                st.markdown("**Higher Intensity**")
                st.audio(high_audio, format='audio/wav')
                
        elif stimulus_type.startswith('video') or stimulus_type == 'flicker':
            # Generate example video stimuli
            low_video = stimulus_manager.generate_video_stimulus(stimulus_type, 0.3, duration=1.5)
            high_video = stimulus_manager.generate_video_stimulus(stimulus_type, 0.7, duration=1.5)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Lower Intensity**")
                st.markdown(f'<img src="{low_video}" style="width: 150px; height: 150px; border: 1px solid #ccc;">', 
                           unsafe_allow_html=True)
            with col2:
                st.markdown("**Higher Intensity**")
                st.markdown(f'<img src="{high_video}" style="width: 150px; height: 150px; border: 1px solid #ccc;">', 
                           unsafe_allow_html=True)
        
        st.caption("These are examples showing the difference you'll be asked to detect.")
        
    except Exception as e:
        st.error(f"Unable to generate stimulus preview: {str(e)}")
        st.info("Preview unavailable, but the experiment will work normally.")

def welcome_screen():
    """Display welcome screen and collect participant information"""
    st.title("🧠 Psychophysics 2AFC Experiment")
    st.markdown("---")
    
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
    
    # Experiment configuration
    st.subheader("Experiment Configuration")
    
    # Stimulus type selection
    available_stimuli = st.session_state.stimulus_manager.get_available_stimulus_types()
    
    stimulus_categories = {
        'Visual Stimuli': {
            'visual_intensity': 'Brightness/Contrast',
            'visual_size': 'Size Comparison',
            'visual_color': 'Color Hue',
            'gabor': 'Gabor Patches',
            'noise': 'Visual Noise'
        },
        'Auditory Stimuli': {
            'auditory_pitch': 'Pitch/Frequency',
            'auditory_volume': 'Volume/Loudness',
            'noise': 'Audio Noise'
        },
        'Video Stimuli': {
            'video_speed': 'Motion Speed',
            'flicker': 'Flicker Rate'
        }
    }
    
    st.subheader("Stimulus Type")
    selected_category = st.selectbox("Choose stimulus category:", list(stimulus_categories.keys()))
    stimulus_type = st.selectbox(
        "Select specific stimulus type:", 
        list(stimulus_categories[selected_category].keys()),
        format_func=lambda x: stimulus_categories[selected_category][x]
    )
    
    # Show description of selected stimulus type
    descriptions = {
        'visual_intensity': 'Compare circles with different brightness levels',
        'visual_size': 'Compare circles of different sizes',
        'visual_color': 'Compare circles with different color hues',
        'gabor': 'Compare Gabor patches with different spatial frequencies',
        'noise': 'Compare visual noise patterns with different intensities',
        'auditory_pitch': 'Compare tones with different pitch/frequency',
        'auditory_volume': 'Compare tones with different volume levels',
        'noise': 'Compare white noise with different intensity levels',
        'video_speed': 'Compare moving objects with different speeds',
        'flicker': 'Compare flickering objects with different rates'
    }
    
    st.info(f"**Task**: {descriptions.get(stimulus_type, 'Compare stimuli and choose the more intense one')}")
    
    # Show stimulus preview
    if st.checkbox("Show stimulus preview"):
        show_stimulus_preview_inline(stimulus_type)
    
    col1, col2 = st.columns(2)
    with col1:
        num_trials = st.slider("Number of trials:", 10, 100, 30)
        stimulus_duration = st.slider("Stimulus duration (seconds):", 0.5, 5.0, 2.0, 0.1)
    
    with col2:
        inter_trial_interval = st.slider("Inter-trial interval (seconds):", 0.5, 3.0, 1.0, 0.1)
        num_practice_trials = st.slider("Practice trials:", 3, 10, 5)
    
    # Start experiment button
    if st.button("Start Experiment", type="primary"):
        if participant_id.strip():
            st.session_state.participant_id = participant_id.strip()
            st.session_state.experiment_manager = ExperimentManager(
                num_trials=num_trials,
                num_practice_trials=num_practice_trials,
                stimulus_duration=stimulus_duration,
                inter_trial_interval=inter_trial_interval,
                participant_id=st.session_state.participant_id,
                stimulus_type=stimulus_type
            )
            st.session_state.experiment_stage = 'instructions'
            st.rerun()
        else:
            st.error("Please enter a valid Participant ID")

def show_stimulus_preview_inline(stimulus_type):
    """Show a preview of the stimulus type"""
    st.subheader("Stimulus Preview")
    
    try:
        stimulus_manager = st.session_state.stimulus_manager
        
        if stimulus_type.startswith('visual') or stimulus_type in ['gabor', 'noise']:
            # Generate two example visual stimuli
            low_intensity = stimulus_manager.generate_visual_stimulus(stimulus_type, 0.3)
            high_intensity = stimulus_manager.generate_visual_stimulus(stimulus_type, 0.7)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Lower Intensity**")
                st.markdown(f'<img src="{low_intensity}" style="width: 150px; height: 150px; border: 1px solid #ccc;">', 
                           unsafe_allow_html=True)
            with col2:
                st.markdown("**Higher Intensity**")
                st.markdown(f'<img src="{high_intensity}" style="width: 150px; height: 150px; border: 1px solid #ccc;">', 
                           unsafe_allow_html=True)
                
        elif stimulus_type.startswith('auditory'):
            # Generate example audio stimuli
            low_audio = stimulus_manager.generate_audio_stimulus(stimulus_type, 0.3, duration=1.0)
            high_audio = stimulus_manager.generate_audio_stimulus(stimulus_type, 0.7, duration=1.0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Lower Intensity**")
                st.audio(low_audio, format='audio/wav')
            with col2:
                st.markdown("**Higher Intensity**")
                st.audio(high_audio, format='audio/wav')
                
        elif stimulus_type.startswith('video') or stimulus_type == 'flicker':
            # Generate example video stimuli
            low_video = stimulus_manager.generate_video_stimulus(stimulus_type, 0.3, duration=1.5)
            high_video = stimulus_manager.generate_video_stimulus(stimulus_type, 0.7, duration=1.5)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Lower Intensity**")
                st.markdown(f'<img src="{low_video}" style="width: 150px; height: 150px; border: 1px solid #ccc;">', 
                           unsafe_allow_html=True)
            with col2:
                st.markdown("**Higher Intensity**")
                st.markdown(f'<img src="{high_video}" style="width: 150px; height: 150px; border: 1px solid #ccc;">', 
                           unsafe_allow_html=True)
        
        st.caption("These are examples showing the difference you'll be asked to detect.")
        
    except Exception as e:
        st.error(f"Unable to generate stimulus preview: {str(e)}")
        st.info("Preview unavailable, but the experiment will work normally.")

def instructions_screen():
    """Display detailed instructions before practice"""
    st.title("📋 Experiment Instructions")
    st.markdown("---")
    
    st.header("Task Description")
    
    # Get experiment manager to show specific instructions
    exp_manager = st.session_state.experiment_manager
    stimulus_type = exp_manager.stimulus_type if exp_manager else "visual_intensity"
    
    # Specific instructions based on stimulus type
    task_descriptions = {
        'visual_intensity': "You will see two circles with different brightness levels. Choose the **brighter** one.",
        'visual_size': "You will see two circles of different sizes. Choose the **larger** one.",
        'visual_color': "You will see two colored circles. Choose the one with **higher color intensity**.",
        'gabor': "You will see two Gabor patches (striped patterns). Choose the one with **higher spatial frequency** (more stripes).",
        'noise': "You will see two visual noise patterns. Choose the one with **more intense noise**.",
        'auditory_pitch': "You will hear two tones with different pitches. Choose the one with **higher pitch**.",
        'auditory_volume': "You will hear two tones with different volumes. Choose the **louder** one.",
        'video_speed': "You will see two moving objects. Choose the one moving **faster**.",
        'flicker': "You will see two flickering objects. Choose the one flickering **faster**."
    }
    
    description = task_descriptions.get(stimulus_type, "You will compare two stimuli and choose the more intense one.")
    
    st.write(f"""
    {description}
    
    Your task is to:
    1. **Examine both stimuli carefully**
    2. **Make your choice based on the specific criterion**
    3. **Respond as quickly and accurately as possible**
    """)
    
    st.header("How to Respond")
    st.write("""
    - Click the **Left** button to choose the left stimulus
    - Click the **Right** button to choose the right stimulus
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
        if st.button("Start Practice Trials →", type="primary"):
            st.session_state.experiment_stage = 'practice'
            st.session_state.experiment_manager.start_practice()
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
            st.write(f"**Total trials completed:** {total_trials}")
            st.write(f"**Average reaction time:** {avg_rt:.2f} seconds")
        
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
    st.write(f"Trial {exp_manager.current_trial + 1} of {exp_manager.num_trials}")
    
    # Run trial
    run_trial(is_practice=False)

def run_trial(is_practice=False):
    """Run a single trial"""
    exp_manager = st.session_state.experiment_manager
    
    # Get current trial data
    current_trial = exp_manager.get_current_trial(is_practice)
    
    if current_trial is None:
        st.error("Error loading trial data")
        return
    
    # Display appropriate instructions based on stimulus type
    stimulus_type = current_trial['stimulus_type']
    instructions = get_stimulus_instructions(stimulus_type)
    st.subheader(instructions)
    
    # Record trial start time if not already recorded
    if not st.session_state.awaiting_response:
        st.session_state.trial_start_time = time.time()
        st.session_state.awaiting_response = True
    
    # Display stimuli based on type
    display_stimuli(current_trial)
    
    # Response buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        button_col1, button_col2 = st.columns(2)
        
        with button_col1:
            if st.button("← Left (A)", key="left_button", use_container_width=True):
                record_response("left", current_trial, is_practice)
        
        with button_col2:
            if st.button("Right (L) →", key="right_button", use_container_width=True):
                record_response("right", current_trial, is_practice)
    
    # Keyboard shortcuts info
    st.markdown("*Use keyboard: **A** for Left, **L** for Right*")

def get_stimulus_instructions(stimulus_type):
    """Get appropriate instructions for each stimulus type"""
    instructions = {
        'visual_intensity': "Choose the stimulus that appears brighter:",
        'visual_size': "Choose the stimulus that appears larger:",
        'visual_color': "Choose the stimulus with higher color intensity:",
        'gabor': "Choose the stimulus with higher spatial frequency:",
        'noise': "Choose the stimulus with more visual noise:",
        'auditory_pitch': "Choose the stimulus with higher pitch:",
        'auditory_volume': "Choose the stimulus that sounds louder:",
        'video_speed': "Choose the stimulus moving faster:",
        'flicker': "Choose the stimulus flickering faster:"
    }
    return instructions.get(stimulus_type, "Choose the more intense stimulus:")

def display_stimuli(current_trial):
    """Display stimuli based on their type"""
    stimulus_type = current_trial['stimulus_type']
    left_stimulus = current_trial['left_stimulus']
    right_stimulus = current_trial['right_stimulus']
    
    if stimulus_type.startswith('visual') or stimulus_type in ['gabor', 'noise']:
        display_visual_stimuli(left_stimulus, right_stimulus)
    elif stimulus_type.startswith('auditory'):
        display_audio_stimuli(left_stimulus, right_stimulus)
    elif stimulus_type.startswith('video') or stimulus_type == 'flicker':
        display_video_stimuli(left_stimulus, right_stimulus)

def display_visual_stimuli(left_stimulus, right_stimulus):
    """Display visual stimuli side by side"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        stim_col1, stim_col2 = st.columns(2)
        
        with stim_col1:
            st.markdown("### Left Stimulus")
            st.markdown(f'<img src="{left_stimulus["content"]}" style="width: 200px; height: 200px; border: 2px solid #ccc;">', 
                       unsafe_allow_html=True)
        
        with stim_col2:
            st.markdown("### Right Stimulus")
            st.markdown(f'<img src="{right_stimulus["content"]}" style="width: 200px; height: 200px; border: 2px solid #ccc;">', 
                       unsafe_allow_html=True)

def display_audio_stimuli(left_stimulus, right_stimulus):
    """Display audio stimuli with playback controls"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        stim_col1, stim_col2 = st.columns(2)
        
        with stim_col1:
            st.markdown("### Left Stimulus")
            st.markdown("🔊 Click to play")
            st.audio(left_stimulus["content"], format='audio/wav')
        
        with stim_col2:
            st.markdown("### Right Stimulus")
            st.markdown("🔊 Click to play")
            st.audio(right_stimulus["content"], format='audio/wav')
        
        st.info("💡 **Tip**: You can play each audio stimulus multiple times before making your choice")

def display_video_stimuli(left_stimulus, right_stimulus):
    """Display video stimuli (animated GIFs)"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        stim_col1, stim_col2 = st.columns(2)
        
        with stim_col1:
            st.markdown("### Left Stimulus")
            st.markdown(f'<img src="{left_stimulus["content"]}" style="width: 200px; height: 200px; border: 2px solid #ccc;">', 
                       unsafe_allow_html=True)
        
        with stim_col2:
            st.markdown("### Right Stimulus")
            st.markdown(f'<img src="{right_stimulus["content"]}" style="width: 200px; height: 200px; border: 2px solid #ccc;">', 
                       unsafe_allow_html=True)

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
        'timestamp': datetime.now().isoformat()
    }
    
    # Add to experiment manager
    exp_manager = st.session_state.experiment_manager
    exp_manager.record_trial(trial_result, is_practice)
    
    # Reset trial state
    st.session_state.trial_start_time = None
    st.session_state.awaiting_response = False
    
    # Show brief feedback
    st.success(f"Response recorded! (RT: {reaction_time:.2f}s)")
    
    # Auto-advance after brief delay
    time.sleep(exp_manager.inter_trial_interval)
    st.rerun()

# Main app logic
def main():
    """Main application logic"""
    
    # Handle different experiment stages
    if st.session_state.experiment_stage == 'welcome':
        welcome_screen()
    elif st.session_state.experiment_stage == 'instructions':
        instructions_screen()
    elif st.session_state.experiment_stage == 'practice':
        practice_screen()
    elif st.session_state.experiment_stage == 'experiment':
        experiment_screen()
    
    # Add footer
    st.markdown("---")
    st.markdown("*Psychophysics 2AFC Experiment Platform*")

if __name__ == "__main__":
    main()
