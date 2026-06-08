import logging
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from celery import shared_task
from celery.result import AsyncResult
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from pizza_management.ingredient.model import Ingredient
from pizza_management.ingredient.validators import IngredientCreateRequest
from pizza_management.ingredient.serializers import IngredientSerializer
from pizza_management.shared.image_processor import ImageProcessor
from pizza_management.shared.firebase_service import FirebaseStorageService
from pizza_management.shared.image_handler import LocalImageHandler
from helper.cache_helpers import CacheHelper

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='pizza_management.ingredient.process_import')
def process_ingredient_import_async(self, ingredients_data, import_id):
    """
    Process ingredient import asynchronously via Celery - OPTIMIZED with batch image processing.
    
    Strategy: Create ingredients immediately (no blocking on image), then batch-process images
    in background with parallel uploads, cache deduplication, and piece images.
    
    Args:
        ingredients_data: List of ingredient dictionaries
        import_id: UUID for tracking this import session
    """
    total_items = len(ingredients_data)
    results = {"created": [], "errors": 0}
    images_to_process = []  # Collect image pairs for batch processing
    
    # Store task_id in cache for cancellation
    cache_key_task = f"import_task_{import_id}"
    cache_key_items = f"import_created_items_{import_id}"
    
    logger.info(f"[Async Import {import_id}] Starting: {total_items} ingredients (Option 1+2+3: Fast create + Batch images)")
    
    try:
        # Store task_id in cache for cancellation
        CacheHelper.cache_set(cache_key_task, self.request.id, timeout=3600)
        logger.info(f"[Async Import {import_id}] Task ID stored: {self.request.id}")
        
        for idx, ingredient_data in enumerate(ingredients_data):
            try:
                # Copy to avoid modifying original
                data = ingredient_data.copy()
                
                # Extract image fields for later batch processing
                image_url = data.pop('image_url', None)
                image_source_url = data.pop('image_source_url', None)
                piece_image_url = data.pop('piece_image_url', None)
                piece_image_source_url = data.pop('piece_image_source_url', None)
                data.pop('image_file', None)
                data.pop('piece_file', None)
                
                logger.info(f"[Import {idx}] Image sources: main={image_source_url}, piece={piece_image_source_url}")
                
                # Validate and create
                valid_data = IngredientCreateRequest(**data)
                ingredient_dict = valid_data.model_dump(exclude_none=True)
                
                # ===== OPTION 1: CREATE INGREDIENT IMMEDIATELY (NO BLOCKING) =====
                ingredient = Ingredient.objects.create(
                    name=ingredient_dict['name'],
                    description=ingredient_dict.get('description'),
                    price=ingredient_dict['price'],
                    type=ingredient_dict['type'],
                    sub_type=ingredient_dict.get('sub_type'),
                    is_active=ingredient_dict.get('is_active', True),
                    image_url=None,  # ← No image yet, will be filled by batch task
                    image_source_url=image_source_url,
                    piece_image_url=None,  # ← No piece image yet
                    piece_image_source_url=piece_image_source_url,
                )
                
                results["created"].append(ingredient.id)
                
                # Store created ingredient IDs in cache for cleanup on cancel
                created_items = CacheHelper.cache_get(cache_key_items) or []
                created_items.append(ingredient.id)
                CacheHelper.cache_set(cache_key_items, created_items, timeout=3600)
                
                # Collect image URLs for batch processing (if exists)
                if image_url:
                    images_to_process.append({
                        "item_id": ingredient.id,
                        "image_url": image_url,
                        "folder": "ingredients",
                        "image_type": "main"
                    })
                
                if piece_image_url:
                    images_to_process.append({
                        "item_id": ingredient.id,
                        "image_url": piece_image_url,
                        "folder": "ingredients",
                        "image_type": "piece"
                    })
                
                logger.info(f"[Import {idx}] ✓ Created: {ingredient.name} (ID: {ingredient.id}) - Images queued")
                
            except Exception as e:
                results["errors"] += 1
                logger.error(f"[Import {idx}] Error: {str(e)}")
        
        # Broadcast fast completion for ingredient creation (no progress update, just items created)
        logger.info(f"[Async Import {import_id}] Ingredients created: {len(results['created'])}, errors: {results['errors']}")
        # Skip progress broadcast here - it will be 100% anyway
        
        # ===== OPTION 2+3: ENQUEUE BATCH IMAGE PROCESSING ======
        if images_to_process:
            logger.info(f"[Async Import {import_id}] Enqueueing batch processing for {len(images_to_process)} images")
            image_batch_task = process_images_batch_async.delay(images_to_process, import_id)
            # Store image batch task_id in cache for cancellation
            import_image_task_key = f"import_image_task_{import_id}"
            CacheHelper.cache_set(import_image_task_key, image_batch_task.id, timeout=3600)
            logger.info(f"[Async Import {import_id}] Image batch task_id stored: {image_batch_task.id}")
        
        # Invalidate cache
        if results["created"]:
            CacheHelper.cache_clear_pattern("ingredients_*")
            logger.info("[Import] Cache cleared")
        
        # Broadcast final completion
        _broadcast_import_completion(import_id, len(results["created"]), results["errors"])
        logger.info(f"[Async Import {import_id}] Complete: {len(results['created'])} ingredients created, {results['errors']} errors, {len(images_to_process)} images queued for processing")
        
    except Exception as e:
        logger.error(f"[Async Import {import_id}] Fatal error: {str(e)}")
        _broadcast_import_error(import_id, str(e))


