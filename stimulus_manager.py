import os
import random
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
import librosa
import soundfile as sf
import streamlit as st
from typing import Dict, List, Optional, Tuple, Union
import base64
import io

class StimulusManager:
    """Manages creation and presentation of different stimulus types for 2AFC experiments"""
    
    def __init__(self):
        """Initialize the stimulus manager"""
        self.stimulus_cache = {}
        self.supported_types = ['visual_intensity', 'visual_size', 'visual_color', 'auditory_pitch', 'auditory_volume', 'video_speed']
        
    def generate_visual_stimulus(self, stimulus_type: str, intensity: float, size: Tuple[int, int] = (200, 200)) -> str:
        """
        Generate visual stimuli of different types
        
        Args:
            stimulus_type: Type of visual stimulus ('intensity', 'size', 'color', 'gabor', 'noise')
            intensity: Stimulus intensity/parameter value (0.0 to 1.0)
            size: Size of the stimulus in pixels
            
        Returns:
            Base64 encoded image string for HTML display
        """
        width, height = size
        
        if stimulus_type == 'visual_intensity':
            return self._generate_intensity_stimulus(intensity, width, height)
        elif stimulus_type == 'visual_size':
            return self._generate_size_stimulus(intensity, width, height)
        elif stimulus_type == 'visual_color':
            return self._generate_color_stimulus(intensity, width, height)
        elif stimulus_type == 'gabor':
            return self._generate_gabor_stimulus(intensity, width, height)
        elif stimulus_type == 'noise':
            return self._generate_noise_stimulus(intensity, width, height)
        else:
            return self._generate_intensity_stimulus(intensity, width, height)
    
    def _generate_intensity_stimulus(self, intensity: float, width: int, height: int) -> str:
        """Generate a grayscale circle with varying intensity"""
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Create circle in center
        margin = 20
        circle_size = min(width, height) - 2 * margin
        x1 = (width - circle_size) // 2
        y1 = (height - circle_size) // 2
        x2 = x1 + circle_size
        y2 = y1 + circle_size
        
        # Convert intensity to grayscale value (0 = black, 1 = light gray)
        gray_value = int(255 * (1 - intensity))
        color = (gray_value, gray_value, gray_value)
        
        draw.ellipse([x1, y1, x2, y2], fill=color, outline='gray')
        
        return self._image_to_base64(img)
    
    def _generate_size_stimulus(self, size_factor: float, width: int, height: int) -> str:
        """Generate a circle with varying size"""
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Size varies from 20% to 80% of container
        min_size = 0.2 * min(width, height)
        max_size = 0.8 * min(width, height)
        circle_size = int(min_size + size_factor * (max_size - min_size))
        
        x1 = (width - circle_size) // 2
        y1 = (height - circle_size) // 2
        x2 = x1 + circle_size
        y2 = y1 + circle_size
        
        draw.ellipse([x1, y1, x2, y2], fill='black', outline='gray')
        
        return self._image_to_base64(img)
    
    def _generate_color_stimulus(self, hue_factor: float, width: int, height: int) -> str:
        """Generate a colored circle with varying hue"""
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Convert hue factor to HSV color
        import colorsys
        hue = hue_factor  # 0 to 1
        saturation = 0.8
        value = 0.8
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        color = tuple(int(255 * c) for c in rgb)
        
        margin = 20
        circle_size = min(width, height) - 2 * margin
        x1 = (width - circle_size) // 2
        y1 = (height - circle_size) // 2
        x2 = x1 + circle_size
        y2 = y1 + circle_size
        
        draw.ellipse([x1, y1, x2, y2], fill=color, outline='gray')
        
        return self._image_to_base64(img)
    
    def _generate_gabor_stimulus(self, frequency: float, width: int, height: int) -> str:
        """Generate a Gabor patch stimulus"""
        # Create coordinate matrices
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        X, Y = np.meshgrid(x, y)
        
        # Gabor parameters
        sigma = 0.3
        freq = 2 + frequency * 8  # Frequency from 2 to 10
        
        # Generate Gabor patch
        gaussian = np.exp(-(X**2 + Y**2) / (2 * sigma**2))
        sinusoid = np.cos(2 * np.pi * freq * X)
        gabor = gaussian * sinusoid
        
        # Normalize to 0-255
        gabor = ((gabor + 1) / 2 * 255).astype(np.uint8)
        
        # Convert to PIL image
        img = Image.fromarray(gabor, mode='L').convert('RGB')
        
        return self._image_to_base64(img)
    
    def _generate_noise_stimulus(self, noise_level: float, width: int, height: int) -> str:
        """Generate a random noise stimulus"""
        # Generate random noise
        noise = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        
        # Apply noise level (0 = no noise, 1 = full noise)
        background = np.full((height, width, 3), 128, dtype=np.uint8)  # Gray background
        combined = (1 - noise_level) * background + noise_level * noise
        combined = combined.astype(np.uint8)
        
        img = Image.fromarray(combined)
        
        return self._image_to_base64(img)
    
    def generate_audio_stimulus(self, stimulus_type: str, parameter: float, duration: float = 1.0, sample_rate: int = 44100) -> bytes:
        """
        Generate audio stimuli of different types
        
        Args:
            stimulus_type: Type of audio stimulus ('pitch', 'volume', 'noise')
            parameter: Stimulus parameter value (0.0 to 1.0)
            duration: Duration in seconds
            sample_rate: Audio sample rate
            
        Returns:
            Audio data as bytes
        """
        if stimulus_type == 'auditory_pitch':
            return self._generate_pitch_stimulus(parameter, duration, sample_rate)
        elif stimulus_type == 'auditory_volume':
            return self._generate_volume_stimulus(parameter, duration, sample_rate)
        elif stimulus_type == 'noise':
            return self._generate_audio_noise_stimulus(parameter, duration, sample_rate)
        else:
            return self._generate_pitch_stimulus(parameter, duration, sample_rate)
    
    def _generate_pitch_stimulus(self, pitch_factor: float, duration: float, sample_rate: int) -> bytes:
        """Generate a sine wave with varying pitch"""
        # Frequency range from 200 Hz to 2000 Hz
        min_freq = 200
        max_freq = 2000
        frequency = min_freq + pitch_factor * (max_freq - min_freq)
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Apply fade in/out to avoid clicks
        fade_samples = int(0.01 * sample_rate)  # 10ms fade
        wave[:fade_samples] *= np.linspace(0, 1, fade_samples)
        wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        return self._audio_to_bytes(wave, sample_rate)
    
    def _generate_volume_stimulus(self, volume_factor: float, duration: float, sample_rate: int) -> bytes:
        """Generate a sine wave with varying volume"""
        frequency = 440  # A4 note
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = volume_factor * 0.5 * np.sin(2 * np.pi * frequency * t)
        
        # Apply fade in/out
        fade_samples = int(0.01 * sample_rate)
        wave[:fade_samples] *= np.linspace(0, 1, fade_samples)
        wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        return self._audio_to_bytes(wave, sample_rate)
    
    def _generate_audio_noise_stimulus(self, noise_level: float, duration: float, sample_rate: int) -> bytes:
        """Generate white noise with varying intensity"""
        # Generate white noise
        noise = np.random.normal(0, noise_level * 0.3, int(sample_rate * duration))
        
        # Apply fade in/out
        fade_samples = int(0.01 * sample_rate)
        noise[:fade_samples] *= np.linspace(0, 1, fade_samples)
        noise[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        return self._audio_to_bytes(noise, sample_rate)
    
    def generate_video_stimulus(self, stimulus_type: str, parameter: float, duration: float = 2.0) -> str:
        """
        Generate simple video stimuli (animated GIFs)
        
        Args:
            stimulus_type: Type of video stimulus ('speed', 'flicker')
            parameter: Stimulus parameter value (0.0 to 1.0)
            duration: Duration in seconds
            
        Returns:
            Base64 encoded GIF string
        """
        if stimulus_type == 'video_speed':
            return self._generate_speed_video(parameter, duration)
        elif stimulus_type == 'flicker':
            return self._generate_flicker_video(parameter, duration)
        else:
            return self._generate_speed_video(parameter, duration)
    
    def _generate_speed_video(self, speed_factor: float, duration: float) -> str:
        """Generate a moving circle with varying speed"""
        frames = []
        fps = 10
        total_frames = int(duration * fps)
        
        for frame_num in range(total_frames):
            img = Image.new('RGB', (200, 200), 'white')
            draw = ImageDraw.Draw(img)
            
            # Calculate circle position based on speed
            progress = (frame_num / total_frames) * speed_factor * 2  # Speed affects how far it moves
            x_pos = int(50 + progress * 100) % 150  # Circular motion
            y_pos = 100
            
            # Draw circle
            radius = 20
            draw.ellipse([x_pos-radius, y_pos-radius, x_pos+radius, y_pos+radius], 
                        fill='black', outline='gray')
            
            frames.append(img)
        
        return self._images_to_gif_base64(frames, duration=int(1000/fps))
    
    def _generate_flicker_video(self, flicker_rate: float, duration: float) -> str:
        """Generate a flickering circle with varying rate"""
        frames = []
        fps = 20
        total_frames = int(duration * fps)
        
        # Flicker rate from 1 Hz to 10 Hz
        freq = 1 + flicker_rate * 9
        
        for frame_num in range(total_frames):
            img = Image.new('RGB', (200, 200), 'white')
            draw = ImageDraw.Draw(img)
            
            # Calculate flicker state
            time_point = frame_num / fps
            intensity = (np.sin(2 * np.pi * freq * time_point) + 1) / 2
            
            # Draw circle with varying intensity
            gray_value = int(255 * (1 - intensity))
            color = (gray_value, gray_value, gray_value)
            
            draw.ellipse([75, 75, 125, 125], fill=color, outline='gray')
            
            frames.append(img)
        
        return self._images_to_gif_base64(frames, duration=int(1000/fps))
    
    def _image_to_base64(self, img: Image.Image) -> str:
        """Convert PIL image to base64 string"""
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    def _audio_to_bytes(self, audio_array: np.ndarray, sample_rate: int) -> bytes:
        """Convert numpy audio array to bytes"""
        buffer = io.BytesIO()
        sf.write(buffer, audio_array, sample_rate, format='WAV')
        return buffer.getvalue()
    
    def _images_to_gif_base64(self, images: List[Image.Image], duration: int = 100) -> str:
        """Convert list of PIL images to base64 GIF"""
        buffer = io.BytesIO()
        images[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=0
        )
        gif_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/gif;base64,{gif_str}"
    
    def create_trial_stimuli(self, stimulus_type: str, num_stimuli: int = 2) -> List[Dict]:
        """
        Create a set of stimuli for a trial
        
        Args:
            stimulus_type: Type of stimulus to generate
            num_stimuli: Number of stimuli to generate (typically 2 for 2AFC)
            
        Returns:
            List of stimulus dictionaries
        """
        stimuli = []
        
        for i in range(num_stimuli):
            # Generate random parameter values with some minimum difference
            if i == 0:
                parameter = random.uniform(0.2, 0.8)
            else:
                # Ensure minimum difference between stimuli
                min_diff = 0.1
                if stimuli[0]['parameter'] < 0.5:
                    parameter = random.uniform(stimuli[0]['parameter'] + min_diff, 1.0)
                else:
                    parameter = random.uniform(0.0, stimuli[0]['parameter'] - min_diff)
            
            stimulus = {
                'type': stimulus_type,
                'parameter': parameter,
                'position': i,  # 0 = left, 1 = right
            }
            
            # Generate the actual stimulus content based on type
            if stimulus_type.startswith('visual'):
                stimulus['content'] = self.generate_visual_stimulus(stimulus_type, parameter)
                stimulus['modality'] = 'visual'
            elif stimulus_type.startswith('auditory'):
                stimulus['content'] = self.generate_audio_stimulus(stimulus_type, parameter)
                stimulus['modality'] = 'auditory'
            elif stimulus_type.startswith('video'):
                stimulus['content'] = self.generate_video_stimulus(stimulus_type, parameter)
                stimulus['modality'] = 'video'
            
            stimuli.append(stimulus)
        
        return stimuli
    
    def get_available_stimulus_types(self) -> Dict[str, List[str]]:
        """Get all available stimulus types organized by modality"""
        return {
            'visual': [
                'visual_intensity',
                'visual_size', 
                'visual_color',
                'gabor',
                'noise'
            ],
            'auditory': [
                'auditory_pitch',
                'auditory_volume',
                'noise'
            ],
            'video': [
                'video_speed',
                'flicker'
            ]
        }