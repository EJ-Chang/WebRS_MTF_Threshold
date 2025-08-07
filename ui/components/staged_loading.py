"""
Staged loading components for improved user experience
Provides progressive loading: text → controls → images
"""
import streamlit as st
import time
from typing import Dict, Any, Callable, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class StagedLoader:
    """Manages staged loading of UI components"""
    
    def __init__(self, enable_staging: bool = True):
        self.enable_staging = enable_staging
        self.stage_containers = {}
        
    def create_stage_containers(self, stages: list = None) -> Dict[str, Any]:
        """Create containers for different loading stages
        
        Args:
            stages: List of stage names (default: ['header', 'content', 'controls', 'images'])
            
        Returns:
            Dict of stage containers
        """
        if stages is None:
            stages = ['header', 'content', 'controls', 'images']
        
        containers = {}
        for stage in stages:
            container_key = f"stage_container_{stage}"
            if container_key not in st.session_state:
                st.session_state[container_key] = st.empty()
            containers[stage] = st.session_state[container_key]
        
        self.stage_containers = containers
        logger.debug(f"📦 Created {len(stages)} stage containers: {stages}")
        return containers
    
    def load_stage(self, stage_name: str, content_func: Callable, delay: float = 0.1) -> bool:
        """Load content for a specific stage
        
        Args:
            stage_name: Name of the stage to load
            content_func: Function that generates the content
            delay: Delay before loading this stage (seconds)
            
        Returns:
            True if loading was successful
        """
        try:
            if not self.enable_staging:
                # If staging is disabled, load immediately
                content_func()
                return True
            
            if stage_name not in self.stage_containers:
                logger.warning(f"Stage container not found: {stage_name}")
                content_func()  # Fallback to direct loading
                return False
            
            # Add delay for staged loading effect
            if delay > 0:
                time.sleep(delay)
            
            # Load content into stage container
            with self.stage_containers[stage_name].container():
                content_func()
            
            logger.debug(f"📥 Loaded stage: {stage_name} (delay: {delay}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error loading stage {stage_name}: {e}")
            # Fallback to direct loading
            try:
                content_func()
            except Exception as e2:
                logger.error(f"Fallback loading also failed: {e2}")
            return False
    
    def clear_all_stages(self):
        """Clear all stage containers"""
        try:
            for stage_name, container in self.stage_containers.items():
                container.empty()
            logger.debug("🧹 Cleared all stage containers")
        except Exception as e:
            logger.error(f"Error clearing stages: {e}")

