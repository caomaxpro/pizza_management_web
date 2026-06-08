"""
Local Image Handler - Save and delete images locally with optimization
"""
from pathlib import Path
import uuid
from django.conf import settings
from helper.image_helper import ImageOptimizer
from typing import Optional


class LocalImageHandler:
    """Handle local image storage with optimization"""
    
    INGREDIENTS_FOLDER = 'ingredients'
    
    @staticmethod
    def save_image(
        image_bytes: bytes,
        filename_hint: str = "image",
        folder: str = INGREDIENTS_FOLDER,
        max_width: int = 1920,
        quality: int = 100,
        output_format: str = "webp",
        optimize: bool = True
    ) -> Optional[str]:
        """
        Save image locally with optional optimization
        
        Args:
            image_bytes: Raw image bytes
            filename_hint: Original filename for reference
            folder: Subfolder in MEDIA_ROOT
            max_width: Max width for optimization (px)
            quality: Quality for optimization (0-100)
            output_format: Output format ('webp', 'jpeg', 'png')
            optimize: If True, optimize image
            
        Returns:
            Media URL to saved image, or None if save fails
        """
        try:
            # Create media directory
            media_dir = Path(settings.MEDIA_ROOT) / folder
            media_dir.mkdir(parents=True, exist_ok=True)
            
            # Optimize if requested
            if optimize:
                result = ImageOptimizer.process_image_complete(
                    image_bytes,
                    max_width=max_width,
                    quality=quality,
                    output_format=output_format,
                    create_thumb=True
                )
                
                if not result['is_valid']:
                    raise ValueError(f"Image optimization failed: {result['error']}")
                
                image_bytes = result['optimized_bytes']
                ext = '.webp'
                compression = result['compression_ratio']
                print(f"Image optimized: {filename_hint} (compression: {compression}x)")
            else:
                ext = Path(filename_hint).suffix
            
            # Generate unique filename
            filename = f"{uuid.uuid4().hex[:8]}_image{ext}"
            file_path = media_dir / filename
            
            # Save to disk
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            
            # Return media URL
            media_url = str(settings.MEDIA_URL).rstrip('/') + '/'
            url = f"{media_url}{folder}/{filename}"
            print(f"Saved image locally: {url}")
            return url
            
        except Exception as e:
            print(f"Error saving local image: {e}")
            return None
    
    @staticmethod
    def delete_image(image_url: str) -> bool:
        """Delete image from local media folder"""
        try:
            if not image_url or '/media/' not in image_url:
                return False
            
            media_root = Path(settings.MEDIA_ROOT)
            relative_path = image_url.split('/media/')[-1]
            file_path = media_root / relative_path
            
            if file_path.exists():
                file_path.unlink()
                print(f"Deleted local image: {file_path}")
                return True
            else:
                print(f"Image not found: {file_path}")
                return False
                
        except Exception as e:
            print(f"Error deleting local image: {e}")
            raise