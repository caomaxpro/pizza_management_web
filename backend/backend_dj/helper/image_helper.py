#!/usr/bin/env python3
"""
Image Helper - Resize, optimize, and convert images for web delivery
"""
from PIL import Image, ImageOps
import io
from typing import Tuple, Optional, Dict, Any

class ImageOptimizer:
    """Optimize images for web: resize, compress, convert to WebP/JPEG/PNG"""
    
    # Default configuration
    MAX_FULL_WIDTH = 1920
    MAX_THUMBNAIL_WIDTH = 400
    QUALITY_FULL = 80
    QUALITY_THUMBNAIL = 75
    WEBP_METHOD = 6  # 0-6, higher = slower but better compression
    
    @staticmethod
    def optimize_image(
        image_bytes: bytes,
        max_width: int = 1920,
        quality: int = 80,
        output_format: str = "webp"
    ) -> Tuple[bytes, str]:
        """
        Optimize image: resize, compress, convert format.
        
        Args:
            image_bytes: Raw image bytes
            max_width: Max width in pixels (maintain aspect ratio)
            quality: Image quality (0-100, for JPEG/WebP)
            output_format: 'webp', 'jpeg', or 'png'
            
        Returns:
            Tuple of (optimized_bytes, content_type)
            
        Raises:
            ValueError: If image format not supported or input invalid
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"Invalid image: {e}")
        
        # Fix rotation based on EXIF orientation
        img = ImageOps.exif_transpose(img)
        
        # Resize if needed (maintain aspect ratio)
        if img.width > max_width:
            new_height = round(max_width * img.height / img.width)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to target format
        output_io = io.BytesIO()
        
        if output_format == "webp":
            # WebP supports lossy+alpha natively; no need for lossless to preserve transparency
            if img.mode in ("RGBA", "LA"):
                # Save directly - PIL preserves alpha channel in WebP lossy mode
                img.save(output_io, format="WEBP", quality=quality, method=ImageOptimizer.WEBP_METHOD)
            elif img.mode == "P":
                # Palette mode: convert to RGBA to capture any palette transparency, then save
                img = img.convert("RGBA")
                img.save(output_io, format="WEBP", quality=quality, method=ImageOptimizer.WEBP_METHOD)
            else:
                img = img.convert("RGB")
                img.save(output_io, format="WEBP", quality=quality, method=ImageOptimizer.WEBP_METHOD)
            content_type = "image/webp"
            
        elif output_format == "jpeg":
            # JPEG: convert to RGB (no transparency)
            img = img.convert("RGB")
            img.save(output_io, format="JPEG", quality=quality, optimize=True, progressive=True)
            content_type = "image/jpeg"
            
        elif output_format == "png":
            # PNG: keep transparency if present
            if img.mode not in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            img.save(output_io, format="PNG", optimize=True)
            content_type = "image/png"
        else:
            raise ValueError(f"Unsupported format: {output_format}")
        
        return output_io.getvalue(), content_type
    
    @staticmethod
    def create_thumbnail(
        image_bytes: bytes,
        thumb_width: int = 400,
        quality: int = 75,
        output_format: str = "webp"
    ) -> Tuple[bytes, str]:
        """
        Create a thumbnail optimized for web (e.g., product list).
        
        Args:
            image_bytes: Raw image bytes
            thumb_width: Thumbnail width in pixels
            quality: Image quality (0-100)
            output_format: 'webp', 'jpeg', or 'png'
            
        Returns:
            Tuple of (thumbnail_bytes, content_type)
        """
        return ImageOptimizer.optimize_image(
            image_bytes,
            max_width=thumb_width,
            quality=quality,
            output_format=output_format
        )
    
    @staticmethod
    def get_image_info(image_bytes: bytes) -> dict:
        """
        Get basic image information without modifying.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dict with 'width', 'height', 'format', 'mode', 'size_kb'
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "size_kb": len(image_bytes) / 1024
            }
        except Exception as e:
            raise ValueError(f"Cannot read image: {e}")
    
    @staticmethod
    def validate_image(
        image_bytes: bytes,
        max_size_mb: float = 5.0,
        allowed_formats: Tuple[str, ...] = ("JPEG", "PNG", "GIF", "WEBP")
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate image: format, size, integrity.
        
        Args:
            image_bytes: Raw image bytes
            max_size_mb: Maximum file size in MB
            allowed_formats: Tuple of allowed image formats (PIL format names)
            
        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, error_str) if invalid
        """
        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"Image too large: {size_mb:.1f}MB (max: {max_size_mb}MB)"
        
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.format not in allowed_formats:
                return False, f"Format not allowed: {img.format}. Allowed: {', '.join(allowed_formats)}"
            return True, None
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    @staticmethod
    def process_image_complete(
        image_bytes: bytes,
        max_width: int = 1920,
        quality: int = 80,
        output_format: str = "webp",
        create_thumb: bool = True,
        thumb_width: int = 400,
        thumb_quality: int = 75,
        max_size_mb: float = 5.0
    ) -> Dict[str, Any]:
        """
        Complete image processing pipeline: validate → get info → optimize → optional thumbnail.
        
        Args:
            image_bytes: Raw image data
            max_width: Max width for optimized image (px)
            quality: Quality for optimized image (0-100)
            output_format: 'webp', 'jpeg', or 'png'
            create_thumb: If True, also create thumbnail
            thumb_width: Thumbnail width (px)
            thumb_quality: Thumbnail quality (0-100)
            max_size_mb: Max input file size (MB)
            
        Returns:
            Dict with keys:
            - is_valid (bool): Passed validation
            - error (str or None): Error message if not valid
            - info (dict): Original image info (width, height, format, mode, size_kb)
            - optimized_bytes (bytes): Optimized image bytes
            - optimized_type (str): Content type (e.g., 'image/webp')
            - thumbnail_bytes (bytes or None): Thumbnail bytes if create_thumb=True
            - thumbnail_type (str or None): Thumbnail content type
            - compression_ratio (float): Original size / optimized size
            
        Raises:
            ValidationError: If image fails validation (caught in return dict)
        """
        
        result = {
            "is_valid": False,
            "error": None,
            "info": None,
            "optimized_bytes": None,
            "optimized_type": None,
            "thumbnail_bytes": None,
            "thumbnail_type": None,
            "compression_ratio": None
        }
        
        # Step 1: Validate
        is_valid, error_msg = ImageOptimizer.validate_image(image_bytes, max_size_mb)
        if not is_valid:
            result["error"] = error_msg
            return result
        
        # Step 2: Get info
        try:
            info = ImageOptimizer.get_image_info(image_bytes)
            result["info"] = info
        except Exception as e:
            result["error"] = f"Failed to read image info: {str(e)}"
            return result
        
        # Step 3: Optimize main image
        try:
            opt_bytes, opt_type = ImageOptimizer.optimize_image(
                image_bytes,
                max_width=max_width,
                quality=quality,
                output_format=output_format
            )
            result["optimized_bytes"] = opt_bytes
            result["optimized_type"] = opt_type
            result["compression_ratio"] = round(len(image_bytes) / len(opt_bytes), 2)
        except Exception as e:
            result["error"] = f"Failed to optimize image: {str(e)}"
            return result
        
        # Step 4: Create thumbnail (optional)
        if create_thumb:
            try:
                thumb_bytes, thumb_type = ImageOptimizer.create_thumbnail(
                    image_bytes,
                    thumb_width=thumb_width,
                    quality=thumb_quality,
                    output_format=output_format
                )
                result["thumbnail_bytes"] = thumb_bytes
                result["thumbnail_type"] = thumb_type
            except Exception as e:
                result["error"] = f"Failed to create thumbnail: {str(e)}"
                # Don't fail whole process if thumbnail fails
                result["thumbnail_bytes"] = None
                result["thumbnail_type"] = None
        
        result["is_valid"] = True
        return result


# Backward compatibility: standalone functions
def optimize_image_bytes(
    image_bytes: bytes,
    max_width: int = 1920,
    quality: int = 80,
    to_webp: bool = True
) -> Tuple[bytes, str]:
    """
    Optimize image to bytes (simple interface).
    
    Args:
        image_bytes: Raw image data
        max_width: Max width in pixels
        quality: Image quality (0-100)
        to_webp: If True, output WebP; else JPEG
        
    Returns:
        Tuple of (optimized_bytes, content_type)
    """
    output_format = "webp" if to_webp else "jpeg"
    return ImageOptimizer.optimize_image(
        image_bytes,
        max_width=max_width,
        quality=quality,
        output_format=output_format
    )