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

# Test data - VALID ingredient with image URL
test_data = [
    {
        "name": "Test Cheese Ingredient",
        "description": "High quality mozzarella",
        "price": 5.50,
        "type": "cheese",  # VALID type
        "is_active": True,
        "image_url": "https://via.placeholder.com/200?text=cheese",  # Placeholder image for testing
    },
    {
        "name": "Test Topping",
        "description": "Fresh pepperoni",
        "price": 3.50,
        "type": "topping",  # VALID type
        "sub_type": "meat",  # Valid for topping
        "is_active": True,
        "image_url": "https://via.placeholder.com/200?text=pepperoni",  # Placeholder image
    }
]

import_id = str(uuid.uuid4())
print(f"[TEST] Starting REAL import test with ID: {import_id}")
print(f"[TEST] Test data items: {len(test_data)}")
for item in test_data:
    print(f"  - {item['name']} (type: {item['type']}, with image: {item.get('image_url') is not None})")

# Call the async task
print(f"\n[TEST] Calling process_ingredient_import_async.delay()...")
result = process_ingredient_import_async.delay(test_data, import_id)
print(f"[TEST] Task queued with ID: {result.id}")

# Wait for task to complete
print(f"\n[TEST] Waiting 10 seconds for task execution...")
for i in range(10):
    time.sleep(1)
    print(f"  [{i+1}/10] state={result.state}", end='\r')

print(f"\n[TEST] Final Task State: {result.state}")
if result.state == 'FAILURE':
    print(f"[TEST] Task failed with error: {result.info}")

# Check if ingredients were created
print(f"\n[TEST] Checking database for created ingredients...")
test_ingredients = Ingredient.objects.filter(name__startswith="Test").order_by('-id')
print(f"[TEST] Found {test_ingredients.count()} test ingredients")

for ing in test_ingredients:
    print(f"  - ID: {ing.id}")
    print(f"    Name: {ing.name}")
    print(f"    Type: {ing.type}")
    print(f"    Image URL: {ing.image_url if ing.image_url else 'NOT SET'}")
    print(f"    Created: {ing.created_at}")

# Wait a moment for batch processing
print(f"\n[TEST] Waiting 5 more seconds for batch image processing...")
time.sleep(5)

# Check if images were processed
print(f"\n[TEST] Checking if images were processed...")
for ing in test_ingredients:
    ing.refresh_from_db()
    print(f"  - {ing.name}: image_url={ing.image_url if ing.image_url else 'STILL NOT SET'}")
