#!/usr/bin/env python3
"""
Real-Time Insect Detection with Camera
Integrates with Flask web server for notifications and LED control
"""

import os
import sys
import cv2
import numpy as np
import time
from datetime import datetime
import requests
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("⚠️ YOLO not available - install with: pip install ultralytics")
    YOLO_AVAILABLE = False

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    print("⚠️ TensorFlow not available - install with: pip install tensorflow")
    TF_AVAILABLE = False

# Configuration
class Config:
    MODEL_PATH = "/home/pi/pfa/models/yolo_best.pt"
    BACKUP_MODEL = "/home/pi/pfa/models/cnn_pest_best.h5"
    
    FLASK_URL = "http://localhost:5000"
    DETECTION_API = f"{FLASK_URL}/api/detection"
    
    TARGET_CLASS = "Grasshopper"
    CONFIDENCE_THRESHOLD = 0.70
    
    # Camera settings
    CAMERA_ID = 0  # 0 for USB camera, -1 for PiCamera
    IMG_SIZE = 224
    
    # Detection interval
    DETECTION_INTERVAL = 2  # seconds between detections


class RealTimeDetector:
    """Real-time insect detection system"""
    
    def __init__(self):
        self.model = None
        self.camera = None
        self.running = False
        self.class_names = []
        
    def load_model(self):
        """Load YOLO model"""
        if not os.path.exists(Config.MODEL_PATH):
            print(f"❌ Model not found: {Config.MODEL_PATH}")
            print("\n📥 Please add your YOLO model or download from Google Drive:")
            print("   1. Download your model from Google Drive")
            print("   2. Place it at: /home/pi/pfa/models/yolo_best.pt")
            return False
        
        if not YOLO_AVAILABLE:
            print("❌ YOLO not installed")
            return False
        
        try:
            print(f"🔄 Loading YOLO model from {Config.MODEL_PATH}...")
            self.model = YOLO(Config.MODEL_PATH)
            print("✅ Model loaded successfully")
            
            # Get class names
            self.class_names = list(self.model.names.values())
            print(f"📋 Classes: {', '.join(self.class_names)}")
            
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def init_camera(self):
        """Initialize camera"""
        try:
            print(f"📷 Initializing camera {Config.CAMERA_ID}...")
            self.camera = cv2.VideoCapture(Config.CAMERA_ID)
            
            if not self.camera.isOpened():
                print("❌ Could not open camera")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            print("✅ Camera initialized")
            return True
        except Exception as e:
            print(f"❌ Camera error: {e}")
            return False
    
    def capture_frame(self):
        """Capture a frame from camera"""
        if self.camera is None:
            return None
        
        ret, frame = self.camera.read()
        if not ret:
            print("⚠️ Failed to capture frame")
            return None
        
        return frame
    
    def detect(self, frame):
        """Run detection on frame"""
        if self.model is None:
            return None
        
        try:
            # Run inference
            results = self.model(frame, imgsz=Config.IMG_SIZE, device="cpu", verbose=False)
            
            if len(results) == 0:
                return None
            
            result = results[0]
            
            # Get prediction
            if hasattr(result, 'probs') and result.probs is not None:
                top1_idx = result.probs.top1
                confidence = float(result.probs.top1conf) * 100
                class_name = result.names[top1_idx]
                
                return {
                    'class': class_name,
                    'confidence': confidence,
                    'is_grasshopper': class_name.lower() == Config.TARGET_CLASS.lower()
                }
            
            return None
        except Exception as e:
            print(f"⚠️ Detection error: {e}")
            return None
    
    def send_to_server(self, detection):
        """Send detection to Flask server"""
        try:
            # Send via local function call to app.py
            from app import add_detection
            add_detection(
                insect_type=detection['class'],
                confidence=detection['confidence']
            )
            return True
        except Exception as e:
            print(f"⚠️ Could not send to server: {e}")
            return False
    
    def run(self):
        """Main detection loop"""
        print("\n" + "="*60)
        print("🦗 REAL-TIME INSECT DETECTION")
        print("="*60 + "\n")
        
        # Load model
        if not self.load_model():
            print("\n❌ Cannot start without model")
            return False
        
        # Initialize camera
        if not self.init_camera():
            print("\n❌ Cannot start without camera")
            return False
        
        self.running = True
        print("\n✅ Detection system started!")
        print(f"🎯 Target: {Config.TARGET_CLASS}")
        print(f"📊 Confidence threshold: {Config.CONFIDENCE_THRESHOLD*100}%")
        print(f"⏱️ Detection interval: {Config.DETECTION_INTERVAL}s")
        print("\n⚡ Press Ctrl+C to stop\n")
        print("="*60 + "\n")
        
        last_detection_time = 0
        
        try:
            while self.running:
                current_time = time.time()
                
                # Check if it's time for next detection
                if current_time - last_detection_time < Config.DETECTION_INTERVAL:
                    time.sleep(0.1)
                    continue
                
                # Capture frame
                frame = self.capture_frame()
                if frame is None:
                    continue
                
                # Run detection
                detection = self.detect(frame)
                
                if detection and detection['confidence'] >= Config.CONFIDENCE_THRESHOLD * 100:
                    # Valid detection
                    is_grasshopper = detection['is_grasshopper']
                    icon = "🦗" if is_grasshopper else "⚠️"
                    
                    print(f"{icon} Detected: {detection['class']} "
                          f"({detection['confidence']:.1f}% confidence)")
                    
                    # Send to server (triggers LEDs and web notification)
                    self.send_to_server(detection)
                    
                    last_detection_time = current_time
                
                # Small delay
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Stopping detection...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        
        if self.camera is not None:
            self.camera.release()
            print("✅ Camera released")
        
        print("✅ Detection stopped")


