#!/usr/bin/env python3
"""
Download dataset and models from Google Drive
"""

import os
import sys

def install_gdown():
    """Install gdown if not available"""
    try:
        import gdown
        return True
    except ImportError:
        print("📦 Installing gdown...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "gdown"])
        import gdown
        return True

def download_from_drive(url, output_path, filename=None):
    """Download file from Google Drive"""
    import gdown
    
    # Extract file ID from URL if it's a sharing link
    if 'drive.google.com' in url:
        if '/file/d/' in url:
            file_id = url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in url:
            file_id = url.split('id=')[1].split('&')[0]
        else:
            file_id = url
        
        url = f'https://drive.google.com/uc?id={file_id}'
    
    print(f"📥 Downloading from Google Drive...")
    print(f"   URL: {url}")
    print(f"   Destination: {output_path}")
    
    try:
        if filename:
            output = os.path.join(output_path, filename)
        else:
            output = output_path
        
        os.makedirs(os.path.dirname(output), exist_ok=True)
        
        gdown.download(url, output, quiet=False, fuzzy=True)
        
        print(f"✅ Downloaded successfully to {output}")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def extract_zip(zip_path, extract_to):
    """Extract ZIP file"""
    import zipfile
    
    print(f"📦 Extracting {zip_path}...")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        print(f"✅ Extracted to {extract_to}")
        
        # Remove zip file
        os.remove(zip_path)
        print(f"🗑️ Removed ZIP file")
        
        return True
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

def main():
    """Main function"""
    print("\n" + "="*60)
    print("📥 GOOGLE DRIVE DOWNLOADER")
    print("Dataset and Model Download Tool")
    print("="*60 + "\n")
    
    # Install gdown
    if not install_gdown():
        print("❌ Could not install gdown")
        return
    
    print("🔧 Choose what to download:")
    print("   1. Dataset (images)")
    print("   2. YOLO Model")
    print("   3. CNN Model")
    print("   4. All of the above")
    print("   5. Custom URL")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    base_path = "/home/pi/pfa"
    
    if choice == "1":
        # Download dataset
        print("\n📊 Dataset Download")
        url = input("Enter Google Drive URL for dataset: ").strip()
        
        if url:
            zip_path = os.path.join(base_path, "dataset.zip")
            if download_from_drive(url, zip_path):
                extract_zip(zip_path, os.path.join(base_path, "dataset"))
    
    elif choice == "2":
        # Download YOLO model
        print("\n🤖 YOLO Model Download")
        url = input("Enter Google Drive URL for YOLO model (.pt): ").strip()
        
        if url:
            output_path = os.path.join(base_path, "models", "yolo_best.pt")
            download_from_drive(url, output_path)
    
    elif choice == "3":
        # Download CNN model
        print("\n🧠 CNN Model Download")
        url = input("Enter Google Drive URL for CNN model (.h5): ").strip()
        
        if url:
            output_path = os.path.join(base_path, "models", "cnn_pest_best.h5")
            download_from_drive(url, output_path)
    
    elif choice == "4":
        # Download all
        print("\n📦 Downloading All")
        
        print("\n1️⃣ Dataset")
        url = input("Enter Google Drive URL for dataset: ").strip()
        if url:
            zip_path = os.path.join(base_path, "dataset.zip")
            if download_from_drive(url, zip_path):
                extract_zip(zip_path, os.path.join(base_path, "dataset"))
        
        print("\n2️⃣ YOLO Model")
        url = input("Enter Google Drive URL for YOLO model: ").strip()
        if url:
            output_path = os.path.join(base_path, "models", "yolo_best.pt")
            download_from_drive(url, output_path)
        
        print("\n3️⃣ CNN Model")
        url = input("Enter Google Drive URL for CNN model: ").strip()
        if url:
            output_path = os.path.join(base_path, "models", "cnn_pest_best.h5")
            download_from_drive(url, output_path)
    
    elif choice == "5":
        # Custom download
        print("\n🔗 Custom Download")
        url = input("Enter Google Drive URL: ").strip()
        filename = input("Enter output filename (e.g., model.pt): ").strip()
        
        if url and filename:
            output_path = os.path.join(base_path, filename)
            download_from_drive(url, output_path)
    
    else:
        print("❌ Invalid choice")
    
    print("\n" + "="*60)
    print("✅ Download process complete!")
    print("="*60 + "\n")
    
    # Show what we have
    print("📂 Current files:")
    
    models_dir = os.path.join(base_path, "models")
    if os.path.exists(models_dir):
        models = os.listdir(models_dir)
        if models:
            print("\n🤖 Models:")
            for m in models:
                size = os.path.getsize(os.path.join(models_dir, m)) / (1024**2)
                print(f"   ✓ {m} ({size:.1f} MB)")
    
    dataset_dir = os.path.join(base_path, "dataset")
    if os.path.exists(dataset_dir):
        splits = ['train', 'val', 'test']
        for split in splits:
            split_path = os.path.join(dataset_dir, split)
            if os.path.exists(split_path):
                classes = [d for d in os.listdir(split_path) 
                          if os.path.isdir(os.path.join(split_path, d))]
                if classes:
                    total = sum(len(os.listdir(os.path.join(split_path, c))) 
                               for c in classes)
                    print(f"\n📊 {split.capitalize()}: {len(classes)} classes, {total} images")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
