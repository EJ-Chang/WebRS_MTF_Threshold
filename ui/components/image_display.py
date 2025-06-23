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
from typing import Optional, Dict, Any, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)



def crop_image_center(image_array: np.ndarray) -> Optional[np.ndarray]:
    """
    Crop image to maintain original cropped dimensions without resizing
    
    Args:
        image_array: Input image array
        
    Returns:
        Original image array (no cropping or resizing applied)
    """
    if image_array is None:
        return None
    
    # Return original image without any modifications
    # Cropping logic is handled in mtf_experiment.py load_and_prepare_image function
    return image_array

def display_mtf_stimulus_image(image_data: Any, caption: str = "") -> Optional[Dict[str, Any]]:
    """
    Display MTF stimulus image for the experiment with fixed sizing
    
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

        # Use original image dimensions without any resizing
        processed_img = crop_image_center(image_array)
        if processed_img is None:
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

        # Fixed pixel size styling to prevent DPI scaling
        simple_style = f"""
        display: block;
        margin: 0 auto;
        width: {final_w}px !important;
        height: {final_h}px !important;
        image-rendering: pixelated;
        zoom: 1;
        -webkit-transform: scale(1);
        -moz-transform: scale(1);
        -ms-transform: scale(1);
        transform: scale(1);
        """

        # Clean HTML for stimulus display with fixed sizing
        html_content = f"""
        <div style="text-align: center; margin: 20px 0;">
            <img id="{img_id}" src="data:image/png;base64,{img_str}" 
                 style="{simple_style}">
            <p style="margin: 10px 0; color: #666; font-size: 14px;">{caption}</p>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)

        # Log image display for debugging
        logger.debug(f"Displayed image with original dimensions: {final_w}x{final_h}")

        # Return image dimensions for button positioning
        return {
            'display_height': final_h,
            'center_position': final_h / 2,
            'original_width': final_w,
            'original_height': final_h,
            'responsive_sizing': False
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