def simulate_detection():
    """
    Simulate detections for testing without camera/model
    Useful for testing web interface and LEDs
    """
    print("\n" + "="*60)
    print("🧪 SIMULATION MODE - Testing System")
    print("="*60 + "\n")
    
    from app import add_detection
    
    # Simulate different detections
    insects = [
        ('Grasshopper', 95.5, True),
        ('Aphid', 89.2, False),
        ('Grasshopper', 92.3, True),
        ('Beetle', 87.6, False),
        ('Grasshopper', 96.1, True),
    ]
    
    print("🔄 Simulating detections...\n")
    
    try:
        for i, (insect, conf, is_grass) in enumerate(insects, 1):
            icon = "🦗" if is_grass else "⚠️"
            print(f"{icon} [{i}/{len(insects)}] Detecting: {insect} ({conf}% confidence)")
            
            add_detection(insect, conf)
            
            print(f"   → LED: {'🟢 GREEN' if is_grass else '🔴 RED'}")
            print(f"   → Web notification sent\n")
            
            time.sleep(4)  # Wait for LED to finish
        
        print("✅ Simulation complete!")
        print("\n💡 Check the web interface at http://localhost:5000\n")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Simulation stopped")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-Time Insect Detection')
    parser.add_argument('--simulate', action='store_true', 
                       help='Run in simulation mode (no camera/model needed)')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device ID (default: 0)')
    parser.add_argument('--interval', type=float, default=2.0,
                       help='Detection interval in seconds (default: 2.0)')
    parser.add_argument('--threshold', type=float, default=0.70,
                       help='Confidence threshold (default: 0.70)')
    
    args = parser.parse_args()
    
    # Update config
    Config.CAMERA_ID = args.camera
    Config.DETECTION_INTERVAL = args.interval
    Config.CONFIDENCE_THRESHOLD = args.threshold
    
    if args.simulate:
        # Run simulation
        simulate_detection()
    else:
        # Run real detection
        detector = RealTimeDetector()
        detector.run()
