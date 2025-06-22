"""
Helper utilities for WebRS MTF Threshold experiment.
"""
import streamlit as st
import time
from typing import Any, Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

def format_time_duration(seconds: float) -> str:
    """
    Format time duration in human readable format
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f} ms"
    elif seconds < 60:
        return f"{seconds:.1f} s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"

def safe_get_session_state(key: str, default: Any = None) -> Any:
    """
    Safely get value from session state
    
    Args:
        key: Session state key
        default: Default value if key not found
        
    Returns:
        Session state value or default
    """
    try:
        return st.session_state.get(key, default)
    except Exception as e:
        logger.warning(f"Error accessing session state key '{key}': {e}")
        return default

def safe_set_session_state(key: str, value: Any) -> bool:
    """
    Safely set value in session state
    
    Args:
        key: Session state key
        value: Value to set
        
    Returns:
        True if successful
    """
    try:
        st.session_state[key] = value
        return True
    except Exception as e:
        logger.error(f"Error setting session state key '{key}': {e}")
        return False

def validate_participant_id(participant_id: str) -> tuple[bool, str]:
    """
    Validate participant ID
    
    Args:
        participant_id: Participant identifier
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not participant_id:
        return False, "Participant ID cannot be empty"
    
    if len(participant_id.strip()) < 2:
        return False, "Participant ID must be at least 2 characters long"
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in participant_id for char in invalid_chars):
        return False, f"Participant ID cannot contain: {', '.join(invalid_chars)}"
    
    return True, ""

def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate basic statistics for a list of values
    
    Args:
        values: List of numeric values
        
    Returns:
        Dictionary with statistics
    """
    if not values:
        return {}
    
    try:
        import numpy as np
        
        return {
            'count': len(values),
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'median': float(np.median(values))
        }
    except ImportError:
        # Fallback without numpy
        sorted_values = sorted(values)
        n = len(values)
        
        mean_val = sum(values) / n
        variance = sum((x - mean_val) ** 2 for x in values) / n
        std_val = variance ** 0.5
        
        if n % 2 == 0:
            median_val = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            median_val = sorted_values[n//2]
        
        return {
            'count': n,
            'mean': mean_val,
            'std': std_val,
            'min': min(values),
            'max': max(values),
            'median': median_val
        }

def show_error_message(message: str, error: Optional[Exception] = None) -> None:
    """
    Show error message in Streamlit
    
    Args:
        message: Error message to display
        error: Optional exception object
    """
    if error:
        logger.error(f"{message}: {error}")
        st.error(f"{message}: {str(error)}")
    else:
        logger.error(message)
        st.error(message)

def show_success_message(message: str) -> None:
    """
    Show success message in Streamlit
    
    Args:
        message: Success message to display
    """
    logger.info(message)
    st.success(message)

def show_warning_message(message: str) -> None:
    """
    Show warning message in Streamlit
    
    Args:
        message: Warning message to display
    """
    logger.warning(message)
    st.warning(message)

def show_info_message(message: str) -> None:
    """
    Show info message in Streamlit
    
    Args:
        message: Info message to display
    """
    logger.info(message)
    st.info(message)

def retry_operation(operation, max_retries: int = 3, delay: float = 1.0) -> tuple[bool, Any]:
    """
    Retry an operation with exponential backoff
    
    Args:
        operation: Function to retry
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        
    Returns:
        Tuple of (success, result)
    """
    for attempt in range(max_retries + 1):
        try:
            result = operation()
            return True, result
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Operation failed after {max_retries} retries: {e}")
                return False, None
            else:
                logger.warning(f"Operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
    
    return False, None

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def create_download_link(data: str, filename: str, mime_type: str = "text/plain") -> None:
    """
    Create download link for data
    
    Args:
        data: Data to download
        filename: Filename for download
        mime_type: MIME type of the data
    """
    try:
        st.download_button(
            label=f"📥 Download {filename}",
            data=data,
            file_name=filename,
            mime=mime_type
        )
    except Exception as e:
        logger.error(f"Error creating download link: {e}")
        show_error_message("Failed to create download link", e)

def format_percentage(value: float, decimal_places: int = 1) -> str:
    """
    Format value as percentage
    
    Args:
        value: Value between 0 and 1
        decimal_places: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimal_places}f}%"

def get_experiment_timestamp() -> str:
    """
    Get current timestamp for experiment use
    
    Returns:
        ISO format timestamp string
    """
    from datetime import datetime
    return datetime.now().isoformat()

def clean_filename(filename: str) -> str:
    """
    Clean filename for safe file operations
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    import re
    
    # Replace invalid characters with underscores
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple consecutive underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    
    return cleaned or "untitled"