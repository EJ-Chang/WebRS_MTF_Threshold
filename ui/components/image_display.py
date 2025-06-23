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

def get_viewport_size() -> Tuple[int, int]:
    """
    Get viewport size using JavaScript injection
    
    Returns:
        Tuple of (width, height) in pixels
    """
    try:
        # Inject JavaScript to get viewport size with better detection
        viewport_js = f"""
        <script>
        function getViewportSize() {{
            const width = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
            const height = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
            
            // Store in sessionStorage for persistence
            sessionStorage.setItem('viewport_width', width.toString());
            sessionStorage.setItem('viewport_height', height.toString());
            
            // Try to estimate based on common screen sizes if needed
            let adjustedWidth = width;
            let adjustedHeight = height;
            
            // Apply some smart defaults based on detected size
            if (width < 768) {{
                // Mobile device
                adjustedWidth = Math.min(width, 600);
                adjustedHeight = Math.min(height - 150, 450);  // Reserve space for mobile UI
            }} else if (width < 1024) {{
                // Tablet
                adjustedWidth = Math.min(width - 40, 800);
                adjustedHeight = Math.min(height - 200, 600);
            }} else {{
                // Desktop
                adjustedWidth = Math.min(width - 40, 1000);
                adjustedHeight = Math.min(height - 200, 750);
            }}
            
            // Update a hidden div that Streamlit can read
            let sizeDiv = document.getElementById('viewport_size_info');
            if (!sizeDiv) {{
                sizeDiv = document.createElement('div');
                sizeDiv.id = 'viewport_size_info';
                sizeDiv.style.display = 'none';
                document.body.appendChild(sizeDiv);
            }}
            sizeDiv.setAttribute('data-width', adjustedWidth.toString());
            sizeDiv.setAttribute('data-height', adjustedHeight.toString());
            sizeDiv.setAttribute('data-original-width', width.toString());
            sizeDiv.setAttribute('data-original-height', height.toString());
            
            return {{width: adjustedWidth, height: adjustedHeight, originalWidth: width, originalHeight: height}};
        }}
        
        // Get initial size
        const initialSize = getViewportSize();
        
        // Listen for resize events with debouncing
        let resizeTimeout;
        window.addEventListener('resize', function() {{
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(getViewportSize, 150);
        }});
        
        // Run on DOM content loaded
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', getViewportSize);
        }} else {{
            getViewportSize();
        }}
        </script>
        
        <!-- Hidden div for size communication -->
        <div id="viewport_size_info" style="display: none;" 
             data-width="{st.session_state.viewport_width}" 
             data-height="{st.session_state.viewport_height}"></div>
        """
        
        # Use session state to store viewport info with defaults
        if 'viewport_width' not in st.session_state:
            st.session_state.viewport_width = 1024  # Default width
        if 'viewport_height' not in st.session_state:
            st.session_state.viewport_height = 768  # Default height
        
        # Inject the JavaScript (only once per session)
        if 'viewport_js_injected' not in st.session_state:
            st.markdown(viewport_js, unsafe_allow_html=True)
            st.session_state.viewport_js_injected = True
        
        # Try to get updated values (JavaScript may have updated them)
        # For now, we'll use some heuristics based on Streamlit's container behavior
        # In a real implementation, you might need additional methods to get actual viewport size
        
        return st.session_state.viewport_width, st.session_state.viewport_height
        
    except Exception as e:
        logger.warning(f"Could not get viewport size: {e}")
        return 1024, 768  # Fallback default

def calculate_optimal_image_size(viewport_width: int, viewport_height: int) -> Tuple[int, int]:
    """
    Calculate optimal image size based on viewport dimensions
    
    Args:
        viewport_width: Viewport width in pixels
        viewport_height: Viewport height in pixels
        
    Returns:
        Tuple of (target_width, target_height) for image
    """
    try:
        # Reserve space for UI elements (header, buttons, etc.)
        ui_overhead_height = 200  # Approximate space for header, buttons, etc.
        ui_overhead_width = 40    # Padding/margins
        
        available_width = max(400, viewport_width - ui_overhead_width)
        available_height = max(300, viewport_height - ui_overhead_height)
        
        # Define size categories
        if viewport_width < 768:  # Mobile/small screens
            target_width = min(available_width, 600)
            target_height = min(available_height, 450)
        elif viewport_width < 1024:  # Tablets/medium screens
            target_width = min(available_width, 800)
            target_height = min(available_height, 600)
        else:  # Desktop/large screens
            target_width = min(available_width, 1000)
            target_height = min(available_height, 750)
        
        # Ensure minimum sizes
        target_width = max(target_width, 400)
        target_height = max(target_height, 300)
        
        logger.debug(f"Calculated image size: {target_width}x{target_height} for viewport {viewport_width}x{viewport_height}")
        return target_width, target_height
        
    except Exception as e:
        logger.warning(f"Error calculating image size: {e}")
        return 800, 600  # Fallback default

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
    Display MTF stimulus image for the experiment with responsive sizing
    
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
        # Get viewport size for responsive design
        viewport_width, viewport_height = get_viewport_size()
        target_width, target_height = calculate_optimal_image_size(viewport_width, viewport_height)
        
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

        # Apply responsive cropping/resizing based on viewport
        processed_img = crop_image_to_viewport(image_array, target_width, target_height)
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

        # Responsive CSS styling
        responsive_style = f"""
        max-width: min(100%, {target_width}px);
        max-height: min(90vh, {target_height}px);
        width: auto;
        height: auto;
        """

        # Clean HTML for stimulus display with responsive styling
        html_content = f"""
        <div style="text-align: center; margin: 20px 0;">
            <img id="{img_id}" src="data:image/png;base64,{img_str}" 
                 style="{responsive_style}">
            <p style="margin: 10px 0; color: #666; font-size: 14px;">{caption}</p>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)

        # Log responsive behavior for debugging
        logger.debug(f"Displayed image: viewport {viewport_width}x{viewport_height} -> target {target_width}x{target_height} -> final {final_w}x{final_h}")

        # Return image dimensions for button positioning
        return {
            'display_height': final_h,
            'center_position': final_h / 2,
            'original_width': final_w,
            'original_height': final_h,
            'viewport_width': viewport_width,
            'viewport_height': viewport_height,
            'target_width': target_width,
            'target_height': target_height,
            'responsive_sizing': True
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