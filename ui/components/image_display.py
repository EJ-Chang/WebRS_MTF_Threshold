"""
Image display components for WebRS MTF Threshold experiment.
"""
import streamlit as st
import numpy as np
import cv2
import time
import base64
from PIL import Image
from io import BytesIO
from typing import Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

def crop_image_to_viewport(image_array: np.ndarray, target_width: int = 800, target_height: int = 600) -> Optional[np.ndarray]:
    """
    Crop image to fit viewport while maintaining aspect ratio and centering
    
    Args:
        image_array: Input image array
        target_width: Target width in pixels
        target_height: Target height in pixels
        
    Returns:
        Cropped and resized image array
    """
    if image_array is None:
        return None

    h, w = image_array.shape[:2]

    # Calculate aspect ratios
    img_aspect = w / h
    target_aspect = target_width / target_height

    if img_aspect > target_aspect:
        # Image is wider than target, crop width
        new_width = int(h * target_aspect)
        start_x = (w - new_width) // 2
        cropped = image_array[:, start_x:start_x + new_width]
    else:
        # Image is taller than target, crop height
        new_height = int(w / target_aspect)
        start_y = (h - new_height) // 2
        cropped = image_array[start_y:start_y + new_height, :]

    # Resize to target dimensions
    resized = cv2.resize(cropped, (target_width, target_height))
    return resized

def display_mtf_stimulus_image(image_data: Any, caption: str = "") -> Optional[Dict[str, Any]]:
    """
    Display MTF stimulus image for the experiment
    
    Args:
        image_data: Image data (various formats supported)
        caption: Optional caption for the image
        
    Returns:
        Dict with image dimensions for button positioning
    """
    if image_data is None:
        st.error("❌ Stimulus image not available")
        return None

    try:
        # Process image data format
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                # Extract base64 data
                base64_data = image_data.split(',')[1]
                img_bytes = base64.b64decode(base64_data)
                img = Image.open(BytesIO(img_bytes))
                image_array = np.array(img)
            else:
                st.error("❌ Invalid image data format")
                return None
        elif isinstance(image_data, np.ndarray):
            image_array = image_data
        else:
            try:
                image_array = np.array(image_data)
            except Exception as e:
                st.error(f"❌ Failed to convert to numpy array: {e}")
                return None

        if not isinstance(image_array, np.ndarray):
            st.error("❌ Invalid image array")
            return None

        # Process the image for display
        processed_img = image_array

        # Convert to PIL for display
        img_pil = Image.fromarray(processed_img)

        # Convert to base64 for HTML display
        buffer = BytesIO()
        img_pil.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        # Add unique ID for positioning calculation
        img_id = f"mtf_img_{int(time.time() * 1000)}"
        final_h, final_w = processed_img.shape[:2]

        # Clean HTML for stimulus display
        html_content = f"""
        <div style="text-align: center; margin: 20px 0;">
            <img id="{img_id}" src="data:image/png;base64,{img_str}" 
                 style="max-width: 100%; height: auto;">
            <p style="margin: 10px 0; color: #666; font-size: 14px;">{caption}</p>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)

        # Return image dimensions for button positioning
        return {
            'display_height': final_h,
            'center_position': final_h / 2,
            'original_width': final_w,
            'original_height': final_h,
            'no_scaling': True
        }
        
    except Exception as e:
        logger.error(f"Error displaying MTF stimulus image: {e}")
        st.error(f"❌ Error displaying image: {e}")
        return None

def display_fullscreen_image(image_data: Any, caption: str = "") -> Optional[Dict[str, Any]]:
    """
    Legacy function - redirect to MTF stimulus display
    
    Args:
        image_data: Image data
        caption: Optional caption
        
    Returns:
        Image display information
    """
    return display_mtf_stimulus_image(image_data, caption)