#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_dj.settings')
sys.path.insert(0, '/home/cao-le/Web Projects/pizza_admin_web/backend/backend_dj')
django.setup()

import json
import uuid
from pizza_management.ingredient.tasks import process_ingredient_import_async
from pizza_management.ingredient.model import Ingredient
from celery.result import AsyncResult

# Test data - simple ingredient without images first
test_data = [
    {
        "name": "Test Ingredient 1",
        "description": "Test description",
        "price": 10.5,
        "type": "vegetable",
        "sub_type": "leafy",
        "is_active": True,
        "image_url": None,  # No image for first test
    }
]

import_id = str(uuid.uuid4())
print(f"[TEST] Starting import test with ID: {import_id}")
print(f"[TEST] Test data: {json.dumps(test_data, indent=2)}")

# Call the async task directly (this will queue it)
print(f"\n[TEST] Queuing async task...")
result = process_ingredient_import_async.delay(test_data, import_id)
print(f"[TEST] Task ID: {result.id}")
print(f"[TEST] Task State: {result.state}")

# Wait a moment for the task to complete
import time
print(f"\n[TEST] Waiting 5 seconds for task to complete...")
time.sleep(5)

# Check task state
print(f"[TEST] Final Task State: {result.state}")
print(f"[TEST] Task Result: {result.result}")

# Check if ingredient was created
print(f"\n[TEST] Checking database...")
ingredients = Ingredient.objects.filter(name__startswith="Test Ingredient").order_by('-id')
print(f"[TEST] Found {ingredients.count()} test ingredients")

for ing in ingredients:
    print(f"  - ID: {ing.id}, Name: {ing.name}, Image URL: {ing.image_url}, Created: {ing.created_at}")

# Check queued tasks
print(f"\n[TEST] Checking Redis queue...")
import redis
from django.conf import settings

redis_client = redis.Redis(
    host=settings.CELERY_BROKER_URL.split('@')[1].split(':')[0] if '@' in settings.CELERY_BROKER_URL else 'localhost',
    port=int(settings.CELERY_BROKER_URL.rstrip('/').split(':')[-1]) if ':' in settings.CELERY_BROKER_URL else 6379,
    db=0
)
queue_len = redis_client.llen('celery')
print(f"[TEST] Tasks in queue: {queue_len}")

# List recent tasks
if queue_len > 0:
    print(f"[TEST] Recent tasks:")
    for i in range(min(3, queue_len)):
        task_msg = redis_client.lindex('celery', i)
        if task_msg:
            print(f"  - {task_msg[:100]}")
