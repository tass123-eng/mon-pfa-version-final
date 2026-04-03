#!/usr/bin/env python3
from ultralytics import YOLO
import os

os.makedirs('models', exist_ok=True)
print("📥 Downloading YOLOv8 Nano model (~6MB)...")
model = YOLO('yolov8n.pt')
model.save('models/yolo_pretrained.pt')
print("✅ Model downloaded and saved to models/yolo_pretrained.pt")
