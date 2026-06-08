from django.conf import settings
from pizza_management.models import Item, Ingredient
from pizza_management.shared.image_handler import LocalImageHandler
from pizza_management.shared.firebase_service import FirebaseStorageService
from pathlib import Path
from io import BytesIO

class ItemService:
    @staticmethod
    def create_with_fks(item_dict, dough_id, sauce_id, cheese_id, toppings_ids, extras_ids):
        """Create item with FK relationships"""
        item = Item.objects.create(**item_dict)
        ItemService._set_fks(item, dough_id, sauce_id, cheese_id)
        item.save()
        if toppings_ids:
            item.toppings.set(toppings_ids)
        if extras_ids:
            item.extras.set(extras_ids)
        return item
    
    @staticmethod
    def update_with_fks(item, update_dict, dough_id, sauce_id, cheese_id, toppings_ids, extras_ids):
        """Update item with FK relationships"""
        for attr, value in update_dict.items():
            setattr(item, attr, value)
        ItemService._set_fks(item, dough_id, sauce_id, cheese_id)
        item.save()
        if toppings_ids is not None:
            item.toppings.set(toppings_ids)
        if extras_ids is not None:
            item.extras.set(extras_ids)
        return item
    
    @staticmethod
    def _set_fks(item, dough_id, sauce_id, cheese_id):
        """Set FK relationships"""
        if dough_id:
            item.dough = Ingredient.objects.get(id=dough_id)
        if sauce_id:
            item.sauce = Ingredient.objects.get(id=sauce_id)
        if cheese_id:
            item.cheese = Ingredient.objects.get(id=cheese_id)