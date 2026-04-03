# 🦗 IoT INSECT DETECTION SYSTEM - COMPLETE

## ✅ WHAT'S BEEN CREATED

I've built a **complete IoT insect detection system** for your Raspberry Pi with:

### 🎯 Core Features
1. **Real-time AI Detection** - YOLO/CNN models detect insects
2. **Web Dashboard** - Beautiful real-time interface with notifications
3. **GPIO LED Control** - Physical feedback (Green/Red LEDs)
4. **Flask Backend** - WebSocket communication for instant updates
5. **Google Drive Integration** - Easy dataset/model download

---

## 📁 NEW FILES CREATED

### Web Application (5 files)
- **app.py** - Flask server + GPIO LED control + WebSocket
- **templates/index.html** - Beautiful responsive web interface
- **detect_realtime.py** - Real-time camera detection
- **download_from_drive.py** - Download models from Google Drive
- **start_iot_system.sh** - Complete startup script

### Documentation (1 file)
- **IOT_SYSTEM_GUIDE.md** - Complete guide with wiring, API, troubleshooting

### Updated Files
- **requirements.txt** - Added Flask, SocketIO, RPi.GPIO, gdown

---

## 🔌 HOW IT WORKS

```
┌──────────────┐
│   Camera     │ ← Captures insects
└──────┬───────┘
       ↓
┌──────────────┐
│  YOLO Model  │ ← Detects & classifies
└──────┬───────┘
       ↓
┌──────────────┐
│ Flask Server │ ← Processes detection
└───┬──────┬───┘
    ↓      ↓
┌────────┐ ┌─────────────┐
│  LEDs  │ │ Web Browser │
│ 🟢 🔴  │ │  Dashboard  │
└────────┘ └─────────────┘

🟢 Green LED = Grasshopper detected (target)
🔴 Red LED = Other insect detected (alert)
```

---

## 🚀 HOW TO USE IT

### Step 1: Install Dependencies
```bash
cd /home/pi/pfa
pip3 install --break-system-packages flask flask-socketio gdown RPi.GPIO
```

### Step 2: Download Your Models from Google Drive
```bash
python3 download_from_drive.py
```
Paste your Google Drive sharing links when prompted.

### Step 3: Wire the LEDs

**Green LED (Grasshopper):**
- Connect to GPIO 17 (Physical Pin 11)
- LED → 220Ω resistor → Ground

**Red LED (Other Insects):**
- Connect to GPIO 27 (Physical Pin 13)
- LED → 220Ω resistor → Ground

### Step 4: Start the System
```bash
sudo ./start_iot_system.sh
```

### Step 5: Open Web Interface
Open browser to: **http://localhost:5000**

### Step 6: Test Without Hardware
```bash
# Test with simulation (no camera/LEDs needed)
python3 detect_realtime.py --simulate
```

---

## 🎨 WEB INTERFACE FEATURES

The web dashboard shows:
- ✅ **Real-time Statistics** (Total, Grasshoppers, Others)
- ✅ **Live Detection Feed** with confidence scores
- ✅ **LED Status Indicators** (visual feedback)
- ✅ **Detection History** (last 50 detections)
- ✅ **Control Buttons** (Start/Stop, Test LEDs)
- ✅ **Instant Notifications** (pop-ups for new detections)
- ✅ **Responsive Design** (works on phone/tablet)

---

## 📱 WHAT YOU NEED TO PROVIDE

### 1. Your Trained Models
You have 2 options:

**Option A: Google Drive (Easiest)**
```bash
python3 download_from_drive.py
```
Then provide:
- Your YOLO model sharing link (.pt file)
- Your CNN model sharing link (.h5 file)

**Option B: Manual Copy**
```bash
# Copy your files to:
/home/pi/pfa/models/yolo_best.pt
/home/pi/pfa/models/cnn_pest_best.h5
```

### 2. Your Dataset (Optional)
Only needed if you want to retrain or test:
```bash
python3 download_from_drive.py
```
Select option 1 and provide your dataset ZIP link.

---

## 🎯 DETECTION LOGIC

```python
if detected_insect == "Grasshopper":
    → 🟢 Turn on GREEN LED
    → 📱 Send notification: "Grasshopper detected!"
    → 📊 Update web dashboard
    → ⏲️ LED stays on for 3 seconds
else:
    → 🔴 Turn on RED LED  
    → ⚠️ Send alert: "Other insect detected!"
    → 📊 Update web dashboard
    → ⏲️ LED stays on for 3 seconds
```

---

## 🧪 TESTING WITHOUT HARDWARE

You can test the entire system without camera or LEDs:

```bash
# 1. Start web server
python3 app.py

# 2. In another terminal, run simulation
python3 detect_realtime.py --simulate

# 3. Open browser to http://localhost:5000
# You'll see simulated detections appear!
```

---

## 🔧 CONFIGURATION

### Change Target Insect
Edit `detect_realtime.py`:
```python
TARGET_CLASS = "Aphid"  # Or any other insect class
```

### Change LED Pins
Edit `app.py`:
```python
GREEN_LED_PIN = 17  # Your pin number
RED_LED_PIN = 27    # Your pin number
```

