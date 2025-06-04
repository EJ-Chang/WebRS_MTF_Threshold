import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime
import json
from experiment import ExperimentManager
from data_manager import DataManager
from psychometric_analysis import PsychometricAnalyzer

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
if 'psychometric_analyzer' not in st.session_state:
    st.session_state.psychometric_analyzer = PsychometricAnalyzer()
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

def completion_screen():
    """Display experiment completion with psychometric function analysis"""
    st.title("🎉 Experiment Complete!")
    st.success("Thank you for participating in this psychophysics experiment!")
    
    exp_manager = st.session_state.experiment_manager
    analyzer = st.session_state.psychometric_analyzer
    
    # Get experiment data
    all_data = exp_manager.get_all_data()
    trial_data = all_data.get('main_trials', [])
    
    if not trial_data:
        st.error("No trial data available for analysis.")
        return
    
    # Display basic statistics
    st.subheader("📊 Experiment Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Trials", len(trial_data))
    
    with col2:
        correct_trials = sum(1 for trial in trial_data if trial.get('is_correct', False))
        accuracy = correct_trials / len(trial_data) if trial_data else 0
        st.metric("Overall Accuracy", f"{accuracy:.1%}")
    
    with col3:
        avg_rt = np.mean([trial.get('reaction_time', 0) for trial in trial_data])
        st.metric("Average RT", f"{avg_rt:.2f}s")
    
    # Calculate and display psychometric function
    st.subheader("📈 Your Psychometric Function")
    st.write("This shows how your accuracy changes with stimulus difficulty:")
    
    try:
        # Calculate psychometric data
        psych_data = analyzer.calculate_psychometric_data(trial_data)
        
        if not psych_data or 'grouped_data' not in psych_data:
            st.error("Insufficient data for psychometric analysis.")
            return
        
        # Fit psychometric function
        fit_results = analyzer.fit_psychometric_function(psych_data['grouped_data'])
        
        # Display interactive plot
        if 'error' not in fit_results:
            fig = analyzer.create_psychometric_plot(psych_data, fit_results)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display analysis summary
            st.subheader("📋 Analysis Results")
            summary = analyzer.generate_analysis_summary(psych_data, fit_results)
            st.text(summary)
            
            # Display threshold information prominently
            if 'thresholds' in fit_results:
                st.subheader("🎯 Your Discrimination Threshold")
                threshold_75 = fit_results['thresholds']['threshold_75']
                st.info(f"**75% Threshold: {threshold_75:.4f}**\n\nThis is the stimulus difference you need to achieve 75% accuracy in brightness discrimination.")
        
        else:
            st.error(f"Could not fit psychometric function: {fit_results['error']}")
            
            # Show raw data instead
            st.subheader("📊 Raw Data Summary")
            grouped_data = psych_data['grouped_data']
            st.dataframe(grouped_data)
    
    except Exception as e:
        st.error(f"Error analyzing psychometric function: {str(e)}")
        
        # Show basic trial summary as fallback
        st.subheader("📊 Trial Summary")
        trial_summary = []
        for trial in trial_data:
            trial_summary.append({
                'Trial': trial.get('trial_number', 'Unknown'),
                'Stimulus Difference': trial.get('stimulus_difference', 0),
                'Correct': trial.get('is_correct', False),
                'Reaction Time': trial.get('reaction_time', 0)
            })
        
        df = pd.DataFrame(trial_summary)
        st.dataframe(df)
    
    # Data export options
    st.subheader("💾 Download Your Data")
    data_manager = st.session_state.data_manager
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV export
        csv_data = data_manager.export_to_csv(trial_data, st.session_state.participant_id)
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"psychophysics_data_{st.session_state.participant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # JSON export
        json_data = data_manager.export_to_json(all_data)
        st.download_button(
            label="📋 Download JSON",
            data=json_data,
            file_name=f"psychophysics_data_{st.session_state.participant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    # Option to start new experiment
    st.markdown("---")
    if st.button("🔄 Start New Experiment", type="primary"):
        # Reset all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

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
    
    # Check if experiment is complete
    if not is_practice and hasattr(exp_manager, 'current_trial') and exp_manager.current_trial >= exp_manager.num_trials:
        st.session_state.experiment_stage = 'completed'
        time.sleep(1)  # Brief delay before showing results
        st.rerun()
    else:
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
    elif st.session_state.experiment_stage == 'completed':
        completion_screen()
    
    # Add footer
    st.markdown("---")
    st.markdown("*Psychophysics 2AFC Experiment Platform*")

if __name__ == "__main__":
    main()
