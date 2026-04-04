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
    
    FLASK_URL = os.getenv("FLASK_URL", "http://localhost:4200")
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

    def verify_grasshopper_with_heuristic(self, frame):
        """Second-pass shape/color guardrail to reduce false positive grasshopper alerts."""
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            lower_green = np.array([30, 40, 40])
            upper_green = np.array([90, 255, 255])
            mask_green = cv2.inRange(hsv, lower_green, upper_green)

            lower_brown = np.array([10, 40, 40])
            upper_brown = np.array([30, 255, 200])
            mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)

            lower_yellow = np.array([20, 40, 100])
            upper_yellow = np.array([40, 255, 255])
            mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

            mask = cv2.bitwise_or(mask_green, mask_brown)
            mask = cv2.bitwise_or(mask, mask_yellow)

            total_pixels = frame.shape[0] * frame.shape[1]
            if total_pixels <= 0:
                return False, 0.0

            color_pixels = cv2.countNonZero(mask)
            color_percentage = (color_pixels / total_pixels) * 100

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return False, 0.0

            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            if area < 500:
                return False, 0.0

            x, y, w, h = cv2.boundingRect(largest)
            if w <= 0 or h <= 0:
                return False, 0.0

            elongation = max(w / float(h), h / float(w))
            score = 0.0

            if elongation > 1.35:
                score += 0.45
            if 8 < color_percentage < 55:
                score += 0.30

            perimeter = cv2.arcLength(largest, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if 0.08 < circularity < 0.45:
                    score += 0.25

            return score >= 0.6, score
        except Exception:
            return False, 0.0
    
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

                is_target = class_name.lower() == Config.TARGET_CLASS.lower()
                if is_target:
                    heuristic_ok, heuristic_score = self.verify_grasshopper_with_heuristic(frame)
                    if not heuristic_ok:
                        # Keep a valid detection event but downgrade to non-grasshopper.
                        adjusted_conf = max(72.0, min(89.0, confidence * 0.80))
                        return {
                            'class': 'other_insect',
                            'confidence': adjusted_conf,
                            'is_grasshopper': False,
                            'raw_class': class_name,
                            'guardrail': f'heuristic_reject_{heuristic_score:.2f}'
                        }
                
                return {
                    'class': class_name,
                    'confidence': confidence,
                    'is_grasshopper': is_target
                }
            
            return None
        except Exception as e:
            print(f"⚠️ Detection error: {e}")
            return None
    
    def send_to_server(self, detection):
        """Send detection to Flask server"""
        try:
            payload = {
                'type': detection['class'],
                'confidence': detection['confidence'],
                'timestamp': datetime.now().isoformat()
            }
            response = requests.post(Config.DETECTION_API, json=payload, timeout=2)
            if response.status_code == 200:
                return True
            print(f"⚠️ Server returned status {response.status_code}")
            return False
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
