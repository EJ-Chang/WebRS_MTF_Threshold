import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scipy.optimize import curve_fit
from scipy import stats
import streamlit as st
from typing import List, Dict, Tuple, Optional

class PsychometricAnalyzer:
    """
    Analyze psychophysics experiment data and generate psychometric functions.
    """
    
    def __init__(self):
        """Initialize the analyzer."""
        pass
    
    def weibull_function(self, x: np.ndarray, alpha: float, beta: float, gamma: float = 0.5, lambda_param: float = 0.02) -> np.ndarray:
        """
        Weibull psychometric function.
        
        Args:
            x: Stimulus intensity values
            alpha: Threshold parameter (50% point)
            beta: Slope parameter
            gamma: Guess rate (lower asymptote)
            lambda_param: Lapse rate (upper asymptote = 1 - lambda)
            
        Returns:
            Probability of correct response
        """
        return gamma + (1 - gamma - lambda_param) * (1 - np.exp(-((x / alpha) ** beta)))
    
    def logistic_function(self, x: np.ndarray, alpha: float, beta: float, gamma: float = 0.5, lambda_param: float = 0.02) -> np.ndarray:
        """
        Logistic psychometric function.
        
        Args:
            x: Stimulus intensity values
            alpha: Threshold parameter (50% point)
            beta: Slope parameter
            gamma: Guess rate (lower asymptote)
            lambda_param: Lapse rate
            
        Returns:
            Probability of correct response
        """
        return gamma + (1 - gamma - lambda_param) / (1 + np.exp(-beta * (x - alpha)))
    
    def calculate_psychometric_data(self, trial_data: List[Dict]) -> Dict:
        """
        Calculate psychometric function data points from trial results.
        
        Args:
            trial_data: List of trial dictionaries
            
        Returns:
            Dictionary with psychometric function data
        """
        if not trial_data:
            return {}
        
        # Filter out practice trials
        main_trials = [trial for trial in trial_data if not trial.get('is_practice', False)]
        
        if not main_trials:
            return {}
        
        # Extract stimulus differences and responses
        stimulus_diffs = []
        responses = []
        reaction_times = []
        
        for trial in main_trials:
            diff = trial.get('stimulus_difference', 0)
            is_correct = trial.get('is_correct', False)
            rt = trial.get('reaction_time', 0)
            
            stimulus_diffs.append(diff)
            responses.append(1 if is_correct else 0)
            reaction_times.append(rt)
        
        # Create DataFrame for easier analysis
        df = pd.DataFrame({
            'stimulus_diff': stimulus_diffs,
            'correct': responses,
            'reaction_time': reaction_times
        })
        
        # Group by stimulus difference and calculate proportion correct
        grouped = df.groupby('stimulus_diff').agg({
            'correct': ['count', 'sum', 'mean'],
            'reaction_time': 'mean'
        }).round(3)
        
        # Flatten column names
        grouped.columns = ['n_trials', 'n_correct', 'prop_correct', 'mean_rt']
        grouped = grouped.reset_index()
        
        return {
            'raw_data': df,
            'grouped_data': grouped,
            'stimulus_range': (min(stimulus_diffs), max(stimulus_diffs)),
            'total_trials': len(main_trials)
        }
    
    def fit_psychometric_function(self, grouped_data: pd.DataFrame, function_type: str = 'weibull') -> Dict:
        """
        Fit a psychometric function to the data.
        
        Args:
            grouped_data: Grouped trial data
            function_type: Type of function to fit ('weibull' or 'logistic')
            
        Returns:
            Dictionary with fitted parameters and goodness of fit
        """
        if len(grouped_data) < 3:
            return {'error': 'Insufficient data points for fitting'}
        
        x_data = grouped_data['stimulus_diff'].values
        y_data = grouped_data['prop_correct'].values
        n_trials = grouped_data['n_trials'].values
        
        # Choose function
        if function_type == 'logistic':
            func = self.logistic_function
            # Initial parameter guess: [alpha, beta, gamma, lambda]
            p0 = [np.median(x_data), 5.0, 0.5, 0.02]
            bounds = ([0, 0.1, 0, 0], [max(x_data)*2, 50, 0.5, 0.1])
        else:  # weibull
            func = self.weibull_function
            p0 = [np.median(x_data), 2.0, 0.5, 0.02]
            bounds = ([0, 0.5, 0, 0], [max(x_data)*2, 10, 0.5, 0.1])
        
        try:
            # Weighted fitting based on number of trials
            popt, pcov = curve_fit(func, x_data, y_data, p0=p0, bounds=bounds, 
                                 sigma=1/np.sqrt(n_trials), absolute_sigma=True)
            
            # Calculate goodness of fit
            y_pred = func(x_data, *popt)
            r_squared = 1 - np.sum((y_data - y_pred)**2) / np.sum((y_data - np.mean(y_data))**2)
            
            # Calculate parameter errors
            param_errors = np.sqrt(np.diag(pcov))
            
            # Calculate threshold at different performance levels
            threshold_75 = self.calculate_threshold(popt, func, 0.75)
            threshold_84 = self.calculate_threshold(popt, func, 0.84)
            
            return {
                'parameters': {
                    'alpha': popt[0],
                    'beta': popt[1], 
                    'gamma': popt[2],
                    'lambda': popt[3]
                },
                'parameter_errors': {
                    'alpha_err': param_errors[0],
                    'beta_err': param_errors[1],
                    'gamma_err': param_errors[2],
                    'lambda_err': param_errors[3]
                },
                'goodness_of_fit': {
                    'r_squared': r_squared,
                    'rmse': np.sqrt(np.mean((y_data - y_pred)**2))
                },
                'thresholds': {
                    'threshold_75': threshold_75,
                    'threshold_84': threshold_84
                },
                'function_type': function_type
            }
            
        except Exception as e:
            return {'error': f'Fitting failed: {str(e)}'}
    
    def calculate_threshold(self, params: List[float], func, target_performance: float = 0.75) -> float:
        """
        Calculate threshold for a given performance level.
        
        Args:
            params: Fitted function parameters
            func: Psychometric function
            target_performance: Target performance level (e.g., 0.75 for 75%)
            
        Returns:
            Threshold value
        """
        # Use numerical search to find threshold
        x_range = np.linspace(0.001, 1.0, 1000)
        y_vals = func(x_range, *params)
        
        # Find closest point to target performance
        closest_idx = np.argmin(np.abs(y_vals - target_performance))
        return x_range[closest_idx]
    
    def create_psychometric_plot(self, psych_data: Dict, fit_results: Dict) -> go.Figure:
        """
        Create an interactive psychometric function plot.
        
        Args:
            psych_data: Psychometric data dictionary
            fit_results: Fitted function results
            
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        grouped_data = psych_data['grouped_data']
        
        # Add data points
        fig.add_trace(go.Scatter(
            x=grouped_data['stimulus_diff'],
            y=grouped_data['prop_correct'],
            mode='markers',
            marker=dict(
                size=grouped_data['n_trials'] * 3,  # Size proportional to n trials
                color='blue',
                line=dict(color='darkblue', width=1),
                opacity=0.7
            ),
            name='Data',
            text=[f'Trials: {n}<br>Correct: {int(n*p)}/{int(n)}<br>RT: {rt:.2f}s' 
                  for n, p, rt in zip(grouped_data['n_trials'], 
                                    grouped_data['prop_correct'],
                                    grouped_data['mean_rt'])],
            hovertemplate='%{text}<br>Stimulus Diff: %{x:.3f}<br>Accuracy: %{y:.1%}<extra></extra>'
        ))
        
        # Add fitted curve if available
        if 'parameters' in fit_results:
            x_smooth = np.linspace(0, max(grouped_data['stimulus_diff']) * 1.2, 100)
            
            if fit_results['function_type'] == 'logistic':
                y_smooth = self.logistic_function(x_smooth, **fit_results['parameters'])
            else:
                y_smooth = self.weibull_function(x_smooth, **fit_results['parameters'])
            
            fig.add_trace(go.Scatter(
                x=x_smooth,
                y=y_smooth,
                mode='lines',
                line=dict(color='red', width=2),
                name=f'{fit_results["function_type"].capitalize()} Fit',
                hovertemplate='Stimulus Diff: %{x:.3f}<br>Predicted Accuracy: %{y:.1%}<extra></extra>'
            ))
            
            # Add threshold lines
            if 'thresholds' in fit_results:
                threshold_75 = fit_results['thresholds']['threshold_75']
                
                # Vertical line at 75% threshold
                fig.add_vline(
                    x=threshold_75,
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"75% Threshold: {threshold_75:.3f}"
                )
                
                # Horizontal line at 75%
                fig.add_hline(
                    y=0.75,
                    line_dash="dash", 
                    line_color="green",
                    annotation_text="75% Performance"
                )
        
        # Update layout
        fig.update_layout(
            title='Psychometric Function',
            xaxis_title='Stimulus Difference',
            yaxis_title='Proportion Correct',
            yaxis=dict(range=[0.4, 1.0], tickformat='.0%'),
            xaxis=dict(range=[0, max(grouped_data['stimulus_diff']) * 1.1]),
            width=800,
            height=500,
            showlegend=True,
            hovermode='closest'
        )
        
        return fig
    
    def generate_analysis_summary(self, psych_data: Dict, fit_results: Dict) -> str:
        """
        Generate a text summary of the psychometric analysis.
        
        Args:
            psych_data: Psychometric data dictionary
            fit_results: Fitted function results
            
        Returns:
            Formatted summary string
        """
        summary = []
        summary.append("PSYCHOMETRIC FUNCTION ANALYSIS")
        summary.append("=" * 40)
        summary.append("")
        
        # Basic statistics
        grouped_data = psych_data['grouped_data']
        total_trials = psych_data['total_trials']
        
        summary.append(f"Total trials analyzed: {total_trials}")
        summary.append(f"Unique stimulus differences: {len(grouped_data)}")
        summary.append(f"Stimulus range: {psych_data['stimulus_range'][0]:.3f} - {psych_data['stimulus_range'][1]:.3f}")
        summary.append("")
        
        # Overall performance
        overall_accuracy = grouped_data['prop_correct'].mean()
        summary.append(f"Overall accuracy: {overall_accuracy:.1%}")
        summary.append("")
        
        # Fitted function results
        if 'parameters' in fit_results:
            params = fit_results['parameters']
            param_errs = fit_results['parameter_errors']
            
            summary.append(f"FITTED {fit_results['function_type'].upper()} FUNCTION:")
            summary.append(f"  Threshold (α): {params['alpha']:.4f} ± {param_errs['alpha_err']:.4f}")
            summary.append(f"  Slope (β): {params['beta']:.2f} ± {param_errs['beta_err']:.2f}")
            summary.append(f"  Guess rate (γ): {params['gamma']:.3f} ± {param_errs['gamma_err']:.3f}")
            summary.append(f"  Lapse rate (λ): {params['lambda']:.3f} ± {param_errs['lambda_err']:.3f}")
            summary.append("")
            
            # Goodness of fit
            gof = fit_results['goodness_of_fit']
            summary.append(f"GOODNESS OF FIT:")
            summary.append(f"  R²: {gof['r_squared']:.3f}")
            summary.append(f"  RMSE: {gof['rmse']:.3f}")
            summary.append("")
            
            # Thresholds
            if 'thresholds' in fit_results:
                thresholds = fit_results['thresholds']
                summary.append(f"DISCRIMINATION THRESHOLDS:")
                summary.append(f"  75% threshold: {thresholds['threshold_75']:.4f}")
                summary.append(f"  84% threshold: {thresholds['threshold_84']:.4f}")
        
        elif 'error' in fit_results:
            summary.append(f"FITTING ERROR: {fit_results['error']}")
        
        return "\n".join(summary)