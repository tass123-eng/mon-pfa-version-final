#!/usr/bin/env python3
"""
Flask Web Server for Real-Time Insect Detection
Handles web interface, notifications, and GPIO LED control
"""

from flask import Flask, render_template, jsonify, request, redirect
from flask import send_from_directory
from flask_socketio import SocketIO, emit
import threading
import time
import os
import re
import unicodedata
from datetime import datetime
import json
import cv2
import numpy as np

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

# Try to import RPi.GPIO, fallback to mock for testing
# DISABLED: Electronic components not installed yet
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = False  # Force mock mode - no hardware yet
except ImportError:
    print("⚠️ RPi.GPIO not available, using mock GPIO")
    GPIO_AVAILABLE = False
    class GPIO:
        BCM = 'BCM'
        OUT = 'OUT'
        HIGH = 1
        LOW = 0
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode, initial=0): pass
        @staticmethod
        def output(pin, state): pass
        @staticmethod
        def cleanup(): pass

from flask_cors import CORS
# Flask app setup
app = Flask(
    __name__,
    static_folder="SmartAgriCom with html+css+js - Copie",  # Sert le frontend depuis ce dossier
    static_url_path=''
)
app.config['SECRET_KEY'] = 'insect_detection_secret_2026'
CORS(app)  # Autorise les requêtes cross-origin si besoin
socketio = SocketIO(app, cors_allowed_origins="*")

# GPIO Pin Configuration
GREEN_LED_PIN = 17  # GPIO 17 for grasshopper (safe)
RED_LED_PIN = 27    # GPIO 27 for other insects (danger)
BUZZER_PIN = 23     # GPIO 23 for buzzer alert

# Detection state
detection_state = {
    'running': False,
    'last_detection': None,
    'total_detections': 0,
    'grasshopper_count': 0,
    'other_insects_count': 0,
    'history': []
}

MODEL_CANDIDATES = [
    os.path.join('models', 'yolov8n.pt'),
    os.path.join('models', 'mixage.pt')
]
MODEL_PATH = MODEL_CANDIDATES[0]
ai_model = None
model_load_error = None
active_model_path = None
TARGET_CLASS = 'Grasshopper'
CONF_THRESHOLD_PERCENT = 70.0
GUARDRAIL_ENABLED = True
GUARDRAIL_MAX_AI_CONF_FOR_OVERRIDE = 97.0
GUARDRAIL_MIN_HEURISTIC_NON_CONF = 60.0


def load_ai_model():
    """Load YOLO model once and cache it for subsequent requests."""
    global ai_model, model_load_error, active_model_path

    if ai_model is not None:
        return ai_model

    if not YOLO_AVAILABLE:
        model_load_error = 'ultralytics is not installed'
        return None

    model_path = next((path for path in MODEL_CANDIDATES if os.path.exists(path)), None)
    if model_path is None:
        model_load_error = f'model not found. Tried: {MODEL_CANDIDATES}'
        return None

    try:
        ai_model = YOLO(model_path)
        active_model_path = model_path
        print(f"✅ AI model loaded: {model_path}")
        return ai_model
    except Exception as e:
        model_load_error = f'failed to load model: {e}'
        return None


def predict_with_ai_model(image):
    """Run YOLO prediction and return normalized tuple (label, confidence%)."""
    model = load_ai_model()
    if model is None:
        return None

    results = model(image, verbose=False)
    if not results:
        return None

    result = results[0]

    # Classification model path
    if hasattr(result, 'probs') and result.probs is not None:
        top1 = int(result.probs.top1)
        confidence = float(result.probs.top1conf) * 100
        class_name = result.names[top1] if top1 in result.names else str(top1)
        return class_name, round(confidence, 1)

    # Detection model path
    if hasattr(result, 'boxes') and result.boxes is not None and len(result.boxes) > 0:
        conf_values = result.boxes.conf.tolist()
        cls_values = result.boxes.cls.tolist()
        best_idx = int(np.argmax(conf_values))

        confidence = float(conf_values[best_idx]) * 100
        class_id = int(cls_values[best_idx])
        class_name = result.names[class_id] if class_id in result.names else str(class_id)
        return class_name, round(confidence, 1)

    return None


def is_target_grasshopper_prediction(pred_class, confidence):
    """Apply the same rule used in pfa_mixage scripts."""
    if pred_class is None:
        return False

    same_class = str(pred_class).strip().lower() == TARGET_CLASS.lower()
    return same_class and float(confidence) >= CONF_THRESHOLD_PERCENT


