"""
Logger utility for WebRS MTF Threshold experiment.
"""
import logging

def get_logger(name: str) -> logging.Logger:
    """Get logger instance with specified name"""
    return logging.getLogger(name)

# Common loggers
app_logger = get_logger('app')
experiment_logger = get_logger('experiment')
data_logger = get_logger('data')
ui_logger = get_logger('ui')