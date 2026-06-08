from django.db import models
from django.utils import timezone
from django.db.models import Q
from simple_history.models import HistoricalRecords
from django.conf import settings
from pizza_management.shared.constants import INGREDIENT_TYPE_CHOICES
from pizza_management.shared.image_handler import LocalImageHandler
from pizza_management.shared.firebase_service import FirebaseStorageService

class Ingredient(models.Model):
    """Ingredient model for pizza components"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    price = models.FloatField()
    original_price = models.FloatField(null=True, blank=True)
    
    type = models.CharField(max_length=50, choices=INGREDIENT_TYPE_CHOICES)
    sub_type = models.CharField(max_length=50, null=True, blank=True)
    
    image_url = models.URLField(max_length=500, blank=True, null=True)
    image_source_url = models.CharField(max_length=500, blank=True, null=True, help_text="Source path for backup (e.g., assets/images/...)")
    piece_image_url = models.URLField(max_length=500, blank=True, null=True)
    piece_image_source_url = models.CharField(max_length=500, blank=True, null=True, help_text="Source path for piece image backup")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.name} ({self.type})"

    def delete(self, *args, **kwargs):
        if self.image_url:
            try:
                if not settings.FIREBASE_ENABLED:
                    LocalImageHandler.delete_image(self.image_url)
                else:
                    FirebaseStorageService.delete_image(self.image_url)
            except Exception as e:
                print(f"Error deleting image for {self.name}: {e}")
        
        if self.piece_image_url:
            try:
                if not settings.FIREBASE_ENABLED:
                    LocalImageHandler.delete_image(self.piece_image_url)
                else:
                    FirebaseStorageService.delete_image(self.piece_image_url)
            except Exception as e:
                print(f"Error deleting piece image for {self.name}: {e}")
        
        return super().delete(*args, **kwargs)