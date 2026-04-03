#!/usr/bin/env python3
"""
Quick test script to verify Raspberry Pi setup
Run this after installation to check if everything is working
"""

import sys
import os

def test_imports():
    """Test if all required packages can be imported"""
    print("="*60)
    print("Testing Python Package Imports")
    print("="*60)
    
    tests = []
    
    # Test numpy
    try:
        import numpy as np
        print(f"✅ numpy {np.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"❌ numpy: {e}")
        tests.append(False)
    
    # Test OpenCV
    try:
        import cv2
        print(f"✅ opencv {cv2.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"❌ opencv: {e}")
        tests.append(False)
    
    # Test matplotlib
    try:
        import matplotlib
        print(f"✅ matplotlib {matplotlib.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"❌ matplotlib: {e}")
        tests.append(False)
    
    # Test TensorFlow
    try:
        import tensorflow as tf
        print(f"✅ tensorflow {tf.__version__}")
        # Test if it works
        tf.constant([1, 2, 3])
        tests.append(True)
    except ImportError as e:
        print(f"❌ tensorflow: {e}")
        tests.append(False)
    except Exception as e:
        print(f"⚠️ tensorflow imported but error on test: {e}")
        tests.append(False)
    
    # Test PyTorch
    try:
        import torch
        print(f"✅ torch {torch.__version__}")
        # Test if it works
        torch.tensor([1, 2, 3])
        tests.append(True)
    except ImportError as e:
        print(f"❌ torch: {e}")
        tests.append(False)
    except Exception as e:
        print(f"⚠️ torch imported but error on test: {e}")
        tests.append(False)
    
    # Test scikit-learn
    try:
        import sklearn
        print(f"✅ sklearn {sklearn.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"❌ sklearn: {e}")
        tests.append(False)
    
    # Test ultralytics
    try:
        from ultralytics import YOLO
        import ultralytics
        print(f"✅ ultralytics {ultralytics.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"❌ ultralytics: {e}")
        tests.append(False)
    
    # Test seaborn
    try:
        import seaborn as sns
        print(f"✅ seaborn {sns.__version__}")
        tests.append(True)
    except ImportError as e:
        print(f"❌ seaborn: {e}")
        tests.append(False)
    
    print("\n" + "="*60)
    passed = sum(tests)
    total = len(tests)
    print(f"Results: {passed}/{total} packages imported successfully")
    print("="*60)
    
    return all(tests)


def test_directories():
    """Test if required directories exist"""
    print("\n" + "="*60)
    print("Testing Directory Structure")
    print("="*60)
    
    base_dir = "/home/pi/pfa"
    required_dirs = [
        "dataset",
        "models",
        "outputs",
        "dataset/train",
        "dataset/val",
        "dataset/test"
    ]
    
    tests = []
    for dir_name in required_dirs:
        full_path = os.path.join(base_dir, dir_name)
        if os.path.exists(full_path):
            print(f"✅ {full_path}")
            tests.append(True)
        else:
            print(f"❌ {full_path} (missing)")
            tests.append(False)
    
    print("\n" + "="*60)
    passed = sum(tests)
    total = len(tests)
    print(f"Results: {passed}/{total} directories exist")
    print("="*60)
    
    return all(tests)


def test_files():
    """Test if required files exist"""
    print("\n" + "="*60)
    print("Testing Required Files")
    print("="*60)
    
    base_dir = "/home/pi/pfa"
    required_files = [
        "pfa_mixage.py",
        "requirements.txt",
        "README.md",
        "QUICKSTART.md",
        "setup.sh"
    ]
    
    tests = []
    for file_name in required_files:
        full_path = os.path.join(base_dir, file_name)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"✅ {file_name} ({size} bytes)")
            tests.append(True)
        else:
            print(f"❌ {file_name} (missing)")
            tests.append(False)
    
    print("\n" + "="*60)
    passed = sum(tests)
    total = len(tests)
    print(f"Results: {passed}/{total} files exist")
    print("="*60)
    
    return all(tests)


def test_models():
    """Test if model files exist"""
    print("\n" + "="*60)
    print("Testing Model Files")
    print("="*60)
    
    base_dir = "/home/pi/pfa/models"
    model_files = [
        "cnn_pest_best.h5",
        "yolo_best.pt"
    ]
    
    tests = []
    for file_name in model_files:
        full_path = os.path.join(base_dir, file_name)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path) / (1024 * 1024)  # MB
            print(f"✅ {file_name} ({size:.2f} MB)")
            tests.append(True)
        else:
            print(f"⚠️ {file_name} (not found - you need to add this)")
            tests.append(False)
    
    if not any(tests):
        print("\n⚠️ No model files found. You need to:")
        print("   1. Copy your CNN model to: /home/pi/pfa/models/cnn_pest_best.h5")
        print("   2. Copy your YOLO model to: /home/pi/pfa/models/yolo_best.pt")
    
    print("\n" + "="*60)
    passed = sum(tests)
    total = len(tests)
    print(f"Results: {passed}/{total} model files exist")
    print("="*60)
    
    return any(tests)  # At least one model is OK


def test_dataset():
    """Check if dataset has content"""
    print("\n" + "="*60)
    print("Testing Dataset Content")
    print("="*60)
    
    base_dir = "/home/pi/pfa/dataset"
    splits = ['train', 'val', 'test']
    
    has_data = False
    
    for split in splits:
        split_path = os.path.join(base_dir, split)
        if os.path.exists(split_path):
            classes = [d for d in os.listdir(split_path) 
                      if os.path.isdir(os.path.join(split_path, d))]
            
            if classes:
                total_images = 0
                for cls in classes:
                    cls_path = os.path.join(split_path, cls)
                    images = [f for f in os.listdir(cls_path) 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    total_images += len(images)
                
                print(f"✅ {split}: {len(classes)} classes, {total_images} images")
                has_data = True
            else:
                print(f"⚠️ {split}: Empty (no class folders)")
        else:
            print(f"❌ {split}: Directory not found")
    
    if not has_data:
        print("\n⚠️ No dataset found. You need to:")
        print("   1. Organize your images into class folders")
        print("   2. Place them in /home/pi/pfa/dataset/train|val|test/")
        print("\n   Expected structure:")
        print("   dataset/")
        print("   ├── train/")
        print("   │   ├── class1/")
        print("   │   │   ├── img1.jpg")
        print("   │   │   └── img2.jpg")
        print("   │   └── class2/")
        print("   ├── val/")
        print("   └── test/")
    
    print("\n" + "="*60)
    print(f"Dataset status: {'✅ Ready' if has_data else '⚠️ Needs setup'}")
    print("="*60)
    
    return has_data


def test_system():
    """Test Raspberry Pi system resources"""
    print("\n" + "="*60)
    print("Testing System Resources")
    print("="*60)
    
    # Try to get temperature
    try:
        import subprocess
        temp_output = subprocess.check_output(['vcgencmd', 'measure_temp']).decode()
        print(f"🌡️ {temp_output.strip()}")
    except:
        print("⚠️ Could not read temperature (vcgencmd not available)")
    
    # Memory info
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            for line in lines[:3]:
                print(f"💾 {line.strip()}")
    except:
        print("⚠️ Could not read memory info")
    
    # CPU info
    try:
        with open('/proc/cpuinfo', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'model name' in line.lower() or 'Hardware' in line:
                    print(f"🖥️ {line.strip()}")
                    break
    except:
        print("⚠️ Could not read CPU info")
    
    print("="*60)
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🦗 PEST DETECTION SETUP TEST")
    print("Raspberry Pi 4 B+ Environment Check")
    print("="*60 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Python Packages", test_imports()))
    results.append(("Directory Structure", test_directories()))
    results.append(("Required Files", test_files()))
    results.append(("Model Files", test_models()))
    results.append(("Dataset", test_dataset()))
    results.append(("System", test_system()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 FINAL SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("="*60)
    print(f"Total: {passed}/{total} tests passed")
    print("="*60)
    
    # Final advice
    if passed == total:
        print("\n🎉 Excellent! Your setup is complete and ready to use!")
        print("\nNext steps:")
        print("1. Activate virtual environment: source venv/bin/activate")
        print("2. Run inference: python3 pfa_mixage.py --split test")
        print("3. Check results in: /home/pi/pfa/outputs/")
    elif passed >= total - 2:
        print("\n⚠️ Almost ready! A few items need attention:")
        print("- If models are missing: Copy your trained models to /home/pi/pfa/models/")
        print("- If dataset is empty: Organize your images in /home/pi/pfa/dataset/")
        print("\nOnce fixed, run: python3 pfa_mixage.py --split test")
    else:
        print("\n❌ Setup incomplete. Please:")
        print("1. Run setup script: ./setup.sh")
        print("2. Add your models and dataset")
        print("3. Run this test again: python3 test_setup.py")
    
    print("\nFor help, see README.md or QUICKSTART.md")
    print("")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
