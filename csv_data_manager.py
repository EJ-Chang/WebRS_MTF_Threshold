"""
CSV-based data manager for psychophysics experiments
Replaces database storage with simple CSV file storage
"""
import pandas as pd
import os
import csv
from datetime import datetime
from typing import List, Dict, Optional
import json

class CSVDataManager:
    """Manages experiment data using CSV files"""
    
    def __init__(self, data_dir: str = "experiment_data"):
        """Initialize CSV data manager
        
        Args:
            data_dir: Directory to store CSV files
        """
        self.data_dir = data_dir
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"📁 Created data directory: {self.data_dir}")
    
    def get_participant_file_path(self, participant_id: str) -> str:
        """Get file path for participant data"""
        safe_id = "".join(c for c in participant_id if c.isalnum() or c in ('-', '_'))
        return os.path.join(self.data_dir, f"{safe_id}_data.csv")
    
    def get_experiment_summary_path(self, participant_id: str) -> str:
        """Get file path for experiment summary"""
        safe_id = "".join(c for c in participant_id if c.isalnum() or c in ('-', '_'))
        return os.path.join(self.data_dir, f"{safe_id}_summary.json")
    
    def create_participant_record(self, participant_id: str, experiment_config: Dict):
        """Create initial participant record
        
        Args:
            participant_id: Unique participant identifier
            experiment_config: Experiment configuration dictionary
        """
        summary_path = self.get_experiment_summary_path(participant_id)
        
        summary_data = {
            'participant_id': participant_id,
            'created_at': datetime.now().isoformat(),
            'experiment_config': experiment_config,
            'status': 'started',
            'total_trials': 0,
            'completed_trials': 0
        }
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Created participant record: {participant_id}")
    
    def save_trial_data(self, participant_id: str, trial_data: Dict):
        """Save single trial data to CSV
        
        Args:
            participant_id: Participant identifier
            trial_data: Trial data dictionary
        """
        file_path = self.get_participant_file_path(participant_id)
        
        # Add timestamp if not present
        if 'timestamp' not in trial_data:
            trial_data['timestamp'] = datetime.now().isoformat()
        
        # Convert numpy types to Python types
        cleaned_data = self._clean_trial_data(trial_data)
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(file_path)
        
        # Write to CSV
        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            if cleaned_data:
                fieldnames = cleaned_data.keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header if file is new
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(cleaned_data)
        
        print(f"💾 Saved trial data for {participant_id}")
    
    def save_multiple_trials(self, participant_id: str, trials_data: List[Dict]):
        """Save multiple trials at once
        
        Args:
            participant_id: Participant identifier
            trials_data: List of trial data dictionaries
        """
        if not trials_data:
            return
        
        file_path = self.get_participant_file_path(participant_id)
        
        # Clean all trial data
        cleaned_trials = [self._clean_trial_data(trial) for trial in trials_data]
        
        # Create DataFrame and save
        df = pd.DataFrame(cleaned_trials)
        df.to_csv(file_path, index=False, encoding='utf-8')
        
        print(f"💾 Saved {len(trials_data)} trials for {participant_id}")
    
    def _clean_trial_data(self, trial_data: Dict) -> Dict:
        """Clean trial data by converting numpy types to Python types
        
        Args:
            trial_data: Raw trial data dictionary
            
        Returns:
            Cleaned trial data dictionary
        """
        cleaned = {}
        
        for key, value in trial_data.items():
            if value is None:
                cleaned[key] = None
            elif hasattr(value, 'item'):  # numpy scalar
                cleaned[key] = value.item()
            elif hasattr(value, 'dtype'):  # numpy array/scalar
                if 'float' in str(value.dtype):
                    cleaned[key] = float(value)
                elif 'int' in str(value.dtype):
                    cleaned[key] = int(value)
                else:
                    cleaned[key] = str(value)
            else:
                cleaned[key] = value
        
        return cleaned
    
    def get_participant_data(self, participant_id: str) -> Optional[pd.DataFrame]:
        """Load participant data from CSV
        
        Args:
            participant_id: Participant identifier
            
        Returns:
            DataFrame with participant data or None if not found
        """
        file_path = self.get_participant_file_path(participant_id)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            return df
        except Exception as e:
            print(f"❌ Error loading data for {participant_id}: {e}")
            return None
    
    def get_experiment_summary(self, participant_id: str) -> Optional[Dict]:
        """Get experiment summary data
        
        Args:
            participant_id: Participant identifier
            
        Returns:
            Summary dictionary or None if not found
        """
        summary_path = self.get_experiment_summary_path(participant_id)
        
        if not os.path.exists(summary_path):
            return None
        
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading summary for {participant_id}: {e}")
            return None
    
    def update_experiment_status(self, participant_id: str, status: str, **kwargs):
        """Update experiment status and metadata
        
        Args:
            participant_id: Participant identifier
            status: New status ('started', 'completed', 'interrupted')
            **kwargs: Additional fields to update
        """
        summary = self.get_experiment_summary(participant_id)
        if not summary:
            return
        
        summary['status'] = status
        summary['updated_at'] = datetime.now().isoformat()
        
        # Update additional fields
        for key, value in kwargs.items():
            summary[key] = value
        
        # Save updated summary
        summary_path = self.get_experiment_summary_path(participant_id)
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def complete_experiment(self, participant_id: str):
        """Mark experiment as completed
        
        Args:
            participant_id: Participant identifier
        """
        # Get trial count
        df = self.get_participant_data(participant_id)
        trial_count = len(df) if df is not None else 0
        
        self.update_experiment_status(
            participant_id, 
            'completed',
            completed_at=datetime.now().isoformat(),
            total_trials=trial_count
        )
        
        print(f"✅ Experiment completed for {participant_id}")
    
    def export_to_csv_string(self, participant_id: str) -> Optional[str]:
        """Export participant data as CSV string
        
        Args:
            participant_id: Participant identifier
            
        Returns:
            CSV data as string or None if not found
        """
        df = self.get_participant_data(participant_id)
        if df is None:
            return None
        
        return df.to_csv(index=False)
    
    def list_participants(self) -> List[Dict]:
        """List all participants with their data files
        
        Returns:
            List of participant info dictionaries
        """
        participants = []
        
        if not os.path.exists(self.data_dir):
            return participants
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith('_data.csv'):
                participant_id = filename[:-9]  # Remove '_data.csv'
                
                # Get file info
                file_path = os.path.join(self.data_dir, filename)
                file_stat = os.stat(file_path)
                
                # Try to get summary info
                summary = self.get_experiment_summary(participant_id)
                
                participants.append({
                    'participant_id': participant_id,
                    'data_file': filename,
                    'file_size': file_stat.st_size,
                    'modified_at': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'status': summary.get('status', 'unknown') if summary else 'unknown',
                    'trial_count': len(pd.read_csv(file_path)) if os.path.exists(file_path) else 0
                })
        
        return participants
    
    def calculate_psychometric_function(self, participant_id: str) -> Dict:
        """Calculate psychometric function from participant data
        
        Args:
            participant_id: Participant identifier
            
        Returns:
            Dictionary with psychometric function data
        """
        df = self.get_participant_data(participant_id)
        if df is None or df.empty:
            return {}
        
        # Filter out practice trials
        if 'is_practice' in df.columns:
            df = df[~df['is_practice']]
        
        if df.empty:
            return {}
        
        # Group by stimulus difference
        if 'stimulus_difference' in df.columns:
            grouped = df.groupby('stimulus_difference').agg({
                'is_correct': ['count', 'sum', 'mean'],
                'reaction_time': ['mean', 'std']
            }).round(3)
            
            # Flatten column names
            grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
            
            return grouped.to_dict()
        
        return {}
    
    def cleanup_old_files(self, days_old: int = 30):
        """Remove old data files
        
        Args:
            days_old: Remove files older than this many days
        """
        if not os.path.exists(self.data_dir):
            return
        
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
        removed_count = 0
        
        for filename in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, filename)
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_time:
                os.remove(file_path)
                removed_count += 1
        
        if removed_count > 0:
            print(f"🗑️ Removed {removed_count} old data files")