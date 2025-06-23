"""
Database models and operations for psychophysics experiments
"""
import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd

logger = logging.getLogger(__name__)

Base = declarative_base()

class Participant(Base):
    __tablename__ = 'participants'
    
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.now)
    experiments = relationship("Experiment", back_populates="participant")

class Experiment(Base):
    __tablename__ = 'experiments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    participant_id = Column(String, ForeignKey('participants.id'))
    experiment_type = Column(String, nullable=False)
    use_ado = Column(Boolean, default=False)
    num_trials = Column(Integer)
    num_practice_trials = Column(Integer)
    max_trials = Column(Integer)
    min_trials = Column(Integer)
    convergence_threshold = Column(Float)
    stimulus_duration = Column(Float)
    inter_trial_interval = Column(Float)
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)
    
    participant = relationship("Participant", back_populates="experiments")
    trials = relationship("Trial", back_populates="experiment")

class Trial(Base):
    __tablename__ = 'trials'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey('experiments.id'))
    trial_number = Column(Integer, nullable=False)
    is_practice = Column(Boolean, default=False)
    
    # Stimulus parameters
    mtf_value = Column(Float)  # For MTF experiments
    ado_stimulus_value = Column(Float)  # ADO selected value for next trial
    stimulus_image_file = Column(String)  # Record which image file was used
    
    # Response data
    response = Column(String)  # 'clear', 'not_clear'
    reaction_time = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)
    
    # Essential trial info (for easy querying without joins)
    participant_id = Column(String)  # Direct participant reference
    experiment_type = Column(String)  # 'MTF_Clarity', etc.
    
    # ADO computation results (optional, for analysis)
    estimated_threshold = Column(Float)  # Current estimated threshold
    estimated_slope = Column(Float)  # Current estimated slope
    threshold_std = Column(Float)  # Threshold uncertainty
    slope_std = Column(Float)  # Slope uncertainty
    
    experiment = relationship("Experiment", back_populates="trials")

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        
        try:
            self.engine = create_engine(self.database_url)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            print(f"✅ Database connected: {self.database_url.split('@')[0]}@***")
            
        except Exception as e:
            print(f"⚠️ Database connection failed: {e}")
            print("🔄 Falling back to SQLite...")
            self._setup_sqlite_fallback()
    
    def _get_database_url(self):
        """Get database URL with Replit-specific handling"""
        # Try standard DATABASE_URL first (Replit PostgreSQL uses this)
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            print("🐘 Using Replit PostgreSQL via DATABASE_URL")
            return db_url
        
        # Try legacy REPLIT_DB_URL
        replit_db = os.getenv('REPLIT_DB_URL')
        if replit_db:
            print("🐘 Using REPLIT_DB_URL PostgreSQL")
            return replit_db
        
        # Fall back to SQLite for development
        print("💾 Using SQLite fallback")
        return "sqlite:///./psychophysics_experiments.db"
    
    def _setup_sqlite_fallback(self):
        """Setup SQLite as fallback database"""
        # self.database_url = "sqlite:///./psychophysics_experiments.db"
        # 在本機環境中，將PostgreSQL設定改為SQLite
        self.database_url = "sqlite:///psychophysics_experiments.db"
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        print("✅ SQLite database initialized")
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def create_participant(self, participant_id: str):
        """Create a new participant if not exists"""
        session = self.get_session()
        try:
            participant = session.query(Participant).filter(Participant.id == participant_id).first()
            if not participant:
                participant = Participant(id=participant_id)
                session.add(participant)
                session.commit()
                session.refresh(participant)  # Refresh to get the committed data
            return participant
        finally:
            session.close()
    
    def create_experiment(self, participant_id: str, experiment_type: str, **kwargs):
        """Create a new experiment record"""
        session = self.get_session()
        try:
            # Ensure participant exists
            self.create_participant(participant_id)
            
            experiment = Experiment(
                participant_id=participant_id,
                experiment_type=experiment_type,
                use_ado=kwargs.get('use_ado', False),
                num_trials=kwargs.get('num_trials'),
                num_practice_trials=kwargs.get('num_practice_trials'),
                max_trials=kwargs.get('max_trials'),
                min_trials=kwargs.get('min_trials'),
                convergence_threshold=kwargs.get('convergence_threshold'),
                stimulus_duration=kwargs.get('stimulus_duration'),
                inter_trial_interval=kwargs.get('inter_trial_interval')
            )
            session.add(experiment)
            session.commit()
            session.refresh(experiment)
            return experiment.id
        finally:
            session.close()
    
    def save_trial(self, experiment_id: int, trial_data: dict):
        """Save a trial to the database - ensuring consistency with CSV format"""
        session = self.get_session()
        try:
            # Convert numpy types to standard Python types to avoid database issues
            def convert_numpy_value(value):
                if value is None:
                    return None
                if hasattr(value, 'item'):  # numpy scalar
                    return value.item()
                if hasattr(value, 'dtype'):  # numpy array/scalar
                    return float(value) if 'float' in str(value.dtype) else int(value)
                return value
            
            # Map trial data to simplified database fields
            trial = Trial(
                experiment_id=experiment_id,
                trial_number=trial_data.get('trial_number'),
                is_practice=trial_data.get('is_practice', False),
                # Stimulus parameters
                mtf_value=convert_numpy_value(trial_data.get('mtf_value')),
                ado_stimulus_value=convert_numpy_value(trial_data.get('ado_stimulus_value')),
                stimulus_image_file=trial_data.get('stimulus_image_file'),
                # Response data
                response=trial_data.get('response'),
                reaction_time=convert_numpy_value(trial_data.get('reaction_time')),
                timestamp=datetime.fromisoformat(trial_data.get('timestamp', datetime.now().isoformat())),
                # Essential trial info (for easy querying)
                participant_id=trial_data.get('participant_id'),
                experiment_type=trial_data.get('experiment_type'),
                # ADO computation results (optional)
                estimated_threshold=convert_numpy_value(trial_data.get('estimated_threshold')),
                estimated_slope=convert_numpy_value(trial_data.get('estimated_slope')),
                threshold_std=convert_numpy_value(trial_data.get('threshold_std')),
                slope_std=convert_numpy_value(trial_data.get('slope_std'))
            )
            session.add(trial)
            session.commit()
            
            
            return trial.id
        finally:
            session.close()
    
    def complete_experiment(self, experiment_id: int):
        """Mark an experiment as completed"""
        session = self.get_session()
        try:
            experiment = session.query(Experiment).filter(Experiment.id == experiment_id).first()
            if experiment:
                session.query(Experiment).filter(Experiment.id == experiment_id).update(
                    {'completed_at': datetime.now()}
                )
                session.commit()
        finally:
            session.close()
    
    def get_experiment_data(self, experiment_id: int):
        """Get all data for an experiment"""
        session = self.get_session()
        try:
            experiment = session.query(Experiment).filter(Experiment.id == experiment_id).first()
            if not experiment:
                return None
            
            trials = session.query(Trial).filter(Trial.experiment_id == experiment_id).all()
            
            return {
                'experiment': {
                    'id': experiment.id,
                    'participant_id': experiment.participant_id,
                    'experiment_type': experiment.experiment_type,
                    'use_ado': experiment.use_ado,
                    'num_trials': experiment.num_trials,
                    'num_practice_trials': experiment.num_practice_trials,
                    'max_trials': experiment.max_trials,
                    'min_trials': experiment.min_trials,
                    'convergence_threshold': experiment.convergence_threshold,
                    'stimulus_duration': experiment.stimulus_duration,
                    'inter_trial_interval': experiment.inter_trial_interval,
                    'started_at': experiment.started_at,
                    'completed_at': experiment.completed_at
                },
                'trials': [
                    {
                        'participant_id': trial.participant_id,
                        'trial_number': trial.trial_number,
                        'mtf_value': trial.mtf_value,
                        'ado_stimulus_value': trial.ado_stimulus_value,
                        'response': trial.response,
                        'reaction_time': trial.reaction_time,
                        'timestamp': trial.timestamp,
                        'experiment_type': trial.experiment_type,
                        'stimulus_image_file': trial.stimulus_image_file,
                        'max_trials': experiment.max_trials,  # From experiment level
                        'is_practice': trial.is_practice,
                        # ADO computation results (simplified)
                        'estimated_threshold': trial.estimated_threshold,
                        'estimated_slope': trial.estimated_slope,
                        'threshold_std': trial.threshold_std,
                        'slope_std': trial.slope_std
                    }
                    for trial in trials
                ]
            }
        finally:
            session.close()
    
    def get_participant_experiments(self, participant_id: str):
        """Get all experiments for a participant"""
        session = self.get_session()
        try:
            experiments = session.query(Experiment).filter(Experiment.participant_id == participant_id).all()
            return [
                {
                    'id': exp.id,
                    'experiment_type': exp.experiment_type,
                    'started_at': exp.started_at,
                    'completed_at': exp.completed_at,
                    'trial_count': len(exp.trials)
                }
                for exp in experiments
            ]
        finally:
            session.close()
    
    def export_to_csv(self, experiment_id: int):
        """Export experiment data to CSV format with specified field order"""
        data = self.get_experiment_data(experiment_id)
        if not data:
            return None
        
        # Define the required field order - only keep essential fields
        required_fields = [
            'participant_id', 'trial_number', 'mtf_value', 'ado_stimulus_value', 
            'response', 'reaction_time', 'timestamp', 'experiment_type', 
            'stimulus_image_file', 'max_trials'
        ]
        
        # Create DataFrame with only required fields in specified order
        df = pd.DataFrame(data['trials'])
        
        # Add max_trials from experiment data if not in trials
        if 'max_trials' not in df.columns and data['experiment']['max_trials']:
            df['max_trials'] = data['experiment']['max_trials']
        
        # Select and reorder columns
        available_fields = [field for field in required_fields if field in df.columns]
        df_ordered = df[available_fields]
        
        return df_ordered.to_csv(index=False)
    
    def update_trial_ado_value(self, experiment_id: int, trial_number: int, ado_stimulus_value: float):
        """Update the ado_stimulus_value for a specific trial"""
        session = self.get_session()
        try:
            # Find the trial to update
            trial = session.query(Trial).filter(
                Trial.experiment_id == experiment_id,
                Trial.trial_number == trial_number
            ).first()
            
            if trial:
                trial.ado_stimulus_value = ado_stimulus_value
                session.commit()
                logger.info(f"Updated trial {trial_number} ado_stimulus_value to {ado_stimulus_value}")
                return True
            else:
                logger.warning(f"Trial {trial_number} not found in experiment {experiment_id}")
                return False
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating trial ADO value: {e}")
            return False
        finally:
            session.close()

    def get_all_participants(self):
        """Get list of all participants"""
        session = self.get_session()
        try:
            participants = session.query(Participant).all()
            return [
                {
                    'id': p.id,
                    'created_at': p.created_at,
                    'experiment_count': len(p.experiments)
                }
                for p in participants
            ]
        finally:
            session.close()