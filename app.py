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
from datetime import datetime
import json

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

# Detection state
detection_state = {
    'running': False,
    'last_detection': None,
    'total_detections': 0,
    'grasshopper_count': 0,
    'other_insects_count': 0,
    'history': []
}

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
             print("✅ GPIO initialized - LEDs ready")
         except Exception as e:
             print(f"⚠️ GPIO initialization error: {e}")
    else:
        print("⚠️ GPIO mock mode - Electronic components not installed yet")

def control_leds(insect_type):
    """
    Control LEDs based on insect type
    Green LED = Grasshopper (safe/target)
    Red LED = Other insects (danger/alert)
    """
    # DISABLED: Electronic components not installed yet
    if insect_type.lower() == 'grasshopper':
        # Grasshopper detected - Green LED ON (simulated)
        print("💡 [SIMULATED] GREEN LED ON - Grasshopper detected")
        GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
        GPIO.output(RED_LED_PIN, GPIO.LOW)
    else:
        # Other insect - Red LED ON (simulated)
        print("💡 [SIMULATED] RED LED ON - Other insect detected")
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        GPIO.output(RED_LED_PIN, GPIO.HIGH)
    
    # Keep LED on for 3 seconds then turn off
    time.sleep(3)
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)
    GPIO.output(RED_LED_PIN, GPIO.LOW)

def add_detection(insect_type, confidence, image_path=None):
    """Add a detection to history and trigger notifications"""
    detection = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'type': insect_type,
        'confidence': confidence,
        'image': image_path,
        'is_grasshopper': insect_type.lower() == 'grasshopper'
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
    
    # Control LEDs in separate thread to not block
    led_thread = threading.Thread(target=control_leds, args=(insect_type,))
    led_thread.daemon = True
    led_thread.start()
    
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
    # GPIO.output(GREEN_LED_PIN, GPIO.LOW)
    # GPIO.output(RED_LED_PIN, GPIO.LOW)
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
        # GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
        # time.sleep(1)
        # GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        return jsonify({'success': True, 'message': 'Green LED tested (simulated)'})
    else:
        print("💡 [SIMULATED] Testing RED LED")
        # GPIO.output(RED_LED_PIN, GPIO.HIGH)
        # time.sleep(1)
        # GPIO.output(RED_LED_PIN, GPIO.LOW)
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
    print("\n" + "="*60)
    print("🦗 INSECT DETECTION WEB SERVER")
    print("="*60)
    print(f"🌐 Starting Flask server...")
    print(f"🔧 GPIO Mode: {'Real' if GPIO_AVAILABLE else 'Mock'}")
    print(f"🟢 Green LED Pin: GPIO {GREEN_LED_PIN} (Grasshopper)")
    print(f"🔴 Red LED Pin: GPIO {RED_LED_PIN} (Other Insects)")
    
    init_gpio()
    
    print(f"\n📱 Access web interface at:")
    print(f"   http://localhost:4200")
    print(f"   http://raspberrypi.local:4200")
    print(f"\n⚡ Press Ctrl+C to stop\n")
    print("="*60 + "\n")
    
    try:
        socketio.run(app, host='0.0.0.0', port=4200, debug=False)
    except KeyboardInterrupt:
        print("\n\n⚠️ Shutting down...")
        cleanup()
