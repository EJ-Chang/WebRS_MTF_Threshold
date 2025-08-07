"""
GIF Animation component for fixation cross
Provides smooth animation without st.rerun() dependencies
"""
import streamlit as st
import base64
import os
import time
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

def show_gif_fixation_with_timer(duration: float = 3.0, show_progress: bool = True) -> None:
    """
    Display GIF-animated fixation cross with automatic timing
    
    This function uses pre-rendered GIF animations for the smoothest possible
    fixation cross display, completely independent of JavaScript or CSS.
    
    Args:
        duration: Fixation duration in seconds
        show_progress: Whether to show progress indicator
    """
    try:
        # Select appropriate GIF based on duration
        gif_mapping = {
            1.0: "fixation_cross_1s.gif",
            2.0: "fixation_cross_2s.gif", 
            3.0: "fixation_cross_3s.gif",
            5.0: "fixation_cross_5s.gif"
        }
        
        # Find closest duration
        available_durations = sorted(gif_mapping.keys())
        closest_duration = min(available_durations, key=lambda x: abs(x - duration))
        gif_filename = gif_mapping[closest_duration]
        
        # Path to GIF file
        gif_path = os.path.join("assets", "animations", gif_filename)
        
        if not os.path.exists(gif_path):
            logger.warning(f"GIF file not found: {gif_path}, falling back to CSS animation")
            from ui.components.progress_indicators import show_css_fixation_with_timer
            show_css_fixation_with_timer(duration, show_progress)
            return
        
        # Load and encode GIF
        with open(gif_path, "rb") as gif_file:
            gif_data = gif_file.read()
            gif_base64 = base64.b64encode(gif_data).decode()
        
        # Display GIF with container
        gif_html = f"""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: 350px;
            background: #f8f9fa;
            border-radius: 10px;
            margin: 20px 0;
            border: 2px solid #dee2e6;
        ">
            <img src="data:image/gif;base64,{gif_base64}" 
                 style="max-width: 100%; max-height: 100%; border-radius: 8px;"
                 alt="Fixation Cross Animation">
        </div>
        """
        
        # Generate unique ID for countdown (used in both HTML and JavaScript)
        countdown_id = f"countdown_{int(time.time() * 1000)}"
        
        if show_progress:
            gif_html += f"""
            <div style="text-align: center; margin: 10px 0; color: #666; font-size: 16px;">
                ⏱️ 固視點：<span id="{countdown_id}">0.0</span> 秒 (GIF 動畫)
            </div>
            """
        
        st.markdown(gif_html, unsafe_allow_html=True)
        
        logger.debug(f"🎬 Displayed GIF fixation animation: {gif_filename} (duration: {duration}s)")
        
        # Add JavaScript timer with dynamic countdown (same as CSS version)
        completion_js = f"""
        <script>
        // Dynamic countdown timer for GIF animation
        (function() {{
            var startTime = Date.now();
            var duration = {duration * 1000}; // Convert to milliseconds
            var countdownElement = document.getElementById('{countdown_id}');
            
            function updateCountdown() {{
                var elapsed = Date.now() - startTime;
                var remaining = Math.max(0, duration - elapsed);
                var remainingSeconds = remaining / 1000;
                
                if (countdownElement) {{
                    countdownElement.textContent = remainingSeconds.toFixed(1);
                    
                    // Color change as time runs out (same as CSS version)
                    if (remainingSeconds <= 1.0) {{
                        countdownElement.style.color = '#dc3545'; // Red for final second
                        countdownElement.style.fontWeight = 'bold';
                    }} else if (remainingSeconds <= 2.0) {{
                        countdownElement.style.color = '#fd7e14'; // Orange for warning
                    }} else {{
                        countdownElement.style.color = '#28a745'; // Green for normal
                    }}
                }}
                
                // Continue updating until complete
                if (remaining > 0) {{
                    setTimeout(updateCountdown, 100); // Update every 100ms
                }}
            }}
            
            // Start countdown immediately if progress is shown
            if (countdownElement) {{
                updateCountdown();
            }}
            
            // Mark fixation as completed when done
            setTimeout(function() {{
                sessionStorage.setItem('fixation_completed', 'true');
                sessionStorage.setItem('fixation_completion_time', Date.now());
                
                // Final countdown display
                if (countdownElement) {{
                    countdownElement.textContent = '0.0';
                    countdownElement.style.color = '#28a745';
                    countdownElement.style.fontWeight = 'bold';
                }}
            }}, {duration * 1000});
        }})();
        </script>
        """
        
        st.markdown(completion_js, unsafe_allow_html=True)
        
    except Exception as e:
        logger.error(f"Error displaying GIF fixation: {e}")
        # Fallback to CSS animation
        from ui.components.progress_indicators import show_css_fixation_with_timer
        show_css_fixation_with_timer(duration, show_progress)

def get_available_gif_durations() -> list:
    """Get list of available GIF animation durations"""
    try:
        animations_dir = os.path.join("assets", "animations")
        if not os.path.exists(animations_dir):
            return []
        
        durations = []
        for filename in os.listdir(animations_dir):
            if filename.startswith("fixation_cross_") and filename.endswith(".gif"):
                # Extract duration from filename (e.g., "fixation_cross_3s.gif" -> 3.0)
                duration_str = filename.replace("fixation_cross_", "").replace("s.gif", "")
                try:
                    duration = float(duration_str)
                    durations.append(duration)
                except ValueError:
                    continue
        
        return sorted(durations)
        
    except Exception as e:
        logger.error(f"Error getting available GIF durations: {e}")
        return []
