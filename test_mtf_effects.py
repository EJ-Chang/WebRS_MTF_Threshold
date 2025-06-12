#!/usr/bin/env python3
"""
Test script to verify MTF effects are working correctly
"""

import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt

def apply_mtf_to_image(image, mtf_percent):
    """Enhanced MTF implementation with more noticeable effects"""
    # More aggressive MTF mapping for clearer perceptual differences
    if mtf_percent >= 90:
        sigma = 0.5  # Minimal blur for high MTF
    elif mtf_percent >= 70:
        sigma = 1.5 + (90 - mtf_percent) * 0.2  # Gradual increase
    elif mtf_percent >= 50:
        sigma = 5.5 + (70 - mtf_percent) * 0.3  # More noticeable blur
    elif mtf_percent >= 30:
        sigma = 11.5 + (50 - mtf_percent) * 0.4  # Strong blur
    else:
        sigma = 19.5 + (30 - mtf_percent) * 0.5  # Very strong blur
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=sigma, sigmaY=sigma)
    
    print(f"Applied MTF {mtf_percent:.1f}% with sigma={sigma:.2f}")
    return blurred, sigma

def create_test_pattern():
    """Create a high-contrast checkerboard pattern"""
    pattern_size = 800
    checker_size = 20
    pattern = np.zeros((pattern_size, pattern_size), dtype=np.uint8)
    
    # Vectorized checkerboard creation
    x, y = np.meshgrid(np.arange(pattern_size), np.arange(pattern_size))
    checker_mask = ((x // checker_size) + (y // checker_size)) % 2 == 0
    pattern[checker_mask] = 255
    
    # Convert to RGB
    pattern_rgb = np.stack([pattern, pattern, pattern], axis=-1)
    return pattern_rgb

def test_mtf_range():
    """Test MTF effects across different values"""
    # Create test pattern
    test_pattern = create_test_pattern()
    
    # Test different MTF values
    mtf_values = [90, 70, 50, 30, 10]
    results = []
    
    for mtf in mtf_values:
        blurred, sigma = apply_mtf_to_image(test_pattern, mtf)
        results.append((mtf, blurred, sigma))
        
        # Calculate image metrics
        original_std = np.std(test_pattern)
        blurred_std = np.std(blurred)
        blur_ratio = blurred_std / original_std
        
        print(f"MTF {mtf}%: σ={sigma:.2f}, std_ratio={blur_ratio:.3f}")
    
    return results

if __name__ == "__main__":
    print("Testing MTF effects...")
    results = test_mtf_range()
    
    print("\nMTF Test Results:")
    print("MTF% | Sigma | Effect")
    print("-----|-------|-------")
    for mtf, _, sigma in results:
        if sigma < 1:
            effect = "Minimal"
        elif sigma < 5:
            effect = "Light"
        elif sigma < 10:
            effect = "Moderate"
        elif sigma < 15:
            effect = "Strong"
        else:
            effect = "Very Strong"
        print(f"{mtf:3d}% | {sigma:5.2f} | {effect}")
    
    print("\nMTF effects test completed!")