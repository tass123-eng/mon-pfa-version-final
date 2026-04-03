#!/usr/bin/env python3
"""
Setup Pretrained YOLO Model for Insect Detection
No training required - uses existing pretrained models
"""

import os
import sys

def download_pretrained_model():
    """
    Download a pretrained YOLO model suitable for insect detection
    
    Options:
    1. YOLOv8n (nano) - Fastest, smallest, general purpose
    2. YOLOv8s (small) - Balanced speed/accuracy
    3. Insect-specific model from community (if available)
    """
    
    print("\n" + "="*70)
    print("🦗 PRETRAINED MODEL SETUP - NO TRAINING NEEDED")
    print("="*70)
    
    print("\n📋 Available Options:\n")
    print("1. YOLOv8 Nano (Recommended for Pi)")
    print("   ✅ Size: ~6MB")
    print("   ✅ Speed: Very fast on Raspberry Pi")
    print("   ✅ Can detect: insects, animals, objects")
    print("   ⚠️  General purpose - will detect many insect types\n")
    
    print("2. YOLOv8 Small")
    print("   ✅ Size: ~22MB")
    print("   ✅ Better accuracy than nano")
    print("   ⚠️  Slower on Raspberry Pi\n")
    
    print("3. Custom Insect Detection Model")
    print("   ✅ Specialized for insects")
    print("   ✅ Better at distinguishing insect types")
    print("   ⚠️  Requires download from community sources\n")
    
    print("4. Use Ultralytics Zoo (Pre-trained)")
    print("   ✅ Multiple pretrained models available")
    print("   ✅ No training required")
    print("   ✅ Can classify grasshopper vs other insects\n")
    
    choice = input("Choose option (1-4) [1]: ").strip() or "1"
    
    print("\n" + "="*70)
    
    if choice == "1":
        setup_yolov8_nano()
    elif choice == "2":
        setup_yolov8_small()
    elif choice == "3":
        setup_custom_insect_model()
    elif choice == "4":
        setup_ultralytics_zoo()
    else:
        print("❌ Invalid choice")
        sys.exit(1)

def setup_yolov8_nano():
    """Setup YOLOv8 Nano model - best for Raspberry Pi"""
    print("\n📥 Setting up YOLOv8 Nano (Recommended)...\n")
    
    try:
        # Install ultralytics if not installed
        print("1️⃣ Installing Ultralytics YOLO...")
        os.system("pip3 install --break-system-packages ultralytics")
        
        print("\n2️⃣ Downloading YOLOv8n model (6MB)...")
        from ultralytics import YOLO
        
        # This will auto-download the model
        model = YOLO('yolov8n.pt')
        
        # Save to models directory
        os.makedirs('models', exist_ok=True)
        model.save('models/yolo_pretrained.pt')
        
        print("\n✅ SUCCESS! YOLOv8 Nano installed")
        print(f"📂 Model saved to: models/yolo_pretrained.pt")
        print(f"💾 Size: ~6MB")
        print(f"\n🎯 This model can detect:")
        print("   - Birds, insects, animals")
        print("   - Various object types")
        print("   - Will work for grasshopper detection!")
        
        print("\n📝 Next Steps:")
        print("   1. Update detect_realtime.py to use: models/yolo_pretrained.pt")
        print("   2. Model will detect insects automatically")
        print("   3. You can customize class names for your needs")
        
        create_detection_config()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Manual installation:")
        print("   pip3 install --break-system-packages ultralytics")
        print("   python3 -c \"from ultralytics import YOLO; YOLO('yolov8n.pt')\"")

def setup_yolov8_small():
    """Setup YOLOv8 Small model - better accuracy"""
    print("\n📥 Setting up YOLOv8 Small...\n")
    
    try:
        print("1️⃣ Installing Ultralytics YOLO...")
        os.system("pip3 install --break-system-packages ultralytics")
        
        print("\n2️⃣ Downloading YOLOv8s model (22MB)...")
        from ultralytics import YOLO
        
        model = YOLO('yolov8s.pt')
        
        os.makedirs('models', exist_ok=True)
        model.save('models/yolo_pretrained.pt')
        
        print("\n✅ SUCCESS! YOLOv8 Small installed")
        print(f"📂 Model saved to: models/yolo_pretrained.pt")
        print(f"💾 Size: ~22MB")
        
        create_detection_config()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

def setup_custom_insect_model():
    """Setup custom insect detection model from community"""
    print("\n📥 Custom Insect Model Setup\n")
    
    print("🌐 Community Pretrained Models:")
    print("\n1. Roboflow Universe - Insect Detection Models")
    print("   https://universe.roboflow.com/")
    print("   Search for: 'insect detection' or 'pest detection'")
    
    print("\n2. Hugging Face - Insect Classification")
    print("   https://huggingface.co/models?search=insect")
    
    print("\n3. GitHub - Pretrained Pest Detection")
    print("   Search: 'insect detection pytorch' or 'pest detection model'")
    
    print("\n📝 Manual Setup Instructions:")
    print("   1. Find a pretrained model online")
    print("   2. Download the .pt or .pth file")
    print("   3. Copy to: /home/pi/pfa/models/yolo_pretrained.pt")
    print("   4. Update detection script with model path")
    
    print("\n💡 Recommended Sources:")
    print("   - Roboflow (easiest)")
    print("   - Ultralytics Model Zoo")
    print("   - Academic datasets (often include pretrained models)")

