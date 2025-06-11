"""
MTF Experiment Manager for Streamlit Web Interface
Integrates MTF ADO testing into the existing web framework
"""

import numpy as np
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import base64
from io import BytesIO
from PIL import Image
import cv2

# Import the ADO and MTF utilities with fallback handling
try:
    from experiments.ado_utils import ADOEngine
    from experiments.mtf_utils import apply_mtf_to_image, load_and_prepare_image
    MTF_UTILS_AVAILABLE = True
except ImportError as e:
    print(f"MTF utilities not available: {e}")
    MTF_UTILS_AVAILABLE = False
    
    # Fallback implementations for web interface
    def apply_mtf_to_image(image, mtf_percent):
        """Fallback MTF implementation using simple Gaussian blur"""
        import cv2
        # Simple approximation: lower MTF = more blur
        sigma = (100 - mtf_percent) / 20.0  # Convert MTF% to blur amount
        return cv2.GaussianBlur(image, (0, 0), sigmaX=sigma, sigmaY=sigma)
    
    def load_and_prepare_image(path, use_right_half=True):
        """Fallback image loading"""
        import cv2
        img = cv2.imread(path)
        if img is not None:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if use_right_half:
                width = img_rgb.shape[1]
                mid_point = width // 2
                img_rgb = img_rgb[:, mid_point:]
            return img_rgb
        return None
    
    # Simple ADO fallback
    class ADOEngine:
        def __init__(self, **kwargs):
            self.design_space = kwargs.get('design_space', np.arange(10, 90, 10))
            self.trial_history = []
            self.response_history = []
            
        def get_optimal_design(self):
            # Simple adaptive strategy: start high, move toward threshold
            if len(self.trial_history) == 0:
                return 70.0  # Start with high MTF
            
            # Simple 1-up-1-down strategy
            last_response = self.response_history[-1] if self.response_history else 1
            last_mtf = self.trial_history[-1] if self.trial_history else 70.0
            
            if last_response == 1:  # Clear response, make it harder
                return max(10.0, last_mtf - 10.0)
            else:  # Not clear, make it easier
                return min(90.0, last_mtf + 10.0)
        
        def update_posterior(self, mtf, response):
            self.trial_history.append(mtf)
            self.response_history.append(response)
        
        def get_parameter_estimates(self):
            if len(self.trial_history) < 3:
                return {
                    'threshold_mean': 50.0,
                    'threshold_sd': 20.0,
                    'slope_mean': 1.0,
                    'slope_sd': 0.5
                }
            
            # Estimate threshold as average of reversal points
            responses = np.array(self.response_history)
            if len(responses) > 2:
                threshold_est = np.mean(self.trial_history[-5:]) if len(self.trial_history) >= 5 else np.mean(self.trial_history)
                uncertainty = np.std(self.trial_history[-5:]) if len(self.trial_history) >= 5 else 10.0
            else:
                threshold_est = 50.0
                uncertainty = 15.0
                
            return {
                'threshold_mean': threshold_est,
                'threshold_sd': uncertainty,
                'slope_mean': 1.0,
                'slope_sd': 0.3
            }