# ===== HELPER FUNCTIONS FOR OPTION 2+3 BATCH PROCESSING =====

def _get_image_cache_key(image_url):
    """Generate deterministic cache key for image URL (hash-based)"""
    return f"image_cache:{hashlib.sha256(image_url.encode()).hexdigest()[:16]}"


def _validate_firebase_url(url):
    """
    Validate if Firebase URL still exists via HEAD request.
    Returns True if accessible, False if 404/error.
    """
    if not url or not url.startswith('https://'):
        return True  # Not Firebase URL, assume OK
    
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        is_valid = response.status_code < 400
        if not is_valid:
            logger.warning(f"[Firebase Validation] URL unreachable: {url[:60]}... (status: {response.status_code})")
        return is_valid
    except requests.RequestException as e:
        logger.warning(f"[Firebase Validation] Error checking {url[:60]}...: {e}")
        return False


def _get_max_workers():
    """Dynamically calculate max_workers based on available RAM"""
    base_workers = 8
    if psutil is None:
        logger.warning("[RAM Monitor] psutil not available, using default workers")
        return base_workers
    
    try:
        ram_available_gb = psutil.virtual_memory().available / (1024**3)
        logger.info(f"[RAM Monitor] Available RAM: {ram_available_gb:.2f} GB")
        
        if ram_available_gb < 0.5:
            workers = 2
            logger.info(f"[RAM Monitor] Low RAM, using {workers} workers")
        elif ram_available_gb < 1.0:
            workers = 4
            logger.info(f"[RAM Monitor] Mid RAM, using {workers} workers")
        else:
            workers = min(8, base_workers)
            logger.info(f"[RAM Monitor] Healthy RAM, using {workers} workers")
        
        return workers
    except Exception as e:
        logger.error(f"[RAM Monitor] Error checking RAM: {e}, using default")
        return base_workers