def is_grasshopper_label(insect_type):
    """Normalize label variants and decide if detection is a grasshopper."""
    if insect_type is None:
        return False

    raw_value = str(insect_type).strip().lower()
    ascii_value = unicodedata.normalize('NFKD', raw_value).encode('ascii', 'ignore').decode('ascii')
    normalized = ascii_value.replace('-', '_').replace(' ', '_')

    # Always treat negation forms as non-grasshopper first.
    if re.search(r'(^|_)(non|not|no|sans|other|autre|autres)(_|$)', normalized):
        if any(keyword in normalized for keyword in ('grasshopper', 'criquet', 'locust', 'orthoptera')):
            return False

    if any(token in normalized for token in ('noncriquet', 'non_criquet', 'notcriquet', 'not_criquet')):
        return False

    grasshopper_aliases = {
        'grasshopper',
        'grass_hopper',
        'criquet',
        'criquets',
        'locust',
        'locusta_migratoria',
        'orthoptera'
    }
    other_aliases = {
        'other',
        'other_insect',
        'other_insects',
        'autre_insecte',
        'autres_insecte',
        'autres_insectes',
        'not_grasshopper',
        'non_grasshopper',
        'non_criquet',
        'pas_criquet',
        'not_criquet'
    }

    if normalized in grasshopper_aliases:
        return True
    if normalized in other_aliases:
        return False

    # Fallback: positive keywords only if no explicit negation signal.
    if any(keyword in normalized for keyword in ('grasshopper', 'criquet', 'locust', 'orthoptera')):
        return True

    return False


