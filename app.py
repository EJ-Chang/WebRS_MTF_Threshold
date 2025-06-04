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

# Configure page
st.set_page_config(
    page_title="Psychophysics 2AFC Experiment",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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
    
    col1, col2 = st.columns(2)
    with col1:
        num_trials = st.slider("Number of trials:", 10, 100, 30)
        stimulus_duration = st.slider("Stimulus duration (seconds):", 0.5, 5.0, 2.0, 0.1)
    
    with col2:
        inter_trial_interval = st.slider("Inter-trial interval (seconds):", 0.5, 3.0, 1.0, 0.1)
        num_practice_trials = st.slider("Practice trials:", 3, 10, 5)
    
    # ADO configuration
    st.subheader("Adaptive Design Optimization (ADO)")
    use_ado = st.checkbox(
        "Enable ADO for optimal stimulus selection", 
        value=True,
        help="ADO adaptively selects stimuli to maximize information gain about the psychometric function"
    )
    
    if use_ado:
        st.info("🧠 ADO will intelligently select stimuli to efficiently estimate your psychometric function parameters")
    
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
                use_ado=use_ado
            )
            st.session_state.experiment_stage = 'instructions'
            st.rerun()
        else:
            st.error("Please enter a valid Participant ID")

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
        if st.button("Start Practice Trials →", type="primary"):
            st.session_state.experiment_stage = 'practice'
            st.session_state.experiment_manager.start_practice()
            # Reset trial state for new session
            st.session_state.trial_locked = False
            st.session_state.current_trial_data = None
            st.session_state.awaiting_response = False
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
    
    # Add ADO stimulus value if available
    if 'ado_stimulus_value' in trial_data:
        trial_result['ado_stimulus_value'] = trial_data['ado_stimulus_value']
    
    # Add to experiment manager
    exp_manager = st.session_state.experiment_manager
    exp_manager.record_trial(trial_result, is_practice)
    
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