def _process_single_image(item_id, image_url, folder, image_type="main", import_id=None):
    """
    Process single image: check cache, download/process, upload, update DB.
    Designed to run inside ThreadPoolExecutor for parallel uploads.
    For ingredients, supports both main and piece images.
    
    Args:
        import_id: Optional - used to track uploaded images for cancellation cleanup
    """
    try:
        # 🛑 CHECK CANCELLATION BEFORE ANY WORK - CRITICAL FIX!
        if import_id:
            cancel_flag_key = f"import_cancel_flag_{import_id}"
            if CacheHelper.cache_get(cancel_flag_key):
                logger.warning(f"🛑 [WORKER CANCELLED] _process_single_image skipping item={item_id} ({image_type}) - cancellation flag detected")
                return (item_id, None, "Cancelled before processing", image_type)
        
        cache_key = _get_image_cache_key(image_url)
        
        # Check cache first (OPTION 3: Cache deduplication)
        cached_result = CacheHelper.cache_get(cache_key)
        if cached_result:
            # Validate Firebase URL still exists before using cache
            if _validate_firebase_url(cached_result):
                logger.info(f"[Image Cache HIT] item={item_id} ({image_type}), url={image_url[:50]}... → {cached_result[:50]}...")
                if image_type == "piece":
                    Ingredient.objects.filter(id=item_id).update(piece_image_url=cached_result)
                else:
                    Ingredient.objects.filter(id=item_id).update(image_url=cached_result)
                return (item_id, cached_result, None, image_type)
            else:
                # Firebase URL gone, invalidate cache and reprocess
                logger.warning(f"[Image Cache INVALID] item={item_id} ({image_type}), cached URL unreachable, clearing cache and reprocessing...")
                CacheHelper.cache_delete(cache_key)
                # Fall through to reprocess
        
        # 🛑 FINAL CHECK before uploading - cancellation may have happened during cache check
        if import_id:
            cancel_flag_key = f"import_cancel_flag_{import_id}"
            if CacheHelper.cache_get(cancel_flag_key):
                logger.warning(f"🛑 [WORKER CANCELLED] _process_single_image aborting upload for item={item_id} ({image_type}) - cancellation flag detected before upload")
                return (item_id, None, "Cancelled before upload", image_type)
        
        # Process image
        processed_url = None
        if image_url.startswith(('http://', 'https://')):
            logger.info(f"[Image Processing] item={item_id} ({image_type}) → DOWNLOAD mode from {image_url}")
            processed_url = ImageProcessor.download_and_upload_image(image_url, folder)
        else:
            logger.info(f"[Image Processing] item={item_id} ({image_type}) → LOCAL mode from {image_url}")
            processed_url = ImageProcessor.process_image_path(image_url, folder)
        
        # Validate processing - now expects None on error instead of fallback URL
        if processed_url is None:
            raise Exception(f"Image processing returned None - upload or processing failed")
        
        # ⚠️ TRACK UPLOADED IMAGE URL FOR CANCELLATION (BEFORE DB update!)
        if import_id:
            tracking_key = f"import_uploaded_images_{import_id}"
            uploaded_images = CacheHelper.cache_get(tracking_key) or []
            if processed_url not in uploaded_images:
                uploaded_images.append(processed_url)
                CacheHelper.cache_set(tracking_key, uploaded_images, timeout=3600)
                logger.info(f"[Track Upload] Tracked for cancellation: {processed_url[:80]}...")
        
        # Update DB
        if image_type == "piece":
            Ingredient.objects.filter(id=item_id).update(piece_image_url=processed_url)
        else:
            Ingredient.objects.filter(id=item_id).update(image_url=processed_url)
        
        # ✅ Clear ingredient detail cache IMMEDIATELY (prevent stale NULL from being cached)
        detail_cache_key = f"ingredients_detail:id_{item_id}"
        CacheHelper.cache_delete(detail_cache_key)
        logger.info(f"[Cache Invalidated] Cleared {detail_cache_key} after image update ({image_type})")
        
        # Cache result (24 hours)
        CacheHelper.cache_set(cache_key, processed_url, timeout=86400)
        logger.info(f"[Image Success] item={item_id} ({image_type}) → {processed_url[:80]}...")
        
        return (item_id, processed_url, None, image_type)
    
    except Exception as e:
        logger.error(f"[Image Error] item={item_id} ({image_type}) err={str(e)[:100]}")
        return (item_id, None, str(e), image_type)


