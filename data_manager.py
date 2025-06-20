import pandas as pd
import csv
import json
from datetime import datetime
from typing import List, Dict, Optional
import io

class DataManager:
    """Handles data storage, export, and analysis for the 2AFC experiment"""
    
    def __init__(self):
        """Initialize the data manager"""
        self.data_cache = {}
    
    def export_to_csv(self, trial_data: List[Dict], participant_id: str) -> str:
        """
        Export trial data to CSV format
        
        Args:
            trial_data: List of trial result dictionaries
            participant_id: Participant identifier
            
        Returns:
            CSV data as string
        """
        if not trial_data:
            return "No data to export"
        
        # Create DataFrame from trial data
        df = pd.DataFrame(trial_data)
        
        # Ensure consistent column order
        desired_columns = [
            'participant_id',
            'trial_number',
            'is_practice',
            'left_stimulus',
            'right_stimulus',
            'stimulus_difference',
            'response',
            'correct_response',
            'is_correct',
            'reaction_time',
            'timestamp',
            'experiment_timestamp'
        ]
        
        # Reorder columns (only include those that exist)
        existing_columns = [col for col in desired_columns if col in df.columns]
        df = df[existing_columns]
        
        # Convert to CSV string
        output = io.StringIO()
        df.to_csv(output, index=False)
        csv_string = output.getvalue()
        output.close()
        
        return csv_string
    
    def export_to_json(self, experiment_data: Dict) -> str:
        """
        Export complete experiment data to JSON format
        
        Args:
            experiment_data: Complete experiment data dictionary
            
        Returns:
            JSON data as string
        """
        return json.dumps(experiment_data, indent=2, default=str)
    
    def calculate_psychometric_function(self, trial_data: List[Dict]) -> Dict:
        """
        Calculate psychometric function data points
        
        Args:
            trial_data: List of trial result dictionaries
            
        Returns:
            Dictionary with psychometric function data
        """
        if not trial_data:
            return {}
        
        # Group trials by stimulus difference
        difference_groups = {}
        
        for trial in trial_data:
            if trial.get('is_practice', False):
                continue  # Skip practice trials
            
            diff = trial.get('stimulus_difference', 0)
            # Round to nearest 0.1 for grouping
            diff_rounded = round(diff, 1)
            
            if diff_rounded not in difference_groups:
                difference_groups[diff_rounded] = {
                    'trials': [],
                    'correct': 0,
                    'total': 0,
                    'reaction_times': []
                }
            
            difference_groups[diff_rounded]['trials'].append(trial)
            difference_groups[diff_rounded]['total'] += 1
            difference_groups[diff_rounded]['reaction_times'].append(trial.get('reaction_time', 0))
            
            if trial.get('is_correct', False):
                difference_groups[diff_rounded]['correct'] += 1
        
        # Calculate performance metrics for each difficulty level
        psychometric_data = {}
        for diff, data in difference_groups.items():
            if data['total'] > 0:
                psychometric_data[diff] = {
                    'stimulus_difference': diff,
                    'accuracy': data['correct'] / data['total'],
                    'total_trials': data['total'],
                    'correct_trials': data['correct'],
                    'mean_reaction_time': sum(data['reaction_times']) / len(data['reaction_times']) if data['reaction_times'] else 0,
                    'reaction_time_std': pd.Series(data['reaction_times']).std() if len(data['reaction_times']) > 1 else 0
                }
        
        return psychometric_data
    
    def generate_analysis_report(self, experiment_data: Dict) -> str:
        """
        Generate a comprehensive analysis report
        
        Args:
            experiment_data: Complete experiment data dictionary
            
        Returns:
            Formatted analysis report as string
        """
        report_lines = []
        
        # Header
        report_lines.append("="*60)
        report_lines.append("PSYCHOPHYSICS 2AFC EXPERIMENT ANALYSIS REPORT")
        report_lines.append("="*60)
        report_lines.append("")
        
        # Participant info
        participant_info = experiment_data.get('participant_info', {})
        report_lines.append("PARTICIPANT INFORMATION:")
        report_lines.append(f"  Participant ID: {participant_info.get('participant_id', 'N/A')}")
        report_lines.append(f"  Number of trials: {participant_info.get('num_trials', 'N/A')}")
        report_lines.append(f"  Practice trials: {participant_info.get('num_practice_trials', 'N/A')}")
        report_lines.append("")
        
        # Summary statistics
        summary = experiment_data.get('summary', {})
        if summary:
            report_lines.append("OVERALL PERFORMANCE:")
            report_lines.append(f"  Total trials completed: {summary.get('total_trials', 0)}")
            report_lines.append(f"  Overall accuracy: {summary.get('accuracy', 0):.2%}")
            report_lines.append(f"  Correct responses: {summary.get('correct_responses', 0)}")
            report_lines.append("")
            
            report_lines.append("REACTION TIME STATISTICS:")
            report_lines.append(f"  Mean reaction time: {summary.get('avg_reaction_time', 0):.3f} seconds")
            report_lines.append(f"  Median reaction time: {summary.get('median_reaction_time', 0):.3f} seconds")
            report_lines.append(f"  Min reaction time: {summary.get('min_reaction_time', 0):.3f} seconds")
            report_lines.append(f"  Max reaction time: {summary.get('max_reaction_time', 0):.3f} seconds")
            report_lines.append("")
        
        # Psychometric function analysis
        trial_data = experiment_data.get('trial_data', [])
        if trial_data:
            psychometric_data = self.calculate_psychometric_function(trial_data)
            
            if psychometric_data:
                report_lines.append("PSYCHOMETRIC FUNCTION:")
                report_lines.append("  Stimulus Diff | Accuracy | Trials | Mean RT")
                report_lines.append("  -------------|----------|--------|--------")
                
                for diff in sorted(psychometric_data.keys()):
                    data = psychometric_data[diff]
                    report_lines.append(f"  {diff:11.1f} | {data['accuracy']:7.1%} | {data['total_trials']:6d} | {data['mean_reaction_time']:6.3f}")
                
                report_lines.append("")
        
        # Experiment timing
        if summary.get('experiment_start_time') and summary.get('experiment_end_time'):
            start_time = datetime.fromisoformat(summary['experiment_start_time'])
            end_time = datetime.fromisoformat(summary['experiment_end_time'])
            duration = end_time - start_time
            
            report_lines.append("EXPERIMENT TIMING:")
            report_lines.append(f"  Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"  End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"  Total duration: {duration}")
            report_lines.append("")
        
        # Footer
        report_lines.append("="*60)
        report_lines.append(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("="*60)
        
        return "\n".join(report_lines)
    
    def validate_trial_data(self, trial_data: List[Dict]) -> Dict:
        """
        Validate trial data for completeness and consistency
        
        Args:
            trial_data: List of trial result dictionaries
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        if not trial_data:
            validation_results['is_valid'] = False
            validation_results['errors'].append("No trial data provided")
            return validation_results
        
        # Check for required fields
        required_fields = ['trial_number', 'response', 'reaction_time', 'participant_id']
        missing_fields = set()
        
        for trial in trial_data:
            for field in required_fields:
                if field not in trial:
                    missing_fields.add(field)
        
        if missing_fields:
            validation_results['errors'].extend([f"Missing required field: {field}" for field in missing_fields])
            validation_results['is_valid'] = False
        
        # Check for reasonable reaction times
        reaction_times = [trial.get('reaction_time', 0) for trial in trial_data]
        if reaction_times:
            min_rt = min(reaction_times)
            max_rt = max(reaction_times)
            
            if min_rt < 0.1:  # Less than 100ms is likely too fast
                validation_results['warnings'].append(f"Very fast reaction times detected (min: {min_rt:.3f}s)")
            
            if max_rt > 10.0:  # More than 10s is likely too slow
                validation_results['warnings'].append(f"Very slow reaction times detected (max: {max_rt:.3f}s)")
        
        # Generate statistics
        validation_results['statistics'] = {
            'total_trials': len(trial_data),
            'practice_trials': sum(1 for trial in trial_data if trial.get('is_practice', False)),
            'main_trials': sum(1 for trial in trial_data if not trial.get('is_practice', False)),
            'unique_participants': len(set(trial.get('participant_id', '') for trial in trial_data))
        }
        
        return validation_results
