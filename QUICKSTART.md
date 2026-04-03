# Quick Start Guide - Pest Detection on Raspberry Pi 4 B+

## 🚀 Quick Setup (5 Steps)

### 1️⃣ Run Setup Script
```bash
cd /home/pi/pfa
./setup.sh
```
This will take 20-40 minutes. It installs all dependencies and configures your Raspberry Pi.

### 2️⃣ Prepare Your Dataset
```bash
# Option A: If you have your dataset ready
cp -r /path/to/your/dataset/* /home/pi/pfa/dataset/

# Option B: Create empty structure and add images manually
# Already created by setup.sh at /home/pi/pfa/dataset/
```

Dataset structure should be:
```
/home/pi/pfa/dataset/
├── train/
│   ├── Grasshopper/
│   ├── AphidFly/
│   └── ...
├── val/
│   └── (same classes)
└── test/
    └── (same classes)
```

### 3️⃣ Add Your Models
```bash
# Copy your trained models
cp /path/to/your/cnn_model.h5 /home/pi/pfa/models/cnn_pest_best.h5
cp /path/to/your/yolo_model.pt /home/pi/pfa/models/yolo_best.pt
```

### 4️⃣ Run Inference
```bash
# Activate virtual environment
source /home/pi/pfa/venv/bin/activate

# Run on test set
python3 pfa_mixage.py --split test

# Or use the helper script
./run.sh --split test
```

### 5️⃣ View Results
```bash
# Results are saved in outputs/
ls -lh /home/pi/pfa/outputs/

# View images (if you have desktop environment)
feh /home/pi/pfa/outputs/*.png

# Or copy to another machine
scp pi@raspberrypi:/home/pi/pfa/outputs/*.png ./
```

## 🎯 Common Commands

### Run Evaluation
```bash
# On test set (default)
./run.sh

# On validation set
./run.sh --split val

# With smaller batch size (if OOM)
./run.sh --split test --batch-size 4

# Custom paths
./run.sh --data-root /path/to/dataset --cnn-model /path/to/model.h5
```

### Monitor System
```bash
# Temperature (important!)
vcgencmd measure_temp

# Full system monitor
./monitor.sh

# Watch temperature in real-time
watch -n 2 vcgencmd measure_temp
```

### Manage Resources
```bash
# Free up memory
sudo sync
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

# Kill other processes
htop  # Interactive process manager

# Reboot if needed
sudo reboot
```

## 🐛 Quick Troubleshooting

### Problem: Out of Memory (OOM)
**Solution:**
```bash
# Use smaller batch size
./run.sh --batch-size 4

# Or even smaller
./run.sh --batch-size 2
```

### Problem: Too Slow
**Solution:**
```bash
# Enable performance mode
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Close other applications
sudo systemctl stop [service-name]
```

### Problem: Overheating
**Solution:**
```bash
# Check temperature
vcgencmd measure_temp

# If >80°C, stop and cool down
# Add heatsink or fan
# Reduce clock speed temporarily:
echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Problem: TensorFlow Import Error
**Solution:**
```bash
source venv/bin/activate
pip uninstall tensorflow
pip install tensorflow-aarch64

# Or use TFLite
pip install tflite-runtime
```

### Problem: YOLO/Torch Error
**Solution:**
```bash
pip uninstall torch torchvision
pip install torch==1.13.0 torchvision==0.14.0 --index-url https://download.pytorch.org/whl/cpu
pip install ultralytics
```

## 📊 Expected Performance

### Inference Time (Raspberry Pi 4 B+)
- **CNN**: ~15-30 seconds per 100 images
- **YOLO**: ~20-40 seconds per 100 images
- **Total (ensemble)**: ~40-80 seconds per 100 images

### Memory Usage
- **Idle**: ~500MB
- **During inference**: 2-3GB
- **Peak**: ~3.5GB

### Accuracy (example)
- CNN: ~85-90%
- YOLO: ~90-95%
- Smart Ensemble: ~92-96%

## 🔄 Workflow Example

```bash
# 1. Activate environment
cd /home/pi/pfa
source venv/bin/activate

# 2. Check system
./monitor.sh

# 3. Run on validation set first (smaller)
python3 pfa_mixage.py --split val --batch-size 8

# 4. If successful, run on test set
python3 pfa_mixage.py --split test --batch-size 8

# 5. Check results
ls -lh outputs/
cat outputs/*.txt  # If any text logs

# 6. View metrics
grep "Accuracy" outputs/*.log  # If logs exist

# 7. Transfer results
scp -r outputs/ user@your-pc:~/pest-detection-results/
```

## 📝 File Overview

```
/home/pi/pfa/
├── pfa_mixage.py          # Main inference script (optimized)
├── pfa_mixage_backup.py   # Original Colab version (backup)
├── setup.sh               # Installation script
├── run.sh                 # Helper script to run inference
├── monitor.sh             # System monitoring script
├── requirements.txt       # Python dependencies
├── README.md              # Full documentation
├── QUICKSTART.md          # This file
├── dataset/               # Your dataset goes here
│   ├── train/
│   ├── val/
│   └── test/
├── models/                # Your trained models
│   ├── cnn_pest_best.h5
│   └── yolo_best.pt
├── outputs/               # Results saved here
│   ├── model_comparison.png
│   ├── Smart_Ensemble_Test_Set.png
│   ├── roc_curve.png
│   └── pest_detection_results.png
└── venv/                  # Python virtual environment
```

## 🎓 Learning Resources

### Understanding the Code
- **Config class**: All settings (batch size, paths, etc.)
- **ModelInference**: Handles CNN and YOLO loading/prediction
- **ensemble_weighted()**: Combines models with fixed weights
- **ensemble_smart()**: Adapts based on confidence
- **run_ensemble_evaluation()**: Main pipeline

### Customization
Edit these in `pfa_mixage.py`:
```python
class Config:
    BATCH_SIZE = 8              # Change this for memory
    ALPHA = 0.85                # YOLO weight
    BETA = 0.15                 # CNN weight
    CONFIDENCE_THRESHOLD = 0.75 # Smart ensemble threshold
    TARGET_CLASS = "Grasshopper" # Detection target
```

## 💡 Tips for Best Results

1. **Cool your Pi**: Use heatsink and fan for stable performance
2. **Use good power supply**: Official 3A+ adapter recommended
3. **Start small**: Test on validation set first
4. **Monitor temperature**: Stay below 80°C
5. **Close other apps**: Free up memory before running
6. **Use fast SD card**: Class 10 or better
7. **Regular reboots**: Keep system fresh for long sessions

## 🆘 Support

If you encounter issues:

1. Check `README.md` for detailed documentation
2. Run `./monitor.sh` to check system resources
3. Try reducing batch size: `--batch-size 4` or `--batch-size 2`
4. Verify model paths are correct
5. Check dataset structure matches expected format
6. Review error messages carefully
7. Reboot and try again

## ✅ Quick Test

After setup, test if everything works:

```bash
cd /home/pi/pfa
source venv/bin/activate

# Test Python imports
python3 << EOF
import tensorflow as tf
from ultralytics import YOLO
import numpy as np
print("✅ All imports successful!")
print(f"TensorFlow: {tf.__version__}")
EOF

# If that works, your setup is ready!
```

---

**Ready to Go!** 🚀

For detailed information, see [README.md](README.md)
