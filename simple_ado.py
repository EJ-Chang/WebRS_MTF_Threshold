import numpy as np
from typing import List, Dict, Tuple
import random

class SimpleADO:
    """
    Simplified Adaptive Design Optimization for 2AFC psychophysics.
    Uses a more practical approach focused on threshold estimation.
    """
    
    def __init__(self, initial_difference: float = 0.2, target_accuracy: float = 0.75):
        """
        Initialize simple ADO.
        
        Args:
            initial_difference: Starting stimulus difference
            target_accuracy: Target accuracy level (e.g., 0.75 for 75% threshold)
        """
        self.current_difference = initial_difference
        self.target_accuracy = target_accuracy
        self.min_difference = 0.01  # Minimum detectable difference
        self.max_difference = 0.8   # Maximum difference
        
        # Track performance
        self.trial_history: List[Dict] = []
        self.window_size = 5  # Number of recent trials to consider
        
        # Adaptive parameters
        self.step_size = 0.05  # How much to change difficulty
        self.convergence_threshold = 0.02  # When to consider converged
        
    def select_stimulus_difference(self) -> float:
        """
        Select the next stimulus difference based on recent performance.
        
        Returns:
            Optimal stimulus difference for next trial
        """
        if len(self.trial_history) < 3:
            # Start with initial differences for first few trials
            initial_diffs = [0.3, 0.15, 0.1]
            if len(self.trial_history) < len(initial_diffs):
                return initial_diffs[len(self.trial_history)]
        
        # Calculate recent accuracy
        recent_trials = self.trial_history[-self.window_size:]
        if not recent_trials:
            return self.current_difference
            
        recent_accuracy = sum(trial['is_correct'] for trial in recent_trials) / len(recent_trials)
        
        # Adaptive rule: adjust difficulty based on performance
        if recent_accuracy > self.target_accuracy + 0.1:
            # Too easy - make harder (smaller difference)
            new_difference = self.current_difference * 0.8
        elif recent_accuracy < self.target_accuracy - 0.1:
            # Too hard - make easier (larger difference)
            new_difference = self.current_difference * 1.3
        else:
            # Near target - small adjustments
            if recent_accuracy > self.target_accuracy:
                new_difference = self.current_difference * 0.95
            else:
                new_difference = self.current_difference * 1.05
        
        # Ensure within bounds
        new_difference = np.clip(new_difference, self.min_difference, self.max_difference)
        
        # Add small random variation to avoid getting stuck
        variation = random.uniform(0.9, 1.1)
        new_difference *= variation
        new_difference = np.clip(new_difference, self.min_difference, self.max_difference)
        
        self.current_difference = new_difference
        return new_difference
    
    def update_with_response(self, stimulus_difference: float, is_correct: bool, reaction_time: float = 1.0):
        """
        Update the algorithm with participant response.
        
        Args:
            stimulus_difference: The stimulus difference that was presented
            is_correct: Whether the response was correct
            reaction_time: Response time (optional)
        """
        trial_data = {
            'stimulus_difference': stimulus_difference,
            'is_correct': is_correct,
            'reaction_time': reaction_time,
            'trial_number': len(self.trial_history) + 1
        }
        
        self.trial_history.append(trial_data)
    
    def get_threshold_estimate(self) -> float:
        """
        Estimate the current threshold (75% correct point).
        
        Returns:
            Estimated threshold
        """
        if len(self.trial_history) < 5:
            return self.current_difference
        
        # Simple estimation: average of recent stimulus differences
        recent_trials = self.trial_history[-10:]
        recent_diffs = [trial['stimulus_difference'] for trial in recent_trials]
        return np.mean(recent_diffs)
    
    def get_performance_summary(self) -> Dict:
        """
        Get summary of current performance and algorithm state.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.trial_history:
            return {'n_trials': 0}
        
        recent_trials = self.trial_history[-self.window_size:]
        recent_accuracy = sum(trial['is_correct'] for trial in recent_trials) / len(recent_trials)
        
        all_diffs = [trial['stimulus_difference'] for trial in self.trial_history]
        
        return {
            'n_trials': len(self.trial_history),
            'recent_accuracy': recent_accuracy,
            'current_difference': self.current_difference,
            'threshold_estimate': self.get_threshold_estimate(),
            'min_difference_tested': min(all_diffs) if all_diffs else 0,
            'max_difference_tested': max(all_diffs) if all_diffs else 0,
            'converged': self.is_converged()
        }
    
    def is_converged(self) -> bool:
        """
        Check if the algorithm has converged.
        
        Returns:
            True if converged
        """
        if len(self.trial_history) < 10:
            return False
        
        # Check if recent differences are stable
        recent_diffs = [trial['stimulus_difference'] for trial in self.trial_history[-5:]]
        diff_std = np.std(recent_diffs)
        
        return diff_std < self.convergence_threshold