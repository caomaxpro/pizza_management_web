#!/usr/bin/env python3
import os
import sys
import uuid
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, '/home/cao-le/Flutter Projects/pizza_ordering_app/backend')

# load .env của project
load_dotenv(os.path.join(BASE_DIR, 'backend_dj', '.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_dj.settings')

import django
django.setup()

from backend_dj.pizza_management.models import Item

def main():
    sku = f"TEST-SKU-{uuid.uuid4().hex[:8]}"
    item = Item.objects.create(
        name="Pizza_2",
        price=10.99,
        unit_sku=sku
    )
    print("✅ Created item:")
    print("  id:", item.pk)
    print("  name:", item.name)
    print("  unit_sku:", item.unit_sku)
    print("\nIf you want to delete it, run:")
    print(f"  python manage.py shell -c \"from pizza_management.models import Item; Item.objects.filter(pk={item.pk}).delete()\"")

if __name__ == "__main__":
    main()