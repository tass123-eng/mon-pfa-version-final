# 🦗 IoT Insect Detection System - Complete Guide

## 🎯 Overview
Real-time insect detection system with:
- **AI Detection**: YOLO + CNN ensemble
- **Web Interface**: Real-time dashboard with notifications
- **GPIO Control**: LED indicators (Green = Grasshopper, Red = Other)
- **Flask Backend**: WebSocket communication
- **Raspberry Pi Optimized**: Runs on RPi 4 B+

---

## 📋 What You Need

### Hardware
1. **Raspberry Pi 4 B+** (4GB RAM recommended)
2. **Camera**: USB webcam or Pi Camera
3. **LEDs**:
   - 1x Green LED (3mm or 5mm)
   - 1x Red LED (3mm or 5mm)
   - 2x 220Ω resistors
   - Jumper wires
4. **Power Supply**: 3A+ recommended

### Software
- Raspbian OS (Bullseye or later)
- Python 3.7+
- Your trained models (YOLO .pt and/or CNN .h5)
- Your dataset (optional, for training)

---

## 🔌 LED Wiring Guide

Connect LEDs to Raspberry Pi GPIO:

```
Green LED (Grasshopper detected):
┌──────────┐
│ RPi GPIO │
│  Pin 11  │──────┬────[LED]────[220Ω]────┬──── GND
│ (GPIO17) │      │    (Green)             │
└──────────┘      │                        │
                  └────────────────────────┘

Red LED (Other insects):
┌──────────┐
│ RPi GPIO │
│  Pin 13  │──────┬────[LED]────[220Ω]────┬──── GND
│ (GPIO27) │      │    (Red)               │
└──────────┘      │                        │
                  └────────────────────────┘
```

**Pin Layout:**
```
Raspberry Pi GPIO Header:
 3V3  (1) (2)  5V
     (3) (4)  5V
     (5) (6)  GND
     (7) (8)  
 GND  (9) (10) 
GPIO17(11) (12) 
GPIO27(13) (14) GND
      ...
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/pi/pfa
pip3 install -r requirements.txt
```

Or manual install:
```bash
pip3 install flask flask-socketio RPi.GPIO opencv-python-headless
pip3 install torch ultralytics tensorflow gdown
```

### 2. Download Your Models

**Option A: From Google Drive**
```bash
python3 download_from_drive.py
```
Then paste your Google Drive sharing links.

**Option B: Manual Copy**
```bash
# Copy your models to:
cp your_yolo_model.pt models/yolo_best.pt
cp your_cnn_model.h5 models/cnn_pest_best.h5
```

### 3. Start the System

```bash
sudo ./start_iot_system.sh
```

This will:
- ✅ Check models
- ✅ Start web server
- ✅ Initialize GPIO for LEDs
- ✅ Show you all options

### 4. Access Web Interface

Open browser to:
- **Local**: http://localhost:5000
- **Network**: http://YOUR_RPI_IP:5000

---

## 🎮 Usage

### Web Interface (Recommended)

1. Open http://localhost:5000
2. Click "Start Detection"
3. System will detect insects in real-time
4. Notifications appear on screen
5. LEDs light up:
   - 🟢 **Green** = Grasshopper detected (target)
   - 🔴 **Red** = Other insect detected (alert)

### Command Line

**Real-time detection with camera:**
```bash
python3 detect_realtime.py
```

**Simulation mode (no camera/model needed):**
```bash
python3 detect_realtime.py --simulate
```

**Custom options:**
```bash
python3 detect_realtime.py --camera 0 --interval 2.0 --threshold 0.70
```

### Test LEDs

```bash
# In web interface, click "Test Green LED" or "Test Red LED"

# Or via API:
curl -X POST http://localhost:5000/api/test_led \
  -H "Content-Type: application/json" \
  -d '{"type":"green"}'
```

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────┐
│                 Web Interface                    │
│        (HTML/CSS/JS + Socket.IO)                │
│     http://localhost:5000                       │
└────────────┬────────────────────────────────────┘
             │ WebSocket
             ↓
┌─────────────────────────────────────────────────┐
│            Flask Backend (app.py)                │
│  - WebSocket server                             │
│  - REST API                                      │
│  - GPIO LED control                              │
│  - Detection history                             │
└────────┬────────────────────────┬─────────────── ┘
         │                        │
         ↓                        ↓
┌──────────────────┐    ┌──────────────────┐
│  GPIO LEDs       │    │  Detection Engine │
│  - Green (17)    │    │  detect_realtime.py│
│  - Red (27)      │    │  - Camera capture │
│                  │    │  - YOLO inference │
└──────────────────┘    │  - Send to Flask  │
                        └───────────┬────────┘
                                    │
                        ┌───────────▼────────┐
                        │   AI Models        │
                        │   - YOLO (.pt)     │
                        │   - CNN (.h5)      │
                        └────────────────────┘
```

---

## 📁 File Structure

```
/home/pi/pfa/
├── 🌐 Web Application
│   ├── app.py                    # Flask server + GPIO
│   ├── templates/
│   │   └── index.html           # Web interface
│   └── static/ (optional)
│
├── 🤖 Detection System
│   ├── detect_realtime.py        # Real-time detection
│   ├── pfa_mixage.py            # Batch inference (original)
│   └── download_from_drive.py    # Google Drive downloader
│
├── 🚀 Startup & Tools
│   ├── start_iot_system.sh      # Main startup script
│   ├── setup.sh                 # Initial installation
│   ├── test_setup.py            # Verify installation
│   └── validate_optimization.py  # Code validation
│
├── 📚 Documentation
│   ├── README.md                # Main docs
│   ├── IOT_SYSTEM_GUIDE.md      # This file
│   ├── QUICKSTART.md            # Quick start
│   └── OPTIMIZATION_SUMMARY.md   # Technical details
│
├── 📦 Data & Models
│   ├── models/
│   │   ├── yolo_best.pt         # YOLO model
│   │   └── cnn_pest_best.h5     # CNN model
│   ├── dataset/
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   └── outputs/                 # Results
│
└── 📝 Configuration
    ├── requirements.txt          # Python packages
    └── logs/                    # System logs