### Adjust Detection Settings
Edit `detect_realtime.py`:
```python
CONFIDENCE_THRESHOLD = 0.70  # 70% confidence minimum
DETECTION_INTERVAL = 2       # Check every 2 seconds
```

---

## 📊 SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────┐
│         WEB BROWSER (Any Device)        │
│  http://localhost:5000 or network IP    │
└──────────────┬──────────────────────────┘
               │ HTTP + WebSocket
               ↓
┌─────────────────────────────────────────┐
│       FLASK SERVER (app.py)             │
│  • Serves web interface                 │
│  • Handles WebSocket connections        │
│  • Controls GPIO LEDs                   │
│  • Stores detection history             │
│  • REST API endpoints                   │
└──────┬──────────────────┬───────────────┘
       │                  │
       ↓                  ↓
┌──────────────┐   ┌─────────────────────┐
│  GPIO LEDs   │   │  DETECTION ENGINE   │
│              │   │  (detect_realtime.py)│
│  GPIO 17 🟢  │   │                     │
│  GPIO 27 🔴  │   │  • Camera capture   │
│              │   │  • YOLO inference   │
└──────────────┘   │  • Send to Flask    │
                   └──────────┬──────────┘
                              │
                   ┌──────────▼──────────┐
                   │    AI MODELS        │
                   │  yolo_best.pt       │
                   │  cnn_pest_best.h5   │
                   └─────────────────────┘
```

---

## 🌐 API ENDPOINTS

The Flask server provides these APIs:

```
GET  /                    → Web dashboard
GET  /api/status          → Current system status
POST /api/start           → Start detection
POST /api/stop            → Stop detection
GET  /api/history         → Detection history
GET  /api/stats           → Statistics
POST /api/test_led        → Test LED (green/red)
```

WebSocket Events:
```
new_detection    → New insect detected
status_change    → System started/stopped
```

---

## 📋 QUICK REFERENCE COMMANDS

```bash
# Start everything
sudo ./start_iot_system.sh

# Just web server
python3 app.py

# Just detection
python3 detect_realtime.py

# Simulation mode
python3 detect_realtime.py --simulate

# Download models
python3 download_from_drive.py

# Test setup
python3 test_setup.py

# Check logs
tail -f logs/flask.log
```

---

## 🐛 TROUBLESHOOTING

### "ModuleNotFoundError"
```bash
pip3 install --break-system-packages flask flask-socketio RPi.GPIO gdown
```

### "GPIO not available"
```bash
sudo usermod -a -G gpio pi
sudo reboot
```

### "Camera not found"
```bash
ls /dev/video*  # List cameras
python3 detect_realtime.py --camera 1  # Try different ID
```

### "Model not found"
```bash
# Download from Google Drive
python3 download_from_drive.py

# Or check if file exists
ls -lh models/
```

### Web interface won't load
```bash
# Check if server is running
ps aux | grep app.py

# Check port
sudo netstat -tulpn | grep 5000

# Restart
sudo killall python3
python3 app.py
```

---

## 📖 DOCUMENTATION

- **IOT_SYSTEM_GUIDE.md** - Complete guide with wiring diagrams
- **README.md** - Main documentation
- **QUICKSTART.md** - Quick start guide
- **OPTIMIZATION_SUMMARY.md** - Technical optimization details

---

## ✨ FEATURES SUMMARY

### ✅ Completed
- [x] Real-time detection engine
- [x] Flask web server with WebSocket
- [x] Beautiful web dashboard
- [x] GPIO LED control (Green/Red)
- [x] Notification system
- [x] Detection history
- [x] Statistics tracking
- [x] Google Drive integration
- [x] Simulation mode for testing
- [x] Comprehensive documentation
- [x] LED test functionality
- [x] Start/Stop controls
- [x] Mobile-responsive design

### 🎯 Ready For
- [x] Real-time camera detection
- [x] Multiple insect classification
- [x] Grasshopper vs Others detection
- [x] Web notifications
- [x] LED indicators
- [x] Remote access (LAN)
- [x] Testing without hardware

---

## 🎉 WHAT TO DO NEXT

1. **Install dependencies:**
   ```bash
   pip3 install --break-system-packages flask flask-socketio gdown RPi.GPIO
   ```

2. **Provide your Google Drive links:**
   - YOLO model (.pt file)
   - CNN model (.h5 file) [optional]
   - Dataset (ZIP) [optional]

3. **Wire up the LEDs** (or skip for simulation)

4. **Run the system:**
   ```bash
   sudo ./start_iot_system.sh
   ```

5. **Test it:**
   ```bash
   python3 detect_realtime.py --simulate
   ```

6. **Access web interface:**
   Open http://localhost:5000

---

## 📞 NEED HELP?

Tell me:
1. Your Google Drive links (for models/dataset)
2. Any errors you're seeing
3. What you want to customize

I can help with:
- Downloading your models
- Fixing any errors
- Customizing features
- Adding more functionality

---

## 🏆 SUCCESS!

You now have a **complete IoT insect detection system**:
- ✅ Web interface ready
- ✅ Backend server ready
- ✅ Detection system ready
- ✅ LED control ready
- ✅ Google Drive integration ready
- ✅ Documentation ready

**Just add your models and you're good to go! 🦗🚀**
