#!/usr/bin/env python3
"""
Analyze specific images for insect detection
Uses color and shape analysis
"""

import cv2
import numpy as np
import requests
import sys
from datetime import datetime

# Configuration
FLASK_URL = "http://localhost:5000"
TARGET_CLASS = "grasshopper"

def analyze_color_shape(image_path):
    """
    Analyze image using color and shape detection
    No ML model needed!
    """
    print(f"\n{'='*60}")
    print(f"🔍 Analyzing: {image_path}")
    print('='*60)
    
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not read image: {image_path}")
        return None, 0.0
    
    print(f"📐 Image size: {image.shape[1]}x{image.shape[0]} pixels")
    
    # Convert to HSV for better color analysis
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Define color ranges for grasshoppers (green/brown)
    # Green range (grasshoppers are often green)
    lower_green = np.array([30, 40, 40])
    upper_green = np.array([90, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    
    # Brown range (some grasshoppers are brown)
    lower_brown = np.array([10, 40, 40])
    upper_brown = np.array([30, 255, 200])
    mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)
    
    # Yellow/tan range (common grasshopper color)
    lower_yellow = np.array([20, 40, 100])
    upper_yellow = np.array([40, 255, 255])
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # Combine all masks
    mask = cv2.bitwise_or(mask_green, mask_brown)
    mask = cv2.bitwise_or(mask, mask_yellow)
    
    # Calculate color coverage
    total_pixels = image.shape[0] * image.shape[1]
    color_pixels = cv2.countNonZero(mask)
    color_percentage = (color_pixels / total_pixels) * 100
    
    print(f"🎨 Color Analysis:")
    print(f"   Green/Brown/Yellow coverage: {color_percentage:.1f}%")
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) == 0:
        print(f"⚠️  No significant green/brown regions found")
        return "other_insect", 0.3
    
    # Get largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_contour)
    area_percentage = (area / total_pixels) * 100
    
    print(f"📏 Shape Analysis:")
    print(f"   Largest region: {area_percentage:.1f}% of image")
    
    if area < 500:
        print(f"   ⚠️  Region too small")
        return "other_insect", 0.4
    
    # Analyze shape to determine if grasshopper
    x, y, w, h = cv2.boundingRect(largest_contour)
    aspect_ratio = w / float(h) if h > 0 else 0
    
    print(f"   Aspect ratio: {aspect_ratio:.2f}")
    print(f"   Width: {w}px, Height: {h}px")
    
    # Grasshopper characteristics:
    # - MUST have elongated body (aspect ratio > 1.5 for horizontal grasshoppers)
    # - Green, brown, or yellow color (but not too much - could be background)
    # - Specific shape: long and thin, not round or compact
    
    confidence = 0.3  # Base confidence - start skeptical
    insect_type = "other_insect"
    
    # Check for grasshopper characteristics
    grasshopper_indicators = []
    non_grasshopper_indicators = []
    
    # CRITICAL: Aspect ratio (grasshoppers are elongated)
    if aspect_ratio > 1.5:  # Strong elongation = likely grasshopper
        confidence += 0.25
        grasshopper_indicators.append("strongly elongated")
    elif aspect_ratio > 1.2:
        confidence += 0.10
        grasshopper_indicators.append("somewhat elongated")
    elif aspect_ratio < 0.9:  # Vertical orientation - likely not grasshopper
        confidence -= 0.2
        non_grasshopper_indicators.append("vertical/compact shape")
    
    # Color check (but be careful - too much color might be background)
    if 10 < color_percentage < 50:  # Sweet spot for grasshopper
        confidence += 0.20
        grasshopper_indicators.append("appropriate color amount")
    elif color_percentage > 70:  # Too much = probably background
        confidence -= 0.15
        non_grasshopper_indicators.append("too much background color")
    
    # Size check
    if 10 < area_percentage < 70:  # Good subject size
        confidence += 0.10
        grasshopper_indicators.append("good subject size")
    
    # Additional shape analysis
    perimeter = cv2.arcLength(largest_contour, True)
    if perimeter > 0:
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        print(f"   Circularity: {circularity:.2f} (0=line, 1=circle)")
        
        # Grasshoppers are elongated, not circular
        if 0.1 < circularity < 0.4:  # Very elongated
            confidence += 0.15
            grasshopper_indicators.append("elongated body shape")
        elif circularity > 0.6:  # Too round = not grasshopper
            confidence -= 0.2
            non_grasshopper_indicators.append("too round/compact")
    
    # Final classification - BE STRICT
    # Need strong elongation AND good indicators
    if aspect_ratio > 1.5 and confidence > 0.7 and len(grasshopper_indicators) >= 3:
        insect_type = "grasshopper"
        confidence = min(0.92, confidence)
    else:
        insect_type = "other_insect"
        confidence = min(0.88, 0.6 + (len(non_grasshopper_indicators) * 0.1))
    
    if non_grasshopper_indicators:
        print(f"   Non-grasshopper signs: {', '.join(non_grasshopper_indicators)}")
    
    print(f"\n🎯 Detection Result:")
    print(f"   Type: {insect_type.upper()}")
    print(f"   Confidence: {confidence*100:.1f}%")
    
    if grasshopper_indicators:
        print(f"   Indicators: {', '.join(grasshopper_indicators)}")
    
    return insect_type, confidence

def send_to_server(insect_type, confidence, image_path):
    """Send detection to Flask server"""
    try:
        data = {
            'type': insect_type,
            'confidence': confidence * 100,
            'timestamp': datetime.now().isoformat(),
            'image': image_path
        }
        
        response = requests.post(
            f"{FLASK_URL}/api/detection",
            json=data,
            timeout=2
        )
        
        if response.status_code == 200:
            print(f"✅ Sent to web interface")
            return True
        else:
            print(f"⚠️  Server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Failed to send to server: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🦗 INSECT IMAGE ANALYSIS")
    print("="*60)
    print("Using: Color & Shape Detection (No ML required)")
    print()
    
    # Analyze images
    if len(sys.argv) > 1:
        # Use command-line argument if provided
        images = sys.argv[1:]
    else:
        # Default images
        images = ["1.jpg", "2.jpg"]
    
    for img_path in images:
        insect_type, confidence = analyze_color_shape(img_path)
        
        if insect_type:
            # Send to server
            send_to_server(insect_type, confidence, img_path)
            
            # Show emoji
            if insect_type == "grasshopper":
                emoji = "🦗"
                led_color = "GREEN"
            else:
                emoji = "⚠️"
                led_color = "RED"
            
            print(f"\n{emoji} Result: {insect_type} ({confidence*100:.1f}%)")
            print(f"💡 [SIMULATED] {led_color} LED activated")
        
        print()
    
    print("="*60)
    print("✅ Analysis complete!")
    print(f"📱 View results at: {FLASK_URL}")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
