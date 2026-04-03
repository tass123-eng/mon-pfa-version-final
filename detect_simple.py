#!/usr/bin/env python3
"""
Simple Insect Detection using Pretrained Model
No training required - works immediately!
"""

import cv2
import numpy as np
import requests
import time
from datetime import datetime

# Configuration
MODEL_PATH = "models/yolo_pretrained.pt"
TARGET_CLASS = "grasshopper"
CONFIDENCE_THRESHOLD = 0.5
FLASK_URL = "http://localhost:5000"

# Try to import YOLO - DISABLED for speed (ultralytics takes too long to load on Pi)
YOLO_AVAILABLE = False
# try:
#     from ultralytics import YOLO
#     YOLO_AVAILABLE = True
# except ImportError:
#     YOLO_AVAILABLE = False
#     print("⚠️ YOLO not installed. Install with: pip3 install ultralytics")

class SimpleInsectDetector:
    """
    Simple detector using pretrained YOLO + color/shape analysis
    Works without training!
    """
    
    def __init__(self, use_camera=False, simulate=False):
        self.use_camera = use_camera
        self.simulate = simulate
        self.model = None
        self.running = False
        
        if YOLO_AVAILABLE and not simulate:
            self.load_model()
        else:
            print("🧪 Running in simulation mode")
    
    def load_model(self):
        """Load pretrained YOLO model"""
        try:
            import os
            if os.path.exists(MODEL_PATH):
                print(f"📥 Loading model from {MODEL_PATH}")
                self.model = YOLO(MODEL_PATH)
            else:
                # Download default YOLOv8n
                print("📥 Downloading YOLOv8 Nano (~6MB)...")
                self.model = YOLO('yolov8n.pt')
                # Save for future use
                os.makedirs('models', exist_ok=True)
                self.model.save(MODEL_PATH)
                print(f"✅ Model saved to {MODEL_PATH}")
        except Exception as e:
            print(f"⚠️ Model loading failed: {e}")
            self.model = None
    
    def detect_with_yolo(self, image):
        """Detect insects using YOLO model"""
        if self.model is None:
            return None, 0.0
        
        try:
            results = self.model(image, conf=CONFIDENCE_THRESHOLD, verbose=False)
            
            # Check if anything detected
            if len(results[0].boxes) > 0:
                # Get first detection
                box = results[0].boxes[0]
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = results[0].names[class_id]
                
                # Simple classification: if it's small and detected, it's an insect
                # You can customize this logic
                return class_name, confidence
            
            return None, 0.0
        except Exception as e:
            print(f"⚠️ Detection error: {e}")
            return None, 0.0
    
    def detect_with_color_shape(self, image):
        """
        Simple detection using color and shape analysis
        No ML model needed!
        """
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for grasshoppers (green/brown)
        # Green range
        lower_green = np.array([30, 40, 40])
        upper_green = np.array([90, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        
        # Brown range
        lower_brown = np.array([10, 40, 40])
        upper_brown = np.array([30, 255, 200])
        mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)
        
        # Combine masks
        mask = cv2.bitwise_or(mask_green, mask_brown)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 0:
            # Get largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            # If area is significant, consider it an insect
            if area > 500:  # Minimum area threshold
                # Analyze shape to determine if grasshopper
                x, y, w, h = cv2.boundingRect(largest_contour)
                aspect_ratio = w / float(h) if h > 0 else 0
                
                # Grasshoppers typically have elongated shape (aspect ratio > 1.5)
                if aspect_ratio > 1.5:
                    confidence = min(0.95, area / 10000)  # Higher confidence for larger area
                    return "grasshopper", confidence
                else:
                    confidence = min(0.85, area / 10000)
                    return "other_insect", confidence
        
        return None, 0.0
    
    def detect(self, image=None):
        """
        Main detection function
        Uses YOLO if available, falls back to color/shape analysis
        """
        if self.simulate:
            # Simulation mode - generate random detections
            import random
            insects = ["grasshopper", "aphid", "beetle", "moth"]
            insect_type = random.choice(insects)
            confidence = random.uniform(0.75, 0.98)
            return insect_type, confidence
        
        if image is None:
            return None, 0.0
        
        # Try YOLO first
        if self.model is not None:
            result, confidence = self.detect_with_yolo(image)
            if result is not None:
                return result, confidence
        
        # Fall back to color/shape analysis
        return self.detect_with_color_shape(image)
    
    def send_to_server(self, insect_type, confidence):
        """Send detection to Flask server"""
        try:
            data = {
                'type': insect_type,
                'confidence': confidence * 100,  # Convert to percentage
                'timestamp': datetime.now().isoformat()
            }
            
            # Add detection via Flask API
            response = requests.post(
                f"{FLASK_URL}/api/detection",
                json=data,
                timeout=2
            )
            
            if response.status_code == 200:
                print(f"✅ Sent to server: {insect_type} ({confidence*100:.1f}%)")
            else:
                print(f"⚠️ Server error: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Failed to send to server: {e}")
    
    def run(self):
        """Main detection loop"""
        self.running = True
        
        print("\n" + "="*60)
        print("🦗 SIMPLE INSECT DETECTOR")
        print("="*60)
        print(f"🔧 Mode: {'Simulation' if self.simulate else 'Real'}")
        print(f"📹 Camera: {'Yes' if self.use_camera else 'No'}")
        print(f"🤖 YOLO: {'Yes' if self.model else 'Color/Shape Analysis'}")
        print(f"🎯 Target: {TARGET_CLASS}")
        print("="*60 + "\n")
        
        try:
            if self.use_camera:
                self.run_with_camera()
            else:
                self.run_simulation()
        except KeyboardInterrupt:
            print("\n\n⚠️ Stopped by user")
        finally:
            self.running = False
    
    def run_with_camera(self):
        """Run detection with camera"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot open camera")
            return
        
        print("📹 Camera started. Press 'q' to quit\n")
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ Cannot read frame")
                break
            
            # Detect
            insect_type, confidence = self.detect(frame)
            
            if insect_type is not None:
                print(f"🦗 Detected: {insect_type} ({confidence*100:.1f}% confidence)")
                self.send_to_server(insect_type, confidence)
            
            time.sleep(2)  # Check every 2 seconds
        
        cap.release()
    
    def run_simulation(self):
        """Run simulation without camera"""
        print("🧪 Running simulation...\n")
        
        for i in range(10):
            if not self.running:
                break
            
            # Simulate detection
            insect_type, confidence = self.detect()
            
            if insect_type is not None:
                emoji = "🦗" if insect_type == "grasshopper" else "⚠️"
                print(f"{emoji} [{i+1}/10] Detected: {insect_type} ({confidence*100:.1f}% confidence)")
                self.send_to_server(insect_type, confidence)
            
            time.sleep(3)
        
        print("\n✅ Simulation complete!")

if __name__ == '__main__':
    import sys
    
    # Parse arguments
    simulate = '--simulate' in sys.argv
    use_camera = '--camera' in sys.argv
    
    # Create detector
    detector = SimpleInsectDetector(use_camera=use_camera, simulate=simulate)
    
    # Run
    detector.run()