def analyze_uploaded_image(image):
    """Analyze uploaded image with color/shape heuristic and return (label, confidence%)."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

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

    total_pixels = image.shape[0] * image.shape[1]
    color_pixels = cv2.countNonZero(mask)
    color_percentage = (color_pixels / total_pixels) * 100 if total_pixels > 0 else 0

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return "other_insect", 35.0

    largest_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_contour)
    area_percentage = (area / total_pixels) * 100 if total_pixels > 0 else 0

    if area < 500:
        return "other_insect", 40.0

    x, y, w, h = cv2.boundingRect(largest_contour)
    aspect_ratio = w / float(h) if h > 0 else 0
    inverse_aspect_ratio = h / float(w) if w > 0 else 0
    elongation_ratio = max(aspect_ratio, inverse_aspect_ratio)

    confidence = 0.3
    grasshopper_indicators = 0
    non_grasshopper_indicators = 0

    # Use orientation-invariant elongation to avoid missing vertical/inclined grasshoppers.
    if elongation_ratio > 1.5:
        confidence += 0.25
        grasshopper_indicators += 1
    elif elongation_ratio > 1.25:
        confidence += 0.10
        grasshopper_indicators += 1
    elif elongation_ratio < 1.05:
        confidence -= 0.15
        non_grasshopper_indicators += 1

    if 10 < color_percentage < 50:
        confidence += 0.2
        grasshopper_indicators += 1
    elif color_percentage > 70:
        confidence -= 0.15
        non_grasshopper_indicators += 1

    if 10 < area_percentage < 70:
        confidence += 0.1
        grasshopper_indicators += 1

    perimeter = cv2.arcLength(largest_contour, True)
    if perimeter > 0:
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        if 0.1 < circularity < 0.4:
            confidence += 0.15
            grasshopper_indicators += 1
        elif circularity > 0.6:
            confidence -= 0.2
            non_grasshopper_indicators += 1

    # More robust decision rule for real photos (angle, crop, and background variability).
    if elongation_ratio > 1.35 and confidence >= 0.6 and grasshopper_indicators >= 2:
        return "grasshopper", round(min(0.92, confidence) * 100, 1)

    # Avoid overconfident negative predictions when features are ambiguous.
    normalized_conf = round(min(0.82, max(0.45, 0.52 + (non_grasshopper_indicators * 0.08))) * 100, 1)
    return "other_insect", normalized_conf

# Initialize GPIO
def init_gpio():
    """Initialize GPIO pins for LED control"""
    # DISABLED: Electronic components not installed yet
    if GPIO_AVAILABLE:
         try:
             GPIO.cleanup()  # Clean up any previous usage
             GPIO.setwarnings(False)
             GPIO.setmode(GPIO.BCM)
             GPIO.setup(GREEN_LED_PIN, GPIO.OUT, initial=GPIO.LOW)
             GPIO.setup(RED_LED_PIN, GPIO.OUT, initial=GPIO.LOW)
             GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)
             print("✅ GPIO initialized - LEDs and Buzzer ready")
         except Exception as e:
             print(f"⚠️ GPIO initialization error: {e}")
    else:
        print("⚠️ GPIO mock mode - Electronic components not installed yet")

def control_leds_and_buzzer(insect_type):
    """
    Control LEDs and Buzzer based on insect type
    Cricket detected: Red LED ON + Buzzer alert (3 beeps)
    Other insect: Green LED ON + No sound
    """
    def led_buzzer_thread():
        try:
            if is_grasshopper_label(insect_type):
                # Cricket detected - Green LED ON, Buzzer OFF
                print("🦗 [ALERT] CRICKET DETECTED - GREEN LED ON")
                GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
                GPIO.output(RED_LED_PIN, GPIO.LOW)
                GPIO.output(BUZZER_PIN, GPIO.LOW)
            else:
                # Other insect detected - Red LED ON + Buzzer alert (3 beeps)
                print("⚠️ [ALERT] OTHER INSECT DETECTED - RED LED ON + BUZZER ACTIVE")
                GPIO.output(GREEN_LED_PIN, GPIO.LOW)
                GPIO.output(RED_LED_PIN, GPIO.HIGH)
                
                # Buzzer beep pattern: 3 beeps
                for i in range(3):
                    GPIO.output(BUZZER_PIN, GPIO.HIGH)
                    time.sleep(0.3)  # 300ms beep
                    GPIO.output(BUZZER_PIN, GPIO.LOW)
                    time.sleep(0.2)  # 200ms silence
            
            # Keep LED on for 3 seconds
            time.sleep(3)
            
            # Turn off all
            GPIO.output(GREEN_LED_PIN, GPIO.LOW)
            GPIO.output(RED_LED_PIN, GPIO.LOW)
            GPIO.output(BUZZER_PIN, GPIO.LOW)
        except Exception as e:
            print(f"⚠️ LED/Buzzer control error: {e}")
            GPIO.output(GREEN_LED_PIN, GPIO.LOW)
            GPIO.output(RED_LED_PIN, GPIO.LOW)
            GPIO.output(BUZZER_PIN, GPIO.LOW)
    
    # Run LED/Buzzer control in background thread to avoid blocking API response
    thread = threading.Thread(target=led_buzzer_thread, daemon=True)
    thread.start()

def add_detection(insect_type, confidence, image_path=None):
    """Add a detection to history and trigger notifications"""
    detection = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'type': insect_type,
        'confidence': confidence,
        'image': image_path,
        'is_grasshopper': is_grasshopper_label(insect_type)
    }
    
    # Update state
    detection_state['last_detection'] = detection
    detection_state['total_detections'] += 1
    
    if detection['is_grasshopper']:
        detection_state['grasshopper_count'] += 1
    else:
        detection_state['other_insects_count'] += 1
    
    # Add to history (keep last 100)
    detection_state['history'].insert(0, detection)
    if len(detection_state['history']) > 100:
        detection_state['history'] = detection_state['history'][:100]
    
    # Send notification to web interface
    socketio.emit('new_detection', detection)
    
    print(f"📊 Detection: {insect_type} ({confidence:.1f}% confidence)")
    
    return detection

# Routes

# Route principale : sert index.html du frontend
@app.route('/')
def index():
    # Redirige automatiquement vers le port 4200 si l'utilisateur accède à la racine sur le port 5000
    if request.host.endswith(':5000'):
        return redirect('http://localhost:4200', code=302)
    return app.send_static_file('index.html')

@app.route('/api/status')
def get_status():
    """Get current detection status"""
    return jsonify(detection_state)

@app.route('/api/start', methods=['POST'])
def start_detection():
    """Start detection system"""
    detection_state['running'] = True
    socketio.emit('status_change', {'running': True})
    return jsonify({'success': True, 'message': 'Detection started'})

@app.route('/api/stop', methods=['POST'])
def stop_detection():
    """Stop detection system"""
    detection_state['running'] = False
    # Turn off all LEDs (commented out - hardware not installed)
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)
    GPIO.output(RED_LED_PIN, GPIO.LOW)
    socketio.emit('status_change', {'running': False})
    return jsonify({'success': True, 'message': 'Detection stopped'})

@app.route('/api/detection', methods=['POST'])
def receive_detection():
    """Receive detection from detection script"""
    data = request.json
    insect_type = data.get('type', 'unknown')
    confidence = data.get('confidence', 0)
    
    # Add detection
    detection = add_detection(insect_type, confidence)
    
    return jsonify({'success': True, 'detection': detection})


@app.route('/api/detect-image', methods=['POST'])
def detect_image():
    """Receive uploaded image and return detection result using heuristic analysis.
    
    NOTE: The YOLO model (yolov8n.pt) is a generic COCO detector that cannot recognize insects.
    We use the heuristic shape/color analyzer as primary detector since it's designed for grasshoppers.
    """
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Empty filename'}), 400

    try:
        file_bytes = np.frombuffer(file.read(), np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if image is None:
            return jsonify({'success': False, 'message': 'Invalid image format'}), 400

        # Primary detection: Use heuristic analysis (shape/color) - designed for grasshoppers
        heuristic_type, heuristic_conf = analyze_uploaded_image(image)
        heuristic_is_grasshopper = is_grasshopper_label(heuristic_type)
        
        final_type = 'grasshopper' if heuristic_is_grasshopper else 'other_insect'
        final_confidence = float(heuristic_conf)
        decision_source = 'heuristic_shape_color'
        raw_type = heuristic_type

        is_grasshopper = is_grasshopper_label(final_type)
        display_label = 'criquet' if is_grasshopper else 'autres insectes'

        detection = add_detection(final_type, final_confidence)

        # Trigger LED and buzzer alerts based on detection
        control_leds_and_buzzer(final_type)

        return jsonify({
            'success': True,
            'raw_type': raw_type,
            'final_type': final_type,
            'label': display_label,
            'is_grasshopper': is_grasshopper,
            'confidence': round(final_confidence, 1),
            'source': f"{decision_source}",
            'model_confidence': heuristic_conf,
            'heuristic_type': heuristic_type,
            'heuristic_confidence': heuristic_conf,
            'detection': detection
        })
    except Exception as e:
        print(f"⚠️ detect-image error: {e}")
        return jsonify({'success': False, 'message': 'Detection failed'}), 500

@app.route('/api/history')
def get_history():
    """Get detection history"""
    return jsonify(detection_state['history'])

@app.route('/api/stats')
def get_stats():
    """Get detection statistics"""
    stats = {
        'total': detection_state['total_detections'],
        'grasshopper': detection_state['grasshopper_count'],
        'other': detection_state['other_insects_count'],
        'running': detection_state['running']
    }
    return jsonify(stats)

@app.route('/api/test_led', methods=['POST'])
def test_led():
    """Test LED functionality (simulated - hardware not installed)"""
    data = request.json
    led_type = data.get('type', 'green')
    
    if led_type == 'green':
        print("💡 [SIMULATED] Testing GREEN LED")
        GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        return jsonify({'success': True, 'message': 'Green LED tested (simulated)'})
    else:
        print("💡 [SIMULATED] Testing RED LED")
        GPIO.output(RED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
        return jsonify({'success': True, 'message': 'Red LED tested (simulated)'})
 ###

# Pour toutes les autres routes (SPA ou fichiers statiques)
@app.route('/<path:path>')
def static_proxy(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    return app.send_static_file('index.html')
   

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"🔌 Client connected")
    emit('status_change', {'running': detection_state['running']})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"🔌 Client disconnected")

# Cleanup on exit
def cleanup():
    """Clean up GPIO on exit"""
    if GPIO_AVAILABLE:
        GPIO.cleanup()
        print("✅ GPIO cleaned up")

import atexit
atexit.register(cleanup)

if __name__ == '__main__':
    primary_port = 4200
    fallback_port = 4201

    print("\n" + "="*60)
    print("🦗 INSECT DETECTION WEB SERVER")
    print("="*60)
    print(f"🌐 Starting Flask server...")
    print(f"🔧 GPIO Mode: {'Real' if GPIO_AVAILABLE else 'Mock'}")
    print(f"🟢 Green LED Pin: GPIO {GREEN_LED_PIN} (Grasshopper)")
    print(f"🔴 Red LED Pin: GPIO {RED_LED_PIN} (Other Insects)")
    print(f"🔊 Buzzer Pin: GPIO {BUZZER_PIN} (Alert for other insects)")
    
    init_gpio()
    
    print(f"\n📱 Access web interface at:")
    print(f"   http://localhost:{primary_port}")
    print(f"   http://raspberrypi.local:{primary_port}")
    print(f"\n⚡ Press Ctrl+C to stop\n")
    print("="*60 + "\n")
    
    try:
        socketio.run(app, host='0.0.0.0', port=primary_port, debug=False)
    except OSError as e:
        if getattr(e, 'winerror', None) == 10048:
            print(f"\n⚠️ Port {primary_port} already in use. Retrying on port {fallback_port}...")
            print(f"📱 New URL: http://localhost:{fallback_port}\n")
            socketio.run(app, host='0.0.0.0', port=fallback_port, debug=False)
        else:
            raise
    except KeyboardInterrupt:
        print("\n\n⚠️ Shutting down...")
        cleanup()
