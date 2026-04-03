#!/bin/bash
# Setup script for Pest Detection System on Raspberry Pi 4 B+

set -e  # Exit on error

echo "=========================================="
echo "Pest Detection Setup for Raspberry Pi 4 B+"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo -e "${YELLOW}Warning: Not running on Raspberry Pi${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Update system
echo -e "${GREEN}Step 1: Updating system...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# Step 2: Install system dependencies
echo -e "${GREEN}Step 2: Installing system dependencies...${NC}"
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    libatlas-base-dev \
    libopenblas-dev \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libqtgui4 \
    libqt4-test \
    build-essential \
    cmake \
    pkg-config

# Step 3: Create directories
echo -e "${GREEN}Step 3: Creating directories...${NC}"
mkdir -p /home/pi/pfa/dataset/{train,val,test}
mkdir -p /home/pi/pfa/models
mkdir -p /home/pi/pfa/outputs

# Step 4: Create virtual environment
echo -e "${GREEN}Step 4: Creating virtual environment...${NC}"
cd /home/pi/pfa
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Removing..."
    rm -rf venv
fi
python3 -m venv venv
source venv/bin/activate

# Step 5: Upgrade pip
echo -e "${GREEN}Step 5: Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel

# Step 6: Install Python packages
echo -e "${GREEN}Step 6: Installing Python packages...${NC}"
echo "This may take 15-30 minutes on Raspberry Pi..."

# Install numpy first (many packages depend on it)
pip install "numpy>=1.21.0,<1.24.0"

# Install TensorFlow (try multiple methods)
echo "Installing TensorFlow..."
if pip install "tensorflow>=2.8.0,<2.13.0" 2>/dev/null; then
    echo "TensorFlow installed successfully"
elif pip install tensorflow-aarch64 2>/dev/null; then
    echo "TensorFlow (aarch64) installed successfully"
else
    echo -e "${YELLOW}Warning: Standard TensorFlow installation failed${NC}"
    echo "You may need to install manually for your architecture"
fi

# Install PyTorch for ARM
echo "Installing PyTorch..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install remaining packages
pip install -r requirements.txt

# Step 7: Increase swap space (important for compilation)
echo -e "${GREEN}Step 7: Increasing swap space...${NC}"
CURRENT_SWAP=$(grep CONF_SWAPSIZE /etc/dphys-swapfile | grep -o '[0-9]*')
if [ "$CURRENT_SWAP" -lt 2048 ]; then
    echo "Increasing swap to 2GB..."
    sudo dphys-swapfile swapoff
    sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    echo -e "${GREEN}Swap increased to 2GB${NC}"
else
    echo "Swap already sufficient ($CURRENT_SWAP MB)"
fi

# Step 8: Set CPU governor to performance
echo -e "${GREEN}Step 8: Optimizing CPU performance...${NC}"
sudo apt-get install -y cpufrequtils
# This setting won't persist after reboot
echo "Setting CPU governor to performance mode (temporary)..."
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
    if [ -f "$cpu/cpufreq/scaling_governor" ]; then
        echo performance | sudo tee "$cpu/cpufreq/scaling_governor" > /dev/null
    fi
done

# Optional: Make performance mode persistent
read -p "Make CPU performance mode persistent? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpufrequtils > /dev/null
    sudo systemctl restart cpufrequtils
fi

# Step 9: Create helper scripts
echo -e "${GREEN}Step 9: Creating helper scripts...${NC}"

# Run script
cat > /home/pi/pfa/run.sh << 'EOF'
#!/bin/bash
cd /home/pi/pfa
source venv/bin/activate
python3 pfa_mixage.py "$@"
EOF
chmod +x /home/pi/pfa/run.sh

# Monitor script
cat > /home/pi/pfa/monitor.sh << 'EOF'
#!/bin/bash
echo "Raspberry Pi System Monitor"
echo "============================"
echo ""
echo "Temperature: $(vcgencmd measure_temp)"
echo "CPU Frequency: $(vcgencmd measure_clock arm | awk -F= '{printf "%.0f MHz\n", $2/1000000}')"
echo ""
echo "Memory Usage:"
free -h
echo ""
echo "Disk Usage:"
df -h /
echo ""
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | awk '{print "  " $2 "% user, " $4 "% system, " $8 "% idle"}'
EOF
chmod +x /home/pi/pfa/monitor.sh

# Step 10: Download test images (optional)
echo -e "${GREEN}Step 10: Setup complete!${NC}"
echo ""
echo "=========================================="
echo "Installation Summary"
echo "=========================================="
echo "✅ System dependencies installed"
echo "✅ Virtual environment created at: /home/pi/pfa/venv"
echo "✅ Python packages installed"
echo "✅ Directories created:"
echo "   - /home/pi/pfa/dataset (place your data here)"
echo "   - /home/pi/pfa/models (place your models here)"
echo "   - /home/pi/pfa/outputs (results will be saved here)"
echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo "1. Place your dataset in /home/pi/pfa/dataset/"
echo "   Structure: dataset/{train,val,test}/class_name/*.jpg"
echo ""
echo "2. Place your models in /home/pi/pfa/models/"
echo "   - cnn_pest_best.h5"
echo "   - yolo_best.pt"
echo ""
echo "3. Activate virtual environment:"
echo "   source /home/pi/pfa/venv/bin/activate"
echo ""
echo "4. Run the program:"
echo "   ./run.sh --split test"
echo "   or"
echo "   python3 pfa_mixage.py --split test"
echo ""
echo "5. Monitor system resources:"
echo "   ./monitor.sh"
echo ""
echo "=========================================="
echo "Troubleshooting"
echo "=========================================="
echo "- If you get OOM errors, reduce batch size:"
echo "  python3 pfa_mixage.py --batch-size 4"
echo ""
echo "- Monitor temperature: vcgencmd measure_temp"
echo "- Check logs in /home/pi/pfa/outputs/"
echo ""
echo "For more information, see README.md"
echo ""

# Final check
echo -e "${GREEN}Testing Python imports...${NC}"
source venv/bin/activate
python3 << 'PYEOF'
import sys
errors = []

try:
    import numpy
    print("✅ numpy")
except ImportError as e:
    errors.append(f"numpy: {e}")
    print("❌ numpy")

try:
    import cv2
    print("✅ opencv")
except ImportError as e:
    errors.append(f"opencv: {e}")
    print("❌ opencv")

try:
    import tensorflow as tf
    print(f"✅ tensorflow {tf.__version__}")
except ImportError as e:
    errors.append(f"tensorflow: {e}")
    print("❌ tensorflow")

try:
    import torch
    print(f"✅ torch {torch.__version__}")
except ImportError as e:
    errors.append(f"torch: {e}")
    print("❌ torch")

try:
    import sklearn
    print("✅ sklearn")
except ImportError as e:
    errors.append(f"sklearn: {e}")
    print("❌ sklearn")

try:
    from ultralytics import YOLO
    print("✅ ultralytics")
except ImportError as e:
    errors.append(f"ultralytics: {e}")
    print("❌ ultralytics")

if errors:
    print("\n⚠️ Some packages failed to import:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
else:
    print("\n✅ All packages imported successfully!")

PYEOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Setup completed successfully!${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️ Setup completed with warnings${NC}"
    echo "Some packages may need manual installation"
fi
