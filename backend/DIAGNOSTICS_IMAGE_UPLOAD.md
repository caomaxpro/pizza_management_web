# Image Upload & Progress Pipeline Diagnostics

## Quick Start - Run These Checks

### 1. **Verify Firebase Setup**
```bash
cd /home/cao-le/Web\ Projects/pizza_admin_web/backend/backend_dj

# Check Firebase credentials file exists
echo "Firebase Credentials:"
ls -la ${FIREBASE_CREDENTIALS_PATH}

# Verify environment variables
echo "Firebase Config:"
echo "  Storage Bucket: $FIREBASE_STORAGE_BUCKET"
echo "  Credentials Path: $FIREBASE_CREDENTIALS_PATH"
echo "  Disable Firebase: $DISABLE_FIREBASE"
```

### 2. **Check Redis is Running (Celery Broker)**
```bash
redis-cli ping
# Should output: PONG
```

### 3. **Verify Django Settings Loads Firebase**
```bash
source ../.venv/bin/activate
python manage.py shell << 'EOF'
import firebase_admin
try:
    app = firebase_admin.get_app()
    print("✓ Firebase initialized in Django")
except ValueError:
    print("⚠ Firebase not initialized - checking USE_LOCAL_STORAGE...")
    from django.conf import settings
    print(f"  USE_LOCAL_STORAGE: {settings.USE_LOCAL_STORAGE}")
    print(f"  FIREBASE_ENABLED: {settings.FIREBASE_ENABLED}")
EOF
```

### 4. **Start Celery Worker with Verbose Output**
```bash
# Terminal 1: Backend directory
cd /home/cao-le/Web\ Projects/pizza_admin_web/backend/backend_dj
source ../.venv/bin/activate
celery -A backend_dj worker --loglevel=info --concurrency=2 -n worker1@%h
# Watch for:
# - "[Celery Init] ✓ Firebase already initialized"
# - "[Batch Task] Starting: N images"
# - "[Image Progress]" events broadcasting
```

### 5. **Test Image Upload Directly**
```bash
# Terminal 2: Backend directory (new terminal)
cd /home/cao-le/Web\ Projects/pizza_admin_web/backend/backend_dj
source ../.venv/bin/activate
python << 'EOF'
from pizza_management.shared.firebase_service import FirebaseStorageService
from pizza_management.shared.image_processor import ImageProcessor
import requests

# Test Firebase upload with real image
test_url = "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"

try:
    print("Downloading test image...")
    response = requests.get(test_url, timeout=10)
    image_bytes = response.content
    print(f"✓ Downloaded {len(image_bytes)} bytes")
    
    print("\nAttempting Firebase upload...")
    result = FirebaseStorageService.upload_image_optimized(
        image_bytes,
        original_filename="test_image.png",
        folder="test"
    )
    print(f"✓ Upload result: {result}")
    
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    traceback.print_exc()
EOF
```

### 6. **Test Image Batch Task**
```bash
# Terminal 2: Backend directory
cd /home/cao-le/Web\ Projects/pizza_admin_web/backend/backend_dj
source ../.venv/bin/activate
python << 'EOF'
from pizza_management.item.tasks import process_images_batch_async
import uuid

# Create test batch
test_images = [
    {
        "item_id": "test-1",
        "image_url": "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png",
        "folder": "items"
    }
]

import_id = str(uuid.uuid4())
print(f"Testing batch processing with import_id: {import_id}")
print(f"Images to process: {len(test_images)}")

# Queue the task
try:
    task = process_images_batch_async.delay(test_images, import_id)
    print(f"✓ Task queued: {task.id}")
    print(f"  Check Celery worker output for progress events")
except Exception as e:
    print(f"❌ Error queueing task: {e}")
    import traceback
    traceback.print_exc()
EOF
```

### 7. **Check WebSocket Consumer Event Registration**
```bash
cd /home/cao-le/Web\ Projects/pizza_admin_web/backend/backend_dj
grep -r "image_progress" pizza_management/*/consumers.py
# Should show the async def image_progress(self, event) handlers
```

### 8. **Monitor Backend Logs in Real-Time**
```bash
# Terminal 3: Log monitoring
tail -f logs/*.log | grep -E "(Firebase|Image|Batch|Progress|ERROR|✓)"
```

## Expected Log Output Flow

When importing items with images:

```
[Async Import {import_id}] Starting: 5 items
[Import 0] ✓ Created: Pizza Item 1 (ID: 123)
[Import 1] ✓ Created: Pizza Item 2 (ID: 124)
...
[Async Import {import_id}] Items created: 5, errors: 0
[Async Import {import_id}] Enqueueing batch processing for 5 images

← Celery Worker Picks Up Batch Task →

[Batch Task] Starting: 5 images
[Image Processing] item=123 → DOWNLOAD mode from https://...
[Celery Init] ✓ Firebase already initialized
[Firebase Optimized Upload] items/uuid_image.webp (compression: 2.5x)
[Image Success] item=123 → https://storage.googleapis.com/...
[Batch Result] item=123 processed & cached

← After Every 3 Images or at End →

[Image Progress] completed: 3/5 (60%)
← WebSocket broadcast to frontend: type="image_progress" →

[Batch Complete] 5 processed, 0 cached, 0 failed
[Image Batch Complete] Broadcasting final stats
← WebSocket broadcast to frontend: type="image_batch_completed" →
```

## Troubleshooting

### Images not uploading
- Check `[Firebase Optimized Upload Error]` logs
- Verify Firebase credentials file is readable
- Ensure `FIREBASE_STORAGE_BUCKET` environment variable is set
- Check GCP bucket exists and service account has permissions

### Progress events not reaching frontend
- Verify `[Image Progress]` is logged in worker
- Check WebSocket group name: should be `item_import_{import_id}` or `ingredient_import_{import_id}`
- Verify browser WebSocket connection in DevTools → Network

### Celery task not executing
- Verify Redis is running: `redis-cli ping`
- Check Celery worker is actually running: look for "Celery Registered Tasks"
- Check `CELERY_ALWAYS_EAGER = True` is NOT set in settings (would run synchronously)

### Firebase initialization fails in worker
- The fix ensures `django.setup()` is called in celery_app.py
- Check `[Celery Init]` log message appears when worker starts
- If not, Firebase may not be configured - check `DISABLE_FIREBASE` env var

## Fixed Issues (This Update)

✅ **Silent Firebase Failures** - Now logs errors with `logger.error()` instead of `print()`
✅ **Image Processor Fallback** - Returns `None` on failure instead of original URL (detects errors)
✅ **Celery Firebase Init** - Explicit Django setup in celery_app.py ensures Firebase is available
✅ **Better Error Traces** - Full exception info logged for debugging
