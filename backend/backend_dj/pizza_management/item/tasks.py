import logging
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from celery import shared_task
from celery.result import AsyncResult
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from pizza_management.item.model import Item
from pizza_management.item.validators import ItemCreateRequest
from pizza_management.item.serializers import ItemSerializer
from pizza_management.shared.image_processor import ImageProcessor
from pizza_management.ingredient.model import Ingredient
from helper.cache_helpers import CacheHelper

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='pizza_management.item.process_import')
def process_item_import_async(self, items_data, import_id):
    """
    Process item import asynchronously via Celery - OPTIMIZED with batch image processing.
    
    Strategy: Create items immediately (no blocking on image), then batch-process images
    in background with parallel uploads and cache deduplication.
    
    Args:
        items_data: List of item dictionaries
        import_id: UUID for tracking this import session
    """
    total_items = len(items_data)
    results = {"created": [], "errors": 0}
    images_to_process = []  # Collect image pairs for batch processing
    
    # Store task_id in cache for cancellation
    cache_key_task = f"import_task_{import_id}"
    cache_key_items = f"import_created_items_{import_id}"
    
    logger.info(f"[Async Import {import_id}] Starting: {total_items} items (Option 1+2+3: Fast create + Batch images)")
    
    try:
        # Store task_id in cache for cancellation
        CacheHelper.cache_set(cache_key_task, self.request.id, timeout=3600)
        logger.info(f"[Async Import {import_id}] Task ID stored: {self.request.id}")
        
        for idx, item_data in enumerate(items_data):
            try:
                # Copy to avoid modifying original
                data = item_data.copy()
                
                # Skip if item with ID already exists
                item_id = data.get("id")
                if item_id and Item.objects.filter(id=item_id).exists():
                    logger.info(f"[Import {idx}] Skipping item ID {item_id} - already exists")
                    results["errors"] += 1
                    continue
                
                # Extract relationships
                dough_id = data.pop("dough", None)
                sauce_id = data.pop("sauce", None)
                cheese_id = data.pop("cheese", None)
                toppings_ids = data.pop("toppings", None)
                extras_ids = data.pop("extras", None)
                
                # Extract image fields for later batch processing
                image_url = data.pop('image_url', None)
                image_source_url = data.pop('image_source_url', None)
                data.pop('image_file', None)
                
                logger.info(f"[Import {idx}] Image source: {image_source_url}")
                
                # Remove ID from data (will be auto-generated unless specified)
                if item_id:
                    data_with_id = data.copy()
                    data_with_id['id'] = item_id
                else:
                    data_with_id = data.copy()
                    data_with_id.pop('id', None)
                
                # Validate and prepare
                valid_data = ItemCreateRequest(**data_with_id)
                item_dict = valid_data.model_dump(exclude_none=True)
                
                # ===== OPTION 1: CREATE ITEM IMMEDIATELY (NO BLOCKING) =====
                item = Item.objects.create(
                    name=item_dict['name'],
                    description=item_dict.get('description'),
                    price=item_dict['price'],
                    original_price=item_dict.get('original_price'),
                    category=item_dict.get('category'),
                    type=item_dict.get('type'),
                    sub_type=item_dict.get('sub_type'),
                    is_active=item_dict.get('is_active', True),
                    image_url=None,  # ← No image yet, will be filled by batch task
                    image_source_url=image_source_url,
                )
                
                # Set relationships
                if dough_id:
                    try:
                        item.dough = Ingredient.objects.get(id=dough_id)
                    except Ingredient.DoesNotExist:
                        logger.warning(f"[Import {idx}] Dough ingredient ID {dough_id} not found")
                
                if sauce_id:
                    try:
                        item.sauce = Ingredient.objects.get(id=sauce_id)
                    except Ingredient.DoesNotExist:
                        logger.warning(f"[Import {idx}] Sauce ingredient ID {sauce_id} not found")
                
                if cheese_id:
                    try:
                        item.cheese = Ingredient.objects.get(id=cheese_id)
                    except Ingredient.DoesNotExist:
                        logger.warning(f"[Import {idx}] Cheese ingredient ID {cheese_id} not found")
                
                item.save()
                
                if toppings_ids:
                    item.toppings.set(toppings_ids)
                if extras_ids:
                    item.extras.set(extras_ids)
                
                results["created"].append(item.id)
                
                # Store created item IDs in cache for cleanup on cancel
                created_items = CacheHelper.cache_get(cache_key_items) or []
                created_items.append(item.id)
                CacheHelper.cache_set(cache_key_items, created_items, timeout=3600)
                
                # Collect image URL for batch processing (if exists)
                if image_url:
                    images_to_process.append({
                        "item_id": item.id,
                        "image_url": image_url,
                        "folder": "items"
                    })
                
                logger.info(f"[Import {idx}] ✓ Created: {item.name} (ID: {item.id}) - Image queued")
                
            except Exception as e:
                results["errors"] += 1
                logger.error(f"[Import {idx}] Error: {str(e)}")
        
        # Broadcast fast completion for item creation (no progress update, just items created)
        logger.info(f"[Async Import {import_id}] Items created: {len(results['created'])}, errors: {results['errors']}")
        # Skip progress broadcast here - it will be 100% anyway
        
        # ===== OPTION 2+3: ENQUEUE BATCH IMAGE PROCESSING ======
        if images_to_process:
            logger.info(f"[Async Import {import_id}] Enqueueing batch processing for {len(images_to_process)} images")
            process_images_batch_async.delay(images_to_process, import_id)
        
        # Invalidate cache
        if results["created"]:
            CacheHelper.cache_clear_pattern("items_*")
            logger.info("[Import] Cache cleared")
        
        # Broadcast final completion
        _broadcast_import_completion(import_id, len(results["created"]), results["errors"])
        logger.info(f"[Async Import {import_id}] Complete: {len(results['created'])} items created, {results['errors']} errors, {len(images_to_process)} images queued for processing")
        
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


