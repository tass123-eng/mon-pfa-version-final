#!/bin/bash
# Complete IoT Insect Detection System Startup Script

echo "==============================================="
echo "🦗 INSECT DETECTION IoT SYSTEM"
echo "Raspberry Pi 4 B+ | Real-Time Detection"
echo "==============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root for GPIO
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠️ Not running as root. GPIO may not work.${NC}"
    echo "   Run with: sudo ./start_iot_system.sh"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

cd /home/pi/pfa

# Check if models exist
echo "🔍 Checking models..."
if [ ! -f "models/yolo_best.pt" ] && [ ! -f "models/cnn_pest_best.h5" ]; then
    echo -e "${RED}❌ No models found!${NC}"
    echo ""
    echo "You need to add your trained models:"
    echo "  1. Download from Google Drive (recommended):"
    echo "     python3 download_from_drive.py"
    echo ""
    echo "  2. Or manually copy:"
    echo "     models/yolo_best.pt"
    echo "     models/cnn_pest_best.h5"
    echo ""
    read -p "Do you want to download from Google Drive now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 download_from_drive.py
    else
        echo -e "${YELLOW}⚠️ Starting without models (simulation mode only)${NC}"
    fi
fi

# Check LED wiring
echo ""
echo "🔌 LED Wiring Guide:"
echo "   Connect LEDs to the following GPIO pins:"
echo ""
echo "   🟢 GREEN LED (Grasshopper):"
echo "      GPIO 17 (Pin 11) → LED → 220Ω Resistor → GND"
echo ""
echo "   🔴 RED LED (Other Insects):"
echo "      GPIO 27 (Pin 13) → LED → 220Ω Resistor → GND"
echo ""
read -p "Are LEDs connected? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️ LEDs will be simulated in software${NC}"
fi

# Start Flask web server in background
echo ""
echo -e "${GREEN}🌐 Starting Flask web server...${NC}"
python3 app.py > logs/flask.log 2>&1 &
FLASK_PID=$!
echo "   PID: $FLASK_PID"

# Wait for server to start
sleep 3

# Check if server is running
if ps -p $FLASK_PID > /dev/null; then
    echo -e "${GREEN}✅ Web server started${NC}"
    echo "   Access at: http://localhost:5000"
    echo "   Access from network: http://$(hostname -I | awk '{print $1}'):5000"
else
    echo -e "${RED}❌ Web server failed to start${NC}"
    cat logs/flask.log
    exit 1
fi

echo ""
echo "==============================================="
echo "📊 SYSTEM READY"
echo "==============================================="
echo ""
echo "🌐 Web Interface:"
echo "   Local: http://localhost:5000"
echo "   Network: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "🎮 Control Options:"
echo ""
echo "   1️⃣ Web Interface (Recommended)"
echo "      - Open browser to address above"
echo "      - Click 'Start Detection'"
echo ""
echo "   2️⃣ Command Line Detection"
echo "      - Real detection:"
echo "        python3 detect_realtime.py"
echo ""
echo "      - Simulation (no camera needed):"
echo "        python3 detect_realtime.py --simulate"
echo ""
echo "   3️⃣ Manual Control"
echo "      - Start web server: python3 app.py"
echo "      - Run detection: python3 detect_realtime.py"
echo ""
echo "🔧 Configuration:"
echo "   - Edit app.py for LED pins"
echo "   - Edit detect_realtime.py for detection settings"
echo ""
echo "📝 Logs:"
echo "   - Web server: logs/flask.log"
echo "   - Detection: logs/detection.log"
echo ""
echo "⏹️ To stop:"
echo "   - Press Ctrl+C or run: sudo killall python3"
echo ""
echo "==============================================="
echo ""

# Ask user what to do
echo "What would you like to do?"
echo "  1) Open web interface (requires browser)"
echo "  2) Run simulation detection"
echo "  3) Run real-time detection with camera"
echo "  4) Keep server running and exit"
echo ""
read -p "Choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "Opening web browser..."
        if command -v chromium-browser &> /dev/null; then
            chromium-browser http://localhost:5000 &
        elif command -v firefox &> /dev/null; then
            firefox http://localhost:5000 &
        else
            echo "No browser found. Please open: http://localhost:5000"
        fi
        echo ""
        echo "Web server running. Press Ctrl+C to stop."
        wait $FLASK_PID
        ;;
    2)
        echo ""
        echo "Running simulation..."
        python3 detect_realtime.py --simulate
        echo ""
        echo "Simulation complete. Web server still running."
        echo "Press Ctrl+C to stop server."
        wait $FLASK_PID
        ;;
    3)
        echo ""
        echo "Starting real-time detection..."
        python3 detect_realtime.py
        echo ""
        echo "Detection stopped. Web server still running."
        echo "Press Ctrl+C to stop server."
        wait $FLASK_PID
        ;;
    4)
        echo ""
        echo "✅ Server running in background (PID: $FLASK_PID)"
        echo "   To stop: sudo kill $FLASK_PID"
        echo ""
        ;;
    *)
        echo "Invalid choice. Server running. Press Ctrl+C to stop."
        wait $FLASK_PID
        ;;
esac
