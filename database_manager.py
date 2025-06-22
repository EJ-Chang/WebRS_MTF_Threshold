"""
Database Manager for Replit PostgreSQL integration
Handles database operations for the psychophysics experiment platform
"""
import os
from typing import Optional, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, Participant, Experiment, Trial
from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Manages database operations for experiments"""
    
    def __init__(self):
        """Initialize database manager with PostgreSQL connection"""
        self.engine = None
        self.Session = None
        self.initialize_connection()
    
    def initialize_connection(self):
        """Initialize database connection"""
        try:
            # Get database URL from environment (Replit provides this)
            database_url = os.environ.get('DATABASE_URL')
            
            if database_url:
                self.engine = create_engine(database_url, echo=False)
                self.Session = sessionmaker(bind=self.engine)
                
                # Create tables if they don't exist
                Base.metadata.create_all(self.engine)
                logger.info("Database connection established successfully")
            else:
                logger.warning("No DATABASE_URL found, database features disabled")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            self.engine = None
            self.Session = None
    
    def is_available(self) -> bool:
        """Check if database is available"""
        return self.engine is not None and self.Session is not None
    
    def create_participant(self, participant_id: str) -> bool:
        """Create a new participant record"""
        if not self.is_available():
            return False
            
        try:
            session = self.Session()
            participant = Participant(id=participant_id)
            session.add(participant)
            session.commit()
            session.close()
            logger.info(f"Created participant: {participant_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create participant: {e}")
            return False
    
    def save_experiment_data(self, experiment_data: Dict[str, Any]) -> bool:
        """Save experiment data to database"""
        if not self.is_available():
            return False
            
        try:
            session = self.Session()
            
            # Create experiment record
            experiment = Experiment(
                participant_id=experiment_data.get('participant_id'),
                experiment_type=experiment_data.get('experiment_type', 'MTF'),
                use_ado=experiment_data.get('use_ado', False),
                num_trials=experiment_data.get('num_trials', 0),
                num_practice_trials=experiment_data.get('num_practice_trials', 0)
            )
            
            session.add(experiment)
            session.flush()  # Get the experiment ID
            
            # Save trial data
            trials_data = experiment_data.get('trials', [])
            for trial_data in trials_data:
                trial = Trial(
                    experiment_id=experiment.id,
                    trial_number=trial_data.get('trial_number'),
                    is_practice=trial_data.get('is_practice', False),
                    mtf_value=trial_data.get('mtf_value'),
                    ado_stimulus_value=trial_data.get('ado_stimulus_value'),
                    response=trial_data.get('response'),
                    is_correct=trial_data.get('is_correct'),
                    reaction_time=trial_data.get('reaction_time')
                )
                session.add(trial)
            
            session.commit()
            session.close()
            logger.info(f"Saved experiment data for participant: {experiment_data.get('participant_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save experiment data: {e}")
            return False