#!/usr/bin/env python
"""Direct ingredient import script - bypasses HTTP layer"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_dj.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from pizza_management.ingredient.model import Ingredient
from pizza_management.shared.image_processor import ImageProcessor
from pizza_management.ingredient.validators import IngredientCreateRequest

json_path = os.path.join(os.path.dirname(__file__), 'test', 'ingredients.json')
with open(json_path) as f:
    data = json.load(f)

ingredients_data = data if isinstance(data, list) else data.get('ingredients', [])
print(f"Loaded {len(ingredients_data)} ingredients from JSON")

created = []
errors = []

for idx, ingredient_data in enumerate(ingredients_data):
    try:
        ingredient_data = dict(ingredient_data)  # make a copy
        image_file_path = ingredient_data.pop('image_file', None)
        piece_file_path = ingredient_data.pop('piece_file', None)

        valid_data = IngredientCreateRequest(**ingredient_data)
        ingredient_dict = valid_data.model_dump(exclude_none=True)

        image_url = ImageProcessor.process_image_path(image_file_path, "ingredients") if image_file_path else None
        piece_url = ImageProcessor.process_image_path(piece_file_path, "ingredients") if piece_file_path else None

        ingredient = Ingredient.objects.create(
            name=ingredient_dict['name'],
            description=ingredient_dict.get('description'),
            price=ingredient_dict['price'],
            type=ingredient_dict['type'],
            sub_type=ingredient_dict.get('sub_type'),
            is_active=ingredient_dict.get('is_active', True),
            image_url=image_url,
            piece_image_url=piece_url,
        )

        created.append(ingredient.name)
        print(f"  [{idx+1}/{len(ingredients_data)}] ✓ {ingredient.name}")

    except Exception as e:
        errors.append({'index': idx, 'name': ingredient_data.get('name', '?'), 'error': str(e)})
        print(f"  [{idx+1}/{len(ingredients_data)}] ✗ ERROR: {e}")

print(f"\n=== DONE ===")
print(f"Created: {len(created)}")
print(f"Errors:  {len(errors)}")

if errors:
    print("\nErrors:")
    for err in errors:
        print(f"  - [{err['index']}] {err['name']}: {err['error']}")

# Quick verify
from pizza_management.ingredient.model import Ingredient as Ing
sample = Ing.objects.first()
if sample:
    print(f"\nSample URL: {sample.image_url}")