class MTFExperimentManager:
    """Manages MTF ADO experiment for web interface"""
    
    def __init__(self, 
                 max_trials: int = 50,
                 min_trials: int = 15,
                 convergence_threshold: float = 0.15,
                 participant_id: str = "",
                 base_image_path: str = "stimuli_preparation/stimuli_img.png"):
        """
        Initialize MTF experiment manager
        
        Args:
            max_trials: Maximum number of trials
            min_trials: Minimum trials before convergence check
            convergence_threshold: Convergence criterion for threshold SD
            participant_id: Participant identifier
            base_image_path: Path to base stimulus image
        """
        self.max_trials = max_trials
        self.min_trials = min_trials
        self.convergence_threshold = convergence_threshold
        self.participant_id = participant_id
        self.base_image_path = base_image_path
        
        # Trial data storage
        self.trial_data = []
        self.current_trial = 0
        self.converged = False
        
        # Initialize ADO engine
        self.ado_engine = None
        self.base_image = None
        
        # Load base image
        self._load_base_image()
        self._initialize_ado_engine()
    
    def _load_base_image(self):
        """Load and prepare the base stimulus image"""
        try:
            if os.path.exists(self.base_image_path):
                self.base_image = load_and_prepare_image(self.base_image_path, use_right_half=True)
                print(f"Base image loaded: {self.base_image.shape}")
            else:
                print(f"Base image not found: {self.base_image_path}")
                # Create a simple test pattern as fallback
                self.base_image = self._create_test_pattern()
        except Exception as e:
            print(f"Error loading base image: {e}")
            self.base_image = self._create_test_pattern()
    
    def _create_test_pattern(self) -> np.ndarray:
        """Create a test pattern if base image is not available"""
        # Create a simple Gabor-like pattern for testing
        height, width = 400, 400
        y, x = np.ogrid[:height, :width]
        
        # Create sinusoidal grating
        frequency = 0.1
        pattern = np.sin(2 * np.pi * frequency * x) * np.cos(2 * np.pi * frequency * y)
        
        # Normalize to 0-255 range
        pattern = ((pattern + 1) * 127.5).astype(np.uint8)
        
        # Convert to RGB
        rgb_pattern = np.stack([pattern, pattern, pattern], axis=-1)
        
        return rgb_pattern
    
    def _initialize_ado_engine(self):
        """Initialize the ADO engine for MTF testing"""
        try:
            self.ado_engine = ADOEngine(
                design_space=np.arange(10, 90, 1),  # MTF values from 10% to 89%
                threshold_range=(5, 95),
                slope_range=(0.05, 5.0),
                threshold_points=31,
                slope_points=21
            )
            print("ADO engine initialized successfully")
        except Exception as e:
            print(f"Failed to initialize ADO engine: {e}")
            self.ado_engine = None
    
    def generate_stimulus_image(self, mtf_value: float) -> str:
        """
        Generate stimulus image with specified MTF value
        Returns base64 encoded image for web display
        """
        try:
            # Apply MTF to base image
            img_mtf = apply_mtf_to_image(self.base_image, mtf_value)
            
            # Convert to PIL Image
            img_pil = Image.fromarray(img_mtf)
            
            # Convert to base64 for web display
            buffer = BytesIO()
            img_pil.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Error generating stimulus: {e}")
            return None
    
    def get_next_trial(self) -> Optional[Dict]:
        """Get the next trial parameters using ADO"""
        if self.current_trial >= self.max_trials or self.converged:
            return None
        
        if self.ado_engine is None:
            # Fallback: random MTF selection
            mtf_value = float(np.random.choice(np.arange(10, 90, 10)))
        else:
            try:
                mtf_value = self.ado_engine.get_optimal_design()
            except Exception as e:
                print(f"ADO error: {e}")
                mtf_value = float(np.random.choice(np.arange(10, 90, 10)))
        
        self.current_trial += 1
        
        # Generate stimulus image
        stimulus_image = self.generate_stimulus_image(mtf_value)
        
        trial_data = {
            'trial_number': self.current_trial,
            'mtf_value': mtf_value,
            'stimulus_image': stimulus_image,
            'timestamp': datetime.now().isoformat()
        }
        
        return trial_data
    
    def record_response(self, trial_data: Dict, response: bool, reaction_time: float):
        """
        Record participant response and update ADO
        
        Args:
            trial_data: Current trial information
            response: True for "clear", False for "not clear"
            reaction_time: Response time in seconds
        """
        # Convert response to int (1 for clear, 0 for not clear)
        response_value = 1 if response else 0
        
        # Update ADO engine
        if self.ado_engine:
            try:
                self.ado_engine.update_posterior(trial_data['mtf_value'], response_value)
                estimates = self.ado_engine.get_parameter_estimates()
                
                # Check convergence
                if self.current_trial >= self.min_trials:
                    self.converged = estimates['threshold_sd'] < self.convergence_threshold
                
            except Exception as e:
                print(f"ADO update error: {e}")
                estimates = {
                    'threshold_mean': np.nan,
                    'threshold_sd': np.nan,
                    'slope_mean': np.nan,
                    'slope_sd': np.nan
                }
        else:
            estimates = {
                'threshold_mean': np.nan,
                'threshold_sd': np.nan,
                'slope_mean': np.nan,
                'slope_sd': np.nan
            }
        
        # Store trial result
        trial_result = {
            **trial_data,
            'response': response_value,
            'response_text': 'clear' if response else 'not_clear',
            'reaction_time': reaction_time,
            'threshold_mean': estimates['threshold_mean'],
            'threshold_sd': estimates['threshold_sd'],
            'slope_mean': estimates['slope_mean'],
            'slope_sd': estimates['slope_sd'],
            'converged': self.converged
        }
        
        self.trial_data.append(trial_result)
        
        return trial_result
    
    def get_current_estimates(self) -> Dict:
        """Get current parameter estimates from ADO"""
        if self.ado_engine and len(self.trial_data) > 0:
            try:
                return self.ado_engine.get_parameter_estimates()
            except:
                pass
        
        return {
            'threshold_mean': np.nan,
            'threshold_sd': np.nan,
            'slope_mean': np.nan,
            'slope_sd': np.nan
        }
    
    def is_experiment_complete(self) -> bool:
        """Check if experiment should end"""
        return (self.current_trial >= self.max_trials or 
                (self.converged and self.current_trial >= self.min_trials))
    
    def get_experiment_summary(self) -> Dict:
        """Get experiment summary statistics"""
        if not self.trial_data:
            return {}
        
        # Calculate basic statistics
        total_trials = len(self.trial_data)
        clear_responses = sum(1 for trial in self.trial_data if trial['response'] == 1)
        accuracy_rate = clear_responses / total_trials if total_trials > 0 else 0
        
        reaction_times = [trial['reaction_time'] for trial in self.trial_data]
        avg_rt = np.mean(reaction_times) if reaction_times else 0
        
        # Get final estimates
        final_estimates = self.get_current_estimates()
        
        return {
            'total_trials': total_trials,
            'clear_responses': clear_responses,
            'accuracy_rate': accuracy_rate,
            'average_reaction_time': avg_rt,
            'converged': self.converged,
            'final_threshold': final_estimates.get('threshold_mean', np.nan),
            'threshold_uncertainty': final_estimates.get('threshold_sd', np.nan),
            'participant_id': self.participant_id
        }
    
    def export_data(self) -> List[Dict]:
        """Export trial data for analysis"""
        return self.trial_data.copy()