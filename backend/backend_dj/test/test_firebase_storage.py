#!/usr/bin/env python3
"""
Test Image Optimization & Upload to Firebase Storage
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('/home/cao-le/Flutter Projects/pizza_ordering_app/backend/backend_dj/.env')

# Thêm backend_dj vào Python path
sys.path.insert(0, '/home/cao-le/Flutter Projects/pizza_ordering_app/backend')

from firebase_admin import credentials, initialize_app, storage
from backend_dj.helper.image_helper import ImageOptimizer
import uuid

KEY_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')
if KEY_PATH:
    KEY_PATH = KEY_PATH.replace('\\ ', ' ')
BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')

if not KEY_PATH or not BUCKET:
    raise RuntimeError("Missing FIREBASE_CREDENTIALS_PATH or FIREBASE_STORAGE_BUCKET in .env")

# Image config
IMAGE_PATH = "/home/cao-le/Pictures/cpomo__icon.png"

def main():
    try:
        # Step 1: Read image
        print(f"📖 Reading image from: {IMAGE_PATH}")
        if not os.path.exists(IMAGE_PATH):
            print(f"❌ File not found: {IMAGE_PATH}")
            return
        
        with open(IMAGE_PATH, 'rb') as f:
            image_bytes = f.read()
        print(f"✅ Loaded {len(image_bytes) / 1024:.1f}KB")
        
        # Step 2: Optimize using ImageOptimizer
        print("\n🖼️ Processing image (validate → optimize → thumbnail)...")
        result = ImageOptimizer.process_image_complete(
            image_bytes,
            max_width=1920,
            quality=80,
            output_format="webp",
            create_thumb=True,
            thumb_width=400,
            thumb_quality=75
        )
        
        if not result["is_valid"]:
            print(f"❌ Validation failed: {result['error']}")
            return
        
        # Step 3: Print optimization results
        print(f"✅ Optimization successful!")
        print(f"  Original info:")
        print(f"    - Size: {result['info']['size_kb']:.1f}KB")
        print(f"    - Dimensions: {result['info']['width']}x{result['info']['height']}")
        print(f"    - Format: {result['info']['format']}")
        print(f"  Optimized:")
        print(f"    - Size: {len(result['optimized_bytes']) / 1024:.1f}KB")
        print(f"    - Compression: {result['compression_ratio']}x")
        print(f"    - Type: {result['optimized_type']}")
        if result['thumbnail_bytes']:
            print(f"  Thumbnail:")
            print(f"    - Size: {len(result['thumbnail_bytes']) / 1024:.1f}KB")
            print(f"    - Type: {result['thumbnail_type']}")
        
        # Step 4: Initialize Firebase
        print("\n🔥 Initializing Firebase...")
        cred = credentials.Certificate(KEY_PATH)
        initialize_app(cred, {"storageBucket": BUCKET})
        bucket = storage.bucket()
        print(f"✅ Connected to bucket: {bucket.name}")
        
        # Step 5: Upload optimized image
        unique_id = uuid.uuid4().hex[:8]
        optimized_path = f"test_optimized/cpomo_{unique_id}.webp"
        thumbnail_path = f"test_optimized/cpomo_{unique_id}_thumb.webp"
        
        print(f"\n📤 Uploading optimized image...")
        blob_main = bucket.blob(optimized_path)
        blob_main.upload_from_string(
            result['optimized_bytes'],
            content_type=result['optimized_type']
        )
        print(f"✅ Uploaded: {optimized_path}")
        
        # Step 6: Upload thumbnail
        if result['thumbnail_bytes']:
            print(f"📤 Uploading thumbnail...")
            blob_thumb = bucket.blob(thumbnail_path)
            blob_thumb.upload_from_string(
                result['thumbnail_bytes'],
                content_type=result['thumbnail_type']
            )
            print(f"✅ Uploaded: {thumbnail_path}")
        
        # Step 7: Summary
        print("\n" + "="*60)
        print("✨ SUCCESS! Image optimization & upload complete.")
        print("="*60)
        print(f"\n📁 Firebase paths:")
        print(f"  - Main: gs://{BUCKET}/{optimized_path}")
        print(f"  - Thumb: gs://{BUCKET}/{thumbnail_path}")
        print(f"\nNext step: Use these URLs in your Item model's image_url & piece_image_url fields")
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()