def _process_single_image(item_id, image_url, folder):
    """
    Process single image: check cache, download/process, upload, update DB.
    Designed to run inside ThreadPoolExecutor for parallel uploads.
    """
    try:
        cache_key = _get_image_cache_key(image_url)
        
        # Check cache first (OPTION 3: Cache deduplication)
        cached_result = CacheHelper.cache_get(cache_key)
        if cached_result:
            # Validate Firebase URL still exists before using cache
            if _validate_firebase_url(cached_result):
                logger.info(f"[Image Cache HIT] item={item_id}, url={image_url[:50]}... → {cached_result[:50]}...")
                Item.objects.filter(id=item_id).update(image_url=cached_result)
                return (item_id, cached_result, None)
            else:
                # Firebase URL gone, invalidate cache and reprocess
                logger.warning(f"[Image Cache INVALID] item={item_id}, cached URL unreachable, clearing cache and reprocessing...")
                CacheHelper.cache_delete(cache_key)
                # Fall through to reprocess
        
        # Process image
        processed_url = None
        if image_url.startswith(('http://', 'https://')):
            logger.info(f"[Image Processing] item={item_id} → DOWNLOAD mode from {image_url}")
            processed_url = ImageProcessor.download_and_upload_image(image_url, folder)
        else:
            logger.info(f"[Image Processing] item={item_id} → LOCAL mode from {image_url}")
            processed_url = ImageProcessor.process_image_path(image_url, folder)
        
        # Validate processing
        if processed_url is None:
            raise Exception(f"Image processing returned None - upload or processing failed")
        
        # Update DB
        Item.objects.filter(id=item_id).update(image_url=processed_url)
        
        # ✅ Clear item detail cache IMMEDIATELY (prevent stale NULL from being cached)
        detail_cache_key = f"items_detail:id_{item_id}"
        CacheHelper.cache_delete(detail_cache_key)
        logger.info(f"[Cache Invalidated] Cleared {detail_cache_key} after image update")
        
        # Cache result (24 hours)
        CacheHelper.cache_set(cache_key, processed_url, timeout=86400)
        logger.info(f"[Image Success] item={item_id} → {processed_url[:80]}...")
        
        return (item_id, processed_url, None)
    
    except Exception as e:
        logger.error(f"[Image Error] item={item_id} err={str(e)[:150]}")
        return (item_id, None, str(e))


