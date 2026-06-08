from django.conf import settings
from io import BytesIO
from pathlib import Path
import requests
from pizza_management.shared.image_handler import LocalImageHandler
from pizza_management.shared.firebase_service import FirebaseStorageService


class ImageProcessor:
    """Shared image processing utilities"""
    
    @staticmethod
    def upload_image(image_file, folder="items"):
        """Upload image file to local or Firebase"""
        print(f"\n[ImageProcessor.upload_image] START")
        print(f"  File: {image_file.name if hasattr(image_file, 'name') else image_file}")
        print(f"  Folder: {folder}")
        print(f"  Storage type: {settings.STORAGE_TYPE}")
        
        try:
            if settings.USE_LOCAL_STORAGE:
                print(f"  → Using LOCAL storage")
                image_bytes = image_file.read()
                print(f"  ✓ Image read: {len(image_bytes)} bytes")
                
                result = LocalImageHandler.save_image(
                    image_bytes,
                    filename_hint=image_file.name,
                    folder=folder
                )
                print(f"  ✓ Local save result: {result}")
                print(f"[ImageProcessor.upload_image] SUCCESS\n")
                return result
            else:
                print(f"  → Using FIREBASE storage (optimized)")
                print(f"  Validating image...")
                FirebaseStorageService.is_valid_image(image_file)
                print(f"  ✓ Validation passed")
                image_bytes = image_file.read()
                
                result = FirebaseStorageService.upload_image_optimized(
                    image_bytes,
                    original_filename=image_file.name,
                    folder=folder
                )
                print(f"  ✓ Firebase optimized upload result: {result}")
                print(f"[ImageProcessor.upload_image] SUCCESS\n")
                return result
                
        except Exception as e:
            print(f"  ❌ Error uploading image: {e}")
            print(f"[ImageProcessor.upload_image] FAILED\n")
            return None

    @staticmethod
    def process_image_path(file_path, folder="items"):
        """Process image from filesystem path - resolves relative paths using Django BASE_DIR"""
        print(f"\n[ImageProcessor.process_image_path] START")
        print(f"  Input file path: {file_path}")
        print(f"  Folder: {folder}")
        print(f"  Storage type: {settings.STORAGE_TYPE}")
        
        try:
            # Attempt 1: Try absolute path first
            img_path = Path(file_path)
            if img_path.is_absolute() and img_path.exists():
                print(f"  ✓ Using absolute path: {img_path}")
                resolved_path = img_path
            else:
                # Attempt 2: Resolve relative to Django BASE_DIR
                base_dir = Path(settings.BASE_DIR)
                relative_path = base_dir / file_path
                print(f"  Attempting relative path vs BASE_DIR ({base_dir}):")
                print(f"    → {relative_path}")
                
                if relative_path.exists():
                    print(f"    ✓ Found at BASE_DIR-relative path")
                    resolved_path = relative_path
                else:
                    # Attempt 3: Try one level up (in case we're in backend_dj and path is from backend)
                    parent_path = base_dir.parent / file_path
                    print(f"    ✗ Not found, trying parent directory:")
                    print(f"      → {parent_path}")
                    
                    if parent_path.exists():
                        print(f"      ✓ Found at parent path")
                        resolved_path = parent_path
                    else:
                        # Attempt 4: List what we're looking for (debugging)
                        print(f"    ✗ Not found at parent either")
                        print(f"  ⚠ File not found after all attempts, returning original path")
                        print(f"[ImageProcessor.process_image_path] FILE NOT FOUND\n")
                        return file_path
            
            print(f"  Final resolved path: {resolved_path}")
            print(f"  Reading file...")
            with open(resolved_path, 'rb') as f:
                image_bytes = f.read()
            print(f"  ✓ File read: {len(image_bytes)} bytes")
            
            if settings.USE_LOCAL_STORAGE:
                print(f"  → Using LOCAL storage")
                result = LocalImageHandler.save_image(
                    image_bytes,
                    filename_hint=resolved_path.name,
                    folder=folder
                )
                print(f"  ✓ Local save result: {result}")
                print(f"[ImageProcessor.process_image_path] SUCCESS\n")
                return result
            else:
                print(f"  → Using FIREBASE storage (optimized)")
                result = FirebaseStorageService.upload_image_optimized(
                    image_bytes,
                    original_filename=resolved_path.name,
                    folder=folder
                )
                print(f"  ✓ Firebase optimized upload result: {result}")
                print(f"[ImageProcessor.process_image_path] SUCCESS\n")
                return result
                
        except Exception as e:
            print(f"  ❌ Error processing image: {e}")
            print(f"  Returning original file path as fallback")
            print(f"[ImageProcessor.process_image_path] ERROR (fallback)\n")
            return file_path

    @staticmethod
    def download_and_upload_image(image_url, folder="items"):
        """Download image from URL and upload to storage"""
        print(f"\n[ImageProcessor.download_and_upload_image] START")
        print(f"  Image URL: {image_url}")
        print(f"  Folder: {folder}")
        print(f"  Storage type: {settings.STORAGE_TYPE}")
        
        try:
            if not image_url or not isinstance(image_url, str):
                print(f"  ⚠ Invalid image URL, returning as-is")
                print(f"[ImageProcessor.download_and_upload_image] INVALID URL\n")
                return image_url
            
            # Download image from URL
            print(f"  Downloading image...")
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image_bytes = response.content
            print(f"  ✓ Downloaded: {len(image_bytes)} bytes")
            
            # Extract filename from URL
            filename = image_url.split('/')[-1].split('?')[0] or "image.png"
            print(f"  Filename hint: {filename}")
            
            if settings.USE_LOCAL_STORAGE:
                print(f"  → Using LOCAL storage")
                result = LocalImageHandler.save_image(
                    image_bytes,
                    filename_hint=filename,
                    folder=folder
                )
                print(f"  ✓ Local save result: {result}")
                print(f"[ImageProcessor.download_and_upload_image] SUCCESS\n")
                return result
            else:
                print(f"  → Using FIREBASE storage (optimized)")
                result = FirebaseStorageService.upload_image_optimized(
                    image_bytes,
                    original_filename=filename,
                    folder=folder
                )
                print(f"  ✓ Firebase optimized upload result: {result}")
                print(f"[ImageProcessor.download_and_upload_image] SUCCESS\n")
                return result
                
        except Exception as e:
            print(f"  ❌ Error downloading/uploading image: {e}")
            print(f"[ImageProcessor.download_and_upload_image] ERROR - returning None\n")
            return None