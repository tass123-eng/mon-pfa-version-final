#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pest Detection Ensemble System - Optimized for Raspberry Pi 4 B+
Combined CNN + YOLO model inference with intelligent ensemble
Author: Optimized for Raspberry Pi
Date: January 2026
"""

import os
import sys
import subprocess
import shutil
import random
import gc
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import cv2

# Matplotlib configuration for headless operation
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for RPi
import matplotlib.pyplot as plt
import seaborn as sns

# TensorFlow optimization for Raspberry Pi
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import tensorflow as tf
# Configure TensorFlow for Raspberry Pi 4 B+
tf.config.set_visible_devices([], 'GPU')  # Disable GPU (not available on RPi)
tf.config.threading.set_intra_op_parallelism_threads(4)  # RPi 4 has 4 cores
tf.config.threading.set_inter_op_parallelism_threads(4)

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    roc_curve,
    auc,
    accuracy_score
)
from sklearn.preprocessing import label_binarize
from sklearn.utils.class_weight import compute_class_weight

# YOLO - Install if needed
try:
    from ultralytics import YOLO
except ModuleNotFoundError:
    print("⚠️ Installing ultralytics...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ultralytics"])
    from ultralytics import YOLO

# ============================
# 🔧 CONFIGURATION FOR RASPBERRY PI
# ============================
class Config:
    """Configuration optimized for Raspberry Pi 4 B+"""
    
    # Paths - Adjust these for your setup
    DATA_ROOT = "/home/pi/pfa/dataset"
    MODEL_DIR = "/home/pi/pfa/models"
    OUTPUT_DIR = "/home/pi/pfa/outputs"
    
    CNN_PATH = os.path.join(MODEL_DIR, "cnn_pest_best.h5")
    YOLO_PATH = os.path.join(MODEL_DIR, "yolo_best.pt")
    
    # Dataset directories
    TRAIN_DIR = os.path.join(DATA_ROOT, "train")
    VAL_DIR = os.path.join(DATA_ROOT, "val")
    TEST_DIR = os.path.join(DATA_ROOT, "test")
    
    # Optimized parameters for RPi 4 B+ (4GB RAM)
    IMG_SIZE = (224, 224)
    BATCH_SIZE = 8  # Reduced for memory constraints
    NUM_THREADS = 4  # RPi 4 has 4 cores
    
    # Ensemble parameters
    ALPHA = 0.85  # YOLO weight
    BETA = 0.15   # CNN weight
    CONFIDENCE_THRESHOLD = 0.75
    
    # Target class for detection
    TARGET_CLASS = "Grasshopper"
    CONF_THRESHOLD_PERCENT = 70


# ============================
# 🛠️ UTILITY FUNCTIONS
# ============================
def clear_memory():
    """Clear memory to prevent OOM on Raspberry Pi"""
    gc.collect()
    tf.keras.backend.clear_session()


def ensure_directories():
    """Create necessary directories"""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(Config.MODEL_DIR, exist_ok=True)
    print(f"✅ Output directory: {Config.OUTPUT_DIR}")


def check_dataset():
    """Verify dataset structure"""
    if not os.path.exists(Config.DATA_ROOT):
        print(f"❌ Dataset not found at {Config.DATA_ROOT}")
        print("Please create the dataset directory with train/val/test subdirectories")
        return False
    
    for split in ['train', 'val', 'test']:
        split_dir = os.path.join(Config.DATA_ROOT, split)
        if os.path.exists(split_dir):
            classes = [d for d in os.listdir(split_dir) 
                      if os.path.isdir(os.path.join(split_dir, d))]
            print(f"✅ {split}: {len(classes)} classes found")
        else:
            print(f"⚠️ {split} directory not found")
    
    return True


def split_dataset(source_dir, output_dir, ratio=(0.7, 0.2, 0.1)):
    """
    Split dataset into train/val/test
    Optimized for Raspberry Pi - avoids loading entire dataset into memory
    """
    print(f"📂 Splitting dataset from {source_dir}...")
    
    try:
        import splitfolders
    except ImportError:
        print("Installing split-folders...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "split-folders"])
        import splitfolders
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    splitfolders.ratio(
        source_dir,
        output=output_dir,
        seed=42,
        ratio=ratio,
        group_prefix=None
    )
    
    print("✅ Dataset split complete")


# ============================
# 📊 DATA GENERATORS
# ============================
def create_generators():
    """Create data generators optimized for Raspberry Pi"""
    
    # Reduced augmentation for faster processing on RPi
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        zoom_range=0.2,
        width_shift_range=0.15,
        height_shift_range=0.15,
        horizontal_flip=True,
        fill_mode="nearest"
    )
    
    # No augmentation for val/test
    val_test_datagen = ImageDataGenerator(rescale=1./255)
    
    generators = {}
    
    # Create generators only for existing directories
    if os.path.exists(Config.TRAIN_DIR):
        generators['train'] = train_datagen.flow_from_directory(
            Config.TRAIN_DIR,
            target_size=Config.IMG_SIZE,
            batch_size=Config.BATCH_SIZE,
            class_mode="categorical",
            shuffle=True
        )
        print(f"✅ Train generator: {generators['train'].samples} samples")
    
    if os.path.exists(Config.VAL_DIR):
        generators['val'] = val_test_datagen.flow_from_directory(
            Config.VAL_DIR,
            target_size=Config.IMG_SIZE,
            batch_size=Config.BATCH_SIZE,
            class_mode="categorical",
            shuffle=False
        )
        print(f"✅ Val generator: {generators['val'].samples} samples")
    
    if os.path.exists(Config.TEST_DIR):
        generators['test'] = val_test_datagen.flow_from_directory(
            Config.TEST_DIR,
            target_size=Config.IMG_SIZE,
            batch_size=Config.BATCH_SIZE,
            class_mode="categorical",
            shuffle=False
        )
        print(f"✅ Test generator: {generators['test'].samples} samples")
    
    return generators


# ============================
# 🤖 MODEL LOADING & INFERENCE
# ============================
class ModelInference:
    """Handles model loading and inference optimized for Raspberry Pi"""
    
    def __init__(self):
        self.cnn_model = None
        self.yolo_model = None
        self.class_names = None
        self.num_classes = None
    
    def load_cnn(self):
        """Load CNN model with memory optimization"""
        if not os.path.isfile(Config.CNN_PATH):
            print(f"⚠️ CNN model not found at {Config.CNN_PATH}")
            return False
        
        print(f"🔄 Loading CNN model from {Config.CNN_PATH}...")
        clear_memory()
        
        try:
            self.cnn_model = tf.keras.models.load_model(
                Config.CNN_PATH, 
                compile=False
            )
            print("✅ CNN model loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Error loading CNN: {e}")
            return False
    
    def load_yolo(self):
        """Load YOLO model"""
        if not os.path.isfile(Config.YOLO_PATH):
            print(f"⚠️ YOLO model not found at {Config.YOLO_PATH}")
            return False
        
        print(f"🔄 Loading YOLO model from {Config.YOLO_PATH}...")
        
        try:
            self.yolo_model = YOLO(Config.YOLO_PATH)
            print("✅ YOLO model loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Error loading YOLO: {e}")
            return False
    
    def predict_cnn_batch(self, generator, verbose=0):
        """
        CNN predictions in batches to manage memory on Raspberry Pi
        """
        if self.cnn_model is None:
            raise ValueError("CNN model not loaded")
        
        print("🔄 Running CNN inference...")
        predictions = []
        
        steps = len(generator)
        for i in range(steps):
            batch_x, _ = next(generator)
            batch_pred = self.cnn_model.predict(batch_x, verbose=0)
            predictions.append(batch_pred)
            
            if verbose and (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{steps} batches")
            
            # Clear memory periodically
            if (i + 1) % 20 == 0:
                gc.collect()
        
        predictions = np.vstack(predictions)
        print(f"✅ CNN inference complete: {len(predictions)} predictions")
        
        return predictions
    
    def predict_yolo_stream(self, filepaths, imgsz=224):
        """
        YOLO predictions with streaming for memory efficiency
        """
        if self.yolo_model is None:
            raise ValueError("YOLO model not loaded")
        
        print("🔄 Running YOLO inference...")
        
        # Process in smaller batches to avoid memory issues
        batch_size = 16
        all_probs = []
        
        for i in range(0, len(filepaths), batch_size):
            batch_paths = filepaths[i:i + batch_size]
            
            results = self.yolo_model(
                source=batch_paths,
                imgsz=imgsz,
                device="cpu",
                verbose=False,
                stream=False
            )
            
            for r in results:
                if hasattr(r, 'probs') and r.probs is not None:
                    probs = r.probs.data.cpu().numpy()
                    all_probs.append(probs)
                else:
                    # Fallback for no detection
                    all_probs.append(np.zeros(self.num_classes))
            
            if (i + batch_size) % 100 == 0:
                print(f"  Processed {min(i + batch_size, len(filepaths))}/{len(filepaths)} images")
            
            # Clear memory
            gc.collect()
        
        predictions = np.array(all_probs)
        print(f"✅ YOLO inference complete: {len(predictions)} predictions")
        
        return predictions


# ============================
# 🎯 ENSEMBLE METHODS
# ============================
def ensemble_weighted(cnn_probs, yolo_probs, alpha=None, beta=None):
    """Weighted ensemble: alpha*YOLO + beta*CNN"""
    if alpha is None:
        alpha = Config.ALPHA
    if beta is None:
        beta = Config.BETA
    
    min_len = min(len(cnn_probs), len(yolo_probs))
    ensemble_probs = alpha * yolo_probs[:min_len] + beta * cnn_probs[:min_len]
    
    return ensemble_probs


def ensemble_smart(cnn_probs, yolo_probs, threshold=None):
    """
    Smart ensemble: Use CNN confidence to decide weighting
    If CNN is very confident (>threshold), average both models
    Otherwise, trust YOLO more
    """
    if threshold is None:
        threshold = Config.CONFIDENCE_THRESHOLD
    
    final_probs = []
    min_len = min(len(cnn_probs), len(yolo_probs))
    
    for i in range(min_len):
        cnn_confidence = np.max(cnn_probs[i])
        
        if cnn_confidence > threshold:
            # High CNN confidence: average both
            final_probs.append((cnn_probs[i] + yolo_probs[i]) / 2.0)
        else:
            # Low CNN confidence: trust YOLO more
            final_probs.append(yolo_probs[i])
    
    return np.array(final_probs)


# ============================
# 📈 EVALUATION & VISUALIZATION
# ============================
def evaluate_model(y_true, y_pred, model_name="Model"):
    """Calculate and print accuracy"""
    accuracy = accuracy_score(y_true, y_pred)
    print(f"📊 {model_name} Accuracy: {accuracy:.4f}")
    return accuracy


def plot_confusion_matrix(y_true, y_pred, class_names, title, save_path=None):
    """Plot confusion matrix optimized for RPi"""
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm, 
        annot=False,  # Disable annotation for many classes
        fmt='d', 
        cmap='Blues',
        xticklabels=class_names,
        yticklabels=class_names
    )
    plt.title(title)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()
    
    if save_path is None:
        save_path = os.path.join(Config.OUTPUT_DIR, f"{title.replace(' ', '_')}.png")
    
    plt.savefig(save_path, dpi=100, bbox_inches='tight')
    plt.close()
    print(f"✅ Confusion matrix saved to {save_path}")
    
    # Print classification report
    print(f"\nClassification Report - {title}")
    print(classification_report(y_true, y_pred, target_names=class_names, zero_division=0))


def plot_roc_curve(y_true, ensemble_probs, num_classes, class_names, save_path=None):
    """Plot ROC curve (macro average)"""
    y_true_bin = label_binarize(y_true, classes=np.arange(num_classes))
    
    # Calculate ROC for each class
    fpr = {}
    tpr = {}
    roc_auc = {}
    
    for i in range(num_classes):
        fpr[i], tpr[i], _ = roc_curve(y_true_bin[:, i], ensemble_probs[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])
    
    # Compute macro-average ROC
    all_fpr = np.unique(np.concatenate([fpr[i] for i in range(num_classes)]))
    mean_tpr = np.zeros_like(all_fpr)
    for i in range(num_classes):
        mean_tpr += np.interp(all_fpr, fpr[i], tpr[i])
    mean_tpr /= num_classes
    
    roc_auc_macro = auc(all_fpr, mean_tpr)
    
    # Plot
    plt.figure(figsize=(8, 6))
    plt.plot(all_fpr, mean_tpr, label=f'ROC macro (AUC = {roc_auc_macro:.3f})', linewidth=2)
    plt.plot([0, 1], [0, 1], 'k--', label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve - Ensemble Model')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if save_path is None:
        save_path = os.path.join(Config.OUTPUT_DIR, "roc_curve.png")
    
    plt.savefig(save_path, dpi=100, bbox_inches='tight')
    plt.close()
    print(f"✅ ROC curve saved to {save_path}")


def plot_comparison(accuracies, labels, title="Model Comparison", save_path=None):
    """Plot accuracy comparison bar chart"""
    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, accuracies, color=['#3498db', '#e74c3c', '#2ecc71'])
    
    # Add value labels on bars
    for bar, acc in zip(bars, accuracies):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{acc:.3f}', ha='center', va='bottom', fontweight='bold')
    
    plt.ylim(0, 1.0)
    plt.ylabel('Accuracy')
    plt.title(title)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    if save_path is None:
        save_path = os.path.join(Config.OUTPUT_DIR, "model_comparison.png")
    
    plt.savefig(save_path, dpi=100, bbox_inches='tight')
    plt.close()
    print(f"✅ Comparison chart saved to {save_path}")


# ============================
# 🦗 DETECTION DEMO
# ============================
def detect_pests(image_paths, model_inference, n_display=8):
    """
    Detect pests in images and display results
    Optimized for Raspberry Pi
    """
    print(f"\n🦗 Running pest detection on {len(image_paths)} images...")
    
    # Randomly sample images if too many
    if len(image_paths) > n_display:
        image_paths = random.sample(image_paths, n_display)
    
    # Run YOLO inference
    results = model_inference.yolo_model(
        source=image_paths,
        imgsz=224,
        device="cpu",
        verbose=False
    )
    
    # Create figure
    fig_height = 4 * ((n_display + 1) // 2)
    plt.figure(figsize=(12, fig_height))
    
    for i, (img_path, r) in enumerate(zip(image_paths, results)):
        # Read image
        img = cv2.imread(img_path)
        if img is None:
            continue
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Get prediction
        pred_class = r.names[r.probs.top1] if hasattr(r.probs, 'top1') else "Unknown"
        confidence = float(r.probs.top1conf) * 100 if hasattr(r.probs, 'top1conf') else 0.0
        
        # Determine if target pest is detected
        if pred_class == Config.TARGET_CLASS and confidence >= Config.CONF_THRESHOLD_PERCENT:
            decision = f"🦗 {Config.TARGET_CLASS.upper()} DETECTED"
            color = 'green'
        else:
            decision = f"❌ NOT {Config.TARGET_CLASS.upper()}"
            color = 'red'
        
        # Plot
        plt.subplot((n_display + 1) // 2, 2, i + 1)
        plt.imshow(img)
        plt.axis('off')
        plt.title(f"{pred_class} — {confidence:.1f}%\n{decision}",
                 color=color, fontsize=10, fontweight='bold')
    
    plt.suptitle(f'🦗 {Config.TARGET_CLASS} Detection - YOLO Classification', 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    save_path = os.path.join(Config.OUTPUT_DIR, "pest_detection_results.png")
    plt.savefig(save_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Detection results saved to {save_path}")


# ============================
# 🎯 MAIN EXECUTION
# ============================
def run_ensemble_evaluation(split='test'):
    """
    Main function to run ensemble model evaluation
    Optimized workflow for Raspberry Pi
    """
    print("\n" + "="*60)
    print("🦗 PEST DETECTION ENSEMBLE SYSTEM")
    print("Optimized for Raspberry Pi 4 B+")
    print("="*60 + "\n")
    
    # Setup
    ensure_directories()
    
    # Check dataset
    if not check_dataset():
        print("\n⚠️ Please ensure your dataset is properly structured:")
        print(f"   {Config.DATA_ROOT}/")
        print("   ├── train/")
        print("   │   ├── class1/")
        print("   │   └── class2/")
        print("   ├── val/")
        print("   └── test/")
        return
    
    # Create data generators
    print("\n📊 Creating data generators...")
    generators = create_generators()
    
    if split not in generators:
        print(f"❌ {split} split not available")
        return
    
    generator = generators[split]
    y_true = generator.classes
    class_names = list(generator.class_indices.keys())
    num_classes = len(class_names)
    
    print(f"\n✅ Dataset loaded:")
    print(f"   Split: {split}")
    print(f"   Classes: {num_classes}")
    print(f"   Samples: {len(y_true)}")
    
    # Initialize model inference
    model_inf = ModelInference()
    model_inf.class_names = class_names
    model_inf.num_classes = num_classes
    
    # Load models
    print("\n🤖 Loading models...")
    cnn_loaded = model_inf.load_cnn()
    yolo_loaded = model_inf.load_yolo()
    
    if not (cnn_loaded and yolo_loaded):
        print("\n⚠️ Could not load both models. Please check model paths:")
        print(f"   CNN:  {Config.CNN_PATH}")
        print(f"   YOLO: {Config.YOLO_PATH}")
        return
    
    # CNN predictions
    print(f"\n🔄 Running CNN inference on {split} set...")
    clear_memory()
    generator.reset()  # Reset generator
    cnn_probs = model_inf.predict_cnn_batch(generator, verbose=1)
    y_pred_cnn = np.argmax(cnn_probs, axis=1)
    acc_cnn = evaluate_model(y_true, y_pred_cnn, "CNN")
    
    # YOLO predictions
    print(f"\n🔄 Running YOLO inference on {split} set...")
    clear_memory()
    filepaths = generator.filepaths
    yolo_probs = model_inf.predict_yolo_stream(filepaths)
    y_pred_yolo = np.argmax(yolo_probs, axis=1)
    acc_yolo = evaluate_model(y_true, y_pred_yolo, "YOLO")
    
    # Ensemble predictions
    print("\n🔄 Computing ensemble predictions...")
    
    # Weighted ensemble
    ens_weighted_probs = ensemble_weighted(cnn_probs, yolo_probs)
    y_pred_weighted = np.argmax(ens_weighted_probs, axis=1)
    acc_weighted = evaluate_model(y_true[:len(y_pred_weighted)], y_pred_weighted, 
                                  "Weighted Ensemble")
    
    # Smart ensemble
    ens_smart_probs = ensemble_smart(cnn_probs, yolo_probs)
    y_pred_smart = np.argmax(ens_smart_probs, axis=1)
    acc_smart = evaluate_model(y_true[:len(y_pred_smart)], y_pred_smart, 
                               "Smart Ensemble")
    
    # Visualizations
    print("\n📊 Generating visualizations...")
    
    # Comparison chart
    plot_comparison(
        [acc_cnn, acc_yolo, acc_smart],
        ['CNN', 'YOLO', 'Smart Ensemble'],
        f'Model Comparison - {split.capitalize()} Set'
    )
    
    # Confusion matrix for best model (smart ensemble)
    plot_confusion_matrix(
        y_true[:len(y_pred_smart)],
        y_pred_smart,
        class_names,
        f'Smart Ensemble - {split.capitalize()} Set'
    )
    
    # ROC curve
    plot_roc_curve(
        y_true[:len(ens_smart_probs)],
        ens_smart_probs,
        num_classes,
        class_names
    )
    
    # Detection demo (if validation set exists)
    if split == 'val' and os.path.exists(Config.VAL_DIR):
        print("\n🦗 Running detection demo...")
        all_images = []
        for cls in os.listdir(Config.VAL_DIR):
            cls_path = os.path.join(Config.VAL_DIR, cls)
            if os.path.isdir(cls_path):
                for img in os.listdir(cls_path):
                    if img.lower().endswith(('.jpg', '.png', '.jpeg')):
                        all_images.append(os.path.join(cls_path, img))
        
        if all_images:
            detect_pests(all_images, model_inf, n_display=8)
    
    # Summary
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    print(f"CNN Accuracy:            {acc_cnn:.4f}")
    print(f"YOLO Accuracy:           {acc_yolo:.4f}")
    print(f"Weighted Ensemble:       {acc_weighted:.4f}")
    print(f"Smart Ensemble:          {acc_smart:.4f} ⭐")
    print("="*60)
    print(f"\n✅ All results saved to: {Config.OUTPUT_DIR}")
    
    clear_memory()


def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Pest Detection Ensemble System for Raspberry Pi'
    )
    parser.add_argument(
        '--split',
        type=str,
        default='test',
        choices=['train', 'val', 'test'],
        help='Dataset split to evaluate on (default: test)'
    )
    parser.add_argument(
        '--data-root',
        type=str,
        help='Path to dataset root directory'
    )
    parser.add_argument(
        '--cnn-model',
        type=str,
        help='Path to CNN model file'
    )
    parser.add_argument(
        '--yolo-model',
        type=str,
        help='Path to YOLO model file'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=8,
        help='Batch size for inference (default: 8)'
    )
    
    args = parser.parse_args()
    
    # Override config if provided
    if args.data_root:
        Config.DATA_ROOT = args.data_root
        Config.TRAIN_DIR = os.path.join(Config.DATA_ROOT, "train")
        Config.VAL_DIR = os.path.join(Config.DATA_ROOT, "val")
        Config.TEST_DIR = os.path.join(Config.DATA_ROOT, "test")
    
    if args.cnn_model:
        Config.CNN_PATH = args.cnn_model
    
    if args.yolo_model:
        Config.YOLO_PATH = args.yolo_model
    
    if args.batch_size:
        Config.BATCH_SIZE = args.batch_size
    
    # Run evaluation
    try:
        run_ensemble_evaluation(split=args.split)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
