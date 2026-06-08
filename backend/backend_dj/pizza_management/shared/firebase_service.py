"""
Firebase Storage Service - Handle image uploads to Firebase Storage
"""
import os
import io
import uuid
import logging
from pathlib import Path
from firebase_admin import storage
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from typing import Optional
from helper.image_helper import ImageOptimizer
from google.cloud import exceptions as gcloud_exceptions

logger = logging.getLogger(__name__)


class FirebaseStorageService:
    """Service for uploading files to Firebase Storage"""
    
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    MAX_FILE_SIZE_MB = 10  # 10MB max per file
    
    @staticmethod
    def is_valid_image(file_obj) -> bool:
        """Validate file is an image and not too large"""
        if not file_obj:
            return False
        
        # Check file size
        if file_obj.size > FirebaseStorageService.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File too large. Max {FirebaseStorageService.MAX_FILE_SIZE_MB}MB")
        
        # Check extension
        ext = file_obj.name.rsplit('.', 1)[-1].lower() if '.' in file_obj.name else ''
        if ext not in FirebaseStorageService.ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid file type. Allowed: {FirebaseStorageService.ALLOWED_EXTENSIONS}")
        
        return True
    
    @staticmethod
    def upload_image(file_obj, folder: str = "items") -> Optional[str]:
        """
        Upload image to Firebase Storage
        
        Args:
            file_obj: Django UploadedFile object
            folder: Storage folder path (e.g., "items", "users", "orders")
        
        Returns:
            Public URL to the uploaded file, or None if upload fails
        """
        try:
            if not FirebaseStorageService.is_valid_image(file_obj):
                return None
            
            # Generate unique filename
            filename = f"{uuid.uuid4()}_{file_obj.name}"
            filepath = f"{folder}/{filename}"
            
            # Get Firebase Storage bucket
            bucket = storage.bucket()
            blob = bucket.blob(filepath)
            
            # Upload file
            blob.upload_from_string(
                file_obj.read(),
                content_type=file_obj.content_type
            )
            
            # Make public (optional - set IAM permissions in Firebase Console)
            # blob.make_public()
            
            # Return public URL
            return f"https://storage.googleapis.com/{bucket.name}/{filepath}"
            
        except Exception as e:
            logger.error(f"[Firebase Upload Error] {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def upload_image_optimized(
        image_bytes: bytes,
        original_filename: str,
        folder: str = "items",
        max_width: int = 1920,
        quality: int = 80,
        output_format: str = "webp"
    ) -> Optional[str]:
        """
        Optimize image and upload to Firebase Storage
        
        Args:
            image_bytes: Raw image bytes to upload
            original_filename: Original filename (for reference)
            folder: Storage folder path (e.g., "ingredients", "users")
            max_width: Max width for optimization (px)
            quality: Optimization quality (0-100)
            output_format: Output format ('webp', 'jpeg', 'png')
        
        Returns:
            Public URL to the uploaded file, or None if upload fails
        """
        try:
            # STEP 1: Optimize image
            result = ImageOptimizer.process_image_complete(
                image_bytes,
                max_width=max_width,
                quality=quality,
                output_format=output_format,
                create_thumb=True
            )
            
            if not result['is_valid']:
                raise ValueError(f"Image optimization failed: {result['error']}")
            
            optimized_bytes = result['optimized_bytes']
            content_type = result['optimized_type']
            
            # STEP 2: Upload optimized image to Firebase
            filename = f"{uuid.uuid4()}_{Path(original_filename).stem}.webp"
            filepath = f"{folder}/{filename}"
            
            bucket = storage.bucket()
            blob = bucket.blob(filepath)
            
            blob.upload_from_string(
                optimized_bytes,
                content_type=content_type
            )
            
            logger.info(f"[Firebase Optimized Upload] {filepath} (compression: {result['compression_ratio']}x)")
            return f"https://storage.googleapis.com/{bucket.name}/{filepath}"
            
        except Exception as e:
            logger.error(f"[Firebase Optimized Upload Error] {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def delete_image(file_url: str) -> bool:
        """Delete image from Firebase Storage - handles 404 gracefully"""
        try:
            if not file_url or 'storage.googleapis.com' not in file_url:
                logger.warning(f"[FIREBASE] Invalid URL for deletion: {file_url}")
                return False
            
            # Extract file path from URL correctly
            # URL format: https://storage.googleapis.com/bucket-name/path/to/file
            try:
                # Split by domain to get the rest
                parts_after_domain = file_url.split('storage.googleapis.com/')[1]
                # Split by first / to separate bucket from path
                bucket_and_path = parts_after_domain.split('/', 1)
                if len(bucket_and_path) < 2:
                    logger.warning(f"[FIREBASE] Could not parse bucket/path from URL: {file_url}")
                    return False
                
                file_path = bucket_and_path[1]  # Everything after bucket name
                logger.info(f"[FIREBASE] Attempting to delete: {file_path}")
            except (IndexError, ValueError) as e:
                logger.error(f"[FIREBASE] URL parsing error for {file_url}: {e}")
                return False
            
            bucket = storage.bucket()
            blob = bucket.blob(file_path)
            blob.delete()
            logger.info(f"[FIREBASE] Successfully deleted: {file_path}")
            return True
        
        except gcloud_exceptions.NotFound as e:
            # File doesn't exist - that's OK, treat as successful delete
            logger.warning(f"[FIREBASE] File already deleted or not found: {file_url} - {str(e)}")
            return True
        
        except gcloud_exceptions.Forbidden as e:
            logger.error(f"[FIREBASE] Permission denied when deleting {file_url}: {str(e)}")
            return False
        
        except Exception as e:
            logger.error(f"[FIREBASE] Error deleting {file_url}: {str(e)}", exc_info=True)
            return False