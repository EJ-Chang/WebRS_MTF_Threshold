import numpy as np
import scipy.optimize as opt
import scipy.stats as stats
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class ADOOptimizer:
    """
    Adaptive Design Optimization for psychophysics experiments.
    
    This class implements ADO to optimally select stimulus values that maximize
    information gain about psychometric function parameters.
    """
    
    def __init__(self, 
                 stimulus_range: Tuple[float, float] = (0.0, 1.0),
                 n_grid_points: int = 50,
                 prior_alpha: float = 2.0,
                 prior_beta: float = 2.0,
                 prior_gamma: float = 0.02,
                 prior_lambda: float = 0.02):
        """
        Initialize ADO optimizer.
        
        Args:
            stimulus_range: Range of possible stimulus values (min, max)
            n_grid_points: Number of points for parameter grid search
            prior_alpha: Prior parameter for threshold (alpha)
            prior_beta: Prior parameter for slope (beta)
            prior_gamma: Prior parameter for guess rate (gamma)
            prior_lambda: Prior parameter for lapse rate (lambda)
        """
        self.stimulus_range = stimulus_range
        self.n_grid_points = n_grid_points
        
        # Psychometric function parameters
        # Using 4-parameter Weibull: P(x) = gamma + (1-gamma-lambda) * (1 - exp(-(x/alpha)^beta))
        self.parameter_names = ['alpha', 'beta', 'gamma', 'lambda']
        
        # Set up parameter grids for Bayesian inference (optimized for speed)
        self.alpha_grid = np.linspace(0.1, 0.9, n_grid_points)  # threshold
        self.beta_grid = np.linspace(0.5, 5.0, n_grid_points)   # slope
        self.gamma_grid = np.linspace(0.0, 0.1, 10)             # guess rate (reduced)
        self.lambda_grid = np.linspace(0.0, 0.1, 10)            # lapse rate (reduced)
        
        # Initialize prior distribution
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.prior_gamma = prior_gamma
        self.prior_lambda = prior_lambda
        
        # Initialize posterior as uniform prior
        self._initialize_posterior()
        
        # Store trial history
        self.trial_history = []
        self.response_history = []
        
    def _initialize_posterior(self):
        """Initialize posterior distribution as uniform prior."""
        # Create 4D grid for all parameter combinations
        alpha_mesh, beta_mesh, gamma_mesh, lambda_mesh = np.meshgrid(
            self.alpha_grid, self.beta_grid, self.gamma_grid, self.lambda_grid, indexing='ij'
        )
        
        # Initialize uniform posterior
        self.posterior = np.ones_like(alpha_mesh)
        
        # Apply prior constraints
        # Beta distribution priors for alpha (threshold)
        alpha_prior = stats.beta.pdf(alpha_mesh, self.prior_alpha, self.prior_beta)
        
        # Gamma distribution prior for beta (slope)
        beta_prior = stats.gamma.pdf(beta_mesh, a=2, scale=1)
        
        # Beta distribution priors for gamma and lambda (constrained to be small)
        gamma_prior = stats.beta.pdf(gamma_mesh, 1, 19)  # Favor small values
        lambda_prior = stats.beta.pdf(lambda_mesh, 1, 19)  # Favor small values
        
        # Combine priors
        self.posterior *= alpha_prior * beta_prior * gamma_prior * lambda_prior
        
        # Normalize
        self.posterior /= np.sum(self.posterior)
        
    def weibull_psychometric(self, x: np.ndarray, alpha: float, beta: float, 
                           gamma: float, lambda_param: float) -> np.ndarray:
        """
        4-parameter Weibull psychometric function.
        
        Args:
            x: Stimulus values
            alpha: Threshold parameter
            beta: Slope parameter
            gamma: Guess rate (lower asymptote)
            lambda_param: Lapse rate (affects upper asymptote)
            
        Returns:
            Probability of positive response
        """
        return gamma + (1 - gamma - lambda_param) * (1 - np.exp(-((x / alpha) ** beta)))
    
    def calculate_likelihood(self, stimulus: float, response: bool, 
                           alpha: float, beta: float, gamma: float, lambda_param: float) -> float:
        """
        Calculate likelihood of observing response given parameters.
        
        Args:
            stimulus: Stimulus value presented
            response: Observed response (True for positive, False for negative)
            alpha, beta, gamma, lambda_param: Psychometric function parameters
            
        Returns:
            Likelihood value
        """
        p_correct = self.weibull_psychometric(np.array([stimulus]), alpha, beta, gamma, lambda_param)[0]
        
        # Ensure probability is within valid range
        p_correct = np.clip(p_correct, 1e-10, 1 - 1e-10)
        
        if response:
            return p_correct
        else:
            return 1 - p_correct
    
    def update_posterior(self, stimulus: float, response: bool):
        """
        Update posterior distribution based on new observation using Bayes' rule.
        
        Args:
            stimulus: Stimulus value that was presented
            response: Observed response (True for correct/positive, False for incorrect/negative)
        """
        # Store trial data
        self.trial_history.append(stimulus)
        self.response_history.append(response)
        
        # Calculate likelihood for each parameter combination
        alpha_mesh, beta_mesh, gamma_mesh, lambda_mesh = np.meshgrid(
            self.alpha_grid, self.beta_grid, self.gamma_grid, self.lambda_grid, indexing='ij'
        )
        
        # Vectorized likelihood calculation
        likelihood = np.zeros_like(self.posterior)
        
        for i, alpha in enumerate(self.alpha_grid):
            for j, beta in enumerate(self.beta_grid):
                for k, gamma in enumerate(self.gamma_grid):
                    for l, lambda_param in enumerate(self.lambda_grid):
                        likelihood[i, j, k, l] = self.calculate_likelihood(
                            stimulus, response, alpha, beta, gamma, lambda_param
                        )
        
        # Update posterior: P(theta|data) ∝ P(data|theta) * P(theta)
        self.posterior *= likelihood
        
        # Normalize
        posterior_sum = np.sum(self.posterior)
        if posterior_sum > 0:
            self.posterior /= posterior_sum
        else:
            # If posterior becomes zero, reinitialize
            self._initialize_posterior()
    
    def calculate_expected_information_gain(self, stimulus: float) -> float:
        """
        Calculate expected information gain for a given stimulus value.
        
        Args:
            stimulus: Candidate stimulus value
            
        Returns:
            Expected information gain (mutual information)
        """
        # Current entropy
        current_entropy = -np.sum(self.posterior * np.log(self.posterior + 1e-10))
        
        # Calculate expected entropy after observing response
        alpha_mesh, beta_mesh, gamma_mesh, lambda_mesh = np.meshgrid(
            self.alpha_grid, self.beta_grid, self.gamma_grid, self.lambda_grid, indexing='ij'
        )
        
        # Calculate probability of positive response for each parameter combination
        p_positive = np.zeros_like(self.posterior)
        
        for i, alpha in enumerate(self.alpha_grid):
            for j, beta in enumerate(self.beta_grid):
                for k, gamma in enumerate(self.gamma_grid):
                    for l, lambda_param in enumerate(self.lambda_grid):
                        p_positive[i, j, k, l] = self.weibull_psychometric(
                            np.array([stimulus]), alpha, beta, gamma, lambda_param
                        )[0]
        
        # Expected probability of positive response
        p_pos_expected = np.sum(self.posterior * p_positive)
        p_neg_expected = 1 - p_pos_expected
        
        # Avoid log(0) by adding small epsilon
        p_pos_expected = np.clip(p_pos_expected, 1e-10, 1 - 1e-10)
        p_neg_expected = np.clip(p_neg_expected, 1e-10, 1 - 1e-10)
        
        # Calculate posterior entropy for each possible outcome
        entropy_pos = 0
        entropy_neg = 0
        
        if p_pos_expected > 1e-10:
            # Posterior after positive response
            posterior_pos = self.posterior * p_positive
            posterior_pos /= (np.sum(posterior_pos) + 1e-10)
            entropy_pos = -np.sum(posterior_pos * np.log(posterior_pos + 1e-10))
        
        if p_neg_expected > 1e-10:
            # Posterior after negative response
            posterior_neg = self.posterior * (1 - p_positive)
            posterior_neg /= (np.sum(posterior_neg) + 1e-10)
            entropy_neg = -np.sum(posterior_neg * np.log(posterior_neg + 1e-10))
        
        # Expected posterior entropy
        expected_entropy = p_pos_expected * entropy_pos + p_neg_expected * entropy_neg
        
        # Information gain = current entropy - expected entropy
        information_gain = current_entropy - expected_entropy
        
        return information_gain
    
    def select_optimal_stimulus(self, candidate_stimuli: Optional[np.ndarray] = None) -> float:
        """
        Select the optimal stimulus value that maximizes expected information gain.
        
        Args:
            candidate_stimuli: Array of candidate stimulus values. If None, uses uniform grid.
            
        Returns:
            Optimal stimulus value
        """
        if candidate_stimuli is None:
            candidate_stimuli = np.linspace(self.stimulus_range[0], self.stimulus_range[1], 50)
        
        # Calculate information gain for each candidate
        information_gains = []
        
        for stimulus in candidate_stimuli:
            ig = self.calculate_expected_information_gain(stimulus)
            information_gains.append(ig)
        
        information_gains = np.array(information_gains)
        
        # Select stimulus with maximum information gain
        optimal_idx = np.argmax(information_gains)
        optimal_stimulus = candidate_stimuli[optimal_idx]
        
        return optimal_stimulus
    
    def get_parameter_estimates(self) -> Dict[str, float]:
        """
        Get current parameter estimates (posterior means).
        
        Returns:
            Dictionary with parameter estimates
        """
        alpha_mesh, beta_mesh, gamma_mesh, lambda_mesh = np.meshgrid(
            self.alpha_grid, self.beta_grid, self.gamma_grid, self.lambda_grid, indexing='ij'
        )
        
        # Calculate posterior means
        alpha_estimate = np.sum(self.posterior * alpha_mesh)
        beta_estimate = np.sum(self.posterior * beta_mesh)
        gamma_estimate = np.sum(self.posterior * gamma_mesh)
        lambda_estimate = np.sum(self.posterior * lambda_mesh)
        
        return {
            'alpha': alpha_estimate,
            'beta': beta_estimate,
            'gamma': gamma_estimate,
            'lambda': lambda_estimate
        }
    
    def get_parameter_credible_intervals(self, confidence: float = 0.95) -> Dict[str, Tuple[float, float]]:
        """
        Get credible intervals for parameters.
        
        Args:
            confidence: Confidence level (e.g., 0.95 for 95% CI)
            
        Returns:
            Dictionary with parameter credible intervals
        """
        alpha_ci = (0, 1)  # Placeholder implementation
        beta_ci = (0, 5)
        gamma_ci = (0, 0.1)
        lambda_ci = (0, 0.1)
        
        # For full implementation, would need to compute marginal distributions
        # and find credible intervals
        
        return {
            'alpha': alpha_ci,
            'beta': beta_ci,
            'gamma': gamma_ci,
            'lambda': lambda_ci
        }
    
    def predict_psychometric_curve(self, x_values: np.ndarray) -> np.ndarray:
        """
        Predict psychometric curve based on current parameter estimates.
        
        Args:
            x_values: Stimulus values for prediction
            
        Returns:
            Predicted probabilities
        """
        estimates = self.get_parameter_estimates()
        
        return self.weibull_psychometric(
            x_values,
            estimates['alpha'],
            estimates['beta'],
            estimates['gamma'],
            estimates['lambda']
        )
    
    def get_entropy(self) -> float:
        """Get current posterior entropy (measure of uncertainty)."""
        return -np.sum(self.posterior * np.log(self.posterior + 1e-10))
    
    def get_trial_summary(self) -> Dict:
        """Get summary of trials conducted so far."""
        if not self.trial_history:
            return {'n_trials': 0}
        
        return {
            'n_trials': len(self.trial_history),
            'stimuli_range': (min(self.trial_history), max(self.trial_history)),
            'response_rate': np.mean(self.response_history),
            'current_entropy': self.get_entropy(),
            'parameter_estimates': self.get_parameter_estimates()
        }