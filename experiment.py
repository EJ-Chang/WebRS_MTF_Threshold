import random
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from ado_optimizer import ADOOptimizer

class ExperimentManager:
    """Manages the flow and logic of the 2AFC psychophysics experiment"""
    
    def __init__(self, num_trials: int = 30, num_practice_trials: int = 5, 
                 stimulus_duration: float = 2.0, inter_trial_interval: float = 1.0,
                 participant_id: str = "", use_ado: bool = True):
        """
        Initialize the experiment manager
        
        Args:
            num_trials: Number of main experiment trials
            num_practice_trials: Number of practice trials
            stimulus_duration: Duration to show stimuli (seconds)
            inter_trial_interval: Pause between trials (seconds)
            participant_id: Unique identifier for participant
            use_ado: Whether to use Adaptive Design Optimization
        """
        self.num_trials = num_trials
        self.num_practice_trials = num_practice_trials
        self.stimulus_duration = stimulus_duration
        self.inter_trial_interval = inter_trial_interval
        self.participant_id = participant_id
        self.use_ado = use_ado
        
        # Trial management
        self.current_trial = 0
        self.current_practice_trial = 0
        self.practice_completed = False
        self.experiment_completed = False
        
        # Data storage
        self.trial_data: List[Dict] = []
        self.practice_data: List[Dict] = []
        
        # ADO optimizer for adaptive stimulus selection
        if use_ado:
            self.ado_optimizer = ADOOptimizer(
                stimulus_range=(0.0, 1.0),
                n_grid_points=30,  # Reduced for faster computation
                prior_alpha=2.0,
                prior_beta=2.0
            )
        else:
            self.ado_optimizer = None
        
        # Generate practice trials (always random for practice)
        self.practice_trials = self._generate_practice_trials(num_practice_trials)
        
        # For ADO, trials are generated adaptively
        if not use_ado:
            self.main_trials = self._generate_trial_sequence(num_trials)
        else:
            self.main_trials = []  # Will be generated adaptively
        
        # Experiment metadata
        self.experiment_start_time = None
        self.experiment_end_time = None
    
    def _generate_practice_trials(self, num_trials: int) -> List[Dict]:
        """
        Generate practice trials with random stimulus selection
        
        Args:
            num_trials: Number of practice trials to generate
            
        Returns:
            List of trial dictionaries with stimulus parameters
        """
        trials = []
        
        for i in range(num_trials):
            # Generate stimulus intensities (0.1 to 0.9 for visual contrast)
            left_intensity = round(random.uniform(0.2, 0.8), 2)
            right_intensity = round(random.uniform(0.2, 0.8), 2)
            
            # Ensure some difference between stimuli
            while abs(left_intensity - right_intensity) < 0.1:
                right_intensity = round(random.uniform(0.2, 0.8), 2)
            
            trial = {
                'trial_number': i + 1,
                'left_stimulus': left_intensity,
                'right_stimulus': right_intensity,
                'correct_response': 'left' if left_intensity > right_intensity else 'right',
                'stimulus_difference': abs(left_intensity - right_intensity),
                'is_practice': True
            }
            
            trials.append(trial)
        
        # Randomize trial order
        random.shuffle(trials)
        
        # Re-assign trial numbers after shuffling
        for i, trial in enumerate(trials):
            trial['trial_number'] = i + 1
        
        return trials

    def _generate_trial_sequence(self, num_trials: int, is_practice: bool = False) -> List[Dict]:
        """
        Generate a randomized sequence of trials (for non-ADO experiments)
        
        Args:
            num_trials: Number of trials to generate
            is_practice: Whether these are practice trials
            
        Returns:
            List of trial dictionaries with stimulus parameters
        """
        trials = []
        
        for i in range(num_trials):
            # Generate stimulus intensities (0.1 to 0.9 for visual contrast)
            left_intensity = round(random.uniform(0.2, 0.8), 2)
            right_intensity = round(random.uniform(0.2, 0.8), 2)
            
            # Ensure some difference between stimuli
            while abs(left_intensity - right_intensity) < 0.1:
                right_intensity = round(random.uniform(0.2, 0.8), 2)
            
            trial = {
                'trial_number': i + 1,
                'left_stimulus': left_intensity,
                'right_stimulus': right_intensity,
                'correct_response': 'left' if left_intensity > right_intensity else 'right',
                'stimulus_difference': abs(left_intensity - right_intensity),
                'is_practice': is_practice
            }
            
            trials.append(trial)
        
        # Randomize trial order
        random.shuffle(trials)
        
        # Re-assign trial numbers after shuffling
        for i, trial in enumerate(trials):
            trial['trial_number'] = i + 1
        
        return trials

    def _generate_ado_trial(self) -> Dict:
        """
        Generate next trial using ADO optimization
        
        Returns:
            Trial dictionary with ADO-selected stimulus parameters
        """
        if not self.ado_optimizer:
            raise ValueError("ADO optimizer not initialized")
        
        # Get optimal stimulus value from ADO
        optimal_stimulus = self.ado_optimizer.select_optimal_stimulus()
        
        # For 2AFC, we need to decide how to present the stimuli
        # Option 1: Use optimal stimulus as the target, random as reference
        # Option 2: Use optimal stimulus as difference between stimuli
        
        # Using option 2: optimal_stimulus represents the stimulus difference
        reference_intensity = 0.5  # Fixed reference
        target_intensity = reference_intensity + optimal_stimulus
        
        # Ensure target is within valid range
        target_intensity = np.clip(target_intensity, 0.0, 1.0)
        
        # Randomly assign which side gets the target
        if random.random() < 0.5:
            left_stimulus = target_intensity
            right_stimulus = reference_intensity
            correct_response = 'left'
        else:
            left_stimulus = reference_intensity
            right_stimulus = target_intensity
            correct_response = 'right'
        
        trial = {
            'trial_number': self.current_trial + 1,
            'left_stimulus': round(left_stimulus, 3),
            'right_stimulus': round(right_stimulus, 3),
            'correct_response': correct_response,
            'stimulus_difference': abs(left_stimulus - right_stimulus),
            'ado_stimulus_value': optimal_stimulus,
            'reference_intensity': reference_intensity,
            'is_practice': False
        }
        
        return trial
    
    def start_practice(self):
        """Initialize practice session"""
        self.current_practice_trial = 0
        self.practice_completed = False
        self.practice_data = []
    
    def start_main_experiment(self):
        """Initialize main experiment session"""
        self.current_trial = 0
        self.experiment_completed = False
        self.trial_data = []
        self.experiment_start_time = datetime.now()
    
    def get_current_trial(self, is_practice: bool = False) -> Optional[Dict]:
        """
        Get the current trial data
        
        Args:
            is_practice: Whether to get practice or main trial
            
        Returns:
            Dictionary with current trial parameters or None if no more trials
        """
        if is_practice:
            if self.current_practice_trial >= len(self.practice_trials):
                return None
            return self.practice_trials[self.current_practice_trial]
        else:
            # Check if experiment is completed
            if self.current_trial >= self.num_trials:
                return None
            
            if self.use_ado:
                # Generate trial adaptively using ADO
                return self._generate_ado_trial()
            else:
                # Use pre-generated trials
                if self.current_trial >= len(self.main_trials):
                    return None
                return self.main_trials[self.current_trial]
    
    def record_trial(self, trial_result: Dict, is_practice: bool = False):
        """
        Record the result of a completed trial
        
        Args:
            trial_result: Dictionary containing trial data and response
            is_practice: Whether this was a practice trial
        """
        # Add experiment metadata
        trial_result['participant_id'] = self.participant_id
        trial_result['experiment_timestamp'] = datetime.now().isoformat()
        
        # For practice trials, determine correctness from stimulus values
        if is_practice:
            left_stimulus = trial_result.get('left_stimulus', 0)
            right_stimulus = trial_result.get('right_stimulus', 0)
            correct_response = 'left' if left_stimulus > right_stimulus else 'right'
            trial_result['correct_response'] = correct_response
            trial_result['is_correct'] = trial_result['response'] == correct_response
            trial_result['stimulus_difference'] = abs(left_stimulus - right_stimulus)
            
            self.practice_data.append(trial_result)
            self.current_practice_trial += 1
            
            # Check if practice is completed
            if self.current_practice_trial >= self.num_practice_trials:
                self.practice_completed = True
        else:
            # For main experiment trials
            left_stimulus = trial_result.get('left_stimulus', 0)
            right_stimulus = trial_result.get('right_stimulus', 0)
            correct_response = 'left' if left_stimulus > right_stimulus else 'right'
            is_correct = trial_result['response'] == correct_response
            
            trial_result['correct_response'] = correct_response
            trial_result['is_correct'] = is_correct
            trial_result['stimulus_difference'] = abs(left_stimulus - right_stimulus)
            
            # Update ADO optimizer with the response
            if self.use_ado and self.ado_optimizer:
                # Get the stimulus value that was used for ADO
                ado_stimulus_value = trial_result.get('ado_stimulus_value', 
                                                    trial_result['stimulus_difference'])
                
                # Update ADO with stimulus and correctness
                self.ado_optimizer.update_posterior(ado_stimulus_value, is_correct)
            
            self.trial_data.append(trial_result)
            self.current_trial += 1
            
            # Check if experiment is completed
            if self.current_trial >= self.num_trials:
                self.experiment_completed = True
                self.experiment_end_time = datetime.now()
    
    def get_experiment_summary(self) -> Dict:
        """
        Generate a summary of the experiment results
        
        Returns:
            Dictionary with experiment summary statistics
        """
        if not self.trial_data:
            return {}
        
        # Calculate basic statistics
        total_trials = len(self.trial_data)
        correct_responses = sum(1 for trial in self.trial_data if trial.get('is_correct', False))
        accuracy = correct_responses / total_trials if total_trials > 0 else 0
        
        reaction_times = [trial['reaction_time'] for trial in self.trial_data]
        avg_reaction_time = np.mean(reaction_times) if reaction_times else 0
        median_reaction_time = np.median(reaction_times) if reaction_times else 0
        
        # Calculate performance by stimulus difference
        difficulty_analysis = {}
        for trial in self.trial_data:
            diff = trial.get('stimulus_difference', 0)
            diff_category = f"{diff:.1f}"
            
            if diff_category not in difficulty_analysis:
                difficulty_analysis[diff_category] = {'correct': 0, 'total': 0}
            
            difficulty_analysis[diff_category]['total'] += 1
            if trial.get('is_correct', False):
                difficulty_analysis[diff_category]['correct'] += 1
        
        summary = {
            'participant_id': self.participant_id,
            'total_trials': total_trials,
            'accuracy': accuracy,
            'correct_responses': correct_responses,
            'avg_reaction_time': avg_reaction_time,
            'median_reaction_time': median_reaction_time,
            'min_reaction_time': min(reaction_times) if reaction_times else 0,
            'max_reaction_time': max(reaction_times) if reaction_times else 0,
            'experiment_start_time': self.experiment_start_time.isoformat() if self.experiment_start_time else None,
            'experiment_end_time': self.experiment_end_time.isoformat() if self.experiment_end_time else None,
            'difficulty_analysis': difficulty_analysis,
            'ado_enabled': self.use_ado
        }
        
        # Add ADO-specific information if ADO was used
        if self.use_ado and self.ado_optimizer:
            ado_summary = self.ado_optimizer.get_trial_summary()
            parameter_estimates = self.ado_optimizer.get_parameter_estimates()
            
            summary['ado_info'] = {
                'parameter_estimates': parameter_estimates,
                'final_entropy': ado_summary.get('current_entropy', 0),
                'stimuli_range': ado_summary.get('stimuli_range', (0, 1)),
                'n_ado_trials': ado_summary.get('n_trials', 0)
            }
        
        return summary
    
    def get_all_data(self) -> Dict:
        """
        Get all experiment data including trials and summary
        
        Returns:
            Dictionary with complete experiment data
        """
        return {
            'participant_info': {
                'participant_id': self.participant_id,
                'num_trials': self.num_trials,
                'num_practice_trials': self.num_practice_trials,
                'stimulus_duration': self.stimulus_duration,
                'inter_trial_interval': self.inter_trial_interval
            },
            'practice_data': self.practice_data,
            'trial_data': self.trial_data,
            'summary': self.get_experiment_summary()
        }
    
    def get_ado_parameter_estimates(self) -> Dict:
        """Get current ADO parameter estimates."""
        if self.use_ado and self.ado_optimizer:
            return self.ado_optimizer.get_parameter_estimates()
        return {}
    
    def get_ado_entropy(self) -> float:
        """Get current ADO posterior entropy."""
        if self.use_ado and self.ado_optimizer:
            return self.ado_optimizer.get_entropy()
        return 0.0
    
    def predict_psychometric_curve(self, x_values: np.ndarray) -> np.ndarray:
        """Predict psychometric curve based on current estimates."""
        if self.use_ado and self.ado_optimizer:
            return self.ado_optimizer.predict_psychometric_curve(x_values)
        return np.zeros_like(x_values)
