"""
Image display components for WebRS MTF Threshold experiment.
Updated with lossless pixel-perfect rendering.
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


def numpy_to_lossless_base64(image_array: np.ndarray) -> str:
    """
    Convert numpy array to lossless base64 string without PIL recompression.
    
    This function uses OpenCV's PNG encoding to avoid any quality loss that
    might occur with PIL's save operations.
    
    Args:
        image_array: Input image array in RGB format (H, W, 3)
        
    Returns:
        str: Base64 encoded PNG data string
        
    Raises:
        ValueError: If image array format is invalid
        RuntimeError: If encoding fails
    """
    if not isinstance(image_array, np.ndarray):
        raise ValueError("Input must be a numpy array")
    
    if len(image_array.shape) != 3 or image_array.shape[2] != 3:
        raise ValueError("Image array must be RGB format (H, W, 3)")
    
    try:
        # Convert RGB to BGR for OpenCV (OpenCV uses BGR by default)
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        # Encode as PNG with lossless compression
        # Use maximum compression (9) for smaller size while maintaining lossless quality
        encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
        success, encoded_img = cv2.imencode('.png', image_bgr, encode_params)
        
        if not success:
            raise RuntimeError("Failed to encode image as PNG")
        
        # Convert to base64 string
        img_base64 = base64.b64encode(encoded_img.tobytes()).decode('utf-8')
        
        logger.debug(f"🔄 Lossless encoding: {image_array.shape} → {len(img_base64)} base64 chars")
        return img_base64
        
    except Exception as e:
        logger.error(f"Error in numpy_to_lossless_base64: {e}")
        raise RuntimeError(f"Lossless encoding failed: {e}")


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

def display_mtf_stimulus_image(image_data: Any, caption: str = "", staged_loading: bool = True) -> Optional[Dict[str, Any]]:
    """
    Display MTF stimulus image with lossless pixel-perfect rendering and optional staged loading.
    
    Features:
    - Direct numpy → base64 conversion without PIL recompression
    - Pixel-perfect CSS rendering with crisp edges
    - Absolute pixel dimensions for precise display
    - Optional staged loading: placeholder → loading → final image
    
    Args:
        image_data: Image data (various formats supported)
        caption: Optional caption for the image
        staged_loading: Whether to use staged loading (default True)
        
    Returns:
        Dict with container dimensions for button positioning
    """
    if image_data is None:
        st.error("❌ Stimulus image not available")
        return None

    # Staged loading: show placeholder first if enabled
    if staged_loading:
        # Create placeholder containers
        if 'image_container' not in st.session_state:
            st.session_state.image_container = st.empty()
        
        # Show placeholder initially
        placeholder_html = """
        <div style="
            text-align: center; 
            margin: 20px auto; 
            width: 400px; 
            height: 400px; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            border: 2px dashed #ddd; 
            border-radius: 10px;
            background: #f8f9fa;
            color: #6c757d;
        ">
            <div style="font-size: 48px; margin-bottom: 15px;">🖼️</div>
            <div style="font-size: 16px;">載入刺激圖片中...</div>
            <div style="margin-top: 10px;">
                <div style="width: 200px; height: 4px; background: #e9ecef; border-radius: 2px;">
                    <div style="width: 0%; height: 100%; background: #007bff; border-radius: 2px; animation: loading-bar 2s ease-in-out;"></div>
                </div>
            </div>
        </div>
        <style>
        @keyframes loading-bar {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }
        </style>
        """
        
        st.session_state.image_container.markdown(placeholder_html, unsafe_allow_html=True)
        time.sleep(0.2)  # Brief pause to show placeholder

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

        # Use original image without forcing pixel-perfect cropping
        processed_img = crop_image_center(image_array)
        if processed_img is None:
            processed_img = image_array

        # Check if we have a pre-encoded base64 string to avoid repeated encoding
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            # Already has base64 data, extract it
            img_str = image_data.split(',')[1]
            logger.debug("✅ Using pre-encoded base64 data (no encoding needed)")
        elif hasattr(st.session_state, 'mtf_experiment_manager'):
            # Try to get pre-encoded base64 from experiment manager
            exp_manager = st.session_state.mtf_experiment_manager
            trial_data = st.session_state.get('mtf_trial_data')
            if trial_data and 'mtf_value' in trial_data:
                mtf_value = trial_data['mtf_value']
                try:
                    pre_encoded = exp_manager.generate_and_cache_base64_image(mtf_value)
                    if pre_encoded:
                        img_str = pre_encoded
                        # Check if this was pregenerated during fixation
                        if hasattr(st.session_state, 'pregeneration_mtf') and st.session_state.pregeneration_mtf == mtf_value:
                            pregeneration_time = st.session_state.get('pregeneration_time', 0)
                            logger.info(f"🎯 Using pregenerated image from fixation: MTF {mtf_value:.1f}% (generated in {pregeneration_time:.2f}ms)")
                        else:
                            logger.debug("🚀 Using cached base64 from experiment manager (performance optimized)")
                    else:
                        raise Exception("Pre-encoding failed")
                except Exception as e:
                    logger.warning(f"Pre-encoding failed, using real-time encoding: {e}")
                    # Fallback to real-time encoding
                    try:
                        img_str = numpy_to_lossless_base64(processed_img)
                        logger.debug("⚠️ Using real-time lossless base64 encoding")
                    except Exception as e2:
                        logger.warning(f"⚠️ Lossless encoding failed, falling back to PIL: {e2}")
                        img_pil = Image.fromarray(processed_img)
                        buffer = BytesIO()
                        img_pil.save(buffer, format='PNG')
                        img_str = base64.b64encode(buffer.getvalue()).decode()
            else:
                # No trial data, use real-time encoding
                try:
                    img_str = numpy_to_lossless_base64(processed_img)
                    logger.debug("✅ Using real-time lossless base64 encoding")
                except Exception as e:
                    logger.warning(f"⚠️ Lossless encoding failed, falling back to PIL: {e}")
                    img_pil = Image.fromarray(processed_img)
                    buffer = BytesIO()
                    img_pil.save(buffer, format='PNG')
                    img_str = base64.b64encode(buffer.getvalue()).decode()
        else:
            # No experiment manager, use real-time encoding
            try:
                img_str = numpy_to_lossless_base64(processed_img)
                logger.debug("✅ Using real-time lossless base64 encoding")
            except Exception as e:
                logger.warning(f"⚠️ Lossless encoding failed, falling back to PIL: {e}")
                img_pil = Image.fromarray(processed_img)
                buffer = BytesIO()
                img_pil.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode()

        # Add unique ID for CSS targeting
        img_id = f"mtf_img_{int(time.time() * 1000)}"
        original_h, original_w = processed_img.shape[:2]

        # Adaptive container dimensions based on image size
        # CRITICAL: Never scale images in psychophysical experiments - maintain 1:1 pixel ratio
        padding = 40
        display_width = original_w   # Always use original dimensions for accurate stimulus presentation
        display_height = original_h  # No scaling allowed in psychophysical experiments
        
        container_width = min(display_width + padding, 2000)  # Increased to accommodate 1600x1600 images
        container_height = min(display_height + padding, 2000)  # Must fit full-size images

        # Container style
        container_style = (
            f"text-align: center; "
            f"margin: 20px auto; "
            f"width: {container_width}px; "
            f"height: {container_height}px; "
            f"display: flex; "
            f"flex-direction: column; "
            f"align-items: center; "
            f"justify-content: center; "
            f"position: relative; "
            f"border: 1px solid #ddd; "
        )

        # Pixel-perfect image style - NEVER scale in psychophysical experiments
        image_style = (
            f"width: {display_width}px; "  # Original dimensions - no scaling allowed
            f"height: {display_height}px; "  # Original dimensions - no scaling allowed
            f"display: block; "
            f"-webkit-user-select: none; "
            f"-moz-user-select: none; "
            f"-ms-user-select: none; "
            f"user-select: none; "
        )
        
        # Pixel-perfect CSS - CRITICAL: 1:1 pixel ratio for psychophysical accuracy
        pixel_perfect_css = f"""
        <style>
        #{img_id} {{
            /* Pixel-perfect rendering settings - NO SCALING ALLOWED */
            image-rendering: pixelated !important;
            image-rendering: crisp-edges !important;
            image-rendering: -webkit-crisp-edges !important;
            image-rendering: -moz-crisp-edges !important;
            max-width: none !important;
            max-height: none !important;
            width: {display_width}px !important;  /* Original size - psychophysical accuracy */
            height: {display_height}px !important;  /* Original size - psychophysical accuracy */
            display: block !important;
            margin: 0 auto !important;
        }}
        /* Ensure parent container respects fixed size and prevents overlap */
        .stMarkdown > div > div:has(#{img_id}) {{
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            width: 100%;
            margin-bottom: 20px;
        }}
        /* Add spacing after image containers to prevent button overlap */
        div:has(#{img_id}) + * {{
            margin-top: 20px !important;
        }}
        </style>
        """
        
        html_content = f"""
        {pixel_perfect_css}
        <div style="{container_style}">
            <img id="{img_id}" src="data:image/png;base64,{img_str}" 
                 style="{image_style}"
                 draggable="false">
            <p style="margin: 10px 0; color: #666; font-size: 14px; text-align: center; position: absolute; bottom: 5px; width: 100%;">{caption}</p>
        </div>
        """
        
        # Display image with staged loading support
        if staged_loading and 'image_container' in st.session_state:
            # Replace placeholder with actual image
            st.session_state.image_container.markdown(html_content, unsafe_allow_html=True)
            logger.debug("🎬 Staged loading: Replaced placeholder with actual image")
        else:
            # Direct display without staging
            st.markdown(html_content, unsafe_allow_html=True)

        # Enhanced logging for pixel-perfect display
        logger.debug(f"🖼️ Pixel-perfect display: {original_w}x{original_h} (1:1 ratio) | Container: {container_width}x{container_height}")
        logger.debug(f"✨ Applied lossless rendering with NO scaling (psychophysical accuracy)")

        # Return container dimensions for button positioning
        return {
            'display_height': container_height,
            'center_position': container_height / 2,
            'original_width': original_w,
            'original_height': original_h,
            'display_width': display_width,  # Same as original - no scaling
            'display_height': display_height,  # Same as original - no scaling
            'container_width': container_width,
            'container_height': container_height,
            'pixel_perfect': True,  # Pixel-perfect 1:1 ratio maintained
            'lossless_encoding': True,  # No quality loss
            'no_scaling': True,  # Critical: No scaling applied for psychophysical accuracy
            'psychophysical_compliance': True  # Ensures experimental validity
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