def display_trial_with_staged_loading(session_manager, experiment_controller, enable_staging: bool = True):
    """Display trial screen with staged loading
    
    Args:
        session_manager: Session manager instance
        experiment_controller: Experiment controller instance  
        enable_staging: Whether to enable staged loading
    """
    try:
        # Create staged loader
        loader = StagedLoader(enable_staging)
        containers = loader.create_stage_containers(['header', 'progress', 'content', 'controls'])
        
        # Stage 1: Header and basic info (immediate)
        def load_header():
            st.subheader("請判斷圖像是否清楚")
            
        loader.load_stage('header', load_header, delay=0)
        
        # Stage 2: Progress indicator (quick)
        def load_progress():
            from ui.components.progress_indicators import show_trial_progress
            progress = experiment_controller.get_experiment_progress()
            show_trial_progress(
                progress['current_trial'],
                progress['total_trials'], 
                progress['is_practice'],
                session_manager.get_practice_trials_completed()
            )
            
        loader.load_stage('progress', load_progress, delay=0.1)
        
        # Stage 3: Main content area (medium delay)
        def load_content():
            # Create placeholder for image
            image_placeholder = st.empty()
            
            # Show loading message
            with image_placeholder.container():
                st.info("⏳ 準備刺激圖片中...")
                
            return image_placeholder
            
        image_placeholder = None
        if enable_staging:
            def load_content_wrapper():
                nonlocal image_placeholder
                image_placeholder = load_content()
            loader.load_stage('content', load_content_wrapper, delay=0.2)
        
        # Stage 4: Controls (after content is ready)
        def load_controls():
            from ui.components.response_buttons import create_response_buttons
            trial_key = session_manager.get_experiment_trial() if not session_manager.is_practice_mode() else session_manager.get_practice_trials_completed()
            
            st.markdown("<div style='margin: 30px 0;'></div>", unsafe_allow_html=True)
            
            left_pressed, right_pressed = create_response_buttons(
                left_label="不清楚",
                right_label="清楚", 
                key_suffix=f"trial_{trial_key}_{'exp' if not session_manager.is_practice_mode() else 'practice'}"
            )
            
            return left_pressed, right_pressed
            
        response_data = {'left': False, 'right': False}
        
        def load_controls_wrapper():
            left, right = load_controls()
            response_data['left'] = left
            response_data['right'] = right
            
        loader.load_stage('controls', load_controls_wrapper, delay=0.3)
        
        # Finally: Load the actual image (heaviest operation last)
        trial_data = session_manager.get_mtf_trial_data()
        if trial_data and enable_staging:
            def load_final_image():
                from ui.components.image_display import display_mtf_stimulus_image
                
                image_data = trial_data.get('stimulus_image')
                mtf_value = trial_data.get('mtf_value', 0)
                
                # Clear loading message and show actual image
                if image_placeholder:
                    image_placeholder.empty()
                    
                with image_placeholder.container():
                    display_mtf_stimulus_image(
                        image_data,
                        caption=f"MTF 值: {mtf_value:.1f}" if session_manager.get_show_trial_feedback() else "",
                        staged_loading=False  # Already staged at higher level
                    )
                    
            # Add longer delay for image loading
            time.sleep(0.2)  # Additional delay for heavy image processing
            load_final_image()
            
        elif trial_data:
            # Direct loading if staging is disabled
            from ui.components.image_display import display_mtf_stimulus_image
            
            image_data = trial_data.get('stimulus_image')
            mtf_value = trial_data.get('mtf_value', 0)
            
            display_mtf_stimulus_image(
                image_data,
                caption=f"MTF 值: {mtf_value:.1f}" if session_manager.get_show_trial_feedback() else "",
                staged_loading=enable_staging
            )
        
        # Return response data for processing
        return response_data['left'], response_data['right']
        
    except Exception as e:
        logger.error(f"Error in staged loading: {e}")
        # Fallback to regular loading
        return False, False

def show_loading_progress(message: str = "載入中", steps: int = 3, step_delay: float = 0.3):
    """Show animated loading progress
    
    Args:
        message: Loading message
        steps: Number of progress steps
        step_delay: Delay between steps
    """
    try:
        progress_container = st.empty()
        
        for step in range(steps + 1):
            progress = step / steps
            dots = "." * (step % 4)
            
            progress_html = f"""
            <div style="
                text-align: center;
                padding: 20px;
                color: #666;
                font-size: 16px;
            ">
                <div style="margin-bottom: 15px;">
                    {message}{dots}
                </div>
                <div style="
                    width: 200px;
                    height: 4px;
                    background: #e9ecef;
                    border-radius: 2px;
                    margin: 0 auto;
                    overflow: hidden;
                ">
                    <div style="
                        width: {progress * 100}%;
                        height: 100%;
                        background: linear-gradient(90deg, #007bff, #28a745);
                        border-radius: 2px;
                        transition: width 0.3s ease;
                    "></div>
                </div>
                <div style="margin-top: 10px; font-size: 14px; color: #999;">
                    {int(progress * 100)}% 完成
                </div>
            </div>
            """
            
            progress_container.markdown(progress_html, unsafe_allow_html=True)
            
            if step < steps:
                time.sleep(step_delay)
        
        # Clear loading indicator
        time.sleep(0.2)
        progress_container.empty()
        
    except Exception as e:
        logger.error(f"Error showing loading progress: {e}")