@shared_task(bind=True, name='pizza_management.ingredient.process_images_batch')
def process_images_batch_async(self, images_batch, import_id):
    """
    OPTION 2+3: Batch process images in parallel with ThreadPoolExecutor + cache + RAM control.
    Supports both main and piece images for ingredients.
    
    Args:
        images_batch: List of {item_id, image_url, folder, image_type}
        import_id: For logging/tracking
        
    Returns:
        dict with results
    """
    logger.info(f"[Batch Task] Starting: {len(images_batch)} images")
    
    max_workers = _get_max_workers()
    results = {"processed": 0, "failed": 0, "cached": 0}
    BATCH_SIZE = 1  # Broadcast progress after every image to prevent WebSocket timeout
    total_images = len(images_batch)
    completed_count = 0
    
    # Check cancellation flag at start
    cancel_flag_key = f"import_cancel_flag_{import_id}"
    if CacheHelper.cache_get(cancel_flag_key):
        logger.info(f"[Batch Task] Cancellation signal received at start, aborting image processing for import_id {import_id}")
        # Broadcast cancellation to client
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"ingredient_import_{import_id}",
                    {
                        "type": "import.cancelled",
                        "message": "Image processing cancelled before starting"
                    }
                )
        except Exception as e:
            logger.warning(f"[Batch Task] Failed to broadcast cancellation: {str(e)}")
        return results
    
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(_process_single_image, img['item_id'], img['image_url'], img['folder'], img.get('image_type', 'main'), import_id): img
                for img in images_batch
            }
            
            # Collect results as they complete
            cancellation_detected = False
            for future in as_completed(futures):
                # CHECK CANCELLATION FLAG ACTIVELY - this is the critical fix!
                if CacheHelper.cache_get(cancel_flag_key):
                    if not cancellation_detected:
                        cancellation_detected = True
                        logger.warning(f"🛑 [CANCELLATION DETECTED] Terminating image processing for import_id {import_id}")
                        
                        # Cancel all remaining pending futures
                        cancelled_count = 0
                        for f in futures:
                            if not f.done():  # Only cancel futures that haven't completed yet
                                if f.cancel():
                                    cancelled_count += 1
                        
                        logger.warning(f"🛑 [FUTURES CANCELLED] Cancelled {cancelled_count} pending futures out of {len(futures)} total")
                        
                        # Force immediate shutdown without waiting
                        executor.shutdown(wait=False)
                        break
                
                try:
                    item_id, processed_url, error, image_type = future.result()
                    completed_count += 1
                    
                    if error:
                        results["failed"] += 1
                        logger.error(f"[Batch Result] item={item_id} ({image_type}) failed: {error}")
                    else:
                        # Check if it was cached
                        if processed_url:
                            cache_key = _get_image_cache_key(futures[future]['image_url'])
                            if CacheHelper.cache_get(cache_key):
                                results["cached"] += 1
                                logger.info(f"[Batch Result] item={item_id} ({image_type}) from cache")
                            else:
                                results["processed"] += 1
                                logger.info(f"[Batch Result] item={item_id} ({image_type}) processed & cached")
                except Exception as e:
                    logger.error(f"[Batch Error] {str(e)}")
                    results["failed"] += 1
                    completed_count += 1
                
                # Broadcast progress every BATCH_SIZE images or at the end
                if completed_count % BATCH_SIZE == 0 or completed_count == total_images:
                    percentage = int((completed_count / total_images) * 100) if total_images > 0 else 100
                    _broadcast_image_progress(import_id, completed_count, total_images, percentage)
        
        logger.info(f"[Batch Complete] {results['processed']} processed, {results['cached']} cached, {results['failed']} failed")
        
        # 🔄 Clear ALL ingredient caches so frontend gets fresh data with images immediately
        logger.info("[Cache Invalidation] Clearing all ingredient caches...")
        CacheHelper.cache_clear_pattern("ingredients_list*")
        CacheHelper.cache_clear_pattern("ingredients_detail*")
        CacheHelper.cache_clear_pattern("ingredients_filter*")
        CacheHelper.cache_clear_pattern("ingredients_paginated*")
        logger.info("[Cache Invalidation] ✅ All ingredient caches cleared")
        
        # Broadcast batch completion via WebSocket
        _broadcast_image_batch_complete(import_id, results)
        
        # Clear cancellation flag when done
        cancel_flag_key = f"import_cancel_flag_{import_id}"
        CacheHelper.cache_delete(cancel_flag_key)
        logger.info(f"[Batch Task] Cancellation flag cleared for import_id {import_id}")
        
    except Exception as e:
        logger.error(f"[Batch Fatal] {str(e)}")
        # Clean up cancellation flag on error too
        cancel_flag_key = f"import_cancel_flag_{import_id}"
        CacheHelper.cache_delete(cancel_flag_key)
        _broadcast_import_error(import_id, f"Image batch processing failed: {str(e)}")


