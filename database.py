"""
Database models and operations for psychophysics experiments
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd

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
    left_stimulus = Column(Float)
    right_stimulus = Column(Float)
    stimulus_difference = Column(Float)
    mtf_value = Column(Float)  # For MTF experiments
    ado_stimulus_value = Column(Float)  # ADO selected value
    
    # Response data
    response = Column(String)  # 'left', 'right', 'clear', 'not_clear'
    is_correct = Column(Boolean)
    reaction_time = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)
    
    experiment = relationship("Experiment", back_populates="trials")

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
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
        """Save a trial to the database"""
        session = self.get_session()
        try:
            trial = Trial(
                experiment_id=experiment_id,
                trial_number=trial_data.get('trial_number'),
                is_practice=trial_data.get('is_practice', False),
                left_stimulus=trial_data.get('left_stimulus'),
                right_stimulus=trial_data.get('right_stimulus'),
                stimulus_difference=trial_data.get('stimulus_difference'),
                mtf_value=trial_data.get('mtf_value'),
                ado_stimulus_value=trial_data.get('ado_stimulus_value'),
                response=trial_data.get('response'),
                is_correct=trial_data.get('is_correct'),
                reaction_time=trial_data.get('reaction_time'),
                timestamp=datetime.fromisoformat(trial_data.get('timestamp', datetime.now().isoformat()))
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
                    'started_at': experiment.started_at,
                    'completed_at': experiment.completed_at
                },
                'trials': [
                    {
                        'trial_number': trial.trial_number,
                        'is_practice': trial.is_practice,
                        'left_stimulus': trial.left_stimulus,
                        'right_stimulus': trial.right_stimulus,
                        'stimulus_difference': trial.stimulus_difference,
                        'mtf_value': trial.mtf_value,
                        'ado_stimulus_value': trial.ado_stimulus_value,
                        'response': trial.response,
                        'is_correct': trial.is_correct,
                        'reaction_time': trial.reaction_time,
                        'timestamp': trial.timestamp
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
        """Export experiment data to CSV format"""
        data = self.get_experiment_data(experiment_id)
        if not data:
            return None
        
        df = pd.DataFrame(data['trials'])
        return df.to_csv(index=False)
    
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