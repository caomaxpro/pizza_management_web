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
import time
from pizza_management.ingredient.tasks import process_ingredient_import_async
from pizza_management.ingredient.model import Ingredient

# Test data - using actual local image files
test_data = [
    {
        "name": "Test Mozzarella Cheese",
        "description": "Premium fresh mozzarella",
        "price": 4.50,
        "type": "cheese",
        "is_active": True,
        "image_url": "assets/images/topping/cheese/mozzarella.png",  # LOCAL FILE
    },
    {
        "name": "Test Pepperoni Topping",
        "description": "Spicy pepperoni slices",
        "price": 2.50,
        "type": "topping",
        "sub_type": "meat",
        "is_active": True,
        "image_url": "assets/images/topping/meat/pepperoni.png",  # LOCAL FILE
    }
]

import_id = str(uuid.uuid4())
print(f"[TEST] Starting test with REAL LOCAL IMAGE FILES - ID: {import_id}")
print(f"[TEST] Test data items: {len(test_data)}")
for item in test_data:
    img_exists = os.path.exists(f"/home/cao-le/Web Projects/pizza_admin_web/backend/backend_dj/{item['image_url']}")
    print(f"  - {item['name']} (type: {item['type']}, image: {item['image_url']}, exists: {img_exists})")

# Call the async task
print(f"\n[TEST] Calling process_ingredient_import_async.delay()...")
result = process_ingredient_import_async.delay(test_data, import_id)
print(f"[TEST] Task queued with ID: {result.id}")

# Wait for main task to complete
print(f"\n[TEST] Waiting 5 seconds for main ingredient creation task...")
time.sleep(5)

# Check if ingredients were created
print(f"\n[TEST] Checking database for created ingredients...")
test_ingredients = Ingredient.objects.filter(name__startswith="Test M", name__contains="ozzarella") | Ingredient.objects.filter(name__startswith="Test P", name__contains="epperoni")
test_ingredients = test_ingredients.order_by('-id')
print(f"[TEST] Found {test_ingredients.count()} test ingredients")

for ing in test_ingredients:
    print(f"  - ID: {ing.id}")
    print(f"    Name: {ing.name}")
    print(f"    Type: {ing.type}")
    print(f"    Image URL (before batch): {ing.image_url if ing.image_url else 'NOT SET'}")

# Wait for batch processing to complete
print(f"\n[TEST] Waiting 10 more seconds for batch image processing...")
for i in range(10):
    print(f"  [{i+1}/10]", end='\r')
    time.sleep(1)

# Check if images were processed
print(f"\n\n[TEST] FINAL CHECK - Images after batch processing:")
for ing in test_ingredients:
    ing.refresh_from_db()
    if ing.image_url:
        print(f"  ✅ {ing.name}: image_url=%s" % ing.image_url[:80])
    else:
        print(f"  ❌ {ing.name}: image_url=STILL NOT SET")