@shared_task(bind=True, name='pizza_management.ingredient.process_ingredient_image')
def process_ingredient_image_async(self, ingredient_id, image_url, image_type="main"):
    """
    OPTION 1+3: Per-ingredient image processing task (backup/retry for failed images).
    
    Args:
        ingredient_id: Ingredient to update
        image_url: Image source URL/path
        image_type: "main" or "piece"
        
    Returns:
        Processed image URL or raises exception for retry
    """
    logger.info(f"[Per-Item Task] Processing {image_type} image for ingredient={ingredient_id}")
    
    try:
        ingredient = Ingredient.objects.get(id=ingredient_id)
        cache_key = _get_image_cache_key(image_url)
        
        # Check cache
        cached = CacheHelper.cache_get(cache_key)
        if cached:
            if image_type == "piece":
                ingredient.piece_image_url = cached
            else:
                ingredient.image_url = cached
            ingredient.save()
            logger.info(f"[Per-Item] ingredient={ingredient_id} ({image_type}) from cache")
            return cached
        
        # Process
        if image_url.startswith(('http://', 'https://')):
            processed = ImageProcessor.download_and_upload_image(image_url, "ingredients")
        else:
            processed = ImageProcessor.process_image_path(image_url, "ingredients")
        
        # Validate
        if not processed or processed == image_url:
            raise Exception(f"Processing failed")
        
        # Update DB & cache
        if image_type == "piece":
            ingredient.piece_image_url = processed
        else:
            ingredient.image_url = processed
        ingredient.save()
        CacheHelper.cache_set(cache_key, processed, timeout=86400)
        logger.info(f"[Per-Item] ingredient={ingredient_id} ({image_type}) processed & cached")
        
        return processed
    
    except Exception as e:
        logger.error(f"[Per-Item Error] ingredient={ingredient_id} ({image_type}) err={str(e)}")
        # Retry with exponential backoff (3 max retries)
        raise self.retry(exc=e, countdown=60, max_retries=3)


def _broadcast_image_progress(import_id, processed, total, percentage):
    """Broadcast image processing progress via WebSocket (every N images)"""
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        async_to_sync(channel_layer.group_send)(
            f"ingredient_import_{import_id}",
            {
                "type": "image_progress",  # ← Use underscore for Channels routing
                "processed": processed,
                "total": total,
                "percentage": percentage,
                "message": f"Processing images: {processed}/{total}",
            }
        )
        logger.debug(f"[WS] Image progress: {percentage}% ({processed}/{total})")
    except Exception as e:
        logger.error(f"[WS] Failed to broadcast image progress: {str(e)}")


def _broadcast_image_batch_complete(import_id, results):
    """Broadcast image batch processing completion via WebSocket"""
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        async_to_sync(channel_layer.group_send)(
            f"ingredient_import_{import_id}",
            {
                "type": "image_batch_completed",  # ← FIXED: Use underscore, not dot
                "processed": results.get("processed", 0),
                "cached": results.get("cached", 0),
                "failed": results.get("failed", 0),
                "message": f"Image batch: {results.get('processed', 0)} processed, {results.get('cached', 0)} from cache, {results.get('failed', 0)} failed",
            }
        )
        logger.info(f"[WS] Image batch complete: {results}")
    except Exception as e:
        logger.error(f"[WS] Failed to broadcast image batch: {str(e)}")


def _broadcast_import_progress(import_id, current, total, percentage, completed_ingredient=None):
    """Broadcast progress via WebSocket with completed ingredient data"""
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        # Serialize ingredient if available
        ingredient_data = None
        if completed_ingredient:
            try:
                ingredient_data = IngredientSerializer(completed_ingredient).data
            except Exception as serialize_err:
                logger.error(f"Failed to serialize ingredient: {serialize_err}")
        
        async_to_sync(channel_layer.group_send)(
            f"ingredient_import_{import_id}",
            {
                "type": "import_progress",  # ← FIXED: Use underscore, not dot
                "current": current,
                "total": total,
                "percentage": percentage,
                "message": f"Processing {current}/{total}",
                "completed_ingredient": ingredient_data,
            }
        )
        log_msg = f"[WS] Progress {percentage}% ({current}/{total})"
        if completed_ingredient:
            log_msg += f" - Created: {completed_ingredient.name}"
        logger.debug(log_msg)
    except Exception as e:
        logger.error(f"[WS] Failed to broadcast progress: {str(e)}")


def _broadcast_import_completion(import_id, total_created, total_errors):
    """Broadcast completion via WebSocket"""
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        async_to_sync(channel_layer.group_send)(
            f"ingredient_import_{import_id}",
            {
                "type": "import_completed",  # ← FIXED: Use underscore, not dot
                "total_created": total_created,
                "total_errors": total_errors,
                "message": f"Completed: {total_created} created, {total_errors} errors",
            }
        )
        logger.info(f"[WS] Completion: {total_created} created, {total_errors} errors")
    except Exception as e:
        logger.error(f"[WS] Failed to broadcast completion: {str(e)}")