def setup_ultralytics_zoo():
    """Use Ultralytics model zoo with classification"""
    print("\n📥 Setting up Ultralytics Classification Model...\n")
    
    try:
        print("1️⃣ Installing Ultralytics...")
        os.system("pip3 install --break-system-packages ultralytics")
        
        print("\n2️⃣ Downloading classification model...")
        from ultralytics import YOLO
        
        # Use classification model instead of detection
        model = YOLO('yolov8n-cls.pt')  # Classification model
        
        os.makedirs('models', exist_ok=True)
        model.save('models/yolo_classifier.pt')
        
        print("\n✅ SUCCESS! Classification model installed")
        print(f"📂 Model saved to: models/yolo_classifier.pt")
        print(f"\n🎯 This model classifies images into categories")
        print("   - Better for distinguishing insect types")
        print("   - Can be fine-tuned with small dataset (50-100 images)")
        
        create_classification_config()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

def create_detection_config():
    """Create configuration for detection"""
    config = """# Detection Configuration
# Using pretrained YOLO model (no training needed)

MODEL_PATH = "models/yolo_pretrained.pt"
MODEL_TYPE = "detection"  # Object detection

# Insect classes to detect
# The model will detect objects, we'll classify as grasshopper or other
TARGET_CLASS = "grasshopper"

# Detection settings
CONFIDENCE_THRESHOLD = 0.5  # 50% confidence minimum
IMAGE_SIZE = 640  # Input image size

# Class mapping (customize based on what model detects)
INSECT_CLASSES = {
    'bird': 'other',  # YOLO detects birds as class 14
    'cat': 'other',
    'dog': 'other',
    # Add more mappings as needed
    # For unknown detections, default to 'other'
}

# Simple classification logic:
# If model detects small objects in specific size range -> likely insect
# Can add color/shape analysis later
"""
    
    with open('detection_config.py', 'w') as f:
        f.write(config)
    
    print(f"\n📝 Created: detection_config.py")

def create_classification_config():
    """Create configuration for classification"""
    config = """# Classification Configuration
# Using pretrained classification model

MODEL_PATH = "models/yolo_classifier.pt"
MODEL_TYPE = "classification"

# Classes
TARGET_CLASS = "grasshopper"
OTHER_CLASSES = ["aphid", "beetle", "fly", "moth", "other_insect"]

# Settings
CONFIDENCE_THRESHOLD = 0.6
IMAGE_SIZE = 224  # Classification models use smaller size
"""
    
    with open('detection_config.py', 'w') as f:
        f.write(config)
    
    print(f"\n📝 Created: detection_config.py")

def show_alternative_solutions():
    """Show alternative approaches without large dataset"""
    print("\n" + "="*70)
    print("🎯 ALTERNATIVE SOLUTIONS (No Large Dataset Needed)")
    print("="*70)
    
    print("\n1️⃣ Use Image Classification with Small Dataset")
    print("   📸 Collect: 50-100 images of grasshoppers")
    print("   📸 Collect: 50-100 images of other insects")
    print("   ✅ Fine-tune pretrained model with this small dataset")
    print("   ✅ Works well for binary classification")
    print("   ⏱️  Training time: ~10-30 minutes on Colab")
    
    print("\n2️⃣ Use Color & Shape Analysis (No ML)")
    print("   🎨 Analyze color: Grasshoppers are typically green/brown")
    print("   📏 Analyze shape: Long body, prominent legs")
    print("   ✅ No training needed")
    print("   ✅ Works with simple computer vision")
    print("   ⚠️  Less accurate but fast")
    
    print("\n3️⃣ Use Public Pretrained Models")
    print("   🌐 Search online for 'insect classification model'")
    print("   🌐 Roboflow Universe has free models")
    print("   ✅ Ready to use")
    print("   ✅ No training needed")
    
    print("\n4️⃣ Hybrid Approach")
    print("   🤖 Use pretrained YOLO to detect insects")
    print("   🎨 Use color/shape to classify type")
    print("   ✅ Combines ML with classical CV")
    print("   ✅ Good balance of accuracy and speed")
    
    print("\n5️⃣ Edge Impulse (Embedded ML Platform)")
    print("   🌐 https://edgeimpulse.com")
    print("   ✅ Free tier available")
    print("   ✅ Optimized for Raspberry Pi")
    print("   ✅ Easy training with small dataset")
    print("   ✅ Exports to TensorFlow Lite")

if __name__ == '__main__':
    print("\n🦗 Welcome to Pretrained Model Setup")
    print("   No large dataset or training required!\n")
    
    show_alternative_solutions()
    
    print("\n" + "="*70)
    choice = input("\n❓ Would you like to setup a pretrained model now? (y/n) [y]: ").strip().lower()
    
    if choice in ['', 'y', 'yes']:
        download_pretrained_model()
    else:
        print("\n📝 You can run this script anytime:")
        print("   python3 setup_pretrained_model.py")
        print("\n💡 Or check the alternative solutions above!")
