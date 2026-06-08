from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords
from django.conf import settings
from pizza_management.ingredient.model import Ingredient
from pizza_management.shared.constants import ITEM_TYPE_CHOICES, PIZZA_SUB_TYPE_CHOICES
from pizza_management.shared.image_handler import LocalImageHandler
from pizza_management.shared.firebase_service import FirebaseStorageService

class Item(models.Model):
    """Item model for sellable products"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.FloatField()
    original_price = models.FloatField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    type = models.CharField(max_length=50, choices=ITEM_TYPE_CHOICES, null=True, blank=True)
    sub_type = models.CharField(max_length=50, choices=PIZZA_SUB_TYPE_CHOICES, null=True, blank=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    image_source_url = models.CharField(max_length=500, blank=True, null=True, help_text="Source path for backup (e.g., assets/images/pizza/...)")
    
    # Relationships to Ingredient
    dough = models.ForeignKey(Ingredient, null=True, blank=True, related_name="as_dough_for", 
                              on_delete=models.SET_NULL, limit_choices_to={"type": "dough"})
    sauce = models.ForeignKey(Ingredient, null=True, blank=True, related_name="as_sauce_for", 
                              on_delete=models.SET_NULL, limit_choices_to={"type": "sauce"})
    cheese = models.ForeignKey(Ingredient, null=True, blank=True, related_name="as_cheese_for", 
                               on_delete=models.SET_NULL, limit_choices_to={"type": "cheese"})
    toppings = models.ManyToManyField(Ingredient, blank=True, related_name="as_topping_for",
                                      limit_choices_to={"type": "topping"})
    extras = models.ManyToManyField(Ingredient, blank=True, related_name="as_extra_for",
                                    limit_choices_to={"type": "extra"})
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        # Delete associated image from storage
        if self.image_url:
            try:
                if not settings.FIREBASE_ENABLED:
                    LocalImageHandler.delete_image(self.image_url)
                else:
                    FirebaseStorageService.delete_image(self.image_url)
            except Exception as e:
                print(f"Error deleting image for {self.name}: {e}")
        
        return super().delete(*args, **kwargs)