def _broadcast_import_error(import_id, error_msg):
    """Broadcast error via WebSocket"""
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        async_to_sync(channel_layer.group_send)(
            f"ingredient_import_{import_id}",
            {
                "type": "import_error",  # ← FIXED: Use underscore, not dot
                "error": error_msg,
                "message": f"Import failed: {error_msg}",
            }
        )
        logger.error(f"[WS] Error: {error_msg}")
    except Exception as e:
        logger.error(f"[WS] Failed to broadcast error: {str(e)}")


def cancel_ingredient_import(import_id):
    """
    Cancel an ongoing ingredient import and cleanup created items + images.
    Handles both items and image phases by deleting:
    - Images from storage (Firebase or local disk)
    - Ingredients from database
    - All related cache entries
    Sends progress updates via WebSocket throughout the process.
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    def send_progress(step, total_steps, action_description, percentage):
        """Send cancel progress update via WebSocket"""
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"ingredient_import_{import_id}",
                    {
                        "type": "import.cancel_progress",
                        "step": step,
                        "total_steps": total_steps,
                        "action": action_description,
                        "percentage": percentage,
                    }
                )
                logger.info(f"[Cancel Progress] {step}/{total_steps} ({percentage}%): {action_description}")
        except Exception as e:
            logger.warning(f"[Cancel Progress] Failed to send progress: {str(e)}")
    
    try:
        cache_key_task = f"import_task_{import_id}"
        cache_key_items = f"import_created_items_{import_id}"
        
        # Total 5 steps for cancellation
        total_steps = 5
        current_step = 0
        
        # 1. Get task_id from cache
        task_id = CacheHelper.cache_get(cache_key_task)
        if not task_id:
            logger.warning(f"[Cancel] No task found for import_id: {import_id}")
            return False, "Task not found"
        
        # 2. Revoke Celery task (terminate=True forcefully stops workers)
        current_step += 1
        send_progress(current_step, total_steps, "Stopping background tasks...", int((current_step / total_steps) * 100))
        AsyncResult(task_id).revoke(terminate=True)
        logger.info(f"[Cancel] Task {task_id} revoked for import_id {import_id}")
        
        # 2b. ALSO revoke image batch task if it exists
        import_image_task_key = f"import_image_task_{import_id}"
        image_batch_task_id = CacheHelper.cache_get(import_image_task_key)
        if image_batch_task_id:
            try:
                AsyncResult(image_batch_task_id).revoke(terminate=True)
                logger.info(f"[Cancel] Image batch task {image_batch_task_id} revoked for import_id {import_id}")
                CacheHelper.cache_delete(import_image_task_key)
            except Exception as e:
                logger.warning(f"[Cancel] Failed to revoke image batch task: {str(e)}")
        
        # 2c. Set cancellation flag for ThreadPoolExecutor to check
        cancel_flag_key = f"import_cancel_flag_{import_id}"
        CacheHelper.cache_set(cancel_flag_key, True, timeout=3600)
        logger.warning(f"🛑 [Cancel] CANCELLATION FLAG SET for import_id {import_id} - ThreadPoolExecutor will detect and stop pending uploads")
        logger.warning(f"🛑 [Cancel] Image batch task revoked and flag set - waiting for pending image uploads to be cancelled...")
        
        # 3. Get created ingredient IDs
        created_item_ids = CacheHelper.cache_get(cache_key_items) or []
        if not created_item_ids:
            logger.info(f"[Cancel] No created items found for import_id {import_id}")
            CacheHelper.cache_delete(cache_key_task)
            CacheHelper.cache_delete(cache_key_items)
            # Clean up cancellation flag
            cancel_flag_key = f"import_cancel_flag_{import_id}"
            CacheHelper.cache_delete(cancel_flag_key)
            send_progress(total_steps, total_steps, "Completed (no items to delete)", 100)
            return True, "Cancelled. (No items were created)"
        
        # 4. Delete images from storage BEFORE deleting ingredients
        current_step += 1
        send_progress(current_step, total_steps, f"Deleting {len(created_item_ids)} images from storage...", int((current_step / total_steps) * 100))
        logger.info(f"[Cancel] Cleaning up images from storage for {len(created_item_ids)} ingredients...")
        
        deleted_count = 0
        images_deleted = 0
        
        for idx, ingredient_id in enumerate(created_item_ids):
            try:
                ingredient = Ingredient.objects.get(id=ingredient_id)
                
                # Delete main image
                if ingredient.image_url:
                    try:
                        from django.conf import settings
                        storage_type = getattr(settings, 'STORAGE_TYPE', 'firebase')
                        
                        if storage_type == 'firebase':
                            FirebaseStorageService.delete_image(ingredient.image_url)
                        else:
                            LocalImageHandler.delete_image(ingredient.image_url)
                        
                        images_deleted += 1
                        logger.info(f"[Cancel] Deleted main image for ingredient {ingredient_id}: {ingredient.image_url[:60]}...")
                    except Exception as img_err:
                        logger.warning(f"[Cancel] Failed to delete main image for ingredient {ingredient_id}: {str(img_err)}")
                
                # Delete piece image
                if ingredient.piece_image_url:
                    try:
                        from django.conf import settings
                        storage_type = getattr(settings, 'STORAGE_TYPE', 'firebase')
                        
                        if storage_type == 'firebase':
                            FirebaseStorageService.delete_image(ingredient.piece_image_url)
                        else:
                            LocalImageHandler.delete_image(ingredient.piece_image_url)
                        
                        images_deleted += 1
                        logger.info(f"[Cancel] Deleted piece image for ingredient {ingredient_id}: {ingredient.piece_image_url[:60]}...")
                    except Exception as img_err:
                        logger.warning(f"[Cancel] Failed to delete piece image for ingredient {ingredient_id}: {str(img_err)}")
                
            except Ingredient.DoesNotExist:
                logger.warning(f"[Cancel] Ingredient {ingredient_id} not found (already deleted?)")
            except Exception as e:
                logger.error(f"[Cancel] Error cleaning images for ingredient {ingredient_id}: {str(e)}")
        
        logger.info(f"[Cancel] Image cleanup complete: {images_deleted} images deleted from storage")
        
        # ALSO delete tracked uploaded images that might not be in DB yet
        tracking_key = f"import_uploaded_images_{import_id}"
        tracked_uploaded_images = CacheHelper.cache_get(tracking_key) or []
        
        for image_url in tracked_uploaded_images:
            if image_url:  # Skip empty
                try:
                    # Delete from storage (Firebase or local)
                    from django.conf import settings
                    storage_type = getattr(settings, 'STORAGE_TYPE', 'firebase')
                    
                    if storage_type == 'firebase':
                        FirebaseStorageService.delete_image(image_url)
                    else:
                        LocalImageHandler.delete_image(image_url)
                    
                    images_deleted += 1
                    logger.info(f"[Cancel] Deleted tracked uploaded image: {image_url[:60]}...")
                except Exception as img_err:
                    logger.warning(f"[Cancel] Failed to delete tracked image {image_url[:60]}...: {str(img_err)}")
        
        logger.info(f"[Cancel] Tracked image cleanup complete: {len(tracked_uploaded_images)} tracked images deleted")
        
        # Clear tracking cache
        CacheHelper.cache_delete(tracking_key)
        
        # 5. Delete all ingredients from database
        current_step += 1
        send_progress(current_step, total_steps, f"Deleting {len(created_item_ids)} ingredients from database...", int((current_step / total_steps) * 100))
        deleted_count, _ = Ingredient.objects.filter(id__in=created_item_ids).delete()
        logger.info(f"[Cancel] Deleted {deleted_count} created ingredients from database for import_id {import_id}")
        
        # 6. Cleanup cache entries
        current_step += 1
        send_progress(current_step, total_steps, "Cleaning up caches...", int((current_step / total_steps) * 100))
        CacheHelper.cache_delete(cache_key_task)
        CacheHelper.cache_delete(cache_key_items)
        
        # Clean up cancellation flag and image task tracking
        cancel_flag_key = f"import_cancel_flag_{import_id}"
        CacheHelper.cache_delete(cancel_flag_key)
        CacheHelper.cache_delete(import_image_task_key)
        
        # 7. Invalidate all ingredient-related caches
        CacheHelper.cache_clear_pattern("ingredients_*")
        CacheHelper.cache_clear_pattern("image_cache:*")  # Also clear image dedup cache
        
        logger.info(f"[Cancel] ✅ Complete cancellation for import_id {import_id}: {deleted_count} items + {images_deleted} images deleted")
        
        # Send final complete progress
        send_progress(total_steps, total_steps, "Cancellation complete!", 100)
        
        return True, f"Cancelled. Deleted {len(created_item_ids)} ingredients and {images_deleted} images from storage."
        
    except Exception as e:
        logger.error(f"[Cancel] Error cancelling import {import_id}: {str(e)}", exc_info=True)
        return False, str(e)
