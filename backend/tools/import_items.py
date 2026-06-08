#!/usr/bin/env python3
import os
import sys
import json
import shutil
import uuid
import re
from pathlib import Path
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parents[1]  # backend/
sys.path.insert(0, str(BASE))

load_dotenv(BASE / 'backend_dj' / '.env')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_dj.settings')
import django
django.setup()

from django.conf import settings
from django.db import transaction
from backend_dj.pizza_management.models import Item

DATA_PATH = BASE / 'assets' / 'data' / 'item.json'
IMAGES_ROOT = BASE / 'assets' / 'images'
MEDIA_ITEMS_DIR = Path(settings.MEDIA_ROOT) / 'items'
MEDIA_ITEMS_DIR.mkdir(parents=True, exist_ok=True)

def copy_image_file(rel_path_str):
    """Copy image from assets/images to MEDIA_ROOT/items, return media URL or None"""
    if not rel_path_str:
        return None
    p = rel_path_str.replace('assets/images/', '').lstrip('/')
    src = IMAGES_ROOT / p
    if not src.exists():
        print(f"   ⚠ image missing: {src}")
        return None
    dest_name = f"{uuid.uuid4().hex[:8]}_{src.name}"
    dest = MEDIA_ITEMS_DIR / dest_name
    shutil.copy2(src, dest)
    media_url = str(settings.MEDIA_URL).rstrip('/') + '/'
    url = f"{media_url}items/{dest_name}"
    return url

def get_unit_sku(item_obj):
    if 'id' in item_obj and item_obj['id']:
        return f"ITEM-{item_obj['id']}"
    return None

def import_items():
    with open(DATA_PATH, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    
    created = 0
    skipped = 0
    print(f"\n{'='*60}")
    print(f"Importing {len(data)} items from {DATA_PATH}")
    print(f"Images root: {IMAGES_ROOT}")
    print(f"Media root: {MEDIA_ITEMS_DIR}")
    print(f"{'='*60}\n")
    
    with transaction.atomic():
        for obj in data:
            name = obj.get('name') or 'Unnamed'
            price = float(obj.get('price') or 0)
            description = obj.get('description') or ''
            type_val = obj.get('type')
            sub_type_val = obj.get('sub_type')
            unit_sku = get_unit_sku(obj)
            
            # check duplicate
            if unit_sku and Item.objects.filter(unit_sku=unit_sku).exists():
                print(f"⊘ Skipping {unit_sku} (already exists)")
                skipped += 1
                continue
            
            # copy images
            image_url = copy_image_file(obj.get('image_url'))
            piece_image_url = copy_image_file(obj.get('piece_image_url'))
            
            # create item
            try:
                item = Item.objects.create(
                    name=name,
                    price=price,
                    description=description,
                    unit_sku=unit_sku,
                    type=type_val,
                    sub_type=sub_type_val,
                    image_url=image_url,
                    piece_image_url=piece_image_url,
                    is_ingredient=(type_val == 'ingredient')
                )
                created += 1
                print(f"✓ Created: {item.pk:3d} {name:30s} ({unit_sku})")
            except Exception as e:
                print(f"✗ ERROR: {name} - {e}")
                skipped += 1
    
    print(f"\n{'='*60}")
    print(f"✓ Completed: {created} created, {skipped} skipped")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import_items()