@shared_task(bind=True, name='pizza_management.item.process_images_batch')
def process_images_batch_async(self, images_batch, import_id):
    """
    OPTION 2+3: Batch process images in parallel with ThreadPoolExecutor + cache + RAM control.
    
    Args:
        images_batch: List of {item_id, image_url, folder}
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
    
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(_process_single_image, img['item_id'], img['image_url'], img['folder']): img
                for img in images_batch
            }
            
            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    item_id, processed_url, error = future.result()
                    completed_count += 1
                    
                    if error:
                        results["failed"] += 1
                        logger.error(f"[Batch Result] item={item_id} failed: {error}")
                    else:
                        # Check if it was cached
                        if processed_url:
                            cache_key = _get_image_cache_key(futures[future]['image_url'])
                            if CacheHelper.cache_get(cache_key):
                                results["cached"] += 1
                                logger.info(f"[Batch Result] item={item_id} from cache")
                            else:
                                results["processed"] += 1
                                logger.info(f"[Batch Result] item={item_id} processed & cached")
                except Exception as e:
                    logger.error(f"[Batch Error] {str(e)}")
                    results["failed"] += 1
                    completed_count += 1
                
                # Broadcast progress every BATCH_SIZE images or at the end
                if completed_count % BATCH_SIZE == 0 or completed_count == total_images:
                    percentage = int((completed_count / total_images) * 100) if total_images > 0 else 100
                    _broadcast_image_progress(import_id, completed_count, total_images, percentage)
        
        logger.info(f"[Batch Complete] {results['processed']} processed, {results['cached']} cached, {results['failed']} failed")
        
        # 🔄 Clear ALL item caches so frontend gets fresh data with images immediately
        logger.info("[Cache Invalidation] Clearing all item caches...")
        CacheHelper.cache_clear_pattern("items_list*")
        CacheHelper.cache_clear_pattern("items_detail*")
        CacheHelper.cache_clear_pattern("items_filter*")
        CacheHelper.cache_clear_pattern("items_paginated*")
        logger.info("[Cache Invalidation] ✅ All item caches cleared")
        
        # Broadcast batch completion via WebSocket
        _broadcast_image_batch_complete(import_id, results)
        
    except Exception as e:
        logger.error(f"[Batch Fatal] {str(e)}")
        _broadcast_import_error(import_id, f"Image batch processing failed: {str(e)}")


@shared_task(bind=True, name='pizza_management.item.process_item_image')
def process_item_image_async(self, item_id, image_url):
    """
    OPTION 1+3: Per-item image processing task (backup/retry for failed images).
    
    Args:
        item_id: Item to update
        image_url: Image source URL/path
        
    Returns:
        Processed image URL or raises exception for retry
    """
    logger.info(f"[Per-Item Task] Processing image for item={item_id}")
    
    try:
        item = Item.objects.get(id=item_id)
        cache_key = _get_image_cache_key(image_url)
        
        # Check cache
        cached = CacheHelper.cache_get(cache_key)
        if cached:
            item.image_url = cached
            item.save()
            logger.info(f"[Per-Item] item={item_id} from cache")
            return cached
        
        # Process
        if image_url.startswith(('http://', 'https://')):
            processed = ImageProcessor.download_and_upload_image(image_url, "items")
        else:
            processed = ImageProcessor.process_image_path(image_url, "items")
        
        # Validate
        if not processed or processed == image_url:
            raise Exception(f"Processing failed")
        
        # Update DB & cache
        item.image_url = processed
        item.save()
        CacheHelper.cache_set(cache_key, processed, timeout=86400)
        logger.info(f"[Per-Item] item={item_id} processed & cached")
        
        return processed
    
    except Exception as e:
        logger.error(f"[Per-Item Error] item={item_id} err={str(e)}")
        # Retry with exponential backoff (3 max retries)
        raise self.retry(exc=e, countdown=60, max_retries=3)


def _broadcast_image_progress(import_id, processed, total, percentage):
    """Broadcast image processing progress via WebSocket (every N images)"""
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        async_to_sync(channel_layer.group_send)(
            f"item_import_{import_id}",
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
            f"item_import_{import_id}",
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


def _broadcast_import_progress(import_id, current, total, percentage, completed_item=None):
    """Broadcast progress via WebSocket with completed item data"""
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        # Serialize item if available
        item_data = None
        if completed_item:
            try:
                item_data = ItemSerializer(completed_item).data
            except Exception as serialize_err:
                logger.error(f"Failed to serialize item: {serialize_err}")
        
        async_to_sync(channel_layer.group_send)(
            f"item_import_{import_id}",
            {
                "type": "import_progress",  # ← FIXED: Use underscore, not dot
                "current": current,
                "total": total,
                "percentage": percentage,
                "message": f"Processing {current}/{total}",
                "completed_item": item_data,
            }
        )
        log_msg = f"[WS] Progress {percentage}% ({current}/{total})"
        if completed_item:
            log_msg += f" - Created: {completed_item.name}"
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
            f"item_import_{import_id}",
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
            f"item_import_{import_id}",
            {
                "type": "import_error",  # ← FIXED: Use underscore, not dot
                "error": error_msg,
                "message": f"Import failed: {error_msg}",
            }
        )
        logger.error(f"[WS] Error: {error_msg}")
    except Exception as e:
        logger.error(f"[WS] Failed to broadcast error: {str(e)}")


def cancel_item_import(import_id):
    """Cancel an async item import by deleting created items"""
    try:
        cache_key_items = f"import_created_items_{import_id}"
        cache_key_task = f"import_task_{import_id}"
        
        # Get created item IDs from cache
        created_items = CacheHelper.cache_get(cache_key_items) or []
        logger.info(f"[Cancel {import_id}] Found {len(created_items)} items to delete")
        
        # Delete created items
        if created_items:
            Item.objects.filter(id__in=created_items).delete()
            logger.info(f"[Cancel {import_id}] Deleted {len(created_items)} items")
        
        # Broadcast cancellation
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"item_import_{import_id}",
                    {
                        "type": "import.cancelled",
                        "message": f"Import cancelled - {len(created_items)} items deleted",
                    }
                )
                logger.info(f"[Cancel {import_id}] Cancellation broadcasted")
        except Exception as ws_err:
            logger.error(f"[Cancel {import_id}] Failed to broadcast cancellation: {ws_err}")
        
        # Clear cache
        CacheHelper.cache_delete(cache_key_items)
        CacheHelper.cache_delete(cache_key_task)
        
        # Invalidate cache
        CacheHelper.cache_clear_pattern("items_*")
        logger.info(f"[Cancel {import_id}] Cache cleared")
        
    except Exception as e:
        logger.error(f"[Cancel {import_id}] Error: {str(e)}")
