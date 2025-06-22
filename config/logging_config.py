"""
Logging configuration for WebRS MTF Threshold experiment.
"""
import logging
import sys
from datetime import datetime

def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # File handler (optional)
    try:
        file_handler = logging.FileHandler(
            f'experiment_log_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
    except Exception:
        file_handler = None
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add handlers
    root_logger.addHandler(console_handler)
    if file_handler:
        root_logger.addHandler(file_handler)
    
    return root_logger

# Initialize logging
setup_logging()