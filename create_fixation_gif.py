#!/usr/bin/env python3
"""
Create animated GIF for fixation cross
Generates high-quality rotating fixation cross with progress indicator
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import math

def create_fixation_cross_gif():
    """Create rotating fixation cross GIF with progress ring"""
    
    print("🎬 Creating Fixation Cross GIF Animation...")
    print("=" * 50)
    
    # Animation parameters
    duration = 3.0  # 3 seconds
    fps = 30  # 30 fps for smooth animation
    frames = int(duration * fps)  # 90 frames
    
    # Image dimensions
    size = 400
    center = size // 2
    
    # Create output directory
    assets_dir = "assets/animations"
    os.makedirs(assets_dir, exist_ok=True)
    
    frames_list = []
    
    print(f"📐 Animation settings:")
    print(f"   Duration: {duration}s")
    print(f"   FPS: {fps}")
    print(f"   Total frames: {frames}")
    print(f"   Image size: {size}x{size}")
    
    for frame in range(frames):
        # Calculate rotation angle and scale
        progress = frame / frames
        rotation_angle = progress * 360  # Full rotation
        
        # Pulsing scale effect (1.0 to 1.2)
        scale_factor = 1.0 + 0.2 * math.sin(progress * 8 * math.pi)  # 4 pulses per rotation
        
        # Create image with PIL
        img = Image.new('RGBA', (size, size), (240, 240, 240, 255))  # Light gray background
        draw = ImageDraw.Draw(img)
        
        # Draw progress ring
        ring_radius = 60
        ring_thickness = 6
        ring_progress_angle = progress * 360
        
        # Background ring (light gray)
        ring_bbox = [
            center - ring_radius, center - ring_radius,
            center + ring_radius, center + ring_radius
        ]
        draw.arc(ring_bbox, 0, 360, fill=(200, 200, 200), width=ring_thickness)
        
        # Progress ring (blue)
        if ring_progress_angle > 0:
            draw.arc(ring_bbox, -90, -90 + ring_progress_angle, fill=(0, 123, 255), width=ring_thickness)
        
        # Create fixation cross
        cross_size = int(40 * scale_factor)
        cross_thickness = int(8 * scale_factor)
        
        # Calculate rotated cross coordinates
        def rotate_point(x, y, angle, cx=center, cy=center):
            """Rotate point around center"""
            rad = math.radians(angle)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            
            # Translate to origin
            x -= cx
            y -= cy
            
            # Rotate
            new_x = x * cos_a - y * sin_a
            new_y = x * sin_a + y * cos_a
            
            # Translate back
            new_x += cx
            new_y += cy
            
            return new_x, new_y
        
        # Draw rotated cross
        # Horizontal bar
        h_points = [
            (center - cross_size, center - cross_thickness//2),
            (center + cross_size, center - cross_thickness//2), 
            (center + cross_size, center + cross_thickness//2),
            (center - cross_size, center + cross_thickness//2)
        ]
        
        # Vertical bar  
        v_points = [
            (center - cross_thickness//2, center - cross_size),
            (center + cross_thickness//2, center - cross_size),
            (center + cross_thickness//2, center + cross_size),
            (center - cross_thickness//2, center + cross_size)
        ]
        
        # Rotate points
        h_rotated = [rotate_point(x, y, rotation_angle) for x, y in h_points]
        v_rotated = [rotate_point(x, y, rotation_angle) for x, y in v_points]
        
        # Draw cross bars
        draw.polygon(h_rotated, fill=(51, 51, 51))  # Dark gray
        draw.polygon(v_rotated, fill=(51, 51, 51))
        
        # Add progress text
        progress_text = f"{progress*100:.1f}%"
        try:
            # Try to use a better font if available
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            font = ImageFont.load_default()
            
        # Get text bounding box for centering
        text_bbox = draw.textbbox((0, 0), progress_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        text_x = center - text_width // 2
        text_y = center + 100
        
        draw.text((text_x, text_y), progress_text, fill=(102, 102, 102), font=font)
        
        frames_list.append(img)
        
        # Progress indicator
        if frame % 10 == 0:
            print(f"   Frame {frame+1}/{frames} ({progress*100:.1f}%)")
    
    # Save as GIF
    output_path = os.path.join(assets_dir, "fixation_cross_3s.gif")
    
    print(f"\n💾 Saving GIF animation...")
    frames_list[0].save(
        output_path,
        save_all=True,
        append_images=frames_list[1:],
        duration=int(1000/fps),  # Duration per frame in milliseconds
        loop=0,  # Infinite loop
        optimize=True
    )
    
    file_size = os.path.getsize(output_path) / 1024  # KB
    print(f"✅ GIF created successfully!")
    print(f"   📁 Path: {output_path}")
    print(f"   📊 Size: {file_size:.1f} KB")
    print(f"   🎬 Duration: {duration}s")
    print(f"   🖼️ Frames: {frames}")
    
    return output_path

def create_multiple_duration_gifs():
    """Create GIFs with different durations for flexibility"""
    
    durations = [1.0, 2.0, 3.0, 5.0]
    created_files = []
    
    print("\n🎯 Creating Multiple Duration GIFs...")
    print("=" * 40)
    
    for duration in durations:
        print(f"\n⏱️ Creating {duration}s version...")
        
        fps = 30
        frames = int(duration * fps)
        size = 300  # Smaller size for multiple files
        center = size // 2
        
        frames_list = []
        
        for frame in range(frames):
            progress = frame / frames
            rotation_angle = progress * 360
            scale_factor = 1.0 + 0.15 * math.sin(progress * 6 * math.pi)
            
            # Create simplified version
            img = Image.new('RGBA', (size, size), (245, 245, 245, 255))
            draw = ImageDraw.Draw(img)
            
            # Simple progress ring
            ring_radius = 45
            ring_progress = progress * 360
            
            if ring_progress > 0:
                ring_bbox = [center-ring_radius, center-ring_radius, center+ring_radius, center+ring_radius]
                draw.arc(ring_bbox, -90, -90 + ring_progress, fill=(0, 123, 255), width=4)
            
            # Simple cross
            cross_size = int(25 * scale_factor)
            cross_thick = int(5 * scale_factor)
            
            # Rotated cross (simplified calculation)
            rad = math.radians(rotation_angle)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            
            # Cross arms
            arm1_x = cross_size * cos_a
            arm1_y = cross_size * sin_a
            arm2_x = cross_size * -sin_a  
            arm2_y = cross_size * cos_a
            
            # Draw cross lines
            draw.line([(center-arm1_x, center-arm1_y), (center+arm1_x, center+arm1_y)], fill=(51, 51, 51), width=cross_thick)
            draw.line([(center-arm2_x, center-arm2_y), (center+arm2_x, center+arm2_y)], fill=(51, 51, 51), width=cross_thick)
            
            frames_list.append(img)
        
        # Save GIF
        assets_dir = "assets/animations"
        output_path = os.path.join(assets_dir, f"fixation_cross_{duration:.0f}s.gif")
        
        frames_list[0].save(
            output_path,
            save_all=True,
            append_images=frames_list[1:],
            duration=int(1000/fps),
            loop=0,
            optimize=True
        )
        
        file_size = os.path.getsize(output_path) / 1024
        print(f"   ✅ Created: {output_path} ({file_size:.1f} KB)")
        created_files.append(output_path)
    
    return created_files

def create_gif_display_component():
    """Create component for displaying GIF animations in Streamlit"""
    
    component_code = '''"""