```

---

## 🔧 Configuration

### LED Pins (app.py)
```python
GREEN_LED_PIN = 17  # GPIO 17 (Pin 11)
RED_LED_PIN = 27    # GPIO 27 (Pin 13)
```

### Detection Settings (detect_realtime.py)
```python
TARGET_CLASS = "Grasshopper"
CONFIDENCE_THRESHOLD = 0.70
DETECTION_INTERVAL = 2  # seconds
CAMERA_ID = 0  # 0 = USB camera
```

### Flask Server (app.py)
```python
PORT = 5000
HOST = '0.0.0.0'  # accessible from network
```

---

## 🐛 Troubleshooting

### LEDs Not Working
```bash
# Check GPIO permissions
sudo usermod -a -G gpio pi
sudo reboot

# Test GPIO
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(17, GPIO.OUT); GPIO.output(17, 1)"
```

### Camera Not Found
```bash
# List cameras
ls /dev/video*

# Test camera
v4l2-ctl --list-devices

# Try different camera ID
python3 detect_realtime.py --camera 1
```

### Web Interface Not Loading
```bash
# Check if Flask is running
ps aux | grep app.py

# Check port
sudo netstat -tulpn | grep 5000

# Restart server
sudo killall python3
python3 app.py
```

### Model Not Loading
```bash
# Check model exists
ls -lh models/

# Check file permissions
chmod 644 models/*.pt models/*.h5

# Test model loading
python3 -c "from ultralytics import YOLO; YOLO('models/yolo_best.pt')"
```

### Out of Memory
```bash
# Increase swap
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Reduce detection interval
python3 detect_realtime.py --interval 5.0
```

---

## 📡 API Reference

### REST API

#### Get Status
```bash
GET /api/status
Response: {
  "running": bool,
  "last_detection": {...},
  "total_detections": int,
  "grasshopper_count": int,
  "other_insects_count": int
}
```

#### Start Detection
```bash
POST /api/start
Response: {"success": true, "message": "Detection started"}
```

#### Stop Detection
```bash
POST /api/stop
Response: {"success": true, "message": "Detection stopped"}
```

#### Get History
```bash
GET /api/history
Response: [
  {
    "timestamp": "2026-01-20 12:00:00",
    "type": "Grasshopper",
    "confidence": 95.5,
    "is_grasshopper": true
  },
  ...
]
```

#### Test LED
```bash
POST /api/test_led
Body: {"type": "green" | "red"}
Response: {"success": true, "message": "LED tested"}
```

### WebSocket Events

#### Client → Server
- `connect`: Client connected
- `disconnect`: Client disconnected

#### Server → Client
- `new_detection`: New insect detected
  ```javascript
  {
    timestamp: "2026-01-20 12:00:00",
    type: "Grasshopper",
    confidence: 95.5,
    is_grasshopper: true
  }
  ```

- `status_change`: Detection status changed
  ```javascript
  {
    running: true
  }
  ```

---

## 🎨 Customization

### Change Target Insect

Edit `detect_realtime.py`:
```python
TARGET_CLASS = "YourInsectName"  # Must match model class
```

### Add More LEDs

Edit `app.py`:
```python
YELLOW_LED_PIN = 22
GPIO.setup(YELLOW_LED_PIN, GPIO.OUT)
```

### Custom Notifications

Edit `templates/index.html`:
```javascript
function showNotification(data) {
    // Add your custom notification logic
    // e.g., play sound, send email, etc.
}
```

### Multiple Cameras

```python
# detect_realtime.py
cameras = [0, 1, 2]  # Multiple camera IDs
for cam_id in cameras:
    detector = RealTimeDetector()
    detector.camera_id = cam_id
    detector.run()
```

---

## 📱 Mobile Access

Access from phone/tablet on same network:

1. Find Raspberry Pi IP:
```bash
hostname -I
```

2. Open on mobile: `http://192.168.1.X:5000`

3. Add to home screen for app-like experience

---

## 🔐 Security

### Enable HTTPS (Optional)

```bash
pip install pyopenssl

# Generate certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# Update app.py
socketio.run(app, ssl_context=('cert.pem', 'key.pem'))
```

### Password Protection

```bash
pip install flask-httpauth

# Add to app.py
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify(username, password):
    return username == 'admin' and password == 'yourpassword'

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')
```

---

## 🎯 Next Steps

1. **Deploy to Production**
   - Set up systemd service for auto-start
   - Configure firewall
   - Set up remote access (VPN/SSH)

2. **Enhance Features**
   - Email notifications
   - Data logging to database
   - Statistics and analytics
   - Mobile app

3. **Optimize Performance**
   - Use TensorFlow Lite
   - Implement model quantization
   - Multi-threading for detection

4. **Scale Up**
   - Multiple cameras
   - Distributed detection
   - Cloud integration

---

## 📞 Support

If you encounter issues:

1. Check logs: `tail -f logs/flask.log`
2. Run validation: `python3 test_setup.py`
3. Test components individually
4. Check hardware connections
5. Review documentation

---

## 🏆 Success Checklist

- [ ] Dependencies installed
- [ ] Models downloaded
- [ ] LEDs connected and tested
- [ ] Camera working
- [ ] Web interface accessible
- [ ] Detection working
- [ ] LEDs responding to detections
- [ ] Notifications appearing

---

**System Ready! Start detecting insects! 🦗🔴🟢**