GIF Animation component for fixation cross
Provides smooth animation without st.rerun() dependencies
"""
import streamlit as st
import base64
import os
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
        
        if show_progress:
            gif_html += f"""
            <div style="text-align: center; margin: 10px 0; color: #666; font-size: 16px;">
                ⏱️ 固視點：{duration:.1f} 秒 (GIF 動畫)
            </div>
            """
        
        st.markdown(gif_html, unsafe_allow_html=True)
        
        logger.debug(f"🎬 Displayed GIF fixation animation: {gif_filename} (duration: {duration}s)")
        
        # Add JavaScript timer for completion detection (same as CSS version)
        completion_js = f"""
        <script>
        setTimeout(function() {{
            sessionStorage.setItem('fixation_completed', 'true');
            sessionStorage.setItem('fixation_completion_time', Date.now());
        }}, {duration * 1000});
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
'''
    
    # Save component
    component_path = "ui/components/gif_animations.py"
    os.makedirs(os.path.dirname(component_path), exist_ok=True)
    
    with open(component_path, 'w', encoding='utf-8') as f:
        f.write(component_code)
    
    print(f"✅ GIF animation component created: {component_path}")
    return component_path

if __name__ == "__main__":
    print("🎬 Fixation Cross GIF Generator")
    print("=" * 40)
    
    # Create main GIF
    main_gif = create_fixation_cross_gif()
    
    # Create multiple durations
    multiple_gifs = create_multiple_duration_gifs()
    
    # Create Streamlit component
    component_path = create_gif_display_component()
    
    print(f"\n🎉 GIF Animation System Created Successfully!")
    print(f"📁 Main GIF: {main_gif}")
    print(f"📁 Additional GIFs: {len(multiple_gifs)} files")
    print(f"🧩 Component: {component_path}")
    
    print(f"\n💡 Usage Instructions:")
    print(f"   1. Import: from ui.components.gif_animations import show_gif_fixation_with_timer")
    print(f"   2. Use: show_gif_fixation_with_timer(duration=3.0)")
    print(f"   3. Benefit: Zero CPU usage during animation, perfect smoothness")
    
    total_size = sum(os.path.getsize(f) for f in [main_gif] + multiple_gifs) / 1024
    print(f"📊 Total size: {total_size:.1f} KB")